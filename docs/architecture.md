# Architecture

- **Main mode**: `collectors/public_web` + `collectors/fallback_sources` без логина.
- **Optional mode**: `collectors/official_api`, выключен `ENABLE_OFFICIAL_API=false`.
- **Backend**: FastAPI API + service layer.
- **Storage**: SQLAlchemy models, Alembic migration, default SQLite.
- **Background jobs**: APScheduler (`scripts/run_scheduler.py`).
- **Analytics**: viral score, clustering, hooks, CTA, format/tone tagging.
- **UI**: Streamlit with sections Dashboard/Posts/Idea Lab/Jobs/Settings-ish controls in sidebar.
