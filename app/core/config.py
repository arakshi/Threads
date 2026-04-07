from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=False)

    app_name: str = Field(default='Охотник за вирусными Threads', alias='APP_NAME')
    app_env: str = Field(default='dev', alias='APP_ENV')
    api_host: str = Field(default='127.0.0.1', alias='API_HOST')
    api_port: int = Field(default=8000, alias='API_PORT')
    ui_port: int = Field(default=8501, alias='UI_PORT')
    database_url: str = Field(default='sqlite:///./threads_viral.db', alias='DATABASE_URL')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')
    enable_official_api: bool = Field(default=False, alias='ENABLE_OFFICIAL_API')
    threads_official_access_token: str = Field(default='', alias='THREADS_OFFICIAL_ACCESS_TOKEN')
    threads_official_user_id: str = Field(default='', alias='THREADS_OFFICIAL_USER_ID')
    request_timeout_seconds: int = Field(default=20, alias='REQUEST_TIMEOUT_SECONDS')
    user_agent_pool: str = Field(default='Mozilla/5.0', alias='USER_AGENT_POOL')
    scheduler_interval_minutes: int = Field(default=30, alias='SCHEDULER_INTERVAL_MINUTES')
    demo_mode: bool = Field(default=True, alias='DEMO_MODE')

    @property
    def user_agents(self) -> List[str]:
        return [ua.strip() for ua in self.user_agent_pool.split('|') if ua.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
