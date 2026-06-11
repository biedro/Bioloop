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


def test_store_artifacts_moments_and_feedback_round_trip(tmp_path):
    store = OuraStore(tmp_path / "oura.sqlite3")

    artifact_id = store.save_artifact(
        artifact_type="life_rings",
        title="A quiet record",
        date_range={"start": "2026-01-01", "end": "2026-01-31"},
        settings={"template": "life_rings", "export": {"include_raw_values": False}},
        narrative={"caption": "Here are 31 nights of your life.", "evidence": ["Nights included: 31"]},
        privacy_level="share-safe",
    )
    moment_id = store.save_moment(
        start_day="2026-01-12",
        end_day="2026-01-18",
        title="Training block",
        note="Private context",
    )
    feedback_id = store.record_feedback(kind="resonance_rating", value=5, artifact_id=artifact_id)

    artifacts = store.list_artifacts()
    moments = store.list_moments()
    feedback = store.dataframe("beta_feedback")

    assert artifacts.iloc[0]["id"] == artifact_id
    assert artifacts.iloc[0]["privacy_level"] == "share-safe"
    assert moments.iloc[0]["id"] == moment_id
    assert moments.iloc[0]["source"] == "user"
    assert feedback.iloc[0]["id"] == feedback_id
    assert feedback.iloc[0]["value"] == "5"


def test_store_lists_overlapping_moments_and_deletes_beta_objects(tmp_path):
    store = OuraStore(tmp_path / "oura.sqlite3")
    artifact_id = store.save_artifact(
        artifact_type="life_rings",
        title="Winter rings",
        date_range={"start": "2026-01-01", "end": "2026-01-31"},
        settings={"template": "life_rings"},
        narrative={"caption": "Here are 31 nights of your life."},
        privacy_level="private",
    )
    overlapping_id = store.save_moment(
        start_day="2026-01-10",
        end_day="2026-01-12",
        title="Recovery period",
    )
    store.save_moment(
        start_day="2026-02-10",
        end_day="2026-02-12",
        title="Later trip",
    )

    overlap = store.list_moments_between("2026-01-01", "2026-01-31")
    selected = store.get_artifact(artifact_id)

    assert len(overlap) == 1
    assert overlap.iloc[0]["id"] == overlapping_id
    assert selected.iloc[0]["title"] == "Winter rings"

    store.delete_moment(overlapping_id)
    store.delete_artifact(artifact_id)

    assert store.list_moments_between("2026-01-01", "2026-01-31").empty
    assert store.get_artifact(artifact_id).empty
