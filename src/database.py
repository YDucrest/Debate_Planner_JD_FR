from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import Event, School, Team

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"


def _connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                categories_json TEXT NOT NULL,
                number_of_rooms INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS schools (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS teams (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                school_id TEXT NOT NULL,
                school_name TEXT NOT NULL,
                category TEXT NOT NULL,
                label TEXT NOT NULL,
                participant_1 TEXT NOT NULL DEFAULT '',
                participant_2 TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
                FOREIGN KEY(school_id) REFERENCES schools(id) ON DELETE CASCADE
            );
            """
        )


def save_event(
    event: Event,
    schools: list[School],
    teams: list[Team],
    db_path: Path = DB_PATH,
) -> None:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO events(id, name, categories_json, number_of_rooms, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                categories_json=excluded.categories_json,
                number_of_rooms=excluded.number_of_rooms,
                updated_at=excluded.updated_at
            """,
            (
                event.id,
                event.name,
                json.dumps(event.categories, ensure_ascii=False),
                event.number_of_rooms,
                now,
            ),
        )
        conn.execute("DELETE FROM teams WHERE event_id = ?", (event.id,))
        conn.execute("DELETE FROM schools WHERE event_id = ?", (event.id,))
        conn.executemany(
            "INSERT INTO schools(id, event_id, name, category) VALUES (?, ?, ?, ?)",
            [(s.id, s.event_id, s.name, s.category) for s in schools],
        )
        conn.executemany(
            """
            INSERT INTO teams(
                id, event_id, school_id, school_name, category, label, participant_1, participant_2
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    t.id,
                    t.event_id,
                    t.school_id,
                    t.school_name,
                    t.category,
                    t.label,
                    t.participant_1,
                    t.participant_2,
                )
                for t in teams
            ],
        )


def list_events(db_path: Path = DB_PATH) -> list[dict[str, str]]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, name, updated_at FROM events ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def load_event(
    event_id: str, db_path: Path = DB_PATH
) -> tuple[Event, list[School], list[Team]]:
    init_db(db_path)
    with _connect(db_path) as conn:
        event_row = conn.execute(
            "SELECT * FROM events WHERE id = ?", (event_id,)
        ).fetchone()
        if event_row is None:
            raise KeyError(f"Événement introuvable : {event_id}")
        school_rows = conn.execute(
            "SELECT * FROM schools WHERE event_id = ? ORDER BY name, category", (event_id,)
        ).fetchall()
        team_rows = conn.execute(
            "SELECT * FROM teams WHERE event_id = ? ORDER BY school_name, label", (event_id,)
        ).fetchall()

    event = Event(
        id=event_row["id"],
        name=event_row["name"],
        categories=json.loads(event_row["categories_json"]),
        number_of_rooms=int(event_row["number_of_rooms"]),
    )
    schools = [
        School(
            id=row["id"],
            event_id=row["event_id"],
            name=row["name"],
            category=row["category"],
        )
        for row in school_rows
    ]
    teams = [
        Team(
            id=row["id"],
            event_id=row["event_id"],
            school_id=row["school_id"],
            school_name=row["school_name"],
            category=row["category"],
            label=row["label"],
            participant_1=row["participant_1"],
            participant_2=row["participant_2"],
        )
        for row in team_rows
    ]
    return event, schools, teams


def delete_event(event_id: str, db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
