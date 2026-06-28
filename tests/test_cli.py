import subprocess
import sys
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

if __name__ == "__main__":
    unittest.main()
