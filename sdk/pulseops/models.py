from pydantic import BaseModel, Field


class EventPayload(BaseModel):
    client_event_id: str
    model: str
    feature: str | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    messages_json: str = ""
    response_text: str = ""
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    is_error: bool = False
    error_code: str | None = None
    error_message: str | None = None
    sampled_at: str = ""
    sample_rate: float = 1.0


class BatchPayload(BaseModel):
    project_key: str
    events: list[EventPayload]