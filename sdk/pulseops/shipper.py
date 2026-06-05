from __future__ import annotations

import httpx

from pulseops._internal.logging import get_sdk_logger
from pulseops.models import BatchPayload, EventPayload

logger = get_sdk_logger()


class BatchShipper:
    def __init__(self, base_url: str, project_key: str, timeout_sec: float = 10.0) -> None:
        self._ingest_url = base_url.rstrip("/") + "/api/v1/ingest"
        self._project_key = project_key
        self._timeout = timeout_sec

    def ship(self, events: list[EventPayload]) -> bool:
        if not events:
            return True
        payload = BatchPayload(project_key=self._project_key, events=events)
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    self._ingest_url,
                    content=payload.model_dump_json(),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.warning(f"PulseOps ship failed: {e}")
            return False