# Phase 48 One Real Automated Paper Send Design

## Purpose

Design one real automated Alpaca paper send.

This is one controlled automated paper send only. This is paper trading only. This is not live trading. This is not multi-symbol automation. This is not higher frequency. This is not increased notional. This is not batch trading. This is not cancel/replace.

## Context

- Baseline V12: PASS
- Phase 44 Automated Paper Send Design: PASS
- Phase 45 Automated Paper Send Implementation: PASS
- Phase 47 Automated Paper Send Mocked Regression: PASS

Phase 47 proved the automated paper send path can pass end-to-end with a mocked Alpaca client while enforcing safety gates, limits, kill switch, cooldown, reconciliation dependency, post-mortem dependency, unresolved issue blocking, and audit logging.

Phase 48 is the design for exactly one real Alpaca paper send through the automated paper send path.

## Required Default State

- `DRY_RUN_ONLY` remains default.
- `PAPER_ORDER_EXECUTION_ENABLED=false` by default.
- `PAPER_AUTOMATED_SEND_ENABLED=false` by default.

## Required Flags For This One Run Only

All three flags must be true only for the explicit one-run execution context:

- `PAPER_ORDER_EXECUTION_ENABLED=true`
- `PAPER_AUTOMATED_SEND_ENABLED=true`
- `ALPACA_PAPER=true`

After the run, `PAPER_ORDER_EXECUTION_ENABLED` and `PAPER_AUTOMATED_SEND_ENABLED` must be unset or disabled.

## Required Pre-Send Checks

1. Full tests PASS.
2. Architecture validation PASS.
3. V10 full pipeline dry-run regression PASS.
4. Automated paper send mocked regression PASS.
5. Strategy Evaluation PASS.
6. Evaluation-First Gate `EVALUATION_GATE_PASSED`.
7. Negative Case Regression PASS.
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

If any check fails, the send must block before order submission and write an explicit block reason.

## Required Send Constraints

- One automated paper send only.
- One symbol only.
- One order only.
- Paper trading only.
- Max notional <= 100 USD.
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

## Required Send Behavior

- Submit exactly one Alpaca paper limit/day order only if all checks pass.
- If any check fails, block before send.
- If blocked, write explicit block reason.
- If submitted, write Alpaca paper order id.
- Always write automated paper send report.
- Always write automation audit log.
- If submitted, run reconciliation.
- If submitted, write post-send safety.
- If submitted, write post-mortem.
- Always return system to `DRY_RUN_ONLY`.
- Always require `PAPER_ORDER_EXECUTION_ENABLED` unset/disabled after run.
- Always require `PAPER_AUTOMATED_SEND_ENABLED` unset/disabled after run.

## Required Artifacts

```text
reports/one_real_automated_paper_send/<timestamp>/ONE_REAL_AUTOMATED_PAPER_SEND_REPORT.md
reports/one_real_automated_paper_send/<timestamp>/AUTOMATION_AUDIT_LOG.md
reports/one_real_automated_paper_send/<timestamp>/RECONCILIATION.md
reports/one_real_automated_paper_send/<timestamp>/POST_SEND_SAFETY.md
reports/one_real_automated_paper_send/<timestamp>/POST_MORTEM.md
```

## Required Report Contents

The report must include:

- Full tests status.
- Architecture validation status.
- V10 full pipeline dry-run regression status.
- Automated paper send mocked regression status.
- Strategy evaluation status.
- Evaluation gate status.
- Negative case regression status.
- Candidate status.
- Human review status.
- Finalized request status.
- Manual execution confirmation status.
- Paper send preflight status.
- Automation kill switch status.
- Daily order limit status.
- Daily notional limit status.
- Cooldown status.
- Previous reconciliation status.
- Previous post-mortem status.
- Unresolved issue status.
- Paper account confirmation.
- Live endpoint rejection.
- Send status.
- Alpaca paper order id if submitted.
- Reconciliation status.
- System returned to `DRY_RUN_ONLY`.
- Flags disabled/unset after run.
- Statement: This was one controlled automated paper send only.
- Statement: Live trading remains unsupported.
- Statement: Increasing notional remains prohibited.
- Statement: Batch orders remain prohibited.
- Statement: Cancel/replace remains prohibited.
- Statement: Multi-symbol automation remains prohibited.

## Success Criteria

- If all gates pass, exactly one Alpaca paper order is submitted.
- If submitted, reconciliation is `RECONCILIATION_MATCHED`.
- If blocked, no order is sent and block reason is explicit.
- No live endpoint is used.
- Secrets are not printed.
- System returns to `DRY_RUN_ONLY`.
- `PAPER_ORDER_EXECUTION_ENABLED` is unset/disabled after run.
- `PAPER_AUTOMATED_SEND_ENABLED` is unset/disabled after run.

## Failure Conditions

- Any missing or failed gate.
- Kill switch active.
- Daily order limit exceeded.
- Daily notional limit exceeded.
- Cooldown not satisfied.
- Previous reconciliation missing or mismatched.
- Previous post-mortem missing or blocking.
- Unresolved issue exists.
- Live endpoint detected.
- Non-paper account.
- Notional > 100 USD.
- Non-limit order.
- Non-day time-in-force.
- Short/crypto/options/margin/extended-hours.
- Batch/cancel/replace.
- Secret exposure.

## What Remains Prohibited After This Run

- General automated paper send.
- Repeated automated sends.
- Live trading.
- Live endpoints.
- Increasing notional.
- Batch orders.
- Cancel/replace.
- Multi-symbol automation.
- Higher frequency.
- Removing human review.
- Removing manual execution confirmation.
- Bypassing V12 gates.
