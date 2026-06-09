from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .normalize import (
    normalize_daily_metric,
    normalize_heart_rate,
    normalize_sleep_documents,
    normalize_tags,
    normalize_workouts,
)


DAILY_METRIC_ENDPOINTS = {
    "daily_sleep",
    "daily_readiness",
    "daily_activity",
    "daily_stress",
    "daily_resilience",
    "daily_spo2",
    "daily_cardiovascular_age",
    "vO2_max",
}


class OuraStore:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS raw_documents (
                  endpoint TEXT NOT NULL,
                  document_id TEXT NOT NULL,
                  day TEXT,
                  timestamp TEXT,
                  payload TEXT NOT NULL,
                  fetched_at TEXT NOT NULL,
                  PRIMARY KEY (endpoint, document_id)
                );

                CREATE TABLE IF NOT EXISTS sync_status (
                  endpoint TEXT PRIMARY KEY,
                  status TEXT NOT NULL,
                  started_at TEXT,
                  completed_at TEXT,
                  rows_fetched INTEGER DEFAULT 0,
                  error TEXT
                );

                CREATE TABLE IF NOT EXISTS sleep_periods (
                  id TEXT PRIMARY KEY,
                  day TEXT,
                  type TEXT,
                  bedtime_start TEXT,
                  bedtime_end TEXT,
                  time_in_bed INTEGER,
                  total_sleep_duration INTEGER,
                  awake_time INTEGER,
                  deep_sleep_duration INTEGER,
                  light_sleep_duration INTEGER,
                  rem_sleep_duration INTEGER,
                  efficiency INTEGER,
                  average_hrv INTEGER,
                  average_heart_rate REAL,
                  lowest_heart_rate INTEGER,
                  average_breath REAL,
                  readiness_score_delta INTEGER,
                  sleep_score_delta INTEGER,
                  low_battery_alert INTEGER
                );

                CREATE TABLE IF NOT EXISTS sleep_segments (
                  document_id TEXT NOT NULL,
                  day TEXT,
                  sequence INTEGER NOT NULL,
                  source_resolution TEXT NOT NULL,
                  phase TEXT,
                  phase_label TEXT,
                  is_sleep INTEGER,
                  start_time TEXT,
                  end_time TEXT,
                  start_minute REAL,
                  end_minute REAL,
                  PRIMARY KEY (document_id, sequence, source_resolution)
                );

                CREATE TABLE IF NOT EXISTS daily_metrics (
                  endpoint TEXT NOT NULL,
                  day TEXT NOT NULL,
                  score REAL,
                  timestamp TEXT,
                  payload TEXT NOT NULL,
                  PRIMARY KEY (endpoint, day)
                );

                CREATE TABLE IF NOT EXISTS heart_rate (
                  timestamp TEXT PRIMARY KEY,
                  timestamp_unix INTEGER,
                  bpm INTEGER,
                  source TEXT,
                  payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workouts (
                  id TEXT PRIMARY KEY,
                  day TEXT,
                  activity TEXT,
                  intensity TEXT,
                  start_datetime TEXT,
                  end_datetime TEXT,
                  calories REAL,
                  distance REAL,
                  payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tags (
                  id TEXT PRIMARY KEY,
                  endpoint TEXT,
                  day TEXT,
                  text TEXT,
                  start_datetime TEXT,
                  end_datetime TEXT,
                  payload TEXT NOT NULL
                );
                """
            )

    def mark_sync_started(self, endpoint: str) -> None:
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sync_status(endpoint, status, started_at, completed_at, rows_fetched, error)
                VALUES (?, 'running', ?, NULL, 0, NULL)
                ON CONFLICT(endpoint) DO UPDATE SET
                  status='running',
                  started_at=excluded.started_at,
                  completed_at=NULL,
                  rows_fetched=0,
                  error=NULL
                """,
                (endpoint, now),
            )

    def mark_sync_complete(self, endpoint: str, rows_fetched: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE sync_status
                SET status='ok', completed_at=?, rows_fetched=?, error=NULL
                WHERE endpoint=?
                """,
                (utc_now(), rows_fetched, endpoint),
            )

    def mark_sync_error(self, endpoint: str, status: str, error: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sync_status(endpoint, status, started_at, completed_at, rows_fetched, error)
                VALUES (?, ?, ?, ?, 0, ?)
                ON CONFLICT(endpoint) DO UPDATE SET
                  status=excluded.status,
                  completed_at=excluded.completed_at,
                  error=excluded.error
                """,
                (endpoint, status, utc_now(), utc_now(), error),
            )

    def store_endpoint(self, endpoint: str, docs: list[dict[str, Any]]) -> int:
        with self.connect() as conn:
            self._upsert_raw(conn, endpoint, docs)
            if endpoint == "sleep":
                periods, segments = normalize_sleep_documents(docs)
                self._upsert_rows(conn, "sleep_periods", periods, "id")
                self._upsert_sleep_segments(conn, segments)
            elif endpoint in DAILY_METRIC_ENDPOINTS:
                rows = normalize_daily_metric(endpoint, docs)
                self._upsert_daily_metrics(conn, endpoint, rows, docs)
            elif endpoint == "heartrate":
                rows = normalize_heart_rate(docs)
                self._upsert_payload_rows(conn, "heart_rate", rows, docs, "timestamp")
            elif endpoint == "workout":
                rows = normalize_workouts(docs)
                self._upsert_payload_rows(conn, "workouts", rows, docs, "id")
            elif endpoint in {"tag", "enhanced_tag"}:
                rows = normalize_tags(endpoint, docs)
                self._upsert_payload_rows(conn, "tags", rows, docs, "id")
        return len(docs)

    def _upsert_raw(self, conn: sqlite3.Connection, endpoint: str, docs: list[dict[str, Any]]) -> None:
        rows = []
        fetched_at = utc_now()
        for doc in docs:
            payload = json.dumps(doc, sort_keys=True)
            rows.append(
                (
                    endpoint,
                    document_id_for(doc),
                    doc.get("day"),
                    doc.get("timestamp") or doc.get("start_datetime") or doc.get("bedtime_start"),
                    payload,
                    fetched_at,
                )
            )
        conn.executemany(
            """
            INSERT INTO raw_documents(endpoint, document_id, day, timestamp, payload, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(endpoint, document_id) DO UPDATE SET
              day=excluded.day,
              timestamp=excluded.timestamp,
              payload=excluded.payload,
              fetched_at=excluded.fetched_at
            """,
            rows,
        )

    def _upsert_rows(
        self,
        conn: sqlite3.Connection,
        table: str,
        rows: list[dict[str, Any]],
        key_column: str,
    ) -> None:
        if not rows:
            return
        columns = list(rows[0].keys())
        placeholders = ", ".join("?" for _ in columns)
        update_columns = [column for column in columns if column != key_column]
        update_sql = ", ".join(f"{column}=excluded.{column}" for column in update_columns)
        conn.executemany(
            f"""
            INSERT INTO {table}({", ".join(columns)})
            VALUES ({placeholders})
            ON CONFLICT({key_column}) DO UPDATE SET {update_sql}
            """,
            [tuple(row.get(column) for column in columns) for row in rows],
        )

    def _upsert_sleep_segments(self, conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        columns = list(rows[0].keys())
        placeholders = ", ".join("?" for _ in columns)
        update_columns = [
            column
            for column in columns
            if column not in {"document_id", "sequence", "source_resolution"}
        ]
        update_sql = ", ".join(f"{column}=excluded.{column}" for column in update_columns)
        conn.executemany(
            f"""
            INSERT INTO sleep_segments({", ".join(columns)})
            VALUES ({placeholders})
            ON CONFLICT(document_id, sequence, source_resolution) DO UPDATE SET {update_sql}
            """,
            [tuple(row.get(column) for column in columns) for row in rows],
        )

    def _upsert_daily_metrics(
        self,
        conn: sqlite3.Connection,
        endpoint: str,
        rows: list[dict[str, Any]],
        docs: list[dict[str, Any]],
    ) -> None:
        payload_by_day = {doc.get("day"): json.dumps(doc, sort_keys=True) for doc in docs}
        conn.executemany(
            """
            INSERT INTO daily_metrics(endpoint, day, score, timestamp, payload)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(endpoint, day) DO UPDATE SET
              score=excluded.score,
              timestamp=excluded.timestamp,
              payload=excluded.payload
            """,
            [
                (
                    row["endpoint"],
                    row["day"],
                    row.get("score"),
                    row.get("timestamp"),
                    payload_by_day.get(row["day"], "{}"),
                )
                for row in rows
            ],
        )

    def _upsert_payload_rows(
        self,
        conn: sqlite3.Connection,
        table: str,
        rows: list[dict[str, Any]],
        docs: list[dict[str, Any]],
        key_column: str,
    ) -> None:
        if not rows:
            return
        payload_by_id = {str(doc.get(key_column)): json.dumps(doc, sort_keys=True) for doc in docs}
        if key_column == "timestamp":
            payload_by_id = {str(doc.get("timestamp")): json.dumps(doc, sort_keys=True) for doc in docs}
        rows_with_payload = [{**row, "payload": payload_by_id.get(str(row[key_column]), "{}")} for row in rows]
        self._upsert_rows(conn, table, rows_with_payload, key_column)

    def dataframe(self, table: str) -> pd.DataFrame:
        with self.connect() as conn:
            return pd.read_sql_query(f"SELECT * FROM {table}", conn)

    def query(self, sql: str, params: Iterable[Any] = ()) -> pd.DataFrame:
        with self.connect() as conn:
            return pd.read_sql_query(sql, conn, params=tuple(params))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def document_id_for(doc: dict[str, Any]) -> str:
    for key in ("id", "timestamp", "timestamp_unix", "start_datetime", "bedtime_start"):
        value = doc.get(key)
        if value is not None:
            return str(value)
    payload = json.dumps(doc, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
