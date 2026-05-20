from __future__ import annotations

import importlib.util
import os
import sys
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


alpaca_paper_account = load_module("alpaca_paper_account")
paper_order_request = load_module("paper_order_request")
alpaca_paper_order_adapter = load_module("alpaca_paper_order_adapter")
paper_execution_dry_run = load_module("paper_execution_dry_run")


class PaperExecutionDryRunTests(unittest.TestCase):
    def test_default_mode_is_dry_run_only(self) -> None:
        report = paper_execution_dry_run.run_dry_run_flow()

        self.assertEqual(report.adapter_mode, paper_execution_dry_run.DRY_RUN_ONLY)

    def test_dry_run_completes_without_sending(self) -> None:
        client = alpaca_paper_order_adapter.RecordingMockPaperClient()
        report = paper_execution_dry_run.run_dry_run_flow(
            adapter=enabled_adapter(client),
        )

        self.assertEqual(report.final_execution_status, paper_execution_dry_run.DRY_RUN_COMPLETED)
        self.assertEqual(client.payloads, [])

    def test_mocked_send_requires_mocked_paper_send_mode(self) -> None:
        _, _, _, _, request, _ = paper_order_request.deterministic_valid_request()
        confirmation = paper_execution_dry_run.confirmed_manual_execution(request)
        client = alpaca_paper_order_adapter.RecordingMockPaperClient()

        report = paper_execution_dry_run.run_dry_run_flow(
            mode=paper_execution_dry_run.DRY_RUN_ONLY,
            manual_confirmation=confirmation,
            adapter=enabled_adapter(client),
        )

        self.assertEqual(report.final_execution_status, paper_execution_dry_run.DRY_RUN_COMPLETED)
        self.assertEqual(client.payloads, [])

    def test_mocked_send_requires_manual_execution_confirmation(self) -> None:
        report = paper_execution_dry_run.run_dry_run_flow(
            mode=paper_execution_dry_run.MOCKED_PAPER_SEND,
            adapter=enabled_adapter(),
        )

        self.assertEqual(
            report.final_execution_status,
            paper_execution_dry_run.MANUAL_CONFIRMATION_REQUIRED,
        )

    def test_human_approval_alone_is_not_enough_to_send(self) -> None:
        client = alpaca_paper_order_adapter.RecordingMockPaperClient()
        report = paper_execution_dry_run.run_dry_run_flow(
            mode=paper_execution_dry_run.MOCKED_PAPER_SEND,
            adapter=enabled_adapter(client),
        )

        self.assertEqual(
            report.manual_execution_confirmation_status,
            paper_execution_dry_run.MANUAL_EXECUTION_CONFIRMATION_REQUIRED,
        )
        self.assertEqual(client.payloads, [])

    def test_missing_journal_commit_blocks_send(self) -> None:
        report = confirmed_mocked_send(force_missing_journal=True)

        self.assertEqual(report.final_execution_status, paper_execution_dry_run.PAPER_SEND_BLOCKED)

    def test_missing_risk_approval_blocks_send(self) -> None:
        report = confirmed_mocked_send(force_missing_risk=True)

        self.assertEqual(report.final_execution_status, paper_execution_dry_run.PAPER_SEND_BLOCKED)

    def test_invalid_gatekeeper_status_blocks_send(self) -> None:
        report = confirmed_mocked_send(force_invalid_gatekeeper=True)

        self.assertEqual(report.final_execution_status, paper_execution_dry_run.PAPER_SEND_BLOCKED)

    def test_expired_request_blocks_send(self) -> None:
        report = confirmed_mocked_send(force_expired_request=True)

        self.assertEqual(report.final_execution_status, paper_execution_dry_run.PAPER_SEND_BLOCKED)

    def test_live_flag_blocks_send(self) -> None:
        report = confirmed_mocked_send(force_live_flag=True)

        self.assertEqual(report.final_execution_status, paper_execution_dry_run.PAPER_SEND_BLOCKED)

    def test_adapter_disabled_blocks_send(self) -> None:
        _, _, _, _, request, _ = paper_order_request.deterministic_valid_request()
        confirmation = paper_execution_dry_run.confirmed_manual_execution(request)

        report = paper_execution_dry_run.run_dry_run_flow(
            mode=paper_execution_dry_run.MOCKED_PAPER_SEND,
            manual_confirmation=confirmation,
            adapter=alpaca_paper_order_adapter.AlpacaPaperOrderAdapter(
                alpaca_paper_order_adapter.PaperOrderAdapterConfig(execution_enabled=False),
                alpaca_paper_order_adapter.RecordingMockPaperClient(),
            ),
        )

        self.assertEqual(report.final_execution_status, paper_execution_dry_run.PAPER_SEND_BLOCKED)

    def test_preflight_blocked_prevents_send(self) -> None:
        account = alpaca_paper_account.default_mock_snapshot()
        account = type(account)(
            account=account.account,
            positions=account.positions,
            existing_orders=account.existing_orders,
            paper_mode=False,
        )

        report = confirmed_mocked_send(account=account)

        self.assertEqual(report.preflight_status, alpaca_paper_order_adapter.PAPER_ORDER_SEND_BLOCKED)
        self.assertEqual(report.final_execution_status, paper_execution_dry_run.PAPER_SEND_BLOCKED)

    def test_final_report_includes_all_required_references(self) -> None:
        report = confirmed_mocked_send()
        payload = report.as_dict()

        for field in (
            "proposal_id",
            "risk_status",
            "human_approval_status",
            "journal_entry_id",
            "paper_order_request_id",
            "manual_execution_confirmation_status",
            "preflight_status",
            "adapter_mode",
            "final_execution_status",
        ):
            self.assertIn(field, payload)
            self.assertIsNotNone(payload[field])

    def test_no_live_endpoint_exists(self) -> None:
        report = confirmed_mocked_send()

        self.assertNotEqual(report.final_execution_status, "LIVE_APPROVED")

    def test_no_autonomous_execution_exists(self) -> None:
        report = paper_execution_dry_run.run_dry_run_flow(
            mode=paper_execution_dry_run.MOCKED_PAPER_SEND,
            adapter=enabled_adapter(),
        )

        self.assertEqual(
            report.final_execution_status,
            paper_execution_dry_run.MANUAL_CONFIRMATION_REQUIRED,
        )

    def test_no_llm_calls_exist(self) -> None:
        sources = "\n".join(path.read_text(encoding="utf-8") for path in RUNTIME_PATH.glob("*.py"))

        self.assertNotIn("chat.completions", sources)
        self.assertNotIn("responses.create", sources)

    def test_secrets_are_not_logged(self) -> None:
        os.environ["ALPACA_API_SECRET_KEY"] = "secret-value-not-in-report"
        try:
            report = confirmed_mocked_send()
        finally:
            os.environ.pop("ALPACA_API_SECRET_KEY", None)

        self.assertNotIn("secret-value-not-in-report", str(report.as_dict()))

    def test_no_env_file_is_created(self) -> None:
        before = env_files()
        confirmed_mocked_send()

        self.assertEqual(before, env_files())

    def test_mocked_paper_send_completed_when_all_gates_pass(self) -> None:
        report = confirmed_mocked_send()

        self.assertEqual(
            report.final_execution_status,
            paper_execution_dry_run.MOCKED_PAPER_SEND_COMPLETED,
        )


def confirmed_mocked_send(**kwargs):
    _, _, _, _, request, _ = paper_order_request.deterministic_valid_request()
    confirmation = paper_execution_dry_run.confirmed_manual_execution(request)
    return paper_execution_dry_run.run_dry_run_flow(
        mode=paper_execution_dry_run.MOCKED_PAPER_SEND,
        manual_confirmation=confirmation,
        adapter=enabled_adapter(),
        **kwargs,
    )


def enabled_adapter(client=None):
    return alpaca_paper_order_adapter.AlpacaPaperOrderAdapter(
        alpaca_paper_order_adapter.PaperOrderAdapterConfig(
            execution_enabled=True,
            execution_mode=alpaca_paper_order_adapter.MOCKED_PAPER_SEND,
        ),
        client or alpaca_paper_order_adapter.RecordingMockPaperClient(),
    )


def env_files() -> set[str]:
    return {
        path.as_posix()
        for path in ROOT.rglob(".env*")
        if "__pycache__" not in path.parts
    }


if __name__ == "__main__":
    unittest.main()
