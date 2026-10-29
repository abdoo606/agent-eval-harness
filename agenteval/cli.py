"""Command line entry point: python -m agenteval score ..."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .report import to_json, to_markdown
from .rubric import RubricError, load_rubric
from .scoring import Evaluation, score


def _load_evaluations(path: Path) -> list[Evaluation]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw["evaluations"] if isinstance(raw, dict) else raw
    return [
        Evaluation(criterion_id=i["criterion"], score=int(i["score"]), note=i.get("note", ""))
        for i in items
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agenteval", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_score = sub.add_parser("score", help="score one transcript against a rubric")
    p_score.add_argument("--rubric", required=True, type=Path)
    p_score.add_argument("--scores", required=True, type=Path)
    p_score.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    p_score.add_argument("--strict", action="store_true", help="non-zero exit when incomplete")
    p_score.add_argument("--out", type=Path, default=None)

    p_check = sub.add_parser("check-rubric", help="validate a rubric file")
    p_check.add_argument("--rubric", required=True, type=Path)

    args = parser.parse_args(argv)

    if args.command == "check-rubric":
        try:
            rubric = load_rubric(args.rubric)
        except (RubricError, OSError, ValueError) as exc:
            print(f"invalid rubric: {exc}", file=sys.stderr)
            return 1
        print(f"ok: {rubric.name} ({len(rubric.criteria)} criteria, "
              f"total weight {rubric.total_weight():g})")
        return 0

    try:
        rubric = load_rubric(args.rubric)
        result = score(rubric, _load_evaluations(args.scores))
    except (RubricError, OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    text = to_json(result) if args.json else to_markdown(rubric, result)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)

    if args.strict and not result.complete:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
