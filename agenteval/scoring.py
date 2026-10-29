"""Weighted scoring of a single transcript against a rubric."""
from __future__ import annotations

from dataclasses import dataclass, field

from .rubric import Rubric


@dataclass(frozen=True)
class Evaluation:
    """One rater's score for one criterion."""

    criterion_id: str
    score: int
    note: str = ""


@dataclass
class ScoreResult:
    rubric_name: str
    weighted_average: float
    normalized: float  # 0..100
    per_criterion: dict[str, dict[str, float]] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    band: str = ""

    @property
    def complete(self) -> bool:
        return not self.missing


def _band(average: float, scale_max: int) -> str:
    """Map the weighted average onto the rubric's own score anchors.

    Bands are expressed as fractions of the scale (not of the normalised
    0..100 figure) so that "3 out of 5" always means *acceptable* regardless
    of the scale length.
    """
    ratio = average / scale_max
    if ratio >= 0.9:
        return "exceptional"
    if ratio >= 0.7:
        return "strong"
    if ratio >= 0.5:
        return "acceptable"
    if ratio >= 0.3:
        return "weak"
    return "unacceptable"


def score(rubric: Rubric, evaluations: list[Evaluation]) -> ScoreResult:
    """Weighted mean over criteria, normalised to 0..100.

    Weights are relative, so a rubric with weights 3/2/1 and one with 30/20/10
    produce the same result. Missing criteria do not silently count as zero:
    they are reported in ``missing`` and excluded from the mean, which is why
    callers should check ``result.complete`` before trusting the number.
    """
    seen: dict[str, Evaluation] = {}
    for ev in evaluations:
        if ev.criterion_id not in rubric.ids:
            raise ValueError(f"unknown criterion {ev.criterion_id!r}")
        if ev.criterion_id in seen:
            raise ValueError(f"duplicate evaluation for {ev.criterion_id!r}")
        if not rubric.scale_min <= ev.score <= rubric.scale_max:
            raise ValueError(
                f"{ev.criterion_id!r}: score {ev.score} outside "
                f"{rubric.scale_min}..{rubric.scale_max}"
            )
        seen[ev.criterion_id] = ev

    per: dict[str, dict[str, float]] = {}
    weight_sum = 0.0
    weighted_sum = 0.0
    missing: list[str] = []
    for criterion in rubric.criteria:
        ev = seen.get(criterion.id)
        if ev is None:
            missing.append(criterion.id)
            continue
        weight_sum += criterion.weight
        weighted_sum += criterion.weight * ev.score
        per[criterion.id] = {
            "score": float(ev.score),
            "weight": criterion.weight,
            "weighted": criterion.weight * ev.score,
        }

    if weight_sum == 0:
        return ScoreResult(rubric.name, 0.0, 0.0, per, missing, "unacceptable")

    avg = weighted_sum / weight_sum
    span = rubric.scale_max - rubric.scale_min
    normalized = round(100.0 * (avg - rubric.scale_min) / span, 2)
    return ScoreResult(rubric.name, round(avg, 3), normalized, per, missing,
                       _band(avg, rubric.scale_max))
