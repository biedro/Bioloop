from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared for the app
    load_dotenv = None


DEFAULT_SCOPES: list[str] = []


@dataclass(frozen=True)
class Settings:
    app_name: str
    client_id: str
    client_secret: str
    redirect_uri: str
    public_base_url: str
    contact_email: str
    storage_mode: str
    data_dir: Path
    db_path: Path
    token_path: Path
    oauth_state_path: Path
    scopes: list[str]

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.redirect_uri)


def load_settings() -> Settings:
    if load_dotenv:
        load_dotenv()

    scopes = [
        scope
        for scope in os.getenv("OURA_SCOPES", "").replace(",", " ").split()
        if scope
    ]
    data_dir = Path(os.getenv("OURA_DATA_DIR", "data")).expanduser()
    storage_mode = os.getenv("OURA_STORAGE_MODE", "local").strip().lower()
    if storage_mode not in {"local", "session"}:
        storage_mode = "local"
    return Settings(
        app_name=os.getenv("APP_NAME", "Bioloop").strip(),
        client_id=os.getenv("OURA_CLIENT_ID", "").strip(),
        client_secret=os.getenv("OURA_CLIENT_SECRET", "").strip(),
        redirect_uri=os.getenv("OURA_REDIRECT_URI", "http://localhost:8501").strip(),
        public_base_url=os.getenv("OURA_PUBLIC_BASE_URL", "http://localhost:8501").strip(),
        contact_email=os.getenv("APP_CONTACT_EMAIL", "").strip(),
        storage_mode=storage_mode,
        data_dir=data_dir,
        db_path=data_dir / "oura.sqlite3",
        token_path=data_dir / "tokens.json",
        oauth_state_path=data_dir / "oauth_state.json",
        scopes=scopes or DEFAULT_SCOPES.copy(),
    )
