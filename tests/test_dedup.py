from app.utils.text import dedup_hash


def test_dedup_hash_normalization():
    assert dedup_hash('Hello   World') == dedup_hash('hello world')
