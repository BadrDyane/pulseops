from unittest.mock import MagicMock, patch

import pytest

from pulseops.buffer import BatchBuffer
from pulseops.config import PulseOpsConfig
from pulseops.wrapper import WrappedOpenAIClient


def make_mock_response(model="gpt-4o-mini", content="Hello!", input_tokens=10, output_tokens=5):
    response = MagicMock()
    response.usage.prompt_tokens = input_tokens
    response.usage.completion_tokens = output_tokens
    response.choices[0].message.content = content
    response.model = model
    return response


class MockShipper:
    def __init__(self):
        self.shipped = []

    def ship(self, events) -> bool:
        self.shipped.extend(events)
        return True


def make_wrapped_client(sample_rate=1.0):
    mock_openai = MagicMock()
    mock_response = make_mock_response()
    mock_openai.chat.completions.create.return_value = mock_response

    config = PulseOpsConfig(api_key="po_proj_test", sample_rate=sample_rate)
    shipper = MockShipper()
    buffer = BatchBuffer(shipper, max_size=50, flush_interval_sec=60.0)
    client = WrappedOpenAIClient(underlying=mock_openai, config=config, buffer=buffer)
    return client, buffer, shipper, mock_openai


def test_returns_original_response():
    client, buffer, shipper, mock_openai = make_wrapped_client()
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}])
    assert resp == mock_openai.chat.completions.create.return_value
    buffer.stop()


def test_event_captured():
    client, buffer, shipper, _ = make_wrapped_client()
    client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}])
    buffer.flush()
    assert len(shipper.shipped) == 1
    assert shipper.shipped[0].model == "gpt-4o-mini"
    buffer.stop()


def test_pulseops_tags_not_forwarded_to_openai():
    client, buffer, shipper, mock_openai = make_wrapped_client()
    client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}],
        pulseops_tags={"feature": "test_feature", "tenant_id": "acme"},
    )
    call_kwargs = mock_openai.chat.completions.create.call_args
    assert "pulseops_tags" not in call_kwargs.kwargs
    buffer.stop()


def test_feature_and_tenant_captured():
    client, buffer, shipper, _ = make_wrapped_client()
    client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[],
        pulseops_tags={"feature": "classifier", "tenant_id": "acme"},
    )
    buffer.flush()
    event = shipper.shipped[0]
    assert event.feature == "classifier"
    assert event.tenant_id == "acme"
    buffer.stop()


def test_error_always_logged_regardless_of_sample_rate():
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.side_effect = Exception("rate limit")
    config = PulseOpsConfig(api_key="po_proj_test", sample_rate=0.0)
    shipper = MockShipper()
    buffer = BatchBuffer(shipper, max_size=50, flush_interval_sec=60.0)
    client = WrappedOpenAIClient(underlying=mock_openai, config=config, buffer=buffer)
    with pytest.raises(Exception):
        client.chat.completions.create(model="gpt-4o-mini", messages=[])
    buffer.flush()
    assert len(shipper.shipped) == 1
    assert shipper.shipped[0].is_error is True
    buffer.stop()


def test_non_error_not_logged_at_zero_sample_rate():
    client, buffer, shipper, _ = make_wrapped_client(sample_rate=0.0)
    client.chat.completions.create(model="gpt-4o-mini", messages=[])
    buffer.flush()
    assert len(shipper.shipped) == 0
    buffer.stop()


def test_getattr_forwarded_to_underlying():
    client, buffer, _, mock_openai = make_wrapped_client()
    _ = client.images
    mock_openai.images  # just access it
    buffer.stop()