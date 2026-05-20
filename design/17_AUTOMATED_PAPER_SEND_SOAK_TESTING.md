# Phase 50 Automated Paper Send Soak Testing Design

## 1. Purpose

Design a controlled paper-only soak testing program for repeated automated paper sends over time.

This phase is design only.

This design does not authorize live trading.
This design does not authorize increasing notional.
This design does not authorize multi-symbol automation.
This design does not authorize batch orders.
This design does not authorize cancel/replace.
This design does not remove Human Review.
This design does not remove Manual Execution Confirmation.

Soak testing means repeated automated paper sends may be tested only under strict limits, monitoring, reconciliation, post-mortem, daily caps, cooldowns, kill switch, and review requirements.

## 2. Context

Baseline V13 is `PASS`.

Operating Policy After V13 is `PASS`.

V13 proves one real automated Alpaca paper send completed successfully with reconciliation matched.

V13 does not authorize repeated automated sends. Phase 50 defines the design requirements that must exist before repeated automated paper-send testing can be implemented or run.

## 3. Required Default State

Default state:

- `DRY_RUN_ONLY` remains default.
- `PAPER_ORDER_EXECUTION_ENABLED=false` by default.
- `PAPER_AUTOMATED_SEND_ENABLED=false` by default.

Automated paper send soak testing must not run by default.

`PAPER_ORDER_EXECUTION_ENABLED` and `PAPER_AUTOMATED_SEND_ENABLED` must be disabled or unset after every individual run.

## 4. Required Flags Per Run

All three flags must be true for an individual approved soak run:

- `PAPER_ORDER_EXECUTION_ENABLED=true`
- `PAPER_AUTOMATED_SEND_ENABLED=true`
- `ALPACA_PAPER=true`

Flags must be enabled only for the individual run and disabled or unset immediately after.

These flags authorize only one paper-only soak run attempt after all V13 gates pass. They do not authorize live trading, live endpoints, increasing notional, batch orders, cancel/replace, multi-symbol automation, higher frequency, or bypassing any gate.

## 5. Soak Test Constraints

Soak test constraints:

- Paper trading only.
- One symbol only.
- Max one automated paper order per day.
- Max notional `<= 100 USD`.
- Limit order only.
- Day time-in-force only.
- No short selling.
- No crypto.
- No options.
- No margin/leverage.
- No extended hours.
- No batch orders.
- No cancel/replace.
- No live trading.
- No live endpoints.
- No multi-symbol automation.
- No higher frequency.

Any violation blocks the soak run before order submission.

## 6. Required Gates Before Every Soak Run

Before every soak run, all gates must pass:

1. Full tests `PASS`.
2. Architecture validation `PASS`.
3. V10 full pipeline dry-run regression `PASS`.
4. Automated paper send mocked regression `PASS`.
5. Strategy Evaluation `PASS`.
6. Evaluation-First Gate `EVALUATION_GATE_PASSED`.
7. Negative Case Regression `PASS`.
8. Candidate created from valid `TRADE_PROPOSAL`.
9. Human Review status `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
10. Finalized Paper Order Request status `PAPER_ORDER_REQUEST_FINALIZED`.
11. Manual Execution Confirmation status `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
12. Paper Send Preflight status `PAPER_ORDER_SEND_ALLOWED`.
13. Automation kill switch inactive.
14. Daily order limit not exceeded.
15. Daily notional limit not exceeded.
16. Cooldown satisfied.
17. Previous reconciliation exists and matched.
18. Previous post-mortem exists with no blockers.
19. No unresolved issue exists.
20. Alpaca paper account confirmed.
21. Live endpoint rejected.
22. Secrets present but never printed.

If any gate is missing, failed, stale, or ambiguous, the soak run must be blocked before order submission and write an explicit block reason.

## 7. Required Soak Controls

Required soak controls:

1. Soak run registry.
2. Daily order counter.
3. Daily notional tracker.
4. Cooldown tracker.
5. Kill switch.
6. Previous reconciliation dependency.
7. Previous post-mortem dependency.
8. Unresolved issue blocker.
9. Consecutive failure counter.
10. Consecutive success counter.
11. Reconciliation mismatch block.
12. Post-mortem blocker.
13. Approval-rate monitoring.
14. No-trade/rejection quality monitoring.
15. Journal quality monitoring.
16. Automation audit log.
17. End-of-soak summary report.

These controls are mandatory for soak testing. A soak run without these controls is not authorized.

## 8. Soak Run Registry

The soak run registry must record every attempted soak run.

For each attempted run, the registry must include:

- Timestamp.
- Run identifier.
- Symbol.
- Proposed notional.
- Gate status summary.
- Human Review status.
- Manual Execution Confirmation status.
- Paper Send Preflight status.
- Send decision.
- Submitted paper order id if submitted.
- Reconciliation status.
- Post-mortem status.
- Block reason if blocked.
- Flag cleanup status.

The registry must include blocked runs as well as submitted paper orders.

## 9. Daily Limits And Cooldown

Daily limits:

- Max one automated paper order per day.
- Max daily automated notional `<= 100 USD`.

Cooldown:

- Cooldown must be satisfied before every soak run.
- Cooldown violation blocks before order submission.
- Cooldown status must be written to the soak daily limits artifact.

Daily order and notional limits must count all submitted automated paper orders in the soak period.

## 10. Reconciliation And Post-Mortem Dependencies

Every submitted paper order must reconcile.

A future soak run is blocked unless the previous reconciliation exists and matched.

Every submitted paper order must have a post-mortem.

A future soak run is blocked unless the previous post-mortem exists and has no unresolved blockers.

Any reconciliation mismatch or missing reconciliation immediately stops the soak.

Any missing post-mortem or unresolved post-mortem blocker immediately stops the soak.

## 11. Quality Monitoring

Soak testing must monitor process quality, not profit.

Required quality monitoring:

- Approval-rate monitoring.
- No-trade/rejection quality monitoring.
- Journal quality monitoring.
- Evaluation score inflation monitoring.
- Rubber-stamping detection.

Repeated approvals without enough rejections or no-trades are a red flag.

Evaluation score inflation is a red flag.

Rubber-stamping is a red flag.

Journal quality degradation is a red flag.

Red flags must block or extend soak testing according to the recommendation rules.

## 12. Required Soak Stop Conditions

The soak must stop immediately if any stop condition occurs:

- Any reconciliation mismatch.
- Missing reconciliation.
- Missing post-mortem.
- Unresolved post-mortem blocker.
- Kill switch active.
- Secret exposure.
- Live endpoint detected.
- More than one order in a day.
- Daily notional exceeded.
- Cooldown violation.
- Batch/cancel/replace attempt.
- Repeated approvals without enough rejections/no-trades.
- Evaluation score inflation.
- Rubber-stamping detected.
- Journal quality degradation.
- Any failed V13 gate.

When the soak stops, no further soak run may proceed until review and post-mortem are complete.

## 13. Required Soak Success Criteria

Soak success requires:

- Minimum planned soak period completed.
- All submitted paper orders reconciled matched.
- Every send has post-mortem.
- No unresolved issues.
- No live endpoint touched.
- No secrets printed.
- No notional increase.
- No batch/cancel/replace.
- No multi-symbol automation.
- No bypassed gates.
- Rejection/no-trade quality remains acceptable.
- Approval-rate remains acceptable.
- Journal quality remains acceptable.

Passing the soak does not authorize live trading, increasing notional, multi-symbol automation, batch orders, cancel/replace, or removal of Human Review or Manual Execution Confirmation.

## 14. Required Reports

Required reports:

```text
reports/automated_paper_send_soak/<timestamp>/SOAK_TEST_PLAN.md
reports/automated_paper_send_soak/<timestamp>/SOAK_RUN_REGISTRY.md
reports/automated_paper_send_soak/<timestamp>/SOAK_DAILY_LIMITS.md
reports/automated_paper_send_soak/<timestamp>/SOAK_QUALITY_REVIEW.md
reports/automated_paper_send_soak/<timestamp>/SOAK_FINAL_REPORT.md
```

Reports must not contain secrets.

Reports must state that live trading remains unsupported.

## 15. SOAK_TEST_PLAN Contents

`SOAK_TEST_PLAN.md` must include:

- Planned soak period.
- Maximum attempted runs.
- Maximum submitted paper orders.
- Daily order limit.
- Daily notional limit.
- Cooldown rule.
- Kill switch rule.
- Required V13 gates.
- Required artifacts per run.
- Stop conditions.
- Success criteria.
- Review cadence.

## 16. SOAK_RUN_REGISTRY Contents

`SOAK_RUN_REGISTRY.md` must include:

- Every attempted run.
- Every blocked run.
- Every submitted paper order.
- Gate summary for each run.
- Block reason for each blocked run.
- Reconciliation status for each submitted run.
- Post-mortem status for each submitted run.
- Flag cleanup status for each run.
- Confirmation that no live endpoint was used.

## 17. SOAK_DAILY_LIMITS Contents

`SOAK_DAILY_LIMITS.md` must include:

- Daily order counter.
- Daily notional tracker.
- Cooldown tracker.
- Kill switch status.
- Daily order limit compliance.
- Daily notional compliance.
- Cooldown compliance.
- Any daily limit violation.

## 18. SOAK_QUALITY_REVIEW Contents

`SOAK_QUALITY_REVIEW.md` must include:

- Approval-rate monitoring.
- No-trade/rejection quality monitoring.
- Journal quality monitoring.
- Evaluation score inflation review.
- Rubber-stamping review.
- Failure Auditor notes.
- Weekly Review notes.
- Recommendation impact.

## 19. SOAK_FINAL_REPORT Contents

`SOAK_FINAL_REPORT.md` must include:

- Soak period.
- Number of attempted runs.
- Number of submitted paper orders.
- Number of blocked runs.
- Reconciliation results.
- Post-mortem results.
- Daily order limit compliance.
- Daily notional compliance.
- Cooldown compliance.
- Kill switch events.
- Unresolved issues.
- Approval-rate analysis.
- No-trade/rejection analysis.
- Journal quality analysis.
- Safety violations.
- Recommendation: `HOLD`, `CONTINUE_SOAK`, or `DESIGN_NEXT_PHASE`.
- Statement: Live trading remains unsupported.
- Statement: Increasing notional remains prohibited.
- Statement: Multi-symbol automation remains prohibited.
- Statement: Batch orders remain prohibited.
- Statement: Cancel/replace remains prohibited.

## 20. Recommendation Rules

Recommendation rules:

- If any reconciliation mismatch occurs, recommendation must be `HOLD`.
- If any post-mortem blocker remains unresolved, recommendation must be `HOLD`.
- If approval-rate red flags return, recommendation must be `HOLD` or `CONTINUE_SOAK`.
- If no-trade/rejection quality degrades, recommendation must be `HOLD` or `CONTINUE_SOAK`.
- If journal quality degrades, recommendation must be `HOLD` or `CONTINUE_SOAK`.
- Do not recommend live trading.
- Do not recommend increasing notional.
- Do not recommend multi-symbol automation.

`DESIGN_NEXT_PHASE` may be recommended only when the soak period is complete, all submitted paper orders reconcile matched, all post-mortems are complete, no unresolved issues exist, no safety violations occurred, and quality monitoring remains acceptable.

## 21. Conditions Before Implementation

Before implementation:

- Operating Policy After V13 must remain `PASS`.
- V13 artifacts must remain available.
- V13 runtime/tests must be committed.
- `.env.local` must keep automation flags disabled by default.
- No unresolved V13 post-mortem issue may exist.

If any condition is missing, Phase 50 implementation is blocked.

## 22. What Remains Prohibited

Still prohibited:

- Live trading.
- Live endpoints.
- Increasing notional.
- Multi-symbol automation.
- Batch orders.
- Cancel/replace.
- Removing Human Review.
- Removing Manual Execution Confirmation.
- Removing Strategy Evaluation Harness.
- Bypassing Evaluation-First Gate.
- Bypassing Negative Case Regression.
- Bypassing Paper Send Preflight.
- Higher frequency beyond the designed soak cadence.
- Scheduled automated paper trading outside the approved soak design.
- Leaving `PAPER_ORDER_EXECUTION_ENABLED` enabled by default.
- Leaving `PAPER_AUTOMATED_SEND_ENABLED` enabled by default.

## 23. Live Trading Statement

Live trading remains unsupported.

Phase 50 is a paper-only soak testing design. It does not authorize live trading, increasing notional, multi-symbol automation, batch orders, cancel/replace, higher frequency, removal of Human Review, removal of Manual Execution Confirmation, or bypassing any V13 gate.
