import json
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup


def extract_json_ld(html: str) -> dict:
    soup = BeautifulSoup(html, 'lxml')
    script = soup.find('script', {'type': 'application/ld+json'})
    if not script or not script.string:
        return {}
    try:
        return json.loads(script.string)
    except json.JSONDecodeError:
        return {}


def _extract_count_by_patterns(html: str, keys: list[str]) -> int | None:
    for key in keys:
        patterns = [
            rf'"{key}"\s*:\s*(\d+)',
            rf"'{key}'\s*:\s*(\d+)",
        ]
        for p in patterns:
            m = re.search(p, html, re.IGNORECASE)
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    continue
    return None


def parse_public_post(html: str, url: str) -> dict:
    data = extract_json_ld(html)
    text = data.get('articleBody') or data.get('description')
    author = ((data.get('author') or {}).get('alternateName') or '').strip('@') or 'unknown'
    external_id_match = re.search(r'/post/([A-Za-z0-9_-]+)', url)
    external_id = external_id_match.group(1) if external_id_match else url.rsplit('/', 1)[-1]
    interaction = data.get('interactionStatistic') or []
    metric_map = {i.get('interactionType', '').lower(): i.get('userInteractionCount') for i in interaction if isinstance(i, dict)}

    likes = metric_map.get('https://schema.org/likeaction')
    replies = metric_map.get('https://schema.org/commentaction')
    reposts = metric_map.get('https://schema.org/shareaction')

    if likes is None:
        likes = _extract_count_by_patterns(html, ['like_count', 'likes', 'likeCount'])
    if replies is None:
        replies = _extract_count_by_patterns(html, ['reply_count', 'replies', 'replyCount', 'comment_count'])
    if reposts is None:
        reposts = _extract_count_by_patterns(html, ['repost_count', 'reposts', 'share_count'])

    quotes = _extract_count_by_patterns(html, ['quote_count', 'quotes'])

    return {
        'external_id': external_id,
        'source': 'threads_public_web',
        'post_url': url,
        'text': text,
        'created_at_external': datetime.now(timezone.utc),
        'likes': likes,
        'replies': replies,
        'reposts': reposts,
        'quotes': quotes,
        'has_media': '<img' in html or '<video' in html,
        'media_count': html.count('<img') + html.count('<video'),
        'language': data.get('inLanguage') if isinstance(data, dict) else None,
        'author_handle': author,
    }
