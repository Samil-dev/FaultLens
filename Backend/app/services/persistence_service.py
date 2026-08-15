"""Small SQLite-backed storage for local CodeTwin MVP data."""

import json
import os
import sqlite3
from pathlib import Path

from app.models.experiment_response import ExperimentRunData
from app.models.system import System


class PersistenceService:
    """Stores submitted systems and completed experiment results locally."""

    def __init__(self) -> None:
        configured_path = os.getenv("CODETWIN_DATABASE_PATH")
        self.database_path = (
            Path(configured_path)
            if configured_path
            else Path(__file__).resolve().parents[2] / "codetwin.sqlite3"
        )
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS systems (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            connection.execute("CREATE TABLE IF NOT EXISTS experiment_history (run_id TEXT PRIMARY KEY, system_id TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT NOT NULL)")

    def save_system(self, system: System) -> System:
        with self._connect() as connection:
            connection.execute("INSERT OR REPLACE INTO systems (id, payload) VALUES (?, ?)", (system.id, json.dumps(system.model_dump(mode="json"))))
        return system

    def list_systems(self) -> list[System]:
        with self._connect() as connection:
            rows = connection.execute("SELECT payload FROM systems ORDER BY id").fetchall()
        return [System.model_validate_json(row["payload"]) for row in rows]

    def save_experiment(self, system_id: str, result: ExperimentRunData) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO experiment_history (run_id, system_id, created_at, payload) VALUES (?, ?, ?, ?)",
                (result.run.id, system_id, result.run.created_at.isoformat(), json.dumps(result.model_dump(mode="json"))),
            )

    def list_experiments(self, system_id: str | None = None) -> list[ExperimentRunData]:
        query, parameters = "SELECT payload FROM experiment_history", ()
        if system_id:
            query, parameters = f"{query} WHERE system_id = ?", (system_id,)
        with self._connect() as connection:
            rows = connection.execute(f"{query} ORDER BY created_at DESC", parameters).fetchall()
        return [ExperimentRunData.model_validate_json(row["payload"]) for row in rows]
