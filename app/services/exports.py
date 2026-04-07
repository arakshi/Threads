import io
import json

import pandas as pd
from sqlalchemy.orm import Session

from app.models.post import Post


def _posts_df(db: Session) -> pd.DataFrame:
    rows = db.query(Post).all()
    return pd.DataFrame(
        [
            {
                'id': p.id,
                'url': p.post_url,
                'text': p.text,
                'viral_score': p.viral_score,
                'likes': p.likes,
                'replies': p.replies,
                'reposts': p.reposts,
                'format': p.format_type,
                'hook': p.hook,
                'cta': p.cta,
            }
            for p in rows
        ]
    )


def export_csv_bytes(db: Session) -> bytes:
    return _posts_df(db).to_csv(index=False).encode('utf-8')


def export_xlsx_bytes(db: Session) -> bytes:
    buf = io.BytesIO()
    _posts_df(db).to_excel(buf, index=False)
    return buf.getvalue()


def export_json_bytes(db: Session) -> bytes:
    return json.dumps(_posts_df(db).to_dict(orient='records'), ensure_ascii=False, indent=2).encode('utf-8')
