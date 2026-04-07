from collections.abc import Sequence

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import Account, JobRun, Post, Topic


class AccountRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, handle: str, display_name: str | None = None, profile_url: str | None = None) -> Account:
        account = Account(handle=handle.strip('@'), display_name=display_name, profile_url=profile_url)
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def list(self) -> Sequence[Account]:
        return self.db.scalars(select(Account).order_by(Account.created_at.desc())).all()


class TopicRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, keywords: list[str]) -> Topic:
        topic = Topic(name=name, keywords_csv=','.join(keywords))
        self.db.add(topic)
        self.db.commit()
        self.db.refresh(topic)
        return topic

    def list(self) -> Sequence[Topic]:
        return self.db.scalars(select(Topic).order_by(Topic.created_at.desc())).all()


class PostRepo:
    def __init__(self, db: Session):
        self.db = db

    def upsert_bulk(self, posts: list[dict]) -> int:
        inserted = 0
        for payload in posts:
            exists = self.db.scalar(select(Post).where(Post.external_id == payload['external_id']))
            if exists:
                continue
            self.db.add(Post(**payload))
            inserted += 1
        self.db.commit()
        return inserted

    def list_top(self, limit: int = 100) -> Sequence[Post]:
        return self.db.scalars(select(Post).order_by(desc(Post.viral_score), desc(Post.collected_at)).limit(limit)).all()

    def list_all(self) -> Sequence[Post]:
        return self.db.scalars(select(Post).order_by(Post.collected_at.desc())).all()


class JobRepo:
    def __init__(self, db: Session):
        self.db = db

    def start(self, job_name: str, details: str = '') -> JobRun:
        jr = JobRun(job_name=job_name, status='running', details=details)
        self.db.add(jr)
        self.db.commit()
        self.db.refresh(jr)
        return jr

    def finish(self, run: JobRun, status: str, details: str = '') -> JobRun:
        from datetime import datetime, timezone

        run.status = status
        run.details = details
        run.finished_at = datetime.now(timezone.utc)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def list_recent(self, limit: int = 50) -> Sequence[JobRun]:
        return self.db.scalars(select(JobRun).order_by(JobRun.started_at.desc()).limit(limit)).all()
