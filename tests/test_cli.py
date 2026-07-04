import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CliExampleTest(unittest.TestCase):
    def test_cli_example(self):
        proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', 'examples/sample-repo'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        code = proc.returncode
        out = proc.stdout
        err = proc.stderr
        self.assertEqual(err, "")
        self.assertEqual(code, 0)
        self.assertIn("Score: 100/100", out)

    def test_json_includes_recommendations_for_missing_checks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "README.md").write_text("short", encoding="utf-8")
            proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', temp_dir, '--json'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        readme_check = next(check for check in payload["checks"] if check["check"] == "README.md")
        license_check = next(check for check in payload["checks"] if check["check"] == "LICENSE")
        self.assertFalse(readme_check["passed"])
        self.assertIn("README over 500 characters", readme_check["recommendation"])
        self.assertIn("LICENSE file", license_check["recommendation"])

    def test_min_score_can_relax_ci_gate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "README.md").write_text("short", encoding="utf-8")
            proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', temp_dir, '--min-score', '0'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Score: 0/100", proc.stdout)

    def test_min_score_rejects_out_of_range_values(self):
        proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', 'examples/sample-repo', '--min-score', '101'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--min-score must be between 0 and 100", proc.stderr)

    def test_require_check_fails_even_when_min_score_is_relaxed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "README.md").write_text("short", encoding="utf-8")
            proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', temp_dir, '--min-score', '0', '--require-check', 'LICENSE'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("Required checks failed: LICENSE", proc.stdout)

    def test_require_check_is_included_in_json_output(self):
        proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', 'examples/sample-repo', '--require-check', 'LICENSE', '--json'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["required_checks"], ["LICENSE"])
        self.assertEqual(payload["failed_required_checks"], [])

if __name__ == "__main__":
    unittest.main()
