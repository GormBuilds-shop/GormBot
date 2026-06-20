import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from db.DatabaseSchema import Base, Commission, IndividualTicket, TicketCategory, Bill
from db.BillingConnection import BillingConnection

@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        ticket = IndividualTicket(
            channel_id=100, author_id=200, author_name="Client", category=TicketCategory.builder
        )
        sess.add(ticket)
        await sess.commit()
        comm = Commission(
            project_name="Test", budget="$500", brief="Brief", description="Desc",
            ticket_channel_id=100
        )
        sess.add(comm)
        await sess.commit()
        yield sess, comm.id
    await engine.dispose()

@pytest.mark.asyncio
async def test_create_bill(session):
    sess, comm_id = session
    conn = BillingConnection(sess)
    bill = await conn.create_bill(comm_id, 500.00, "USD", 50)
    assert bill.id is not None
    assert bill.total_amount == 500.00
    assert bill.deposit_percent == 50

@pytest.mark.asyncio
async def test_get_bill_by_commission(session):
    sess, comm_id = session
    conn = BillingConnection(sess)
    await conn.create_bill(comm_id, 500.00, "USD", 50)
    bill = await conn.get_bill_by_commission(comm_id)
    assert bill is not None
    assert bill.total_amount == 500.00

@pytest.mark.asyncio
async def test_get_unpaid_bills(session):
    sess, comm_id = session
    conn = BillingConnection(sess)
    await conn.create_bill(comm_id, 500.00, "USD", 50)
    unpaid = await conn.get_unpaid_bills()
    assert len(unpaid) == 1

@pytest.mark.asyncio
async def test_mark_deposit_paid(session):
    sess, comm_id = session
    conn = BillingConnection(sess)
    bill = await conn.create_bill(comm_id, 500.00, "USD", 50)
    await conn.mark_deposit_paid(bill.id)
    updated = await conn.get_bill_by_commission(comm_id)
    assert updated.deposit_paid is True

@pytest.mark.asyncio
async def test_mark_final_paid(session):
    sess, comm_id = session
    conn = BillingConnection(sess)
    bill = await conn.create_bill(comm_id, 500.00, "USD", 50)
    await conn.mark_final_paid(bill.id)
    updated = await conn.get_bill_by_commission(comm_id)
    assert updated.final_paid is True
