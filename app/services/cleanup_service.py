from datetime import datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.log import Log


class CleanupService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def delete_old_log(self, retention_days: int):

        cutoff = datetime.now() - timedelta(days=retention_days)

        stmt = delete(Log).where(Log.ingested_at < cutoff)

        try:
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount
        except Exception:
            await self.session.rollback()
            raise
