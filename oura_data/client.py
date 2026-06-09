from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from .config import Settings
from .oauth import TokenStore, refresh_access_token


API_BASE_URL = "https://api.ouraring.com"

ENDPOINTS = [
    "personal_info",
    "sleep",
    "daily_sleep",
    "daily_readiness",
    "daily_activity",
    "heartrate",
    "workout",
    "tag",
    "enhanced_tag",
    "session",
    "daily_spo2",
    "daily_stress",
    "daily_resilience",
    "sleep_time",
    "rest_mode_period",
    "daily_cardiovascular_age",
    "vO2_max",
    "ring_configuration",
    "ring_battery_level",
]

DATETIME_ENDPOINTS = {"heartrate", "ring_battery_level"}


class OuraApiError(RuntimeError):
    pass


class OuraForbiddenError(OuraApiError):
    pass


class OuraUnauthorizedError(OuraApiError):
    pass


class OuraClient:
    def __init__(
        self,
        settings: Settings,
        token_store: TokenStore,
        session: requests.Session | None = None,
        sleeper: Any = time.sleep,
    ):
        self.settings = settings
        self.token_store = token_store
        self.session = session or requests.Session()
        self.sleeper = sleeper

    def get_collection(
        self,
        endpoint: str,
        *,
        start: str | None = None,
        end: str | None = None,
        fields: str | None = None,
    ) -> list[dict[str, Any]]:
        if endpoint == "personal_info":
            payload = self._request("GET", f"/v2/usercollection/{endpoint}", params={})
            return [payload]

        if endpoint == "heartrate" and start and end:
            return self._get_chunked_datetime_collection(
                endpoint,
                start=start,
                end=end,
                fields=fields,
                max_window=timedelta(days=30),
            )

        docs: list[dict[str, Any]] = []
        next_token: str | None = None

        while True:
            params = self._date_params(endpoint, start, end)
            if fields:
                params["fields"] = fields
            if next_token:
                params["next_token"] = next_token

            payload = self._request("GET", f"/v2/usercollection/{endpoint}", params=params)
            page = payload.get("data", [])
            if not isinstance(page, list):
                raise OuraApiError(f"Unexpected response for {endpoint}: data was not a list")
            docs.extend(page)
            next_token = payload.get("next_token")
            if not next_token:
                return docs

    def _get_chunked_datetime_collection(
        self,
        endpoint: str,
        *,
        start: str,
        end: str,
        fields: str | None,
        max_window: timedelta,
    ) -> list[dict[str, Any]]:
        start_dt = parse_api_datetime(start)
        end_dt = parse_api_datetime(end)
        if start_dt >= end_dt:
            return []

        docs: list[dict[str, Any]] = []
        window_start = start_dt
        while window_start < end_dt:
            window_end = min(window_start + max_window, end_dt)
            docs.extend(
                self._get_collection_page_loop(
                    endpoint,
                    start=window_start.isoformat(),
                    end=window_end.isoformat(),
                    fields=fields,
                )
            )
            window_start = window_end
        return docs

    def _get_collection_page_loop(
        self,
        endpoint: str,
        *,
        start: str | None,
        end: str | None,
        fields: str | None,
    ) -> list[dict[str, Any]]:
        docs: list[dict[str, Any]] = []
        next_token: str | None = None

        while True:
            params = self._date_params(endpoint, start, end)
            if fields:
                params["fields"] = fields
            if next_token:
                params["next_token"] = next_token

            payload = self._request("GET", f"/v2/usercollection/{endpoint}", params=params)
            page = payload.get("data", [])
            if not isinstance(page, list):
                raise OuraApiError(f"Unexpected response for {endpoint}: data was not a list")
            docs.extend(page)
            next_token = payload.get("next_token")
            if not next_token:
                return docs

    def _date_params(self, endpoint: str, start: str | None, end: str | None) -> dict[str, str]:
        if not start and not end:
            return {}
        if endpoint in DATETIME_ENDPOINTS:
            params: dict[str, str] = {}
            if start:
                params["start_datetime"] = start
            if end:
                params["end_datetime"] = end
            return params
        params = {}
        if start:
            params["start_date"] = start[:10]
        if end:
            params["end_date"] = end[:10]
        return params

    def _request(self, method: str, path: str, params: dict[str, Any]) -> dict[str, Any]:
        refreshed = False
        for _ in range(5):
            token = self._valid_access_token()
            response = self.session.request(
                method,
                f"{API_BASE_URL}{path}",
                params=params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                timeout=60,
            )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "1"))
                self.sleeper(max(retry_after, 1))
                continue

            if response.status_code == 401 and self._is_scope_error(response):
                raise OuraForbiddenError(self._error_message(response))

            if response.status_code == 401 and not refreshed:
                self._refresh_tokens()
                refreshed = True
                continue

            if response.status_code == 403:
                raise OuraForbiddenError(self._error_message(response))

            if response.status_code == 401:
                raise OuraUnauthorizedError(self._error_message(response))

            if response.status_code >= 400:
                raise OuraApiError(self._error_message(response))

            return response.json()

        raise OuraApiError("Oura API rate limit did not clear after retries.")

    def _valid_access_token(self) -> str:
        tokens = self.token_store.read()
        if not tokens or not tokens.get("access_token"):
            raise OuraUnauthorizedError("No Oura access token is stored.")

        expires_at = tokens.get("expires_at")
        if expires_at and int(expires_at) - int(time.time()) < 120 and tokens.get("refresh_token"):
            tokens = self._refresh_tokens()

        return str(tokens["access_token"])

    def _refresh_tokens(self) -> dict[str, Any]:
        tokens = self.token_store.read()
        if not tokens or not tokens.get("refresh_token"):
            raise OuraUnauthorizedError("No refresh token is available.")

        refreshed = refresh_access_token(
            refresh_token=str(tokens["refresh_token"]),
            settings=self.settings,
            session=self.session,
        )
        self.token_store.write(refreshed)
        return refreshed

    @staticmethod
    def _error_message(response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        return f"Oura API returned {response.status_code}: {payload}"

    @staticmethod
    def _is_scope_error(response: requests.Response) -> bool:
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        text = str(payload).lower()
        return "scope" in text and "not authorized" in text


def parse_api_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
