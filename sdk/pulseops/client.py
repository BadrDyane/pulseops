from __future__ import annotations

import atexit

from pulseops.buffer import BatchBuffer
from pulseops.config import PulseOpsConfig
from pulseops.shipper import BatchShipper
from pulseops.wrapper import WrappedOpenAIClient


class PulseOps:
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        sample_rate: float = 1.0,
        batch_size: int = 50,
        flush_interval_sec: float = 5.0,
        timeout_sec: float = 10.0,
        debug: bool = False,
        register_shutdown_hook: bool = True,
    ) -> None:
        self.config = PulseOpsConfig(
            api_key=api_key,
            base_url=base_url,
            sample_rate=sample_rate,
            batch_size=batch_size,
            flush_interval_sec=flush_interval_sec,
            timeout_sec=timeout_sec,
            debug=debug,
            register_shutdown_hook=register_shutdown_hook,
        )
        self._shipper = BatchShipper(
            base_url=base_url,
            project_key=api_key,
            timeout_sec=timeout_sec,
        )
        self._buffer = BatchBuffer(
            shipper=self._shipper,
            max_size=batch_size,
            flush_interval_sec=flush_interval_sec,
        )
        if register_shutdown_hook:
            atexit.register(self.shutdown)

    def wrap(self, client: object) -> WrappedOpenAIClient:
        return WrappedOpenAIClient(
            underlying=client,
            config=self.config,
            buffer=self._buffer,
        )

    def flush(self) -> None:
        self._buffer.flush()

    def shutdown(self) -> None:
        self._buffer.stop()

    def stats(self) -> dict[str, int]:
        return self._buffer.stats()
