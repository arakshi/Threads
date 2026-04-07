from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(router, prefix='/api')


@app.get('/', include_in_schema=False, response_class=HTMLResponse)
def root_page() -> str:
    return f"""
    <html lang='ru'><head><meta charset='utf-8'><title>{settings.app_name}</title>
    <style>
      body {{font-family: Arial, sans-serif; background:#0b1020; color:#e6edf3; padding:30px;}}
      a {{color:#7dd3fc; font-weight:600;}}
      .card {{background:#111a2e; border:1px solid #253656; border-radius:12px; padding:20px; max-width:760px;}}
    </style></head><body>
      <div class='card'>
        <h1>🧵 Threads Viral Hunter</h1>
        <p>Сервер API запущен. Для удобной работы используйте русскоязычный интерфейс Streamlit.</p>
        <ul>
          <li>UI: <a href='http://{settings.api_host}:{settings.ui_port}' target='_blank'>http://{settings.api_host}:{settings.ui_port}</a></li>
          <li>API docs: <a href='/docs' target='_blank'>/docs</a></li>
          <li>Health: <a href='/api/health' target='_blank'>/api/health</a></li>
        </ul>
      </div>
    </body></html>
    """


if __name__ == '__main__':
    uvicorn.run('app.main:app', host=settings.api_host, port=settings.api_port, reload=True)
