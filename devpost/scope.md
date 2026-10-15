---
doc: scope
status: approved
---

# Goal System (working name)

Type a goal and a deadline. An AI builds the system for you, turns it into today's checklist with done criteria, and keeps re-planning it when you fall behind, so you never have to.

## Goal vs. System (shared definition)
- **Goal:** the outcome. "Get a good job."
- **System:** the ongoing practices that get you there, and how much time each gets daily/weekly: researching companies, roles, and industries; shortlisting companies; practicing interviews and articulation; "the things I should be doing to land a good job."
- **Daily items:** what the system produces for today: a task, a done criterion, a time estimate, and why it matters.

## The Unique Kernel
**The tool owns the system, not you.** Creating the system is the step the learner procrastinates on, and adjusting it when life interrupts is where goals die. The AI does both:
- **Foresees what you can't.** It draws on what it knows about how goals like this usually go, including the long-lead steps you'd miss (e.g., reference letters take weeks and depend on other people).
- **Builds the system, not just a task list.** It defines the workstreams a goal needs and the time each deserves, then derives daily items from them.
- **Sizes the plan to the goal, not the deadline.** If the goal needs 10 days, the roadmap is 10 days, even with a month available.
- **Explains why each step matters.** Every daily item carries a reason connecting it to the goal. Knowing the next step isn't enough; the learner procrastinates when they lack "confidence in that step, that it would take me towards my goal."
- **Plans your goals together, and caps them.** The AI sees every active goal, so each plan is realistic given the others, and it combines work shared across goals where it can. A hard limit on active goals ("a couple") protects focus instead of letting the learner spread shallowly.
- **Adapts on a miss.** If you didn't hit today's criterion, it reshapes the system and upcoming days: rebalances time across workstreams, cuts what's unnecessary, compresses, or tightens. "That's the job of the tool. I don't want to think about that."

## Who It's For
First, the learner: someone with ambitious goals (a scholarship/MS application, 16 products by end of 2026, ₹1 crore by end of 2026) who starts strong, drifts after a few days, and notices a month later. Today they have no system; they believe "motivation is not enough" but put off building one. Meant to work for any goal and anyone with the same pattern.

## The Core Loop
1. **Morning:** open it, see today's checklist across active goals; for each item: what to get done, the done criterion, a time estimate, and **why this step moves the goal forward**. ("On day 7 I will know that I need to find 3 applications.")
2. **Evening:** mark whether the criterion was met.
3. **Missed it?** The roadmap adapts for the next day without the learner rethinking anything.

They come back because each day is already decided, and a miss doesn't break the plan.

## Inspiration & Identity
Not yet discussed. Should feel like the opposite of a guilt spiral: a missed day is just an input to re-planning.

## Why This Matters to the Learner
The demo goal is now the **scholarship to study abroad**: the goal behind the real, recent cost below, and "more specific… more realistic… more common." The 16-products goal is still "close to my heart," but it was replaced as the demo goal during `5-build` because it carries too much uncertainty to judge the tool by: no ideas yet, heavy personalization, and an unclear count.

A real, recent cost: a scholarship application dropped with 2 days left and nothing done, partly because reference letters can't be collected in 2 days. "I think that is because I didn't have any system for that goal." Building systems for unknown goals is hard for them, "but for an agent, it's easy because an agent has seen the internet... It can roughly project better than me."

## What "Working" Looks Like
In a one-minute demo:
1. Add goals with deadlines. Main demo goal: **getting a scholarship to study abroad**, with its real deadline. It tests long-lead steps that depend on other people (reference letters). *(Originally "Build 16 products by the end of 2026"; switched in `5-build`.)* Plus a second goal to show joint planning. Trying to add one past the cap is refused.
2. The AI produces a system for each goal (workstreams + time budgets) and a roadmap to completion sized to what the goal needs, with daily items, done criteria, time estimates, and a reason for each step. It's honest about feasibility and surfaces steps the learner wouldn't foresee.
3. Mark today done; move to the next day.
4. Mark a day **missed**, and watch the remaining roadmap reshape itself. **This is the "oh, that's cool" beat.**

## The POC Boundary
- A small, hard cap on active goals (exact number decided in PRD).
- Goals planned jointly: each roadmap accounts for the others; shared work is combined on a best-effort basis by the AI.
- Goal + deadline in → AI-generated system (workstreams + time budgets) and right-sized roadmap with daily items, done criteria, time estimates, and a "why" for each step.
- Daily check-off: done or missed.
- AI re-planning after a miss.
- A way to move to the next day in the demo without waiting real time.

## Later
- Dedicated logic for detecting and merging shared work across goals (beyond what the AI does in planning).
- Deploy a public hosted version; the PoC is clone-and-run with the user's own API key.
- Use by other people (accounts, sharing).
- Reminders and notifications.

## Explicitly Cut
- **Real-time waiting for days to pass:** impossible to demo; replaced by simulated day advance.
