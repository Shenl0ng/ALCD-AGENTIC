# Automated Paper Send Report

## Summary

- Generated at: 2026-05-20T15:48:36Z
- Final status: AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS
- Paper send status: AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS
- Alpaca paper order id: none
- Error: none
- Block reasons: ["daily order limit exceeded"]

## Automation Flags

- PAPER_AUTOMATED_SEND_ENABLED: True
- PAPER_ORDER_EXECUTION_ENABLED: True
- ALPACA_PAPER: True

## Gates

- Symbol: SIM
- Full tests: PASS
- Architecture validation: PASS
- V10 pipeline regression: PASS
- Strategy Evaluation: PASS
- Evaluation-First Gate: EVALUATION_GATE_PASSED
- Negative Case Regression: PASS
- Candidate status: PAPER_ORDER_CANDIDATE_CREATED
- Human Review status: HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST
- Finalized request status: PAPER_ORDER_REQUEST_FINALIZED
- Manual execution confirmation status: MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT
- Paper send preflight status: PAPER_ORDER_SEND_ALLOWED

## Automation Limit Checks

- Automation limits PASS: False
- Kill switch active: False
- Cooldown satisfied: True
- Daily order count: 1
- Daily notional used: 0
- Previous reconciliation exists: True
- Previous reconciliation mismatch unresolved: False
- Previous post-mortem exists: True
- Previous post-mortem unresolved blocker: False
- Unresolved issue exists: False
- Paper account confirmation: True
- Live endpoint rejection: True

## Results

- Order sent: False
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Post-mortem reference: POST_MORTEM.md
- Returned to DRY_RUN_ONLY: true
- PAPER_ORDER_EXECUTION_ENABLED unset or disabled after run: true
- PAPER_AUTOMATED_SEND_ENABLED unset or disabled after run: true

Automated paper send is paper-only.
Live trading remains unsupported.
Increasing notional remains prohibited.
Batch orders remain prohibited.
Cancel/replace remains prohibited.
