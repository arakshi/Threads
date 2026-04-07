from contextlib import asynccontextmanager
from html import escape
from urllib.parse import quote_plus

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from app.analytics.metrics import keyword_trend, top_posts_window
from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.pipeline import IngestionPipeline
from app.services.repositories import AccountRepo, JobRepo, PostRepo, TopicRepo

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(router, prefix='/api')


def _redirect_with_message(message: str) -> RedirectResponse:
    return RedirectResponse(url=f"/app?msg={quote_plus(message)}", status_code=303)


@app.get('/', include_in_schema=False)
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url='/app', status_code=302)


@app.get('/app/add_account', include_in_schema=False)
def add_account_ui(handle: str = '') -> RedirectResponse:
    handle = handle.strip().lstrip('@')
    if not handle:
        return _redirect_with_message('Введите ник аккаунта.')
    db = SessionLocal()
    try:
        AccountRepo(db).create(handle=handle)
        return _redirect_with_message(f'Аккаунт @{handle} добавлен.')
    except Exception as exc:
        return _redirect_with_message(f'Ошибка добавления аккаунта: {exc}')
    finally:
        db.close()


@app.get('/app/add_topic', include_in_schema=False)
def add_topic_ui(name: str = '', keywords: str = '') -> RedirectResponse:
    name = name.strip()
    kw_list = [k.strip() for k in keywords.split(',') if k.strip()]
    if not name:
        return _redirect_with_message('Введите название темы.')
    db = SessionLocal()
    try:
        TopicRepo(db).create(name=name, keywords=kw_list)
        return _redirect_with_message(f'Тема «{name}» добавлена.')
    except Exception as exc:
        return _redirect_with_message(f'Ошибка добавления темы: {exc}')
    finally:
        db.close()


@app.get('/app/collect', include_in_schema=False)
def collect_ui(urls: str = 'demo://sample', keywords: str = 'продажи,маркетинг,saas') -> RedirectResponse:
    post_urls = [u.strip() for u in urls.splitlines() if u.strip()]
    kw_list = [k.strip() for k in keywords.split(',') if k.strip()]
    db = SessionLocal()
    jobs = JobRepo(db)
    run = jobs.start('collect_ui', details=f'urls={post_urls}; keywords={kw_list}')
    try:
        result = IngestionPipeline(db).run({'post_urls': post_urls, 'keywords': kw_list})
        jobs.finish(run, status='success', details=str(result))
        return _redirect_with_message(f"Сбор завершён: найдено {result.get('collected', 0)}, добавлено {result.get('inserted', 0)}")
    except Exception as exc:
        jobs.finish(run, status='failed', details=str(exc))
        return _redirect_with_message(f'Ошибка сбора: {exc}')
    finally:
        db.close()


@app.get('/app', include_in_schema=False, response_class=HTMLResponse)
def local_ui(msg: str = '', show_guide: int = 0) -> str:
    db = SessionLocal()
    try:
        posts = PostRepo(db).list_top(30)
        jobs = JobRepo(db).list_recent(15)
        accounts = AccountRepo(db).list()
        topics = TopicRepo(db).list()
        top24 = top_posts_window(db, 1, 5)
        top7 = top_posts_window(db, 7, 5)
        trend_marketing = keyword_trend(db, 'marketing', 30)
    finally:
        db.close()

    msg_html = f"<div class='notice'>{escape(msg)}</div>" if msg else ''
    guide_html = """
    <div class='guide'>
      <h3>Как пользоваться</h3>
      <ol>
        <li>Добавьте аккаунт (слева).</li>
        <li>Добавьте тему и ключи (справа).</li>
        <li>В блоке «Запустить парсинг» оставьте demo://sample для теста.</li>
        <li>Нажмите «Запустить сбор».</li>
        <li>Ниже появятся посты, тренды и логи.</li>
      </ol>
    </div>
    """ if show_guide else ''

    posts_rows = ''.join(
        f"<tr><td><a href='{escape(p.post_url)}' target='_blank'>ссылка</a></td><td>{escape((p.text or '')[:180])}</td><td>{p.likes or ''}</td><td>{p.viral_score or ''}</td></tr>"
        for p in posts
    ) or "<tr><td colspan='4'>Пока нет данных</td></tr>"

    jobs_rows = ''.join(
        f"<tr><td>{escape(j.job_name)}</td><td>{escape(j.status)}</td><td>{escape((j.details or '')[:120])}</td></tr>"
        for j in jobs
    ) or "<tr><td colspan='3'>Нет запусков</td></tr>"

    accounts_html = ''.join(f"<span class='tag'>@{escape(a.handle)}</span>" for a in accounts) or '<span class="muted">нет</span>'
    topics_html = ''.join(f"<span class='tag'>{escape(t.name)}</span>" for t in topics) or '<span class="muted">нет</span>'

    return f"""
    <html lang='ru'>
    <head>
      <meta charset='utf-8'/>
      <meta name='viewport' content='width=device-width, initial-scale=1'/>
      <title>Охотник за вирусными Threads</title>
      <style>
        body {{ margin:0; font-family: Inter, Arial, sans-serif; background:#fff; color:#111; }}
        .wrap {{ max-width:1100px; margin:0 auto; padding:24px; }}
        .head {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }}
        .logo {{ font-size:36px; font-weight:800; letter-spacing:-1px; }}
        .btn {{ border-radius:999px; border:1px solid #ddd; padding:10px 16px; background:#fff; cursor:pointer; font-weight:600; }}
        .btn.primary {{ background:#111; color:#fff; border-color:#111; }}
        .notice {{ padding:12px; border-radius:10px; background:#f3f4f6; margin-bottom:12px; }}
        .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
        .card {{ border:1px solid #e5e7eb; border-radius:16px; padding:16px; margin-bottom:12px; background:#fff; }}
        h2 {{ margin:0 0 10px 0; font-size:22px; }}
        input, textarea {{ width:100%; margin-top:8px; padding:10px; border-radius:10px; border:1px solid #d1d5db; }}
        .kpi {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }}
        .pill {{ border:1px solid #e5e7eb; border-radius:14px; padding:12px; background:#fafafa; }}
        table {{ width:100%; border-collapse:collapse; }}
        th,td {{ border-bottom:1px solid #eee; text-align:left; padding:8px; font-size:14px; }}
        .tag {{ display:inline-block; background:#f3f4f6; border-radius:999px; padding:6px 10px; margin:4px 6px 0 0; font-size:13px; }}
        .muted {{ color:#6b7280; }}
        .guide {{ border:1px dashed #cbd5e1; background:#f8fafc; border-radius:12px; padding:12px; margin-bottom:12px; }}
      </style>
    </head>
    <body>
      <div class='wrap'>
        <div class='head'>
          <div class='logo'>Охотник за вирусными Threads</div>
          <div>
            <a href='/app?show_guide=1'><button class='btn'>📘 Гайд</button></a>
            <a href='/app'><button class='btn'>↻ Обновить</button></a>
          </div>
        </div>
        {msg_html}
        {guide_html}

        <div class='kpi card'>
          <div class='pill'>Постов в базе<br><b>{len(posts)}</b></div>
          <div class='pill'>Trend marketing (30д)<br><b>{trend_marketing}</b></div>
          <div class='pill'>Топ 24ч<br><b>{len(top24)}</b></div>
          <div class='pill'>Топ 7д<br><b>{len(top7)}</b></div>
        </div>

        <div class='grid'>
          <div class='card'>
            <h2>Добавить аккаунт</h2>
            <form action='/app/add_account' method='get'>
              <input name='handle' placeholder='например: stepa_sales'>
              <button class='btn primary' type='submit'>Сохранить аккаунт</button>
            </form>
            <div class='muted' style='margin-top:8px'>Watchlist: {accounts_html}</div>
          </div>
          <div class='card'>
            <h2>Добавить тему</h2>
            <form action='/app/add_topic' method='get'>
              <input name='name' placeholder='например: маркетинг'>
              <input name='keywords' value='маркетинг,лиды,контент' placeholder='ключи через запятую'>
              <button class='btn primary' type='submit'>Сохранить тему</button>
            </form>
            <div class='muted' style='margin-top:8px'>Темы: {topics_html}</div>
          </div>
        </div>

        <div class='card'>
          <h2>Запустить парсинг (public-only)</h2>
          <form action='/app/collect' method='get'>
            <textarea name='urls' rows='3'>demo://sample</textarea>
            <input name='keywords' value='продажи,маркетинг,saas'>
            <button class='btn primary' type='submit'>🚀 Запустить сбор</button>
          </form>
        </div>

        <div class='card'>
          <h2>Посты</h2>
          <table>
            <tr><th>URL</th><th>Текст</th><th>Лайки</th><th>Viral</th></tr>
            {posts_rows}
          </table>
        </div>

        <div class='card'>
          <h2>Задачи и логи</h2>
          <table>
            <tr><th>Job</th><th>Статус</th><th>Детали</th></tr>
            {jobs_rows}
          </table>
        </div>
      </div>
    </body></html>
    """


if __name__ == '__main__':
    uvicorn.run('app.main:app', host=settings.api_host, port=settings.api_port, reload=True)
