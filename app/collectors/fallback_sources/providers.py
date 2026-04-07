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
    def fetch(self, query: str) -> list[dict]:
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus('site:threads.com ' + query)}"
        return _search_common(search_url, query, css='a.result__a')


class BingThreadsProvider(FallbackProvider):
    def fetch(self, query: str) -> list[dict]:
        search_url = f"https://www.bing.com/search?q={quote_plus('site:threads.com ' + query)}"
        return _search_common(search_url, query, css='li.b_algo h2 a')


class MultiSearchProvider(FallbackProvider):
    def __init__(self) -> None:
        self.providers = [DuckDuckGoThreadsProvider(), BingThreadsProvider()]

    def fetch(self, query: str) -> list[dict]:
        combined: dict[str, dict] = {}
        for provider in self.providers:
            for row in provider.fetch(query):
                combined[row['post_url']] = row
        return list(combined.values())


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


def _search_common(url: str, query: str, css: str) -> list[dict]:
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            resp = client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp.raise_for_status()
    except Exception as exc:
        logger.warning(f'web fallback failed for {query}: {exc}')
        return []

    soup = BeautifulSoup(resp.text, 'lxml')
    rows: list[dict] = []
    for link in soup.select(css):
        href = link.get('href') or ''
        if 'threads.com' not in href or '/post/' not in href:
            continue
        ext = href.rstrip('/').split('/')[-1]
        rows.append(
            {
                'external_id': f'fallback-search-{ext}',
                'source': 'fallback_search',
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
