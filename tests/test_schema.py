import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from db.DatabaseSchema import (
    Base, Commission, CommissionAssignment, Bill, BotConfig,
    IndividualTicket, TicketCategory
)

@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    await engine.dispose()

@pytest.mark.asyncio
async def test_commission_assignment_creation(session):
    ticket = IndividualTicket(
        channel_id=123, author_id=456, author_name="Test", category=TicketCategory.builder
    )
    session.add(ticket)
    await session.commit()

    comm = Commission(
        project_name="Test", budget="$100", brief="Brief", description="Desc",
        ticket_channel_id=123
    )
    session.add(comm)
    await session.commit()

    assignment = CommissionAssignment(
        commission_id=comm.id, member_id=789, member_name="Builder"
    )
    session.add(assignment)
    await session.commit()

    assert assignment.id is not None
    assert assignment.assigned_at is not None

@pytest.mark.asyncio
async def test_bill_creation(session):
    ticket = IndividualTicket(
        channel_id=100, author_id=200, author_name="Client", category=TicketCategory.builder
    )
    session.add(ticket)
    await session.commit()

    comm = Commission(
        project_name="Project", budget="$500", brief="Brief", description="Desc",
        ticket_channel_id=100
    )
    session.add(comm)
    await session.commit()

    bill = Bill(
        commission_id=comm.id, total_amount=500.00, currency="USD", deposit_percent=50
    )
    session.add(bill)
    await session.commit()

    assert bill.id is not None
    assert bill.deposit_paid is False
    assert bill.final_paid is False

@pytest.mark.asyncio
async def test_bot_config(session):
    config = BotConfig(key="stripe_enabled", value="true")
    session.add(config)
    await session.commit()

    result = await session.get(BotConfig, "stripe_enabled")
    assert result.value == "true"
