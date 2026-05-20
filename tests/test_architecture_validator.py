from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "runtime" / "architecture_validator.py"

spec = importlib.util.spec_from_file_location("architecture_validator", VALIDATOR_PATH)
architecture_validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["architecture_validator"] = architecture_validator
spec.loader.exec_module(architecture_validator)


class ArchitectureValidatorTests(unittest.TestCase):
    def test_repository_architecture_passes(self) -> None:
        report = architecture_validator.validate(ROOT)

        self.assertTrue(report.passed, architecture_validator.format_report(report))

    def test_missing_governance_adlc_binding_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir) / "repo"
            shutil.copytree(ROOT, temp_root)
            target = temp_root / "governance" / "paper_trading_only.md"
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "## ADLC Binding", "## Missing Binding", 1
                ),
                encoding="utf-8",
            )

            report = architecture_validator.validate(temp_root)

        self.assertFalse(report.passed)
        self.assertTrue(
            any(issue.check == "governance_adlc_binding" for issue in report.issues)
        )

    def test_execution_gatekeeper_broad_authority_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir) / "repo"
            shutil.copytree(ROOT, temp_root)
            target = temp_root / "agents" / "08_EXECUTION_GATEKEEPER_AGENT.md"
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "Gate status only. It cannot approve trade quality, cannot approve risk, and cannot approve live or broker execution.",
                    "Gate approval.",
                    1,
                ),
                encoding="utf-8",
            )

            report = architecture_validator.validate(temp_root)

        self.assertFalse(report.passed)
        self.assertTrue(
            any(issue.check == "execution_gatekeeper_authority" for issue in report.issues)
        )

    def test_missing_orchestrator_single_model_block_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir) / "repo"
            shutil.copytree(ROOT, temp_root)
            target = temp_root / "agents" / "00_ORCHESTRATOR.md"
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "- Any workflow asks one model or one agent to perform context analysis, proposal creation, risk approval, execution gatekeeping, and journaling without specialist handoff\n",
                    "",
                    1,
                ),
                encoding="utf-8",
            )

            report = architecture_validator.validate(temp_root)

        self.assertFalse(report.passed)
        self.assertTrue(
            any(issue.check == "orchestrator_single_model_block" for issue in report.issues)
        )


if __name__ == "__main__":
    unittest.main()
