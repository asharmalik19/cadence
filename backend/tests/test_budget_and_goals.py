"""Daily hours, adding a goal, the clarify step, the feasibility loop (prd.md > Daily Time Budget, Adding a Goal)."""

from datetime import date, timedelta

from backend.app import db

TODAY = date.today()
LATER = (TODAY + timedelta(days=60)).isoformat()
GOAL = {"text": "Get a scholarship to study abroad", "deadline": LATER}
ANSWERS = [{"question": "Which level?", "answer": "Master's"}]


def set_hours(client, hours=8):
    r = client.post("/api/settings", json={"daily_hours": hours})
    assert r.status_code == 200
    return r.json()


def test_first_open_has_no_settings_and_no_goals(client):
    state = client.get("/api/state").json()
    assert state["settings"] is None and state["goals"] == [] and state["max_goals"] == 3


def test_hours_question_comes_before_add_goal(client):
    r = client.post("/api/goals/clarify", json=GOAL)
    assert r.status_code == 409
    assert "daily hours" in r.json()["detail"]


def test_setting_hours_starts_the_simulated_day_today(client):
    state = set_hours(client)
    assert state["settings"] == {"daily_hours": 8, "current_day": TODAY.isoformat()}


def test_hours_are_set_once(client):
    set_hours(client)
    assert client.post("/api/settings", json={"daily_hours": 6}).status_code == 409


def test_clarify_returns_questions_and_saves_nothing(client):
    set_hours(client)
    r = client.post("/api/goals/clarify", json=GOAL)
    assert r.status_code == 200 and r.json()["questions"]
    assert client.get("/api/state").json()["goals"] == []


def test_impossible_goal_is_not_added_and_shows_assumptions(make_client):
    client, _ = make_client("impossible")
    set_hours(client)
    r = client.post("/api/goals", json={**GOAL, "clarifications": ANSWERS}).json()
    assert r["status"] == "impossible"
    assert r["message"] and r["assumptions"] and r["smart_goal"]
    assert client.get("/api/state").json()["goals"] == []


def test_new_deadline_after_impossible_is_a_fresh_try(make_client):
    client, planner = make_client("impossible", "ok")
    set_hours(client)
    assert client.post("/api/goals", json={**GOAL, "clarifications": ANSWERS}).json()["status"] == "impossible"
    r = client.post("/api/goals", json={**GOAL, "clarifications": ANSWERS}).json()
    assert r["status"] == "added"
    assert len(planner.calls) == 2


def test_added_goal_has_smart_goal_answers_breakdown_and_complete_tasks(client):
    set_hours(client)
    r = client.post("/api/goals", json={**GOAL, "clarifications": ANSWERS}).json()
    assert r["status"] == "added"
    goal = r["state"]["goals"][0]
    assert goal["id"] == r["goal_id"]
    assert goal["smart_goal"] and goal["feasibility"] == "stretch"
    assert goal["clarifications"] == ANSWERS
    assert goal["breakdown"] and goal["tasks"]
    assert goal["last_change"] is None
    for t in goal["tasks"]:
        assert t["done_criterion"] and t["why"] and t["minutes"] > 0 and t["status"] == "planned"


def test_answers_are_sent_to_the_planner(make_client):
    client, planner = make_client()
    set_hours(client)
    client.post("/api/goals", json={**GOAL, "clarifications": ANSWERS})
    kind, ctx, _ = planner.calls[-1]
    assert kind == "new_goal" and ctx.new_goal.clarifications[0].answer == "Master's"
    assert ctx.daily_hours == 8


def test_plan_breaking_rules_twice_fails_calmly_and_saves_nothing(make_client):
    client, _ = make_client("broken")
    set_hours(client)
    r = client.post("/api/goals", json=GOAL)
    assert r.status_code == 502
    assert r.json()["detail"] == "Planning didn't work this time. Nothing was changed."
    assert client.get("/api/state").json()["goals"] == []


def test_ai_unavailable_fails_calmly(make_client):
    client, _ = make_client("fail")
    set_hours(client)
    assert client.post("/api/goals/clarify", json=GOAL).status_code == 502


def test_deadline_must_be_after_today(client):
    set_hours(client)
    r = client.post("/api/goals/clarify", json={**GOAL, "deadline": TODAY.isoformat()})
    assert r.status_code == 409


def test_goal_survives_a_restart(make_client, tmp_path):
    client, _ = make_client()
    set_hours(client)
    client.post("/api/goals", json=GOAL)
    reopened = db.connect(tmp_path / "test.db")  # a fresh connection, as after restarting the server
    assert len(db.list_goals(reopened)) == 1
    assert db.get_settings(reopened).daily_hours == 8


def test_today_lists_todays_tasks_with_goal_label(client):
    set_hours(client)
    client.post("/api/goals", json=GOAL)
    state = client.get("/api/state").json()
    expected = [t["id"] for t in state["goals"][0]["tasks"] if t["day"] == TODAY.isoformat()]
    assert [t["id"] for t in state["today"]] == expected
    assert all(t["goal_text"] == GOAL["text"] for t in state["today"])


def test_added_goal_keeps_milestones_and_step_kinds(client):
    set_hours(client)
    goal = client.post("/api/goals", json=GOAL).json()["state"]["goals"][0]
    assert goal["milestones"][0]["name"] == "First result"
    assert {t["kind"] for t in goal["tasks"]} == {"explore", "concrete"}
    assert all(t["milestone"] == "First result" for t in goal["tasks"])


def test_deleting_a_goal_removes_it_and_its_tasks_and_frees_a_slot(client):
    set_hours(client)
    goal_id = client.post("/api/goals", json=GOAL).json()["goal_id"]
    r = client.delete(f"/api/goals/{goal_id}")
    assert r.status_code == 200
    assert r.json()["goals"] == [] and r.json()["today"] == []
    assert client.delete(f"/api/goals/{goal_id}").status_code == 404
    assert client.post("/api/goals", json=GOAL).json()["status"] == "added"


def test_older_data_file_is_upgraded_in_place(tmp_path):
    import sqlite3

    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript(
        "CREATE TABLE goals (id INTEGER PRIMARY KEY, text TEXT NOT NULL, deadline TEXT NOT NULL, feasibility TEXT,"
        " smart_goal TEXT NOT NULL, clarifications_json TEXT NOT NULL, breakdown_json TEXT NOT NULL,"
        " last_change TEXT, created_on TEXT NOT NULL);"
        "CREATE TABLE tasks (id INTEGER PRIMARY KEY, goal_id INTEGER NOT NULL, day TEXT NOT NULL, title TEXT NOT NULL,"
        " done_criterion TEXT NOT NULL, minutes INTEGER NOT NULL, why TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'planned');"
        "INSERT INTO goals VALUES (1, 'Old goal', '2026-12-31', 'stretch', 'Old SMART', '[]', '[]', NULL, '2026-10-15');"
        "INSERT INTO tasks VALUES (1, 1, '2026-10-15', 'Old task', 'Done', 30, 'Because', 'planned');"
    )
    old.commit()
    old.close()
    goal = db.list_goals(db.connect(path))[0]
    assert goal.milestones == [] and goal.tasks[0].kind == "concrete" and goal.tasks[0].milestone == ""
