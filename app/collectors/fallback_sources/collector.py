from app.collectors.base import BaseCollector
from app.collectors.fallback_sources.providers import DemoSearchProvider, DuckDuckGoThreadsProvider
from app.core.config import get_settings


class FallbackCollector(BaseCollector):
    name = 'fallback_sources'

    def __init__(self) -> None:
        settings = get_settings()
        self.provider = DemoSearchProvider() if settings.demo_mode else DuckDuckGoThreadsProvider()

    def collect(self, seeds: dict) -> list[dict]:
        keywords = seeds.get('keywords', [])
        rows = []
        for keyword in keywords:
            rows.extend(self.provider.fetch(keyword))
        return rows
