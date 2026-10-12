"""The Planner interface. Services only talk to this, never to a specific AI."""

from typing import Protocol

from .. import config
from ..models import Clarify, NewGoalPlan, PlanContext, Replan


class PlanningFailed(Exception):
    """The AI could not produce a usable plan. Nothing should be saved."""


class Planner(Protocol):
    def clarify(self, ctx: PlanContext) -> Clarify: ...

    def plan_new_goal(self, ctx: PlanContext, problems: list[str] | None = None) -> NewGoalPlan: ...

    def replan(self, ctx: PlanContext, problems: list[str] | None = None) -> Replan: ...


def get_planner() -> Planner:
    """Pick the planner named by AI_PROVIDER in .env."""
    if config.AI_PROVIDER == "gemini":
        from .gemini import GeminiPlanner

        return GeminiPlanner()
    if config.AI_PROVIDER == "fake":
        from .fake import FakePlanner

        return FakePlanner()
    if config.AI_PROVIDER == "openai":
        from .openai import OpenAIPlanner

        return OpenAIPlanner()
    raise ValueError(f"Unknown AI_PROVIDER '{config.AI_PROVIDER}'. Use gemini, fake or openai.")
