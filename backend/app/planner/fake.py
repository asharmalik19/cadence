"""Canned plans so tests (and offline runs) never call the AI or spend money."""

from datetime import timedelta

from ..models import Clarify, GoalPlan, NewGoalPlan, PlanContext, Replan, TaskPlan, Workstream
from .base import PlanningFailed


class FakePlanner:
    """Each call takes the next mode from `modes` (the last one repeats).

    Modes: "ok" (valid plan), "impossible", "broken" (breaks a validation rule), "fail" (raises).
    """

    def __init__(self, *modes: str, days: int = 10, minutes: int = 60) -> None:
        self.modes = list(modes) or ["ok"]
        self.days = days
        self.minutes = minutes
        self.calls: list[tuple[str, PlanContext, list[str] | None]] = []

    def _next_mode(self) -> str:
        return self.modes[min(len(self.calls) - 1, len(self.modes) - 1)]

    def clarify(self, ctx: PlanContext) -> Clarify:
        self.calls.append(("clarify", ctx, None))
        if self._next_mode() == "fail":
            raise PlanningFailed("Fake planner was told to fail")
        return Clarify(questions=["What does one finished unit of this goal look like?"])

    def plan_new_goal(self, ctx: PlanContext, problems: list[str] | None = None) -> NewGoalPlan:
        self.calls.append(("new_goal", ctx, problems))
        mode = self._next_mode()
        if mode == "fail":
            raise PlanningFailed("Fake planner was told to fail")
        if mode == "impossible":
            return NewGoalPlan(
                smart_goal=f"{ctx.new_goal.text} by {ctx.new_goal.deadline}",
                assumptions=["Each unit is full production work."],
                verdict="impossible",
                message="That deadline is too short for this goal.",
                new_goal=None,
                rework=[],
            )
        plan = self._goal_plan(ctx, 0, "")
        if mode == "broken":
            plan.tasks[0].why = ""
        return NewGoalPlan(
            smart_goal=f"{ctx.new_goal.text} by {ctx.new_goal.deadline}",
            assumptions=[],
            verdict="stretch",
            message="A focused plan.",
            new_goal=plan,
            rework=[],
        )

    def replan(self, ctx: PlanContext, problems: list[str] | None = None) -> Replan:
        self.calls.append(("replan", ctx, problems))
        mode = self._next_mode()
        if mode == "fail":
            raise PlanningFailed("Fake planner was told to fail")
        goals = [
            self._goal_plan(ctx, gid, "Shifted the remaining tasks back by one day; deadline still met.")
            for gid in ctx.replan_goal_ids
        ]
        if mode == "broken" and goals:
            goals[0].change_note = ""
        return Replan(goals=goals)

    def _goal_plan(self, ctx: PlanContext, goal_id: int, note: str) -> GoalPlan:
        days, d = [], ctx.start_day
        while len(days) < self.days:  # one task a day, Sundays free
            if d.weekday() != 6:
                days.append(d)
            d += timedelta(days=1)
        return GoalPlan(
            goal_id=goal_id,
            breakdown=[Workstream(name="Build", minutes_per_week=self.minutes * 7, purpose="Make progress.")],
            tasks=[
                TaskPlan(
                    day=day,
                    title=f"Work session {i + 1}",
                    done_criterion="Session finished",
                    minutes=self.minutes,
                    why="Steady daily work moves the goal forward.",
                )
                for i, day in enumerate(days)
            ],
            change_note=note,
        )
