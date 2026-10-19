import os
import tempfile
from datetime import date

# Before anything imports the app: tests never touch data/sysplanner.db or call the real AI.
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "import-time.db")
os.environ["AI_PROVIDER"] = "fake"

import pytest
from fastapi.testclient import TestClient

from backend.app import db
from backend.app.main import create_app
from backend.app.planner.fake import FakePlanner

from backend.app.models import GoalContext, Milestone, NewGoalRequest, PlanContext, TaskContext, Workstream

SHIP = Milestone(name="Ship", target_day=date(2026, 12, 31), reached_when="Shipped.")

TODAY = date(2026, 10, 12)


@pytest.fixture
def new_goal_ctx() -> PlanContext:
    return PlanContext(
        daily_hours=4,
        today=TODAY,
        start_day=TODAY,
        new_goal=NewGoalRequest(text="Write a short book", deadline=date(2026, 11, 30)),
    )


@pytest.fixture
def existing_goal() -> GoalContext:
    """Goal 1 with 3 hours a day planned for 12–14 Oct; the 12th already ticked."""
    return GoalContext(
        id=1,
        text="Build 16 products",
        smart_goal="Ship 16 small apps by 31 Dec 2026",
        clarifications=[],
        deadline=date(2026, 12, 31),
        breakdown=[Workstream(name="Build", minutes_per_week=720, purpose="Ship products.")],
        milestones=[SHIP],
        tasks=[
            TaskContext(id=i + 1, day=date(2026, 10, 12 + i), kind="concrete", milestone="Ship", title=f"Build {i}", minutes=180,
                        status="done" if i == 0 else "planned")
            for i in range(3)
        ],
    )


@pytest.fixture
def make_client(tmp_path):
    """make_client(*modes) -> (TestClient, FakePlanner) on a fresh temp database."""

    def make(*modes, **kw):
        planner = FakePlanner(*modes, **kw)
        conn = db.connect(tmp_path / "test.db")
        return TestClient(create_app(conn, planner)), planner

    return make


@pytest.fixture
def client(make_client):
    c, _ = make_client()
    return c
