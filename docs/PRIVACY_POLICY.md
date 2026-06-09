# Privacy Policy

Last updated: June 8, 2026

Bioloop is an independent, open-source dashboard for users who choose to connect their Oura account through OAuth.

The app may access Oura profile, sleep, readiness, activity, heart-rate, workout, tag, session, SpO2, stress, ring configuration, and heart health data depending on scopes granted by the user.

Data is used only to sync, normalize, visualize, analyze, and export the connected user's own Oura data. The app does not sell Oura data and does not use it for advertising.

In local mode, tokens and synced data are stored on the user's own machine. In public Streamlit session mode, tokens and synced data are stored in a temporary per-session workspace on the app server so different users do not share one token or one SQLite archive.

Users can disconnect from Oura in the sidebar. In session mode, disconnecting deletes the temporary session token and local session database.

The app sends requests to Oura's API after user consent. It does not intentionally share Oura data with other third parties. Hosting providers may process operational logs and runtime infrastructure data according to their own policies.

This app is not affiliated with, endorsed by, or sponsored by Oura.
