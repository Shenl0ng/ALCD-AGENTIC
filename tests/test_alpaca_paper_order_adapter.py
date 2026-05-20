from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from dataclasses import dataclass, replace
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


class AlpacaPaperOrderAdapterTests(unittest.TestCase):
    def test_default_mode_is_dry_run_only(self) -> None:
        config = alpaca_paper_order_adapter.PaperOrderAdapterConfig()

        self.assertEqual(config.execution_mode, alpaca_paper_order_adapter.DRY_RUN_ONLY)

    def test_adapter_disabled_by_default_blocks_sending(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        confirmation = manual_confirmation(request)
        adapter = alpaca_paper_order_adapter.AlpacaPaperOrderAdapter(
            client=alpaca_paper_order_adapter.RecordingMockPaperClient()
        )

        result = adapter.send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=confirmation,
        )

        self.assertEqual(
            result.status,
            alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT,
        )
        self.assertIn("PAPER_ORDER_EXECUTION_ENABLED is not true", result.preflight.violations)

    def test_real_alpaca_paper_send_requires_explicit_mode(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()

        result = enabled_adapter(mode=alpaca_paper_order_adapter.DRY_RUN_ONLY).send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(
            result.status,
            alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT,
        )
        self.assertIn("adapter mode is DRY_RUN_ONLY", result.preflight.violations)

    def test_live_mode_rejected(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        adapter = alpaca_paper_order_adapter.AlpacaPaperOrderAdapter(
            alpaca_paper_order_adapter.PaperOrderAdapterConfig(
                execution_enabled=True,
                execution_mode=alpaca_paper_order_adapter.MOCKED_PAPER_SEND,
                base_url="https://api.alpaca.markets",
            ),
            alpaca_paper_order_adapter.RecordingMockPaperClient(),
        )

        result = adapter.send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(
            result.status,
            alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT,
        )
        self.assertIn("live endpoint/config rejected", result.preflight.violations)

    def test_non_paper_account_rejected(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        account = replace(alpaca_paper_account.default_mock_snapshot(), paper_mode=False)

        result = enabled_adapter().send_paper_order_request(
            request,
            account=account,
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(result.status, alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT)
        self.assertIn("non-paper account rejected", result.preflight.violations)

    def test_expired_request_rejected(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        request = replace(request, expires_at="2026-05-19T13:00:00+00:00")

        result = enabled_adapter().send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(result.status, alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT)
        self.assertIn("request is expired", result.preflight.violations)

    def test_missing_risk_approval_rejected(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        request = replace(request, risk_approval_reference="RISK_REJECTED")

        result = enabled_adapter().send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(result.status, alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT)
        self.assertIn("missing risk approval", result.preflight.violations)

    def test_missing_human_approval_rejected(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        request = replace(request, human_approval_reference=None)

        result = enabled_adapter().send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(result.status, alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT)
        self.assertIn("missing human approval", result.preflight.violations)

    def test_missing_manual_execution_confirmation_rejected(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()

        result = enabled_adapter().send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
        )

        self.assertEqual(result.status, alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT)
        self.assertIn("missing manual execution confirmation", result.preflight.violations)

    def test_missing_journal_commit_rejected(self) -> None:
        _, _, _, _, request, _ = valid_bundle()

        result = enabled_adapter().send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=None,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(result.status, alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT)
        self.assertIn("missing journal commit", result.preflight.violations)

    def test_adlc_fail_rejected(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        request = replace(request, adlc_compliance_reference="FAIL")

        result = enabled_adapter().send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(result.status, alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT)
        self.assertIn("ADLC compliance is not PASS", result.preflight.violations)

    def test_invalid_gatekeeper_status_rejected(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        request = replace(request, gatekeeper_status="EXECUTION_BLOCKED")

        result = enabled_adapter().send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(result.status, alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT)
        self.assertIn(
            "gatekeeper status is not READY_FOR_PAPER_ORDER_REQUEST",
            result.preflight.violations,
        )

    def test_request_not_created_rejected(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        request = replace(request, final_status="PAPER_ORDER_REQUEST_BLOCKED")

        result = enabled_adapter().send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(result.status, alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT)
        self.assertIn(
            "request final_status is not PAPER_ORDER_REQUEST_CREATED",
            result.preflight.violations,
        )

    def test_secrets_not_logged(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        os.environ["ALPACA_API_SECRET_KEY"] = "secret-value-not-in-output"
        try:
            result = enabled_adapter().send_paper_order_request(
                request,
                account=alpaca_paper_account.default_mock_snapshot(),
                journal_commit=journal,
                manual_confirmation=manual_confirmation(request),
            )
        finally:
            os.environ.pop("ALPACA_API_SECRET_KEY", None)

        self.assertNotIn("secret-value-not-in-output", str(result.as_dict()))

    def test_no_env_file_created(self) -> None:
        before = env_files()
        _, _, _, journal, request, _ = valid_bundle()

        enabled_adapter().send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(before, env_files())

    def test_no_live_endpoint_supported(self) -> None:
        config = alpaca_paper_order_adapter.PaperOrderAdapterConfig(
            execution_enabled=True,
            base_url="https://api.alpaca.markets",
        )

        self.assertNotEqual(config.base_url.rstrip("/"), alpaca_paper_account.PAPER_BASE_URL)

    def test_no_cancel_replace_or_live_trading_methods_exist(self) -> None:
        adapter = enabled_adapter()

        self.assertFalse(hasattr(adapter, "cancel_order"))
        self.assertFalse(hasattr(adapter, "replace_order"))
        self.assertFalse(hasattr(adapter, "live_trade"))
        self.assertFalse(hasattr(adapter, "send_live_order"))

    def test_paper_send_path_uses_only_mocked_client(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        client = alpaca_paper_order_adapter.RecordingMockPaperClient()
        adapter = enabled_adapter(client)

        result = adapter.send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(result.status, alpaca_paper_order_adapter.PAPER_ORDER_SUBMITTED)
        self.assertEqual(len(client.payloads), 1)

    def test_mocked_paper_send_succeeds_only_when_every_gate_passes(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()

        allowed = enabled_adapter().send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )
        blocked = enabled_adapter().send_paper_order_request(
            replace(request, live_trading_allowed=True),
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(allowed.status, alpaca_paper_order_adapter.PAPER_ORDER_SUBMITTED)
        self.assertEqual(blocked.status, alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT)

    def test_preflight_blocked_rejected(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        preflight = enabled_adapter().preflight(
            replace(request, live_trading_allowed=True),
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(preflight.final_decision, alpaca_paper_order_adapter.PAPER_ORDER_SEND_BLOCKED)

    def test_more_than_one_order_per_run_rejected(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        adapter = enabled_adapter()

        first = adapter.send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )
        second = adapter.send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(first.status, alpaca_paper_order_adapter.PAPER_ORDER_SUBMITTED)
        self.assertEqual(second.status, alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT)
        self.assertIn("more than one order per run rejected", second.preflight.violations)

    def test_phase_9_order_constraints_rejected(self) -> None:
        cases = (
            ({"quantity": "2"}, "notional over 100 USD"),
            ({"order_type": "market"}, "market orders are not allowed by governance"),
            ({"side": "short"}, "short selling is not allowed by governance"),
            ({"symbol": "AAPL260619C00100000"}, "options are disabled"),
            ({"symbol": "BTCUSD"}, "crypto is disabled"),
            ({"order_intent": "paper_order_request_only_margin"}, "margin/leverage is disabled"),
            ({"time_in_force": "day_extended"}, "extended hours are disabled"),
            ({"order_type": "bracket"}, "bracket/complex orders are disabled"),
        )
        for changes, violation in cases:
            with self.subTest(violation=violation):
                _, _, _, journal, request, _ = valid_bundle()
                request = replace(request, **changes)
                result = enabled_adapter().send_paper_order_request(
                    request,
                    account=alpaca_paper_account.default_mock_snapshot(),
                    journal_commit=journal,
                    manual_confirmation=manual_confirmation(request),
                )

                self.assertEqual(
                    result.status,
                    alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT,
                )
                self.assertIn(violation, result.preflight.violations)

    def test_mocked_alpaca_client_receives_exactly_one_paper_limit_day_order(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()
        client = alpaca_paper_order_adapter.RecordingMockPaperClient()

        result = enabled_adapter(client).send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(result.status, alpaca_paper_order_adapter.PAPER_ORDER_SUBMITTED)
        self.assertEqual(
            list(client.payloads),
            [
                {
                    "symbol": "SIM",
                    "side": "buy",
                    "type": "limit",
                    "time_in_force": "day",
                    "limit_price": "100",
                    "paper_order_request_id": request.paper_order_request_id,
                    "qty": "1",
                }
            ],
        )

    def test_execution_result_and_post_send_journal_are_recorded(self) -> None:
        _, _, _, journal, request, _ = valid_bundle()

        result = enabled_adapter().send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertIsNotNone(result.execution_result)
        self.assertEqual(
            result.execution_result.final_status,
            alpaca_paper_order_adapter.PAPER_ORDER_SUBMITTED,
        )
        self.assertIsNotNone(result.journal_entry)
        self.assertEqual(result.journal_entry.event_type, "paper_order_send_submitted")

    def test_rejects_non_paper_order_request(self) -> None:
        result = enabled_adapter().send_paper_order_request(
            {"not": "a request"},
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=None,
        )

        self.assertEqual(
            result.status,
            alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT,
        )
        self.assertIn("request is not a PaperOrderRequest", result.preflight.violations)


def valid_bundle():
    proposal, risk, approval, journal, request, validation = paper_order_request.deterministic_valid_request()
    return proposal, risk, approval, journal, replace(request, quantity="1"), validation


@dataclass(frozen=True)
class ManualConfirmation:
    confirmation_id: str
    paper_order_request_id: str | None
    confirmation_state: str
    paper_only_confirmation: bool


def manual_confirmation(request):
    return ManualConfirmation(
        confirmation_id=f"manual-confirmation-{request.paper_order_request_id}",
        paper_order_request_id=request.paper_order_request_id,
        confirmation_state=alpaca_paper_order_adapter.MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY,
        paper_only_confirmation=True,
    )


def enabled_adapter(client=None, mode=None):
    return alpaca_paper_order_adapter.AlpacaPaperOrderAdapter(
        alpaca_paper_order_adapter.PaperOrderAdapterConfig(
            execution_enabled=True,
            execution_mode=mode or alpaca_paper_order_adapter.MOCKED_PAPER_SEND,
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
