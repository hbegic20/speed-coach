import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.audit import Audit


async def reload_audit(
    session_factory: async_sessionmaker[AsyncSession], audit_id: uuid.UUID
) -> Audit:
    async with session_factory() as session:
        audit = await session.get(Audit, audit_id)
        assert audit is not None
        return audit
