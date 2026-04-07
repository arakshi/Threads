# Threads Viral Hunter (Local MVP)

Локальный Python-софт для анализа потенциально вирусных постов в Threads с **основным режимом public-only без логина**.

## Что уже реализовано
- FastAPI backend + Streamlit UI.
- SQLAlchemy + Alembic.
- SQLite по умолчанию (PostgreSQL можно включить через `DATABASE_URL`).
- Collectors:
  - `public_web` (базовый режим, без логина)
  - `fallback_sources` (демо-адаптер, расширяемо)
  - `official_api` (интерфейс реализован, выключен флагом)
- APScheduler для фонового сбора.
- Аналитика: viral_score, hooks, CTA, format classification, sentiment/tone, clustering, near-duplicate.
- Экспорт CSV/XLSX/JSON.
- Тесты: parser, viral_score, dedup, clustering.

## Быстрый запуск (PyCharm-friendly)
1. Создайте venv Python 3.12.
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Создайте `.env`:
   ```bash
   cp .env.example .env
   ```
4. Инициализируйте БД:
   ```bash
   python scripts/init_db.py
   ```
5. Запуск backend:
   ```bash
   python scripts/run_app.py
   ```
6. Запуск UI (в отдельном процессе):
   ```bash
   python scripts/run_ui.py
   ```
7. (Опционально) scheduler:
   ```bash
   python scripts/run_scheduler.py
   ```

UI (русскоязычный): http://127.0.0.1:8501  
API docs: http://127.0.0.1:8000/docs
Корневая страница API (`/`) показывает удобную стартовую русскую страницу с ссылками.

Альтернатива для PyCharm: можно запускать напрямую `app/main.py` (теперь стартует uvicorn в `__main__`).

## Рекомендации Run Configurations в PyCharm
Создайте 3 Python run configs:
1. **Backend**: `scripts/run_app.py`
2. **UI**: `scripts/run_ui.py`
3. **Scheduler**: `scripts/run_scheduler.py`

Рабочая директория: корень проекта. Используйте один и тот же `.env`.

## Основные ограничения public-only режима
- Не все счетчики доступны на каждой публичной странице.
- Если поле недоступно, сохраняется `null`.
- Topic search напрямую в Threads-web может быть ограничен; используется fallback-провайдер.

## Seed/fixtures
- `data/seeds/watchlist.json`
- `data/fixtures/sample_thread_post.html`
- `data/fixtures/sample_api_response.json`

## Пример API вызова сбора
```bash
curl -X POST http://127.0.0.1:8000/api/collect \
  -H "Content-Type: application/json" \
  -d '{
    "post_urls": ["demo://sample"],
    "keywords": ["marketing", "saas"]
  }'
```

## Viral Score (формула)
`final = (engagement*0.5 + velocity*0.25 + novelty*0.25) * authority_adjustment * recency_decay`

Компоненты вынесены в `app/analytics/viral_score.py`.
