"""
scorer/behavioral.py
--------------------
Behavioral signal modifier for the Senior AI Engineer JD.

This is a MULTIPLICATIVE modifier applied to the base score.
Range: BEHAVIORAL_MIN to BEHAVIORAL_MAX (defined in jd_config).

Rationale (from redrob_signals_doc + JD):
  "A perfect-on-paper candidate who hasn't logged in for 6 months and has
   a 5% response rate is, for hiring purposes, not actually available."

The modifier rewards candidates who:
  - Are actively in the market (open_to_work, recent login)
  - Respond to recruiters quickly
  - Complete interviews reliably
  - Have short notice periods (≤30 days preferred, up to 30 buyout)
  - Show GitHub activity (actively coding)
  - Have a verified, complete profile (trust signal)

Score architecture:
  sub-score = weighted_average(all signal scores)
  modifier = BEHAVIORAL_MIN + (BEHAVIORAL_MAX - BEHAVIORAL_MIN) × sub_score
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Any

from jd_config import BEHAVIORAL_MIN, BEHAVIORAL_MAX


def _days_since(date_str: str | None) -> int:
    """Days since a date string (YYYY-MM-DD). Returns 9999 if None/invalid."""
    if not date_str:
        return 9999
    try:
        d = date.fromisoformat(date_str)
        return (date.today() - d).days
    except (ValueError, TypeError):
        return 9999


def _recency_score(days: int) -> float:
    """How recently did the candidate log in?"""
    if days < 7:
        return 1.00
    elif days < 30:
        return 0.95
    elif days < 60:
        return 0.85
    elif days < 90:
        return 0.72
    elif days < 180:
        return 0.50
    elif days < 365:
        return 0.30
    else:
        return 0.10


def _response_time_score(hours: float) -> float:
    """Faster response = better signal of engagement."""
    if hours <= 4:
        return 1.00
    elif hours <= 24:
        return 0.90
    elif hours <= 72:
        return 0.75
    elif hours <= 168:
        return 0.55
    elif hours <= 336:
        return 0.35
    else:
        return 0.15


def _notice_period_score(days: int) -> float:
    """JD prefers sub-30 days; can buy out up to 30 days."""
    if days == 0:
        return 1.00
    elif days <= 15:
        return 0.97
    elif days <= 30:
        return 0.92
    elif days <= 60:
        return 0.75
    elif days <= 90:
        return 0.55
    else:
        return 0.30


def _github_score(raw: float) -> float:
    """github_activity_score: -1 means no GitHub linked."""
    if raw < 0:
        return 0.50  # no GitHub — neutral, slight negative
    elif raw < 20:
        return 0.60
    elif raw < 50:
        return 0.78
    elif raw < 75:
        return 0.90
    else:
        return 1.00


def compute_behavioral_modifier(candidate: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """
    Returns (modifier value, debug_info dict).
    modifier range: BEHAVIORAL_MIN – BEHAVIORAL_MAX
    """
    signals = candidate.get("redrob_signals", {})

    # ---- individual signal scores ----------------------------------------
    open_to_work = bool(signals.get("open_to_work_flag", False))
    open_score = 1.0 if open_to_work else 0.50

    last_active = signals.get("last_active_date")
    recency = _recency_score(_days_since(last_active))

    response_rate = float(signals.get("recruiter_response_rate") or 0)
    response_time_h = float(signals.get("avg_response_time_hours") or 999)
    response_time_score = _response_time_score(response_time_h)

    interview_rate = float(signals.get("interview_completion_rate") or 0)

    offer_rate_raw = float(signals.get("offer_acceptance_rate") or -1)
    offer_score = (offer_rate_raw if offer_rate_raw >= 0 else 0.65)  # -1 → neutral

    notice_days = int(signals.get("notice_period_days") or 60)
    notice_score = _notice_period_score(notice_days)

    github_raw = float(signals.get("github_activity_score") or -1)
    github = _github_score(github_raw)

    completeness = float(signals.get("profile_completeness_score") or 50) / 100.0

    verified_email = bool(signals.get("verified_email", False))
    verified_phone = bool(signals.get("verified_phone", False))
    linkedin = bool(signals.get("linkedin_connected", False))
    trust = (
        0.4 * (1.0 if verified_email else 0.0)
        + 0.3 * (1.0 if verified_phone else 0.0)
        + 0.3 * (1.0 if linkedin else 0.0)
    )

    # Recruiter interest signals
    saved_by = int(signals.get("saved_by_recruiters_30d") or 0)
    saved_score = min(saved_by / 10.0, 1.0)  # saturates at 10 saves

    # ---- weighted sub-score ----------------------------------------------
    # Weights reflect importance to "can we actually hire this person?"
    sub_score = (
        0.18 * open_score           # Are they looking?
        + 0.16 * recency            # Are they active?
        + 0.14 * response_rate      # Do they respond?
        + 0.10 * response_time_score  # How fast?
        + 0.10 * interview_rate     # Do they show up?
        + 0.10 * notice_score       # How soon can they start?
        + 0.08 * github             # Are they coding actively?
        + 0.07 * completeness       # Profile quality
        + 0.05 * trust              # Verification
        + 0.02 * saved_score        # Recruiter interest
    )

    # Map sub_score (0-1) → modifier range
    modifier = BEHAVIORAL_MIN + (BEHAVIORAL_MAX - BEHAVIORAL_MIN) * sub_score
    modifier = round(max(BEHAVIORAL_MIN, min(BEHAVIORAL_MAX, modifier)), 4)

    debug = {
        "open_to_work": open_to_work,
        "last_active_date": last_active,
        "recency_score": round(recency, 3),
        "response_rate": response_rate,
        "response_time_h": response_time_h,
        "interview_completion_rate": interview_rate,
        "notice_period_days": notice_days,
        "notice_score": round(notice_score, 3),
        "github_raw": github_raw,
        "github_score": round(github, 3),
        "profile_completeness": completeness,
        "trust_score": round(trust, 3),
        "sub_score": round(sub_score, 4),
        "modifier": modifier,
    }

    return modifier, debug
