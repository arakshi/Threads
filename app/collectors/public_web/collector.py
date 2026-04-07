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

    def collect(self, seeds: dict) -> list[dict]:
        urls = seeds.get('post_urls', [])
        records: list[dict] = []
        for url in urls:
            try:
                if self.settings.demo_mode and 'demo://' in url:
                    from pathlib import Path

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
