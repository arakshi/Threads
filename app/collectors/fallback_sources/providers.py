from abc import ABC, abstractmethod
from datetime import datetime, timezone
from urllib.parse import quote_plus
import re

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
        return _search_html(search_url, query, css='a.result__a')


class BingThreadsProvider(FallbackProvider):
    def fetch(self, query: str) -> list[dict]:
        search_url = f"https://www.bing.com/search?q={quote_plus('site:threads.com ' + query)}"
        return _search_html(search_url, query, css='li.b_algo h2 a')


class DirectThreadsSearchProvider(FallbackProvider):
    def fetch(self, query: str) -> list[dict]:
        url = f"https://www.threads.com/search?q={quote_plus(query)}"
        try:
            with httpx.Client(timeout=25, follow_redirects=True) as client:
                resp = client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                resp.raise_for_status()
        except Exception as exc:
            logger.warning(f'threads search failed for {query}: {exc}')
            return []

        links = set(re.findall(r'https://www\.threads\.com/@[^"\']+/post/[A-Za-z0-9_-]+', resp.text))
        rows = [_row_from_link(link, source='fallback_threads_search') for link in links]
        return rows


class JinaMirrorThreadsProvider(FallbackProvider):
    """Fallback via jina AI mirror that often exposes links from JS-heavy pages."""

    def fetch(self, query: str) -> list[dict]:
        url = f"https://r.jina.ai/http://https://www.threads.com/search?q={quote_plus(query)}"
        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()
        except Exception as exc:
            logger.warning(f'jina mirror failed for {query}: {exc}')
            return []

        links = set(re.findall(r'https://www\.threads\.com/@[^\s)]+/post/[A-Za-z0-9_-]+', resp.text))
        return [_row_from_link(link, source='fallback_jina') for link in links]


class MultiSearchProvider(FallbackProvider):
    def __init__(self) -> None:
        self.providers = [
            DuckDuckGoThreadsProvider(),
            BingThreadsProvider(),
            DirectThreadsSearchProvider(),
            JinaMirrorThreadsProvider(),
        ]

    def fetch(self, query: str) -> list[dict]:
        combined: dict[str, dict] = {}
        for provider in self.providers:
            rows = provider.fetch(query)
            logger.info(f'fallback provider {provider.__class__.__name__} for "{query}": {len(rows)} links')
            for row in rows:
                combined[row['post_url']] = row
        return list(combined.values())


class DemoSearchProvider(FallbackProvider):
    def fetch(self, query: str) -> list[dict]:
        return [_row_from_link('https://www.threads.com/@demo/post/DEMO123', source='fallback_demo', text=f'Demo fallback result for {query}')]


def _search_html(url: str, query: str, css: str) -> list[dict]:
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
        rows.append(_row_from_link(href, source='fallback_search', text=(link.get_text() or '').strip()))
    return rows


def _row_from_link(link: str, source: str, text: str | None = None) -> dict:
    ext = link.rstrip('/').split('/')[-1]
    return {
        'external_id': f'{source}-{ext}',
        'source': source,
        'post_url': link,
        'text': text,
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
