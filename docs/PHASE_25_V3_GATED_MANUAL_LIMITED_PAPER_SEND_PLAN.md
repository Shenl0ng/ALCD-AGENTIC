# Phase 25 V3-Gated Manual Limited Paper Send Plan

## 1. Purpose

Phase 25 defines how to run one manual limited paper send under Baseline Selective Evaluation V3.

Baseline Selective Evaluation V3 is `PASS`.

V3 means:

- V1: safe paper execution plus reconciliation.
- V2: V1 plus mandatory Evaluation-First Gate.
- V3: V2 plus negative-case dataset and negative-case regression.

This is a plan only. It does not send orders, enable `PAPER_ORDER_EXECUTION_ENABLED`, use Alpaca API, modify runtime code, add features, create `.env` files, print secrets, or authorize live trading.

## 2. Entry Criteria

Entry criteria:

- Baseline Selective Evaluation V3 status is `PASS`.
- `docs/BASELINE_SELECTIVE_EVALUATION_V3.md` exists and is reviewed.
- Phase 22 negative-case dataset exists.
- Phase 24 negative-case regression report exists.
- The proposed send is one manual paper send only.
- The proposed send remains paper trading only.
- The proposed notional is `<= 100 USD`.
- The proposed order type is limit only.
- The proposed time in force is `day`.
- The proposed send uses one order maximum.
- No live trading, automation, higher frequency, or notional increase is requested.

## 3. Required Pre-Send Checks

Required pre-send checks:

- Full test suite: `PASS`.
- Architecture validation: `PASS`.
- Strategy Evaluation Harness: `PASS`.
- Evaluation-First Gate: `PASS`.
- Negative-case regression: `PASS`.
- Dry-run: `PASS`.
- Mocked paper send: `PASS`.
- Alpaca paper account confirmed.
- Live endpoint rejected.
- `PAPER_ORDER_EXECUTION_ENABLED` enabled only for this manual run.

If any required pre-send check fails, stop.

## 4. V3-Specific Checks

Required V3-specific checks:

- Negative-case dataset exists.
- Negative-case regression report exists.
- Negative-case regression thresholds: `PASS`.
- No negative case produces paper send readiness.
- No negative case produces broker execution readiness.
- Proposal does not match known negative-case failure patterns.
- Proposal is not a weak setup.
- Proposal is not a forced trade.
- Proposal is not rubber-stamped.
- Proposal has specific higher-timeframe context.
- Proposal has specific liquidity location.
- Proposal has observable confirmation.
- Proposal has fixed risk.
- Proposal has credible invalidation.
- Proposal has journal-ready thesis.

If the proposal resembles a known negative case, stop and record a no-trade or rejection decision.

## 5. Strategy Evaluation Requirements

Strategy Evaluation Harness must confirm:

- Higher-timeframe context quality is specific.
- Liquidity location quality is specific and price-relevant.
- Session timing is valid.
- Entry confirmation is observable.
- Fixed risk is present.
- Reward/risk is acceptable.
- Journal readiness is present.
- Data freshness and completeness are valid.
- Specialist agent sequencing is intact.
- Risk Manager decision quality is acceptable.
- No-trade discipline is preserved.
- Rejection quality remains strong.

Strategy Evaluation status must be `PASS` before the Evaluation-First Gate may proceed.

## 6. Evaluation-First Gate Requirements

Evaluation-First Gate must confirm:

- Strategy Evaluation status is `PASS`.
- Evaluation score meets the required threshold.
- Required dimensions meet tightened requirements.
- ADLC compliance is `PASS`.
- Data integrity is `PASS`.
- Journal reference is present.
- No hard-fail condition exists.
- No approval-rate hard block is active.
- No generic context, weak liquidity, vague confirmation, generic thesis, missing invalidation, forced trade, rubber-stamping, or live trading assumption is present.

No Human Approval, Paper Order Request, or Paper Send may proceed without `EVALUATION_GATE_PASSED`.

## 7. Negative-Case Regression Requirements

Negative-case regression must confirm:

- Total negative cases were evaluated.
- Regression status is `PASS`.
- Threshold results are `PASS`.
- Missed blocks: none.
- False passes: none.
- `NO_TRADE` recognition remains at or above required threshold.
- Weak setup rejection remains at or above required threshold.
- Rubber-stamping cases are detected or blocked.
- Journal/evidence failure cases are detected or blocked.
- Live trading assumption cases are blocked.
- No negative case produces paper send readiness.
- No negative case produces broker execution readiness.

Negative-case regression protections may not be bypassed.

## 8. Risk Manager Requirements

Risk Manager must confirm:

- Paper trading only.
- Max notional `<= 100 USD`.
- Fixed risk before send.
- Stop loss is defined.
- Credible invalidation is defined.
- Reward/risk is acceptable.
- No short selling.
- No crypto.
- No options.
- No margin or leverage.
- No extended hours.
- No batch orders.
- No cancel/replace.
- No notional increase.
- No frequency increase.

Risk Manager output must be `RISK_APPROVED`. Any risk rejection stops the run.

## 9. Human Approval Requirements

Human Approval must confirm:

- Evaluation-First Gate passed.
- Negative-case regression passed.
- The proposal does not match known negative-case failure patterns.
- The proposal is not rubber-stamped.
- The reviewer can explain why no-trade is not the better decision.
- The reviewer can identify the specific higher-timeframe context.
- The reviewer can identify the specific liquidity location.
- The reviewer can identify the observable confirmation.
- The reviewer can identify fixed risk and invalidation.
- The reviewer can confirm journal readiness.

Human Approval must be independent. Repeating automated scores without challenge is not approval.

## 10. Journal Commit Requirements

Journal Commit must exist before send and include:

- Proposal identifier.
- Strategy Evaluation result.
- Evaluation-First Gate result.
- Negative-case regression reference.
- Risk Manager result.
- Human Approval result.
- Manual Execution Confirmation requirement.
- Higher-timeframe context.
- Liquidity location.
- Observable confirmation.
- Fixed risk.
- Credible invalidation.
- Why no-trade was not selected.
- Paper-only boundary.

No journal commit means no send.

## 11. Manual Execution Confirmation Requirements

Manual Execution Confirmation must confirm:

- This is one manual paper send only.
- The account mode is paper.
- The order is limit only.
- Time in force is `day`.
- Notional is `<= 100 USD`.
- No live endpoint is used.
- No batch order is used.
- No cancel/replace is used.
- No automation is used.
- `PAPER_ORDER_EXECUTION_ENABLED` is enabled only for this manual run.
- The system will return to `DRY_RUN_ONLY` after the run.

No manual confirmation means no send.

## 12. Paper Order Request Requirements

Paper Order Request may be created only after:

- Strategy Evaluation Harness: `PASS`.
- Evaluation-First Gate: `EVALUATION_GATE_PASSED`.
- Negative-case regression: `PASS`.
- Risk Manager: `RISK_APPROVED`.
- Human Approval: approved for paper only.
- Journal Commit: present.
- Manual Execution Confirmation: present.

The request must remain paper-only and must not be created from any negative case.

## 13. Paper Send Preflight Requirements

Paper Send Preflight must confirm:

- Paper account mode.
- Live endpoint rejected.
- `PAPER_ORDER_EXECUTION_ENABLED` is enabled only for the manual run.
- One order maximum.
- Limit order only.
- Time in force: `day`.
- Max notional `<= 100 USD`.
- No short selling.
- No crypto.
- No options.
- No margin or leverage.
- No extended hours.
- No batch orders.
- No cancel/replace.
- Evaluation-First Gate reference exists and passed.
- Negative-case regression reference exists and passed.
- Journal commit exists.
- Manual confirmation exists.

If preflight blocks the send, treat the block as valid safety behavior.

## 14. Paper Send Constraints

Paper send constraints:

- One manual paper send only.
- Paper trading only.
- Controlled Alpaca paper send only after all gates pass.
- Max notional `<= 100 USD`.
- Limit order only.
- Time in force: `day`.
- One order maximum.
- No batch orders.
- No automation.
- No live trading.
- No live endpoints.
- No short selling.
- No crypto.
- No options.
- No margin or leverage.
- No extended hours.
- No cancel/replace.
- No increase in notional.
- No increase in frequency.

## 15. Reconciliation Requirements

If the paper send is submitted, reconciliation must confirm:

- Broker-side paper order identifier is recorded.
- Submitted symbol matches request.
- Submitted side matches request.
- Submitted quantity or notional matches request constraints.
- Submitted order type is limit.
- Submitted time in force is `day`.
- Account mode remains paper.
- No live endpoint was used.
- Reconciliation status is `RECONCILIATION_MATCHED`.

If reconciliation does not match, stop further sends and create a failure report.

## 16. Post-Mortem Requirements

Post-mortem must include:

- Whether the send was submitted or safely blocked.
- All gate statuses.
- Strategy Evaluation result.
- Evaluation-First Gate result.
- Negative-case regression reference and status.
- Risk Manager result.
- Human Approval result.
- Journal Commit status.
- Manual Execution Confirmation status.
- Paper Send Preflight result.
- Reconciliation result if submitted.
- Whether the system returned to `DRY_RUN_ONLY`.
- Whether `PAPER_ORDER_EXECUTION_ENABLED` was unset after the run.
- Whether secrets were protected.
- Whether live trading remained untouched.
- Lessons learned.

## 17. Failure Conditions

Failure conditions:

- Full test suite fails.
- Architecture validation fails.
- Strategy Evaluation Harness fails.
- Evaluation-First Gate fails.
- Negative-case regression fails.
- Negative-case regression has missed blocks.
- Negative-case regression has false passes.
- Proposal matches a known negative-case pattern.
- Proposal is a weak setup.
- Proposal is a forced trade.
- Proposal is rubber-stamped.
- Risk Manager rejects.
- Human Approval is missing or rubber-stamped.
- Journal Commit is missing.
- Manual Execution Confirmation is missing.
- Paper Send Preflight fails.
- Live endpoint is not rejected.
- Paper account mode cannot be confirmed.
- Notional exceeds `100 USD`.
- Order is not limit.
- Time in force is not `day`.
- More than one order is attempted.
- Any automation appears.
- Any live trading assumption appears.

## 18. Stop Conditions

Stop immediately when:

- Any V3 gate fails.
- Negative-case regression fails.
- Proposal matches a known negative-case pattern.
- Evaluation-First Gate is not `EVALUATION_GATE_PASSED`.
- Risk Manager is not `RISK_APPROVED`.
- Human Approval is not valid.
- Journal Commit is missing.
- Manual Execution Confirmation is missing.
- Preflight blocks send.
- Reconciliation mismatches.
- `PAPER_ORDER_EXECUTION_ENABLED` is enabled outside the manual run window.
- Any live endpoint is touched.
- Any secret would be printed.

If send is blocked safely, treat it as valid safety behavior.

## 19. Success Criteria

Success criteria:

- Paper send status is `PAPER_ORDER_SUBMITTED` or safely blocked before send.
- If submitted, reconciliation is `RECONCILIATION_MATCHED`.
- System returns to `DRY_RUN_ONLY`.
- `PAPER_ORDER_EXECUTION_ENABLED` is unset after run.
- Secrets are not printed.
- No live trading is touched.
- No automation is introduced.
- No notional increase occurs.
- No frequency increase occurs.
- All required artifacts are produced.

## 20. What Remains Prohibited

The following remain prohibited:

- Live trading.
- Live endpoints.
- Increasing notional.
- Increasing frequency.
- Automation.
- Batch orders.
- Cancel/replace.
- Market orders.
- Short selling.
- Crypto.
- Options.
- Margin or leverage.
- Extended hours.
- More than one order.
- Bypassing Evaluation-First Gate.
- Bypassing negative-case regression protections.
- Bypassing Risk Manager.
- Bypassing Human Approval.
- Bypassing Journal Commit.
- Bypassing Manual Execution Confirmation.
- Broker execution from negative cases.
- Paper send readiness from negative cases.
- Creating `.env` files.
- Printing secrets.
- Recommending increasing notional.
- Recommending automation.
- Recommending live trading.

## 21. Required Artifacts

Required artifacts after run:

- Send result JSON.
- Evaluation gate artifact.
- Negative-case regression reference.
- Post-send journal entry.
- Reconciliation JSON.
- Post-send safety JSON.
- Controlled paper send report.
- Post-mortem.
- Phase 25 run summary.

The run summary must state whether the send was submitted or safely blocked.

## 22. Explicit Live Trading Boundary

Live trading remains unsupported.

Phase 25 does not design, imply, prepare, or authorize live trading. Any live trading assumption must stop the run.

## Recommendation Rules

Recommendation rules:

- If any V3 gate fails, stop.
- If negative-case regression fails, stop.
- If proposal matches a known negative-case pattern, stop.
- If send is blocked safely, treat as valid safety behavior.
- Do not recommend increasing notional.
- Do not recommend automation.
- Do not recommend live trading.

## Safety Statement

This document is a plan only.

No order was sent by this plan. No runtime code was changed by this plan. `PAPER_ORDER_EXECUTION_ENABLED` was not enabled by this plan. Alpaca API was not used by this plan. No `.env` file was created by this plan. No secrets were printed by this plan.
