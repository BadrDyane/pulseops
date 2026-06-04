import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=60, pattern=r'^[a-z0-9-]+$')
    description: str | None = None


class ProjectResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    created_at: datetime
    name: str
    slug: str
    description: str | None
    is_active: bool


class ApiKeyCreate(BaseModel):
    label: str | None = None


class ApiKeyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    created_at: datetime
    project_id: uuid.UUID
    key_prefix: str
    label: str | None
    is_active: bool
    last_used_at: datetime | None
    expires_at: datetime | None


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned only once at creation — includes the plaintext key."""
    key: str