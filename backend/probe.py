"""Real Gemini calls for one goal: clarifying questions (you answer in the terminal), then the plan.

    uv run python -m backend.probe --deadline 2027-01-15
    uv run python -m backend.probe --goal "Build 16 products by the end of 2026" --deadline 2026-12-31

Every run is saved to data/probe-<model>.json with your answers, so you can compare fairly:

    uv run python -m backend.probe --replay data/probe-gemini-flash-latest.json --model gemini-pro-latest
"""

import argparse
import json
from datetime import date
from pathlib import Path

from .app import config
from .app.models import Clarification, NewGoalRequest, PlanContext
from .app.planner.base import PlanningFailed
from .app.planner.gemini import GeminiPlanner
from .app.services import plan_checked
from .app.validation import check_plan


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--goal", default="Get a scholarship to study abroad")
    p.add_argument("--deadline", help="YYYY-MM-DD (required unless --replay; with --replay, overrides the saved deadline)")
    p.add_argument("--hours", type=int, default=8, help="hours per day to plan for")
    p.add_argument("--days", type=int, default=14, help="how many days of tasks to print")
    p.add_argument("--replay", help="reuse the goal and answers saved by an earlier run")
    p.add_argument("--model", help="override GEMINI_MODEL for this run")
    args = p.parse_args()

    if args.replay:
        saved = json.loads(Path(args.replay).read_text())["context"]
        saved.setdefault("daily_hours", args.hours)  # runs saved before the daily limit had weekly_hours
        saved.pop("weekly_hours", None)
        ctx = PlanContext.model_validate(saved)
        if args.deadline:  # same answers, new deadline: like resubmitting after "impossible"
            ctx.new_goal.deadline = date.fromisoformat(args.deadline)
    elif args.deadline:
        today = date.today()
        ctx = PlanContext(
            daily_hours=args.hours,
            today=today,
            start_day=today,
            new_goal=NewGoalRequest(text=args.goal, deadline=date.fromisoformat(args.deadline)),
        )
    else:
        p.error("--deadline is required unless you use --replay")
    goal = ctx.new_goal

    planner = GeminiPlanner()
    if args.model:
        planner.model = args.model
    calls = []
    original = planner._call

    def counted(prompt, schema):  # record stats for every call, including a retry
        try:
            return original(prompt, schema)
        finally:
            calls.append(dict(planner.last_call))

    planner._call = counted
    print(f"{planner.model}: {goal.text!r} by {goal.deadline}, {ctx.daily_hours} h/day\n")
    try:
        if args.replay:
            print("Replaying saved answers:")
            for c in goal.clarifications:
                print(f"Q: {c.question}\nA: {c.answer}")
        else:
            questions = planner.clarify(ctx).questions
            print(f"  ({calls[-1]['seconds']} s)\n")
            goal.clarifications = [
                Clarification(question=q, answer=input(f"Q: {q}\nA: ").strip()) for q in questions
            ]
        print("\nPlanning…\n")
        reply = plan_checked(planner, ctx, "new_goal")
    except PlanningFailed as e:
        print(f"PLANNING FAILED: {e}\n\nCALLS")
        for c in calls:
            print("  " + json.dumps(c))
        raise SystemExit(1)

    print(f"SMART GOAL: {reply.smart_goal}")
    print("ASSUMPTIONS:" + "".join(f"\n  - {a}" for a in reply.assumptions) if reply.assumptions else "ASSUMPTIONS: none")
    print(f"\nVERDICT: {reply.verdict}\n{reply.message}\n")
    if reply.new_goal:
        g = reply.new_goal
        print("BREAKDOWN")
        for w in g.breakdown:
            print(f"  {w.name}: {w.minutes_per_week / 60:.1f} h/week. {w.purpose}")
        days = sorted({t.day for t in g.tasks})
        total = sum(t.minutes for t in g.tasks)
        print(f"\nPLAN: {len(g.tasks)} tasks over {len(days)} working days, {days[0]} → {days[-1]}, "
              f"{total / 60:.0f} h total\n")
        for d in days[: args.days]:
            print(f"{d:%a %d %b}")
            for t in (t for t in g.tasks if t.day == d):
                print(f"  • {t.title} ({t.minutes} min)\n    done when: {t.done_criterion}\n    why: {t.why}")
        print(f"\nRULE CHECK: {check_plan(ctx, reply) or 'no problems'}")

    print("\nCALLS")
    for c in calls:
        print("  " + json.dumps(c))
    config.DB_PATH.parent.mkdir(exist_ok=True)
    out = config.DB_PATH.parent / f"probe-{planner.model}.json"
    run = {"model": planner.model, "context": ctx.model_dump(mode="json"),
           "reply": reply.model_dump(mode="json"), "calls": calls}
    out.write_text(json.dumps(run, indent=1))
    print(f"\nFull run (your answers + reply) saved to {out.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
