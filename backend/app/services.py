"""The rules for each action. Each one loads what it needs, asks the planner if needed, checks the
reply, and saves everything in one transaction (or nothing)."""

import sqlite3
from datetime import date
from typing import Literal, overload

from . import db
from .models import (
    AddGoalAdded,
    AddGoalImpossible,
    AddGoalIn,
    AppState,
    ClarifyIn,
    ClarifyOut,
    NewGoalPlan,
    NewGoalRequest,
    PlanContext,
    Replan,
    Settings,
    TodayTask,
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
    """Step 2: SMART goal, verdict and system. Impossible goals are never saved."""
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
        for plan in reply.rework:  # other goals reshaped to make room
            db.replace_future_tasks(
                conn, plan.goal_id, ctx.start_day, plan.tasks, plan.breakdown, plan.milestones, plan.change_note
            )
    return AddGoalAdded(goal_id=goal_id, state=get_state(conn))


def delete_goal(conn: sqlite3.Connection, goal_id: int) -> AppState:
    """Remove a goal and its plan. Other goals keep their plans; the freed hours become buffer. No AI call."""
    with db.transaction(conn):
        if not db.delete_goal(conn, goal_id):
            raise NotFound("That goal no longer exists.")
    return get_state(conn)


def _check_can_add(conn: sqlite3.Connection, deadline: date) -> Settings:
    settings = db.get_settings(conn)
    if settings is None:
        raise Refused("Set your daily hours first.")
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
