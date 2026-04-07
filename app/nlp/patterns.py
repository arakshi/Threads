import re
from collections import Counter

FORMATS = {
    'story': re.compile(r'\b(i|we)\b.*\bthen\b', re.IGNORECASE),
    'breakdown': re.compile(r'\b(steps|framework|how to|checklist)\b', re.IGNORECASE),
    'provocation': re.compile(r'\b(unpopular opinion|hot take|stop)\b', re.IGNORECASE),
}

CTA_PATTERNS = [r'\b(dm me|comment|follow|subscribe|book a call|link in bio)\b']


def extract_hook(text: str | None) -> str | None:
    if not text:
        return None
    return text.split('\n')[0][:180]


def extract_cta(text: str | None) -> str | None:
    if not text:
        return None
    for pattern in CTA_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(0).lower()
    return None


def classify_format(text: str | None) -> str:
    if not text:
        return 'unknown'
    for label, pattern in FORMATS.items():
        if pattern.search(text):
            return label
    return 'generic'


def sentiment_tone(text: str | None) -> tuple[str, str]:
    if not text:
        return ('unknown', 'neutral')
    positive_words = ['growth', 'win', 'success', 'better']
    negative_words = ['pain', 'problem', 'failed', 'struggle']
    text_l = text.lower()
    p = sum(w in text_l for w in positive_words)
    n = sum(w in text_l for w in negative_words)
    sentiment = 'positive' if p > n else 'negative' if n > p else 'neutral'
    tone = 'assertive' if '!' in text else 'calm'
    return sentiment, tone


def frequent_hooks(posts: list[str], top_n: int = 10) -> list[tuple[str, int]]:
    hooks = [extract_hook(p) for p in posts if p]
    return Counter(hooks).most_common(top_n)
