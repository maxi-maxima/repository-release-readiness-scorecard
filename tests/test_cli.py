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

if __name__ == "__main__":
    unittest.main()
