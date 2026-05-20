# Manual Execution Confirmation

## Summary

- Manual confirmation id: manual-confirmation-finalized-candidate-paper-market_open-001
- Paper order request id: finalized-candidate-paper-market_open-001
- Candidate id: candidate-paper-market_open-001
- Review id: review-candidate-paper-market_open-001
- Confirmer: soak-run-1-confirmer
- Confirmation status: MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT
- Confirmation notes: 
- Required confirmations: {"day_time_in_force_confirmation": true, "finalized_request_reviewed": true, "limit_order_confirmation": true, "no_crypto_confirmation": true, "no_extended_hours_confirmation": true, "no_live_trading_confirmation": true, "no_margin_confirmation": true, "no_options_confirmation": true, "no_short_confirmation": true, "notional_limit_confirmation": true, "order_details_reviewed": true, "paper_only_confirmation": true, "risk_reviewed": true}
- broker_execution_allowed: false
- live_trading_allowed: false
- paper_send_preflight_required: true
- Final status: MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT
- Reason: Manual Execution Confirmation created for future Paper Send Preflight only.

## Confirmation

```json
{
  "manual_confirmation_id": "manual-confirmation-finalized-candidate-paper-market_open-001",
  "paper_order_request_id": "finalized-candidate-paper-market_open-001",
  "candidate_id": "candidate-paper-market_open-001",
  "review_id": "review-candidate-paper-market_open-001",
  "confirmed_at": "2026-05-20T15:49:30Z",
  "confirmer": "soak-run-1-confirmer",
  "confirmation_status": "MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT",
  "confirmation_notes": "",
  "paper_only_confirmation": true,
  "no_live_trading_confirmation": true,
  "finalized_request_reviewed": true,
  "risk_reviewed": true,
  "order_details_reviewed": true,
  "notional_limit_confirmation": true,
  "limit_order_confirmation": true,
  "day_time_in_force_confirmation": true,
  "no_short_confirmation": true,
  "no_crypto_confirmation": true,
  "no_options_confirmation": true,
  "no_margin_confirmation": true,
  "no_extended_hours_confirmation": true,
  "broker_execution_allowed": false,
  "live_trading_allowed": false,
  "paper_send_preflight_required": true
}
```

## Safety

Manual Execution Confirmation does not send orders.
Paper Send Preflight is still required later.
No order was sent.
No broker execution readiness was created.
Live trading remains unsupported.
