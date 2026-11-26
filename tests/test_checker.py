import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proposal_checker import check_proposal  # noqa: E402

EX = ROOT / "examples"
JOB = (EX / "job.txt").read_text()
GOOD = (EX / "good.txt").read_text()
BAD = (EX / "bad.txt").read_text()


def part(report, name):
    return next(c for c in report.checks if c.name == name)


class CheckerTests(unittest.TestCase):
    def test_good_proposal_grades_a(self):
        r = check_proposal(GOOD, JOB)
        self.assertGreaterEqual(r.total, 85, r.as_dict())
        self.assertEqual(r.grade, "A")
        self.assertEqual(r.fixes, [])

    def test_bad_proposal_grades_d_with_fixes(self):
        r = check_proposal(BAD, JOB)
        self.assertLess(r.total, 55)
        self.assertEqual(r.grade, "D")
        self.assertTrue(r.fixes)

    def test_stock_opener_loses_hook_points(self):
        r = check_proposal("Dear Hiring Manager, I am a senior developer.\n\nThanks.", JOB)
        self.assertLessEqual(part(r, "hook").points, 15)

    def test_satisfaction_promise_is_not_proof(self):
        r = check_proposal("I deliver 100% satisfaction on every job.", JOB)
        self.assertEqual(part(r, "proof").points, 0)

    def test_question_at_end_scores_ask(self):
        r = check_proposal("Your checkout is slow. Which apps did you add last?", JOB)
        self.assertEqual(part(r, "ask").points, 15)

    def test_without_job_relevance_is_neutral(self):
        r = check_proposal(GOOD)
        self.assertEqual(part(r, "relevance").points, 10)

    def test_points_within_bounds(self):
        for text in (GOOD, BAD, "", "?"):
            for c in check_proposal(text, JOB).checks:
                self.assertGreaterEqual(c.points, 0)
                self.assertLessEqual(c.points, c.max_points)

    def test_cli_min_exit_code(self):
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        cmd = [sys.executable, "-m", "proposal_checker.cli", str(EX / "bad.txt"), "--job", str(EX / "job.txt")]
        self.assertEqual(subprocess.run(cmd + ["--min", "70"], capture_output=True, env=env).returncode, 1)
        out = subprocess.run(cmd + ["--json"], capture_output=True, text=True, env=env, check=True)
        self.assertIn("total", json.loads(out.stdout))


if __name__ == "__main__":
    unittest.main()
