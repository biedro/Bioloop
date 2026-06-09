from __future__ import annotations

from collections import deque
from datetime import datetime

import pytest

from oura_data import client as client_mod
from oura_data.client import OuraClient, OuraForbiddenError
from oura_data.config import Settings
from oura_data.oauth import TokenStore


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}
        self.text = str(self._payload)

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = deque(responses)
        self.requests = []

    def request(self, method, url, params, headers, timeout):
        self.requests.append({"method": method, "url": url, "params": params, "headers": headers})
        return self.responses.popleft()


@pytest.fixture
def settings(tmp_path):
    return Settings(
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


def token_store(settings):
    store = TokenStore(settings.token_path)
    store.write({"access_token": "access-1", "refresh_token": "refresh-1", "expires_at": 4_102_444_800})
    return store


def test_get_collection_paginates(settings):
    session = FakeSession(
        [
            FakeResponse(payload={"data": [{"id": "a"}], "next_token": "next"}),
            FakeResponse(payload={"data": [{"id": "b"}], "next_token": None}),
        ]
    )
    client = OuraClient(settings, token_store(settings), session=session)

    docs = client.get_collection("sleep", start="2026-01-01", end="2026-01-31")

    assert docs == [{"id": "a"}, {"id": "b"}]
    assert session.requests[1]["params"]["next_token"] == "next"


def test_heartrate_collection_chunks_requests_to_30_days(settings):
    session = FakeSession(
        [
            FakeResponse(payload={"data": [{"timestamp": "2026-01-01T00:00:00Z"}], "next_token": None}),
            FakeResponse(payload={"data": [{"timestamp": "2026-01-31T00:00:00Z"}], "next_token": None}),
            FakeResponse(payload={"data": [{"timestamp": "2026-03-02T00:00:00Z"}], "next_token": None}),
        ]
    )
    client = OuraClient(settings, token_store(settings), session=session)

    docs = client.get_collection(
        "heartrate",
        start="2026-01-01T00:00:00+00:00",
        end="2026-03-15T00:00:00+00:00",
    )

    assert len(docs) == 3
    assert len(session.requests) == 3
    for request in session.requests:
        start = datetime.fromisoformat(request["params"]["start_datetime"])
        end = datetime.fromisoformat(request["params"]["end_datetime"])
        assert (end - start).days <= 30
    assert session.requests[0]["params"]["start_datetime"] == "2026-01-01T00:00:00+00:00"
    assert session.requests[-1]["params"]["end_datetime"] == "2026-03-15T00:00:00+00:00"


def test_429_uses_retry_after(settings):
    sleeps = []
    session = FakeSession(
        [
            FakeResponse(status_code=429, headers={"Retry-After": "3"}),
            FakeResponse(payload={"data": [], "next_token": None}),
        ]
    )
    client = OuraClient(settings, token_store(settings), session=session, sleeper=sleeps.append)

    assert client.get_collection("daily_sleep") == []
    assert sleeps == [3]


def test_401_refreshes_and_retries(settings, monkeypatch):
    session = FakeSession(
        [
            FakeResponse(status_code=401, payload={"detail": "expired"}),
            FakeResponse(payload={"data": [{"id": "ok"}], "next_token": None}),
        ]
    )
    store = token_store(settings)

    def fake_refresh_access_token(refresh_token, settings, session):
        return {"access_token": "access-2", "refresh_token": "refresh-2", "expires_at": 4_102_444_800}

    monkeypatch.setattr(client_mod, "refresh_access_token", fake_refresh_access_token)
    client = OuraClient(settings, store, session=session)

    docs = client.get_collection("daily_sleep")

    assert docs == [{"id": "ok"}]
    assert session.requests[1]["headers"]["Authorization"] == "Bearer access-2"
    assert store.read()["refresh_token"] == "refresh-2"


def test_403_is_graceful_exception(settings):
    session = FakeSession([FakeResponse(status_code=403, payload={"detail": "missing scope"})])
    client = OuraClient(settings, token_store(settings), session=session)

    with pytest.raises(OuraForbiddenError):
        client.get_collection("daily_spo2")


def test_401_scope_error_is_treated_as_forbidden(settings):
    session = FakeSession([FakeResponse(status_code=401, payload={"detail": "Token is not authorized access spo2 scope."})])
    client = OuraClient(settings, token_store(settings), session=session)

    with pytest.raises(OuraForbiddenError):
        client.get_collection("daily_spo2")
