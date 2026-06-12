"""
scorer/skills.py
----------------
Skills matching score for the Senior AI Engineer JD.

Algorithm:
  For each required skill group (from jd_config):
    - Find matching skills in candidate's profile
    - Score = proficiency_weight × duration_weight × endorsement_weight
    - Apply trust multiplier from skill_assessment_scores (Redrob platform)
    - Apply anti-stuffing penalty: advanced/expert skill with 0 duration → ×0.1

  Group scores are combined with group importance weights.
  Nice-to-have groups add a bonus (up to +0.15 on top of required score).

  Final score: 0.0 – 1.0
"""

from __future__ import annotations
import math
import re
from typing import Any

from jd_config import (
    REQUIRED_SKILL_GROUPS,
    NICE_TO_HAVE_SKILL_GROUPS,
)

# Proficiency → numeric weight
PROFICIENCY_WEIGHTS = {
    "beginner": 0.20,
    "intermediate": 0.45,
    "advanced": 0.75,
    "expert": 1.00,
}

# Duration normalisation: log-scale, saturates at ~48 months
_DUR_SAT = 48.0


def _duration_weight(months: int) -> float:
    if months <= 0:
        return 0.0
    return math.log(months + 1) / math.log(_DUR_SAT + 1)


def _endorsement_weight(endorsements: int) -> float:
    """Saturates at 50 endorsements → 1.0"""
    return min(endorsements, 50) / 50.0


def _matches_any(skill_name: str, patterns: list[str]) -> bool:
    """Case-insensitive substring match."""
    lower = skill_name.lower()
    return any(p in lower for p in patterns)


def _score_skill(skill: dict[str, Any], assessment_scores: dict[str, float]) -> float:
    """
    Score a single skill entry.
    Returns a raw quality score 0–1.
    """
    proficiency = skill.get("proficiency", "beginner")
    duration = int(skill.get("duration_months") or 0)
    endorsements = int(skill.get("endorsements") or 0)

    prof_w = PROFICIENCY_WEIGHTS.get(proficiency, 0.2)
    dur_w = _duration_weight(duration)
    end_w = _endorsement_weight(endorsements)

    # Anti-stuffing: high proficiency claim with 0 actual usage
    if proficiency in ("advanced", "expert") and duration == 0:
        stuffing_penalty = 0.08  # nearly zero credit
    elif proficiency == "expert" and duration < 6:
        stuffing_penalty = 0.35
    elif proficiency == "advanced" and duration < 3:
        stuffing_penalty = 0.4
    else:
        stuffing_penalty = 1.0

    # Platform assessment trust boost
    assessment_key = skill.get("name", "")
    platform_score = assessment_scores.get(assessment_key, -1)
    if platform_score >= 0:
        # platform score 0-100; normalise and blend
        platform_w = 0.7 + 0.3 * (platform_score / 100.0)
    else:
        platform_w = 1.0

    # Combine: proficiency is most important, then duration, then endorsements
    raw = (0.50 * prof_w + 0.35 * dur_w + 0.15 * end_w) * stuffing_penalty * platform_w
    return min(raw, 1.0)


def compute_skills_score(candidate: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """
    Returns (score 0-1, debug_info dict).
    """
    skills: list[dict] = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    assessment_scores: dict[str, float] = signals.get("skill_assessment_scores", {}) or {}

    # Build lookup: lower skill name → (skill dict, raw quality score)
    skill_map: dict[str, tuple[dict, float]] = {}
    for s in skills:
        name = (s.get("name") or "").lower()
        quality = _score_skill(s, assessment_scores)
        if name not in skill_map or skill_map[name][1] < quality:
            skill_map[name] = (s, quality)

    debug: dict[str, Any] = {"matched_required": {}, "matched_nice": {}}

    # ----------------------------------------------------------------
    # Required groups
    # ----------------------------------------------------------------
    required_group_scores: list[tuple[float, float]] = []  # (importance, group_score)
    for group_name, (importance, patterns) in REQUIRED_SKILL_GROUPS.items():
        best_score = 0.0
        matched_skills = []
        for skill_name, (skill_obj, quality) in skill_map.items():
            if _matches_any(skill_name, patterns):
                if quality > best_score:
                    best_score = quality
                matched_skills.append(
                    (skill_obj.get("name", skill_name), round(quality, 3))
                )
        required_group_scores.append((importance, best_score))
        debug["matched_required"][group_name] = matched_skills

    # Weighted average of required groups
    total_importance = sum(imp for imp, _ in required_group_scores)
    if total_importance > 0:
        base_score = sum(imp * gs for imp, gs in required_group_scores) / total_importance
    else:
        base_score = 0.0

    # ----------------------------------------------------------------
    # Nice-to-have bonus (max 0.18 additive)
    # ----------------------------------------------------------------
    nice_bonus = 0.0
    max_nice_bonus = 0.18
    for group_name, (importance, patterns) in NICE_TO_HAVE_SKILL_GROUPS.items():
        best_score = 0.0
        matched_skills = []
        for skill_name, (skill_obj, quality) in skill_map.items():
            if _matches_any(skill_name, patterns):
                if quality > best_score:
                    best_score = quality
                matched_skills.append(
                    (skill_obj.get("name", skill_name), round(quality, 3))
                )
        nice_bonus += importance * best_score * 0.05
        debug["matched_nice"][group_name] = matched_skills

    nice_bonus = min(nice_bonus, max_nice_bonus)

    final_score = min(base_score + nice_bonus, 1.0)
    debug["base_score"] = round(base_score, 4)
    debug["nice_bonus"] = round(nice_bonus, 4)
    debug["final_score"] = round(final_score, 4)

    return final_score, debug
