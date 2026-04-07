import re
from pathlib import Path

from loguru import logger

from app.collectors.base import BaseCollector
from app.collectors.public_web.parser import parse_public_post
from app.core.config import get_settings
from app.utils.http import HttpClientFactory


class PublicWebCollector(BaseCollector):
    name = 'public_web'

    def __init__(self) -> None:
        self.settings = get_settings()
        self.http = HttpClientFactory()

    def _discover_from_account(self, handle: str) -> list[str]:
        handle = handle.strip('@')
        profile_url = f'https://www.threads.net/@{handle}'
        try:
            resp = self.http.get(profile_url)
            resp.raise_for_status()
            found = set(re.findall(r'https://www\.threads\.net/@[^"\']+/post/[A-Za-z0-9_-]+', resp.text))
            if not found:
                found = set(re.findall(r'/@[^"\']+/post/[A-Za-z0-9_-]+', resp.text))
                found = {f'https://www.threads.net{x}' for x in found}
            return list(found)
        except Exception as exc:
            logger.warning(f'account discovery failed for {handle}: {exc}')
            return []

    def collect(self, seeds: dict) -> list[dict]:
        urls = set(seeds.get('post_urls', []))
        for account in seeds.get('accounts', []):
            urls.update(self._discover_from_account(account))

        records: list[dict] = []
        for url in urls:
            try:
                if url.startswith('demo://'):
                    fixture = Path('data/fixtures/sample_thread_post.html').read_text(encoding='utf-8')
                    parsed = parse_public_post(fixture, 'https://www.threads.net/@demo/post/DEMO123')
                else:
                    response = self.http.get(url)
                    response.raise_for_status()
                    parsed = parse_public_post(response.text, url)
                records.append(parsed)
            except Exception as exc:
                logger.warning(f'public_web failed for {url}: {exc}')
        return records
