"""Several goals sharing the user's time, and the cap (prd.md > Goal Cap, Daily Time Budget,
The System (Breakdown + Day-by-Day Plan))."""

from datetime import date

from backend.app import db

MONDAY = date(2026, 10, 12)
SCHOLARSHIP = {"text": "Get a scholarship to study abroad", "deadline": "2027-01-15"}
BOOK = {"text": "Write a short book", "deadline": "2027-01-15"}
RUN = {"text": "Run a half marathon", "deadline": "2027-01-15"}
FOURTH = {"text": "Learn Spanish", "deadline": "2027-01-15"}


def start(client, hours=8):
    assert client.post("/api/settings", json={"daily_hours": hours}).status_code == 200
    conn = client.app.state.conn
    with db.transaction(conn):
        db.set_current_day(conn, MONDAY)


def add(client, goal):
    return client.post("/api/goals", json=goal)


def state(client):
    return client.get("/api/state").json()


def goal(client, goal_id):
    return next(g for g in state(client)["goals"] if g["id"] == goal_id)


# --- the cap -------------------------------------------------------------------


def test_a_fourth_goal_is_refused_before_any_ai_call(make_client):
    client, planner = make_client()
    start(client)
    for g in (SCHOLARSHIP, BOOK, RUN):
        assert add(client, g).json()["status"] == "added"
    calls_before = len(planner.calls)

    clarify = client.post("/api/goals/clarify", json={"text": FOURTH["text"], "deadline": FOURTH["deadline"]})
    added = add(client, FOURTH)

    assert clarify.status_code == 409 and added.status_code == 409
    assert "3 active goals" in added.json()["detail"]
    assert len(planner.calls) == calls_before
    assert [g["text"] for g in state(client)["goals"]] == [SCHOLARSHIP["text"], BOOK["text"], RUN["text"]]


def test_state_tells_the_screen_the_cap(client):
    start(client)
    assert state(client)["max_goals"] == 3


# --- planning goals together ---------------------------------------------------


def test_today_mixes_tasks_from_all_goals_labelled_by_goal(client):
    start(client)
    for g in (SCHOLARSHIP, BOOK, RUN):
        add(client, g)
    labels = {t["goal_text"] for t in state(client)["today"]}
    assert labels == {SCHOLARSHIP["text"], BOOK["text"], RUN["text"]}


def test_adding_a_goal_leaves_existing_plans_untouched(make_client):
    client, planner = make_client()
    start(client)
    first = add(client, SCHOLARSHIP).json()["goal_id"]
    before = goal(client, first)
    add(client, BOOK)
    assert goal(client, first) == before
    assert planner.calls[-1][1].goals[0].id == first  # the planner saw the existing goal's time


def test_a_new_goal_that_overflows_the_day_across_goals_is_not_saved(make_client):
    # 90 minutes a day per goal against a 2-hour day: one goal fits, two don't.
    client, planner = make_client(minutes=90)
    start(client, hours=2)
    first = add(client, SCHOLARSHIP).json()["goal_id"]
    before = goal(client, first)

    r = add(client, BOOK)

    assert r.status_code == 502
    assert len(planner.calls) == 3  # first goal, then the second goal plus its one retry
    assert "over the daily limit" in " ".join(planner.calls[-1][2])
    assert [g["id"] for g in state(client)["goals"]] == [first]
    assert goal(client, first)["tasks"] == before["tasks"]


def test_a_new_goal_that_overflows_the_week_is_not_saved(make_client):
    # 3 h x 6 days = 1080 minutes a week. Each Fake goal takes 100 x 6 = 600, so a second one doesn't fit.
    client, planner = make_client(minutes=100)
    start(client, hours=3)
    first = add(client, SCHOLARSHIP).json()["goal_id"]

    assert add(client, BOOK).status_code == 502
    assert any("at most 480 minutes a week" in p for p in planner.calls[-1][2])
    assert [g["id"] for g in state(client)["goals"]] == [first]


def test_the_planner_is_told_the_weekly_time_left(make_client):
    from backend.app.planner.prompts import build_prompt

    client, planner = make_client()
    start(client, hours=7)
    add(client, SCHOLARSHIP)  # 60 x 6 = 360 a week
    add(client, BOOK)
    prompt = build_prompt(planner.calls[-1][1], "new_goal", None)
    assert "the budget is 2520 minutes a week (7 h x 6 working days)" in prompt
    assert "use 360, so 2160 minutes a week are left" in prompt
