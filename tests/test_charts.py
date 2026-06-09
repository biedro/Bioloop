from __future__ import annotations

import numpy as np
import pandas as pd

from oura_data.charts import DATE_GUIDE_MONTHS, make_sleep_tree_rings, sleep_ring_stats


def test_sleep_tree_rings_renders_nonblank_canvas():
    periods = pd.DataFrame(
        [
            {"id": "sleep-1", "day": "2026-01-02"},
            {"id": "sleep-2", "day": "2026-01-03"},
        ]
    )
    segments = pd.DataFrame(
        [
            {
                "document_id": "sleep-1",
                "day": "2026-01-02",
                "source_resolution": "5_min",
                "is_sleep": 1,
                "start_minute": 23 * 60,
                "end_minute": 1440,
            },
            {
                "document_id": "sleep-1",
                "day": "2026-01-02",
                "source_resolution": "5_min",
                "is_sleep": 1,
                "start_minute": 0,
                "end_minute": 7 * 60,
            },
        ]
    )

    fig = make_sleep_tree_rings(segments, periods)

    assert fig is not None
    fig.canvas.draw()
    image = np.asarray(fig.canvas.buffer_rgba())
    patch_colors = [patch.get_facecolor() for patch in fig.axes[0].patches]
    assert image.std() > 0
    assert any(color[2] > color[0] for color in patch_colors)


def test_sleep_tree_rings_handles_datetime_segment_days_after_ui_filter():
    periods = pd.DataFrame(
        [
            {"id": "sleep-1", "day": "2026-01-02"},
            {"id": "sleep-2", "day": "2026-01-03"},
        ]
    )
    segments = pd.DataFrame(
        [
            {
                "document_id": "sleep-1",
                "day": "2026-01-02",
                "source_resolution": "5_min",
                "is_sleep": 1,
                "start_minute": 0,
                "end_minute": 420,
            },
            {
                "document_id": "sleep-2",
                "day": "2026-01-03",
                "source_resolution": "30_sec",
                "is_sleep": 1,
                "start_minute": 60,
                "end_minute": 120,
            },
        ]
    )
    segments["day"] = pd.to_datetime(segments["day"])

    stats = sleep_ring_stats(segments, periods, resolution="5_min")
    fig = make_sleep_tree_rings(segments, periods, resolution="5_min")

    assert stats["days"] == 2
    assert stats["segments_5_min"] == 1
    assert stats["segments_30_sec"] == 1
    assert stats["plotted_segments"] == 1
    assert fig is not None


def test_sleep_tree_rings_supports_stage_colors_date_guides_and_events():
    periods = pd.DataFrame(
        [
            {"id": "sleep-1", "day": "2026-01-02"},
            {"id": "sleep-2", "day": "2026-02-03"},
        ]
    )
    segments = pd.DataFrame(
        [
            {
                "document_id": "sleep-1",
                "day": "2026-01-02",
                "source_resolution": "5_min",
                "phase_label": "deep",
                "is_sleep": 1,
                "start_minute": 0,
                "end_minute": 120,
            },
            {
                "document_id": "sleep-1",
                "day": "2026-01-02",
                "source_resolution": "5_min",
                "phase_label": "light",
                "is_sleep": 1,
                "start_minute": 120,
                "end_minute": 300,
            },
            {
                "document_id": "sleep-2",
                "day": "2026-02-03",
                "source_resolution": "5_min",
                "phase_label": "rem",
                "is_sleep": 1,
                "start_minute": 300,
                "end_minute": 420,
            },
        ]
    )
    events = pd.DataFrame(
        [
            {
                "day": "2026-02-03",
                "kind": "workout",
                "color_key": "workout",
                "start_datetime": "2026-02-03T18:00:00+02:00",
                "end_datetime": "2026-02-03T18:45:00+02:00",
            }
        ]
    )

    fig = make_sleep_tree_rings(
        segments,
        periods,
        sleep_color_mode="Sleep stages",
        date_guides=DATE_GUIDE_MONTHS,
        events=events,
    )

    assert fig is not None
    patch_colors = [patch.get_facecolor() for patch in fig.axes[0].patches]
    assert len(patch_colors) >= 6
