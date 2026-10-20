"""FastAPI app: one route per action. Routes do no thinking; services hold the rules."""

import logging
import sqlite3
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import config, db, services
from .models import (
    AddGoalAdded,
    AddGoalImpossible,
    AddGoalIn,
    AppState,
    ClarifyIn,
    ClarifyOut,
    NextDayIn,
    SettingsIn,
    ToggleIn,
    UpdateIn,
)
from .planner.base import Planner, PlanningFailed, get_planner

log = logging.getLogger("sysplanner")


def create_app(conn: sqlite3.Connection | None = None, planner: Planner | None = None) -> FastAPI:
    """Tests pass their own connection and planner; a normal start opens the data file and .env planner."""
    app = FastAPI(title="SysPlanner")
    app.state.conn = conn or db.connect(config.DB_PATH)
    app.state.planner = planner
    if planner is None:
        try:
            app.state.planner = get_planner()
        except Exception as e:  # e.g. missing key: the app still opens, planning shows the calm error
            log.error("Planner unavailable: %s", e)

    def ask(request: Request) -> Planner:
        if request.app.state.planner is None:
            raise PlanningFailed("The AI planner isn't configured. Check GEMINI_API_KEY in .env.")
        return request.app.state.planner

    @app.exception_handler(services.Refused)
    async def refused(_: Request, e: services.Refused) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(e)})

    @app.exception_handler(services.NotFound)
    async def not_found(_: Request, e: services.NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(e)})

    @app.exception_handler(PlanningFailed)
    async def planning_failed(_: Request, e: PlanningFailed) -> JSONResponse:
        log.error("Planning failed: %s", e)
        return JSONResponse(status_code=502, content={"detail": "Planning didn't work this time. Nothing was changed."})

    @app.get("/api/state")
    def state(request: Request) -> AppState:
        return services.get_state(request.app.state.conn)

    @app.post("/api/settings")
    def settings(body: SettingsIn, request: Request) -> AppState:
        return services.set_daily_hours(request.app.state.conn, body.daily_hours, date.today())

    @app.post("/api/goals/clarify")
    def clarify(body: ClarifyIn, request: Request) -> ClarifyOut:
        return services.clarify_goal(request.app.state.conn, ask(request), body)

    @app.post("/api/goals")
    def add_goal(body: AddGoalIn, request: Request) -> AddGoalImpossible | AddGoalAdded:
        return services.add_goal(request.app.state.conn, ask(request), body)

    @app.delete("/api/goals/{goal_id}")
    def delete_goal(goal_id: int, request: Request) -> AppState:
        return services.delete_goal(request.app.state.conn, goal_id)

    @app.post("/api/goals/{goal_id}/updates")
    def add_update(goal_id: int, body: UpdateIn, request: Request) -> AppState:
        return services.add_update(request.app.state.conn, ask(request), goal_id, body.text)

    @app.post("/api/tasks/{task_id}/toggle")
    def toggle(task_id: int, body: ToggleIn, request: Request) -> AppState:
        return services.toggle_task(request.app.state.conn, task_id, body.done)

    @app.post("/api/day/next")
    def next_day(body: NextDayIn, request: Request) -> AppState:
        # The planner is only needed if something must be re-planned, so a missing key doesn't block a quiet day.
        planner = request.app.state.planner or _Unavailable()
        return services.next_day(request.app.state.conn, planner, body)

    return app


class _Unavailable:
    """Stands in for a missing planner; fails calmly only if a re-plan is actually needed."""

    def __getattr__(self, _: str):
        raise PlanningFailed("The AI planner isn't configured. Check GEMINI_API_KEY in .env.")


app = create_app()
