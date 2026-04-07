from datetime import datetime, timezone

from app.analytics.viral_score import calculate_viral_score


def test_viral_score_nonzero():
    score = calculate_viral_score(
        likes=100,
        replies=20,
        reposts=10,
        quotes=5,
        followers_hint=10_000,
        created_at=datetime.now(timezone.utc),
    )
    assert score > 0
