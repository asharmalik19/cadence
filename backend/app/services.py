"""The rules for each action. Each one loads what it needs, asks the planner if needed, checks the
reply, and saves everything in one transaction (or nothing)."""

import sqlite3
from datetime import date, timedelta
from typing import Literal, overload

from . import db
from .models import (
    AddGoalAdded,
    AddGoalImpossible,
    AddGoalIn,
    AppState,
    ClarifyIn,
    ClarifyOut,
    DETAIL_DAYS,
    GoalContext,
    NewGoalPlan,
    NextDayIn,
    NewGoalRequest,
    PlanContext,
    Replan,
    Settings,
    TodayTask,
    UpdateContext,
)
from .planner.base import Planner, PlanningFailed
from .validation import check_plan

MAX_GOALS = 3
MAX_QUESTIONS = 4


class Refused(Exception):
    """The action isn't allowed right now (e.g. a 4th goal). Shown to the user as-is; nothing changes."""


class NotFound(Exception):
    """The goal asked for doesn't exist (e.g. already deleted in another tab)."""


@overload
def plan_checked(planner: Planner, ctx: PlanContext, kind: Literal["new_goal"]) -> NewGoalPlan: ...
@overload
def plan_checked(planner: Planner, ctx: PlanContext, kind: Literal["replan"]) -> Replan: ...
def plan_checked(planner: Planner, ctx: PlanContext, kind: str) -> NewGoalPlan | Replan:
    """Ask the planner, check the reply, retry once with the problems listed, then give up."""
    ask = planner.plan_new_goal if kind == "new_goal" else planner.replan
    reply = ask(ctx)
    problems = check_plan(ctx, reply)
    if not problems:
        return reply
    reply = ask(ctx, problems)
    problems = check_plan(ctx, reply)
    if problems:
        raise PlanningFailed("The plan broke the rules twice: " + "; ".join(problems[:5]))
    return reply


def get_state(conn: sqlite3.Connection) -> AppState:
    settings = db.get_settings(conn)
    goals = db.list_goals(conn)
    today = []
    if settings:
        today = [
            TodayTask(**t.model_dump(), goal_text=g.text)
            for g in goals
            for t in g.tasks
            if t.day == settings.current_day
        ]
    return AppState(settings=settings, goals=goals, today=today, max_goals=MAX_GOALS)


def set_daily_hours(conn: sqlite3.Connection, daily_hours: int, today: date) -> AppState:
    """Asked once on first open. The simulated current day starts on the real date."""
    if db.get_settings(conn):
        raise Refused("Daily hours are already set.")
    with db.transaction(conn):
        db.set_settings(conn, daily_hours, today)
    return get_state(conn)


def clarify_goal(conn: sqlite3.Connection, planner: Planner, body: ClarifyIn) -> ClarifyOut:
    """Step 1 of adding a goal: what the AI needs to know before it can plan."""
    settings = _check_can_add(conn, body.deadline)
    ctx = _new_goal_context(conn, settings, NewGoalRequest(text=body.text, deadline=body.deadline))
    questions = [q.strip() for q in planner.clarify(ctx).questions if q.strip()]
    return ClarifyOut(questions=questions[:MAX_QUESTIONS])


def add_goal(conn: sqlite3.Connection, planner: Planner, body: AddGoalIn) -> AddGoalImpossible | AddGoalAdded:
    """Step 2: SMART goal, verdict and system. Impossible goals are never saved. The new goal gets only the
    time the existing goals leave free; their plans don't change."""
    settings = _check_can_add(conn, body.deadline)
    request = NewGoalRequest(text=body.text, deadline=body.deadline, clarifications=body.clarifications)
    ctx = _new_goal_context(conn, settings, request)
    reply = plan_checked(planner, ctx, "new_goal")
    if reply.verdict == "impossible" or reply.new_goal is None:
        return AddGoalImpossible(message=reply.message, smart_goal=reply.smart_goal, assumptions=reply.assumptions)

    with db.transaction(conn):
        goal_id = db.insert_goal(
            conn,
            text=body.text,
            deadline=body.deadline,
            feasibility=reply.verdict,
            smart_goal=reply.smart_goal,
            clarifications=body.clarifications,
            breakdown=reply.new_goal.breakdown,
            milestones=reply.new_goal.milestones,
            created_on=settings.current_day,
        )
        db.insert_tasks(conn, goal_id, reply.new_goal.tasks)
    return AddGoalAdded(goal_id=goal_id, state=get_state(conn))


def delete_goal(conn: sqlite3.Connection, goal_id: int) -> AppState:
    """Remove a goal and its plan. Other goals keep their plans; the freed hours become buffer. No AI call."""
    with db.transaction(conn):
        if not db.delete_goal(conn, goal_id):
            raise NotFound("That goal no longer exists.")
    return get_state(conn)


def toggle_task(conn: sqlite3.Connection, task_id: int, done: bool) -> AppState:
    """Tick or untick a task. Only today's tasks: the past is settled, the future hasn't happened."""
    settings = _settings(conn)
    task = db.get_task(conn, task_id)
    if task is None:
        raise NotFound("That task no longer exists.")
    if task.day != settings.current_day:
        raise Refused("Only today's tasks can be ticked.")
    with db.transaction(conn):
        db.set_task_status(conn, task_id, "done" if done else "planned")
    return get_state(conn)


def next_day(conn: sqlite3.Connection, planner: Planner, body: NextDayIn) -> AppState:
    """Close today: save the updates, count unticked tasks as missed, re-plan the goals that need it
    from tomorrow on, and advance the day. Nothing to re-plan means no AI call. If planning fails,
    nothing changes: same day, same ticks, updates not saved."""
    settings = _settings(conn)
    today = settings.current_day
    tomorrow = today + timedelta(days=1)
    goals = db.goal_contexts(conn)
    updates = _clean_updates(body, {g.id for g in goals})

    # The picture the planner sees: today closed, today's updates added.
    reasons: dict[int, list[str]] = {}
    for g in goals:
        missed = False
        for t in g.tasks:
            if t.day == today and t.status == "planned":
                t.status = "missed"
                missed = True
        g.updates += [UpdateContext(day=today, text=text) for text in updates.get(g.id, [])]
        if g.deadline < tomorrow:
            continue  # its time is over; nothing left to plan
        why = []
        if missed:
            why.append("missed tasks today")
        if g.id in updates:
            why.append("new update from the user")
        if _detail_running_low(g, tomorrow):
            why.append(f"fewer than {DETAIL_DAYS // 2} days of daily tasks left: extend to {DETAIL_DAYS} days")
        if why:
            reasons[g.id] = why

    plans = []
    if reasons:
        ctx = _replan_context(settings, tomorrow, goals, reasons)
        plans = plan_checked(planner, ctx, "replan").goals

    with db.transaction(conn):
        for goal_id, texts in updates.items():
            for text in texts:
                db.insert_update(conn, goal_id, today, text)
        db.mark_missed(conn, today)
        for plan in plans:
            db.replace_future_tasks(
                conn, plan.goal_id, tomorrow, plan.tasks, plan.breakdown, plan.milestones, plan.change_note,
                plan.smart_goal,
            )
        db.set_current_day(conn, tomorrow)
    return get_state(conn)


def add_update(conn: sqlite3.Connection, planner: Planner, goal_id: int, text: str) -> AppState:
    """"Anything new?" on a goal's page: save the update and re-plan that goal from today on, right away."""
    settings = _settings(conn)
    today = settings.current_day
    goals = db.goal_contexts(conn)
    goal = next((g for g in goals if g.id == goal_id), None)
    if goal is None:
        raise NotFound("That goal no longer exists.")
    text = text.strip()
    if not text:
        raise Refused("Write what happened first.")
    if goal.deadline < today:
        raise Refused("This goal's deadline has passed, so there is nothing left to re-plan.")

    goal.updates.append(UpdateContext(day=today, text=text))
    ctx = _replan_context(settings, today, goals, {goal_id: ["new update from the user"]})
    plans = plan_checked(planner, ctx, "replan").goals
    with db.transaction(conn):
        db.insert_update(conn, goal_id, today, text)
        for plan in plans:
            db.replace_future_tasks(
                conn, plan.goal_id, today, plan.tasks, plan.breakdown, plan.milestones, plan.change_note,
                plan.smart_goal,
            )
    return get_state(conn)


def _clean_updates(body: NextDayIn, goal_ids: set[int]) -> dict[int, list[str]]:
    updates: dict[int, list[str]] = {}
    for u in body.updates:
        if u.goal_id not in goal_ids:
            raise NotFound("That goal no longer exists.")
        if u.text.strip():
            updates.setdefault(u.goal_id, []).append(u.text.strip())
    return updates


def _detail_running_low(goal: GoalContext, start: date) -> bool:
    """True when work remains (a milestone lies past the last task) but under half the detail window is planned."""
    last_task = max((t.day for t in goal.tasks), default=start - timedelta(days=1))
    last_milestone = max((m.target_day for m in goal.milestones), default=last_task)
    return last_milestone > last_task and (last_task - start).days + 1 < DETAIL_DAYS // 2


def _replan_context(
    settings: Settings, start: date, goals: list[GoalContext], reasons: dict[int, list[str]]
) -> PlanContext:
    return PlanContext(
        daily_hours=settings.daily_hours,
        today=start,
        start_day=start,
        goals=goals,
        replan_goal_ids=list(reasons),
        replan_reasons=reasons,
    )


def _settings(conn: sqlite3.Connection) -> Settings:
    settings = db.get_settings(conn)
    if settings is None:
        raise Refused("Set your daily hours first.")
    return settings


def _check_can_add(conn: sqlite3.Connection, deadline: date) -> Settings:
    settings = _settings(conn)
    if db.count_goals(conn) >= MAX_GOALS:
        raise Refused(f"You already have {MAX_GOALS} active goals. Focus on these first.")
    if deadline <= settings.current_day:
        raise Refused("The deadline needs to be after today.")
    return settings


def _new_goal_context(conn: sqlite3.Connection, settings: Settings, request: NewGoalRequest) -> PlanContext:
    return PlanContext(
        daily_hours=settings.daily_hours,
        today=settings.current_day,
        start_day=settings.current_day,
        goals=db.goal_contexts(conn),
        new_goal=request,
    )
