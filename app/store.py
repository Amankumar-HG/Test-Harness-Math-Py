"""SQLite persistence for learner skill mastery."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from pathlib import Path
from typing import Any

from app.engine.mastery import default_skill_state
from app.engine.skills import SKILLS

_lock = threading.Lock()


class LearnerStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with _lock:
            conn = self._connect()
            try:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS learners (
                        id TEXT PRIMARY KEY,
                        created_at REAL NOT NULL,
                        display_name TEXT
                    );
                    CREATE TABLE IF NOT EXISTS skill_state (
                        learner_id TEXT NOT NULL,
                        skill_id TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        PRIMARY KEY (learner_id, skill_id),
                        FOREIGN KEY (learner_id) REFERENCES learners(id)
                    );
                    CREATE TABLE IF NOT EXISTS attempt_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        learner_id TEXT NOT NULL,
                        skill_id TEXT NOT NULL,
                        difficulty INTEGER NOT NULL,
                        correct INTEGER NOT NULL,
                        prompt TEXT NOT NULL,
                        user_answer TEXT,
                        created_at REAL NOT NULL
                    );
                    """
                )
                conn.commit()
            finally:
                conn.close()

    def create_learner(self, display_name: str | None = None) -> str:
        learner_id = str(uuid.uuid4())
        import time

        with _lock:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT INTO learners (id, created_at, display_name) VALUES (?, ?, ?)",
                    (learner_id, time.time(), display_name or "Learner"),
                )
                for skill_id in SKILLS:
                    conn.execute(
                        "INSERT INTO skill_state (learner_id, skill_id, payload) VALUES (?, ?, ?)",
                        (learner_id, skill_id, json.dumps(default_skill_state())),
                    )
                conn.commit()
            finally:
                conn.close()
        return learner_id

    def ensure_learner(self, learner_id: str | None) -> str:
        if learner_id and self.learner_exists(learner_id):
            return learner_id
        return self.create_learner()

    def learner_exists(self, learner_id: str) -> bool:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT 1 FROM learners WHERE id = ?", (learner_id,)
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def get_all_states(self, learner_id: str) -> dict[str, dict[str, Any]]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT skill_id, payload FROM skill_state WHERE learner_id = ?",
                (learner_id,),
            ).fetchall()
            states = {sid: default_skill_state() for sid in SKILLS}
            for row in rows:
                states[row["skill_id"]] = json.loads(row["payload"])
            return states
        finally:
            conn.close()

    def save_skill_state(self, learner_id: str, skill_id: str, state: dict[str, Any]) -> None:
        with _lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO skill_state (learner_id, skill_id, payload)
                    VALUES (?, ?, ?)
                    ON CONFLICT(learner_id, skill_id) DO UPDATE SET payload = excluded.payload
                    """,
                    (learner_id, skill_id, json.dumps(state)),
                )
                conn.commit()
            finally:
                conn.close()

    def log_attempt(
        self,
        learner_id: str,
        *,
        skill_id: str,
        difficulty: int,
        correct: bool,
        prompt: str,
        user_answer: str | None,
        created_at: float,
    ) -> None:
        with _lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO attempt_log
                    (learner_id, skill_id, difficulty, correct, prompt, user_answer, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        learner_id,
                        skill_id,
                        difficulty,
                        1 if correct else 0,
                        prompt,
                        user_answer,
                        created_at,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def recent_attempts(self, learner_id: str, limit: int = 10) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT skill_id, difficulty, correct, prompt, user_answer, created_at
                FROM attempt_log
                WHERE learner_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (learner_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
