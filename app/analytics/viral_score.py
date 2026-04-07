from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ViralComponents:
    engagement_score: float
    velocity_score: float
    novelty_score: float
    authority_adjustment: float
    recency_decay: float


def _safe(v: int | None) -> float:
    return float(v or 0)


def calculate_components(
    likes: int | None,
    replies: int | None,
    reposts: int | None,
    quotes: int | None,
    followers_hint: int | None,
    created_at: datetime | None,
) -> ViralComponents:
    likes_f, replies_f, reposts_f, quotes_f = _safe(likes), _safe(replies), _safe(reposts), _safe(quotes)
    engagement_score = likes_f + 1.7 * replies_f + 2.2 * reposts_f + 2.4 * quotes_f
    velocity_score = (replies_f + reposts_f * 2 + likes_f * 0.2) / 10
    novelty_score = min(20.0, 5 + quotes_f * 0.5 + replies_f * 0.2)
    authority_adjustment = 0.8 if not followers_hint else max(0.7, min(1.3, 1 + (followers_hint / 1_000_000)))
    hours = 24
    if created_at:
        hours = max(1, (datetime.now(timezone.utc) - created_at).total_seconds() / 3600)
    recency_decay = 1 / (1 + hours / 24)
    return ViralComponents(engagement_score, velocity_score, novelty_score, authority_adjustment, recency_decay)


def calculate_viral_score(**kwargs) -> float:
    c = calculate_components(**kwargs)
    score = (c.engagement_score * 0.5 + c.velocity_score * 0.25 + c.novelty_score * 0.25) * c.authority_adjustment * c.recency_decay
    return round(score, 3)
