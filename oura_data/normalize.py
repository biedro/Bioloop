from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


SLEEP_PHASE_LABELS = {
    "1": "deep",
    "2": "light",
    "3": "rem",
    "4": "awake",
}

EXCLUDED_SLEEP_TYPES = {"deleted", "rest"}


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def minute_of_day(dt: datetime) -> float:
    return dt.hour * 60 + dt.minute + dt.second / 60 + dt.microsecond / 60_000_000


def _split_segment_at_midnight(start: datetime, end: datetime) -> list[tuple[float, float]]:
    pieces: list[tuple[float, float]] = []
    cursor = start
    while cursor < end:
        next_midnight = (cursor + timedelta(days=1)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        piece_end = min(end, next_midnight)
        start_minute = minute_of_day(cursor)
        end_minute = minute_of_day(piece_end)
        if end_minute == 0 and piece_end > cursor:
            end_minute = 1440.0
        pieces.append((start_minute, end_minute))
        cursor = piece_end
    return pieces


def _phase_runs(phase_string: str) -> list[tuple[str, int, int]]:
    if not phase_string:
        return []

    runs: list[tuple[str, int, int]] = []
    current = phase_string[0]
    start = 0
    for index, phase in enumerate(phase_string[1:], start=1):
        if phase == current:
            continue
        runs.append((current, start, index))
        current = phase
        start = index
    runs.append((current, start, len(phase_string)))
    return runs


def sleep_period_row(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": doc["id"],
        "day": doc.get("day"),
        "type": doc.get("type"),
        "bedtime_start": doc.get("bedtime_start"),
        "bedtime_end": doc.get("bedtime_end"),
        "time_in_bed": doc.get("time_in_bed"),
        "total_sleep_duration": doc.get("total_sleep_duration"),
        "awake_time": doc.get("awake_time"),
        "deep_sleep_duration": doc.get("deep_sleep_duration"),
        "light_sleep_duration": doc.get("light_sleep_duration"),
        "rem_sleep_duration": doc.get("rem_sleep_duration"),
        "efficiency": doc.get("efficiency"),
        "average_hrv": doc.get("average_hrv"),
        "average_heart_rate": doc.get("average_heart_rate"),
        "lowest_heart_rate": doc.get("lowest_heart_rate"),
        "average_breath": doc.get("average_breath"),
        "readiness_score_delta": doc.get("readiness_score_delta"),
        "sleep_score_delta": doc.get("sleep_score_delta"),
        "low_battery_alert": int(bool(doc.get("low_battery_alert"))),
    }


def normalize_sleep_documents(docs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    periods: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []

    for doc in docs:
        if doc.get("type") in EXCLUDED_SLEEP_TYPES:
            continue
        if not doc.get("id") or not doc.get("bedtime_start") or not doc.get("bedtime_end"):
            continue

        periods.append(sleep_period_row(doc))
        start = parse_datetime(doc["bedtime_start"])

        for source_resolution, field_name, seconds_per_sample in (
            ("5_min", "sleep_phase_5_min", 300),
            ("30_sec", "sleep_phase_30_sec", 30),
        ):
            phase_string = doc.get(field_name)
            if not phase_string:
                continue

            sequence = 0
            for phase, run_start, run_end in _phase_runs(phase_string):
                phase_start = start + timedelta(seconds=run_start * seconds_per_sample)
                phase_end = start + timedelta(seconds=run_end * seconds_per_sample)
                for start_minute, end_minute in _split_segment_at_midnight(phase_start, phase_end):
                    if start_minute >= end_minute:
                        continue
                    segments.append(
                        {
                            "document_id": doc["id"],
                            "day": doc.get("day"),
                            "sequence": sequence,
                            "source_resolution": source_resolution,
                            "phase": phase,
                            "phase_label": SLEEP_PHASE_LABELS.get(phase, "unknown"),
                            "is_sleep": int(phase in {"1", "2", "3"}),
                            "start_time": phase_start.isoformat(),
                            "end_time": phase_end.isoformat(),
                            "start_minute": start_minute,
                            "end_minute": end_minute,
                        }
                    )
                    sequence += 1

    return periods, segments


def normalize_daily_metric(endpoint: str, docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for doc in docs:
        day = doc.get("day")
        if not day:
            continue
        rows.append(
            {
                "endpoint": endpoint,
                "day": day,
                "score": doc.get("score"),
                "timestamp": doc.get("timestamp"),
            }
        )
    return rows


def normalize_heart_rate(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for doc in docs:
        if not doc.get("timestamp"):
            continue
        rows.append(
            {
                "timestamp": doc["timestamp"],
                "timestamp_unix": doc.get("timestamp_unix"),
                "bpm": doc.get("bpm"),
                "source": doc.get("source"),
            }
        )
    return rows


def normalize_workouts(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for doc in docs:
        doc_id = doc.get("id")
        if not doc_id:
            continue
        rows.append(
            {
                "id": doc_id,
                "day": doc.get("day"),
                "activity": doc.get("activity"),
                "intensity": doc.get("intensity"),
                "start_datetime": doc.get("start_datetime"),
                "end_datetime": doc.get("end_datetime"),
                "calories": doc.get("calories"),
                "distance": doc.get("distance"),
            }
        )
    return rows


def normalize_tags(endpoint: str, docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for doc in docs:
        doc_id = doc.get("id")
        if not doc_id:
            continue
        rows.append(
            {
                "id": doc_id,
                "endpoint": endpoint,
                "day": doc.get("day"),
                "text": doc.get("text") or doc.get("tag_type_code") or doc.get("name"),
                "start_datetime": doc.get("start_datetime") or doc.get("timestamp"),
                "end_datetime": doc.get("end_datetime"),
            }
        )
    return rows
