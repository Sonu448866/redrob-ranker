#!/usr/bin/env python3
"""
rank.py
-------
CLI entry point for the Redrob Intelligent Candidate Ranking system.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv
    python rank.py --candidates ./candidates.jsonl.gz --out ./submission.csv --verbose

Compute constraints (per submission spec):
  ≤5 min wall-clock, ≤16 GB RAM, CPU only, no network during ranking.
"""

import argparse
import logging
import sys
from pathlib import Path

# Enforce UTF-8 encoding for standard output on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def parse_args():
    parser = argparse.ArgumentParser(
        description="Redrob AI — Intelligent Candidate Ranker (Senior AI Engineer JD)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rank.py --candidates ./candidates.jsonl --out ./submission.csv
  python rank.py --candidates ./candidates.jsonl.gz --out ./submission.csv
  python rank.py --candidates ./sample_candidates.json --out ./test_output.csv
        """,
    )
    parser.add_argument(
        "--candidates",
        required=True,
        help="Path to candidates file (.jsonl, .jsonl.gz, or .json)",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output CSV path for the ranked submission",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=100,
        help="Number of top candidates to output (default: 100)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Print progress (default: True)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress all output except errors",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    verbose = args.verbose and not args.quiet

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    candidates_path = Path(args.candidates)
    output_path = Path(args.out)

    # Support .json (list) files too — for sample_candidates.json
    if candidates_path.suffix == ".json":
        import json, tempfile, os
        if verbose:
            print(f"📂 Converting {candidates_path.name} (.json list) to JSONL…")
        with open(candidates_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Write to a temp JSONL
        tmp_path = candidates_path.with_suffix(".jsonl.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        candidates_path = tmp_path
        cleanup_tmp = True
    else:
        cleanup_tmp = False

    if verbose:
        print("=" * 60)
        print("  Redrob AI — Intelligent Candidate Ranking System")
        print("  Role: Senior AI Engineer (Founding Team)")
        print("=" * 60)
        print(f"  Candidates: {args.candidates}")
        print(f"  Output:     {output_path}")
        print(f"  Top-K:      {args.top_k}")
        print("=" * 60)

    try:
        from ranker import Ranker

        ranker = Ranker(top_k=args.top_k, verbose=verbose)
        results = ranker.rank(candidates_path)
        ranker.save_csv(results, output_path)

        if verbose:
            print(f"\n✅ Done! Submission saved to: {output_path}")
            print(f"   Run validation: python validate_submission.py {output_path}")

    finally:
        if cleanup_tmp and candidates_path.exists():
            candidates_path.unlink()


if __name__ == "__main__":
    main()
