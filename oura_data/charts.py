from __future__ import annotations

from datetime import datetime, timedelta
import math

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


AWAKE_ORANGE = "#f2a04b"
SLEEP_BLUE = "#284aa8"
BACKGROUND = "#f7f3ed"
TEXT = "#5d5d5d"
MONTH_GUIDE = "#7b7b7b"

PALETTE_PRESETS = {
    "Current": {
        "awake": AWAKE_ORANGE,
        "sleep": SLEEP_BLUE,
        "deep": "#173a8a",
        "light": "#4169c1",
        "rem": "#6f7fd6",
        "workout": "#d04f3a",
        "tag": "#7b61b8",
        "month_guide": MONTH_GUIDE,
        "winter": "#5c7fb8",
        "spring": "#6fa06f",
        "summer": "#d9a646",
        "autumn": "#b8754b",
    },
    "Complementary": {
        "awake": "#f2a04b",
        "sleep": "#284aa8",
        "deep": "#102f70",
        "light": "#4c78d8",
        "rem": "#7d67c8",
        "workout": "#c9423a",
        "tag": "#168a72",
        "month_guide": "#6d6d6d",
        "winter": "#4f75bd",
        "spring": "#4f9f77",
        "summer": "#d99a32",
        "autumn": "#b8663f",
    },
    "Colorblind Safe": {
        "awake": "#f6c267",
        "sleep": "#4477aa",
        "deep": "#332288",
        "light": "#88ccee",
        "rem": "#aa4499",
        "workout": "#cc6677",
        "tag": "#117733",
        "month_guide": "#666666",
        "winter": "#4477aa",
        "spring": "#228833",
        "summer": "#ccbb44",
        "autumn": "#ee7733",
    },
    "Viridis/Cividis": {
        "awake": "#f2a04b",
        "sleep": "#31688e",
        "deep": "#440154",
        "light": "#21918c",
        "rem": "#35b779",
        "workout": "#fde725",
        "tag": "#3b528b",
        "month_guide": "#6b6b6b",
        "winter": "#3b528b",
        "spring": "#21918c",
        "summer": "#fde725",
        "autumn": "#b58900",
    },
}

SLEEP_PHASE_COLOR_KEYS = {
    "deep": "deep",
    "light": "light",
    "rem": "rem",
    "awake": "awake",
}

SEASON_BY_MONTH = {
    12: "winter",
    1: "winter",
    2: "winter",
    3: "spring",
    4: "spring",
    5: "spring",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "autumn",
    10: "autumn",
    11: "autumn",
}

DATE_GUIDE_NONE = "None"
DATE_GUIDE_MONTHS = "Month rings"
DATE_GUIDE_SEASONS = "Season bands"


def _with_day_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["_day_dt"] = pd.to_datetime(out["day"], errors="coerce")
    out = out.dropna(subset=["_day_dt"])
    out["_day_key"] = out["_day_dt"].dt.strftime("%Y-%m-%d")
    return out


def _selected_day_keys(
    periods: pd.DataFrame,
    *,
    start_day: str | None = None,
    end_day: str | None = None,
    max_days: int | None = None,
) -> list[str]:
    if periods.empty or "day" not in periods.columns:
        return []

    periods = _with_day_keys(periods)
    if start_day:
        periods = periods[periods["_day_dt"] >= pd.to_datetime(start_day)]
    if end_day:
        periods = periods[periods["_day_dt"] <= pd.to_datetime(end_day)]

    days = sorted(periods["_day_key"].unique())
    if max_days and len(days) > max_days:
        days = days[-max_days:]
    return days


def sleep_ring_stats(
    segments: pd.DataFrame,
    periods: pd.DataFrame,
    *,
    resolution: str = "5_min",
    start_day: str | None = None,
    end_day: str | None = None,
    max_days: int | None = None,
) -> dict[str, int]:
    day_keys = _selected_day_keys(
        periods,
        start_day=start_day,
        end_day=end_day,
        max_days=max_days,
    )
    if segments.empty or "day" not in segments.columns or not day_keys:
        return {"days": len(day_keys), "segments_5_min": 0, "segments_30_sec": 0, "plotted_segments": 0}

    sleep = _with_day_keys(segments)
    sleep = sleep[(sleep["is_sleep"].astype(int) == 1) & (sleep["_day_key"].isin(day_keys))]
    return {
        "days": len(day_keys),
        "segments_5_min": int((sleep["source_resolution"] == "5_min").sum()),
        "segments_30_sec": int((sleep["source_resolution"] == "30_sec").sum()),
        "plotted_segments": int((sleep["source_resolution"] == resolution).sum()),
    }


def palette_for(name: str, overrides: dict[str, str] | None = None) -> dict[str, str]:
    palette = PALETTE_PRESETS.get(name, PALETTE_PRESETS["Current"]).copy()
    if overrides:
        palette.update({key: value for key, value in overrides.items() if value})
    return palette


def _parse_datetime(value: object) -> datetime | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime()


def _minute_of_day(value: datetime) -> float:
    return value.hour * 60 + value.minute + value.second / 60


def _draw_date_guides(
    ax,
    days: list[str],
    *,
    inner_radius: float,
    ring_step: float,
    ring_height: float,
    palette: dict[str, str],
    date_guides: str,
) -> None:
    if date_guides == DATE_GUIDE_NONE:
        return

    dates = pd.to_datetime(days)
    guide = pd.DataFrame({"day": days, "date": dates, "index": range(len(days))})
    theta = [i / 240 * 2 * math.pi for i in range(241)]

    if date_guides == DATE_GUIDE_SEASONS:
        guide["season"] = guide["date"].dt.month.map(SEASON_BY_MONTH)
        season_start = 0
        current = guide.iloc[0]["season"]
        for row_index, row in guide.iloc[1:].iterrows():
            if row["season"] == current:
                continue
            _draw_season_band(ax, season_start, row_index - 1, current, inner_radius, ring_step, ring_height, palette)
            season_start = row_index
            current = row["season"]
        _draw_season_band(ax, season_start, len(guide) - 1, current, inner_radius, ring_step, ring_height, palette)

    month_starts = guide[guide["date"].dt.day == 1]
    if month_starts.empty:
        month_starts = guide.groupby([guide["date"].dt.year, guide["date"].dt.month], as_index=False).first()

    for _, row in month_starts.iterrows():
        radius = inner_radius + int(row["index"]) * ring_step
        ax.plot(theta, [radius] * len(theta), color=palette["month_guide"], linewidth=0.3, alpha=0.16, zorder=4)
        date = row["date"]
        if date.month == 1:
            ax.text(
                1.43 * math.pi,
                radius,
                str(date.year),
                color=TEXT,
                fontsize=6,
                alpha=0.55,
                ha="center",
                va="center",
                zorder=5,
            )


def _draw_season_band(
    ax,
    start_index: int,
    end_index: int,
    season: str,
    inner_radius: float,
    ring_step: float,
    ring_height: float,
    palette: dict[str, str],
) -> None:
    bottom = inner_radius + start_index * ring_step
    height = (end_index - start_index + 1) * ring_step + ring_height * 0.1
    ax.bar(
        [0],
        [height],
        width=[2 * math.pi],
        bottom=[bottom],
        color=palette.get(season, palette["month_guide"]),
        alpha=0.045,
        edgecolor="none",
        align="center",
        zorder=2,
    )


def _draw_activity_events(
    ax,
    events: pd.DataFrame,
    *,
    day_to_index: dict[str, int],
    inner_radius: float,
    ring_step: float,
    ring_height: float,
    palette: dict[str, str],
) -> None:
    if events is None or events.empty:
        return

    events = events.copy()
    events["day"] = pd.to_datetime(events["day"], errors="coerce").dt.strftime("%Y-%m-%d")
    events = events[events["day"].isin(day_to_index)]
    if events.empty:
        return

    for _, event in events.iterrows():
        start = _parse_datetime(event.get("start_datetime"))
        end = _parse_datetime(event.get("end_datetime"))
        if start is None:
            continue
        if end is None or end <= start:
            end = start + timedelta(minutes=12)

        start_minute = _minute_of_day(start)
        end_minute = _minute_of_day(end)
        if end_minute <= start_minute:
            end_minute = min(start_minute + 12, 1440)
        width = max((end_minute - start_minute) / 1440 * 2 * math.pi, 0.004)
        center = ((start_minute + end_minute) / 2) / 1440 * 2 * math.pi
        index = day_to_index[str(event["day"])]
        event_height = ring_height * 0.34
        bottom = inner_radius + index * ring_step + ring_height - event_height
        color_key = str(event.get("color_key") or event.get("kind") or "tag")
        ax.bar(
            [center],
            [event_height],
            width=[width],
            bottom=[bottom],
            color=palette.get(color_key, palette["tag"]),
            edgecolor="none",
            align="center",
            alpha=0.98,
            zorder=6,
        )


def make_sleep_tree_rings(
    segments: pd.DataFrame,
    periods: pd.DataFrame,
    *,
    resolution: str = "5_min",
    start_day: str | None = None,
    end_day: str | None = None,
    max_days: int | None = None,
    figsize: tuple[float, float] = (10, 10),
    palette: dict[str, str] | None = None,
    sleep_color_mode: str = "Binary",
    date_guides: str = DATE_GUIDE_NONE,
    events: pd.DataFrame | None = None,
) -> plt.Figure | None:
    days = _selected_day_keys(
        periods,
        start_day=start_day,
        end_day=end_day,
        max_days=max_days,
    )
    if not days:
        return None

    palette = palette_for("Current", palette)
    day_to_index = {day: index for index, day in enumerate(days)}
    ring_count = len(days)
    inner_radius = 0.12
    outer_radius = 1.0
    ring_step = (outer_radius - inner_radius) / ring_count
    ring_height = ring_step * 0.84
    bottoms = [inner_radius + index * ring_step for index in range(ring_count)]

    fig = plt.figure(figsize=figsize, facecolor=BACKGROUND)
    ax = fig.add_subplot(111, projection="polar", facecolor=BACKGROUND)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)

    ax.bar(
        [0.0] * ring_count,
        [ring_height] * ring_count,
        width=[2 * math.pi] * ring_count,
        bottom=bottoms,
        color=AWAKE_ORANGE,
        edgecolor="none",
        align="center",
        zorder=1,
    )

    _draw_date_guides(
        ax,
        days,
        inner_radius=inner_radius,
        ring_step=ring_step,
        ring_height=ring_height,
        palette=palette,
        date_guides=date_guides,
    )

    if not segments.empty:
        sleep = _with_day_keys(segments)
        sleep = sleep[
            (sleep["source_resolution"] == resolution)
            & (sleep["is_sleep"].astype(int) == 1)
            & (sleep["_day_key"].isin(day_to_index))
        ]
        if not sleep.empty:
            widths = (sleep["end_minute"].astype(float) - sleep["start_minute"].astype(float)) / 1440 * 2 * math.pi
            centers = ((sleep["start_minute"].astype(float) + sleep["end_minute"].astype(float)) / 2) / 1440 * 2 * math.pi
            sleep_bottoms = [
                inner_radius + day_to_index[day_key] * ring_step
                for day_key in sleep["_day_key"]
            ]
            if sleep_color_mode == "Sleep stages":
                sleep_colors = [
                    palette[SLEEP_PHASE_COLOR_KEYS.get(str(label), "sleep")]
                    for label in sleep["phase_label"]
                ]
            else:
                sleep_colors = palette["sleep"]
            ax.bar(
                centers.to_numpy(),
                [ring_height] * len(sleep),
                width=widths.to_numpy(),
                bottom=sleep_bottoms,
                color=sleep_colors,
                edgecolor="none",
                align="center",
                alpha=0.94,
                zorder=3,
            )

    _draw_activity_events(
        ax,
        events,
        day_to_index=day_to_index,
        inner_radius=inner_radius,
        ring_step=ring_step,
        ring_height=ring_height,
        palette=palette,
    )

    hours = list(range(0, 24, 3))
    ax.set_xticks([hour / 24 * 2 * math.pi for hour in hours])
    ax.set_xticklabels([f"{hour:02d}" for hour in hours], color=TEXT, fontsize=8)
    ax.set_yticklabels([])
    ax.set_ylim(0, outer_radius + ring_step * 1.25)
    ax.grid(False)
    ax.spines["polar"].set_visible(False)

    ax.add_artist(plt.Circle((0, 0), inner_radius * 0.68, transform=ax.transData._b, color=BACKGROUND, zorder=10))
    fig.tight_layout(pad=0)
    return fig
