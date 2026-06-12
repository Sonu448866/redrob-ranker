"""
scorer/semantic.py
------------------
Semantic similarity between candidate's career text and the JD,
using TF-IDF cosine similarity (CPU-only, no network, < 5 min for 100K).

Why TF-IDF instead of sentence-transformers?
  The compute constraints say: CPU-only, no GPU, ≤5 minutes, ≤16 GB RAM,
  no network. A SBERT model would need ~400MB of model weights and would
  take 30+ minutes for 100K candidates on CPU.
  TF-IDF with a well-curated vocabulary runs in ~10 seconds on 100K docs
  while still capturing the key retrieval/ranking vocabulary differences.

The semantic score is used as an ADDITIVE BONUS on top of structured scores,
not as the primary signal. Max contribution: +0.12 to the final base score.
"""

from __future__ import annotations
import re
from typing import Any

from jd_config import JD_TEXT

# Lazy-initialised at first call
_vectorizer = None
_jd_vector = None


def _build_text(candidate: dict[str, Any]) -> str:
    """Concatenate all meaningful text from a candidate profile."""
    parts: list[str] = []

    # Summary and headline
    profile = candidate.get("profile", {})
    parts.append(profile.get("headline") or "")
    parts.append(profile.get("summary") or "")
    parts.append(profile.get("current_title") or "")

    # Career descriptions
    for job in candidate.get("career_history", []):
        parts.append(job.get("title") or "")
        parts.append(job.get("description") or "")

    # Skill names
    for skill in candidate.get("skills", []):
        parts.append(skill.get("name") or "")

    # Certifications
    for cert in candidate.get("certifications", []):
        parts.append(cert.get("name") or "")

    return " ".join(p for p in parts if p)


def _get_vectorizer_and_jd():
    """Initialise TF-IDF vectorizer (singleton)."""
    global _vectorizer, _jd_vector
    if _vectorizer is not None:
        return _vectorizer, _jd_vector

    from sklearn.feature_extraction.text import TfidfVectorizer

    _vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),   # unigrams + bigrams to capture "vector database", "fine tuning"
        min_df=1,
        max_df=0.95,
        sublinear_tf=True,    # log-scale TF
        strip_accents="unicode",
        lowercase=True,
        max_features=50_000,
    )
    # Fit only on JD text first; transform will generalise
    _vectorizer.fit([JD_TEXT])
    _jd_vector = _vectorizer.transform([JD_TEXT])
    return _vectorizer, _jd_vector


def batch_compute_semantic_scores(
    candidates: list[dict[str, Any]],
) -> list[float]:
    """
    Compute TF-IDF cosine similarity for a batch of candidates.
    Returns list of scores (0-1) in same order as input.

    Fits the vectorizer on JD + all candidate texts for richer vocab.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    jd_text = JD_TEXT
    candidate_texts = [_build_text(c) for c in candidates]

    # Fit on JD + all candidates for best vocabulary
    all_texts = [jd_text] + candidate_texts

    vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.90,
        sublinear_tf=True,
        strip_accents="unicode",
        lowercase=True,
        max_features=60_000,
    )
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    jd_vec = tfidf_matrix[0]          # shape (1, vocab)
    cand_vecs = tfidf_matrix[1:]       # shape (N, vocab)

    similarities = cosine_similarity(jd_vec, cand_vecs)[0]  # shape (N,)

    # Normalise to 0-1 range (cosine is already 0-1 for non-negative TF-IDF)
    max_sim = similarities.max() if similarities.max() > 0 else 1.0
    # Keep raw cosine — don't normalise to prevent inflation
    return similarities.tolist()
