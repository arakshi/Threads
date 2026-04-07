from app.collectors.base import BaseCollector
from app.core.config import get_settings


class OfficialApiCollector(BaseCollector):
    name = 'official_api'

    def __init__(self) -> None:
        self.settings = get_settings()

    def collect(self, seeds: dict) -> list[dict]:
        if not self.settings.enable_official_api:
            return []
        if not self.settings.threads_official_access_token:
            return []
        return []
