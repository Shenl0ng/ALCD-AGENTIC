# V10 Controlled Paper Send Report

## Summary

- Generated at: 2026-05-20T11:29:05Z
- Baseline: V11
- Send status: PAPER_ORDER_SUBMITTED
- Block reasons: []
- Broker paper order id: 30ad9c46-cba2-4d0b-9a82-4bc918def1f4
- Error: none

## Gates

- Full tests: PASS
- Full tests: PASS, 582 tests
- Architecture validation: PASS
- V10 full pipeline dry-run regression: PASS
- Runtime V10 regression check: PASS
- Strategy Evaluation: PASS
- Evaluation-First Gate: EVALUATION_GATE_PASSED
- Negative Case Regression: PASS
- Candidate status: PAPER_ORDER_CANDIDATE_CREATED
- Human Review status: HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST
- Finalized Paper Order Request status: PAPER_ORDER_REQUEST_FINALIZED
- Manual Execution Confirmation status: MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT
- Paper Send Preflight status: PAPER_ORDER_SEND_ALLOWED
- Alpaca paper account confirmed: True
- Live endpoint rejected: True

## Send Controls

- One order only: true
- Paper trading only: True
- Max notional <= 100 USD: True
- Limit order only: True
- Day time-in-force only: True
- No short selling: True
- No crypto: True
- No options: True
- No margin/leverage: True
- No extended hours: True
- No batch orders: True
- No cancel/replace: True
- No live trading: true
- No live endpoints: True
- PAPER_ORDER_EXECUTION_ENABLED true only for manual run: True

## Results

- Order sent: True
- Alpaca order API called: True
- Reconciliation status: RECONCILIATION_MATCHED
- Returned to DRY_RUN_ONLY: true
- Operator must unset PAPER_ORDER_EXECUTION_ENABLED after run: true
- Secrets printed: false

Live trading remains unsupported.
Increasing notional remains prohibited.
Automation beyond approved V10 pipeline remains prohibited.
Batch orders remain prohibited.
Cancel/replace remains prohibited.
