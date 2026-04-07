from abc import ABC, abstractmethod


class FallbackProvider(ABC):
    @abstractmethod
    def fetch(self, query: str) -> list[dict]:
        raise NotImplementedError


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
