from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

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


@app.get('/', include_in_schema=False)
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url='/app')


@app.get('/app', include_in_schema=False, response_class=HTMLResponse)
def local_ui() -> str:
    return """
    <html lang='ru'>
    <head>
      <meta charset='utf-8'/>
      <meta name='viewport' content='width=device-width, initial-scale=1'/>
      <title>Threads Viral Hunter — Локальный интерфейс</title>
      <style>
        body { background:#0b1020; color:#e5e7eb; font-family:Segoe UI,Arial,sans-serif; margin:0; }
        .wrap { max-width:1100px; margin:0 auto; padding:20px; }
        .card { background:#121a2f; border:1px solid #24365a; border-radius:12px; padding:16px; margin-bottom:14px; }
        h1,h2 { margin:0 0 12px 0; }
        input, textarea, button { width:100%; padding:10px; border-radius:8px; border:1px solid #30456e; background:#0f162a; color:#fff; margin-top:8px; }
        button { background:#2563eb; border:none; font-weight:700; cursor:pointer; }
        button:disabled { opacity: .6; cursor: wait; }
        .grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
        .small { color:#94a3b8; font-size:13px; }
        .ok { color:#86efac; }
        .err { color:#fca5a5; }
        table { width:100%; border-collapse:collapse; }
        th,td { border-bottom:1px solid #233452; padding:8px; text-align:left; font-size:13px; }
      </style>
    </head>
    <body>
      <div class='wrap'>
        <h1>🧵 Threads Viral Hunter</h1>
        <div class='small'>Если кнопка не сработала — внизу появится текст ошибки.</div>

        <div class='grid'>
          <div class='card'>
            <h2>Добавить аккаунт</h2>
            <input id='acc' placeholder='например: my_handle'/>
            <button type='button' onclick='addAccount()'>Сохранить аккаунт</button>
          </div>
          <div class='card'>
            <h2>Добавить тему</h2>
            <input id='topic' placeholder='например: продажи'/>
            <input id='keywords' value='маркетинг,лиды,контент' placeholder='ключи через запятую'/>
            <button type='button' onclick='addTopic()'>Сохранить тему</button>
          </div>
        </div>

        <div class='card'>
          <h2>Запустить сбор</h2>
          <textarea id='urls' rows='3'>demo://sample</textarea>
          <input id='kw' value='продажи,маркетинг,saas'/>
          <button type='button' onclick='runCollect()'>🚀 Запустить сбор</button>
          <div id='status' class='small' style='margin-top:8px;'></div>
        </div>

        <div class='card'>
          <h2>Посты</h2>
          <button type='button' onclick='loadPosts()'>Обновить список</button>
          <div id='posts'></div>
        </div>

        <div class='card'>
          <h2>Задачи и логи</h2>
          <button type='button' onclick='loadJobs()'>Обновить логи</button>
          <div id='jobs'></div>
        </div>
      </div>

      <script>
      function setStatus(msg, ok=true){
        const el = document.getElementById('status');
        el.className = ok ? 'small ok' : 'small err';
        el.innerText = msg;
      }
      async function requestJson(url, options={}){
        const r = await fetch(url, options);
        let data = null;
        try { data = await r.json(); } catch (_) { data = null; }
        if(!r.ok){
          throw new Error(data?.detail || `HTTP ${r.status}`);
        }
        return data;
      }
      async function addAccount(){
        const handle = document.getElementById('acc').value.trim();
        if(!handle){ setStatus('Введите ник аккаунта', false); return; }
        try {
          await requestJson('/api/accounts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({handle})});
          setStatus('✅ Аккаунт добавлен');
        } catch(e){ setStatus('❌ Ошибка: '+e.message, false); }
      }
      async function addTopic(){
        const name=document.getElementById('topic').value.trim();
        const keywords=document.getElementById('keywords').value.split(',').map(x=>x.trim()).filter(Boolean);
        if(!name){ setStatus('Введите название темы', false); return; }
        try {
          await requestJson('/api/topics',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,keywords})});
          setStatus('✅ Тема добавлена');
        } catch(e){ setStatus('❌ Ошибка: '+e.message, false); }
      }
      async function runCollect(){
        const post_urls=document.getElementById('urls').value.split('\n').map(x=>x.trim()).filter(Boolean);
        const keywords=document.getElementById('kw').value.split(',').map(x=>x.trim()).filter(Boolean);
        try {
          setStatus('⏳ Идёт сбор данных...');
          const j=await requestJson('/api/collect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({post_urls,keywords})});
          setStatus(`✅ Сбор завершён: найдено ${j.collected ?? 0}, добавлено ${j.inserted ?? 0}`);
          loadPosts();
          loadJobs();
        } catch(e){ setStatus('❌ Ошибка: '+e.message, false); }
      }
      async function loadPosts(){
        try {
          const rows=await requestJson('/api/posts');
          const head='<table><tr><th>URL</th><th>Текст</th><th>Лайки</th><th>Viral</th></tr>';
          const body=rows.slice(0,50).map(p=>`<tr><td><a href="${p.post_url}" target="_blank">ссылка</a></td><td>${(p.text||'').slice(0,140)}</td><td>${p.likes??''}</td><td>${p.viral_score??''}</td></tr>`).join('');
          document.getElementById('posts').innerHTML=head+body+'</table>';
        } catch(e){ setStatus('❌ Не удалось загрузить посты: '+e.message, false); }
      }
      async function loadJobs(){
        try {
          const rows=await requestJson('/api/jobs');
          const head='<table><tr><th>Job</th><th>Статус</th><th>Детали</th></tr>';
          const body=rows.slice(0,30).map(j=>`<tr><td>${j.job_name}</td><td>${j.status}</td><td>${j.details||''}</td></tr>`).join('');
          document.getElementById('jobs').innerHTML=head+body+'</table>';
        } catch(e){ setStatus('❌ Не удалось загрузить логи: '+e.message, false); }
      }
      loadPosts();
      loadJobs();
      </script>
    </body>
    </html>
    """


if __name__ == '__main__':
    uvicorn.run('app.main:app', host=settings.api_host, port=settings.api_port, reload=True)
