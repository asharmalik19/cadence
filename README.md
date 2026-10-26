# Cadence

Type a goal and a deadline. An AI asks what it needs to know, turns it into a SMART goal, tells you
whether the deadline is realistic, and builds a system for it: a breakdown, milestones, and a
day-by-day plan where every task has a done criterion, a time estimate and a why. Plan up to three
goals together inside the hours you have each day. Tick what you did. When you fall behind or
something changes, it re-plans and tells you exactly what moved.

The AI proposes, the backend checks, the database remembers. Every AI reply is checked by code (no
day over your daily hours, a free day every week, nothing past the deadline, every task complete)
before it is saved.

## What you need

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey). A paid key is
  recommended: on the free tier calls can queue for minutes.

## Setup (once)

```bash
cp .env.example .env            # then put your key in GEMINI_API_KEY
uv sync                         # Python dependencies
cd frontend && npm install && cd ..
```

## Run it (one command)

```bash
cd frontend && npm run build && cd ..
uv run uvicorn backend.app.main:app --port 8000
```

Open http://localhost:8000.

Your data lives in `data/cadence.db`. For a fresh start, stop the server and delete that file.

## Try the demo

1. Enter the hours you want to plan per day (e.g. 8: with one free day a week, that is 48 h).
2. **Add goal**: "Get a scholarship to study abroad", pick a deadline a few months out, answer the
   AI's questions. Try a deadline next week first to see it refuse and ask for a new one.
3. Add two more goals. Each new goal gets only the time the others leave free, so all three together
   never exceed your hours per day or per week. If there isn't enough time left, it's refused and
   tells you how many hours a week are free.
4. With three goals, **Add goal** is switched off: three is the limit.
5. On **Today**, tick some tasks and leave one unticked.
6. Click **Next day**, confirm the review (optionally write what happened on a goal), and read the
   **Last change** notes on the re-planned goals.

Days are simulated: **Next day** moves the app's own date forward, so you can try a week in a few
minutes.

AI calls take a while: about 30 seconds for the first goal, up to a minute once three goals are planned together.

## Develop

Two terminals, with live reload:

```bash
uv run uvicorn backend.app.main:app --reload --port 8000
cd frontend && npm run dev      # open http://localhost:5173 (Vite forwards /api to :8000)
```

If port 8000 is taken, run uvicorn with `--port 8010` and Vite with `API_PORT=8010 npm run dev`.

Tests use a fake planner and never call the AI:

```bash
uv run pytest
RUN_LIVE=1 uv run pytest backend/tests/test_gemini_live.py   # one real Gemini call
```

Set `AI_PROVIDER=fake` in `.env` to click through the app with canned plans and no API cost.
`GEMINI_MODEL` switches between `gemini-flash-latest` (default) and `gemini-pro-latest`.

## How it's built

- `backend/app/` — FastAPI. `services.py` holds the rules (cap, missed tasks, when to re-plan),
  `validation.py` checks every AI reply, `planner/` talks to Gemini, `db.py` is the SQLite store.
- `frontend/src/` — React + TypeScript, built with Vite. Shows what the backend returns; decides
  nothing itself.
- `devpost/` — the scope, product definition, technical spec and build checklist this was built from.
