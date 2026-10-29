import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agenteval.cli import main
from agenteval.report import to_json, to_markdown
from agenteval.rubric import load_rubric
from agenteval.scoring import Evaluation, score

ROOT = Path(__file__).resolve().parents[1]


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.rubric = load_rubric(ROOT / "sample_data" / "rubric.json")
        self.result = score(self.rubric, [
            Evaluation("problem_framing", 4),
            Evaluation("verification", 5),
            Evaluation("scope_control", 3),
            Evaluation("communication", 4),
        ])

    def test_markdown_lists_every_criterion(self):
        md = to_markdown(self.rubric, self.result, {"transcript": "t-1"})
        for criterion in self.rubric.criteria:
            self.assertIn(criterion.title, md)
        self.assertIn("**strong**", md)
        self.assertIn("t-1", md)

    def test_markdown_flags_missing(self):
        partial = score(self.rubric, [Evaluation("verification", 4)])
        self.assertIn("Incomplete", to_markdown(self.rubric, partial))

    def test_json_roundtrip(self):
        payload = json.loads(to_json(self.result))
        self.assertTrue(payload["complete"])
        self.assertEqual(payload["band"], "strong")


class CliTests(unittest.TestCase):
    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_score_markdown(self):
        code, out, _ = self.run_cli([
            "score", "--rubric", str(ROOT / "sample_data" / "rubric.json"),
            "--scores", str(ROOT / "sample_data" / "scores.json"),
        ])
        self.assertEqual(code, 0)
        self.assertIn("Evaluation:", out)

    def test_score_json_and_out_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "r.json"
            code, out, _ = self.run_cli([
                "score", "--rubric", str(ROOT / "sample_data" / "rubric.json"),
                "--scores", str(ROOT / "sample_data" / "scores.json"),
                "--json", "--out", str(dest),
            ])
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            self.assertIn("normalized", dest.read_text(encoding="utf-8"))

    def test_strict_incomplete_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "s.json"
            scores.write_text(json.dumps([{"criterion": "verification", "score": 4}]),
                              encoding="utf-8")
            code, _, _ = self.run_cli([
                "score", "--rubric", str(ROOT / "sample_data" / "rubric.json"),
                "--scores", str(scores), "--strict",
            ])
            self.assertEqual(code, 1)

    def test_invalid_rubric_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text('{"criteria": []}', encoding="utf-8")
            code, _, err = self.run_cli(["check-rubric", "--rubric", str(bad)])
            self.assertEqual(code, 1)
            self.assertIn("invalid rubric", err)
