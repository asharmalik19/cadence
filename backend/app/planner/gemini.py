"""The real planner: Gemini with JSON structured output."""

import logging
import time

from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from .. import config
from ..models import Clarify, NewGoalPlan, PlanContext, Replan
from .base import PlanningFailed
from .prompts import SYSTEM, build_prompt

log = logging.getLogger("sysplanner.gemini")


class GeminiPlanner:
    def __init__(self) -> None:
        if not config.GEMINI_API_KEY:
            raise PlanningFailed("GEMINI_API_KEY is not set in .env")
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = config.GEMINI_MODEL
        self.last_call: dict = {}  # stats of the most recent call, for the probe and logs

    def clarify(self, ctx: PlanContext) -> Clarify:
        return self._call(build_prompt(ctx, "clarify", None), Clarify)

    def plan_new_goal(self, ctx: PlanContext, problems: list[str] | None = None) -> NewGoalPlan:
        return self._call(build_prompt(ctx, "new_goal", problems), NewGoalPlan)

    def replan(self, ctx: PlanContext, problems: list[str] | None = None) -> Replan:
        return self._call(build_prompt(ctx, "replan", problems), Replan)

    def _call[T: BaseModel](self, prompt: str, schema: type[T]) -> T:
        started = time.monotonic()
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM,
                    response_mime_type="application/json",
                    response_json_schema=schema.model_json_schema(),
                    max_output_tokens=65536,
                ),
            )
        except Exception as e:  # network, auth, quota: all mean "planning failed"
            raise PlanningFailed(f"Gemini call failed: {e}") from e

        usage = response.usage_metadata
        self.last_call = {
            "model": self.model,
            "seconds": round(time.monotonic() - started, 1),
            "reply_chars": len(response.text or ""),
            "prompt_tokens": usage.prompt_token_count if usage else None,
            "output_tokens": usage.candidates_token_count if usage else None,
            "thinking_tokens": usage.thoughts_token_count if usage else None,
            "total_tokens": usage.total_token_count if usage else None,
        }
        log.warning("Gemini call: %s", self.last_call)

        try:
            return schema.model_validate_json(response.text or "")
        except ValidationError as e:
            raise PlanningFailed(f"Gemini reply did not match the {schema.__name__} shape: {e}") from e
