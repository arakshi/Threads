from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Post(Base):
    __tablename__ = 'posts'
    __table_args__ = (UniqueConstraint('external_id', name='uq_posts_external_id'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str] = mapped_column(String(64), default='threads_public_web')
    account_id: Mapped[int | None] = mapped_column(ForeignKey('accounts.id'), nullable=True)
    post_url: Mapped[str] = mapped_column(String(1000), unique=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at_external: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replies: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reposts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quotes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_media: Mapped[bool] = mapped_column(Boolean, default=False)
    media_count: Mapped[int] = mapped_column(Integer, default=0)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    viral_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    engagement_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    format_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    hook: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cta: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dedup_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    cluster_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    collected_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account = relationship('Account', back_populates='posts')
