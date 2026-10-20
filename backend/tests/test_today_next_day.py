"""Ticking, Next day, updates and re-plans (prd.md > Today and Marking Done, Next Day, Review and Re-plan,
Updates (What Happened), Last Change Note)."""

import json
from datetime import date, timedelta

from backend.app import db

MONDAY = date(2026, 10, 12)  # the simulated day starts here, so the Fake planner's tasks land on known days
TUESDAY = MONDAY + timedelta(days=1)
SCHOLARSHIP = {"text": "Get a scholarship to study abroad", "deadline": "2027-01-15"}
BOOK = {"text": "Write a short book", "deadline": "2027-01-15"}


def start(client, *goals):
    """Hours set, the day moved to MONDAY, then the goals added. Returns the goal ids."""
    assert client.post("/api/settings", json={"daily_hours": 8}).status_code == 200
    conn = client.app.state.conn
    with db.transaction(conn):
        db.set_current_day(conn, MONDAY)
    return [client.post("/api/goals", json=g).json()["goal_id"] for g in goals]


def state(client):
    return client.get("/api/state").json()


def goal(client, goal_id):
    return next(g for g in state(client)["goals"] if g["id"] == goal_id)


def today_ids(client, goal_id=None):
    return [t["id"] for t in state(client)["today"] if goal_id is None or t["goal_id"] == goal_id]


def tick_all_today(client):
    for task_id in today_ids(client):
        assert client.post(f"/api/tasks/{task_id}/toggle", json={"done": True}).status_code == 200


def replans(planner):
    return [ctx for kind, ctx, _ in planner.calls if kind == "replan"]


# --- ticking -------------------------------------------------------------------


def test_ticking_marks_done_and_unticking_undoes_it(client):
    start(client, SCHOLARSHIP)
    task_id = today_ids(client)[0]
    r = client.post(f"/api/tasks/{task_id}/toggle", json={"done": True}).json()
    assert r["today"][0]["status"] == "done"
    r = client.post(f"/api/tasks/{task_id}/toggle", json={"done": False}).json()
    assert r["today"][0]["status"] == "planned"


def test_ticking_is_refused_off_the_current_day(client):
    (gid,) = start(client, SCHOLARSHIP)
    future = next(t for t in goal(client, gid)["tasks"] if t["day"] > MONDAY.isoformat())
    r = client.post(f"/api/tasks/{future['id']}/toggle", json={"done": True})
    assert r.status_code == 409
    assert goal(client, gid)["tasks"][1]["status"] == "planned"
    assert client.post("/api/tasks/9999/toggle", json={"done": True}).status_code == 404


# --- next day ------------------------------------------------------------------


def test_nothing_missed_and_nothing_new_advances_with_no_ai_call(make_client):
    client, planner = make_client()
    start(client, SCHOLARSHIP)
    tick_all_today(client)
    calls_before = len(planner.calls)
    r = client.post("/api/day/next", json={"updates": []})
    assert r.status_code == 200
    assert r.json()["settings"]["current_day"] == TUESDAY.isoformat()
    assert len(planner.calls) == calls_before
    assert r.json()["goals"][0]["last_change"] is None


def test_unticked_tasks_become_missed_and_their_goal_is_replanned(make_client):
    client, planner = make_client()
    (gid,) = start(client, SCHOLARSHIP)
    missed_id = today_ids(client)[0]
    r = client.post("/api/day/next", json={"updates": []}).json()

    g = r["goals"][0]
    assert next(t for t in g["tasks"] if t["id"] == missed_id)["status"] == "missed"
    assert g["last_change"] == "Shifted the remaining tasks back by one day; deadline still met."
    assert r["settings"]["current_day"] == TUESDAY.isoformat()
    # The planner saw the miss and planned from tomorrow on.
    (ctx,) = replans(planner)
    assert ctx.replan_goal_ids == [gid] and ctx.start_day == TUESDAY
    assert "missed tasks today" in ctx.replan_reasons[gid]
    assert next(t for t in ctx.goals[0].tasks if t.id == missed_id).status == "missed"
    # The new plan starts tomorrow; nothing new was planned on the closed day.
    assert {t["day"] for t in g["tasks"] if t["status"] == "planned"} >= {TUESDAY.isoformat()}
    assert [t["id"] for t in g["tasks"] if t["day"] == MONDAY.isoformat()] == [missed_id]


def test_ticking_in_the_review_prevents_a_replan(make_client):
    client, planner = make_client()
    start(client, SCHOLARSHIP)
    tick_all_today(client)  # what the review's tick boxes do
    client.post("/api/day/next", json={"updates": []})
    assert replans(planner) == []


def test_only_goals_with_misses_or_updates_are_replanned(make_client):
    client, planner = make_client()
    scholarship, book = start(client, SCHOLARSHIP, BOOK)
    for task_id in today_ids(client, scholarship):
        client.post(f"/api/tasks/{task_id}/toggle", json={"done": True})
    r = client.post("/api/day/next", json={"updates": []}).json()
    (ctx,) = replans(planner)
    assert ctx.replan_goal_ids == [book]
    notes = {g["id"]: g["last_change"] for g in r["goals"]}
    assert notes[scholarship] is None and notes[book]


def test_an_update_in_the_review_replans_even_with_nothing_missed(make_client):
    client, planner = make_client()
    (gid,) = start(client, SCHOLARSHIP)
    tick_all_today(client)
    r = client.post("/api/day/next", json={"updates": [{"goal_id": gid, "text": "Dropping Dubai"}]}).json()
    (ctx,) = replans(planner)
    assert ctx.replan_reasons[gid] == ["new update from the user"]
    assert ctx.goals[0].updates[-1].text == "Dropping Dubai"
    assert r["goals"][0]["updates"] == [{"id": 1, "goal_id": gid, "day": MONDAY.isoformat(), "text": "Dropping Dubai"}]
    assert r["goals"][0]["last_change"]


def test_blank_updates_are_ignored(make_client):
    client, planner = make_client()
    (gid,) = start(client, SCHOLARSHIP)
    tick_all_today(client)
    r = client.post("/api/day/next", json={"updates": [{"goal_id": gid, "text": "   "}]}).json()
    assert replans(planner) == [] and r["goals"][0]["updates"] == []


def test_a_goal_whose_daily_tasks_run_low_is_extended(make_client):
    client, planner = make_client(days=3)  # 3 days of tasks...
    (gid,) = start(client, SCHOLARSHIP)
    conn = client.app.state.conn
    with db.transaction(conn):  # ...toward a milestone a month away
        milestones = [{"name": "First result", "target_day": "2026-11-12", "reached_when": "It exists."}]
        conn.execute("UPDATE goals SET milestones_json = ? WHERE id = ?", (json.dumps(milestones), gid))
    tick_all_today(client)
    client.post("/api/day/next", json={"updates": []})
    (ctx,) = replans(planner)
    assert ctx.replan_goal_ids == [gid]
    assert "extend" in ctx.replan_reasons[gid][0]


def test_ai_failure_leaves_day_ticks_and_updates_unchanged(make_client):
    client, _ = make_client("ok", "fail")
    (gid,) = start(client, SCHOLARSHIP)
    before = state(client)
    r = client.post("/api/day/next", json={"updates": [{"goal_id": gid, "text": "DAAD deadline is 30 Nov"}]})
    assert r.status_code == 502
    assert r.json()["detail"] == "Planning didn't work this time. Nothing was changed."
    assert state(client) == before


def test_update_for_a_missing_goal_is_refused(client):
    start(client, SCHOLARSHIP)
    r = client.post("/api/day/next", json={"updates": [{"goal_id": 99, "text": "Hi"}]})
    assert r.status_code == 404
    assert state(client)["settings"]["current_day"] == MONDAY.isoformat()


# --- updates from the goal page --------------------------------------------------


def test_update_on_goal_page_replans_from_today_and_keeps_ticks(make_client):
    client, planner = make_client()
    (gid,) = start(client, SCHOLARSHIP)
    ticked = today_ids(client)[0]
    client.post(f"/api/tasks/{ticked}/toggle", json={"done": True})
    r = client.post(f"/api/goals/{gid}/updates", json={"text": "DAAD deadline is 30 Nov"})
    assert r.status_code == 200
    g = r.json()["goals"][0]
    assert g["updates"][0]["text"] == "DAAD deadline is 30 Nov" and g["last_change"]
    assert next(t for t in g["tasks"] if t["id"] == ticked)["status"] == "done"
    (ctx,) = replans(planner)
    assert ctx.start_day == MONDAY and ctx.replan_goal_ids == [gid]
    assert r.json()["settings"]["current_day"] == MONDAY.isoformat()  # the day doesn't move


def test_updates_are_sent_with_later_plans(make_client):
    client, planner = make_client()
    (gid,) = start(client, SCHOLARSHIP)
    client.post(f"/api/goals/{gid}/updates", json={"text": "Only Germany now"})
    client.post("/api/goals", json=BOOK)  # adding another goal
    client.post("/api/day/next", json={"updates": []})
    for kind, ctx, _ in planner.calls[-2:]:
        assert [u.text for u in next(g for g in ctx.goals if g.id == gid).updates] == ["Only Germany now"]


def test_a_rewritten_smart_goal_is_saved(make_client, monkeypatch):
    client, planner = make_client()
    (gid,) = start(client, SCHOLARSHIP)
    original = planner.replan

    def rewrite(ctx, problems=None):
        reply = original(ctx, problems)
        reply.goals[0].smart_goal = "Win a fully funded master's scholarship in Germany by 15 Jan 2027"
        return reply

    monkeypatch.setattr(planner, "replan", rewrite)
    r = client.post(f"/api/goals/{gid}/updates", json={"text": "Only Germany now"}).json()
    assert r["goals"][0]["smart_goal"].endswith("in Germany by 15 Jan 2027")


def test_update_failure_saves_nothing(make_client):
    client, _ = make_client("ok", "fail")
    (gid,) = start(client, SCHOLARSHIP)
    before = state(client)
    assert client.post(f"/api/goals/{gid}/updates", json={"text": "Dropping Dubai"}).status_code == 502
    assert state(client) == before
    assert client.post("/api/goals/99/updates", json={"text": "x"}).status_code == 404
    assert client.post(f"/api/goals/{gid}/updates", json={"text": ""}).status_code == 422
