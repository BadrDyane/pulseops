import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.projects import ApiKey, Project


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def validate_api_key(
    key: str, db: AsyncSession
) -> Project | None:
    key_hash = hash_api_key(key)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.key_hash == key_hash)
        .where(ApiKey.is_active == True)
        .where(
            (ApiKey.expires_at == None) | (ApiKey.expires_at > now)
        )
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        return None

    project_result = await db.execute(
        select(Project).where(Project.id == api_key.project_id)
    )
    return project_result.scalar_one_or_none()