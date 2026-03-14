"""
AI keyword clustering using TF-IDF + KMeans (fast, no download needed).
Optional: sentence-transformers for semantic clustering (more accurate).
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


def cluster_keywords_tfidf(keywords: list[str], n_clusters: int = 5) -> dict[int, list[str]]:
    """Fast clustering using TF-IDF character n-grams."""
    if len(keywords) < n_clusters:
        n_clusters = max(1, len(keywords))

    vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=1,
        max_features=5000,
    )
    X = vectorizer.fit_transform(keywords)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    clusters: dict[int, list[str]] = {}
    for kw, label in zip(keywords, labels):
        clusters.setdefault(int(label), []).append(kw)

    return clusters


def cluster_keywords_semantic(keywords: list[str], n_clusters: int = 5) -> dict[int, list[str]]:
    """
    Semantic clustering using sentence-transformers.
    Falls back to TF-IDF if library not available.
    """
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(keywords, show_progress_bar=False)

        if len(keywords) < n_clusters:
            n_clusters = max(1, len(keywords))

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)

        clusters: dict[int, list[str]] = {}
        for kw, label in zip(keywords, labels):
            clusters.setdefault(int(label), []).append(kw)

        return clusters

    except ImportError:
        return cluster_keywords_tfidf(keywords, n_clusters)


def name_cluster(keywords: list[str]) -> str:
    """
    Generate a descriptive name for a cluster by finding the
    most common meaningful words across all keywords in it.
    """
    from collections import Counter

    stop = {
        "for", "and", "the", "of", "in", "to", "a", "an", "at",
        "with", "how", "book", "guide",
    }
    words = []
    for kw in keywords:
        words.extend([w for w in kw.lower().split() if w not in stop and len(w) > 3])

    if not words:
        return f"Cluster ({len(keywords)} keywords)"

    most_common = Counter(words).most_common(3)
    return " / ".join(w for w, _ in most_common).title()


def auto_name_clusters(clusters: dict[int, list[str]]) -> dict[str, list[str]]:
    """Return clusters with auto-generated human-readable names."""
    return {name_cluster(kws): kws for kws in clusters.values()}
