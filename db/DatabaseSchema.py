from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import enum


class Base(DeclarativeBase):
    pass


class TicketCategory(str, enum.Enum):
    builder = "builder"
    developer = "developer"
    support = "support"
    misc = "misc"
    application = "application"


class CommissionStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class IndividualTicket(Base):
    __tablename__ = "tickets"

    channel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    author_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    author_name: Mapped[str] = mapped_column(String, nullable=False)

    category: Mapped[TicketCategory] = mapped_column(
        Enum(TicketCategory, native_enum=False),
        nullable=False
    )

    first_message: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    voice_channel: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    commission: Mapped["Commission"] = relationship(
        back_populates="ticket",
        uselist=False,
    )


class Commission(Base):
    __tablename__ = "commission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    project_name: Mapped[str] = mapped_column(String, nullable=False)
    budget: Mapped[str] = mapped_column(String, nullable=False)
    brief: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    ticket_channel_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tickets.channel_id"),
        nullable=True,
        unique=True,
    )

    ticket: Mapped[IndividualTicket] = relationship(
        IndividualTicket,
        back_populates="commission",
    )

    status: Mapped[CommissionStatus] = mapped_column(
        Enum(CommissionStatus, native_enum=False),
        nullable=False,
        default=CommissionStatus.open,
        server_default=CommissionStatus.open.value,
    )

    assignments: Mapped[list["CommissionAssignment"]] = relationship(
        "CommissionAssignment", back_populates="commission", cascade="all, delete-orphan"
    )
    bills: Mapped[list["Bill"]] = relationship(
        "Bill", back_populates="commission", cascade="all, delete-orphan"
    )


class CommissionAssignment(Base):
    __tablename__ = "commission_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    commission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commission.id"), nullable=False
    )
    member_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    member_name: Mapped[str] = mapped_column(String, nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    commission: Mapped["Commission"] = relationship(
        "Commission", back_populates="assignments"
    )


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    commission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commission.id"), nullable=False
    )
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    deposit_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    deposit_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    final_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stripe_deposit_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    stripe_final_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    crypto_deposit_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    crypto_final_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    commission: Mapped["Commission"] = relationship(
        "Commission", back_populates="bills"
    )


class BotConfig(Base):
    __tablename__ = "bot_config"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
