import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    feature: Mapped[str] = mapped_column(String, nullable=False)
    version_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    version_num: Mapped[int] = mapped_column(Integer, nullable=False)
    system_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "feature", "version_hash"),
    )