from app.collectors.base import BaseCollector
from app.collectors.fallback_sources.providers import DemoSearchProvider, MultiSearchProvider


class FallbackCollector(BaseCollector):
    name = 'fallback_sources'

    def __init__(self) -> None:
        self.real_provider = MultiSearchProvider()
        self.demo_provider = DemoSearchProvider()

    def collect(self, seeds: dict) -> list[dict]:
        keywords = [k for k in seeds.get('keywords', []) if k]
        if any(k.strip().lower() in {'демо', 'demo'} for k in keywords):
            return self.demo_provider.fetch('demo')

        rows = []
        for keyword in keywords:
            rows.extend(self.real_provider.fetch(keyword))
        return rows
