from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine

configure_logging()
settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(router, prefix='/api')


@app.on_event('startup')
def startup() -> None:
    Base.metadata.create_all(bind=engine)
