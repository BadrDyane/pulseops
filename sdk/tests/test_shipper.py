import httpx
import pytest

from pulseops.models import EventPayload
from pulseops.shipper import BatchShipper


def make_event() -> EventPayload:
    return EventPayload(
        client_event_id="test-001",
        model="gpt-4o-mini",
        sampled_at="2026-01-01T00:00:00Z",
    )


def test_ship_success(respx_mock):
    respx_mock.post("http://localhost:9999/api/v1/ingest").mock(
        return_value=httpx.Response(201, json={"ingested": 1, "skipped": 0})
    )
    shipper = BatchShipper(base_url="http://localhost:9999", project_key="po_proj_test")
    result = shipper.ship([make_event()])
    assert result is True


def test_ship_server_error(respx_mock):
    respx_mock.post("http://localhost:9999/api/v1/ingest").mock(
        return_value=httpx.Response(500)
    )
    shipper = BatchShipper(base_url="http://localhost:9999", project_key="po_proj_test")
    result = shipper.ship([make_event()])
    assert result is False


def test_ship_connection_error(respx_mock):
    respx_mock.post("http://localhost:9999/api/v1/ingest").mock(
        side_effect=httpx.ConnectError("refused")
    )
    shipper = BatchShipper(base_url="http://localhost:9999", project_key="po_proj_test")
    result = shipper.ship([make_event()])
    assert result is False


def test_ship_empty_list():
    shipper = BatchShipper(base_url="http://localhost:9999", project_key="po_proj_test")
    result = shipper.ship([])
    assert result is True


def test_payload_contains_project_key(respx_mock):
    captured = {}

    def capture(request):
        import json
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"ingested": 1, "skipped": 0})

    respx_mock.post("http://localhost:9999/api/v1/ingest").mock(side_effect=capture)
    shipper = BatchShipper(base_url="http://localhost:9999", project_key="po_proj_abc")
    shipper.ship([make_event()])
    assert captured["body"]["project_key"] == "po_proj_abc"