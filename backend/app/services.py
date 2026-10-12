"""The rules for each action. Grows with each build step."""

from typing import Literal, overload

from .models import NewGoalPlan, PlanContext, Replan
from .planner.base import Planner, PlanningFailed
from .validation import check_plan


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
