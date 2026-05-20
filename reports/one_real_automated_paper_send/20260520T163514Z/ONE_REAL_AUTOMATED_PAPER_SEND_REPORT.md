# One Real Automated Paper Send Report

## Summary

- Generated at: 2026-05-20T16:35:14Z
- Final status: ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED
- Send status: ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED
- Block reasons: []
- Submitted order count: 1
- Alpaca paper order id: f600c8a6-834e-4cc4-b529-89ffbfbadd86
- Error: none

## Required Gate Statuses

- Full tests status: PASS
- PASS, 746 tests
- Architecture validation status: PASS
- V10 full pipeline dry-run regression status: PASS
- Automated paper send mocked regression status: PASS
- Soak framework PASS
- Accelerated cooldown PASS
- Strategy evaluation status: PASS
- Evaluation gate status: EVALUATION_GATE_PASSED
- Negative case regression status: PASS
- Candidate status: derived from valid TRADE_PROPOSAL when unblocked
- Human review status: HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST
- Finalized request status: PAPER_ORDER_REQUEST_FINALIZED when unblocked
- Manual execution confirmation status: MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT
- Paper send preflight status: PAPER_ORDER_SEND_ALLOWED when unblocked

## Automation Controls

- Automation kill switch status: inactive
- Daily order limit status: not exceeded
- Daily notional limit status: 0/100
- daily notional limit not exceeded
- Cooldown status: satisfied
- accelerated cooldown satisfied, 60 seconds
- Previous reconciliation status: exists and matched
- Previous post-mortem status: exists with no blockers
- Unresolved issue status: none
- Paper account confirmation: True
- Live endpoint rejection: True

## Results

- Order sent: True
- Alpaca order API called: True
- Reconciliation status: RECONCILIATION_MATCHED
- System returned to DRY_RUN_ONLY: true
- Flags disabled/unset after run: true
- .env.local flags restored to false
- Secrets printed: false

This was one controlled automated paper send only.
Live trading remains unsupported.
Increasing notional remains prohibited.
Batch orders remain prohibited.
Cancel/replace remains prohibited.
Multi-symbol automation remains prohibited.
Higher frequency outside accelerated paper soak test mode remains prohibited.
