"""
scorer/location.py
------------------
Location and availability score for the Senior AI Engineer JD.

JD says:
  Preferred: Pune / Noida
  Acceptable: Hyderabad, Mumbai, Delhi NCR, Bangalore
  Open to relocation candidates from Tier-1 Indian cities
  Outside India: case-by-case (no visa sponsorship)

Availability factors:
  - preferred_work_mode: hybrid/flexible = perfect fit; onsite = fine; remote = slight risk
  - willing_to_relocate: positive signal if not already in Pune/Noida

Score: 0.0 – 1.0
"""

from __future__ import annotations
from typing import Any

from jd_config import PREFERRED_LOCATIONS, ACCEPTABLE_LOCATIONS

# Work mode compatibility with the JD (hybrid-flexible company)
WORK_MODE_SCORES = {
    "hybrid": 1.00,
    "flexible": 0.95,
    "onsite": 0.85,
    "remote": 0.65,  # company is hybrid; remote-only candidate = mild risk
}

TIER1_INDIA_CITIES = {
    "mumbai", "delhi", "bengaluru", "bangalore", "hyderabad", "pune",
    "chennai", "kolkata", "ahmedabad", "surat", "jaipur", "lucknow",
    "kanpur", "nagpur", "noida", "gurugram", "gurgaon", "faridabad",
    "meerut", "indore", "bhopal", "patna", "vadodara",
}

OTHER_INDIA_CITIES_KEYWORDS = ["india"]


def _location_score(location: str, country: str, willing_to_relocate: bool) -> float:
    """
    Returns a raw location score before work-mode adjustment.
    """
    loc = (location or "").lower()
    ctry = (country or "").lower()

    # Preferred cities
    if any(p in loc for p in PREFERRED_LOCATIONS):
        return 1.0

    # Acceptable cities
    if any(a in loc for a in ACCEPTABLE_LOCATIONS):
        return 0.88

    # Tier-1 Indian city (willing to relocate)
    if "india" in ctry or ctry == "in":
        if any(t in loc for t in TIER1_INDIA_CITIES):
            base = 0.78
        else:
            base = 0.65  # smaller Indian city
        if willing_to_relocate:
            base = min(base + 0.12, 0.95)
        return base

    # Outside India
    if willing_to_relocate:
        return 0.48  # still a stretch
    return 0.30


def compute_location_score(candidate: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """
    Returns (score 0-1, debug_info dict).
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    location = profile.get("location") or ""
    country = profile.get("country") or ""
    willing = bool(signals.get("willing_to_relocate", False))
    work_mode = (signals.get("preferred_work_mode") or "flexible").lower()

    loc_score = _location_score(location, country, willing)
    mode_score = WORK_MODE_SCORES.get(work_mode, 0.80)

    # Combined: location matters more
    final_score = 0.75 * loc_score + 0.25 * mode_score

    debug = {
        "location": location,
        "country": country,
        "willing_to_relocate": willing,
        "work_mode": work_mode,
        "location_raw_score": round(loc_score, 4),
        "mode_score": round(mode_score, 4),
        "final_score": round(final_score, 4),
    }

    return min(final_score, 1.0), debug
