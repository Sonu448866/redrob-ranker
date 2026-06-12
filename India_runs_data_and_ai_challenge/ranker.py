"""
ranker.py
---------
Core Ranker class — orchestrates all scoring components and produces
a ranked list of candidates for the Senior AI Engineer JD.

Pipeline:
  1. Stream / load candidates (JSONL or JSON)
  2. Honeypot detection → flag impossible profiles
  3. Per-component scoring (skills, career, experience, education, location)
  4. Behavioral signal modifier (multiplicative)
  5. Semantic TF-IDF boost (additive, small)
  6. Composite final score
  7. Sort, take top 100, generate reasoning
"""

from __future__ import annotations
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Iterator

from jd_config import COMPONENT_WEIGHTS
from scorer.honeypot import detect_honeypot
from scorer.skills import compute_skills_score
from scorer.career import compute_career_score
from scorer.experience import compute_experience_score
from scorer.education import compute_education_score
from scorer.location import compute_location_score
from scorer.behavioral import compute_behavioral_modifier
from scorer.semantic import batch_compute_semantic_scores
from reasoning import generate_reasoning

logger = logging.getLogger(__name__)

# Honeypot candidates receive this score cap (well below any real candidate)
HONEYPOT_SCORE_CAP = 0.001

# Semantic boost max contribution to final score
SEMANTIC_BOOST_MAX = 0.10

# Batch size for semantic scoring (memory-efficient)
SEMANTIC_BATCH_SIZE = 5000


def _load_candidates(path: str | Path) -> Iterator[dict[str, Any]]:
    """Stream candidates from a .jsonl or .jsonl.gz file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Candidates file not found: {path}")

    if p.suffix == ".gz":
        import gzip
        opener = lambda: gzip.open(p, "rt", encoding="utf-8")
    else:
        opener = lambda: open(p, "r", encoding="utf-8")

    with opener() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed line: {e}")


def _score_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """
    Compute all component scores for a single candidate.
    Returns a result dict with all scores + the candidate_id.
    """
    cid = candidate.get("candidate_id", "UNKNOWN")

    # ---- Honeypot check ------------------------------------------------
    is_honeypot, honeypot_reason = detect_honeypot(candidate)

    # ---- Component scores ----------------------------------------------
    skills_score, skills_debug = compute_skills_score(candidate)
    career_score, career_debug = compute_career_score(candidate)
    exp_score, exp_debug = compute_experience_score(candidate)
    edu_score, edu_debug = compute_education_score(candidate)
    loc_score, loc_debug = compute_location_score(candidate)
    behavioral_mod, beh_debug = compute_behavioral_modifier(candidate)

    # ---- Base score (weighted sum) -------------------------------------
    w = COMPONENT_WEIGHTS
    base_score = (
        w["skills"] * skills_score
        + w["career"] * career_score
        + w["experience"] * exp_score
        + w["education"] * edu_score
        + w["location"] * loc_score
    )

    # ---- Final score (before semantic) ---------------------------------
    if is_honeypot:
        final_score = HONEYPOT_SCORE_CAP
    else:
        final_score = base_score * behavioral_mod
        final_score = max(0.0, min(1.0, final_score))

    return {
        "candidate_id": cid,
        "candidate": candidate,        # Keep reference for reasoning generation
        "is_honeypot": is_honeypot,
        "honeypot_reason": honeypot_reason,
        "skills_score": round(skills_score, 6),
        "career_score": round(career_score, 6),
        "experience_score": round(exp_score, 6),
        "education_score": round(edu_score, 6),
        "location_score": round(loc_score, 6),
        "behavioral_modifier": round(behavioral_mod, 6),
        "base_score": round(base_score, 6),
        "final_score": round(final_score, 6),
        # debug
        "skills_debug": skills_debug,
        "career_debug": career_debug,
        "exp_debug": exp_debug,
        "edu_debug": edu_debug,
        "loc_debug": loc_debug,
        "beh_debug": beh_debug,
    }


class Ranker:
    """
    Main ranker class.

    Usage:
        ranker = Ranker()
        results = ranker.rank(candidates_path)
        ranker.save_csv(results, output_path)
    """

    def __init__(self, top_k: int = 100, verbose: bool = True):
        self.top_k = top_k
        self.verbose = verbose

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg, flush=True)

    def rank(self, candidates_path: str | Path) -> list[dict[str, Any]]:
        """
        Full pipeline: load → score → semantic boost → sort → top_k.
        Returns sorted list of result dicts (best first).
        """
        t0 = time.time()
        self._log("🔍 Loading and scoring candidates…")

        # ---- Phase 1: score all candidates --------------------------------
        all_results: list[dict[str, Any]] = []
        n_total = 0
        n_honeypot = 0

        for i, candidate in enumerate(_load_candidates(candidates_path)):
            result = _score_candidate(candidate)
            all_results.append(result)
            n_total += 1
            if result["is_honeypot"]:
                n_honeypot += 1
            if self.verbose and n_total % 10_000 == 0:
                elapsed = time.time() - t0
                self._log(
                    f"  Scored {n_total:,} candidates in {elapsed:.1f}s "
                    f"({n_honeypot} honeypots detected)…"
                )

        t1 = time.time()
        self._log(
            f"✅ Scored {n_total:,} candidates in {t1 - t0:.1f}s "
            f"({n_honeypot} honeypots detected)"
        )

        # ---- Phase 2: sort to get top candidates before semantic ----------
        # We do semantic scoring only on top candidates (much faster)
        all_results.sort(key=lambda r: r["final_score"], reverse=True)

        # Take top 500 for semantic re-ranking (not all 100K — too slow for TF-IDF on 100K)
        # Actually, TF-IDF on 100K is fast enough (~10-20s). We do all of them.
        self._log("🧠 Computing TF-IDF semantic similarities…")
        t2 = time.time()

        # Process in batches to manage memory
        # We only need semantic scores for candidates that could enter top-k
        # But computing all gives us a better TF-IDF vocabulary fit
        # Compromise: score top 5000 only
        TOP_FOR_SEMANTIC = min(5000, len(all_results))
        semantic_candidates = [r["candidate"] for r in all_results[:TOP_FOR_SEMANTIC]]

        if semantic_candidates:
            sem_scores = batch_compute_semantic_scores(semantic_candidates)
            for idx, sem_score in enumerate(sem_scores):
                # Add semantic boost (max SEMANTIC_BOOST_MAX contribution)
                boost = min(sem_score, 1.0) * SEMANTIC_BOOST_MAX
                old_score = all_results[idx]["final_score"]
                if not all_results[idx]["is_honeypot"]:
                    new_score = min(old_score + boost, 1.0)
                    all_results[idx]["final_score"] = round(new_score, 6)
                    all_results[idx]["semantic_score"] = round(sem_score, 6)
                    all_results[idx]["semantic_boost"] = round(boost, 6)

        t3 = time.time()
        self._log(f"✅ Semantic scoring complete in {t3 - t2:.1f}s")

        # ---- Phase 3: final sort and top-k --------------------------------
        all_results.sort(key=lambda r: r["final_score"], reverse=True)
        top_results = all_results[: self.top_k]

        self._log(f"🏆 Top {self.top_k} selected. Generating reasoning…")

        # ---- Phase 4: generate reasoning for top-k ------------------------
        for rank_idx, result in enumerate(top_results):
            rank = rank_idx + 1
            reasoning = generate_reasoning(
                candidate=result["candidate"],
                rank=rank,
                scores=result,
            )
            result["rank"] = rank
            result["reasoning"] = reasoning

        t_end = time.time()
        self._log(f"🎉 Total pipeline time: {t_end - t0:.1f}s")

        # Summary stats for top-10
        self._log("\n📊 Top 10 summary:")
        for r in top_results[:10]:
            p = r["candidate"].get("profile", {})
            self._log(
                f"  #{r['rank']:2d} {r['candidate_id']} | "
                f"{p.get('current_title','?'):35s} | "
                f"score={r['final_score']:.4f} | "
                f"{'⚠️ honeypot' if r['is_honeypot'] else ''}"
            )

        return top_results

    def save_csv(
        self,
        results: list[dict[str, Any]],
        output_path: str | Path,
    ) -> None:
        """Write the ranked list to a CSV file in the required format."""
        import csv

        output_path = Path(output_path)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["candidate_id", "rank", "score", "reasoning"])
            for r in results:
                # Format score to 4 decimal places
                score_str = f"{r['final_score']:.4f}"
                reasoning = r.get("reasoning", "")
                # Escape any newlines in reasoning
                reasoning = reasoning.replace("\n", " ").replace("\r", " ")
                writer.writerow([
                    r["candidate_id"],
                    r["rank"],
                    score_str,
                    reasoning,
                ])

        print(f"✅ Submission written to: {output_path}")
        print(f"   Rows: {len(results)}")
        if results:
            print(f"   Score range: {results[-1]['final_score']:.4f} – {results[0]['final_score']:.4f}")
