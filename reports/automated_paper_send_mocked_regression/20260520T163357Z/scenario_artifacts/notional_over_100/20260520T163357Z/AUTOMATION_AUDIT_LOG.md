# Automation Audit Log

- Timestamp: 2026-05-20T16:33:57Z
- PAPER_AUTOMATED_SEND_ENABLED: True
- PAPER_ORDER_EXECUTION_ENABLED: True
- ALPACA_PAPER: True
- Limit checks: {"cooldown_satisfied": true, "daily_notional_used": "0", "daily_order_count": 0, "kill_switch_active": false, "max_daily_notional": "100", "max_daily_orders": 1, "previous_post_mortem_exists": true, "previous_post_mortem_unresolved_blocker": false, "previous_reconciliation_exists": true, "previous_reconciliation_unresolved_mismatch": false, "unresolved_issue_exists": false}
- Final automated send decision: AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS
- Alpaca paper order submitted: False
- Block or submission reason: ["Paper Send Preflight is not PAPER_ORDER_SEND_ALLOWED", "daily notional limit exceeded", "notional > 100 USD is blocked"]
- Secrets printed: false
