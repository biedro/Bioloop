from __future__ import annotations

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
    st.caption(f"{settings.app_name} is an independent, open-source Oura data visualization app.")
    st.link_button("Open app", settings.public_base_url or "http://localhost:8501")


def render_about(settings) -> None:
    render_static_header(settings, settings.app_name)
    st.markdown(
        f"""
        ## What this app does

        {settings.app_name} connects to the Oura API through OAuth, lets each user sync their own Oura data,
        and visualizes sleep, readiness, activity, workouts, tags, and related trends.

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

        {settings.app_name} is an independent, open-source dashboard for users who choose to connect their
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
        state = new_state()
        state_store.save_state(state)
        auth_url = build_authorization_url(
            client_id=settings.client_id,
            redirect_uri=settings.redirect_uri,
            scopes=settings.scopes,
            state=state,
        )
        st.sidebar.link_button("Connect Oura", auth_url, width="stretch")
    return connected


def render_sync(store: OuraStore, client: OuraClient) -> None:
    st.sidebar.header("Sync")
    default_start = date.today().replace(month=1, day=1) - timedelta(days=365 * 7)
    start_day = st.sidebar.date_input("Start date", value=default_start)
    end_day = st.sidebar.date_input("End date", value=date.today())
    selected = st.sidebar.multiselect("Endpoints", ENDPOINTS, default=ENDPOINTS)

    if st.sidebar.button("Sync selected endpoints", width="stretch"):
        start_iso = f"{start_day.isoformat()}T00:00:00+00:00"
        end_iso = f"{end_day.isoformat()}T23:59:59+00:00"
        progress_box = st.sidebar.empty()

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
        f"Open-source Oura archive and sleep-rings dashboard. "
        f"[About]({settings.public_base_url.rstrip('/')}/?view=about) · "
        f"[Privacy]({privacy_url(settings)}) · [Terms]({terms_url(settings)})"
    )
    connected = render_auth(settings, token_store, state_store)
    if connected:
        render_sync(store, OuraClient(settings, token_store))

    status_tab, rings_tab, trends_tab, exports_tab = st.tabs(["Status", "Sleep Rings", "Trends", "Exports"])
    with status_tab:
        render_status(store)
    with rings_tab:
        render_sleep_rings(store)
    with trends_tab:
        render_trends(store)
    with exports_tab:
        render_exports(store)


if __name__ == "__main__":
    main()
