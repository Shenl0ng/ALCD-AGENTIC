# Soak Final Report

## Summary

- Soak window: Soak Run 1 blocked attempt
- Attempted runs: 1
- Submitted paper orders: 0
- Blocked runs: 1
- Failed gate: cooldown satisfied
- Block reason: 24-hour cooldown not satisfied
- Detailed reason: Phase 52 requires minimum 24-hour cooldown between submitted automated paper orders.
- Previous automated paper send: 2026-05-20T13:42:19Z
- Expected safety behavior: true
- Real order sent: no
- Alpaca API called: no
- Secrets printed: no
- `.env.local` PAPER_ORDER_EXECUTION_ENABLED restored to false: true
- `.env.local` PAPER_AUTOMATED_SEND_ENABLED restored to false: true

## Gate And Artifact References

- Full tests: PASS, 720 tests
- Architecture validation: PASS
- V10 regression: reports/v10_full_pipeline_dry_run_regression/20260520T154836Z/V10_FULL_PIPELINE_DRY_RUN_REGRESSION_REPORT.md
- Mocked regression: reports/automated_paper_send_mocked_regression/20260520T154836Z/AUTOMATED_PAPER_SEND_MOCKED_REGRESSION_REPORT.md
- Negative case regression: reports/negative_case_regression/20260520T154921Z/NEGATIVE_CASE_REGRESSION_REPORT.md
- Candidate: reports/automated_paper_request_candidate/20260520T154921Z/PAPER_ORDER_REQUEST_CANDIDATE.md
- Human review: reports/human_review_queue/20260520T154930Z/HUMAN_REVIEW_RECORD.md
- Finalized request: reports/finalized_paper_order_request/20260520T154921Z/FINALIZED_PAPER_ORDER_REQUEST.md
- Manual confirmation: reports/manual_execution_confirmation/20260520T154930Z/MANUAL_EXECUTION_CONFIRMATION.md
- Preflight: reports/paper_send_preflight/20260520T154921Z/PAPER_SEND_PREFLIGHT.md
- Automated paper send report: none, blocked before send
- Reconciliation: none for this attempt, blocked before send
- Post-send safety: none for this attempt, blocked before send
- Post-mortem: none for this attempt, blocked before send

## Reconciliation And Post-Run Status

- Reconciliation summary: no reconciliation required because no order was submitted
- Post-mortem summary: no post-mortem required because no order was submitted
- Post-send safety summary: no post-send safety report required because no order was submitted
- Daily order limit compliance: true
- Daily notional compliance: true
- Cooldown compliance: false
- Kill switch events: none
- Unresolved issues: none
- Approval-rate analysis: no red flag
- No-trade/rejection analysis: no degradation
- Journal quality analysis: no degradation
- Safety violations: none

## Recommendation

- Recommendation: CONTINUE_SOAK
- Recommendation reason: The block was expected and correct. The cooldown safety control worked. No order was sent. No unresolved issue was created.

Live trading remains unsupported.
Increasing notional remains prohibited.
Multi-symbol automation remains prohibited.
Batch orders remain prohibited.
Cancel/replace remains prohibited.
