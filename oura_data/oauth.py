from __future__ import annotations

import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from .config import Settings


AUTHORIZATION_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"


class OAuthError(RuntimeError):
    pass


class AuthStateError(OAuthError):
    pass


def new_state() -> str:
    return secrets.token_urlsafe(32)


def validate_state(expected: str | None, actual: str | None) -> None:
    if not expected or not actual or not secrets.compare_digest(expected, actual):
        raise AuthStateError("OAuth state did not match. Start the Oura connection again.")


def build_authorization_url(
    *,
    client_id: str,
    redirect_uri: str,
    scopes: list[str],
    state: str,
) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    if scopes:
        params["scope"] = " ".join(scopes)
    return f"{AUTHORIZATION_URL}?{urlencode(params)}"


@dataclass
class JsonFileStore:
    path: Path

    def read(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, value: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        tmp_path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
        tmp_path.chmod(0o600)
        tmp_path.replace(self.path)
        self.path.chmod(0o600)

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()


class TokenStore(JsonFileStore):
    pass


class OAuthStateStore(JsonFileStore):
    def save_state(self, state: str) -> None:
        self.write({"state": state, "created_at": int(time.time())})

    def read_state(self) -> str | None:
        payload = self.read()
        if not payload:
            return None
        return str(payload.get("state") or "")


def _raise_for_token_error(response: requests.Response) -> None:
    if response.status_code < 400:
        return
    try:
        detail = response.json()
    except ValueError:
        detail = response.text
    raise OAuthError(f"Oura token request failed with {response.status_code}: {detail}")


def _with_expiry(payload: dict[str, Any]) -> dict[str, Any]:
    now = int(time.time())
    expires_in = int(payload.get("expires_in") or 0)
    return {
        **payload,
        "obtained_at": now,
        "expires_at": now + expires_in if expires_in else None,
    }


def exchange_code_for_tokens(
    *,
    code: str,
    settings: Settings,
    session: requests.Session | Any = requests,
) -> dict[str, Any]:
    response = session.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.redirect_uri,
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    _raise_for_token_error(response)
    return _with_expiry(response.json())


def refresh_access_token(
    *,
    refresh_token: str,
    settings: Settings,
    session: requests.Session | Any = requests,
) -> dict[str, Any]:
    response = session.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    _raise_for_token_error(response)
    return _with_expiry(response.json())
