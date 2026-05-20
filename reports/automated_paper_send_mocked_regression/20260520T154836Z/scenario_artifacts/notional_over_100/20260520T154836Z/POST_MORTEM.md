# Post-Mortem

- Automated paper send status: AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Block reasons: ["Paper Send Preflight is not PAPER_ORDER_SEND_ALLOWED", "daily notional limit exceeded", "notional > 100 USD is blocked"]
- Unexpected behavior: none recorded
- Missing artifacts: none
- Future sends remain gated by V12 and Phase 44 automation controls.
- Live trading remains unsupported.
