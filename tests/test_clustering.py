from app.nlp.clustering import cluster_texts


def test_cluster_texts():
    clusters = cluster_texts(['how to get leads from threads', 'how to get leads from threads fast', 'totally different cooking post'])
    assert len(clusters) == 3
    assert clusters[0] == clusters[1]
