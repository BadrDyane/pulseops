from __future__ import annotations
from pulseops.config import PulseOpsConfig


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

    def wrap(self, client: object) -> object:
        raise NotImplementedError("SDK wrapping implemented in Phase 2")

    def flush(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def stats(self) -> dict[str, int]:
        return {"events_logged": 0, "events_dropped": 0, "flush_count": 0}