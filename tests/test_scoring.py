import unittest

from agenteval.rubric import build_rubric
from agenteval.scoring import Evaluation, score


def make_rubric():
    return build_rubric({"name": "t", "scale_max": 5, "criteria": [
        {"id": "a", "title": "A", "weight": 3},
        {"id": "b", "title": "B", "weight": 1},
    ]})


class ScoringTests(unittest.TestCase):
    def test_weighted_average_and_normalisation(self):
        # (3*5 + 1*1) / 4 = 4.0 -> (4-1)/4 = 75%
        result = score(make_rubric(), [Evaluation("a", 5), Evaluation("b", 1)])
        self.assertAlmostEqual(result.weighted_average, 4.0)
        self.assertAlmostEqual(result.normalized, 75.0)
        self.assertEqual(result.band, "strong")
        self.assertTrue(result.complete)

    def test_all_best_is_100_and_all_worst_is_0(self):
        best = score(make_rubric(), [Evaluation("a", 5), Evaluation("b", 5)])
        worst = score(make_rubric(), [Evaluation("a", 1), Evaluation("b", 1)])
        self.assertEqual(best.normalized, 100.0)
        self.assertEqual(worst.normalized, 0.0)
        self.assertEqual(worst.band, "unacceptable")

    def test_missing_criterion_is_reported_not_zeroed(self):
        result = score(make_rubric(), [Evaluation("a", 5)])
        self.assertEqual(result.missing, ["b"])
        self.assertFalse(result.complete)
        self.assertAlmostEqual(result.weighted_average, 5.0)

    def test_weights_are_relative(self):
        r1 = build_rubric({"name": "x", "criteria": [
            {"id": "a", "title": "A", "weight": 3}, {"id": "b", "title": "B", "weight": 1}]})
        r2 = build_rubric({"name": "x", "criteria": [
            {"id": "a", "title": "A", "weight": 30}, {"id": "b", "title": "B", "weight": 10}]})
        ev = [Evaluation("a", 3), Evaluation("b", 4)]
        self.assertAlmostEqual(score(r1, ev).normalized, score(r2, ev).normalized)

    def test_rejects_unknown_criterion(self):
        with self.assertRaises(ValueError):
            score(make_rubric(), [Evaluation("zzz", 3)])

    def test_rejects_duplicate_and_out_of_range(self):
        with self.assertRaises(ValueError):
            score(make_rubric(), [Evaluation("a", 3), Evaluation("a", 4)])
        with self.assertRaises(ValueError):
            score(make_rubric(), [Evaluation("a", 9)])

    def test_bands(self):
        cases = {5: "exceptional", 4: "strong", 3: "acceptable", 2: "weak", 1: "unacceptable"}
        for raw, expected in cases.items():
            self.assertEqual(score(make_rubric(), [Evaluation("a", raw), Evaluation("b", raw)]).band,
                             expected)
