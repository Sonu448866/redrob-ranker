"""
scorer/experience.py
--------------------
Experience validity score for the Senior AI Engineer JD.

The JD says 5-9 years, sweet spot 6-8.
Disqualifiers:
  - Pure research / academic (no production deployment)
  - Only <12 months of "AI experience" from LangChain tutorials

Score: 0.0 – 1.0
"""

from __future__ import annotations
from typing import Any
import math

from jd_config import EXP_MIN, EXP_MAX, EXP_SWEET_SPOT_MIN, EXP_SWEET_SPOT_MAX

# Research-only signals in role descriptions / titles
RESEARCH_ONLY_KEYWORDS = [
    "phd", "researcher", "research intern", "research scientist",
    "academic", "university", "published", "paper", "lab",
    "iit research", "isc research",
]

PRODUCTION_SIGNALS = [
    "deployed", "production", "shipped", "real users", "users",
    "scale", "serving", "api", "microservice", "pipeline",
    "latency", "throughput", "a/b", "experiment",
]

LANGCHAIN_ONLY_KEYWORDS = [
    "langchain", "llamaindex", "openai api", "chatgpt api",
    "gpt-4 api", "gpt4 api", "claude api", "gemini api",
]


def _exp_range_score(yoe: float) -> float:
    """
    Optimal: 6-8 years → 1.0
    Acceptable: 5-9 years → 0.85
    Outside: drops off smoothly.
    """
    if yoe <= 0:
        return 0.0
    # Gaussian-like curve centred at 7 yrs
    centre = (EXP_SWEET_SPOT_MIN + EXP_SWEET_SPOT_MAX) / 2  # 7.0
    if EXP_SWEET_SPOT_MIN <= yoe <= EXP_SWEET_SPOT_MAX:
        return 1.0
    elif EXP_MIN <= yoe < EXP_SWEET_SPOT_MIN:
        return 0.80 + 0.20 * (yoe - EXP_MIN) / (EXP_SWEET_SPOT_MIN - EXP_MIN)
    elif EXP_SWEET_SPOT_MAX < yoe <= EXP_MAX:
        return 0.80 + 0.20 * (EXP_MAX - yoe) / (EXP_MAX - EXP_SWEET_SPOT_MAX)
    elif yoe < EXP_MIN:
        # Below minimum — drops sharply
        return max(0.0, 0.60 * (yoe / EXP_MIN))
    else:
        # Above maximum (> 9 yrs) — mild penalty for possible over-seniority
        excess = yoe - EXP_MAX
        return max(0.55, 0.80 - 0.03 * excess)


def _research_only_ratio(career: list[dict]) -> float:
    """
    Returns fraction of career that looks purely research/academic.
    """
    if not career:
        return 0.0

    total_months = sum(int(j.get("duration_months") or 0) for j in career)
    if total_months == 0:
        return 0.0

    research_months = 0
    for job in career:
        desc = (job.get("description") or "").lower()
        title = (job.get("title") or "").lower()
        has_research = any(k in desc or k in title for k in RESEARCH_ONLY_KEYWORDS)
        has_production = any(k in desc for k in PRODUCTION_SIGNALS)
        if has_research and not has_production:
            research_months += int(job.get("duration_months") or 0)

    return research_months / total_months


def _langchain_only_ratio(career: list[dict]) -> float:
    """
    Returns fraction of AI work that looks like surface-level LLM API usage.
    """
    if not career:
        return 0.0

    ai_months = 0
    langchain_months = 0

    for job in career:
        desc = (job.get("description") or "").lower()
        has_ai = any(k in desc for k in ["llm", "ai", "ml", "model", "embedding", "gpt"])
        has_langchain = any(k in desc for k in LANGCHAIN_ONLY_KEYWORDS)
        duration = int(job.get("duration_months") or 0)
        if has_ai:
            ai_months += duration
        if has_langchain and not any(k in desc for k in PRODUCTION_SIGNALS):
            langchain_months += duration

    if ai_months == 0:
        return 0.0
    return langchain_months / ai_months


def compute_experience_score(candidate: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """
    Returns (score 0-1, debug_info dict).
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    yoe = float(profile.get("years_of_experience") or 0)

    range_score = _exp_range_score(yoe)
    research_ratio = _research_only_ratio(career)
    langchain_ratio = _langchain_only_ratio(career)

    # Modifiers for disqualifying patterns
    if research_ratio > 0.80:
        # Pure researcher — strong penalty
        modifier = 0.20
        flag = "pure_research"
    elif research_ratio > 0.50:
        modifier = 0.55
        flag = "mostly_research"
    elif langchain_ratio > 0.70:
        modifier = 0.35
        flag = "langchain_only"
    elif langchain_ratio > 0.40:
        modifier = 0.70
        flag = "partial_langchain"
    else:
        modifier = 1.0
        flag = "none"

    final_score = range_score * modifier

    debug = {
        "years_of_experience": yoe,
        "range_score": round(range_score, 4),
        "research_ratio": round(research_ratio, 4),
        "langchain_ratio": round(langchain_ratio, 4),
        "disqualifier_flag": flag,
        "modifier": modifier,
        "final_score": round(final_score, 4),
    }

    return min(final_score, 1.0), debug
