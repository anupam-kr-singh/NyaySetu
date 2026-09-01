"""Lawyer profiles and their specialization taxonomy."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Enum, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VerificationStatus(str, enum.Enum):
    UNSUBMITTED = "UNSUBMITTED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


lawyer_specializations = Table(
    "lawyer_specializations", Base.metadata,
    Column("lawyer_profile_id", UUID(as_uuid=True), ForeignKey("lawyer_profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("specialization_id", UUID(as_uuid=True), ForeignKey("specializations.id", ondelete="RESTRICT"), primary_key=True),
)


class Specialization(Base):
    __tablename__ = "specializations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class LawyerProfile(Base):
    __tablename__ = "lawyer_profiles"
    __table_args__ = (CheckConstraint("years_of_experience IS NULL OR years_of_experience >= 0", name="ck_lawyer_profiles_years_nonnegative"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True)
    bar_registration_number: Mapped[str | None] = mapped_column(String(200))
    bio: Mapped[str | None] = mapped_column(Text)
    jurisdiction: Mapped[str | None] = mapped_column(String(200))
    city: Mapped[str | None] = mapped_column(String(120))
    years_of_experience: Mapped[int | None] = mapped_column(Integer)
    consultation_fee_note: Mapped[str | None] = mapped_column(String(500))
    verification_status: Mapped[VerificationStatus] = mapped_column(Enum(VerificationStatus, name="lawyer_verification_status", native_enum=True), nullable=False, default=VerificationStatus.UNSUBMITTED)
    is_accepting_requests: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    specializations: Mapped[list[Specialization]] = relationship(secondary=lawyer_specializations, lazy="selectin")
