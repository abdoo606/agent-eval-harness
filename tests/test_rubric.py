import json
import tempfile
import unittest
from pathlib import Path

from agenteval.rubric import RubricError, build_rubric, load_rubric


def rubric(**over):
    data = {
        "name": "r",
        "scale_max": 5,
        "criteria": [
            {"id": "a", "title": "A", "weight": 1},
            {"id": "b", "title": "B", "weight": 2},
        ],
    }
    data.update(over)
    return data


class RubricValidationTests(unittest.TestCase):
    def test_builds_and_exposes_ids(self):
        r = build_rubric(rubric())
        self.assertEqual(r.ids, ("a", "b"))
        self.assertEqual(r.total_weight(), 3.0)
        self.assertEqual(r.get("b").title, "B")

    def test_rejects_duplicate_ids(self):
        data = rubric(criteria=[{"id": "a", "title": "A", "weight": 1},
                                {"id": "a", "title": "A2", "weight": 1}])
        with self.assertRaises(RubricError):
            build_rubric(data)

    def test_rejects_non_positive_weight(self):
        with self.assertRaises(RubricError):
            build_rubric(rubric(criteria=[{"id": "a", "title": "A", "weight": 0}]))

    def test_rejects_empty_criteria(self):
        with self.assertRaises(RubricError):
            build_rubric(rubric(criteria=[]))

    def test_rejects_anchor_out_of_range(self):
        with self.assertRaises(RubricError):
            build_rubric(rubric(criteria=[{"id": "a", "title": "A", "weight": 1,
                                           "anchors": {"9": "too high"}}]))

    def test_anchor_lookup(self):
        r = build_rubric(rubric(criteria=[{"id": "a", "title": "A", "weight": 1,
                                           "anchors": {"3": "ok"}}]))
        self.assertEqual(r.get("a").anchor_for(3), "ok")
        self.assertEqual(r.get("a").anchor_for(5), "")

    def test_load_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text(json.dumps(rubric()), encoding="utf-8")
            self.assertEqual(load_rubric(path).name, "r")
