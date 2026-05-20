# Phase 52 Automated Paper Send Soak Test Run Plan

## 1. Purpose

Define the first controlled automated paper send soak test run plan after Phase 51.

This plan must not send orders.
This plan must not authorize live trading.
This plan must not authorize increasing notional.
This plan must not authorize multi-symbol automation.
This plan must not authorize batch orders.
This plan must not authorize cancel/replace.

## 2. Context

- Baseline V13: `PASS`.
- Operating Policy After V13: `PASS`.
- Phase 50 Automated Paper Send Soak Testing Design: `PASS`.
- Phase 51 Automated Paper Send Soak Testing Implementation: `PASS`.

V13 proved one real automated Alpaca paper send completed successfully with reconciliation matched. Phase 51 implemented the soak framework and tests without sending real orders or calling Alpaca.

## 3. Soak Test Scope

The first soak test window must be conservative.

The first soak is paper trading only. It is not live trading, not increased notional, not multi-symbol automation, not batch orders, and not cancel/replace.

## 4. Required Initial Soak Limits

Required initial soak limits:

- Paper trading only.
- One symbol only.
- Max one automated paper order per day.
- Max notional `<= 100 USD`.
- Limit order only.
- Day time-in-force only.
- Maximum soak window: 5 trading days.
- Maximum submitted paper orders during first soak: 3.
- Minimum cooldown: 24 hours between submitted automated paper orders.
- Stop immediately on any reconciliation mismatch.
- Stop immediately on any missing post-mortem.
- Stop immediately on any unresolved issue.
- Stop immediately on any live endpoint detection.
- Stop immediately on any secret exposure.
- Stop immediately on any failed V13 gate.

## 5. Required Before Each Soak Run

Before each soak run:

1. Full tests `PASS`.
2. Architecture validation `PASS`.
3. V10 full pipeline dry-run regression `PASS`.
4. Automated paper send mocked regression `PASS`.
5. Soak framework status `PASS`.
6. Strategy Evaluation `PASS`.
7. Evaluation-First Gate `EVALUATION_GATE_PASSED`.
8. Negative Case Regression `PASS`.
9. Candidate created from valid `TRADE_PROPOSAL`.
10. Human Review status `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
11. Finalized Paper Order Request status `PAPER_ORDER_REQUEST_FINALIZED`.
12. Manual Execution Confirmation status `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
13. Paper Send Preflight status `PAPER_ORDER_SEND_ALLOWED`.
14. Automation kill switch inactive.
15. Daily order limit not exceeded.
16. Daily notional limit not exceeded.
17. Cooldown satisfied.
18. Previous reconciliation exists and matched.
19. Previous post-mortem exists with no blockers.
20. No unresolved issue exists.
21. Alpaca paper account confirmed.
22. Live endpoint rejected.
23. `PAPER_ORDER_EXECUTION_ENABLED=true` only for the run.
24. `PAPER_AUTOMATED_SEND_ENABLED=true` only for the run.
25. `ALPACA_PAPER=true`.
26. Secrets present but never printed.

If any required check fails, the soak run is blocked before order submission.

## 6. Required After Each Soak Run

After each soak run:

1. Disable or unset `PAPER_ORDER_EXECUTION_ENABLED`.
2. Disable or unset `PAPER_AUTOMATED_SEND_ENABLED`.
3. Confirm `DRY_RUN_ONLY` restored.
4. Write automated paper send report.
5. Write automation audit log.
6. Write reconciliation artifact.
7. Write post-send safety artifact.
8. Write post-mortem.
9. Update soak run registry.
10. Update daily limits tracker.
11. Update cooldown tracker.
12. Update quality review.
13. Check stop conditions before next run.

No next run may start until these post-run requirements are complete.

## 7. Required Stop Conditions

Required stop conditions:

- Reconciliation mismatch.
- Missing reconciliation.
- Missing post-mortem.
- Unresolved issue.
- Kill switch active.
- Daily order limit exceeded.
- Daily notional limit exceeded.
- Cooldown violation.
- Approval-rate red flag.
- No-trade/rejection quality degradation.
- Journal quality degradation.
- Evaluation score inflation.
- Rubber-stamping detected.
- Live endpoint detected.
- Secret exposure.
- Batch/cancel/replace attempt.
- Any failed V13 gate.

If any stop condition occurs, recommendation must be determined by the Phase 51 recommendation rules before any future soak run is considered.

## 8. Required Final Soak Report

Required final soak report:

```text
reports/automated_paper_send_soak/<timestamp>/SOAK_FINAL_REPORT.md
```

Final report must include:

- Soak window.
- Attempted runs.
- Submitted paper orders.
- Blocked runs.
- Reconciliation summary.
- Post-mortem summary.
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
- Live trading remains unsupported.
- Increasing notional remains prohibited.
- Multi-symbol automation remains prohibited.
- Batch orders remain prohibited.
- Cancel/replace remains prohibited.

## 9. Recommendation Rules

Recommendation rules:

- If any reconciliation mismatch occurs, recommendation must be `HOLD`.
- If any missing post-mortem occurs, recommendation must be `HOLD`.
- If any unresolved issue exists, recommendation must be `HOLD`.
- If approval-rate red flags return, recommendation must be `HOLD` or `CONTINUE_SOAK`.
- If no-trade/rejection quality degrades, recommendation must be `HOLD` or `CONTINUE_SOAK`.
- If journal quality degrades, recommendation must be `HOLD` or `CONTINUE_SOAK`.
- If first soak completes cleanly, recommendation may be `CONTINUE_SOAK` or `DESIGN_NEXT_PHASE`.
- Do not recommend live trading.
- Do not recommend increasing notional.
- Do not recommend multi-symbol automation.

## 10. Safety Boundaries

Safety boundaries:

- Live trading remains unsupported.
- Live endpoints remain prohibited.
- Increasing notional remains prohibited.
- Multi-symbol automation remains prohibited.
- Batch orders remain prohibited.
- Cancel/replace remains prohibited.
- Human Review remains required.
- Manual Execution Confirmation remains required.
- `PAPER_ORDER_EXECUTION_ENABLED` must remain disabled by default.
- `PAPER_AUTOMATED_SEND_ENABLED` must remain disabled by default.
- Secrets must never be printed, logged, committed, or written to reports.

## 11. Phase 52 Success Criteria

Phase 52 succeeds only if this run plan is complete, conservative, and consistent with Baseline V13, Operating Policy After V13, Phase 50 design, and Phase 51 implementation.

Phase 52 does not execute the soak. It only defines the first soak run plan.
