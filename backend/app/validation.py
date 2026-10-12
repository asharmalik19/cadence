"""Code checks on every AI reply. The AI proposes; these rules decide whether we trust it."""

from collections import defaultdict
from datetime import date

from .models import GoalPlan, NewGoalPlan, PlanContext, Replan, TaskPlan

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
        problems += _check_tasks("the new goal", new.tasks, ctx.start_day, ctx.new_goal.deadline)
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
        problems += _check_tasks(f"goal {plan.goal_id}", plan.tasks, ctx.start_day, deadlines[plan.goal_id])

    problems += _check_budget(ctx, changed, new_tasks)
    return problems[:MAX_PROBLEMS]


def _check_tasks(label: str, tasks: list[TaskPlan], start: date, deadline: date) -> list[str]:
    problems = []
    for t in tasks:
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
    return problems


def _check_budget(
    ctx: PlanContext, changed: list[GoalPlan], new_tasks: list[tuple[int, TaskPlan]]
) -> list[str]:
    """Every Monday–Sunday week must fit in weekly_hours, across all goals, after the change."""
    changed_ids = {p.goal_id for p in changed}
    per_week: dict[date, int] = defaultdict(int)

    for g in ctx.goals:
        for t in g.tasks:
            if t.status == "missed":
                continue
            # A changed goal keeps only its past and ticked tasks; the reply replaces the rest.
            replaced = g.id in changed_ids and t.status == "planned" and t.day >= ctx.start_day
            if not replaced:
                per_week[_week_start(t.day)] += t.minutes
    for plan in changed:
        for t in plan.tasks:
            per_week[_week_start(t.day)] += t.minutes
    for _, t in new_tasks:
        per_week[_week_start(t.day)] += t.minutes

    limit = ctx.weekly_hours * 60
    return [
        f"The week starting {week} has {minutes} minutes of tasks, over the weekly budget of {limit}."
        for week, minutes in sorted(per_week.items())
        if minutes > limit
    ]


def _week_start(d: date) -> date:
    return date.fromordinal(d.toordinal() - d.weekday())
