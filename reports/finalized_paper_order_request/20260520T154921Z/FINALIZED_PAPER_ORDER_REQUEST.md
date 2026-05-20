# Finalized Paper Order Request

## Summary

- Paper order request id: finalized-candidate-paper-market_open-001
- Candidate id: candidate-paper-market_open-001
- Review id: review-candidate-paper-market_open-001
- Symbol: SIM
- Side: long
- Order type: limit
- Time in force: day
- Notional: 100
- Limit price: 100
- Request status: PAPER_ORDER_REQUEST_FINALIZED
- Gate references: {"evaluation_gate_reference": "evaluation-gate-paper-market_open-001", "human_review_reference": "review-candidate-paper-market_open-001", "journal_reference": "automated-dry-run-journal", "negative_case_regression_reference": "negative-case-regression-pass", "risk_reference": "risk-dry-run-paper-market_open-001", "strategy_evaluation_reference": "strategy-evaluation-paper-market_open-001"}
- Human review reference: review-candidate-paper-market_open-001
- paper_trading_only: true
- manual_execution_confirmation_required: true
- broker_execution_allowed: false
- live_trading_allowed: false
- Final status: PAPER_ORDER_REQUEST_FINALIZED
- Reason: Finalized Paper Order Request created as an inert artifact only.

## Request

```json
{
  "paper_order_request_id": "finalized-candidate-paper-market_open-001",
  "candidate_id": "candidate-paper-market_open-001",
  "review_id": "review-candidate-paper-market_open-001",
  "created_at": "2026-05-20T15:49:21Z",
  "symbol": "SIM",
  "side": "long",
  "order_type": "limit",
  "time_in_force": "day",
  "notional": "100",
  "quantity": null,
  "limit_price": "100",
  "stop_loss": "98",
  "target_1": "104",
  "target_2": "106",
  "thesis": "SIM paper-only long tests a reclaimed 100.00 prior-session low after failed downside liquidity.",
  "invalidation": "A 15-minute close below 98.00 invalidates the reclaimed-low thesis.",
  "proposal_reference": "paper-market_open-001",
  "strategy_evaluation_reference": "strategy-evaluation-paper-market_open-001",
  "evaluation_gate_reference": "evaluation-gate-paper-market_open-001",
  "negative_case_regression_reference": "negative-case-regression-pass",
  "risk_reference": "risk-dry-run-paper-market_open-001",
  "journal_reference": "automated-dry-run-journal",
  "human_review_reference": "review-candidate-paper-market_open-001",
  "paper_trading_only": true,
  "manual_execution_confirmation_required": true,
  "broker_execution_allowed": false,
  "live_trading_allowed": false,
  "request_status": "PAPER_ORDER_REQUEST_FINALIZED"
}
```

## Safety

Finalized Paper Order Request is not broker execution.
Manual Execution Confirmation is still required later.
Paper Send Preflight is still required later.
No order was sent.
No broker execution readiness was created.
Live trading remains unsupported.
