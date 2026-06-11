from __future__ import annotations

import pandas as pd
import pytest

from oura_data.artifacts import (
    default_export_settings,
    export_is_privacy_safe,
    generate_life_rings_story,
    redact_export_metadata,
    validate_narrative_text,
)


def test_life_rings_story_has_evidence_and_safe_language():
    periods = pd.DataFrame(
        [
            {
                "day": "2026-01-01",
                "bedtime_start": "2026-01-01T22:30:00+02:00",
                "total_sleep_duration": 8 * 3600,
            },
            {
                "day": "2026-01-02",
                "bedtime_start": "2026-01-02T22:35:00+02:00",
                "total_sleep_duration": 7.5 * 3600,
            },
            {
                "day": "2026-01-04",
                "bedtime_start": "2026-01-04T22:40:00+02:00",
                "total_sleep_duration": 8.25 * 3600,
            },
        ]
    )
    segments = pd.DataFrame(
        [
            {"day": "2026-01-01", "source_resolution": "5_min", "is_sleep": 1},
            {"day": "2026-01-02", "source_resolution": "5_min", "is_sleep": 1},
        ]
    )
    moments = pd.DataFrame(
        [
            {
                "start_day": "2026-01-02",
                "end_day": "2026-01-02",
                "title": "Quiet weekend",
            }
        ]
    )

    story = generate_life_rings_story(periods, segments, moments=moments)

    assert story["caption"] == "Here are 3 nights of your life."
    assert story["evidence"]
    assert any("Missing days visible in range: 1" in item for item in story["evidence"])
    assert any("Quiet weekend" in item for item in story["evidence"])
    for text in [story["caption"], *story["evidence"]]:
        validate_narrative_text(text)


@pytest.mark.parametrize(
    "text",
    [
        "You should improve this.",
        "This caused your insomnia.",
        "AI detected poor lifestyle choices.",
        "You were diagnosed with burnout.",
    ],
)
def test_narrative_validation_rejects_banned_language(text):
    with pytest.raises(ValueError):
        validate_narrative_text(text)


def test_export_defaults_are_privacy_safe_and_redact_raw_values():
    settings = default_export_settings()
    metadata = {
        "template": "Life Rings",
        "average_hrv": 42,
        "lowest_heart_rate": 51,
        "privacy": "private",
    }

    redacted = redact_export_metadata(metadata, settings)

    assert export_is_privacy_safe(settings)
    assert settings["include_raw_values"] is False
    assert "average_hrv" not in redacted
    assert "lowest_heart_rate" not in redacted
    assert redacted["template"] == "Life Rings"
