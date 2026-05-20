from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime"
ADAPTER_PATH = RUNTIME_PATH / "alpaca_paper_account.py"

if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))

spec = importlib.util.spec_from_file_location("alpaca_paper_account", ADAPTER_PATH)
alpaca_paper_account = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["alpaca_paper_account"] = alpaca_paper_account
spec.loader.exec_module(alpaca_paper_account)


class MockReadOnlyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str] | None]] = []

    def get_json(self, path: str, params: dict[str, str] | None = None):
        self.calls.append((path, params))
        if path == "/v2/account":
            return {
                "id": "acct-123",
                "cash": "1000.50",
                "equity": "1200.75",
                "buying_power": "2000",
                "portfolio_value": "1200.75",
                "daytrade_count": 1,
                "trading_blocked": False,
                "transfers_blocked": False,
                "account_blocked": False,
                "status": "ACTIVE",
            }
        if path == "/v2/positions":
            return [
                {
                    "symbol": "SIM",
                    "qty": "2",
                    "market_value": "300",
                    "unrealized_pl": "12.34",
                    "avg_entry_price": "144",
                }
            ]
        if path == "/v2/orders":
            return [
                {
                    "id": "existing-1",
                    "symbol": "SIM",
                    "side": "buy",
                    "type": "limit",
                    "status": "filled",
                    "submitted_at": "2026-05-19T13:00:00Z",
                }
            ]
        raise AssertionError(f"Unexpected path: {path}")


class AlpacaPaperAccountAdapterTests(unittest.TestCase):
    def test_paper_mode_required(self) -> None:
        config = alpaca_paper_account.AlpacaPaperConfig(
            key_id="key",
            secret_key="secret",
            paper_mode=False,
        )

        with self.assertRaises(alpaca_paper_account.AlpacaSafetyError):
            config.validate()

    def test_live_mode_rejected(self) -> None:
        config = alpaca_paper_account.AlpacaPaperConfig(
            key_id="key",
            secret_key="secret",
            base_url="https://api.alpaca.markets",
        )

        with self.assertRaises(alpaca_paper_account.AlpacaSafetyError):
            config.validate()

    def test_missing_credentials_handled_safely(self) -> None:
        config = alpaca_paper_account.AlpacaPaperConfig(key_id="", secret_key="")

        with self.assertRaises(alpaca_paper_account.AlpacaMissingCredentialsError):
            config.validate()

    def test_secrets_not_logged_or_represented(self) -> None:
        config = alpaca_paper_account.AlpacaPaperConfig(
            key_id="visible-key-should-not-print",
            secret_key="visible-secret-should-not-print",
        )

        rendered = repr(config)

        self.assertNotIn("visible-key-should-not-print", rendered)
        self.assertNotIn("visible-secret-should-not-print", rendered)

    def test_account_read_succeeds_using_mocked_client(self) -> None:
        adapter = adapter_with_mock_client()

        account = adapter.read_account_state()

        self.assertEqual(account.account_id, "acct-123")
        self.assertEqual(account.cash, "1000.50")
        self.assertTrue(account.trading_allowed_in_principle)

    def test_positions_read_succeeds_using_mocked_client(self) -> None:
        adapter = adapter_with_mock_client()

        positions = adapter.read_positions()

        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0].symbol, "SIM")
        self.assertEqual(positions[0].quantity, "2")

    def test_existing_paper_orders_read_succeeds_using_mocked_client(self) -> None:
        client = MockReadOnlyClient()
        adapter = adapter_with_mock_client(client)

        existing_orders = adapter.read_existing_paper_orders()

        self.assertEqual(len(existing_orders), 1)
        self.assertEqual(existing_orders[0].order_id, "existing-1")
        self.assertIn(("/v2/orders", {"status": "all", "limit": "50"}), client.calls)

    def test_no_order_placement_method_exists_or_is_callable(self) -> None:
        adapter = adapter_with_mock_client()

        self.assertFalse(hasattr(adapter, "place_order"))
        self.assertFalse(hasattr(adapter, "submit_order"))
        self.assertFalse(hasattr(adapter, "buy"))
        self.assertFalse(hasattr(adapter, "sell"))

    def test_no_cancel_or_replace_method_exists_or_is_callable(self) -> None:
        adapter = adapter_with_mock_client()

        self.assertFalse(hasattr(adapter, "cancel_order"))
        self.assertFalse(hasattr(adapter, "replace_order"))
        self.assertFalse(hasattr(adapter, "cancel"))
        self.assertFalse(hasattr(adapter, "replace"))

    def test_from_env_uses_environment_only(self) -> None:
        env = {
            alpaca_paper_account.ENV_KEY_ID: "env-key",
            alpaca_paper_account.ENV_SECRET_KEY: "env-secret",
            alpaca_paper_account.ENV_PAPER: "true",
        }
        with patch.dict(os.environ, env, clear=True):
            config = alpaca_paper_account.AlpacaPaperConfig.from_env()

        self.assertEqual(config.base_url, alpaca_paper_account.PAPER_BASE_URL)
        config.validate()


def adapter_with_mock_client(
    client: MockReadOnlyClient | None = None,
) -> alpaca_paper_account.AlpacaPaperAccountReadOnlyAdapter:
    config = alpaca_paper_account.AlpacaPaperConfig(key_id="key", secret_key="secret")
    return alpaca_paper_account.AlpacaPaperAccountReadOnlyAdapter(
        config,
        client or MockReadOnlyClient(),
    )


if __name__ == "__main__":
    unittest.main()
