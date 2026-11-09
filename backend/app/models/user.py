from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, Index, String, Text, func, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AccountStatus, UserRole


def enum_values(enum_cls):
    return [item.value for item in enum_cls]


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),
        CheckConstraint("length(trim(full_name)) > 0", name="ck_users_full_name_nonempty"),
        Index("uq_users_email_ci", text("lower(email)"), unique=True),
        Index("ix_users_role_status", "role", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role", values_callable=enum_values, native_enum=True), nullable=False, default=UserRole.LEARNER)
    status: Mapped[AccountStatus] = mapped_column(SAEnum(AccountStatus, name="account_status", values_callable=enum_values, native_enum=True), nullable=False, default=AccountStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc))
