"""
scorer/career.py
----------------
Career trajectory score for the Senior AI Engineer JD.

Signals used:
  1. Title relevance — current title & historical titles vs JD-relevant titles
  2. Company type — product company vs consulting/services (explicit disqualifier)
  3. Career progression — upward arc, avg tenure per role
  4. Role description text — how much of the work was ML/search/ranking
  5. Career focus consistency — all over the place vs focused on AI/ML

Disqualifiers:
  - Entire career at consulting firms → score × 0.08
  - Current title is a hard non-AI role (Marketing, HR, etc.) → heavy penalty
  - Title chaser: average tenure < 12 months across 3+ companies → penalty

Score: 0.0 – 1.0
"""

from __future__ import annotations
import re
from typing import Any

from jd_config import (
    CONSULTING_FIRMS,
    DISQUALIFIER_TITLES,
    RELEVANT_TITLES,
    PRODUCTION_ML_KEYWORDS,
)

# How much each career element contributes to career_score
_TITLE_WEIGHT = 0.40
_COMPANY_WEIGHT = 0.25
_ROLE_DESC_WEIGHT = 0.25
_PROGRESSION_WEIGHT = 0.10


def _norm(text: str) -> str:
    return text.lower().strip()


def _title_relevance(title: str) -> float:
    """Score 0-1: how relevant is this job title to the JD?"""
    t = _norm(title)
    # Direct hit on relevant titles
    if any(rt in t for rt in RELEVANT_TITLES):
        # Bonus for explicitly AI/ML-focused titles
        if any(kw in t for kw in ["ai", "ml", "machine learning", "nlp", "search",
                                    "ranking", "recommend", "retrieval", "llm",
                                    "data scien", "deep learn"]):
            return 1.0
        return 0.75  # generic SE / backend — partial credit

    # Hard disqualifier titles
    if any(dt in t for dt in DISQUALIFIER_TITLES):
        return 0.05

    # In-between: technical but not ML-focused
    adjacent_technical = [
        "engineer", "developer", "architect", "tech lead", "principal",
        "staff", "analyst", "scientist", "researcher",
    ]
    if any(at in t for at in adjacent_technical):
        return 0.35

    return 0.10


def _company_type_score(career: list[dict]) -> tuple[float, bool]:
    """
    Returns (score 0-1, is_consulting_only).
    Checks if the candidate's career is predominantly at consulting firms.
    """
    if not career:
        return 0.5, False

    total_months = sum(int(j.get("duration_months") or 0) for j in career)
    consulting_months = 0

    for job in career:
        company = _norm(job.get("company") or "")
        duration = int(job.get("duration_months") or 0)
        if any(cf in company for cf in CONSULTING_FIRMS):
            consulting_months += duration

    if total_months == 0:
        return 0.5, False

    consulting_ratio = consulting_months / total_months

    if consulting_ratio >= 0.85:
        return 0.05, True   # consulting-only career = explicit disqualifier
    elif consulting_ratio >= 0.60:
        return 0.30, False  # mostly consulting
    elif consulting_ratio >= 0.40:
        return 0.55, False  # mixed
    elif consulting_ratio >= 0.20:
        return 0.80, False  # some consulting, mostly product
    else:
        return 1.00, False  # product company career


def _role_desc_score(career: list[dict]) -> float:
    """
    Score 0-1 based on how much of the candidate's work was ML/search/ranking.
    Uses recent roles more heavily.
    """
    if not career:
        return 0.0

    keyword_set = set(PRODUCTION_ML_KEYWORDS)
    weighted_scores: list[tuple[float, float]] = []  # (duration_weight, match_score)

    for job in career:
        desc = _norm(job.get("description") or "")
        if not desc:
            continue
        duration = int(job.get("duration_months") or 1)
        words = re.findall(r'\b\w+\b', desc)
        if not words:
            continue
        # Count keyword hits (with some density normalisation)
        hits = sum(1 for kw in keyword_set if kw in desc)
        # Density: hits per 100 words (saturate at 12)
        density = min(hits / max(len(words) / 100, 1), 12) / 12
        weighted_scores.append((duration, density))

    if not weighted_scores:
        return 0.0

    total_dur = sum(d for d, _ in weighted_scores)
    if total_dur == 0:
        return 0.0

    weighted_avg = sum(d * s for d, s in weighted_scores) / total_dur
    return min(weighted_avg * 1.5, 1.0)  # scale up slightly since 12/12 is very high


def _progression_score(career: list[dict], yoe: float) -> float:
    """
    Score 0-1 based on career progression signals.
    Penalises title chasers (frequent job hops for title bumps).
    """
    if not career or len(career) < 2:
        return 0.7  # not enough data to penalise

    durations = [int(j.get("duration_months") or 0) for j in career if not j.get("is_current")]
    if not durations:
        return 0.7

    avg_tenure = sum(durations) / len(durations)

    # Title chaser: avg < 12 months at 3+ jobs
    if avg_tenure < 12 and len(durations) >= 3:
        return 0.3
    elif avg_tenure < 18 and len(durations) >= 4:
        return 0.5
    elif avg_tenure >= 24:
        return 1.0
    else:
        return 0.75


def compute_career_score(candidate: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """
    Returns (score 0-1, debug_info dict).
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    yoe = float(profile.get("years_of_experience") or 0)

    current_title = profile.get("current_title") or ""
    title_score = _title_relevance(current_title)

    # Also consider peak title relevance across career history
    historical_title_scores = [
        _title_relevance(j.get("title") or "") for j in career
    ]
    peak_title_score = max(historical_title_scores) if historical_title_scores else 0.0
    # Blend: current title 65%, peak historical 35%
    blended_title_score = 0.65 * title_score + 0.35 * peak_title_score

    company_score, is_consulting_only = _company_type_score(career)
    role_desc_score = _role_desc_score(career)
    progression_score = _progression_score(career, yoe)

    # Check for hard non-AI current title
    if any(dt in _norm(current_title) for dt in DISQUALIFIER_TITLES):
        current_title_is_disqualifier = True
    else:
        current_title_is_disqualifier = False

    raw_score = (
        _TITLE_WEIGHT * blended_title_score
        + _COMPANY_WEIGHT * company_score
        + _ROLE_DESC_WEIGHT * role_desc_score
        + _PROGRESSION_WEIGHT * progression_score
    )

    # Hard disqualifier modifiers
    if is_consulting_only:
        final_score = raw_score * 0.12
    elif current_title_is_disqualifier:
        # Non-AI title currently, but could have AI background
        final_score = raw_score * 0.25
    else:
        final_score = raw_score

    debug = {
        "current_title": current_title,
        "title_score": round(blended_title_score, 3),
        "company_score": round(company_score, 3),
        "is_consulting_only": is_consulting_only,
        "role_desc_score": round(role_desc_score, 3),
        "progression_score": round(progression_score, 3),
        "raw_score": round(raw_score, 4),
        "final_score": round(final_score, 4),
    }

    return min(final_score, 1.0), debug
