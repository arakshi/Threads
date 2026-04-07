from datetime import datetime

from pydantic import BaseModel


class Message(BaseModel):
    message: str


class JobStatus(BaseModel):
    id: int
    job_name: str
    status: str
    details: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
