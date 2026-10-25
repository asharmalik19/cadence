"""Fast forward over days away: one review, one re-plan (prd.md > Next Day, Review and Re-plan)."""

from datetime import date, timedelta

from backend.app import db

MONDAY = date(2026, 10, 12)
THURSDAY = MONDAY + timedelta(days=3)
SCHOLARSHIP = {"text": "Get a scholarship to study abroad", "deadline": "2027-01-15"}
BOOK = {"text": "Write a short book", "deadline": "2027-01-15"}


def start(client, *goals):
    assert client.post("/api/settings", json={"daily_hours": 8}).status_code == 200
    conn = client.app.state.conn
    with db.transaction(conn):
        db.set_current_day(conn, MONDAY)
    return [client.post("/api/goals", json=g).json()["goal_id"] for g in goals]


def state(client):
    return client.get("/api/state").json()


def tasks_between(client, first, last):
    return [t for g in state(client)["goals"] for t in g["tasks"] if first <= date.fromisoformat(t["day"]) <= last]


def forward(client, to_day, **body):
    return client.post("/api/day/next", json={"updates": [], "to_day": to_day.isoformat(), **body})


def replans(planner):
    return [ctx for kind, ctx, _ in planner.calls if kind == "replan"]


def test_fast_forward_closes_every_day_away_with_one_ai_call(make_client):
    client, planner = make_client()
    start(client, SCHOLARSHIP, BOOK)
    away = {t["id"] for t in tasks_between(client, MONDAY, THURSDAY - timedelta(days=1))}

    r = forward(client, THURSDAY)

    assert r.status_code == 200
    assert r.json()["settings"]["current_day"] == THURSDAY.isoformat()
    assert len(replans(planner)) == 1
    ctx = replans(planner)[0]
    assert ctx.start_day == THURSDAY and sorted(ctx.replan_goal_ids) == sorted(g["id"] for g in r.json()["goals"])
    assert all("over the last 3 days" in why[0] for why in ctx.replan_reasons.values())
    statuses = {t["id"]: t["status"] for g in r.json()["goals"] for t in g["tasks"]}
    assert all(statuses[i] == "missed" for i in away)
    assert all(t["day"] >= THURSDAY.isoformat() for t in r.json()["today"])


def test_ticks_on_days_away_count_as_done_and_prevent_a_replan(make_client):
    client, planner = make_client()
    start(client, SCHOLARSHIP)
    away = [t["id"] for t in tasks_between(client, MONDAY, THURSDAY - timedelta(days=1))]
    calls_before = len(planner.calls)

    r = forward(client, THURSDAY, done_task_ids=away)

    assert r.status_code == 200
    statuses = {t["id"]: t["status"] for t in r.json()["goals"][0]["tasks"]}
    assert all(statuses[i] == "done" for i in away)
    assert len(planner.calls) == calls_before
    assert r.json()["settings"]["current_day"] == THURSDAY.isoformat()


def test_some_ticked_the_rest_missed(make_client):
    client, planner = make_client()
    start(client, SCHOLARSHIP)
    away = [t["id"] for t in tasks_between(client, MONDAY, THURSDAY - timedelta(days=1))]

    r = forward(client, THURSDAY, done_task_ids=away[:1])

    statuses = {t["id"]: t["status"] for t in r.json()["goals"][0]["tasks"]}
    assert statuses[away[0]] == "done"
    assert all(statuses[i] == "missed" for i in away[1:])
    assert len(replans(planner)) == 1


def test_a_date_not_after_the_current_day_is_refused(client):
    start(client, SCHOLARSHIP)
    assert forward(client, MONDAY).status_code == 409
    assert forward(client, MONDAY - timedelta(days=2)).status_code == 409
    assert state(client)["settings"]["current_day"] == MONDAY.isoformat()


def test_ticks_outside_the_days_being_closed_are_refused(client):
    start(client, SCHOLARSHIP)
    later = tasks_between(client, THURSDAY, THURSDAY + timedelta(days=5))[0]["id"]
    assert forward(client, THURSDAY, done_task_ids=[later]).status_code == 409
    assert forward(client, THURSDAY, done_task_ids=[9999]).status_code == 404


def test_updates_are_saved_on_the_last_day_away(make_client):
    client, planner = make_client()
    (gid,) = start(client, SCHOLARSHIP)
    r = forward(client, THURSDAY, updates=[{"goal_id": gid, "text": "Was sick for three days"}])
    assert r.json()["goals"][0]["updates"][0]["day"] == (THURSDAY - timedelta(days=1)).isoformat()
    assert "new update from the user" in replans(planner)[0].replan_reasons[gid]


def test_ai_failure_leaves_day_ticks_and_updates_unchanged(make_client):
    client, _ = make_client("ok", "fail")
    (gid,) = start(client, SCHOLARSHIP)
    before = state(client)
    away = [t["id"] for t in tasks_between(client, MONDAY, THURSDAY - timedelta(days=1))]

    r = forward(client, THURSDAY, done_task_ids=away[:1], updates=[{"goal_id": gid, "text": "Was sick"}])

    assert r.status_code == 502
    assert state(client) == before


def test_next_day_without_a_date_still_moves_one_day(make_client):
    client, _ = make_client()
    start(client, SCHOLARSHIP)
    r = client.post("/api/day/next", json={"updates": []})
    assert r.json()["settings"]["current_day"] == (MONDAY + timedelta(days=1)).isoformat()
