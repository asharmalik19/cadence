---
doc: prd
status: approved
---

# SysPlanner (working name) — Product Requirements

A single-user web app for someone with ambitious, multi-week goals who drifts without a system. You enter a goal and a deadline, the AI builds the system and a right-sized day-by-day plan, you tick off what you get done, and the plan reshapes itself when you don't.
Source: `scope.md > The Unique Kernel`, `scope.md > Who It's For`. "SysPlanner" is a working name; the learner wants to revisit it once the project is ready (see **Open Questions**).

## The Core Journey
Source: `scope.md > The Core Loop`, `scope.md > What "Working" Looks Like`.

1. **First open.** Before anything else, the user enters how many hours a day they want to plan for, weekends included (e.g. 8). This is the time budget all goals share. It can deliberately be less than the hours they really have: the gap is their buffer, and a tight limit forces the plan to prioritize.
   Then the screen is empty apart from an **Add goal** button and the (empty) **Active Goals** panel on the left.
2. **Add a goal.** Clicking **Add goal** asks only for the goal, in plain words (e.g. "Get a scholarship to study abroad for a master's"). The first question that follows is always **"By when?"**, answered with a date.
3. **Clarify, make it SMART, check feasibility.** The user doesn't have to write a perfect goal. The AI first asks only what it needs to plan (usually 2–4 questions tailored to this goal, e.g. "What size is one product?", "How will you build them?"; none if the goal is already specific). The user answers once. The AI then restates the goal as a **SMART goal** (specific, measurable, achievable, time-bound) and judges it against the deadline.
   - **Impossible:** it says clearly why, including what it assumed, and lets the user change the deadline or their answers and try again. This repeats until it's realistic. The goal is not added until then.
   - **Stretch or comfortable:** it goes ahead.
4. **System is built.** The goal appears in **Active Goals**. Its system has two parts: a **breakdown** (the kinds of ongoing work the goal needs and how much time each gets) and a **day-by-day plan** to completion, sized to what the goal needs rather than stretched to the deadline.
5. **More goals.** The user adds up to **3** active goals, one at a time. Each new goal is planned into the time the existing goals leave free, so all plans together fit the daily and weekly budget; existing plans don't change. A goal that doesn't fit the time left is refused with how much time is free. Trying to add a 4th is refused.
6. **Today.** On a normal open, the main area shows **Today**: every task due today across all active goals. Each task shows what to do, its done criterion, a time estimate, and why it moves the goal forward.
7. **Mark wins.** During or at the end of the day, the user ticks tasks they finished. They never mark a task as missed.
8. **Next day → review.** Clicking **Next day** first opens a **review of today** listing every task still unticked: "Tick any you actually did." The user ticks any they forgot, and can write an optional **update** per goal: anything that happened or changed ("DAAD deadline is 30 Nov", "dropping Dubai").
9. **Re-plan.** Whatever is still unticked counts as missed. The AI re-plans each goal with a miss or a new update from the next day onward, treating every update as fact. That can be a simple one-day shift or a deeper reshape (rebalance, cut, compress), whichever the goal needs.
10. **See what changed.** Each re-planned goal shows a **Last change** note saying exactly what the AI did, e.g. "Shifted Days 6–14 back by one day; deadline still met."
11. **Repeat.** The main area now shows the new day's Today list. The loop continues.

**Success (the demo):** add the scholarship goal plus two more, get refused on a 4th, see a believable breakdown and plan with a "why" on every task, tick some tasks, leave one unticked, click Next day, and watch the **Last change** note explain how the plan reshaped.

## Screens and Layout

One main screen with a persistent left panel. The main area switches between views.

- **Active Goals panel (left, always visible).** Lists active goals (max 3) and holds the **Add goal** button. Clicking a goal opens its **Goal view**. There is also a way back to **Today**.
- **Today view (main area, default).** Today's tasks from all active goals, each with a tick box. Holds the **Next day** control.
- **Goal view (main area).** One goal's full system: the goal, its **SMART version** and deadline, the **breakdown**, the **day-by-day plan**, and the **Last change** note.
- **Daily hours (first-open step).** Asked once, before the first goal: hours to plan for per day.
- **Add goal (form/dialog).** Goal text, then "By when?" (deadline), then the AI's clarifying questions with answer boxes, then the feasibility response (impossible → change deadline or answers and retry).
- **End-of-day review (dialog/step).** Shown after clicking **Next day**: the unticked tasks with tick boxes and a confirm action that triggers the re-plan.
- **Empty state.** Before any goal exists, the main area is a clear prompt to add your first goal.

## Look and Feel

Reference: screenshots of a third-party app ("Yggdrasil") the learner shared **for colors, contrast and vibe only**. Do **not** reuse its name, tree logo, branding or layouts. This app's UI must come from its own function.

- **Colors:** very dark forest-green background; slightly lighter green cards/surfaces; muted sage green for secondary labels and calm accents; gold for highlights (active item, key dates, emphasis); off-white primary text. High contrast between text and background.
- **Typography character:** an elegant serif for page titles and headings; a clean sans-serif for body text; small labels in spaced-out capitals.
- **Style:** quiet, reflective, premium. Rounded cards with thin, subtle borders; generous spacing; left-sidebar navigation with a clear gold marker on the active item.
- **Tone:** never guilt-inducing. A missed day is just an input to re-planning (`scope.md > Inspiration & Identity`). Avoid red failure states, streak-shaming or loud alerts.

## Features and Behavior

### Daily Time Budget
Source: `scope.md > The Unique Kernel` (plans goals together).

- On first open, before any goal can be added, the user enters the hours per day to plan for (every day, weekends included).
- All active goals' tasks on any single day together must fit within that daily limit. The AI treats it as real: if work doesn't fit, it prioritizes and cuts what matters least instead of squeezing.
- **The whole plan fits the week too, not just the next two weeks.** The weekly budget is the daily hours × 6 working days (e.g. 6 h → 36 h). All goals' breakdowns (hours per week out to their deadlines) together must stay within it.
- Days don't have to be even. The AI may give one goal a deep day and another goal the next day, grouping related work so the user can focus.
- **One free day a week.** Every Monday–Sunday week keeps at least one day with no planned tasks, for admin, chores and rest (e.g. 8 h × 6 days = 48 planned hours). It isn't a fixed weekday: the AI picks where it hurts least, and the user moves it with an update ("admin on Thursday this week").
- **Resilience to the unplanned.** A coffee with a friend or a lost afternoon needs no special handling: the daily limit sits below the user's real hours as a buffer; an unfinished task is simply left unticked and re-planned at Next day; anything bigger is an update.
  - [ ] On first open, the hours question appears before **Add goal** is usable.
  - [ ] No day's combined time estimates across all active goals exceed the daily limit.
  - [ ] All active goals' breakdowns together never exceed the weekly budget (daily hours × 6).
  - [ ] Every week of the plan has at least one day with no tasks from any goal, and the Goal view shows it as a free day.
- *(Assumption: set once and not editable in the POC.)*

### Adding a Goal
Source: `scope.md > The POC Boundary`.

- Clicking **Add goal** asks for the goal in plain words. The next screen asks **"By when?"** with a date picker; the deadline is required. The AI writes its clarifying questions only after it knows the deadline, because the deadline changes which questions matter (weeks away: what's already done; a year away: which direction).
- **Clarifying questions:** the AI asks only what it needs to plan this goal (none if it's already specific). The user answers once in the dialog.
- **SMART goal:** the AI restates the goal in SMART form from the goal, answers and deadline. It is shown in the Goal view.
- The AI checks feasibility before building anything, and an impossible verdict says what it assumed.
  - [ ] "Get a scholarship to study abroad" gets clarifying questions (e.g. which level and field, which countries or programs, what is already prepared) before any verdict.
  - [ ] The AI never invents choices the user hasn't made (which scholarships, universities or ideas); if one is undecided, the plan includes the work to decide it by a date.
  - [ ] The Goal view shows the SMART version of the goal.
  - [ ] An obviously impossible goal (e.g. "Get a scholarship abroad in 3 days") gets a clear message that the deadline is too short, with what the AI assumed, and the user can change the deadline or their answers.
  - [ ] A new deadline that is still impossible gets the same message again.
  - [ ] The goal does not appear in **Active Goals** until a realistic deadline is accepted.
  - [ ] A stretch goal (hard but doable) is planned normally.

### Goal Cap
Source: `scope.md > The Unique Kernel` ("caps them").

- Maximum **3** active goals.
  - [ ] With 3 goals active, trying to add a 4th is refused with a plain message. No goal is added.
  - [ ] A goal can be deleted with the small trash icon next to it in the Active Goals panel (gold on hover), after an inline "can't be undone" confirm. Its tasks and updates go with it, which frees a slot. Other goals keep their plans; the freed hours become buffer.
  - [ ] There is no way to finish or archive a goal in the POC.

### The System (Breakdown + Day-by-Day Plan)
Source: `scope.md > Goal vs. System`, `scope.md > The Unique Kernel`.

- **Breakdown:** the ongoing kinds of work the goal needs and the time each gets (e.g. for a scholarship: Research and shortlist programs 3 hrs/week, Essays 5 hrs/week, References and documents 1 hr/week). It's shown on screen because it gives the user confidence in the plan.
- **Milestones:** dated checkpoints from now to the goal (e.g. "Choose 2–3 countries", "References secured", "Applications submitted"). They are the backbone of the plan and are shown on the Goal view.
- **Day-by-day plan, two weeks ahead:** daily tasks only for the next 14 days. Beyond that, the milestones guide the plan, and daily steps are filled in as the user makes decisions and shares updates ("rolling-wave" planning). Each task has what to do, a criterion, a time estimate, a why, and the milestone it works toward.
- **Two kinds of step:**
  - **Concrete:** a clear output in a predictable time (send the reference emails, upload documents). Its criterion is the finished output.
  - **Explore:** one session on an open question that can't be settled in one sitting (choosing countries or scholarships, reflecting on what you want). An open question is spread over several explore sessions on different days and ends in a dated "decide" milestone. An explore step's criterion is the **progress** it leaves (notes, a comparison, a conversation), never that the question is settled.
- The plan is sized to the goal, not the deadline: if the goal needs 10 days, the plan is 10 days.
- The AI surfaces long-lead or easy-to-miss steps (e.g. things that depend on other people).
- Plans are made jointly: each goal's plan accounts for the other active goals, and shared work is combined where the AI sees it (best effort).
- **A new goal gets only the time left over.** Existing goals keep their plans when a goal is added; the new goal is planned into the daily and weekly time they leave free. If it can't reach its deadline in that time, it is refused as impossible, and the message says how much time is left and what would free more (a later deadline, or deleting a goal).
  - [ ] Adding a goal never changes an existing goal's plan.
  - [ ] A goal that doesn't fit the time left is refused with how many hours a week are free.
  - [ ] Opening a goal shows its milestones, its breakdown (work types with time amounts) and its day-by-day plan.
  - [ ] Daily tasks run at most 14 days ahead; later work appears only as milestones.
  - [ ] An open question like "which countries?" appears as several explore sessions with progress criteria, followed by a dated decide milestone, not as one timed task.
  - [ ] Every task in the plan has a done criterion, a time estimate and a why that connects it to the goal.
  - [ ] For the scholarship goal, the plan surfaces long-lead steps that depend on other people (e.g. asking for reference letters) early, weeks before they are needed.
  - [ ] After adding a second goal, any change to the first goal's plan is described in its **Last change** note.

### Today and Marking Done
Source: `scope.md > The Core Loop` (Morning, Evening).

- **Today** is the default view and lists today's tasks from all active goals, each labelled with its goal.
- The user only ever ticks tasks as **done**. An unticked task is treated as not done.
  - [ ] Opening the app with goals shows Today's tasks across all active goals.
  - [ ] Ticking a task visibly marks it done.
  - [ ] There is no "mark missed" control.

### Next Day, Review and Re-plan
Source: `scope.md > The Core Loop` (Missed it?), `scope.md > The POC Boundary` (simulated day advance).

- **Next day** simulates the passing of a day, so the demo doesn't wait for real time.
- Before advancing, an **end-of-day review** lists all still-unticked tasks so the user can tick any they did but forgot. This protects against needless re-plans.
- After confirming, every task still unticked counts as missed, and the AI re-plans each affected goal from the next day on. A goal with no missed tasks is not re-planned.
- The AI decides how much change is needed: a simple shift is a valid outcome.
- **Fast forward.** Days away happen. When the app's day is behind the real date, Today shows "You're N days behind" with a **Fast forward** button. It opens the same review for every day from the app's day up to a chosen date (default: today; any later date works, which also serves the demo): unticked tasks grouped by day, plus an optional update per goal ("was sick", "travelling"). Confirming counts what's still unticked as missed and re-plans the affected goals once, from the chosen date, inside the daily hours and weekly budget. The weekly free day is kept: a gap is absorbed by re-planning, and if a deadline can't be met any more, the Last change note says so and the user decides (later deadline, smaller goal).
  - [ ] Clicking **Next day** with unticked tasks shows the review before anything changes.
  - [ ] Ticking a task in the review prevents it from triggering a re-plan.
  - [ ] After confirming, the main area shows the new day's tasks.
  - [ ] A goal's plan changes after a missed task, even if the change is only a shift.
  - [ ] With the app's day behind the real date, Today shows how many days behind it is and a Fast forward button.
  - [ ] Fast forward over several days lists every unticked task from those days in one review, makes one re-plan, and lands on the chosen date.
  - [ ] Tasks ticked in that review count as done; every week after a fast forward still has a free day.

### Updates (What Happened)
Source: `scope.md > The Unique Kernel` (adapts), decided during `5-build`.

- The first plan is a well-informed first draft. As the user works through it, facts appear and minds change: a deadline turns out different, a requirement doesn't apply, a recommender says no, the user drops a country. The user tells the tool; the tool re-plans.
- Two places to write an update:
  - **Goal view, any time:** an "Anything new?" box. Submitting re-plans that goal from today onward right away (ticked tasks stay).
  - **End-of-day review:** an optional update per goal, applied in the same re-plan as that day's misses.
- Updates are saved with the goal and sent with every later plan and re-plan, like the clarifying answers. They are notes, not edits: the user never changes tasks directly (see **Non-Goals**).
- A re-plan may also rewrite the **SMART goal** when an update changes the goal itself (e.g. "only Germany now"), and the **Last change** note says so.
  - [ ] Writing "The DAAD deadline is 30 Nov" on the scholarship goal re-plans it so its tasks lead to submitting by 30 Nov, and the Last change note mentions the new deadline fact.
  - [ ] An update written in the end-of-day review re-plans that goal even if it had no missed tasks.
  - [ ] Updates stay visible on the goal's page, and later re-plans still respect them.

### Last Change Note
- Each goal shows a **Last change** note describing what the most recent re-plan did (after a miss or an update), in plain words, whether it was a simple shift or a deeper reshape.
  - [ ] After a re-plan, the affected goal's **Last change** note says what changed (which days or tasks moved, were cut, compressed or rebalanced) and whether the deadline is still met.
  - [ ] A goal that has never been re-planned shows no last-change content (or an equivalent "no changes yet").

## States and Boundaries

- **First use / empty:** daily hours asked first; then no goals; a prompt plus **Add goal** button; Active Goals panel empty.
- **Planning in progress:** while the AI builds or re-plans a system, the user sees that it's working. *(Assumption: some visible working indicator; wording/style left to spec.)*
- **Impossible deadline:** clear message with the AI's assumptions, plus a way to change the deadline or answers, repeating until realistic (see **Adding a Goal**).
- **At cap:** a 4th goal is refused.
- **Review with nothing unticked:** the review still opens, showing only the optional update boxes. With no misses and no updates, confirming advances the day with no re-plan and no AI call.
- **AI unavailable or fails:** *(Assumption: show a calm error saying planning failed, with a retry. Nothing is added or changed.)*

## Product Decisions

- **"System" = everything for a goal:** breakdown plus day-by-day plan. Breakdown is visible because it builds confidence in the steps.
- **Today across all goals is the home view; clicking a goal opens its system.** Carried from the scope's morning loop.
- **Users only mark wins.** No "mark missed": unticked means not done, which keeps it guilt-free.
- **End-of-day review on Next day instead of notifications.** It catches forgotten ticks before re-planning. Notifications stay in Later (hard to demo, and out of scope).
- **Re-plans are always visible, even simple shifts,** through a **Last change** note per goal. Chosen over a re-plan counter, which only shows that a change happened, not what changed.
- **Cap of 3 active goals,** a plain refusal beyond that, and no finish/archive in the POC. Based on focus advice (1–3 goals) and the scope's "a couple."
- **Goals can be deleted.** Added during `5-build`: using the app for a real goal, the learner had to delete the whole data file twice to start over, and with the cap a wrong goal would block a slot for good. Delete only, with an inline confirm and no undo. No AI call: other goals keep their plans until their next re-plan.
- **Impossible goals are never added.** The user changes the deadline or answers until it's realistic. Stretch goals are fine.
- **Not every step fits a time box.** Reviewing the first in-app plan, the learner pointed out that "choose your countries in 2 hours" isn't realistic: some steps are open questions that take days of research and reflection. Plans now use milestones as the backbone, two kinds of step (concrete vs. explore, with progress criteria), and detail only two weeks ahead. A fully loose plan was considered and rejected: there is still a clear list every day, because a vague next step is where drift starts.
- **The tool makes the goal SMART, not the user.** A one-sentence goal was too ambiguous: in the first real AI call, "Build 16 products by the end of 2026" was judged impossible because the AI assumed full production software. The user supplies the goal and deadline (Specific, with the AI's help, and Time-bound); the AI asks what it's missing, writes the SMART version, judges Achievable, and makes it Measurable through done criteria. The answers and SMART goal are saved with the goal and used in every later plan and re-plan.
- **One daily hours number, entered at first open before any goal,** so the AI plans all goals against a known time limit. Changed from weekly during `5-build`: a weekly limit allowed lopsided days, and the learner plans day by day, deliberately below their real hours ("plan as if you have 40 hours") to keep a buffer and force priorities. Evenness is not required: deep days on one goal are preferred over a little of everything.
- **A new goal gets the leftover time; existing plans don't change on add.** Changed during `5-build` (it was "adding a goal reworks existing plans"): the first live three-goal run showed the AI never reworked anything, and nothing checked the long-term plan, so three goals' breakdowns added up to 50 h a week against a 36 h budget. The learner chose leftover time plus a code-checked weekly budget: simple, predictable, and the total never exceeds their time. Smarter rebalancing (by deadline or by a priority the user picks) waits until real use shows it's needed.
- **No bulk add.** Adding one at a time is simpler, and bulk would complicate the feasibility loop.
- **Working name: SysPlanner,** to be revisited once the project is ready. Noted concerns: "sys" can read as IT jargon, and "planner" undersells that the tool does the planning.

## What We're Building
- Add goal with required deadline; AI clarifying questions; AI-written SMART goal; feasibility check with the impossible → change and retry loop.
- AI-built system per goal: breakdown with time amounts and a day-by-day plan (done criterion, time estimate, why per task), sized to the goal and planned jointly across active goals.
- Active Goals panel (max 3) with a refusal on the 4th and a delete icon per goal.
- Today view across goals with done-ticking.
- Next day control, end-of-day review, AI re-plan of affected goals.
- Updates ("what happened") from the Goal view and the end-of-day review, saved with the goal and driving re-plans.
- Last change note per goal.
- The dark-green/sage/gold look described above.

## Deferred From the POC
- **Completing or archiving goals:** delete covers freeing a slot.
- **Notifications and reminders:** replaced by the end-of-day review; `scope.md > Later`.
- **Dedicated shared-work merging logic:** the AI does it best effort; `scope.md > Later`.
- **Accounts, other users, sharing:** single user; `scope.md > Later`.
- **Public hosted version:** clone-and-run with your own API key; `scope.md > Later`.
- **Re-plan history beyond the last change:** only the latest note is kept visible.
- **Feedback on a new system before committing to it:** a draft goal you refine with free-text feedback, then commit. Discussed in `4-spec` and deferred because the draft state complicated the cap, Next day and joint re-planning for the POC.
- **Following the real date automatically:** Today jumping to the system date by itself on open. The POC has an explicit **Fast forward** instead (see **Next Day, Review and Re-plan**), so the user confirms what they did first and the demo can still move through time. Decided during `5-build`.
- **Adding goals in bulk:** bulk adds a second form and a messier feasibility check.
- **Rebalancing goals when a new one doesn't fit:** rework existing plans by deadline and need, or by a priority the user picks, instead of offering only the leftover time. Deferred during `5-build` until real use shows it's needed.

## Possible Later Enhancements
- A re-plan history or counter per goal, to spot goals that keep slipping (worded so it doesn't feel like a guilt score).
- The AI suggesting a realistic deadline when one is impossible.
- **Chat-style goal refinement:** a back-and-forth conversation (or an extra follow-up round) when one round of clarifying questions isn't enough. The POC asks one round and shows remaining assumptions instead.
- Editing a goal or its deadline after it's planned.
- Changing the daily hours later (with a re-plan).

## Non-Goals
- **Real-time day passing:** can't be demoed; replaced by Next day (`scope.md > Explicitly Cut`).
- **Manual system editing:** the tool owns the system; the user shouldn't have to rethink it. Users tell it what happened (updates); the tool decides what changes (`scope.md > The Unique Kernel`).
- **Copying the reference app:** colors and vibe only, not its name, logo or layouts.
- **Streaks, failure counts or shame mechanics:** contrary to the guilt-free intent.

## Open Questions
- **Data across sessions:** resolved in `spec.md`: everything is stored in a local SQLite file and survives restarts.
- **Final app name:** working name is SysPlanner. **Reminder: revisit the name once the build is working, before `6-ship`.** Does not block spec.
