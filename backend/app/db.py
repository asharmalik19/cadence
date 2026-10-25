"""The SQLite file: schema, reads, and all-or-nothing writes. No other module touches SQL."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from .models import (
    Clarification,
    GoalContext,
    GoalOut,
    Milestone,
    Settings,
    TaskContext,
    TaskOut,
    TaskPlan,
    UpdateContext,
    UpdateOut,
    Workstream,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    daily_hours INTEGER NOT NULL,
    current_day TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    deadline TEXT NOT NULL,
    feasibility TEXT,
    smart_goal TEXT NOT NULL,
    clarifications_json TEXT NOT NULL,
    breakdown_json TEXT NOT NULL,
    milestones_json TEXT NOT NULL DEFAULT '[]',
    last_change TEXT,
    created_on TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    goal_id INTEGER NOT NULL REFERENCES goals(id),
    day TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'concrete' CHECK (kind IN ('concrete', 'explore')),
    milestone TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL,
    done_criterion TEXT NOT NULL,
    minutes INTEGER NOT NULL,
    why TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned' CHECK (status IN ('planned', 'done', 'missed'))
);
CREATE TABLE IF NOT EXISTS updates (
    id INTEGER PRIMARY KEY,
    goal_id INTEGER NOT NULL REFERENCES goals(id),
    day TEXT NOT NULL,
    text TEXT NOT NULL
);
"""


def connect(path: Path) -> sqlite3.Connection:
    """Open (and on first run create) the data file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    _upgrade(conn)
    return conn


# Columns added after the first goals were saved. Older data files get them with safe defaults.
_ADDED_COLUMNS = {
    "goals": {"milestones_json": "TEXT NOT NULL DEFAULT '[]'"},
    "tasks": {
        "kind": "TEXT NOT NULL DEFAULT 'concrete' CHECK (kind IN ('concrete', 'explore'))",
        "milestone": "TEXT NOT NULL DEFAULT ''",
    },
}


def _upgrade(conn: sqlite3.Connection) -> None:
    for table, columns in _ADDED_COLUMNS.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, definition in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
    conn.commit()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Everything inside is saved together, or not at all."""
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise


# --- reads -----------------------------------------------------------------


def get_settings(conn: sqlite3.Connection) -> Settings | None:
    row = conn.execute("SELECT daily_hours, current_day FROM settings WHERE id = 1").fetchone()
    return Settings(daily_hours=row["daily_hours"], current_day=row["current_day"]) if row else None


def count_goals(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM goals").fetchone()[0]


def list_goals(conn: sqlite3.Connection) -> list[GoalOut]:
    tasks_by_goal: dict[int, list[TaskOut]] = {}
    for t in conn.execute("SELECT * FROM tasks ORDER BY day, id"):
        tasks_by_goal.setdefault(t["goal_id"], []).append(_task_out(t))
    updates_by_goal: dict[int, list[UpdateOut]] = {}
    for u in conn.execute("SELECT * FROM updates ORDER BY id"):
        updates_by_goal.setdefault(u["goal_id"], []).append(
            UpdateOut(id=u["id"], goal_id=u["goal_id"], day=u["day"], text=u["text"])
        )
    return [
        GoalOut(
            id=g["id"],
            text=g["text"],
            deadline=g["deadline"],
            feasibility=g["feasibility"],
            smart_goal=g["smart_goal"],
            clarifications=[Clarification(**c) for c in json.loads(g["clarifications_json"])],
            breakdown=[Workstream(**w) for w in json.loads(g["breakdown_json"])],
            milestones=[Milestone(**m) for m in json.loads(g["milestones_json"])],
            last_change=g["last_change"],
            created_on=g["created_on"],
            updates=updates_by_goal.get(g["id"], []),
            tasks=tasks_by_goal.get(g["id"], []),
        )
        for g in conn.execute("SELECT * FROM goals ORDER BY id")
    ]


def goal_contexts(conn: sqlite3.Connection) -> list[GoalContext]:
    """Existing goals in the shape the planner sees."""
    return [
        GoalContext(
            id=g.id,
            text=g.text,
            smart_goal=g.smart_goal,
            clarifications=g.clarifications,
            deadline=g.deadline,
            breakdown=g.breakdown,
            milestones=g.milestones,
            updates=[UpdateContext(day=u.day, text=u.text) for u in g.updates],
            tasks=[
                TaskContext(
                    id=t.id, day=t.day, kind=t.kind, milestone=t.milestone, title=t.title, minutes=t.minutes, status=t.status
                )
                for t in g.tasks
            ],
        )
        for g in list_goals(conn)
    ]


def get_task(conn: sqlite3.Connection, task_id: int) -> TaskOut | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _task_out(row) if row else None


def _task_out(row: sqlite3.Row) -> TaskOut:
    return TaskOut(
        id=row["id"],
        goal_id=row["goal_id"],
        day=row["day"],
        kind=row["kind"],
        milestone=row["milestone"],
        title=row["title"],
        done_criterion=row["done_criterion"],
        minutes=row["minutes"],
        why=row["why"],
        status=row["status"],
    )


# --- writes (call inside transaction()) ---------------------------------------


def set_settings(conn: sqlite3.Connection, daily_hours: int, current_day: date) -> None:
    conn.execute(
        "INSERT INTO settings (id, daily_hours, current_day) VALUES (1, ?, ?)",
        (daily_hours, current_day.isoformat()),
    )


def set_task_status(conn: sqlite3.Connection, task_id: int, status: str) -> None:
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))


def mark_missed(conn: sqlite3.Connection, before: date) -> None:
    """Whatever is still unticked on any day before `before` counts as missed."""
    conn.execute("UPDATE tasks SET status = 'missed' WHERE status = 'planned' AND day < ?", (before.isoformat(),))


def set_current_day(conn: sqlite3.Connection, day: date) -> None:
    conn.execute("UPDATE settings SET current_day = ? WHERE id = 1", (day.isoformat(),))


def insert_update(conn: sqlite3.Connection, goal_id: int, day: date, text: str) -> None:
    conn.execute("INSERT INTO updates (goal_id, day, text) VALUES (?, ?, ?)", (goal_id, day.isoformat(), text))


def insert_goal(
    conn: sqlite3.Connection,
    *,
    text: str,
    deadline: date,
    feasibility: str,
    smart_goal: str,
    clarifications: list[Clarification],
    breakdown: list[Workstream],
    milestones: list[Milestone],
    created_on: date,
) -> int:
    cur = conn.execute(
        "INSERT INTO goals (text, deadline, feasibility, smart_goal, clarifications_json, breakdown_json,"
        " milestones_json, created_on) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            text,
            deadline.isoformat(),
            feasibility,
            smart_goal,
            json.dumps([c.model_dump() for c in clarifications]),
            json.dumps([w.model_dump() for w in breakdown]),
            _milestones_json(milestones),
            created_on.isoformat(),
        ),
    )
    return cur.lastrowid


def insert_tasks(conn: sqlite3.Connection, goal_id: int, tasks: list[TaskPlan]) -> None:
    conn.executemany(
        "INSERT INTO tasks (goal_id, day, kind, milestone, title, done_criterion, minutes, why)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (goal_id, t.day.isoformat(), t.kind, t.milestone, t.title, t.done_criterion, t.minutes, t.why)
            for t in tasks
        ],
    )


def replace_future_tasks(
    conn: sqlite3.Connection,
    goal_id: int,
    from_day: date,
    tasks: list[TaskPlan],
    breakdown: list[Workstream],
    milestones: list[Milestone],
    note: str,
    smart_goal: str = "",
) -> None:
    """Swap a goal's still-planned tasks from `from_day` on for new ones. Past and ticked tasks stay.
    A non-empty `smart_goal` replaces the goal's SMART version (an update changed the goal itself)."""
    conn.execute(
        "DELETE FROM tasks WHERE goal_id = ? AND status = 'planned' AND day >= ?", (goal_id, from_day.isoformat())
    )
    insert_tasks(conn, goal_id, tasks)
    conn.execute(
        "UPDATE goals SET breakdown_json = ?, milestones_json = ?, last_change = ? WHERE id = ?",
        (json.dumps([w.model_dump() for w in breakdown]), _milestones_json(milestones), note, goal_id),
    )
    if smart_goal.strip():
        conn.execute("UPDATE goals SET smart_goal = ? WHERE id = ?", (smart_goal.strip(), goal_id))


def delete_goal(conn: sqlite3.Connection, goal_id: int) -> bool:
    """Remove a goal with its tasks and updates. False if there was no such goal."""
    conn.execute("DELETE FROM updates WHERE goal_id = ?", (goal_id,))
    conn.execute("DELETE FROM tasks WHERE goal_id = ?", (goal_id,))
    return conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,)).rowcount > 0


def _milestones_json(milestones: list[Milestone]) -> str:
    return json.dumps([m.model_dump(mode="json") for m in milestones])
