from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime"

if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))


def load_module(name: str):
    path = RUNTIME_PATH / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


offline_review = load_module("offline_strategy_quality_review")


class OfflineStrategyQualityReviewTests(unittest.TestCase):
    def test_missing_dataset_produces_hold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = offline_review.run_offline_strategy_quality_review(Path(tmp))

            self.assertEqual(result.recommendation, offline_review.HOLD)
            self.assertEqual(result.review_status, offline_review.REVIEW_BLOCKED)
            self.assertTrue(result.red_flags)

    def test_missing_no_trade_artifacts_prevents_automation_recommendation(self) -> None:
        with populated_repo(no_trade=False) as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertNotIn("AUTOMATION", result.recommendation)
            self.assertIn("no-trade artifacts missing", result.red_flags)

    def test_weak_journal_reasoning_is_detected(self) -> None:
        with populated_repo(extra_report="weak journal reasoning") as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIn("weak journal reasoning", result.red_flags)

    def test_vague_liquidity_language_is_detected(self) -> None:
        with populated_repo(extra_report="vague liquidity language") as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIn("vague liquidity language", result.red_flags)

    def test_vague_confirmation_language_is_detected(self) -> None:
        with populated_repo(extra_report="vague confirmation language") as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIn("vague confirmation language", result.red_flags)

    def test_repeated_generic_thesis_text_is_detected(self) -> None:
        with populated_repo(
            extra_report=(
                "paper-only setup fixture with context\n"
                "paper-only setup fixture with context\n"
            )
        ) as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIn("repeated generic thesis text", result.red_flags)

    def test_evaluation_score_inflation_is_detected(self) -> None:
        with populated_repo(extra_report="evaluation score inflation") as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIn("evaluation score inflation", result.red_flags)
            self.assertEqual(result.recommendation, offline_review.HOLD)

    def test_risk_rubber_stamping_is_detected(self) -> None:
        with populated_repo(extra_report="risk approval without meaningful challenge") as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIn("risk approval without meaningful challenge", result.red_flags)

    def test_human_approval_rubber_stamping_is_detected(self) -> None:
        with populated_repo(extra_report="human approval rubber-stamping") as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIn("human approval rubber-stamping", result.red_flags)

    def test_agent_rubber_stamping_is_detected(self) -> None:
        with populated_repo(extra_report="all agents approving with no objections") as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIn("agent rubber-stamping", result.red_flags)

    def test_too_many_approvals_is_detected(self) -> None:
        with populated_repo(
            extra_report=(
                "HUMAN_APPROVED_FOR_PAPER_ONLY PAPER_ORDER_SUBMITTED "
                "HUMAN_APPROVED_FOR_PAPER_ONLY PAPER_ORDER_SUBMITTED"
            )
        ) as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIn("too many approvals", result.red_flags)

    def test_too_few_rejections_is_detected(self) -> None:
        with populated_repo(no_trade=False) as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIn("too few rejections", result.red_flags)

    def test_no_trade_avoidance_is_detected(self) -> None:
        with populated_repo(extra_report="no-trade avoidance") as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIn("no-trade avoidance", result.red_flags)

    def test_any_recommendation_to_increase_size_fails(self) -> None:
        with populated_repo(extra_report="increase size before quality improves") as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIn("suggestion to increase size before quality improves", result.red_flags)
            self.assertEqual(result.recommendation, offline_review.HOLD)

    def test_any_automation_recommendation_fails(self) -> None:
        with populated_repo() as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertNotIn("AUTOMATION", result.recommendation)
            self.assertNotIn("automate", result.recommendation.lower())

    def test_report_is_generated_from_local_artifacts(self) -> None:
        with populated_repo() as root:
            result = offline_review.run_offline_strategy_quality_review(root)

            self.assertIsNotNone(result.report_path)
            report_path = Path(result.report_path or "")
            self.assertTrue(report_path.exists())
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("Offline Strategy Quality Review", report)
            self.assertIn("Review Status", report)

    def test_generated_report_states_live_trading_remains_unsupported(self) -> None:
        with populated_repo() as root:
            result = offline_review.run_offline_strategy_quality_review(root)
            report = Path(result.report_path or "").read_text(encoding="utf-8")

            self.assertIn("Live trading remains unsupported.", report)

    def test_no_alpaca_imports_exist(self) -> None:
        source = source_text()

        self.assertNotIn("alpaca_paper", source)
        self.assertNotIn("AlpacaPaper", source)

    def test_no_broker_calls_exist(self) -> None:
        source = source_text()

        self.assertNotIn("urlopen", source)
        self.assertNotIn("/v2/orders", source)
        self.assertNotIn("Request(", source)

    def test_no_order_sends_exist(self) -> None:
        source = source_text()

        self.assertNotIn("send_paper_order_request", source)
        self.assertNotIn("submit_order", source)
        self.assertNotIn("place_order", source)

    def test_no_llm_calls_exist(self) -> None:
        source = source_text()

        self.assertNotIn("chat.completions", source)
        self.assertNotIn("responses.create", source)
        self.assertNotIn("OpenAI", source)

    def test_no_credentials_or_env_files_are_created(self) -> None:
        before = env_files()
        with populated_repo() as root:
            offline_review.run_offline_strategy_quality_review(root)

        self.assertEqual(before, env_files())


class populated_repo:
    def __init__(self, *, no_trade: bool = True, extra_report: str = "") -> None:
        self.no_trade = no_trade
        self.extra_report = extra_report
        self._tmp: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> Path:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        write_text(
            root / "reports/phase_11_repeatability/PHASE_11_REPEATABILITY_SUMMARY.md",
            "PASS repeatability paper_order_submitted reconciliation matched rejected setup noted",
        )
        write_text(
            root / "reports/phase_16_evaluation_gated_regression/PHASE_16_EVALUATION_GATED_REGRESSION_SUMMARY.md",
            "PASS strategy evaluation PASS evaluation gate passed data integrity data freshness data completeness",
        )
        write_text(
            root / "docs/BASELINE_SAFE_PAPER_EXECUTION_V2.md",
            "Baseline Safe Paper Execution V2 ADLC live trading unsupported do not increase notional do not add automation",
        )
        write_text(
            root / "reports/first_controlled_paper_send/20260520T000000Z/FIRST_CONTROLLED_PAPER_SEND_REPORT.md",
            "PAPER_ORDER_SUBMITTED journal explains liquidity confirmation fixed risk",
        )
        write_text(
            root / "reports/first_controlled_paper_send/20260520T000000Z/POST_MORTEM.md",
            "RECONCILIATION_MATCHED no mismatches",
        )
        if self.no_trade:
            write_text(root / "memory/rejected_trades.md", "no trade correct rejection weak setup rejected")
            write_text(root / "evaluation/no_trade_scenarios.md", "no-trade decision rewarded waiting")
        if self.extra_report:
            write_text(root / "memory/journal.md", self.extra_report)
        return root

    def __exit__(self, exc_type, exc, tb) -> None:
        assert self._tmp is not None
        self._tmp.cleanup()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def source_text() -> str:
    return (RUNTIME_PATH / "offline_strategy_quality_review.py").read_text(encoding="utf-8")


def env_files() -> set[str]:
    return {
        path.as_posix()
        for path in ROOT.rglob(".env*")
        if "__pycache__" not in path.parts
    }


if __name__ == "__main__":
    unittest.main()
