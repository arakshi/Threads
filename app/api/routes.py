from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.analytics.metrics import keyword_trend, top_posts_window
from app.db.session import get_db
from app.schemas.common import Message
from app.schemas.entities import AccountCreate, PostOut, TopicCreate
from app.services.exports import export_csv_bytes, export_json_bytes, export_xlsx_bytes
from app.services.pipeline import IngestionPipeline
from app.services.repositories import AccountRepo, JobRepo, PostRepo, TopicRepo

router = APIRouter()


@router.get('/health', response_model=Message)
def health() -> Message:
    return Message(message='ok')


@router.post('/accounts', response_model=Message)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    try:
        AccountRepo(db).create(payload.handle, payload.display_name, payload.profile_url)
        return Message(message='account added')
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/accounts')
def list_accounts(db: Session = Depends(get_db)):
    return [a.handle for a in AccountRepo(db).list()]


@router.post('/topics', response_model=Message)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)):
    try:
        TopicRepo(db).create(payload.name, payload.keywords)
        return Message(message='topic added')
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/topics')
def list_topics(db: Session = Depends(get_db)):
    return [{'name': t.name, 'keywords': t.keywords_csv.split(',') if t.keywords_csv else []} for t in TopicRepo(db).list()]


@router.post('/collect', response_model=dict)
def collect(seeds: dict, db: Session = Depends(get_db)):
    jobs = JobRepo(db)
    run = jobs.start('collect', details=str(seeds))
    try:
        result = IngestionPipeline(db).run(seeds)
        jobs.finish(run, status='success', details=str(result))
        return result
    except Exception as exc:
        jobs.finish(run, status='failed', details=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get('/posts', response_model=list[PostOut])
def list_posts(db: Session = Depends(get_db)):
    return PostRepo(db).list_top(200)


@router.get('/analytics/dashboard')
def dashboard(db: Session = Depends(get_db)):
    return {
        'top_24h': [p.id for p in top_posts_window(db, 1, 10)],
        'top_7d': [p.id for p in top_posts_window(db, 7, 10)],
        'top_30d': [p.id for p in top_posts_window(db, 30, 10)],
        'trend_marketing': keyword_trend(db, 'marketing', 30),
    }


@router.get('/jobs')
def jobs(db: Session = Depends(get_db)):
    return [
        {'job_name': j.job_name, 'status': j.status, 'details': j.details, 'started_at': j.started_at, 'finished_at': j.finished_at}
        for j in JobRepo(db).list_recent()
    ]


@router.get('/export/{fmt}')
def export(fmt: str, db: Session = Depends(get_db)):
    if fmt == 'csv':
        return Response(content=export_csv_bytes(db), media_type='text/csv')
    if fmt == 'xlsx':
        return Response(content=export_xlsx_bytes(db), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    if fmt == 'json':
        return Response(content=export_json_bytes(db), media_type='application/json')
    raise HTTPException(status_code=404, detail='unsupported format')
