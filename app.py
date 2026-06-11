from __future__ import annotations

import json
import math
from dataclasses import replace
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
import secrets
import shutil
import tempfile

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from oura_data.charts import (
    DATE_GUIDE_MONTHS,
    DATE_GUIDE_NONE,
    DATE_GUIDE_SEASONS,
    PALETTE_PRESETS,
    make_sleep_tree_rings,
    palette_for,
    sleep_ring_stats,
)
from oura_data.artifacts import (
    default_export_settings,
    export_is_privacy_safe,
    generate_life_rings_story,
    redact_export_metadata,
)
from oura_data.client import ENDPOINTS, OuraClient
from oura_data.config import load_settings
from oura_data.oauth import (
    OAuthStateStore,
    TokenStore,
    build_authorization_url,
    exchange_code_for_tokens,
    new_state,
    validate_state,
)
from oura_data.storage import OuraStore
from oura_data.sync import sync_all


DIMITRY_PROFILE_URL = "https://www.linkedin.com/in/sergeyevdmitry/"
DIMITRY_POST_URL = "https://www.linkedin.com/feed/update/urn:li:activity:7467961204125208576/"


st.set_page_config(page_title="Bioloop", layout="wide")


@st.cache_resource
def get_store(db_path: str) -> OuraStore:
    return OuraStore(pd.io.common.stringify_path(db_path))


def query_param(name: str) -> str | None:
    value = st.query_params.get(name)
    if isinstance(value, list):
        return value[0] if value else None
    return value


def apply_streamlit_secrets_to_env() -> None:
    import os

    for key in [
        "APP_CONTACT_EMAIL",
        "APP_NAME",
        "OURA_CLIENT_ID",
        "OURA_CLIENT_SECRET",
        "OURA_DATA_DIR",
        "OURA_PUBLIC_BASE_URL",
        "OURA_REDIRECT_URI",
        "OURA_SCOPES",
        "OURA_STORAGE_MODE",
    ]:
        try:
            value = st.secrets.get(key)
        except Exception:
            value = None
        if value and not os.getenv(key):
            os.environ[key] = str(value)


def session_scoped_settings(settings):
    if settings.storage_mode != "session":
        return settings

    if "session_data_id" not in st.session_state:
        st.session_state.session_data_id = secrets.token_urlsafe(18)
    data_dir = Path(tempfile.gettempdir()) / "oura-data-rings" / st.session_state.session_data_id
    return replace(
        settings,
        data_dir=data_dir,
        db_path=data_dir / "oura.sqlite3",
        token_path=data_dir / "tokens.json",
        oauth_state_path=data_dir / "oauth_state.json",
    )


def privacy_url(settings) -> str:
    return f"{settings.public_base_url.rstrip('/')}/?view=privacy"


def terms_url(settings) -> str:
    return f"{settings.public_base_url.rstrip('/')}/?view=terms"


def render_static_header(settings, title: str) -> None:
    st.title(title)
    st.caption(f"{settings.app_name} is an independent, open-source wearable data-art studio.")
    st.link_button("Open app", settings.public_base_url or "http://localhost:8501")


def render_about(settings) -> None:
    render_static_header(settings, settings.app_name)
    st.markdown(
        f"""
        ## What this app does

        {settings.app_name} connects to the Oura API through OAuth, lets each user sync their own Oura data,
        and turns wearable history into private artifacts, reflective stories, and exportable Life Rings.

        The sleep rings visualization is inspired by Dmitry Sergeev's original 24-hour Oura sleep rings chart.
        Attribution: [Dmitry Sergeev]({DIMITRY_PROFILE_URL}) and
        [original LinkedIn post]({DIMITRY_POST_URL}).

        ## Oura review links

        - Website URL: `{settings.public_base_url}`
        - Privacy Policy URL: `{privacy_url(settings)}`
        - Terms of Service URL: `{terms_url(settings)}`

        ## Data handling

        In local mode, data is stored on the user's own machine under `data/`.
        In public Streamlit session mode, OAuth tokens and synced Oura data are kept in a temporary,
        per-session server-side workspace and are cleared when the user disconnects or the session ends.

        This project is not affiliated with, endorsed by, or sponsored by Oura.
        """
    )


def render_privacy_policy(settings) -> None:
    render_static_header(settings, "Privacy Policy")
    contact = settings.contact_email or "the app maintainer"
    st.markdown(
        f"""
        Last updated: June 8, 2026

        ## Overview

        {settings.app_name} is an independent, open-source data-art studio for users who choose to connect their
        Oura account. The app uses OAuth to request consent before accessing Oura data.

        ## Data accessed

        Depending on the scopes selected in the Oura authorization screen, the app may access Oura profile,
        sleep, readiness, activity, heart-rate, workout, tag, session, SpO2, stress, ring configuration,
        and heart health data.

        ## How data is used

        Data is used only to sync, normalize, visualize, analyze, and export the connected user's own Oura data.
        The app does not sell Oura data and does not use it for advertising.

        ## Storage

        - Local/self-hosted mode: OAuth tokens and synced data are stored on the user's machine in the configured
          `OURA_DATA_DIR`.
        - Public Streamlit session mode: tokens and synced data are stored in a temporary per-session workspace
          on the app server so different users do not share one token or one SQLite archive.

        Users can disconnect from Oura in the sidebar. In session mode, disconnecting deletes the temporary
        session token and local session database.

        ## Sharing

        The app sends requests to Oura's API to retrieve data after user consent. It does not intentionally
        share Oura data with other third parties. Hosting providers may process operational logs and runtime
        infrastructure data according to their own policies.

        ## Security

        Client secrets are expected to be stored as environment variables or Streamlit secrets, never committed
        to source control. OAuth tokens and SQLite databases are excluded from git.

        ## Contact

        Questions or deletion requests can be sent to: {contact}

        This app is not affiliated with, endorsed by, or sponsored by Oura.
        """
    )


def render_terms(settings) -> None:
    render_static_header(settings, "Terms of Service")
    contact = settings.contact_email or "the app maintainer"
    st.markdown(
        f"""
        Last updated: June 8, 2026

        ## Acceptance

        By using {settings.app_name}, you agree to use it only with Oura accounts and data you are authorized
        to access. If you do not agree, do not use the app.

        ## No medical advice

        This app is for personal data exploration and visualization. It does not provide medical advice,
        diagnosis, treatment, or emergency guidance.

        ## User responsibility

        You are responsible for reviewing the scopes requested in the Oura OAuth consent screen and for
        complying with Oura's terms and API policies.

        ## Open-source software

        The app is provided as-is, without warranties. You may self-host it under the project's open-source
        license. Self-hosted operators are responsible for their own privacy, security, compliance, and user
        support obligations.

        ## Attribution

        The sleep rings visualization is inspired by Dmitry Sergeev's original Oura visualization:
        [profile]({DIMITRY_PROFILE_URL}) and [post]({DIMITRY_POST_URL}).

        ## Contact

        Questions can be sent to: {contact}

        This app is independent and is not affiliated with, endorsed by, or sponsored by Oura.
        """
    )


def load_table(store: OuraStore, table: str) -> pd.DataFrame:
    try:
        return store.dataframe(table)
    except Exception:
        return pd.DataFrame()


def parse_json_cell(value: object, default: dict | None = None) -> dict:
    if default is None:
        default = {}
    if value is None or pd.isna(value):
        return default
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return default
    return parsed if isinstance(parsed, dict) else default


def artifact_date_label(date_range_json: dict) -> str:
    start = date_range_json.get("start") or "unknown"
    end = date_range_json.get("end") or "unknown"
    return f"{start} to {end}"


def artifact_caption(narrative: dict) -> str:
    if narrative.get("hidden"):
        return "Narrative hidden for this artifact."
    return str(narrative.get("editable_caption") or narrative.get("caption") or "A private Life Rings artifact.")


def filtered_by_day(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    if df.empty or "day" not in df.columns:
        return df
    out = df.copy()
    out["day"] = pd.to_datetime(out["day"], errors="coerce")
    return out[(out["day"].dt.date >= start) & (out["day"].dt.date <= end)]


def build_activity_events(
    workouts: pd.DataFrame,
    tags: pd.DataFrame,
    selected_overlays: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if "Workouts" in selected_overlays and not workouts.empty:
        for _, row in workouts.iterrows():
            rows.append(
                {
                    "kind": "workout",
                    "color_key": "workout",
                    "day": row.get("day"),
                    "start_datetime": row.get("start_datetime"),
                    "end_datetime": row.get("end_datetime"),
                    "label": row.get("activity"),
                }
            )
    if "Tags" in selected_overlays and not tags.empty:
        for _, row in tags.iterrows():
            rows.append(
                {
                    "kind": "tag",
                    "color_key": "tag",
                    "day": row.get("day"),
                    "start_datetime": row.get("start_datetime"),
                    "end_datetime": row.get("end_datetime"),
                    "label": row.get("text"),
                }
            )
    return pd.DataFrame(rows)


def csv_download(label: str, df: pd.DataFrame, filename: str) -> None:
    st.download_button(
        label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        disabled=df.empty,
    )


def figure_bytes(fig, file_format: str, *, facecolor: str | None = None, bbox_inches: str = "tight") -> bytes:
    buffer = BytesIO()
    fig.savefig(
        buffer,
        format=file_format,
        dpi=240,
        facecolor=facecolor or fig.get_facecolor(),
        bbox_inches=bbox_inches,
    )
    return buffer.getvalue()


def make_demo_life_rings_data(days: int = 240) -> tuple[pd.DataFrame, pd.DataFrame]:
    start = date(2025, 1, 1)
    periods: list[dict[str, object]] = []
    segments: list[dict[str, object]] = []
    for index in range(days):
        day = start + timedelta(days=index)
        if index % 37 == 0:
            continue
        seasonal_shift = int(22 * math.sin(index / 365 * 2 * math.pi))
        bedtime_hour = 22 + ((index // 29) % 2)
        bedtime_minute = (35 + index * 7 + seasonal_shift) % 60
        sleep_minutes = 430 + ((index * 11) % 70)
        periods.append(
            {
                "id": f"demo-{day.isoformat()}",
                "day": day.isoformat(),
                "bedtime_start": f"{day.isoformat()}T{bedtime_hour:02d}:{bedtime_minute:02d}:00+02:00",
                "total_sleep_duration": sleep_minutes * 60,
            }
        )
        segments.append(
            {
                "document_id": f"demo-{day.isoformat()}",
                "day": day.isoformat(),
                "sequence": index * 2,
                "source_resolution": "5_min",
                "phase_label": "light",
                "is_sleep": 1,
                "start_minute": bedtime_hour * 60 + bedtime_minute,
                "end_minute": 1440,
            }
        )
        segments.append(
            {
                "document_id": f"demo-{day.isoformat()}",
                "day": day.isoformat(),
                "sequence": index * 2 + 1,
                "source_resolution": "5_min",
                "phase_label": "deep" if index % 3 else "rem",
                "is_sleep": 1,
                "start_minute": 0,
                "end_minute": max(sleep_minutes - (1440 - (bedtime_hour * 60 + bedtime_minute)), 90),
            }
        )
    return pd.DataFrame(periods), pd.DataFrame(segments)


def build_moment_events(moments: pd.DataFrame) -> pd.DataFrame:
    if moments.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for _, row in moments.iterrows():
        start_day = row.get("start_day")
        if not start_day:
            continue
        rows.append(
            {
                "kind": "moment",
                "color_key": "tag",
                "day": start_day,
                "start_datetime": f"{start_day}T12:00:00+00:00",
                "end_datetime": f"{start_day}T12:30:00+00:00",
                "label": row.get("title"),
            }
        )
    return pd.DataFrame(rows)


def moment_count_for_range(store: OuraStore, start_day: date, end_day: date) -> int:
    return len(store.list_moments_between(start_day.isoformat(), end_day.isoformat()))


def sleep_tables(store: OuraStore) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return (
        load_table(store, "sleep_periods"),
        load_table(store, "sleep_segments"),
        load_table(store, "workouts"),
        load_table(store, "tags"),
        load_table(store, "moments"),
    )


def data_range(periods: pd.DataFrame) -> tuple[date | None, date | None]:
    if periods.empty or "day" not in periods.columns:
        return None, None
    days = pd.to_datetime(periods["day"], errors="coerce").dropna()
    if days.empty:
        return None, None
    return days.min().date(), days.max().date()


def render_story_caption(story: dict, *, key_prefix: str) -> dict:
    if story.get("hidden"):
        st.caption("Narrative hidden for this artifact.")
        return story

    st.markdown(f"### {story.get('editable_caption') or story.get('caption')}")
    st.caption(story.get("privacy_note", "Raw health values are hidden from shared exports by default."))
    edited_caption = st.text_input(
        "Caption",
        value=str(story.get("editable_caption") or story.get("caption") or ""),
        key=f"{key_prefix}_caption",
    )
    hide = st.checkbox("Hide narrative on exports", value=bool(story.get("hidden")), key=f"{key_prefix}_hide")
    return {**story, "editable_caption": edited_caption, "hidden": hide}


def render_evidence_drawer(story: dict, stats: dict[str, int] | None = None) -> None:
    with st.expander("Why we said this"):
        for item in story.get("evidence", []):
            st.write(f"- {item}")
        if stats:
            st.write(f"- Days in artifact: {stats.get('days', 0):,}")
            st.write(f"- Plotted sleep segments: {stats.get('plotted_segments', 0):,}")
        st.caption("These statements describe visible patterns. They are not medical advice.")


def render_artifact_card(store: OuraStore, artifact: pd.Series, *, key_prefix: str) -> None:
    date_range_json = parse_json_cell(artifact["date_range"])
    narrative = parse_json_cell(artifact["narrative_json"])
    st.markdown(f"#### {artifact['title']}")
    st.caption(f"{artifact_date_label(date_range_json)} · {artifact['privacy_level']}")
    st.write(artifact_caption(narrative))
    col1, col2 = st.columns([1, 1])
    if col1.button("Open", key=f"{key_prefix}_open"):
        st.session_state.selected_artifact_id = artifact["id"]
        st.rerun()
    if col2.button("Delete", key=f"{key_prefix}_delete"):
        store.delete_artifact(str(artifact["id"]))
        if st.session_state.get("selected_artifact_id") == artifact["id"]:
            st.session_state.pop("selected_artifact_id", None)
        st.rerun()


def render_export_panel(
    store: OuraStore,
    fig,
    *,
    filename_root: str,
    artifact_id: str | None = None,
    key_prefix: str,
) -> None:
    st.subheader("Save, Share, Print")
    col1, col2, col3 = st.columns(3)
    include_raw_values = col1.checkbox(
        "Include raw values",
        value=False,
        key=f"{key_prefix}_include_raw",
        help="Off by default for privacy-safe shared outputs.",
    )
    crop = col2.selectbox("Crop", ["full", "square", "print"], key=f"{key_prefix}_crop")
    export_format = col3.selectbox("Format", ["png", "svg", "pdf"], key=f"{key_prefix}_format")
    export_settings = default_export_settings(
        file_format=export_format,
        crop=crop,
        include_raw_values=include_raw_values,
    )
    if export_is_privacy_safe(export_settings):
        st.caption("Privacy-safe export: raw health values are hidden.")
    else:
        st.warning("This export can include raw health values. Share carefully.")

    metadata = redact_export_metadata(
        {
            "template": "Life Rings",
            "average_hrv": "hidden unless opted in",
            "readiness_score": "hidden unless opted in",
            "privacy": "private by default",
        },
        export_settings,
    )
    with st.expander("Export metadata"):
        st.json(metadata)

    mime = {
        "png": "image/png",
        "svg": "image/svg+xml",
        "pdf": "application/pdf",
    }[export_format]
    st.download_button(
        f"Download {export_format.upper()}",
        figure_bytes(fig, export_format),
        f"{filename_root}.{export_format}",
        mime,
        key=f"{key_prefix}_download",
    )

    print_note = st.text_input("Print note", placeholder="Optional note for the beta print request", key=f"{key_prefix}_print_note")
    if st.button("Request print", key=f"{key_prefix}_print"):
        store.record_feedback(kind="print_intent", value="requested", note=print_note, artifact_id=artifact_id)
        st.success("Print interest saved for this beta artifact.")

    rating = st.slider("This feels like me", 1, 5, 4, key=f"{key_prefix}_rating")
    if st.button("Save feedback", key=f"{key_prefix}_feedback"):
        store.record_feedback(kind="resonance_rating", value=rating, artifact_id=artifact_id)
        st.success("Feedback saved locally.")


def auth_url_for(settings, state_store: OAuthStateStore) -> str:
    state = new_state()
    state_store.save_state(state)
    return build_authorization_url(
        client_id=settings.client_id,
        redirect_uri=settings.redirect_uri,
        scopes=settings.scopes,
        state=state,
    )


def render_auth(settings, token_store: TokenStore, state_store: OAuthStateStore) -> bool:
    st.sidebar.header("Oura")
    if not settings.is_configured:
        st.sidebar.warning("Add OURA_CLIENT_ID and OURA_CLIENT_SECRET to .env, then restart Streamlit.")
        return False

    code = query_param("code")
    returned_state = query_param("state")
    if code:
        try:
            validate_state(state_store.read_state(), returned_state)
            tokens = exchange_code_for_tokens(code=code, settings=settings)
            token_store.write(tokens)
            state_store.clear()
            st.query_params.clear()
            st.sidebar.success("Connected to Oura.")
        except Exception as exc:
            st.sidebar.error(str(exc))

    tokens = token_store.read()
    connected = bool(tokens and tokens.get("access_token"))
    if connected:
        st.sidebar.success("Oura connected")
        if st.sidebar.button("Disconnect"):
            token_store.clear()
            if settings.storage_mode == "session" and settings.data_dir.exists():
                shutil.rmtree(settings.data_dir, ignore_errors=True)
                st.session_state.pop("session_data_id", None)
            st.rerun()
    else:
        auth_url = auth_url_for(settings, state_store)
        st.session_state.auth_url = auth_url
        st.sidebar.link_button("Connect Oura", auth_url, width="stretch")
    return connected


def render_sync(store: OuraStore, client: OuraClient) -> None:
    st.header("Sync")
    default_start = date.today().replace(month=1, day=1) - timedelta(days=365 * 7)
    col1, col2 = st.columns(2)
    start_day = col1.date_input("Start date", value=default_start)
    end_day = col2.date_input("End date", value=date.today())
    selected = st.multiselect("Endpoints", ENDPOINTS, default=ENDPOINTS)

    if st.button("Sync selected endpoints", width="stretch"):
        start_iso = f"{start_day.isoformat()}T00:00:00+00:00"
        end_iso = f"{end_day.isoformat()}T23:59:59+00:00"
        progress_box = st.empty()

        def progress(endpoint: str, status: str) -> None:
            progress_box.info(f"{endpoint}: {status}")

        with st.spinner("Syncing Oura data..."):
            results = sync_all(
                client=client,
                store=store,
                start=start_iso,
                end=end_iso,
                endpoints=selected,
                progress=progress,
            )
        progress_box.empty()
        ok = sum(1 for result in results if result.status == "ok")
        skipped = sum(1 for result in results if result.status == "skipped")
        errors = [result for result in results if result.status == "error"]
        st.success(f"Sync complete: {ok} ok, {skipped} skipped, {len(errors)} errors.")
        if errors:
            st.dataframe(pd.DataFrame([result.__dict__ for result in errors]), width="stretch")


def render_status(store: OuraStore) -> None:
    status = load_table(store, "sync_status")
    raw = load_table(store, "raw_documents")
    if not status.empty:
        st.dataframe(status.sort_values("endpoint"), width="stretch", hide_index=True)
    if not raw.empty:
        counts = raw.groupby("endpoint").size().reset_index(name="documents").sort_values("endpoint")
        st.subheader("Archived Documents")
        st.dataframe(counts, width="stretch", hide_index=True)


def render_sleep_rings(store: OuraStore) -> None:
    periods = load_table(store, "sleep_periods")
    segments = load_table(store, "sleep_segments")
    workouts = load_table(store, "workouts")
    tags = load_table(store, "tags")
    if periods.empty or segments.empty:
        st.info("Sync the sleep endpoint to render the sleep rings.")
        st.caption(
            f"Sleep rings are inspired by [Dmitry Sergeev]({DIMITRY_PROFILE_URL}) "
            f"and his [original LinkedIn post]({DIMITRY_POST_URL})."
        )
        return

    st.caption(
        f"Sleep rings inspired by [Dmitry Sergeev]({DIMITRY_PROFILE_URL}) "
        f"and his [original LinkedIn post]({DIMITRY_POST_URL})."
    )

    min_day = pd.to_datetime(periods["day"]).min().date()
    max_day = pd.to_datetime(periods["day"]).max().date()
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    start_day = col1.date_input("From", value=min_day, min_value=min_day, max_value=max_day, key="rings_start")
    end_day = col2.date_input("To", value=max_day, min_value=min_day, max_value=max_day, key="rings_end")
    resolution = col3.selectbox("Resolution", ["5_min", "30_sec"])
    max_days = col4.number_input("Max rings", min_value=30, max_value=5000, value=2500, step=100)

    style_col1, style_col2, style_col3, style_col4 = st.columns([1, 1, 1, 1])
    sleep_color_mode = style_col1.selectbox("Sleep colors", ["Binary", "Sleep stages"])
    palette_name = style_col2.selectbox("Palette", list(PALETTE_PRESETS), index=0)
    date_guides = style_col3.selectbox(
        "Date guides",
        [DATE_GUIDE_NONE, DATE_GUIDE_MONTHS, DATE_GUIDE_SEASONS],
        index=0,
    )
    selected_overlays = style_col4.multiselect("Overlays", ["Workouts", "Tags"], default=[])

    palette = palette_for(palette_name)
    with st.expander("Colors"):
        color_col1, color_col2, color_col3, color_col4 = st.columns(4)
        palette["awake"] = color_col1.color_picker("Awake", palette["awake"])
        palette["sleep"] = color_col2.color_picker("Sleep", palette["sleep"])
        palette["deep"] = color_col3.color_picker("Deep", palette["deep"])
        palette["light"] = color_col4.color_picker("Light", palette["light"])
        color_col5, color_col6, color_col7, color_col8 = st.columns(4)
        palette["rem"] = color_col5.color_picker("REM", palette["rem"])
        palette["workout"] = color_col6.color_picker("Workout", palette["workout"])
        palette["tag"] = color_col7.color_picker("Tag", palette["tag"])
        palette["month_guide"] = color_col8.color_picker("Month guide", palette["month_guide"])
        if date_guides == DATE_GUIDE_SEASONS:
            season_col1, season_col2, season_col3, season_col4 = st.columns(4)
            palette["winter"] = season_col1.color_picker("Winter", palette["winter"])
            palette["spring"] = season_col2.color_picker("Spring", palette["spring"])
            palette["summer"] = season_col3.color_picker("Summer", palette["summer"])
            palette["autumn"] = season_col4.color_picker("Autumn", palette["autumn"])

    filtered_periods = filtered_by_day(periods, start_day, end_day)
    filtered_segments = filtered_by_day(segments, start_day, end_day)
    filtered_workouts = filtered_by_day(workouts, start_day, end_day)
    filtered_tags = filtered_by_day(tags, start_day, end_day)
    events = build_activity_events(filtered_workouts, filtered_tags, selected_overlays)
    stats = sleep_ring_stats(
        filtered_segments,
        filtered_periods,
        resolution=resolution,
        start_day=start_day.isoformat(),
        end_day=end_day.isoformat(),
        max_days=int(max_days),
    )
    with st.expander("Artifact evidence"):
        metric_cols = st.columns(5)
        metric_cols[0].metric("Days", f"{stats['days']:,}")
        metric_cols[1].metric("5-min sleep segments", f"{stats['segments_5_min']:,}")
        metric_cols[2].metric("30-sec sleep segments", f"{stats['segments_30_sec']:,}")
        metric_cols[3].metric("Plotted segments", f"{stats['plotted_segments']:,}")
        metric_cols[4].metric("Activity overlays", f"{len(events):,}")

    fig = make_sleep_tree_rings(
        filtered_segments,
        filtered_periods,
        resolution=resolution,
        start_day=start_day.isoformat(),
        end_day=end_day.isoformat(),
        max_days=int(max_days),
        palette=palette,
        sleep_color_mode=sleep_color_mode,
        date_guides=date_guides,
        events=events,
    )
    if fig is None:
        st.info("No sleep-stage segments are available for this range.")
        return

    st.pyplot(fig, width="stretch")
    png = BytesIO()
    fig.savefig(png, format="png", dpi=240, facecolor=fig.get_facecolor(), bbox_inches="tight")
    st.download_button("Download PNG", png.getvalue(), "oura_sleep_rings.png", "image/png")


def render_disconnected_story(settings) -> None:
    st.markdown("## YOUR LIFE")
    st.caption("A private museum of your wearable history.")
    periods, segments = make_demo_life_rings_data()
    fig = make_sleep_tree_rings(
        segments,
        periods,
        resolution="5_min",
        palette=palette_for("Current"),
        date_guides=DATE_GUIDE_SEASONS,
        figsize=(9, 9),
    )
    if fig is not None:
        st.pyplot(fig, width="stretch")
    st.markdown("### Every ring is a day. Every season leaves a trace.")
    st.write("Connect Oura to turn your own history into Life Rings, story captions, and privacy-safe exports.")
    st.caption("Your data stays yours. Shared artifacts hide raw health values by default.")
    auth_url = st.session_state.get("auth_url")
    if auth_url and settings.is_configured:
        st.link_button("Connect Oura", auth_url, width="stretch")
    elif not settings.is_configured:
        st.warning("Add Oura API settings before connecting a source.")


def render_life_rings_artifact(
    store: OuraStore,
    *,
    periods: pd.DataFrame,
    segments: pd.DataFrame,
    events: pd.DataFrame | None,
    moments: pd.DataFrame,
    start_day: date,
    end_day: date,
    palette_name: str,
    date_guides: str,
    sleep_color_mode: str,
    resolution: str,
    max_days: int,
    key_prefix: str,
    title: str = "Life Rings",
) -> None:
    filtered_periods = filtered_by_day(periods, start_day, end_day)
    filtered_segments = filtered_by_day(segments, start_day, end_day)
    stats = sleep_ring_stats(
        filtered_segments,
        filtered_periods,
        resolution=resolution,
        start_day=start_day.isoformat(),
        end_day=end_day.isoformat(),
        max_days=max_days,
    )
    story = generate_life_rings_story(filtered_periods, filtered_segments, moments=moments)

    fig = make_sleep_tree_rings(
        filtered_segments,
        filtered_periods,
        resolution=resolution,
        start_day=start_day.isoformat(),
        end_day=end_day.isoformat(),
        max_days=max_days,
        palette=palette_for(palette_name),
        sleep_color_mode=sleep_color_mode,
        date_guides=date_guides,
        events=events,
        figsize=(10, 10),
    )
    if fig is None:
        st.info("No sleep segments are available for this artifact range.")
        return

    st.markdown(f"## {title}")
    st.caption("Every ring is a day. Midnight is at the top; noon is at the bottom.")
    st.pyplot(fig, width="stretch")
    edited_story = render_story_caption(story, key_prefix=key_prefix)
    render_evidence_drawer(edited_story, stats)

    privacy_level = st.selectbox(
        "Privacy level",
        ["private", "share-safe", "print"],
        key=f"{key_prefix}_privacy",
        help="Shared exports hide raw health values unless you explicitly include them.",
    )
    artifact_title = st.text_input("Artifact title", value=title, key=f"{key_prefix}_title")
    artifact_id = None
    if st.button("Save artifact", key=f"{key_prefix}_save"):
        artifact_id = store.save_artifact(
            artifact_type="life_rings",
            title=artifact_title,
            date_range={"start": start_day.isoformat(), "end": end_day.isoformat()},
            settings={
                "template": "life_rings",
                "palette_name": palette_name,
                "date_guides": date_guides,
                "sleep_color_mode": sleep_color_mode,
                "resolution": resolution,
                "max_days": max_days,
                "export": default_export_settings(),
            },
            narrative=edited_story,
            privacy_level=privacy_level,
        )
        st.success("Artifact saved to your private gallery.")

    render_export_panel(
        store,
        fig,
        filename_root=f"bioloop_{artifact_title.lower().replace(' ', '_')}",
        artifact_id=artifact_id,
        key_prefix=f"{key_prefix}_export",
    )


def render_stories(store: OuraStore, settings, connected: bool) -> None:
    if not connected:
        render_disconnected_story(settings)
        return

    periods, segments, workouts, tags, moments = sleep_tables(store)
    if periods.empty or segments.empty:
        st.markdown("## YOUR LIFE")
        st.info("Your source is connected. Sync the sleep endpoint in Settings / Privacy to grow your first Life Rings.")
        return

    start_day, end_day = data_range(periods)
    if start_day is None or end_day is None:
        st.info("Sync sleep data to create your first artifact.")
        return

    events = pd.concat(
        [
            build_activity_events(workouts, tags, ["Workouts", "Tags"]),
            build_moment_events(moments),
        ],
        ignore_index=True,
    )
    st.caption("Stories")
    hero_start = max(start_day, end_day - timedelta(days=364))
    render_life_rings_artifact(
        store,
        periods=periods,
        segments=segments,
        events=events,
        moments=moments,
        start_day=hero_start,
        end_day=end_day,
        palette_name="Current",
        date_guides=DATE_GUIDE_SEASONS,
        sleep_color_mode="Sleep stages",
        resolution="5_min",
        max_days=365,
        key_prefix="stories_life_rings",
        title="YOUR LIFE",
    )


def render_artifacts(store: OuraStore) -> None:
    st.markdown("## Artifacts")
    st.caption("A quiet gallery of saved visual works.")
    artifacts = store.list_artifacts()
    if artifacts.empty:
        st.info("Saved artifacts will appear here after you save your first Life Rings.")
        return

    st.subheader("Private Gallery")
    recent = artifacts.head(6)
    gallery_cols = st.columns(3)
    for index, (_, row) in enumerate(recent.iterrows()):
        with gallery_cols[index % 3].container(border=True):
            render_artifact_card(store, row, key_prefix=f"artifact_card_{row['id']}")

    selected_artifact_id = st.session_state.get("selected_artifact_id")
    if selected_artifact_id:
        selected = artifacts[artifacts["id"] == selected_artifact_id]
        artifact = selected.iloc[0] if not selected.empty else artifacts.iloc[0]
    else:
        artifact = artifacts.iloc[0]

    st.divider()
    st.subheader("Open Artifact")
    date_range_json = parse_json_cell(artifact["date_range"])
    narrative = parse_json_cell(artifact["narrative_json"])
    settings_json = parse_json_cell(artifact["settings_json"])

    with st.container(border=True):
        st.subheader(str(artifact["title"]))
        st.caption(f"{date_range_json.get('start')} to {date_range_json.get('end')} · {artifact['privacy_level']}")
        st.write(artifact_caption(narrative))
        with st.expander("Artifact metadata"):
            st.json(settings_json)

    periods, segments, workouts, tags, moments = sleep_tables(store)
    if periods.empty or segments.empty:
        st.info("Sync sleep data to regenerate saved artifact previews.")
        return
    start = pd.to_datetime(date_range_json.get("start"), errors="coerce")
    end = pd.to_datetime(date_range_json.get("end"), errors="coerce")
    if pd.isna(start) or pd.isna(end):
        st.warning("This artifact has no usable date range.")
        return
    moments_in_range = moment_count_for_range(store, start.date(), end.date())
    st.caption(f"{moments_in_range} saved memories overlap this artifact.")
    events = pd.concat(
        [
            build_activity_events(workouts, tags, ["Workouts", "Tags"]),
            build_moment_events(moments),
        ],
        ignore_index=True,
    )
    render_life_rings_artifact(
        store,
        periods=periods,
        segments=segments,
        events=events,
        moments=moments,
        start_day=start.date(),
        end_day=end.date(),
        palette_name=settings_json.get("palette_name", "Current"),
        date_guides=settings_json.get("date_guides", DATE_GUIDE_SEASONS),
        sleep_color_mode=settings_json.get("sleep_color_mode", "Sleep stages"),
        resolution=settings_json.get("resolution", "5_min"),
        max_days=int(settings_json.get("max_days", 2500)),
        key_prefix=f"artifact_{artifact['id']}",
        title=str(artifact["title"]),
    )


def render_moment_form(store: OuraStore, *, default_day: date, key_prefix: str) -> None:
    with st.form(f"{key_prefix}_moment_form"):
        st.subheader("Add a memory")
        col1, col2 = st.columns(2)
        start_day = col1.date_input("Start day", value=default_day, key=f"{key_prefix}_moment_start")
        end_day = col2.date_input("End day", value=default_day, key=f"{key_prefix}_moment_end")
        memory_type = st.selectbox(
            "Memory type",
            ["Custom", "Travel", "Training block", "Recovery period", "New routine", "Family", "Illness", "Vacation"],
            key=f"{key_prefix}_moment_type",
        )
        title_default = "" if memory_type == "Custom" else memory_type
        title = st.text_input("Title", value=title_default, placeholder="Summer of travel", key=f"{key_prefix}_moment_title")
        note = st.text_area("Note", placeholder="Optional private context", key=f"{key_prefix}_moment_note")
        submitted = st.form_submit_button("Save memory")
        if submitted and title.strip():
            store.save_moment(
                start_day=start_day.isoformat(),
                end_day=end_day.isoformat(),
                title=title.strip(),
                note=note.strip() or None,
            )
            st.success("Memory saved.")
        elif submitted:
            st.warning("Add a title before saving this memory.")


def render_moments_manager(store: OuraStore, *, default_day: date, key_prefix: str) -> None:
    render_moment_form(store, default_day=default_day, key_prefix=key_prefix)
    moments = store.list_moments()
    st.subheader("Saved Memories")
    if moments.empty:
        st.caption("No memories saved yet. Add one when a region of the artifact feels familiar.")
        return

    for index, (_, moment) in enumerate(moments.head(20).iterrows()):
        with st.container(border=True):
            st.markdown(f"#### {moment['title']}")
            end_day = moment["end_day"] if moment["end_day"] else moment["start_day"]
            st.caption(f"{moment['start_day']} to {end_day} · {moment['source']}")
            if moment["note"]:
                st.write(moment["note"])
            if st.button("Delete memory", key=f"{key_prefix}_delete_moment_{moment['id']}_{index}"):
                store.delete_moment(str(moment["id"]))
                st.rerun()


def render_timeline(store: OuraStore) -> None:
    st.markdown("## Timeline")
    st.caption("Move from years to nights, then turn a meaningful range into an artifact.")
    periods, segments, workouts, tags, moments = sleep_tables(store)
    start_day, end_day = data_range(periods)
    if start_day is None or end_day is None:
        st.info("Sync sleep data to explore the timeline.")
        return

    zoom = st.segmented_control("Zoom", ["Lifetime", "Year", "Season", "Month", "Week", "Day"], default="Lifetime")
    days = pd.to_datetime(periods["day"], errors="coerce").dropna().sort_values()
    selected_start, selected_end = start_day, end_day

    if zoom == "Year":
        years = sorted(days.dt.year.unique())
        year = st.selectbox("Year", years, index=len(years) - 1)
        selected_start, selected_end = date(int(year), 1, 1), date(int(year), 12, 31)
    elif zoom == "Season":
        year = st.selectbox("Season year", sorted(days.dt.year.unique()), index=len(sorted(days.dt.year.unique())) - 1)
        season = st.selectbox("Season", ["winter", "spring", "summer", "autumn"])
        ranges = {
            "winter": (date(int(year), 1, 1), date(int(year), 2, 28)),
            "spring": (date(int(year), 3, 1), date(int(year), 5, 31)),
            "summer": (date(int(year), 6, 1), date(int(year), 8, 31)),
            "autumn": (date(int(year), 9, 1), date(int(year), 11, 30)),
        }
        selected_start, selected_end = ranges[season]
    elif zoom == "Month":
        months = sorted(days.dt.to_period("M").astype(str).unique())
        month = st.selectbox("Month", months, index=len(months) - 1)
        selected_start = pd.Period(month).start_time.date()
        selected_end = pd.Period(month).end_time.date()
    elif zoom == "Week":
        selected_start = st.date_input("Week starting", value=max(end_day - timedelta(days=6), start_day))
        selected_end = selected_start + timedelta(days=6)
    elif zoom == "Day":
        selected_start = st.date_input("Night", value=end_day)
        selected_end = selected_start

    events = pd.concat(
        [
            build_activity_events(workouts, tags, ["Workouts", "Tags"]),
            build_moment_events(moments),
        ],
        ignore_index=True,
    )
    render_life_rings_artifact(
        store,
        periods=periods,
        segments=segments,
        events=events,
        moments=moments,
        start_day=max(selected_start, start_day),
        end_day=min(selected_end, end_day),
        palette_name="Current",
        date_guides=DATE_GUIDE_MONTHS if zoom in {"Lifetime", "Year", "Season"} else DATE_GUIDE_NONE,
        sleep_color_mode="Sleep stages",
        resolution="5_min",
        max_days=2500,
        key_prefix=f"timeline_{zoom.lower()}",
        title=f"Life Rings · {zoom}",
    )
    with st.expander("Memories for this period", expanded=False):
        overlap = store.list_moments_between(max(selected_start, start_day).isoformat(), min(selected_end, end_day).isoformat())
        if overlap.empty:
            st.caption("No saved memories overlap this range yet.")
        else:
            for _, moment in overlap.iterrows():
                st.write(f"- {moment['title']} · {moment['start_day']}")
        render_moment_form(store, default_day=max(selected_start, start_day), key_prefix="timeline")


def render_studio(store: OuraStore) -> None:
    st.markdown("## Studio")
    st.caption("Create a first draft quickly, then adjust detail only when you need it.")
    periods, segments, workouts, tags, moments = sleep_tables(store)
    start_day, end_day = data_range(periods)
    if start_day is None or end_day is None:
        st.info("Sync sleep data before opening the artifact studio.")
        return

    template = st.selectbox("Template", ["Life Rings", "Sleep Seasons (coming after Life Rings export quality is stable)"])
    if template != "Life Rings":
        st.info("Sleep Seasons is intentionally held until Life Rings export quality is stable.")
        return

    col1, col2 = st.columns(2)
    selected_start = col1.date_input("From", value=start_day, min_value=start_day, max_value=end_day, key="studio_start")
    selected_end = col2.date_input("To", value=end_day, min_value=start_day, max_value=end_day, key="studio_end")
    col3, col4, col5 = st.columns(3)
    palette_name = col3.selectbox("Palette", list(PALETTE_PRESETS), index=0, key="studio_palette")
    date_guides = col4.selectbox(
        "Date guides",
        [DATE_GUIDE_NONE, DATE_GUIDE_MONTHS, DATE_GUIDE_SEASONS],
        index=2,
        key="studio_guides",
    )
    sleep_color_mode = col5.selectbox("Sleep colors", ["Binary", "Sleep stages"], index=1, key="studio_sleep_color")
    overlays = st.multiselect("Overlays", ["Workouts", "Tags", "Moments"], default=["Moments"], key="studio_overlays")
    events = []
    if "Workouts" in overlays or "Tags" in overlays:
        events.append(build_activity_events(workouts, tags, [item for item in overlays if item in {"Workouts", "Tags"}]))
    if "Moments" in overlays:
        events.append(build_moment_events(moments))
    event_frame = pd.concat(events, ignore_index=True) if events else pd.DataFrame()

    if st.button("Generate draft", width="stretch"):
        st.session_state.studio_generated = True
    if st.session_state.get("studio_generated", False):
        render_life_rings_artifact(
            store,
            periods=periods,
            segments=segments,
            events=event_frame,
            moments=moments,
            start_day=selected_start,
            end_day=selected_end,
            palette_name=palette_name,
            date_guides=date_guides,
            sleep_color_mode=sleep_color_mode,
            resolution="5_min",
            max_days=2500,
            key_prefix="studio_life_rings",
            title="Life Rings Draft",
        )
    with st.expander("Memories", expanded=False):
        render_moments_manager(store, default_day=selected_start, key_prefix="studio")


def render_settings_privacy(
    store: OuraStore,
    settings,
    token_store: TokenStore,
    connected: bool,
) -> None:
    st.markdown("## Settings / Privacy")
    st.caption("Connection, source metadata, local archive controls, and advanced data tools.")
    if connected:
        render_sync(store, OuraClient(settings, token_store))
    else:
        st.info("Connect Oura to sync source data.")

    st.subheader("Local Privacy")
    st.write("Your data stays in the configured local/session archive unless you export it.")
    confirm_delete = st.checkbox("I understand this clears imported source data from the local archive.")
    if st.button("Delete imported data", disabled=not confirm_delete):
        store.clear_imported_data()
        st.success("Imported source data cleared. Saved artifacts and memories remain.")

    with st.expander("Memories", expanded=True):
        periods = load_table(store, "sleep_periods")
        start_day, end_day = data_range(periods)
        render_moments_manager(store, default_day=end_day or date.today(), key_prefix="settings")

    st.subheader("Advanced Data")
    status_tab, trends_tab, exports_tab, rings_tab = st.tabs(["Source Status", "Trends", "CSV Exports", "Life Rings Tools"])
    with status_tab:
        render_status(store)
    with trends_tab:
        render_trends(store)
    with exports_tab:
        render_exports(store)
    with rings_tab:
        render_sleep_rings(store)


def render_trends(store: OuraStore) -> None:
    periods = load_table(store, "sleep_periods")
    metrics = load_table(store, "daily_metrics")
    workouts = load_table(store, "workouts")
    tags = load_table(store, "tags")

    if periods.empty and metrics.empty:
        st.info("Sync sleep and daily endpoints to see trends.")
        return

    sleep_daily = pd.DataFrame()
    if not periods.empty:
        sleep_daily = periods.copy()
        sleep_daily["day"] = pd.to_datetime(sleep_daily["day"], errors="coerce")
        sleep_daily = sleep_daily.dropna(subset=["day"])
        sleep_daily = (
            sleep_daily.groupby("day", as_index=False)
            .agg(
                sleep_hours=("total_sleep_duration", lambda s: s.fillna(0).sum() / 3600),
                time_in_bed_hours=("time_in_bed", lambda s: s.fillna(0).sum() / 3600),
                average_hrv=("average_hrv", "mean"),
                average_heart_rate=("average_heart_rate", "mean"),
                lowest_heart_rate=("lowest_heart_rate", "mean"),
            )
        )

    score_daily = pd.DataFrame()
    if not metrics.empty:
        score_daily = metrics.copy()
        score_daily["day"] = pd.to_datetime(score_daily["day"], errors="coerce")
        score_daily = score_daily.pivot_table(index="day", columns="endpoint", values="score", aggfunc="last").reset_index()

    trend = score_daily
    if not sleep_daily.empty:
        trend = sleep_daily if trend.empty else pd.merge(sleep_daily, trend, on="day", how="outer")
    trend = trend.sort_values("day")

    min_day = trend["day"].min().date()
    max_day = trend["day"].max().date()
    start_day, end_day = st.date_input(
        "Trend range",
        value=(min_day, max_day),
        min_value=min_day,
        max_value=max_day,
    )
    trend = trend[(trend["day"].dt.date >= start_day) & (trend["day"].dt.date <= end_day)]

    y_options = [
        column
        for column in [
            "sleep_hours",
            "daily_sleep",
            "daily_readiness",
            "daily_activity",
            "average_hrv",
            "lowest_heart_rate",
            "average_heart_rate",
        ]
        if column in trend.columns
    ]
    selected_y = st.multiselect("Metrics", y_options, default=y_options[:4])
    if selected_y:
        fig = go.Figure()
        for column in selected_y:
            fig.add_trace(go.Scatter(x=trend["day"], y=trend[column], mode="lines", name=column))
        if not workouts.empty and "day" in workouts.columns:
            workout_counts = workouts.copy()
            workout_counts["day"] = pd.to_datetime(workout_counts["day"], errors="coerce")
            workout_counts = workout_counts.groupby("day").size().reset_index(name="workouts")
            workout_counts = workout_counts[(workout_counts["day"].dt.date >= start_day) & (workout_counts["day"].dt.date <= end_day)]
            if not workout_counts.empty:
                marker_y = [trend[selected_y[0]].max()] * len(workout_counts)
                fig.add_trace(
                    go.Scatter(
                        x=workout_counts["day"],
                        y=marker_y,
                        mode="markers",
                        name="workout days",
                        marker={"size": 7, "color": "#d04f3a"},
                    )
                )
        fig.update_layout(height=460, margin={"l": 10, "r": 10, "t": 30, "b": 10})
        st.plotly_chart(fig, width="stretch")

    if not trend.empty:
        monthly = trend.set_index("day").resample("ME").mean(numeric_only=True).reset_index()
        st.subheader("Monthly Summary")
        st.dataframe(monthly, width="stretch", hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Workouts")
        st.dataframe(workouts.tail(100), width="stretch", hide_index=True)
    with col2:
        st.subheader("Tags")
        st.dataframe(tags.tail(100), width="stretch", hide_index=True)


def render_exports(store: OuraStore) -> None:
    tables = [
        "sleep_periods",
        "sleep_segments",
        "daily_metrics",
        "heart_rate",
        "workouts",
        "tags",
        "sync_status",
        "raw_documents",
    ]
    cols = st.columns(2)
    for index, table in enumerate(tables):
        df = load_table(store, table)
        with cols[index % 2]:
            st.write(f"{table}: {len(df):,} rows")
            csv_download(f"Download {table}", df, f"{table}.csv")


def main() -> None:
    apply_streamlit_secrets_to_env()
    settings = session_scoped_settings(load_settings())

    view = query_param("view")
    if view == "privacy":
        render_privacy_policy(settings)
        return
    if view == "terms":
        render_terms(settings)
        return
    if view == "about":
        render_about(settings)
        return

    store = get_store(str(settings.db_path))
    token_store = TokenStore(settings.token_path)
    state_store = OAuthStateStore(settings.oauth_state_path)

    st.title(settings.app_name)
    st.caption(
        f"Open-source Oura archive and Life Rings data-art studio. "
        f"[About]({settings.public_base_url.rstrip('/')}/?view=about) · "
        f"[Privacy]({privacy_url(settings)}) · [Terms]({terms_url(settings)})"
    )
    connected = render_auth(settings, token_store, state_store)

    space = st.segmented_control(
        "Space",
        ["Stories", "Artifacts", "Timeline", "Studio", "Settings / Privacy"],
        default="Stories",
        label_visibility="collapsed",
        key="bioloop_space",
    )
    if space == "Stories":
        render_stories(store, settings, connected)
    elif space == "Artifacts":
        render_artifacts(store)
    elif space == "Timeline":
        render_timeline(store)
    elif space == "Studio":
        render_studio(store)
    elif space == "Settings / Privacy":
        render_settings_privacy(store, settings, token_store, connected)


if __name__ == "__main__":
    main()
