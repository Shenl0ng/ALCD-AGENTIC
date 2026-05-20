from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EnvironmentHygieneTests(unittest.TestCase):
    def test_gitignore_ignores_local_env_files_but_allows_example(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn(".env", gitignore)
        self.assertIn(".env.*", gitignore)
        self.assertIn("!.env.example", gitignore)

    def test_env_example_contains_placeholders_only(self) -> None:
        env_example = (ROOT / ".env.example").read_text(encoding="utf-8")

        self.assertIn("ALPACA_API_KEY_ID=", env_example)
        self.assertIn("ALPACA_API_SECRET_KEY=", env_example)
        self.assertIn("ALPACA_PAPER=true", env_example)
        self.assertIn("PAPER_ORDER_EXECUTION_ENABLED=false", env_example)
        self.assertNotIn("APCA-", env_example)

    def test_sensitive_env_files_are_not_tracked(self) -> None:
        if not (ROOT / ".git").exists():
            return

        completed = subprocess.run(
            ["git", "ls-files", "--", ".env", ".env.local", ".env.*"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        tracked = {
            line.strip()
            for line in completed.stdout.splitlines()
            if line.strip() and line.strip() != ".env.example"
        }

        self.assertEqual(tracked, set())


if __name__ == "__main__":
    unittest.main()
