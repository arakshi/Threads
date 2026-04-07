from datetime import datetime

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    handle: str
    display_name: str | None = None
    profile_url: str | None = None


class TopicCreate(BaseModel):
    name: str
    keywords: list[str] = Field(default_factory=list)


class PostOut(BaseModel):
    id: int
    external_id: str
    source: str
    post_url: str
    text: str | None
    likes: int | None
    replies: int | None
    reposts: int | None
    quotes: int | None
    has_media: bool
    viral_score: float | None
    format_type: str | None
    hook: str | None
    cta: str | None
    collected_at: datetime

    class Config:
        from_attributes = True
