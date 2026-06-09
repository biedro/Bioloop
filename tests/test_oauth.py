from __future__ import annotations

import pytest

from oura_data.config import Settings
from oura_data.oauth import (
    AuthStateError,
    TokenStore,
    build_authorization_url,
    refresh_access_token,
    validate_state,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = str(self._payload)

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, data, headers, timeout):
        self.calls.append({"url": url, "data": data, "headers": headers, "timeout": timeout})
        return FakeResponse(
            payload={
                "access_token": "access-2",
                "refresh_token": "refresh-2",
                "expires_in": 3600,
                "token_type": "bearer",
            }
        )


def test_build_authorization_url_contains_expected_params():
    url = build_authorization_url(
        client_id="client",
        redirect_uri="http://localhost:8501",
        scopes=["daily", "heartrate"],
        state="state-1",
    )

    assert url.startswith("https://cloud.ouraring.com/oauth/authorize?")
    assert "response_type=code" in url
    assert "client_id=client" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8501" in url
    assert "scope=daily+heartrate" in url
    assert "state=state-1" in url


def test_build_authorization_url_omits_blank_scope():
    url = build_authorization_url(
        client_id="client",
        redirect_uri="http://localhost:8501",
        scopes=[],
        state="state-1",
    )

    assert "scope=" not in url
    assert "state=state-1" in url


def test_validate_state_rejects_mismatch():
    validate_state("abc", "abc")

    with pytest.raises(AuthStateError):
        validate_state("abc", "def")


def test_token_store_round_trips_atomically(tmp_path):
    store = TokenStore(tmp_path / "tokens.json")
    store.write({"access_token": "a", "refresh_token": "r"})
    store.write({"access_token": "b", "refresh_token": "s"})

    assert store.read() == {"access_token": "b", "refresh_token": "s"}


def test_refresh_access_token_posts_refresh_grant(tmp_path):
    settings = Settings(
        app_name="Bioloop",
        client_id="client",
        client_secret="secret",
        redirect_uri="http://localhost:8501",
        public_base_url="http://localhost:8501",
        contact_email="test@example.com",
        storage_mode="local",
        data_dir=tmp_path,
        db_path=tmp_path / "oura.sqlite3",
        token_path=tmp_path / "tokens.json",
        oauth_state_path=tmp_path / "state.json",
        scopes=["daily"],
    )
    session = FakeSession()

    tokens = refresh_access_token(refresh_token="refresh-1", settings=settings, session=session)

    assert tokens["access_token"] == "access-2"
    assert tokens["refresh_token"] == "refresh-2"
    assert tokens["expires_at"] > tokens["obtained_at"]
    assert session.calls[0]["data"]["grant_type"] == "refresh_token"
    assert session.calls[0]["data"]["client_secret"] == "secret"
