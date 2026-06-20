from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .DatabaseSchema import Commission


class CommissionConnection:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_commission(self, comm: Commission) -> str | None:
        if comm.ticket_channel_id is not None:
            existing = await self.get_comm_by_channel(comm.ticket_channel_id)
            if existing is not None:
                return "commission already exists for this ticket!"

        self.session.add(comm)
        await self.session.commit()
        return None

    async def upsert_comm(self, comm: Commission) -> None:
        await self.session.merge(comm)
        await self.session.commit()

    async def delete_comm(self, channel_id: int) -> Optional[Commission]:
        comm = await self.get_comm_by_channel(channel_id)
        if comm is None:
            return None

        await self.session.delete(comm)
        await self.session.commit()
        return comm

    async def get_comm(self, commission_id: int) -> Optional[Commission]:
        return await self.session.get(Commission, commission_id)

    async def get_comm_by_channel(self, channel_id: int) -> Optional[Commission]:
        result = await self.session.execute(
            select(Commission).where(Commission.ticket_channel_id == channel_id)
        )
        return result.scalar_one_or_none()
