"""Rubric model + validation.

A rubric is a named set of weighted criteria scored on a 1..scale_max scale.
Weights are relative, not required to sum to 1.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class RubricError(ValueError):
    """Raised when a rubric definition is invalid."""


@dataclass(frozen=True)
class Criterion:
    id: str
    title: str
    weight: float
    description: str = ""
    anchors: dict[int, str] = field(default_factory=dict)

    def anchor_for(self, score: int) -> str:
        return self.anchors.get(score, "")


@dataclass(frozen=True)
class Rubric:
    name: str
    criteria: tuple[Criterion, ...]
    scale_max: int = 5
    scale_min: int = 1

    def get(self, criterion_id: str) -> Criterion:
        for c in self.criteria:
            if c.id == criterion_id:
                return c
        raise KeyError(criterion_id)

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(c.id for c in self.criteria)

    def total_weight(self) -> float:
        return sum(c.weight for c in self.criteria)


def _parse_criterion(raw: dict[str, Any], scale_max: int) -> Criterion:
    missing = {"id", "title", "weight"} - raw.keys()
    if missing:
        raise RubricError(f"criterion missing keys: {sorted(missing)}")
    weight = float(raw["weight"])
    if weight <= 0:
        raise RubricError(f"criterion {raw['id']!r}: weight must be > 0, got {weight}")
    anchors = {int(k): str(v) for k, v in (raw.get("anchors") or {}).items()}
    bad = [s for s in anchors if s < 1 or s > scale_max]
    if bad:
        raise RubricError(f"criterion {raw['id']!r}: anchor scores out of range {bad}")
    return Criterion(
        id=str(raw["id"]),
        title=str(raw["title"]),
        weight=weight,
        description=str(raw.get("description", "")),
        anchors=anchors,
    )


def build_rubric(data: dict[str, Any]) -> Rubric:
    if "criteria" not in data or not data["criteria"]:
        raise RubricError("rubric needs a non-empty 'criteria' list")
    scale_max = int(data.get("scale_max", 5))
    if scale_max < 2:
        raise RubricError("scale_max must be >= 2")
    criteria = tuple(_parse_criterion(c, scale_max) for c in data["criteria"])
    ids = [c.id for c in criteria]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise RubricError(f"duplicate criterion ids: {dupes}")
    return Rubric(name=str(data.get("name", "unnamed")), criteria=criteria, scale_max=scale_max)


def load_rubric(path: str | Path) -> Rubric:
    return build_rubric(json.loads(Path(path).read_text(encoding="utf-8")))
