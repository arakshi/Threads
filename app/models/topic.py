from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Topic(Base):
    __tablename__ = 'topics'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    keywords_csv: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
