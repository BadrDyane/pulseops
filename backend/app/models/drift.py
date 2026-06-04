import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DriftSnapshot(Base):
    __tablename__ = "drift_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    feature: Mapped[str] = mapped_column(String, nullable=False)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    window_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_response_len: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    avg_output_tokens: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    p50_output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    p95_output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_latency_ms: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    frac_json: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    frac_error: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    is_drifted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    drift_metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)