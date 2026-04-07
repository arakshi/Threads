from collections import Counter
from sqlalchemy.orm import Session

from app.analytics.viral_score import calculate_viral_score
from app.collectors.fallback_sources.collector import FallbackCollector
from app.collectors.official_api.collector import OfficialApiCollector
from app.collectors.public_web.collector import PublicWebCollector
from app.collectors.public_web.parser import parse_public_post
from app.models import Account
from app.nlp.clustering import cluster_texts
from app.nlp.patterns import classify_format, extract_cta, extract_hook, sentiment_tone
from app.services.repositories import AccountRepo, PostRepo
from app.utils.http import HttpClientFactory
from app.utils.text import dedup_hash


class IngestionPipeline:
    def __init__(self, db: Session):
        self.db = db
        self.account_repo = AccountRepo(db)
        self.post_repo = PostRepo(db)
        self.http = HttpClientFactory()
        self.collectors = [PublicWebCollector(), FallbackCollector(), OfficialApiCollector()]

    def _resolve_account_id(self, handle: str | None) -> int | None:
        if not handle:
            return None
        handle = handle.strip('@')
        account = self.db.query(Account).filter(Account.handle == handle).one_or_none()
        if account:
            return account.id
        account = self.account_repo.create(handle=handle)
        return account.id


    def _enrich_metrics(self, item: dict) -> dict:
        has_any = any(item.get(k) is not None for k in ('likes', 'replies', 'reposts', 'quotes'))
        if has_any:
            return item
        url = item.get('post_url')
        if not url or not str(url).startswith('http'):
            return item
        try:
            resp = self.http.get(url)
            resp.raise_for_status()
            parsed = parse_public_post(resp.text, url)
            for key in ('likes', 'replies', 'reposts', 'quotes', 'has_media', 'media_count', 'text', 'language'):
                if item.get(key) is None:
                    item[key] = parsed.get(key)
        except Exception:
            return item
        return item

    def run(self, seeds: dict) -> dict:
        collected: list[dict] = []
        for collector in self.collectors:
            collected.extend(collector.collect(seeds))

        texts = [item.get('text') or '' for item in collected]
        clusters = cluster_texts(texts) if texts else []

        prepared = []
        for idx, item in enumerate(collected):
            item = self._enrich_metrics(item)
            text = item.get('text')
            sentiment, tone = sentiment_tone(text)
            payload = {
                'external_id': item['external_id'],
                'source': item['source'],
                'account_id': self._resolve_account_id(item.get('author_handle')),
                'post_url': item['post_url'],
                'text': text,
                'created_at_external': item.get('created_at_external'),
                'likes': item.get('likes'),
                'replies': item.get('replies'),
                'reposts': item.get('reposts'),
                'quotes': item.get('quotes'),
                'has_media': item.get('has_media', False),
                'media_count': item.get('media_count', 0),
                'language': item.get('language'),
                'viral_score': calculate_viral_score(
                    likes=item.get('likes'),
                    replies=item.get('replies'),
                    reposts=item.get('reposts'),
                    quotes=item.get('quotes'),
                    followers_hint=None,
                    created_at=item.get('created_at_external'),
                ),
                'engagement_rate': None,
                'sentiment': sentiment,
                'tone': tone,
                'format_type': classify_format(text),
                'hook': extract_hook(text),
                'cta': extract_cta(text),
                'dedup_hash': dedup_hash(text),
                'cluster_id': clusters[idx] if idx < len(clusters) else None,
            }
            prepared.append(payload)

        inserted = self.post_repo.upsert_bulk(prepared)
        by_source = dict(Counter([item.get('source', 'unknown') for item in collected]))
        return {'collected': len(collected), 'inserted': inserted, 'by_source': by_source}
