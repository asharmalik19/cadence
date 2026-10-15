"""Validation rules and the retry-once behaviour (spec: Validation Rules in Detail)."""

from datetime import date, timedelta

import pytest

from backend.app.models import GoalPlan, Replan, TaskPlan
from backend.app.planner.base import PlanningFailed
from backend.app.planner.fake import FakePlanner
from backend.app.services import plan_checked
from backend.app.validation import check_plan


def test_valid_fake_plan_has_no_problems(new_goal_ctx):
    assert check_plan(new_goal_ctx, FakePlanner().plan_new_goal(new_goal_ctx)) == []


def test_impossible_verdict_needs_only_a_message(new_goal_ctx):
    assert check_plan(new_goal_ctx, FakePlanner("impossible").plan_new_goal(new_goal_ctx)) == []


def test_every_task_has_done_criterion_minutes_and_why(new_goal_ctx):
    reply = FakePlanner().plan_new_goal(new_goal_ctx)
    reply.new_goal.tasks[0].why = " "
    reply.new_goal.tasks[1].done_criterion = ""
    reply.new_goal.tasks[2].minutes = 0
    problems = check_plan(new_goal_ctx, reply)
    assert any("no why" in p for p in problems)
    assert any("no done criterion" in p for p in problems)
    assert any("minutes greater than 0" in p for p in problems)


def test_tasks_must_sit_between_start_day_and_deadline(new_goal_ctx):
    reply = FakePlanner().plan_new_goal(new_goal_ctx)
    reply.new_goal.tasks[0].day = new_goal_ctx.start_day - timedelta(days=1)
    reply.new_goal.tasks[1].day = date(2026, 12, 1)
    problems = check_plan(new_goal_ctx, reply)
    assert any("before the start day" in p for p in problems)
    assert any("after the deadline" in p for p in problems)


def test_daily_limit_is_checked_per_day(new_goal_ctx):
    # 4 h/day limit; 300 min on one day is over 240.
    reply = FakePlanner(minutes=300, days=1).plan_new_goal(new_goal_ctx)
    problems = check_plan(new_goal_ctx, reply)
    assert problems == ["2026-10-12 has 300 minutes of tasks across all goals, over the daily limit of 240."]


def test_every_week_keeps_a_free_day(new_goal_ctx):
    # Fill Monday 12 Oct to Sunday 18 Oct.
    reply = FakePlanner(days=7).plan_new_goal(new_goal_ctx)
    for i, t in enumerate(reply.new_goal.tasks):
        t.day = new_goal_ctx.start_day + timedelta(days=i)
    assert check_plan(new_goal_ctx, reply) == [
        "The week starting 2026-10-12 has tasks on all 7 days; leave at least one day free."
    ]


def test_free_day_can_be_any_day_of_the_week(new_goal_ctx):
    reply = FakePlanner(days=6).plan_new_goal(new_goal_ctx)
    for i, t in enumerate(reply.new_goal.tasks):  # Mon–Wed, then Fri–Sun: Thursday free
        t.day = new_goal_ctx.start_day + timedelta(days=i if i < 3 else i + 1)
    assert check_plan(new_goal_ctx, reply) == []


def test_uneven_days_are_fine_within_the_limit(new_goal_ctx):
    reply = FakePlanner(days=3).plan_new_goal(new_goal_ctx)
    reply.new_goal.tasks[0].minutes = 240
    reply.new_goal.tasks[1].minutes = 30
    assert check_plan(new_goal_ctx, reply) == []


def test_budget_counts_other_goals_tasks(new_goal_ctx, existing_goal):
    # Goal 1 has 180 min on the 12th. Adding 61 min of new work that day goes over 240.
    new_goal_ctx.goals = [existing_goal]
    reply = FakePlanner(minutes=61, days=1).plan_new_goal(new_goal_ctx)
    assert any("over the daily limit" in p for p in check_plan(new_goal_ctx, reply))


def test_rework_replaces_planned_tasks_but_keeps_ticked_ones(new_goal_ctx, existing_goal):
    # Rework goal 1 down to nothing new: only the 12th's ticked 180 min stays; plus 60 min new = fine.
    new_goal_ctx.goals = [existing_goal]
    reply = FakePlanner(days=1).plan_new_goal(new_goal_ctx)
    reply.rework = [GoalPlan(goal_id=1, breakdown=existing_goal.breakdown, tasks=[], change_note="Paused.")]
    assert check_plan(new_goal_ctx, reply) == []


def test_changed_goal_needs_a_note_and_must_exist(new_goal_ctx, existing_goal):
    new_goal_ctx.goals = [existing_goal]
    reply = FakePlanner(days=1).plan_new_goal(new_goal_ctx)
    reply.rework = [
        GoalPlan(goal_id=1, breakdown=[], tasks=[], change_note=""),
        GoalPlan(goal_id=99, breakdown=[], tasks=[], change_note="x"),
    ]
    problems = check_plan(new_goal_ctx, reply)
    assert "Goal 1 changed but has no change_note." in problems
    assert "Goal 99 does not exist." in problems


def test_replan_must_cover_exactly_the_goals_with_misses(new_goal_ctx, existing_goal):
    ctx = new_goal_ctx.model_copy(update={"new_goal": None, "goals": [existing_goal], "replan_goal_ids": [1]})
    assert check_plan(ctx, Replan(goals=[])) == ["Goal 1 had missed tasks and must be re-planned."]


def test_broken_reply_gets_one_retry_with_the_problems_listed(new_goal_ctx):
    planner = FakePlanner("broken", "ok")
    reply = plan_checked(planner, new_goal_ctx, "new_goal")
    assert reply.new_goal is not None
    assert len(planner.calls) == 2
    assert planner.calls[0][2] is None
    assert any("no why" in p for p in planner.calls[1][2])


def test_two_broken_replies_raise_planning_failed(new_goal_ctx):
    planner = FakePlanner("broken")
    with pytest.raises(PlanningFailed):
        plan_checked(planner, new_goal_ctx, "new_goal")
    assert len(planner.calls) == 2


def test_empty_smart_goal_is_a_problem(new_goal_ctx):
    reply = FakePlanner().plan_new_goal(new_goal_ctx)
    reply.smart_goal = ""
    assert "smart_goal must not be empty." in check_plan(new_goal_ctx, reply)
