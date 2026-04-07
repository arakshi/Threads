from loguru import logger

from app.db.session import SessionLocal
from app.services.pipeline import IngestionPipeline


def scheduled_collect() -> None:
    db = SessionLocal()
    try:
        seeds = {
            'post_urls': ['demo://sample'],
            'keywords': ['marketing', 'saas'],
        }
        result = IngestionPipeline(db).run(seeds)
        logger.info(f'scheduled collect: {result}')
    finally:
        db.close()
