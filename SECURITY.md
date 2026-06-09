# Security Policy

## Sensitive Data

Do not commit `.env`, `.streamlit/secrets.toml`, OAuth tokens, SQLite databases, downloaded Oura exports, logs, or screenshots containing health data.

For local use, data is stored under `OURA_DATA_DIR` and excluded from git. For public Streamlit deployments, use `OURA_STORAGE_MODE=session` so each user gets a temporary session-scoped token and SQLite workspace.

## Reporting

Report security or privacy issues to the maintainer email configured for the deployed app.

## Oura Data

Oura data can include sensitive health and biometric information. Treat every export, log, and visualization as private unless the user explicitly chooses to share it.
