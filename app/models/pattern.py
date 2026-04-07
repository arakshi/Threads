from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PatternInsight(Base):
    __tablename__ = 'pattern_insights'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic: Mapped[str] = mapped_column(String(120), index=True)
    pattern_type: Mapped[str] = mapped_column(String(60), index=True)
    value: Mapped[str] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
