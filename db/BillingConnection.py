from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .DatabaseSchema import Bill


class BillingConnection:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_bill(
        self,
        commission_id: int,
        total_amount: float,
        currency: str,
        deposit_percent: int
    ) -> Bill:
        bill = Bill(
            commission_id=commission_id,
            total_amount=total_amount,
            currency=currency,
            deposit_percent=deposit_percent
        )
        self.session.add(bill)
        await self.session.commit()
        return bill

    async def get_bill_by_commission(self, commission_id: int) -> Optional[Bill]:
        result = await self.session.execute(
            select(Bill).where(Bill.commission_id == commission_id)
        )
        return result.scalar_one_or_none()

    async def get_unpaid_bills(self) -> list[Bill]:
        result = await self.session.execute(
            select(Bill).where(
                or_(Bill.deposit_paid == False, Bill.final_paid == False)
            )
        )
        return list(result.scalars().all())

    async def mark_deposit_paid(self, bill_id: int) -> None:
        bill = await self.session.get(Bill, bill_id)
        if bill:
            bill.deposit_paid = True
            await self.session.commit()

    async def mark_final_paid(self, bill_id: int) -> None:
        bill = await self.session.get(Bill, bill_id)
        if bill:
            bill.final_paid = True
            await self.session.commit()

    async def set_stripe_deposit_id(self, bill_id: int, stripe_id: str) -> None:
        bill = await self.session.get(Bill, bill_id)
        if bill:
            bill.stripe_deposit_id = stripe_id
            await self.session.commit()

    async def set_stripe_final_id(self, bill_id: int, stripe_id: str) -> None:
        bill = await self.session.get(Bill, bill_id)
        if bill:
            bill.stripe_final_id = stripe_id
            await self.session.commit()

    async def set_crypto_deposit_id(self, bill_id: int, crypto_id: str) -> None:
        bill = await self.session.get(Bill, bill_id)
        if bill:
            bill.crypto_deposit_id = crypto_id
            await self.session.commit()

    async def set_crypto_final_id(self, bill_id: int, crypto_id: str) -> None:
        bill = await self.session.get(Bill, bill_id)
        if bill:
            bill.crypto_final_id = crypto_id
            await self.session.commit()
