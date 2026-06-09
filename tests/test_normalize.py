from __future__ import annotations

from oura_data.normalize import normalize_sleep_documents


def test_sleep_stage_segments_split_across_midnight():
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

    periods, segments = normalize_sleep_documents(docs)

    assert len(periods) == 1
    assert len(segments) == 2
    assert segments[0]["start_minute"] == 23 * 60 + 45
    assert segments[0]["end_minute"] == 1440
    assert segments[1]["start_minute"] == 0
    assert segments[1]["end_minute"] == 15


def test_rest_and_deleted_sleep_periods_are_excluded():
    docs = [
        {
            "id": "rest-1",
            "day": "2026-01-02",
            "type": "rest",
            "bedtime_start": "2026-01-02T10:00:00+02:00",
            "bedtime_end": "2026-01-02T10:30:00+02:00",
            "time_in_bed": 1800,
        },
        {
            "id": "deleted-1",
            "day": "2026-01-02",
            "type": "deleted",
            "bedtime_start": "2026-01-02T23:00:00+02:00",
            "bedtime_end": "2026-01-03T07:00:00+02:00",
            "time_in_bed": 28_800,
        },
    ]

    periods, segments = normalize_sleep_documents(docs)

    assert periods == []
    assert segments == []


def test_missing_phase_string_keeps_sleep_period_without_segments():
    docs = [
        {
            "id": "sleep-2",
            "day": "2026-01-03",
            "type": "sleep",
            "bedtime_start": "2026-01-03T14:00:00+02:00",
            "bedtime_end": "2026-01-03T14:30:00+02:00",
            "time_in_bed": 1800,
            "low_battery_alert": False,
        }
    ]

    periods, segments = normalize_sleep_documents(docs)

    assert len(periods) == 1
    assert segments == []
