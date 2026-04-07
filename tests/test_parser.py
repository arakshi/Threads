from pathlib import Path

from app.collectors.public_web.parser import parse_public_post


def test_parse_public_post():
    html = Path('data/fixtures/sample_thread_post.html').read_text(encoding='utf-8')
    row = parse_public_post(html, 'https://www.threads.net/@demo/post/ABC123')
    assert row['external_id'] == 'ABC123'
    assert row['likes'] == 120
    assert row['has_media'] is True
