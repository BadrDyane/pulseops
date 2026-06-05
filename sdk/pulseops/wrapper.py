from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone

from pulseops._internal.logging import get_sdk_logger
from pulseops.buffer import BatchBuffer
from pulseops.config import PulseOpsConfig
from pulseops.cost import estimate_cost
from pulseops.models import EventPayload
from pulseops.sampling import should_log

logger = get_sdk_logger()


class _CompletionsProxy:
    def __init__(
        self,
        underlying_completions: object,
        config: PulseOpsConfig,
        buffer: BatchBuffer,
    ) -> None:
        self._underlying = underlying_completions
        self._config = config
        self._buffer = buffer

    def create(self, *args, **kwargs) -> object:
        tags: dict = kwargs.pop("pulseops_tags", None) or {}

        feature = tags.pop("feature", None)
        tenant_id = tags.pop("tenant_id", None)
        user_id = tags.pop("user_id", None)

        model = kwargs.get("model", args[0] if args else "unknown")
        messages = kwargs.get("messages", [])

        start = time.monotonic()
        is_error = False
        error_code: str | None = None
        error_message: str | None = None
        response = None

        try:
            response = self._underlying.create(*args, **kwargs)
        except Exception as e:
            is_error = True
            error_code = type(e).__name__
            error_message = str(e)
            raise
        finally:
            latency_ms = int((time.monotonic() - start) * 1000)

            try:
                if not is_error and response is not None:
                    input_tokens = getattr(getattr(response, "usage", None), "prompt_tokens", 0) or 0
                    output_tokens = getattr(getattr(response, "usage", None), "completion_tokens", 0) or 0
                    choices = getattr(response, "choices", [])
                    response_text = ""
                    if choices:
                        msg = getattr(choices[0], "message", None)
                        response_text = getattr(msg, "content", "") or ""
                    if kwargs.get("stream"):
                        logger.warning("pulseops: streaming responses are not instrumented in v1 — call not logged")
                        return response
                else:
                    input_tokens = 0
                    output_tokens = 0
                    response_text = ""

                if should_log(is_error, self._config.sample_rate):
                    event = EventPayload(
                        client_event_id=str(uuid.uuid4()),
                        model=model,
                        feature=feature,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        tags={"_client_event_id": str(uuid.uuid4()), **{k: str(v) for k, v in tags.items()}},
                        messages_json=json.dumps(messages),
                        response_text=response_text,
                        latency_ms=latency_ms,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        estimated_cost_usd=estimate_cost(model, input_tokens, output_tokens),
                        is_error=is_error,
                        error_code=error_code,
                        error_message=error_message,
                        sampled_at=datetime.now(timezone.utc).isoformat(),
                        sample_rate=self._config.sample_rate,
                    )
                    self._buffer.add(event)
            except Exception as sdk_err:
                logger.warning(f"pulseops: capture error (non-fatal): {sdk_err}")

        return response


class _ChatProxy:
    def __init__(
        self,
        underlying_chat: object,
        config: PulseOpsConfig,
        buffer: BatchBuffer,
    ) -> None:
        self._underlying = underlying_chat
        self._config = config
        self._buffer = buffer

    @property
    def completions(self) -> _CompletionsProxy:
        return _CompletionsProxy(
            self._underlying.completions,
            self._config,
            self._buffer,
        )


class WrappedOpenAIClient:
    def __init__(
        self,
        underlying: object,
        config: PulseOpsConfig,
        buffer: BatchBuffer,
    ) -> None:
        self._underlying = underlying
        self._config = config
        self._buffer = buffer

    @property
    def chat(self) -> _ChatProxy:
        return _ChatProxy(self._underlying.chat, self._config, self._buffer)

    def __getattr__(self, name: str) -> object:
        return getattr(self._underlying, name)