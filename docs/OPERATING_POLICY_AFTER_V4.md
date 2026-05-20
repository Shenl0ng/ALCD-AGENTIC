# Operating Policy After V4

## 1. Purpose

This policy defines operating rules after Baseline V4.

Baseline V4 means:

- V1: safe paper execution plus reconciliation.
- V2: V1 plus mandatory Evaluation-First Gate.
- V3: V2 plus negative-case dataset and negative-case regression.
- V4: V3 plus successful V3-gated manual limited paper send.

## 2. Current Operating Baseline

V4 is the current operating baseline.

Manual limited paper sends are allowed only under V4 gates.

## 3. Default Operating Mode

`DRY_RUN_ONLY` is the default operating mode.

`PAPER_ORDER_EXECUTION_ENABLED` must be enabled only for the manual run and unset immediately after the run.

## 4. Manual Limited Paper Send Rules

Every send must be manual.

Max notional remains `<= 100 USD`.

Every send must pass:

- Full tests.
- Architecture validation.
- Strategy Evaluation Harness.
- Evaluation-First Gate.
- Negative Case Regression.
- Risk Manager.
- Human Approval.
- Journal Commit.
- Manual Execution Confirmation.
- Paper Send Preflight.
- Reconciliation.
- Post-Mortem.

No send may bypass any V4 gate.

## 5. Secret And Environment Policy

Secrets must never be printed, logged, committed, or written to reports.

`.env.local` is local only and must never be committed.

Do not create new `.env` files for normal operation.

## 6. Live Trading Boundary

Live trading remains unsupported.

Live endpoints remain prohibited.

Any live trading assumption is a stop condition.

## 7. Still Prohibited

The following remain prohibited:

- Increasing notional.
- Automation.
- Live trading.
- Live endpoints.
- Batch orders.
- Cancel/replace.
- Higher frequency.
- Bypassing Evaluation-First Gate.
- Bypassing Negative Case Regression.
- Bypassing Risk Manager.
- Bypassing Human Approval.
- Bypassing Journal Commit.
- Any execution from negative cases.
- Paper send readiness from negative cases.
- Broker execution readiness from negative cases.

## 8. Allowed Work After V4

Allowed work after V4:

- Manual limited paper sends under V4 gates.
- Offline quality review.
- Negative-case expansion.
- Improving rejection quality.
- Improving `NO_TRADE` discipline.
- Improving journal specificity.
- Improving strategy scoring.

## 9. Conditions Before Increasing Notional

Increasing notional remains prohibited unless a future process completes all of the following:

- Separate design phase.
- Separate implementation phase.
- Separate audit.
- Multiple clean V4 runs.
- No unresolved red flags.
- Improved rejection/no-trade metrics.
- Explicit human approval.

Until those conditions are met, max notional remains `<= 100 USD`.

## 10. Conditions Before Automation

Automation remains prohibited unless a future process completes all of the following:

- Separate design phase.
- Separate implementation phase.
- Separate audit.
- Strong no-trade discipline.
- Strong rejection quality.
- No approval-rate red flags.
- No rubber-stamping red flags.
- No live trading assumptions.
- Explicit human approval.

## 11. Stop Conditions

Stop immediately if:

- Any V4 gate fails.
- `PAPER_ORDER_EXECUTION_ENABLED` is enabled outside a manual run.
- A proposal matches a known negative-case failure pattern.
- A proposal is weak, forced, vague, generic, or rubber-stamped.
- Journal readiness is missing.
- Fixed risk or credible invalidation is missing.
- Any live endpoint is touched.
- Any secret would be printed or written.

## 12. Safety Statement

This policy is a markdown operating policy only.

No order was sent by this policy. No runtime code was changed by this policy. `PAPER_ORDER_EXECUTION_ENABLED` was not enabled by this policy. Alpaca API was not used by this policy. No `.env` file was created by this policy. No secrets were printed by this policy.
