from abc import ABC, abstractmethod
from datetime import datetime, timezone
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup
from loguru import logger


class FallbackProvider(ABC):
    @abstractmethod
    def fetch(self, query: str) -> list[dict]:
        raise NotImplementedError


class DuckDuckGoThreadsProvider(FallbackProvider):
    """Public web fallback: search Threads post links via DuckDuckGo HTML."""

    def fetch(self, query: str) -> list[dict]:
        search_url = f"https://duckduckgo.com/html/?q={quote_plus('site:threads.net ' + query)}"
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(search_url, headers={'User-Agent': 'Mozilla/5.0'})
                resp.raise_for_status()
        except Exception as exc:
            logger.warning(f'ddg fallback failed for {query}: {exc}')
            return []

        soup = BeautifulSoup(resp.text, 'lxml')
        rows: list[dict] = []
        for link in soup.select('a.result__a'):
            href = link.get('href') or ''
            if 'threads.net' not in href or '/post/' not in href:
                continue
            ext = href.rstrip('/').split('/')[-1]
            rows.append(
                {
                    'external_id': f'fallback-ddg-{ext}',
                    'source': 'fallback_duckduckgo',
                    'post_url': href,
                    'text': (link.get_text() or '').strip(),
                    'created_at_external': datetime.now(timezone.utc),
                    'likes': None,
                    'replies': None,
                    'reposts': None,
                    'quotes': None,
                    'has_media': False,
                    'media_count': 0,
                    'language': 'unknown',
                    'author_handle': None,
                }
            )
        return rows


class DemoSearchProvider(FallbackProvider):
    def fetch(self, query: str) -> list[dict]:
        return [
            {
                'external_id': f'fallback-{query}-1',
                'source': 'fallback_demo',
                'post_url': f'https://example.com/threads/{query}/1',
                'text': f'Demo fallback result for {query}',
                'created_at_external': None,
                'likes': None,
                'replies': None,
                'reposts': None,
                'quotes': None,
                'has_media': False,
                'media_count': 0,
                'language': 'en',
                'author_handle': 'fallback',
            }
        ]
