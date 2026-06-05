import time
import threading

import pytest

from pulseops.buffer import BatchBuffer
from pulseops.models import EventPayload


def make_event(i: int = 0) -> EventPayload:
    return EventPayload(
        client_event_id=f"test-{i}",
        model="gpt-4o-mini",
        sampled_at="2026-01-01T00:00:00Z",
    )


class MockShipper:
    def __init__(self, should_fail: bool = False) -> None:
        self.shipped: list = []
        self.should_fail = should_fail

    def ship(self, events) -> bool:
        if self.should_fail:
            return False
        self.shipped.extend(events)
        return True


def test_add_and_flush():
    shipper = MockShipper()
    buf = BatchBuffer(shipper, max_size=50, flush_interval_sec=60.0)
    buf.add(make_event(1))
    buf.add(make_event(2))
    buf.flush()
    assert len(shipper.shipped) == 2
    buf.stop()


def test_flush_on_max_size():
    shipper = MockShipper()
    buf = BatchBuffer(shipper, max_size=5, flush_interval_sec=60.0)
    for i in range(5):
        buf.add(make_event(i))
    time.sleep(1.5)  # let daemon thread fire
    assert len(shipper.shipped) == 5
    buf.stop()


def test_flush_on_interval():
    shipper = MockShipper()
    buf = BatchBuffer(shipper, max_size=50, flush_interval_sec=1.0)
    buf.add(make_event(1))
    time.sleep(2.0)
    assert len(shipper.shipped) == 1
    buf.stop()


def test_dropped_events_on_ship_failure():
    shipper = MockShipper(should_fail=True)
    buf = BatchBuffer(shipper, max_size=50, flush_interval_sec=60.0)
    buf.add(make_event(1))
    buf.flush()
    stats = buf.stats()
    assert stats["events_logged"] == 1
    assert stats["events_dropped"] == 1
    buf.stop()


def test_stats_counts():
    shipper = MockShipper()
    buf = BatchBuffer(shipper, max_size=50, flush_interval_sec=60.0)
    for i in range(3):
        buf.add(make_event(i))
    buf.flush()
    stats = buf.stats()
    assert stats["events_logged"] == 3
    assert stats["events_dropped"] == 0
    assert stats["flush_count"] >= 1
    buf.stop()


def test_thread_safety():
    shipper = MockShipper()
    buf = BatchBuffer(shipper, max_size=200, flush_interval_sec=60.0)
    threads = []
    for i in range(10):
        t = threading.Thread(target=lambda i=i: [buf.add(make_event(i * 10 + j)) for j in range(10)])
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    buf.flush()
    assert buf.stats()["events_logged"] == 100
    assert len(shipper.shipped) == 100
    buf.stop()


def test_shutdown_flushes_remaining():
    shipper = MockShipper()
    buf = BatchBuffer(shipper, max_size=50, flush_interval_sec=60.0)
    buf.add(make_event(1))
    buf.add(make_event(2))
    buf.stop()
    assert len(shipper.shipped) == 2