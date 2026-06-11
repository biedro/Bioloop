from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd


RAW_VALUE_LABELS = {
    "average_hrv",
    "average_heart_rate",
    "lowest_heart_rate",
    "readiness",
    "readiness_score",
    "daily_readiness",
    "score",
}

BANNED_NARRATIVE_PHRASES = {
    "you should",
    "this caused",
    "diagnosed",
    "diagnosis",
    "treatment",
    "failed",
    "ai detected",
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


@dataclass(frozen=True)
class DateRange:
    start: str | None
    end: str | None


def default_export_settings(
    *,
    file_format: str = "png",
    crop: str = "full",
    include_raw_values: bool = False,
) -> dict[str, Any]:
    return {
        "format": file_format,
        "crop": crop,
        "include_raw_values": include_raw_values,
    }


def export_is_privacy_safe(settings: dict[str, Any]) -> bool:
    return settings.get("include_raw_values") is not True


def redact_export_metadata(metadata: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    if settings.get("include_raw_values") is True:
        return metadata.copy()
    return {
        key: value
        for key, value in metadata.items()
        if key not in RAW_VALUE_LABELS
    }


def life_rings_date_range(periods: pd.DataFrame) -> DateRange:
    if periods.empty or "day" not in periods.columns:
        return DateRange(None, None)
    days = _to_datetime(periods["day"]).dropna()
    if days.empty:
        return DateRange(None, None)
    return DateRange(days.min().date().isoformat(), days.max().date().isoformat())


def generate_life_rings_story(
    periods: pd.DataFrame,
    segments: pd.DataFrame,
    *,
    moments: pd.DataFrame | None = None,
) -> dict[str, Any]:
    date_range = life_rings_date_range(periods)
    days = _period_days(periods)
    nights = len(days)
    missing_days = _missing_days(days)
    stable_month = _most_stable_month(periods)
    longest_season = _longest_sleep_season(periods)
    moment_titles = _moment_titles_in_range(moments, date_range)

    if nights:
        caption = f"Here are {nights:,} nights of your life."
    else:
        caption = "Your Life Rings are waiting for their first nights."

    evidence = []
    if date_range.start and date_range.end:
        evidence.append(f"Date range: {date_range.start} to {date_range.end}")
    evidence.append(f"Nights included: {nights:,}")
    evidence.append(f"Missing days visible in range: {missing_days:,}")
    if stable_month:
        evidence.append(f"Most regular sleep midpoint appears in {stable_month}")
    if longest_season:
        evidence.append(f"Longest average sleep season appears to be {longest_season}")
    if moment_titles:
        evidence.append(f"Moments in this range: {', '.join(moment_titles[:3])}")

    story = {
        "caption": caption,
        "editable_caption": caption,
        "hidden": False,
        "date_range": {"start": date_range.start, "end": date_range.end},
        "evidence": evidence,
        "privacy_note": "Raw health values are hidden from shared exports by default.",
    }
    validate_narrative_text(caption)
    for item in evidence:
        validate_narrative_text(item)
    return story


def validate_narrative_text(text: str) -> None:
    lowered = text.lower()
    banned = [phrase for phrase in BANNED_NARRATIVE_PHRASES if phrase in lowered]
    if banned:
        raise ValueError(f"Narrative contains banned phrase: {banned[0]}")


def _period_days(periods: pd.DataFrame) -> pd.Series:
    if periods.empty or "day" not in periods.columns:
        return pd.Series(dtype="datetime64[ns]")
    return _to_datetime(periods["day"]).dropna().drop_duplicates().sort_values()


def _missing_days(days: pd.Series) -> int:
    if days.empty:
        return 0
    expected = (days.max().date() - days.min().date()).days + 1
    return max(expected - len(days), 0)


def _most_stable_month(periods: pd.DataFrame) -> str | None:
    if periods.empty or "bedtime_start" not in periods.columns or "day" not in periods.columns:
        return None
    frame = periods[["day", "bedtime_start"]].copy()
    frame["day"] = _to_datetime(frame["day"])
    frame["bedtime_start"] = _to_datetime(frame["bedtime_start"])
    frame = frame.dropna()
    if frame.empty:
        return None
    frame["month"] = frame["day"].dt.tz_localize(None).dt.to_period("M")
    frame["minute"] = frame["bedtime_start"].dt.hour * 60 + frame["bedtime_start"].dt.minute
    grouped = frame.groupby("month").agg(count=("minute", "size"), spread=("minute", "std")).reset_index()
    grouped = grouped[grouped["count"] >= 3].dropna(subset=["spread"])
    if grouped.empty:
        return None
    best = grouped.sort_values(["spread", "count"], ascending=[True, False]).iloc[0]
    return str(best["month"])


def _longest_sleep_season(periods: pd.DataFrame) -> str | None:
    if periods.empty or "day" not in periods.columns or "total_sleep_duration" not in periods.columns:
        return None
    frame = periods[["day", "total_sleep_duration"]].copy()
    frame["day"] = _to_datetime(frame["day"])
    frame["total_sleep_duration"] = pd.to_numeric(frame["total_sleep_duration"], errors="coerce")
    frame = frame.dropna()
    if frame.empty:
        return None
    frame["season"] = frame["day"].dt.month.map(SEASON_BY_MONTH)
    grouped = frame.groupby("season")["total_sleep_duration"].mean().dropna()
    if grouped.empty:
        return None
    return str(grouped.sort_values(ascending=False).index[0])


def _moment_titles_in_range(moments: pd.DataFrame | None, date_range: DateRange) -> list[str]:
    if moments is None or moments.empty or not date_range.start or not date_range.end:
        return []
    frame = moments.copy()
    if "start_day" not in frame.columns or "title" not in frame.columns:
        return []
    frame["start_day"] = _to_datetime(frame["start_day"])
    start = pd.to_datetime(date_range.start, utc=True)
    end = pd.to_datetime(date_range.end, utc=True)
    frame = frame[(frame["start_day"] >= start) & (frame["start_day"] <= end)]
    return [str(title) for title in frame["title"].dropna().tolist()]


def _to_datetime(values: Any) -> pd.Series:
    return pd.to_datetime(values, errors="coerce", utc=True, format="mixed")
