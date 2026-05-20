# Simulated Paper Order Request

Internal request only. No broker order or execution is created.

Paper Mode: REQUIRED

```json
{
  "paper_order_request_id": "paper-order-request-paper-market_open-001",
  "proposal_id": "paper-market_open-001",
  "approval_id": "approval-paper-market_open-001",
  "journal_entry_id": "journal-paper-market_open-001-human_approved_for_paper_only",
  "created_at": "2026-05-19T13:35:00+00:00",
  "expires_at": null,
  "symbol": "SIM",
  "side": "long",
  "order_intent": "paper_order_request_only",
  "quantity": "100",
  "notional": null,
  "order_type": "limit",
  "time_in_force": "day",
  "proposed_entry": "100",
  "stop_loss": "98",
  "target_1": "104",
  "target_2": "106",
  "max_loss_amount": "200",
  "max_loss_pct_equity": "0.002",
  "paper_trading_only": true,
  "broker_execution_allowed": false,
  "live_trading_allowed": false,
  "risk_approval_reference": "RISK_APPROVED",
  "human_approval_reference": "HUMAN_APPROVED_FOR_PAPER_ONLY",
  "journal_commit_reference": "journal-paper-market_open-001-human_approved_for_paper_only",
  "adlc_compliance_reference": "PASS",
  "gatekeeper_status": "READY_FOR_PAPER_ORDER_REQUEST",
  "final_status": "PAPER_ORDER_REQUEST_CREATED"
}
```
