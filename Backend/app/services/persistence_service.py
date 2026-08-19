"""Small SQLite-backed storage for local FaultLens data."""

import json
import logging
import os
import sqlite3
from pathlib import Path

from pydantic import ValidationError

from app.models.experiment_response import ExperimentRunData
from app.models.system import System

logger = logging.getLogger(__name__)


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

    def get_system(self, system_id: str) -> System | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM systems WHERE id = ?", (system_id,)
            ).fetchone()
        if row is None:
            return None
        return System.model_validate_json(row["payload"])

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

        results = []
        for row in rows:
            try:
                results.append(ExperimentRunData.model_validate_json(row["payload"]))
            except ValidationError:
                # A row persisted under an older schema (e.g. before
                # ai_analysis became an AIInsight wrapper) can't be
                # deserialized against the current model. Skip it rather
                # than failing the whole history request — the rest of a
                # system's real history should still be usable.
                logger.warning("Skipping experiment_history row that no longer matches the current schema")
        return results

    def get_experiment(self, run_id: str) -> ExperimentRunData | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM experiment_history WHERE run_id = ?", (run_id,)
            ).fetchone()
        if row is None:
            return None
        try:
            return ExperimentRunData.model_validate_json(row["payload"])
        except ValidationError:
            logger.warning("experiment_history row '%s' no longer matches the current schema", run_id)
            return None
