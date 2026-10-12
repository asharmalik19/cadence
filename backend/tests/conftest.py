from datetime import date

import pytest

from backend.app.models import GoalContext, NewGoalRequest, PlanContext, TaskContext, Workstream

TODAY = date(2026, 10, 12)  # a Monday, so week maths is easy to read


@pytest.fixture
def new_goal_ctx() -> PlanContext:
    return PlanContext(
        weekly_hours=10,
        today=TODAY,
        start_day=TODAY,
        new_goal=NewGoalRequest(text="Write a short book", deadline=date(2026, 11, 30)),
    )


@pytest.fixture
def existing_goal() -> GoalContext:
    """Goal 1 with 3 hours a day planned for this week's Mon–Wed; Monday already ticked."""
    return GoalContext(
        id=1,
        text="Build 16 products",
        smart_goal="Ship 16 small apps by 31 Dec 2026",
        clarifications=[],
        deadline=date(2026, 12, 31),
        breakdown=[Workstream(name="Build", minutes_per_week=720, purpose="Ship products.")],
        tasks=[
            TaskContext(id=i + 1, day=date(2026, 10, 12 + i), title=f"Build {i}", minutes=180,
                        status="done" if i == 0 else "planned")
            for i in range(3)
        ],
    )
