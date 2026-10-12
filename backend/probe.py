"""Real Gemini calls for one goal: clarifying questions (you answer in the terminal), then the plan.

    uv run python -m backend.probe
    uv run python -m backend.probe --goal "Get an MS scholarship" --deadline 2027-01-15 --hours 50
"""

import argparse
import json
from datetime import date

from .app import config
from .app.models import Clarification, NewGoalRequest, PlanContext
from .app.planner.base import PlanningFailed
from .app.planner.gemini import GeminiPlanner
from .app.services import plan_checked
from .app.validation import check_plan


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--goal", default="Build 3 products/apps by the end of 2026")
    p.add_argument("--deadline", default="2026-12-31")
    p.add_argument("--hours", type=int, default=50)
    p.add_argument("--days", type=int, default=14, help="how many days of tasks to print")
    args = p.parse_args()

    today = date.today()
    ctx = PlanContext(
        weekly_hours=args.hours,
        today=today,
        start_day=today,
        new_goal=NewGoalRequest(text=args.goal, deadline=date.fromisoformat(args.deadline)),
    )

    planner = GeminiPlanner()
    calls = []
    original = planner._call

    def counted(prompt, schema):  # record stats for every call, including a retry
        try:
            return original(prompt, schema)
        finally:
            calls.append(dict(planner.last_call))

    planner._call = counted
    print(f"Asking {config.GEMINI_MODEL} about: {args.goal!r} by {args.deadline}, {args.hours} h/week…\n")
    try:
        questions = planner.clarify(ctx).questions
        print(f"  ({calls[-1]['seconds']} s)\n")
        answers = [Clarification(question=q, answer=input(f"Q: {q}\nA: ").strip()) for q in questions]
        ctx.new_goal.clarifications = answers
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
    out = config.DB_PATH.parent / "probe-reply.json"
    out.write_text(reply.model_dump_json(indent=1))
    print(f"\nFull reply saved to {out.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
