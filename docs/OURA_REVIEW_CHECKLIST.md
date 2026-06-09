# Oura Review Checklist

Use this checklist before requesting approval for more than 10 users in the Oura Developer Portal.

## Developer Portal Fields

- Website URL: `https://your-app-name.streamlit.app`
- Privacy Policy URL: `https://your-app-name.streamlit.app/?view=privacy`
- Terms of Service URL: `https://your-app-name.streamlit.app/?view=terms`
- Redirect URI: `https://your-app-name.streamlit.app`
- Contact email: the same monitored email shown in the app's privacy policy.

## Streamlit Secrets

Set these in Streamlit Community Cloud secrets:

```toml
APP_NAME = "Bioloop"
APP_CONTACT_EMAIL = "you@example.com"
OURA_CLIENT_ID = "..."
OURA_CLIENT_SECRET = "..."
OURA_REDIRECT_URI = "https://your-app-name.streamlit.app"
OURA_PUBLIC_BASE_URL = "https://your-app-name.streamlit.app"
OURA_SCOPES = ""
OURA_STORAGE_MODE = "session"
```

## Review Notes

- The app uses OAuth authorization code flow.
- `OURA_SCOPES` is blank by default so Oura requests the scopes configured in the Developer Portal.
- The app does not use personal access tokens.
- The app is independent and not affiliated with Oura.
- Public deployment uses session-scoped temporary storage rather than one shared persistent token or database.
- Users can disconnect in the sidebar.
- Sleep rings attribution is included for Dmitry Sergeev's original visualization inspiration.
