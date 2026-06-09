from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .client import ENDPOINTS, OuraClient, OuraForbiddenError
from .storage import OuraStore


@dataclass
class SyncResult:
    endpoint: str
    status: str
    rows: int
    message: str = ""


ProgressCallback = Callable[[str, str], None]


def sync_endpoint(
    *,
    client: OuraClient,
    store: OuraStore,
    endpoint: str,
    start: str | None,
    end: str | None,
    progress: ProgressCallback | None = None,
) -> SyncResult:
    if progress:
        progress(endpoint, "running")
    store.mark_sync_started(endpoint)
    try:
        docs = client.get_collection(endpoint, start=start, end=end)
        rows = store.store_endpoint(endpoint, docs)
        store.mark_sync_complete(endpoint, rows)
        if progress:
            progress(endpoint, "ok")
        return SyncResult(endpoint=endpoint, status="ok", rows=rows)
    except OuraForbiddenError as exc:
        message = str(exc)
        store.mark_sync_error(endpoint, "skipped", message)
        if progress:
            progress(endpoint, "skipped")
        return SyncResult(endpoint=endpoint, status="skipped", rows=0, message=message)
    except Exception as exc:
        message = str(exc)
        store.mark_sync_error(endpoint, "error", message)
        if progress:
            progress(endpoint, "error")
        return SyncResult(endpoint=endpoint, status="error", rows=0, message=message)


def sync_all(
    *,
    client: OuraClient,
    store: OuraStore,
    start: str | None,
    end: str | None,
    endpoints: list[str] | None = None,
    progress: ProgressCallback | None = None,
) -> list[SyncResult]:
    results: list[SyncResult] = []
    for endpoint in endpoints or ENDPOINTS:
        results.append(
            sync_endpoint(
                client=client,
                store=store,
                endpoint=endpoint,
                start=start,
                end=end,
                progress=progress,
            )
        )
    return results
