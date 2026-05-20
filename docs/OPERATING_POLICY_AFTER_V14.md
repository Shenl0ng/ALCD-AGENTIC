# Operating Policy After V14

## Current Operating Baseline

Baseline V14 is the current operating baseline.

Baseline V14 status is PASS.

DRY_RUN_ONLY is the default operating mode.

Live trading remains unsupported.

## What V14 Proves

V14 proves accelerated paper soak validation completed successfully.

V14 proves one real automated Alpaca paper order was submitted under accelerated paper-only soak controls.

V14 proves reconciliation matched.

V14 proves accelerated cooldown was used only for paper soak framework validation.

V14 proves production/default cooldown remains 24 hours.

V14 proves the system returned to DRY_RUN_ONLY.

V14 proves `.env.local` flags were restored to false.

V14 proves secrets were not printed.

Known V14 result:

- Test status: PASS, 746 tests
- Architecture validation: PASS
- V10 full pipeline dry-run regression: PASS
- Automated paper send mocked regression: PASS
- Soak framework status: PASS
- Accelerated cooldown status: PASS
- Strategy evaluation: PASS
- Evaluation-First Gate: EVALUATION_GATE_PASSED
- Negative Case Regression: PASS
- Candidate status: PAPER_ORDER_CANDIDATE_CREATED
- Human Review status: HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST
- Finalized Paper Order Request status: PAPER_ORDER_REQUEST_FINALIZED
- Manual Execution Confirmation status: MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT
- Paper Send Preflight status: PAPER_ORDER_SEND_ALLOWED
- Automation kill switch: inactive
- Daily order limit: not exceeded
- Daily notional limit: not exceeded
- Accelerated cooldown: satisfied, 60 seconds
- Previous reconciliation: exists and matched
- Previous post-mortem: exists with no blockers
- Unresolved issue status: none
- Paper send status: ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED
- Alpaca paper order id: f600c8a6-834e-4cc4-b529-89ffbfbadd86
- Reconciliation status: RECONCILIATION_MATCHED
- System returned to DRY_RUN_ONLY: confirmed
- `.env.local` flags restored to false: confirmed
- Production/default cooldown remains 24 hours: confirmed
- Accelerated cooldown was used for paper soak framework validation only: confirmed

## Default Operating Mode

DRY_RUN_ONLY is the default mode.

`PAPER_ORDER_EXECUTION_ENABLED` must remain disabled by default.

`PAPER_AUTOMATED_SEND_ENABLED` must remain disabled by default.

`PAPER_SOAK_TEST_ACCELERATED` must remain disabled by default.

`PAPER_SOAK_TEST_COOLDOWN_SECONDS` may remain configured, but accelerated mode must stay disabled unless explicitly needed for a paper-only soak validation run.

Production/default cooldown remains 24 hours.

## Allowed Operations After V14

- Continue automated dry-run analysis.
- Continue candidate creation.
- Continue Human Review Queue.
- Continue finalized paper order requests.
- Continue Manual Execution Confirmation.
- Continue Paper Send Preflight.
- Continue accelerated paper soak validation under explicit test controls.
- Continue production/default 24-hour cooldown soak planning.
- Continue offline quality review.
- Continue negative-case expansion.
- Continue rejection quality improvement.
- Continue NO_TRADE discipline improvement.
- Continue journal quality improvement.

## Prohibited Operations After V14

- Live trading.
- Live endpoints.
- Increasing notional.
- Multi-symbol automation.
- Batch orders.
- Cancel/replace.
- Higher frequency outside accelerated paper soak test mode.
- Production repeated automated sends without separate review.
- Removing Human Review.
- Removing Manual Execution Confirmation.
- Bypassing Strategy Evaluation Harness.
- Bypassing Evaluation-First Gate.
- Bypassing Negative Case Regression.
- Bypassing Paper Send Preflight.
- Leaving `PAPER_ORDER_EXECUTION_ENABLED` enabled.
- Leaving `PAPER_AUTOMATED_SEND_ENABLED` enabled.
- Leaving `PAPER_SOAK_TEST_ACCELERATED` enabled.

## Required Gates Before Any Future Accelerated Soak Run

- Full tests PASS.
- Architecture validation PASS.
- V10 full pipeline dry-run regression PASS.
- Automated paper send mocked regression PASS.
- Soak framework PASS.
- Accelerated cooldown PASS.
- Strategy Evaluation PASS.
- Evaluation-First Gate EVALUATION_GATE_PASSED.
- Negative Case Regression PASS.
- Candidate created from valid TRADE_PROPOSAL.
- Human Review approved.
- Finalized Paper Order Request exists.
- Manual Execution Confirmation exists.
- Paper Send Preflight PAPER_ORDER_SEND_ALLOWED.
- Kill switch inactive.
- Daily order limit not exceeded.
- Daily notional limit not exceeded.
- Accelerated cooldown satisfied.
- Previous reconciliation exists and matched.
- Previous post-mortem exists with no blockers.
- No unresolved issue exists.
- Alpaca paper account confirmed.
- Live endpoint rejected.

Future accelerated soak runs require explicit enablement of:

- `PAPER_ORDER_EXECUTION_ENABLED=true`
- `PAPER_AUTOMATED_SEND_ENABLED=true`
- `PAPER_SOAK_TEST_ACCELERATED=true`
- `ALPACA_PAPER=true`

These flags must be restored to false immediately after the run:

- `PAPER_ORDER_EXECUTION_ENABLED=false`
- `PAPER_AUTOMATED_SEND_ENABLED=false`
- `PAPER_SOAK_TEST_ACCELERATED=false`

## Required Gates Before Any Production/Default Soak Run

- Full tests PASS.
- Architecture validation PASS.
- V10 full pipeline dry-run regression PASS.
- Automated paper send mocked regression PASS.
- Soak framework PASS.
- Strategy Evaluation PASS.
- Evaluation-First Gate EVALUATION_GATE_PASSED.
- Negative Case Regression PASS.
- Candidate created from valid TRADE_PROPOSAL.
- Human Review approved.
- Finalized Paper Order Request exists.
- Manual Execution Confirmation exists.
- Paper Send Preflight PAPER_ORDER_SEND_ALLOWED.
- Kill switch inactive.
- Daily order limit not exceeded.
- Daily notional limit not exceeded.
- Production/default 24-hour cooldown satisfied.
- Previous reconciliation exists and matched.
- Previous post-mortem exists with no blockers.
- No unresolved issue exists.
- Alpaca paper account confirmed.
- Live endpoint rejected.
- Separate review for production/default repeated automated sends completed.

## Required Environment Handling

`.env.local` is local only and must never be committed.

Secrets must never be printed, logged, committed, or written to reports.

`PAPER_ORDER_EXECUTION_ENABLED` must remain disabled by default.

`PAPER_AUTOMATED_SEND_ENABLED` must remain disabled by default.

`PAPER_SOAK_TEST_ACCELERATED` must remain disabled by default.

`PAPER_SOAK_TEST_COOLDOWN_SECONDS` may remain configured, but accelerated mode must stay disabled unless explicitly needed for a paper-only soak validation run.

## Required Artifact Handling

Every paper send must produce reconciliation.

Every paper send must produce a post-mortem.

Artifacts must not contain secrets.

Artifacts must record paper-only status, order status, reconciliation status, risk limit status, cooldown status, and post-send restoration status.

## Required Post-Send Behavior

Every paper send must return the system to DRY_RUN_ONLY.

These flags must be restored to false immediately after each accelerated soak run:

- `PAPER_ORDER_EXECUTION_ENABLED=false`
- `PAPER_AUTOMATED_SEND_ENABLED=false`
- `PAPER_SOAK_TEST_ACCELERATED=false`

Reconciliation must be completed after each paper send.

A post-mortem must be completed after each paper send.

No further send may proceed while reconciliation, post-mortem, or unresolved issue status is incomplete.

## Required Review Behavior

Each paper send must be reviewed before any subsequent paper send.

Review must verify gate compliance, order limit compliance, notional limit compliance, cooldown compliance, reconciliation status, post-mortem status, and issue status.

Review must preserve NO_TRADE discipline and rejection quality.

## Conditions Before Continuing Accelerated Soak

- Accelerated soak must remain paper-only.
- Accelerated cooldown may be used only for paper soak framework validation.
- Accelerated cooldown does not authorize higher frequency outside accelerated paper soak test mode.
- Accelerated cooldown does not authorize live trading.
- Accelerated cooldown does not authorize increasing notional.
- All required accelerated soak gates must pass before each run.
- Environment flags must be explicitly enabled only for the run.
- Environment flags must be restored to false immediately after the run.

## Conditions Before Production/Default Repeated Automated Paper Sends

- Production/default cooldown remains 24 hours.
- Production/default repeated automated paper sends require separate review.
- Production/default repeated automated paper sends require separate soak evidence.
- Production/default repeated automated paper sends require separate audit.
- No accelerated-mode result may be treated as authorization for production frequency increase.
- Human Review and Manual Execution Confirmation must remain mandatory.

## Conditions Before Increasing Notional

- Future sends remain max notional <= 100 USD.
- Increasing notional remains prohibited after V14.
- V14 does not authorize increasing notional.
- Any notional increase requires separate design, implementation, regression, safety review, and audit.

## Conditions Before Multi-Symbol Automation

- Future sends remain one symbol only.
- Multi-symbol automation remains prohibited after V14.
- Any multi-symbol automation requires separate design, implementation, regression, safety review, and audit.

## Conditions Before Live Trading

- Live trading remains unsupported.
- Live endpoints remain prohibited.
- Accelerated cooldown does not authorize live trading.
- V14 does not authorize live trading.
- Any live trading consideration requires a separate governance baseline, separate design, separate implementation, separate audit, and explicit approval outside V14.

## Emergency Stop Procedure

1. Set `PAPER_ORDER_EXECUTION_ENABLED=false` in `.env.local`.
2. Set `PAPER_AUTOMATED_SEND_ENABLED=false` in `.env.local`.
3. Set `PAPER_SOAK_TEST_ACCELERATED=false` in `.env.local`.
4. Return system to DRY_RUN_ONLY.
5. Stop all send attempts.
6. Run architecture validation.
7. Run full tests.
8. Inspect latest artifacts.
9. Complete post-mortem before resuming.

## Fixed Paper Send Constraints

- Future sends remain max notional <= 100 USD.
- Future sends remain one symbol only.
- Future sends remain one order only.
- Future sends remain limit order only.
- Future sends remain day time-in-force only.
- Every paper send must produce reconciliation and post-mortem.
- Every paper send must return system to DRY_RUN_ONLY.
