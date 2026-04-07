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
        return _redirect_with_message('Введите имя аккаунта.')
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
def collect_ui(urls: str = '', keywords: str = 'продажи,маркетинг,бизнес') -> RedirectResponse:
    post_urls = [u.strip() for u in urls.splitlines() if u.strip()]
    kw_list = [k.strip() for k in keywords.split(',') if k.strip()]
    db = SessionLocal()
    jobs = JobRepo(db)
    accounts = [a.handle for a in AccountRepo(db).list()]
    if not post_urls and not accounts and not kw_list:
        return _redirect_with_message('Добавьте хотя бы аккаунт, тему/ключ или ссылку на пост.')
    run = jobs.start('collect_ui', details=f'urls={post_urls}; keywords={kw_list}; accounts={accounts}')
    try:
        result = IngestionPipeline(db).run({'post_urls': post_urls, 'keywords': kw_list, 'accounts': accounts})
        jobs.finish(run, status='success', details=str(result))
        return _redirect_with_message(f"Сбор завершён: найдено {result.get('collected', 0)}, добавлено {result.get('inserted', 0)}")
    except Exception as exc:
        jobs.finish(run, status='failed', details=str(exc))
        return _redirect_with_message(f'Ошибка сбора: {exc}')
    finally:
        db.close()


@app.get('/app', include_in_schema=False, response_class=HTMLResponse)
def local_ui(msg: str = '', show_guide: int = 0, q: str = '', min_score: float = 0.0) -> str:
    db = SessionLocal()
    try:
        posts = PostRepo(db).list_top(200)
        jobs = JobRepo(db).list_recent(20)
        accounts = AccountRepo(db).list()
        topics = TopicRepo(db).list()
        top24 = top_posts_window(db, 1, 10)
        top7 = top_posts_window(db, 7, 10)
        trend_marketing = keyword_trend(db, 'маркетинг', 30)
    finally:
        db.close()

    q_norm = q.strip().lower()
    filtered = []
    for p in posts:
        text = (p.text or '').lower()
        if q_norm and q_norm not in text:
            continue
        if (p.viral_score or 0) < min_score:
            continue
        filtered.append(p)

    avg_score = round(sum((p.viral_score or 0) for p in filtered) / len(filtered), 2) if filtered else 0
    sum_likes = sum((p.likes or 0) for p in filtered)

    msg_html = f"<div class='notice'>{escape(msg)}</div>" if msg else ''
    guide_html = """
    <div class='guide'>
      <h3>Короткий гайд</h3>
      <ol>
        <li>Шаг 1: добавьте 1-3 аккаунта в блоке «Добавить аккаунт».</li>
        <li>Шаг 2: добавьте тему и ключи через запятую.</li>
        <li>Шаг 3: нажмите «Запустить сбор» (ссылки можно оставить пустыми).</li>
        <li>Шаг 4: примените фильтры и смотрите «Собранные посты».</li>
      </ol>
    </div>
    """ if show_guide else ''

    posts_rows = ''.join(
        f"<tr><td><a href='{escape(p.post_url)}' target='_blank'>открыть</a></td><td>{escape((p.text or '')[:180])}</td><td>{p.likes or 0}</td><td>{p.replies or 0}</td><td>{p.reposts or 0}</td><td>{round(p.viral_score or 0, 2)}</td></tr>"
        for p in filtered
    ) or "<tr><td colspan='6'>Постов по фильтрам не найдено</td></tr>"

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
      <title>Охотник за вирусными тредами</title>
      <style>
        body {{ margin:0; font-family: Inter, Arial, sans-serif; background:#0f0f10; color:#f5f5f5; }}
        .wrap {{ max-width:1180px; margin:0 auto; padding:24px; }}
        .head {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }}
        .logo {{ font-size:34px; font-weight:800; }}
        .btn {{ border-radius:999px; border:1px solid #333; padding:10px 16px; background:#1a1a1b; color:#fff; cursor:pointer; font-weight:700; }}
        .btn.main {{ background:#fff; color:#111; border-color:#fff; }}
        .notice {{ padding:12px; border-radius:10px; background:#1b1b1d; margin-bottom:12px; border:1px solid #333; }}
        .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
        .card {{ border:1px solid #2a2a2d; border-radius:16px; padding:16px; margin-bottom:12px; background:#151517; }}
        h2 {{ margin:0 0 10px 0; font-size:22px; }}
        input, textarea {{ width:100%; margin-top:8px; padding:10px; border-radius:10px; border:1px solid #333; background:#0f0f10; color:#fff; }}
        .kpi {{ display:grid; grid-template-columns:repeat(6,1fr); gap:10px; }}
        .pill {{ border:1px solid #2a2a2d; border-radius:14px; padding:12px; background:#101012; }}
        table {{ width:100%; border-collapse:collapse; }}
        th,td {{ border-bottom:1px solid #2b2b2d; text-align:left; padding:8px; font-size:14px; }}
        .tag {{ display:inline-block; background:#242428; border-radius:999px; padding:6px 10px; margin:4px 6px 0 0; font-size:13px; }}
        .muted {{ color:#a1a1aa; }}
        .guide {{ border:1px dashed #3f3f46; background:#111; border-radius:12px; padding:12px; margin-bottom:12px; }}
      </style>
    </head>
    <body>
      <div class='wrap'>
        <div class='head'>
          <div class='logo'>Охотник за вирусными тредами</div>
          <div>
            <a href='/app?show_guide=1'><button class='btn'>Гайд</button></a>
            <a href='/app'><button class='btn'>Обновить</button></a>
          </div>
        </div>
        {msg_html}
        {guide_html}

        <div class='card'>
          <h2>Что нажимать, чтобы всё работало</h2>
          <ol>
            <li>Нажмите «Сохранить аккаунт» минимум 1 раз.</li>
            <li>Нажмите «Сохранить тему».</li>
            <li>Нажмите «Запустить сбор».</li>
            <li>Прокрутите к таблице «Собранные посты».</li>
          </ol>
        </div>

        <div class='kpi card'>
          <div class='pill'>Постов всего<br><b>{len(posts)}</b></div>
          <div class='pill'>Постов по фильтру<br><b>{len(filtered)}</b></div>
          <div class='pill'>Средняя вирусность<br><b>{avg_score}</b></div>
          <div class='pill'>Сумма лайков<br><b>{sum_likes}</b></div>
          <div class='pill'>Топ за 24 часа<br><b>{len(top24)}</b></div>
          <div class='pill'>Топ за 7 дней<br><b>{len(top7)}</b></div>
        </div>

        <div class='grid'>
          <div class='card'>
            <h2>Добавить аккаунт</h2>
            <form action='/app/add_account' method='get'>
              <input name='handle' placeholder='например: stepa_sales'>
              <button class='btn main' type='submit'>Сохранить аккаунт</button>
            </form>
            <div class='muted' style='margin-top:8px'>Аккаунты: {accounts_html}</div>
          </div>
          <div class='card'>
            <h2>Добавить тему</h2>
            <form action='/app/add_topic' method='get'>
              <input name='name' placeholder='например: маркетинг'>
              <input name='keywords' value='маркетинг,лиды,контент' placeholder='ключи через запятую'>
              <button class='btn main' type='submit'>Сохранить тему</button>
            </form>
            <div class='muted' style='margin-top:8px'>Темы: {topics_html}</div>
          </div>
        </div>

        <div class='card'>
          <h2>Запустить сбор</h2>
          <form action='/app/collect' method='get'>
            <textarea name='urls' rows='3' placeholder='Вставьте реальные ссылки на посты (каждая с новой строки). Можно оставить пустым.'></textarea>
            <input name='keywords' value='продажи,маркетинг,бизнес' placeholder='ключевые слова через запятую'>
            <button class='btn main' type='submit'>Запустить сбор</button>
          </form>
          <div class='muted' style='margin-top:8px'>Необязательно вставлять ссылки: если есть аккаунты/ключи, сбор всё равно выполнится.</div>
          <a href='/app/collect?urls=demo://sample&keywords=демо' style='display:inline-block;margin-top:8px'>Запустить тестовый пример</a>
        </div>

        <div class='card'>
          <h2>Фильтры просмотра</h2>
          <form action='/app' method='get'>
            <input name='q' value='{escape(q)}' placeholder='поиск по тексту поста'>
            <input name='min_score' type='number' step='0.1' value='{min_score}' placeholder='минимальная вирусность'>
            <button class='btn main' type='submit'>Применить фильтры</button>
          </form>
          <div class='muted' style='margin-top:8px'>Тренд «маркетинг» за 30 дней: <b>{trend_marketing}</b></div>
        </div>

        <div class='card'>
          <h2>Собранные посты</h2>
          <table>
            <tr><th>Ссылка</th><th>Текст</th><th>Лайки</th><th>Ответы</th><th>Репосты</th><th>Вирусность</th></tr>
            {posts_rows}
          </table>
        </div>

        <div class='card'>
          <h2>Журнал задач</h2>
          <table>
            <tr><th>Задача</th><th>Статус</th><th>Детали</th></tr>
            {jobs_rows}
          </table>
        </div>
      </div>
    </body></html>
    """


if __name__ == '__main__':
    uvicorn.run('app.main:app', host=settings.api_host, port=settings.api_port, reload=True)
