from __future__ import annotations

import threading
import time

from pulseops._internal.logging import get_sdk_logger
from pulseops.models import EventPayload
from pulseops.shipper import BatchShipper

logger = get_sdk_logger()


class BatchBuffer:
    def __init__(
        self,
        shipper: BatchShipper,
        max_size: int = 50,
        flush_interval_sec: float = 5.0,
    ) -> None:
        self._shipper = shipper
        self._max_size = max_size
        self._flush_interval = flush_interval_sec

        self._events: list[EventPayload] = []
        self._lock = threading.Lock()
        self._last_flush = time.monotonic()
        self._stopped = False

        self._events_logged = 0
        self._events_dropped = 0
        self._flush_count = 0

        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

    def add(self, event: EventPayload) -> None:
        with self._lock:
            self._events.append(event)
            self._events_logged += 1
            if len(self._events) >= self._max_size:
                self._last_flush = 0.0  # signal immediate flush

    def _flush_loop(self) -> None:
        while not self._stopped:
            time.sleep(0.5)
            age = time.monotonic() - self._last_flush
            with self._lock:
                should = len(self._events) >= self._max_size or age >= self._flush_interval
            if should:
                self._do_flush()

    def _do_flush(self) -> None:
        with self._lock:
            if not self._events:
                return
            to_ship = self._events[:]
            self._events.clear()
            self._last_flush = time.monotonic()

        success = self._shipper.ship(to_ship)
        self._flush_count += 1
        if not success:
            self._events_dropped += len(to_ship)

    def flush(self) -> None:
        self._do_flush()

    def stop(self) -> None:
        self._stopped = True
        self._do_flush()

    def stats(self) -> dict[str, int]:
        return {
            "events_logged": self._events_logged,
            "events_dropped": self._events_dropped,
            "flush_count": self._flush_count,
        }