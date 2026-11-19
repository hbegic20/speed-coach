import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.audits import process_audit


async def run_audit(context: dict[str, Any], audit_id: str) -> None:
    session_factory: async_sessionmaker[AsyncSession] = context["session_factory"]
    async with session_factory() as session:
        await process_audit(session, uuid.UUID(audit_id))
