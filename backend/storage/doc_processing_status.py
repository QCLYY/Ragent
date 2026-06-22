"""Document processing progress state stored in Redis cache."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from backend.storage.cache import cache


_TTL_SECONDS = 3600


def _status_key(filename: str, tenant_id: int) -> str:
    raw = f"{tenant_id}:{filename}".encode("utf-8", errors="ignore")
    digest = hashlib.sha1(raw).hexdigest()
    return f"doc_processing:{digest}"


def set_document_processing_status(
    filename: str,
    tenant_id: int,
    *,
    status: str,
    stage: str,
    progress: int,
    message: str,
    chunks: int | None = None,
    error: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "filename": filename,
        "tenant_id": tenant_id,
        "status": status,
        "stage": stage,
        "progress": max(0, min(100, int(progress))),
        "message": message,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if chunks is not None:
        payload["chunks"] = chunks
    if error:
        payload["error"] = error
    if extra:
        payload.update(extra)
    cache.set_json(_status_key(filename, tenant_id), payload, ttl=_TTL_SECONDS)
    return payload


def get_document_processing_status(filename: str, tenant_id: int) -> dict[str, Any] | None:
    return cache.get_json(_status_key(filename, tenant_id))
