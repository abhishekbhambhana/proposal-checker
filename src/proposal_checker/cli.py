"""Command line.

    proposal-checker proposal.txt --job job.txt
    cat proposal.txt | proposal-checker - --json
"""
from __future__ import annotations

import argparse
import json
import sys

from .checker import check_proposal


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="proposal-checker", description="Grade an Upwork proposal 0 to 100.")
    ap.add_argument("proposal", help="text file with the proposal ('-' for stdin)")
    ap.add_argument("--job", help="text file with the job post, for hook and relevance checks")
    ap.add_argument("--json", action="store_true", help="print JSON")
    ap.add_argument("--min", type=int, default=0, help="exit 1 if the score is below this (for scripts)")
    args = ap.parse_args(argv)

    report = check_proposal(_read(args.proposal), _read(args.job) if args.job else "")

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(f"\n{report.total}/100  [{report.grade}]  {report.words} words\n")
        for c in report.checks:
            filled = int(round(16 * c.points / c.max_points))
            print(f"  {c.name:<10} {'#' * filled}{'.' * (16 - filled)} {c.points:>4.0f}/{c.max_points:<3.0f} {'; '.join(c.notes)}")
        if report.fixes:
            print("\n  Fix first:")
            for i, fix in enumerate(report.fixes, 1):
                print(f"  {i}. {fix}")
        print()
    return 1 if report.total < args.min else 0


if __name__ == "__main__":
    raise SystemExit(main())
