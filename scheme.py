from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GovernmentScheme(Base):
    __tablename__ = "government_schemes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    short_name: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    eligibility: Mapped[str] = mapped_column(Text, nullable=False)
    benefits: Mapped[str] = mapped_column(Text, nullable=False)
    required_documents: Mapped[str] = mapped_column(Text, nullable=False)
    application_process: Mapped[str] = mapped_column(Text, nullable=False)
    official_url: Mapped[str] = mapped_column(String(300), nullable=False)
    last_verified_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    verification_note: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    state_applicability: Mapped[str] = mapped_column(String(120), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
