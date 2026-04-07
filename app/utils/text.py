import hashlib
import re


def normalize_text(text: str | None) -> str:
    if not text:
        return ''
    return re.sub(r'\s+', ' ', text).strip().lower()


def dedup_hash(text: str | None) -> str:
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
