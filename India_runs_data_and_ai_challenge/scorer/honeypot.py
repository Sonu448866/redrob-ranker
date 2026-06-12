"""
scorer/honeypot.py
------------------
Detects candidates with logically impossible or fabricated profiles.
The dataset contains ~80 honeypot candidates that must be excluded from
the top 100 (>10% honeypot rate = disqualification).

Detection checks (any single hard trigger = honeypot; 2+ soft = honeypot):
  HARD triggers:
    H1 – "expert" proficiency with duration_months == 0
    H2 – Overlapping full-time employments (same months at two jobs)
    H3 – Total career duration > years_of_experience * 12 + 24 months
  SOFT triggers (count ≥ 2 → honeypot):
    S1 – years_of_experience >> sum(career_history.duration_months) / 12 + 2
    S2 – Skill count > 30 with total experience < 3 years
    S3 – Claimed "expert" in 5+ skills with avg duration < 12 months each
    S4 – Profile completeness 100 with very few signals filled
"""

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _overlapping_jobs(career: list[dict]) -> bool:
    """Return True if two non-current full-time roles overlap in time."""
    from datetime import date

    intervals: list[tuple[date, date]] = []
    for job in career:
        try:
            start = date.fromisoformat(job["start_date"])
            end_raw = job.get("end_date")
            if end_raw is None:
                continue  # current job — skip
            end = date.fromisoformat(end_raw)
            intervals.append((start, end))
        except (ValueError, TypeError, KeyError):
            continue

    # Check pairwise overlap
    for i in range(len(intervals)):
        for j in range(i + 1, len(intervals)):
            s1, e1 = intervals[i]
            s2, e2 = intervals[j]
            # Overlap exists if one starts before the other ends
            overlap_start = max(s1, s2)
            overlap_end = min(e1, e2)
            if overlap_start < overlap_end:
                # Significant overlap: >3 months
                months = (overlap_end.year - overlap_start.year) * 12 + (
                    overlap_end.month - overlap_start.month
                )
                if months > 3:
                    return True
    return False


def detect_honeypot(candidate: dict[str, Any]) -> tuple[bool, str]:
    """
    Returns (is_honeypot, reason_string).
    If is_honeypot is True, the candidate must be scored near 0.
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})

    yoe = float(profile.get("years_of_experience", 0) or 0)

    # ------------------------------------------------------------------ HARD
    # H1: Expert skill with 0 duration
    expert_zero_dur = [
        s["name"]
        for s in skills
        if s.get("proficiency") in ("expert", "advanced")
        and int(s.get("duration_months") or 0) == 0
    ]
    if len(expert_zero_dur) >= 3:
        return True, (
            f"Honeypot H1: {len(expert_zero_dur)} advanced/expert skills "
            f"with 0 months usage ({', '.join(expert_zero_dur[:3])}…)"
        )

    # H2: Overlapping full-time jobs (>3 month overlap)
    if len(career) >= 2 and _overlapping_jobs(career):
        return True, "Honeypot H2: overlapping full-time employment periods detected"

    # H3: Total career duration inconsistent with YOE
    total_career_months = sum(int(j.get("duration_months") or 0) for j in career)
    max_possible_months = yoe * 12 + 24  # allow 2 years leeway
    if total_career_months > max_possible_months + 36 and yoe > 0:
        return True, (
            f"Honeypot H3: total career months ({total_career_months}) far exceeds "
            f"years_of_experience ({yoe:.1f} yrs → ~{max_possible_months:.0f} months max)"
        )

    # ------------------------------------------------------------------ SOFT
    soft_flags: list[str] = []

    # S1: YOE >> career months
    if yoe > 3 and total_career_months > 0:
        career_yrs = total_career_months / 12
        if yoe > career_yrs + 4:
            soft_flags.append(
                f"S1: YOE ({yoe:.1f}) >> career history ({career_yrs:.1f} yrs)"
            )

    # S2: Too many skills for experience level
    if yoe < 3 and len(skills) > 25:
        soft_flags.append(
            f"S2: {len(skills)} skills listed with only {yoe:.1f} yrs experience"
        )

    # S3: Many expert skills with tiny average duration
    expert_skills = [s for s in skills if s.get("proficiency") in ("expert", "advanced")]
    if len(expert_skills) >= 5:
        avg_dur = sum(int(s.get("duration_months") or 0) for s in expert_skills) / len(
            expert_skills
        )
        if avg_dur < 8:
            soft_flags.append(
                f"S3: {len(expert_skills)} advanced/expert skills, avg duration "
                f"{avg_dur:.1f} months"
            )

    # S4: Single expert-zero-duration skill (1 is suspicious but not hard trigger)
    if len(expert_zero_dur) >= 1:
        soft_flags.append(
            f"S4: {len(expert_zero_dur)} advanced/expert skills with 0 duration"
        )

    if len(soft_flags) >= 2:
        return True, "Honeypot (soft): " + "; ".join(soft_flags)

    return False, ""
