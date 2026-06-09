from __future__ import annotations

from oura_data.storage import OuraStore


def test_store_endpoint_upserts_raw_and_sleep_tables_idempotently(tmp_path):
    store = OuraStore(tmp_path / "oura.sqlite3")
    docs = [
        {
            "id": "sleep-1",
            "day": "2026-01-02",
            "type": "long_sleep",
            "bedtime_start": "2026-01-01T23:45:00+02:00",
            "bedtime_end": "2026-01-02T00:15:00+02:00",
            "time_in_bed": 1800,
            "total_sleep_duration": 1800,
            "low_battery_alert": False,
            "sleep_phase_5_min": "111111",
        }
    ]

    store.store_endpoint("sleep", docs)
    store.store_endpoint("sleep", docs)

    assert len(store.dataframe("raw_documents")) == 1
    assert len(store.dataframe("sleep_periods")) == 1
    assert len(store.dataframe("sleep_segments")) == 2


def test_store_endpoint_upserts_daily_metrics_idempotently(tmp_path):
    store = OuraStore(tmp_path / "oura.sqlite3")
    docs = [{"id": "daily-1", "day": "2026-01-02", "score": 88, "timestamp": "2026-01-02T08:00:00+02:00"}]

    store.store_endpoint("daily_sleep", docs)
    store.store_endpoint("daily_sleep", [{**docs[0], "score": 90}])

    rows = store.dataframe("daily_metrics")
    assert len(rows) == 1
    assert rows.iloc[0]["score"] == 90
