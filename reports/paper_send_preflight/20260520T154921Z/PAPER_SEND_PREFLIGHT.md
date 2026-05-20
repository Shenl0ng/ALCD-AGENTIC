# Paper Send Preflight

## Summary

- Preflight id: preflight-finalized-candidate-paper-market_open-001
- Paper order request id: finalized-candidate-paper-market_open-001
- Manual confirmation id: manual-confirmation-finalized-candidate-paper-market_open-001
- Preflight status: PAPER_ORDER_SEND_ALLOWED
- Checks: {"account_mode_checked": true, "confirmation_broker_execution_allowed_false": true, "confirmation_live_trading_allowed_false": true, "live_endpoint_rejected": true, "max_notional_check": true, "no_batch_check": true, "no_cancel_replace_check": true, "no_crypto_check": true, "no_extended_hours_check": true, "no_margin_check": true, "no_options_check": true, "no_short_check": true, "one_order_only_check": true, "order_type_check": true, "paper_send_preflight_required": true, "paper_trading_only": true, "time_in_force_check": true}
- Failure reasons: []
- broker_execution_allowed: false
- live_trading_allowed: false
- Final status: PAPER_ORDER_SEND_ALLOWED
- Reason: Paper Send Preflight passed for later controlled paper send consideration only.

## Preflight

```json
{
  "preflight_id": "preflight-finalized-candidate-paper-market_open-001",
  "paper_order_request_id": "finalized-candidate-paper-market_open-001",
  "manual_confirmation_id": "manual-confirmation-finalized-candidate-paper-market_open-001",
  "checked_at": "2026-05-20T15:49:21Z",
  "preflight_status": "PAPER_ORDER_SEND_ALLOWED",
  "paper_trading_only": true,
  "account_mode_checked": true,
  "live_endpoint_rejected": true,
  "max_notional_check": true,
  "order_type_check": true,
  "time_in_force_check": true,
  "no_short_check": true,
  "no_crypto_check": true,
  "no_options_check": true,
  "no_margin_check": true,
  "no_extended_hours_check": true,
  "one_order_only_check": true,
  "no_batch_check": true,
  "no_cancel_replace_check": true,
  "broker_execution_allowed": false,
  "live_trading_allowed": false,
  "failure_reasons": [],
  "final_status": "PAPER_ORDER_SEND_ALLOWED"
}
```

## Safety

Paper Send Preflight does not send orders.
PAPER_ORDER_SEND_ALLOWED is not broker execution.
PAPER_ORDER_SEND_ALLOWED does not call Alpaca.
PAPER_ORDER_EXECUTION_ENABLED was not enabled.
No order was sent.
No broker execution readiness was created.
Live trading remains unsupported.
