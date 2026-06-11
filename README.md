# Bioloop

Privacy-first, open-source data-art studio designed to help you own, archive, and transform wearable history into calm, reflective artifacts. It connects to the Oura API via OAuth, backs up your history into a private local SQLite database, and renders beautiful 24-hour radial Life Rings mapping sleep stages, recovery trends, workouts, and tags.

Bioloop is artifact-first, not dashboard-first. The intended first impression is a private museum of the user's wearable history: stories, artifacts, timeline, studio, and privacy controls before metric dashboards or analysis panels. See the [Product and UX Constitution](docs/PRODUCT_UX_CONSTITUTION.md), [Product Experience Design](docs/PRODUCT_EXPERIENCE_DESIGN.md), and [Visual References](docs/VISUAL_REFERENCES.md).

The sleep rings visualization is inspired by Dmitry Sergeev's original Oura chart:

- Dmitry Sergeev: <https://www.linkedin.com/in/sergeyevdmitry/>
- Original LinkedIn post: <https://www.linkedin.com/feed/update/urn:li:activity:7467961204125208576/>

This project is independent and is not affiliated with, endorsed by, or sponsored by Oura.

## Features

- OAuth authorization code flow for Oura API v2.
- Local SQLite archive for sleep, readiness, activity, workouts, tags, sessions, SpO2, stress, ring configuration, heart health, and heart-rate data.
- 24-hour Life Rings artifact with sleep/awake, sleep-stage colors, custom palettes, month/season guides, and workout/tag overlays.
- Supporting trend views for sleep duration, scores, HRV, resting heart rate, workouts, tags, and monthly summaries.
- CSV exports for normalized and raw archive tables.
- Public Streamlit session mode for safer multi-user hosting.

## Local Setup

1. Create an Oura API application at <https://cloud.ouraring.com/oauth/applications>.
2. Add `http://localhost:8501` as a redirect URI.
3. Copy `.env.example` to `.env` and fill in your values:

```env
APP_NAME=Bioloop
APP_CONTACT_EMAIL=you@example.com
OURA_CLIENT_ID=your_oura_client_id
OURA_CLIENT_SECRET=your_oura_client_secret
OURA_REDIRECT_URI=http://localhost:8501
OURA_PUBLIC_BASE_URL=http://localhost:8501
OURA_SCOPES=
OURA_DATA_DIR=data
OURA_STORAGE_MODE=local
```

4. Install and run:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/streamlit run app.py
```

Local mode stores tokens and Oura health data under `data/`, which is ignored by git.

## Streamlit Community Cloud

For public deployment, set Streamlit secrets from `.streamlit/secrets.toml.example` and use session storage:

```toml
APP_NAME = "Bioloop"
APP_CONTACT_EMAIL = "you@example.com"
OURA_CLIENT_ID = "your_oura_client_id"
OURA_CLIENT_SECRET = "your_oura_client_secret"
OURA_REDIRECT_URI = "https://your-app-name.streamlit.app"
OURA_PUBLIC_BASE_URL = "https://your-app-name.streamlit.app"
OURA_SCOPES = ""
OURA_STORAGE_MODE = "session"
```

Then add the deployed app URL as an Oura redirect URI.

Leave `OURA_SCOPES` blank to request all scopes configured in the Oura Developer Portal. Set it only if you want to request a narrower space-separated list.

Session mode creates a temporary token/database workspace per Streamlit session. This avoids one shared token or one shared SQLite archive across public users. Users should export anything they want to keep before the session ends.

## Oura Developer Portal URLs

After deployment, use:

- Website URL: `https://your-app-name.streamlit.app`
- Privacy Policy URL: `https://your-app-name.streamlit.app/?view=privacy`
- Terms of Service URL: `https://your-app-name.streamlit.app/?view=terms`
- Redirect URI: `https://your-app-name.streamlit.app`

See [docs/OURA_REVIEW_CHECKLIST.md](docs/OURA_REVIEW_CHECKLIST.md).

## Data Handling

- The app uses OAuth and does not use personal access tokens.
- Oura data is used only to sync, normalize, visualize, analyze, and export the connected user's data.
- The app does not sell data and does not include analytics or advertising telemetry.
- `.env`, Streamlit secrets, OAuth tokens, SQLite databases, downloaded data, and logs are excluded from git.

## Development

```bash
.venv/bin/python -m pytest
```

Before designing or implementing product-facing changes, read [docs/PRODUCT_UX_CONSTITUTION.md](docs/PRODUCT_UX_CONSTITUTION.md). Build artifact-first: prioritize Stories, Artifacts, Timeline, Studio, and Settings / Privacy. Avoid metric-dashboard homepages, chatbot-first navigation, red/green scoring systems, gamification, medical claims, and raw health values in shared outputs by default.

Use synthetic fixtures only. Do not commit real Oura data, screenshots containing private data, or OAuth credentials.

## License

MIT. See [LICENSE](LICENSE).
