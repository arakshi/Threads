import random

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings


class HttpClientFactory:
    def __init__(self) -> None:
        self.settings = get_settings()

    def build_headers(self) -> dict[str, str]:
        ua = random.choice(self.settings.user_agents)
        return {'User-Agent': ua, 'Accept-Language': 'en-US,en;q=0.9'}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def get(self, url: str) -> httpx.Response:
        with httpx.Client(timeout=self.settings.request_timeout_seconds, headers=self.build_headers(), follow_redirects=True) as client:
            return client.get(url)
