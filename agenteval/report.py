"""Markdown + JSON rendering of a score result."""
from __future__ import annotations

import json

from .rubric import Rubric
from .scoring import ScoreResult


def to_markdown(rubric: Rubric, result: ScoreResult, meta: dict[str, str] | None = None) -> str:
    meta = meta or {}
    lines = [f"# Evaluation: {result.rubric_name}", ""]
    for key, value in meta.items():
        lines.append(f"- **{key}**: {value}")
    if meta:
        lines.append("")
    lines.append(f"**Weighted average**: {result.weighted_average} / {rubric.scale_max}")
    lines.append(f"**Normalised**: {result.normalized}/100 → **{result.band}**")
    lines.append("")
    lines.append("| Criterion | Weight | Score | Weighted |")
    lines.append("|---|---:|---:|---:|")
    for criterion in rubric.criteria:
        row = result.per_criterion.get(criterion.id)
        if row is None:
            lines.append(f"| {criterion.title} | {criterion.weight:g} | _missing_ | — |")
        else:
            lines.append(
                f"| {criterion.title} | {criterion.weight:g} | {int(row['score'])} "
                f"| {row['weighted']:g} |"
            )
    if result.missing:
        lines.append("")
        lines.append(f"> Incomplete: {len(result.missing)} criterion/criteria not scored "
                     f"({', '.join(result.missing)}).")
    return "\n".join(lines) + "\n"


def to_json(result: ScoreResult) -> str:
    payload = {
        "rubric": result.rubric_name,
        "weighted_average": result.weighted_average,
        "normalized": result.normalized,
        "band": result.band,
        "complete": result.complete,
        "missing": result.missing,
        "per_criterion": result.per_criterion,
    }
    return json.dumps(payload, indent=2, sort_keys=True)
