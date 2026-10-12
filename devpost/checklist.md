---
doc: checklist
status: approved
---

# Build Checklist

Build mode: learn

## Slices

- [ ] **1. Gemini builds a real system for the 16-products goal (terminal probe)**
  Becomes usable: One command sends "Build 16 products by the end of 2026" to Gemini, which asks its clarifying questions in the terminal; you answer, and it prints the SMART goal, its assumptions, the verdict, the breakdown, the first two weeks of tasks, the Validation result, and each call's time, reply size and token cost.
  Why now: The AI is the product and the biggest unknown. Before any screen exists we need to know whether Flash returns a valid, believable plan of ~85 days in one call, how long it takes and what it costs. That decides Flash vs. Pro and whether the 14-day fallback is needed, and it is the single technical layer that earns its own slice because it proves a critical risk and leaves runnable evidence.
  PRD ref: `prd.md > The System (Breakdown + Day-by-Day Plan)`, `prd.md > Adding a Goal`
  Spec ref: `spec.md > Planner Layer`, `spec.md > Planner in Detail`, `spec.md > Validation Rules in Detail`, `spec.md > Data Model` (AI reply shapes), `spec.md > Gemini API`, `spec.md > Decisions and Open Issues` (To check early in the build)
  Build: Scaffold the backend (`pyproject.toml` with uv, `.env.example`, `config.py`), the Pydantic reply shapes in `models.py` (including `Clarify`, `smart_goal`, `assumptions`), the Planner interface (`clarify`, `plan_new_goal`, `replan`) plus `gemini.py`, `fake.py`, `openai.py` stub and `prompts.py`, and `validation.py` `check_plan`. Add a small probe script and the opt-in `test_gemini_live.py`. Log `usage_metadata` per call.
  Verify (mechanical): Run the probe with the real key once; confirm the clarify reply parses into `Clarify` with questions about what a product is, and the plan reply parses into `NewGoalPlan`, `check_plan` returns no problems (or the retry fixes them), and record time, reply size and tokens. Run `uv run pytest` and confirm the validation tests pass with the Fake planner and the live test is skipped without `RUN_LIVE=1`.
  Learner check: Run the probe yourself, answer its questions the way you'd describe your products, and read the SMART goal, breakdown and first two weeks. Does it plan roughly one product every 5–6 days, surface steps you wouldn't have foreseen, and give a why you'd believe? Say whether Flash is good enough.
  Commit: `Add Gemini planner, validation, and live probe for the 16-products goal`

- [ ] **2. Set your weekly hours, add a goal, and see its system in the browser**
  Becomes usable: Open the app, enter weekly hours, add a goal with a deadline, answer the AI's clarifying questions, get turned back on an impossible deadline until it's realistic, then see the goal (with its SMART version) in the sidebar and its Goal view (breakdown + day-by-day plan). Everything survives a restart.
  Why now: Puts the kernel from slice 1 on screen in the real look and feel as early as possible, so feedback on the look and the plan display can shape the rest. It also brings in the database, services, routes and the frontend scaffold that every later slice lands on.
  PRD ref: `prd.md > The Core Journey` (steps 1–4), `prd.md > Weekly Time Budget`, `prd.md > Adding a Goal`, `prd.md > The System (Breakdown + Day-by-Day Plan)`, `prd.md > Screens and Layout`, `prd.md > Look and Feel`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Components`, `spec.md > Data Model`, `spec.md > File Structure`, `spec.md > API Routes in Detail`, `spec.md > Look and Feel`, `spec.md > Where It Runs and How Someone Tries It`
  Build: `db.py` (schema, transactions), `services.py` (set hours, add goal with feasibility + validation retry), `main.py` routes (`GET /api/state`, `POST /api/settings`, `POST /api/goals/clarify`, `POST /api/goals`), test fixtures and `test_budget_and_goals.py` (hours, feasibility loop, single-goal add). Frontend scaffold with Vite proxy, theme, App shell, `WeeklyHoursStep`, `Sidebar`, `AddGoalDialog` (goal + deadline → questions → verdict), `GoalView` (shows SMART goal)/`Breakdown`/`DayPlan`/`LastChangeNote`, `PlanningIndicator`, `ErrorNotice`, empty state.
  Verify (mechanical): `uv run pytest` passes; `npm run build` type-checks cleanly; with both dev servers running, drive the API (settings → clarify → impossible goal → realistic goal) via the Fake planner and confirm the state, then restart the backend and confirm `GET /api/state` still returns the goal.
  Learner check: Start both dev servers, open http://localhost:5173, enter your hours, try "Build 16 products in 3 days" and confirm it's refused and asks for a new deadline, then use 31 Dec 2026 and open the goal. Tell me how the look and the plan display feel.
  Commit: `Add weekly hours, add-goal flow with feasibility loop, and Goal view`

- [ ] **3. Tick today's tasks, click Next day, and watch a miss re-plan the goal**
  Becomes usable: Today shows today's tasks with done criterion, minutes and why; you tick what you did; Next day opens the review of unticked tasks; confirming marks the rest missed, Gemini re-plans that goal, the day advances and the goal's Last change note says what moved. All ticked skips the review and the AI.
  Why now: This is the "oh, that's cool" beat and the second half of the kernel (adapts on a miss). The re-plan prompt is the other big AI risk, so it comes before multi-goal work, which only widens it.
  PRD ref: `prd.md > The Core Journey` (steps 6–11), `prd.md > Today and Marking Done`, `prd.md > Next Day, Review and Re-plan`, `prd.md > Last Change Note`
  Spec ref: `spec.md > Services`, `spec.md > API Routes in Detail`, `spec.md > Data Model` (Tasks, Ticks rows), `spec.md > Today View`, `spec.md > End-of-Day Review`, `spec.md > Important Failure Modes`
  Build: Services for toggle (current day only) and next day (mark missed, re-plan only goals with misses, replace tasks from tomorrow on, write notes, advance day, all in one transaction; nothing changes on AI failure). Routes `POST /api/tasks/{id}/toggle`, `POST /api/day/next`. `test_today_next_day.py`. Frontend `TodayView`, `TaskCard`, `ReviewDialog`, Today link in the sidebar, past days dimmed in `DayPlan`.
  Verify (mechanical): `uv run pytest` passes, including: toggle refused off the current day, review-skip path makes no AI call, missed tasks marked, only affected goals re-planned, AI failure leaves day and tasks unchanged. `npm run build` is clean. One real re-plan call on the slice-2 goal, with time and tokens recorded.
  Learner check: On Today, tick some tasks and leave one unticked, click Next day, see it listed in the review, confirm, then open the goal and read the Last change note. Does it say plainly what moved and whether the deadline still holds?
  Commit: `Add Today ticking, end-of-day review, and re-plan on missed tasks`

- [ ] **4. Plan up to three goals together, refuse a fourth, and run the full demo from one command**
  Becomes usable: Adding goals 2 and 3 re-plans the existing goals jointly within the weekly hours, each changed goal gets a Last change note, Today mixes tasks from all goals labelled by goal, and a 4th goal is refused with a plain message. `npm run build` plus one uvicorn command serves the whole app at http://localhost:8000, with a README to set it up.
  Why now: Joint planning and the cap complete the kernel ("plans your goals together, and caps them") on top of a single-goal loop that already works. The one-command run and README close the POC for the demo.
  PRD ref: `prd.md > The Core Journey` (step 5 and Success), `prd.md > Goal Cap`, `prd.md > The System (Breakdown + Day-by-Day Plan)` (rework on add), `prd.md > Weekly Time Budget`, `prd.md > Last Change Note`
  Spec ref: `spec.md > Services`, `spec.md > Validation Rules in Detail` (weekly budget across all goals), `spec.md > Data Model` (Tasks row: rework on add), `spec.md > Sidebar`, `spec.md > Where It Runs and How Someone Tries It`
  Build: Rework handling in add goal (replace existing goals' planned tasks from today on, keep ticks, write notes), cap check returning 409 before any AI call, cross-goal weekly budget in validation, sidebar disables Add goal at 3 with a reason, goal labels on Today. `main.py` serves `frontend/dist`. `README.md` with setup, run and demo steps.
  Verify (mechanical): `uv run pytest` passes, including cap refusal with no AI call, rework replacing only planned tasks, and the cross-goal budget rule. `npm run build`, then the single uvicorn command serves the app at :8000 and `GET /api/state` works there. One real three-goal run, checked against the weekly budget.
  Learner check: From a fresh database, run the demo from `prd.md > The Core Journey > Success`: hours, the 16-products goal, two more, try a 4th, tick some, leave one, Next day, read the notes. Say whether it's demo-ready.
  Commit: `Add joint planning for up to three goals, the goal cap, and one-command demo`

## Hands-on Checkpoints

- [ ] Early usable behavior explored — after slice 1 (plan quality: Flash vs. Pro, prompt changes) and after slice 2 (look and feel, plan display in the browser)
- [ ] Final kick-the-tires exploration and feedback completed

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: [what actually happened; real document/test/code references; unfinished work if interrupted]
Route and stops: [actual paths and symbols; guided stops completed, or reference-only route]
Edit outcome: [tried/kept/reverted/declined/not applicable; verification if changed]
Reflection: [offered/answered/declined/already covered — personal answer belongs only in the ignored profile]
Activity mode: [live app and editor, explicit static fallback, focused alternative, prior practice, or recap]

## Revisions

- Added clarifying questions and an AI-written SMART goal before the feasibility verdict (slices 1 and 2; `prd.md > Adding a Goal`, `spec.md > API Routes in Detail`, `spec.md > Data Model`) — the first real Gemini call judged "Build 16 products by the end of 2026" impossible because a one-sentence goal left it to assume full production software; the learner decided the tool should ask what it's missing rather than make the user reword the goal.
