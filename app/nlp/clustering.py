from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def cluster_texts(texts: list[str], threshold: float = 0.35) -> list[int]:
    if not texts:
        return []
    if len(texts) == 1:
        return [0]

    cleaned = [t if (t or '').strip() else f'empty_{i}' for i, t in enumerate(texts)]
    try:
        tfidf = TfidfVectorizer(min_df=1, stop_words='english')
        matrix = tfidf.fit_transform(cleaned)
        sim = cosine_similarity(matrix)
    except ValueError:
        # e.g. "empty vocabulary" when all docs are effectively stop-words
        return list(range(len(texts)))

    clusters = [-1] * len(texts)
    current = 0
    for i in range(len(texts)):
        if clusters[i] != -1:
            continue
        clusters[i] = current
        for j in range(i + 1, len(texts)):
            if sim[i, j] >= threshold:
                clusters[j] = current
        current += 1
    return clusters


def near_duplicates(texts: list[str], threshold: float = 0.9) -> dict[int, list[int]]:
    if len(texts) < 2:
        return {}
    try:
        tfidf = TfidfVectorizer(min_df=1, stop_words='english').fit_transform(texts)
    except ValueError:
        return {}
    sim = cosine_similarity(tfidf)
    groups = defaultdict(list)
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if sim[i, j] >= threshold:
                groups[i].append(j)
    return dict(groups)
