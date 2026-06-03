from dataclasses import dataclass


@dataclass
class PulseOpsConfig:
    api_key: str
    base_url: str = "http://localhost:8000"
    sample_rate: float = 1.0
    batch_size: int = 50
    flush_interval_sec: float = 5.0
    timeout_sec: float = 10.0
    debug: bool = False
    register_shutdown_hook: bool = True