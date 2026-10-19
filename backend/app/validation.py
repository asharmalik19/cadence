"""Code checks on every AI reply. The AI proposes; these rules decide whether we trust it."""

from collections import defaultdict
from datetime import date, timedelta

from .models import DETAIL_DAYS, GoalPlan, NewGoalPlan, PlanContext, Replan, TaskPlan

MAX_PROBLEMS = 20  # keep the retry prompt short


def check_plan(ctx: PlanContext, reply: NewGoalPlan | Replan) -> list[str]:
    """Return plain-language problems with the reply, or an empty list if it's fine."""
    problems: list[str] = []
    deadlines = {g.id: g.deadline for g in ctx.goals}

    if isinstance(reply, NewGoalPlan):
        if not reply.smart_goal.strip():
            problems.append("smart_goal must not be empty.")
        if reply.verdict == "impossible":
            if not reply.message.strip():
                problems.append("An impossible verdict needs a message explaining why.")
            return problems
        if reply.new_goal is None:
            return ["A stretch or comfortable verdict must include new_goal."]
        if ctx.new_goal is None:
            return ["Internal error: no new goal in the context."]
        new = reply.new_goal
        if new.goal_id != 0:
            problems.append("new_goal.goal_id must be 0.")
        if not new.breakdown:
            problems.append("The new goal needs a breakdown with at least one workstream.")
        if not new.tasks:
            problems.append("The new goal needs at least one task.")
        problems += _check_goal_plan("the new goal", new, ctx.start_day, ctx.new_goal.deadline)
        changed = reply.rework
        new_tasks = [(0, t) for t in new.tasks]
    else:
        changed = reply.goals
        new_tasks = []
        returned = {g.goal_id for g in reply.goals}
        for gid in ctx.replan_goal_ids:
            if gid not in returned:
                problems.append(f"Goal {gid} had missed tasks and must be re-planned.")
        for gid in returned - set(ctx.replan_goal_ids):
            problems.append(f"Goal {gid} had no missed tasks and must not be in the reply.")

    for plan in changed:
        if plan.goal_id not in deadlines:
            problems.append(f"Goal {plan.goal_id} does not exist.")
            continue
        if not plan.change_note.strip():
            problems.append(f"Goal {plan.goal_id} changed but has no change_note.")
        problems += _check_goal_plan(f"goal {plan.goal_id}", plan, ctx.start_day, deadlines[plan.goal_id])

    problems += _check_budget(ctx, changed, new_tasks)
    return problems[:MAX_PROBLEMS]


def _check_goal_plan(label: str, plan: GoalPlan, start: date, deadline: date) -> list[str]:
    problems = []
    horizon = min(deadline, start + timedelta(days=DETAIL_DAYS - 1))
    names = {m.name for m in plan.milestones}
    if not plan.milestones:
        problems.append(f"{label} needs at least one milestone.")
    for m in plan.milestones:
        if not m.name.strip() or not m.reached_when.strip():
            problems.append(f"A milestone of {label} needs a name and a reached_when.")
        if m.target_day > deadline:
            problems.append(f"Milestone '{m.name}' of {label} is after the deadline {deadline}.")
    for t in plan.tasks:
        where = f"Task '{t.title or '(untitled)'}' on {t.day} for {label}"
        if not t.title.strip():
            problems.append(f"{where} has no title.")
        if not t.done_criterion.strip():
            problems.append(f"{where} has no done criterion.")
        if not t.why.strip():
            problems.append(f"{where} has no why.")
        if t.minutes <= 0:
            problems.append(f"{where} needs minutes greater than 0.")
        if t.day < start:
            problems.append(f"{where} is before the start day {start}.")
        if t.day > deadline:
            problems.append(f"{where} is after the deadline {deadline}.")
        elif t.day > horizon:
            problems.append(f"{where} is beyond the {DETAIL_DAYS}-day detail window (last day {horizon}); "
                            "plan later work as milestones only.")
        if t.milestone not in names:
            problems.append(f"{where} names milestone '{t.milestone}', which isn't in the milestones list.")
    return problems


def _check_budget(
    ctx: PlanContext, changed: list[GoalPlan], new_tasks: list[tuple[int, TaskPlan]]
) -> list[str]:
    """After the change, across all goals: no day over daily_hours, and every Monday–Sunday week keeps
    at least one free day (the user's admin day; the AI chooses which)."""
    changed_ids = {p.goal_id for p in changed}
    per_day: dict[date, int] = defaultdict(int)

    for g in ctx.goals:
        for t in g.tasks:
            if t.status == "missed":
                continue
            # A changed goal keeps only its past and ticked tasks; the reply replaces the rest.
            replaced = g.id in changed_ids and t.status == "planned" and t.day >= ctx.start_day
            if not replaced:
                per_day[t.day] += t.minutes
    for plan in changed:
        for t in plan.tasks:
            per_day[t.day] += t.minutes
    for _, t in new_tasks:
        per_day[t.day] += t.minutes

    limit = ctx.daily_hours * 60
    problems = [
        f"{day} has {minutes} minutes of tasks across all goals, over the daily limit of {limit}."
        for day, minutes in sorted(per_day.items())
        if minutes > limit
    ]
    busy_days_per_week: dict[date, set[date]] = defaultdict(set)
    for day, minutes in per_day.items():
        if minutes > 0:
            busy_days_per_week[_week_start(day)].add(day)
    problems += [
        f"The week starting {week} has tasks on all 7 days; leave at least one day free."
        for week, days in sorted(busy_days_per_week.items())
        if len(days) == 7
    ]
    return problems


def _week_start(d: date) -> date:
    return date.fromordinal(d.toordinal() - d.weekday())
