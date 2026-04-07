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
        .btn-row { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
        .grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
        .small { color:#94a3b8; font-size:13px; }
        .ok { color:#86efac; }
        .err { color:#fca5a5; }
        table { width:100%; border-collapse:collapse; }
        th,td { border-bottom:1px solid #233452; padding:8px; text-align:left; font-size:13px; }
        .kpi { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:10px 0 14px; }
        .pill { background:#0f162a; border:1px solid #30456e; border-radius:8px; padding:10px; }
        #guide { display:none; position:fixed; inset:0; background:rgba(0,0,0,.55); }
        #guide .modal { max-width:760px; margin:6% auto; background:#111a2f; border:1px solid #30456e; border-radius:12px; padding:16px; }
      </style>
    </head>
    <body>
      <div class='wrap'>
        <h1>🧵 Threads Viral Hunter</h1>
        <div class='btn-row'>
          <button type='button' onclick='openGuide()'>📘 Как пользоваться (гайд)</button>
          <button type='button' onclick='refreshAll()'>🔄 Обновить всё</button>
        </div>
        <div id='status' class='small' style='margin:8px 0 12px;'></div>

        <div class='kpi'>
          <div class='pill'>Постов: <b id='kpi_posts'>0</b></div>
          <div class='pill'>Тренд marketing (30д): <b id='kpi_trend'>0</b></div>
          <div class='pill'>Топ 24ч: <b id='kpi_24h'>0</b></div>
          <div class='pill'>Топ 7д: <b id='kpi_7d'>0</b></div>
        </div>

        <div class='grid'>
          <div class='card'>
            <h2>Добавить аккаунт</h2>
            <input id='acc' placeholder='например: stepa_sales'/>
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
          <h2>Запустить парсинг/сбор</h2>
          <textarea id='urls' rows='3'>demo://sample</textarea>
          <input id='kw' value='продажи,маркетинг,saas'/>
          <button type='button' onclick='runCollect()'>🚀 Запустить сбор</button>
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

      <div id='guide'>
        <div class='modal'>
          <h2>📘 Короткий гайд (1 минута)</h2>
          <ol>
            <li>Введите аккаунт и нажмите «Сохранить аккаунт».</li>
            <li>Введите тему и ключи, нажмите «Сохранить тему».</li>
            <li>В блоке «Запустить парсинг/сбор» оставьте `demo://sample` для первого теста.</li>
            <li>Нажмите «Запустить сбор» и дождитесь статуса ✅.</li>
            <li>Нажмите «Обновить список» в блоке «Посты».</li>
          </ol>
          <button type='button' onclick='closeGuide()'>Закрыть</button>
        </div>
      </div>

      <script>
      function setStatus(msg, ok){
        var el = document.getElementById('status');
        el.className = ok ? 'small ok' : 'small err';
        el.innerText = msg;
      }
      function openGuide(){ document.getElementById('guide').style.display='block'; }
      function closeGuide(){ document.getElementById('guide').style.display='none'; }

      function parseJsonSafe(text){
        try { return JSON.parse(text); } catch (e) { return null; }
      }

      function requestJson(url, options){
        options = options || {};
        return fetch(url, options).then(function(r){
          return r.text().then(function(t){
            var data = parseJsonSafe(t);
            if(!r.ok){
              var detail = data && data.detail ? data.detail : ('HTTP ' + r.status);
              throw new Error(detail);
            }
            return data;
          });
        });
      }

      function addAccount(){
        var handle = document.getElementById('acc').value.trim();
        if(!handle){ setStatus('Введите ник аккаунта', false); return; }
        requestJson('/api/accounts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({handle:handle})})
          .then(function(){ setStatus('✅ Аккаунт добавлен', true); })
          .catch(function(e){ setStatus('❌ Ошибка: '+e.message, false); });
      }

      function addTopic(){
        var name = document.getElementById('topic').value.trim();
        var keywords = document.getElementById('keywords').value.split(',').map(function(x){return x.trim();}).filter(Boolean);
        if(!name){ setStatus('Введите название темы', false); return; }
        requestJson('/api/topics',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name,keywords:keywords})})
          .then(function(){ setStatus('✅ Тема добавлена', true); })
          .catch(function(e){ setStatus('❌ Ошибка: '+e.message, false); });
      }

      function runCollect(){
        var post_urls = document.getElementById('urls').value.split('\n').map(function(x){return x.trim();}).filter(Boolean);
        var keywords = document.getElementById('kw').value.split(',').map(function(x){return x.trim();}).filter(Boolean);
        setStatus('⏳ Идёт сбор...', true);
        requestJson('/api/collect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({post_urls:post_urls,keywords:keywords})})
          .then(function(j){
            setStatus('✅ Сбор завершён: найдено ' + (j && j.collected ? j.collected : 0) + ', добавлено ' + (j && j.inserted ? j.inserted : 0), true);
            refreshAll();
          })
          .catch(function(e){ setStatus('❌ Ошибка: '+e.message, false); });
      }

      function loadPosts(){
        requestJson('/api/posts').then(function(rows){
          rows = rows || [];
          document.getElementById('kpi_posts').innerText = String(rows.length);
          var head = '<table><tr><th>URL</th><th>Текст</th><th>Лайки</th><th>Viral</th></tr>';
          var body = rows.slice(0,50).map(function(p){
            var text = (p.text || '').slice(0,140);
            return '<tr><td><a href="'+p.post_url+'" target="_blank">ссылка</a></td><td>'+text+'</td><td>'+(p.likes || '')+'</td><td>'+(p.viral_score || '')+'</td></tr>';
          }).join('');
          document.getElementById('posts').innerHTML = head + body + '</table>';
        }).catch(function(e){ setStatus('❌ Не удалось загрузить посты: '+e.message, false); });
      }

      function loadJobs(){
        requestJson('/api/jobs').then(function(rows){
          rows = rows || [];
          var head = '<table><tr><th>Job</th><th>Статус</th><th>Детали</th></tr>';
          var body = rows.slice(0,30).map(function(j){
            return '<tr><td>'+j.job_name+'</td><td>'+j.status+'</td><td>'+(j.details || '')+'</td></tr>';
          }).join('');
          document.getElementById('jobs').innerHTML = head + body + '</table>';
        }).catch(function(e){ setStatus('❌ Не удалось загрузить логи: '+e.message, false); });
      }

      function loadDashboard(){
        requestJson('/api/analytics/dashboard').then(function(d){
          d = d || {};
          document.getElementById('kpi_trend').innerText = String(d.trend_marketing || 0);
          document.getElementById('kpi_24h').innerText = String((d.top_24h || []).length);
          document.getElementById('kpi_7d').innerText = String((d.top_7d || []).length);
        }).catch(function(e){ setStatus('❌ Не удалось загрузить тренды: '+e.message, false); });
      }

      function refreshAll(){
        loadPosts();
        loadJobs();
        loadDashboard();
      }

      refreshAll();
      </script>
    </body>
    </html>
    """


if __name__ == '__main__':
    uvicorn.run('app.main:app', host=settings.api_host, port=settings.api_port, reload=True)
