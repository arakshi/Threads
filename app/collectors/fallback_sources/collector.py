from app.collectors.base import BaseCollector
from app.collectors.fallback_sources.providers import DemoSearchProvider


class FallbackCollector(BaseCollector):
    name = 'fallback_sources'

    def __init__(self) -> None:
        self.provider = DemoSearchProvider()

    def collect(self, seeds: dict) -> list[dict]:
        keywords = seeds.get('keywords', [])
        rows = []
        for keyword in keywords:
            rows.extend(self.provider.fetch(keyword))
        return rows
