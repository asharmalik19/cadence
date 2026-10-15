"""One real Gemini call. Costs money, so it only runs with RUN_LIVE=1."""

import os
from datetime import date

import pytest

from backend.app.models import NewGoalRequest, PlanContext
from backend.app.services import plan_checked

pytestmark = pytest.mark.skipif(os.getenv("RUN_LIVE") != "1", reason="set RUN_LIVE=1 to call Gemini")


def test_gemini_plans_16_products_goal():
    from backend.app.planner.gemini import GeminiPlanner

    today = date.today()
    ctx = PlanContext(
        daily_hours=8,
        today=today,
        start_day=today,
        new_goal=NewGoalRequest(text="Build 16 products by the end of 2026", deadline=date(2026, 12, 31)),
    )
    reply = plan_checked(GeminiPlanner(), ctx, "new_goal")
    assert reply.verdict in ("stretch", "comfortable")
    assert reply.new_goal and reply.new_goal.breakdown and reply.new_goal.tasks
