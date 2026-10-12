"""Empty slot for an OpenAI planner. Not part of the POC."""

from ..models import Clarify, NewGoalPlan, PlanContext, Replan


class OpenAIPlanner:
    def clarify(self, ctx: PlanContext) -> Clarify:
        raise NotImplementedError("OpenAI planner not built yet")

    def plan_new_goal(self, ctx: PlanContext, problems: list[str] | None = None) -> NewGoalPlan:
        raise NotImplementedError("OpenAI planner not built yet")

    def replan(self, ctx: PlanContext, problems: list[str] | None = None) -> Replan:
        raise NotImplementedError("OpenAI planner not built yet")
