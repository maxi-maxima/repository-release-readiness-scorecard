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
        self.assertIn("Score: 100/100 (100%, ready)", out)

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
        self.assertIn("0%, not-ready", proc.stdout)

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

    def test_markdown_output_is_pr_ready(self):
        proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', 'examples/sample-repo', '--markdown'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("## Release Readiness Score", proc.stdout)
        self.assertIn("**Score:** 100/100 (100%, ready)", proc.stdout)
        self.assertIn("| Check | Result | Points | Recommendation |", proc.stdout)
        self.assertIn("| README.md | pass | 20/20 |  |", proc.stdout)

    def test_output_writes_selected_report_to_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir, "readiness.md")
            proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', 'examples/sample-repo', '--markdown', '--output', str(output_path)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

            self.assertEqual(proc.stderr, "")
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), proc.stdout)
            self.assertIn("## Release Readiness Score", output_path.read_text(encoding="utf-8"))


    def test_artifact_check_reports_unignored_cache_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "README.md").write_text("x" * 600, encoding="utf-8")
            cache_dir = Path(temp_dir, "__pycache__")
            cache_dir.mkdir()
            Path(cache_dir, "mod.cpython-311.pyc").write_bytes(b"cache")
            proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', temp_dir, '--artifact-check', '--json', '--min-score', '0'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["artifact_check_passed"])
        self.assertEqual(payload["artifact_findings"], ["__pycache__/mod.cpython-311.pyc"])

    def test_fail_on_artifacts_returns_dedicated_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "README.md").write_text("x" * 600, encoding="utf-8")
            Path(temp_dir, "debug.log").write_text("debug", encoding="utf-8")
            proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', temp_dir, '--fail-on-artifacts', '--min-score', '0'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 4)
        self.assertIn("✗ generated artifacts 1 finding(s)", proc.stdout)

    def test_artifact_check_respects_gitignore_patterns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "README.md").write_text("x" * 600, encoding="utf-8")
            Path(temp_dir, ".gitignore").write_text("*.log\n__pycache__/\n", encoding="utf-8")
            cache_dir = Path(temp_dir, "__pycache__")
            cache_dir.mkdir()
            Path(cache_dir, "mod.cpython-311.pyc").write_bytes(b"cache")
            Path(temp_dir, "debug.log").write_text("debug", encoding="utf-8")
            proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', temp_dir, '--artifact-check', '--json', '--min-score', '0'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["artifact_check_passed"])
        self.assertEqual(payload["artifact_findings"], [])

    def test_ignore_check_excludes_not_applicable_artifact_from_score(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "README.md").write_text("release " * 100, encoding="utf-8")
            Path(temp_dir, "LICENSE").write_text("MIT", encoding="utf-8")
            Path(temp_dir, ".gitignore").write_text("__pycache__/", encoding="utf-8")
            Path(temp_dir, "tests").mkdir()
            Path(temp_dir, "README.zh-CN.md").write_text("说明", encoding="utf-8")
            Path(temp_dir, "pyproject.toml").write_text("[project]\nname='demo'", encoding="utf-8")
            proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', temp_dir, '--ignore-check', 'examples', '--json'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["score"], 85)
        self.assertEqual(payload["max_score"], 85)
        self.assertEqual(payload["score_percent"], 100)
        self.assertEqual(payload["ignored_checks"], ["examples"])

    def test_required_check_ignored_is_not_failed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proc = subprocess.run(['python', '-m', 'repository_release_readiness_scorecard', temp_dir, '--min-score', '0', '--require-check', 'examples', '--ignore-check', 'examples'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        self.assertEqual(proc.stderr, "")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Ignored checks: examples", proc.stdout)

if __name__ == "__main__":
    unittest.main()
