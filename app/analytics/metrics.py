from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.post import Post


def top_posts_window(db: Session, days: int = 1, limit: int = 20):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = (
        select(Post)
        .where(Post.collected_at >= since)
        .order_by(Post.viral_score.desc().nullslast(), Post.collected_at.desc())
        .limit(limit)
    )
    return db.scalars(stmt).all()


def keyword_trend(db: Session, keyword: str, days: int = 30) -> int:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = select(func.count()).select_from(Post).where(Post.collected_at >= since, Post.text.ilike(f'%{keyword}%'))
    return db.scalar(stmt) or 0
