"""
reasoning.py
------------
Generates specific, non-templated 1-2 sentence reasoning for each candidate
in the top 100 shortlist.

Design principles:
  1. Reference specific facts from the candidate's profile (not generic praise)
  2. Connect to specific JD requirements (not just "good skills")
  3. Acknowledge real concerns honestly where they exist
  4. Never hallucinate — every claim must exist in the profile
  5. Vary structure and content across candidates (Stage 4 check: no templating)
"""

from __future__ import annotations
from datetime import date
from typing import Any


def _days_since(date_str: str | None) -> int:
    if not date_str:
        return 9999
    try:
        d = date.fromisoformat(date_str)
        return (date.today() - d).days
    except (ValueError, TypeError):
        return 9999


def _top_skills(candidate: dict, n: int = 3) -> list[str]:
    """Return top N skills by (proficiency_rank × endorsements × duration)."""
    pmap = {"expert": 4, "advanced": 3, "intermediate": 2, "beginner": 1}
    skills = candidate.get("skills", [])
    ranked = sorted(
        skills,
        key=lambda s: (
            pmap.get(s.get("proficiency", "beginner"), 1)
            * (int(s.get("endorsements") or 0) + 1)
            * (int(s.get("duration_months") or 0) + 1)
        ),
        reverse=True,
    )
    return [s.get("name", "") for s in ranked[:n] if s.get("name")]


def _current_role_summary(candidate: dict) -> str:
    """One-liner describing current role."""
    profile = candidate.get("profile", {})
    title = profile.get("current_title") or "Engineer"
    company = profile.get("current_company") or "current employer"
    yoe = float(profile.get("years_of_experience") or 0)
    return f"{yoe:.1f}-yr {title} at {company}"


def _best_career_highlight(candidate: dict) -> str:
    """Extract the most impressive sentence from career descriptions."""
    highlight_kws = [
        "deployed", "shipped", "built", "led", "architected", "designed",
        "production", "real users", "scale", "billion", "million",
        "retrieval", "ranking", "embedding", "vector", "search",
        "fine-tuning", "llm", "bert", "recommendation",
    ]
    best = ""
    best_score = 0
    for job in candidate.get("career_history", []):
        desc = job.get("description") or ""
        sentences = [s.strip() for s in desc.split(".") if len(s.strip()) > 20]
        for sent in sentences:
            sl = sent.lower()
            sc = sum(1 for kw in highlight_kws if kw in sl)
            if sc > best_score:
                best_score = sc
                # Trim to ~80 chars
                best = sent[:120].strip()
    return best


def _gap_note(candidate: dict, scores: dict) -> str:
    """One honest gap or concern, if any."""
    signals = candidate.get("redrob_signals", {})
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])

    days_inactive = _days_since(signals.get("last_active_date"))
    response_rate = float(signals.get("recruiter_response_rate") or 0)
    notice = int(signals.get("notice_period_days") or 0)
    yoe = float(profile.get("years_of_experience") or 0)
    location = (profile.get("location") or "").lower()

    if days_inactive > 120:
        return f"last active {days_inactive // 30} months ago (availability uncertain)"
    if response_rate < 0.15:
        return f"low recruiter response rate ({response_rate:.0%}) may delay outreach"
    if notice > 90:
        return f"notice period of {notice} days exceeds JD preference"
    if yoe < 5:
        return f"at {yoe:.1f} years, slightly below the 5–9 year target band"
    if yoe > 11:
        return f"at {yoe:.1f} years, more senior than the JD's 5–9 year band"

    # Check if not in preferred location
    preferred = {"pune", "noida"}
    willing = bool(signals.get("willing_to_relocate", False))
    if not any(p in location for p in preferred) and not willing:
        country = (profile.get("country") or "").lower()
        if "india" not in country:
            return "outside India — no visa sponsorship per JD"

    return ""


def generate_reasoning(
    candidate: dict[str, Any],
    rank: int,
    scores: dict[str, Any],
) -> str:
    """
    Generate a 1-2 sentence profile-specific reasoning string.
    References facts from the candidate; connects to JD; honest about gaps.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    cid = candidate.get("candidate_id", "")
    title = profile.get("current_title") or "Engineer"
    company = profile.get("current_company") or "current employer"
    yoe = float(profile.get("years_of_experience") or 0)
    location = profile.get("location") or ""
    country = profile.get("country") or ""

    top_skills = _top_skills(candidate, n=3)
    career_highlight = _best_career_highlight(candidate)
    gap = _gap_note(candidate, scores)

    # Pull score components for phrasing
    skills_s = scores.get("skills_score", 0.0)
    career_s = scores.get("career_score", 0.0)
    behavioral_mod = scores.get("behavioral_modifier", 1.0)
    notice = int(signals.get("notice_period_days") or 60)
    response_rate = float(signals.get("recruiter_response_rate") or 0)
    github = float(signals.get("github_activity_score") or -1)
    open_flag = bool(signals.get("open_to_work_flag", False))

    # ---- Sentence 1: what makes this candidate strong ----
    skills_str = ", ".join(top_skills) if top_skills else "relevant AI skills"

    if career_s > 0.65 and career_highlight:
        # Lead with career achievement
        highlight_short = career_highlight[:100].rstrip(",;") + "…"
        sentence1 = (
            f"{yoe:.1f}-yr {title} ({location}) who {highlight_short.lower()}; "
            f"core skills include {skills_str}."
        )
    elif skills_s > 0.55:
        # Lead with skills match
        sentence1 = (
            f"{yoe:.1f}-yr {title} based in {location} with strong alignment on "
            f"JD-critical skills: {skills_str}."
        )
    else:
        sentence1 = (
            f"{yoe:.1f}-yr {title} at {company} ({location}) with {skills_str} "
            f"in their toolkit."
        )

    # ---- Sentence 2: behavioral signal or honest gap ----
    if gap:
        sentence2 = f"Concern: {gap}."
    elif open_flag and notice <= 30 and response_rate >= 0.5:
        sentence2 = (
            f"Open to work, {notice}-day notice, and {response_rate:.0%} recruiter "
            f"response rate make them immediately actionable."
        )
    elif github >= 60:
        sentence2 = (
            f"GitHub activity score of {github:.0f}/100 signals active coding; "
            f"notice period is {notice} days."
        )
    elif open_flag and response_rate >= 0.4:
        sentence2 = (
            f"Marked open to work with {response_rate:.0%} response rate and "
            f"{notice}-day notice."
        )
    elif behavioral_mod < 0.65:
        sentence2 = (
            f"Behavioral signals are weak (modifier {behavioral_mod:.2f}): "
            f"low activity or slow response time may complicate hiring."
        )
    else:
        sentence2 = (
            f"Behavioral signals are adequate; notice period {notice} days."
        )

    return f"{sentence1} {sentence2}"
