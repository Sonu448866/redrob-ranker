"""
scorer/education.py
-------------------
Education score for the Senior AI Engineer JD.

Factors:
  1. Institution tier (tier_1 best → tier_4 worst; unknown = average)
  2. Field of study relevance (CS/EE/Math/Stats/AI = high; other STEM = medium; non-STEM = low)
  3. Degree level (PhD / M.Tech / M.S. > B.Tech / B.E. / B.S.)

Score: 0.0 – 1.0
"""

from __future__ import annotations
from typing import Any

from jd_config import HIGH_RELEVANCE_FIELDS

TIER_SCORES = {
    "tier_1": 1.00,
    "tier_2": 0.78,
    "tier_3": 0.55,
    "tier_4": 0.30,
    "unknown": 0.45,
}

DEGREE_LEVEL_SCORES = {
    "phd": 1.00,
    "ph.d": 1.00,
    "d.sc": 1.00,
    "m.tech": 0.88,
    "m.e.": 0.88,
    "m.s.": 0.88,
    "ms": 0.88,
    "mtech": 0.88,
    "m.sc": 0.82,
    "msc": 0.82,
    "m.b.a": 0.55,
    "mba": 0.55,
    "b.tech": 0.72,
    "b.e.": 0.72,
    "be": 0.72,
    "btech": 0.72,
    "b.s.": 0.72,
    "bs": 0.72,
    "b.sc": 0.65,
    "bsc": 0.65,
    "diploma": 0.45,
}

_HIGH_REL = 1.00
_MED_REL = 0.70
_LOW_REL = 0.40


def _field_relevance(field: str) -> float:
    fl = field.lower()
    if any(hrf in fl for hrf in HIGH_RELEVANCE_FIELDS):
        return _HIGH_REL

    # Medium relevance: engineering fields
    medium_fields = [
        "engineering", "physics", "operations research", "cognitive science",
        "bioinformatics", "robotics",
    ]
    if any(m in fl for m in medium_fields):
        return _MED_REL

    return _LOW_REL


def _degree_level_score(degree: str) -> float:
    dl = degree.lower().strip()
    for key, score in DEGREE_LEVEL_SCORES.items():
        if key in dl:
            return score
    # Unknown degree
    return 0.60


def compute_education_score(candidate: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """
    Returns (score 0-1, debug_info dict).
    Takes the best education entry (highest combined score).
    """
    education: list[dict] = candidate.get("education", [])

    if not education:
        return 0.35, {"note": "no education listed"}

    best_score = 0.0
    best_entry = {}

    for edu in education:
        tier = edu.get("tier", "unknown") or "unknown"
        degree = edu.get("degree", "") or ""
        field = edu.get("field_of_study", "") or ""

        tier_s = TIER_SCORES.get(tier, 0.45)
        degree_s = _degree_level_score(degree)
        field_s = _field_relevance(field)

        # Combine: institution tier most important, then field, then level
        combined = 0.45 * tier_s + 0.35 * field_s + 0.20 * degree_s

        if combined > best_score:
            best_score = combined
            best_entry = {
                "institution": edu.get("institution", ""),
                "degree": degree,
                "field": field,
                "tier": tier,
                "tier_score": round(tier_s, 3),
                "degree_score": round(degree_s, 3),
                "field_score": round(field_s, 3),
                "combined": round(combined, 4),
            }

    return min(best_score, 1.0), best_entry
