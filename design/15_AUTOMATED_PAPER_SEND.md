# Phase 44 Automated Paper Send Design

## 1. Purpose

Design automated paper send for paper trading only.

This phase is design only.

This is not live trading.
This is not general automation.
This is not multi-symbol trading.
This is not increased notional.
This is not batch trading.
This is not cancel/replace.

Automated paper send means the system may submit one Alpaca paper order automatically only after every V12 gate passes and after explicit paper automation flags are enabled.

This design keeps automated paper send disabled by default.

This phase must not send orders.
This phase must not enable `PAPER_ORDER_EXECUTION_ENABLED`.
This phase must not use Alpaca API.
This phase must not modify runtime code.
This phase must not add live trading.
This phase must not create `.env` files.
This phase must not print secrets.

## 2. Context

Baseline V12 is `PASS`.

Operating Policy After V12 is `PASS`.

V12 proves the complete V10 pipeline can produce one successful controlled Alpaca paper send with reconciliation matched.

The current V12 allowed flow is:

```text
Automated dry-run
-> Strategy Evaluation Harness
-> Evaluation-First Gate
-> Negative Case Regression
-> Paper Order Request Candidate
-> Human Review Queue
-> Finalized Paper Order Request
-> Manual Execution Confirmation
-> Paper Send Preflight
-> Controlled Alpaca Paper Send
-> Reconciliation
-> Post-mortem
```

Phase 44 designs a narrower automated paper send extension, not a live trading system.

## 3. Required Default State

Default state:

- `PAPER_AUTOMATED_SEND_ENABLED=false`
- `PAPER_ORDER_EXECUTION_ENABLED=false`
- `DRY_RUN_ONLY` remains default

Automated paper send must not run by default.

`PAPER_ORDER_EXECUTION_ENABLED` and `PAPER_AUTOMATED_SEND_ENABLED` must be unset or disabled after any automated paper send run.

## 4. Required Automation Flags

All three automation flags must be true for automated paper send:

- `PAPER_AUTOMATED_SEND_ENABLED=true`
- `PAPER_ORDER_EXECUTION_ENABLED=true`
- `ALPACA_PAPER=true`

If any flag is missing or false, automated paper send must block.

These flags authorize only one paper-only automation run after all V12 gates pass. They do not authorize live trading, live endpoints, increased notional, batch orders, cancel/replace, multi-symbol automation, higher frequency, or bypassing any gate.

## 5. Required Pipeline Before Automated Send

Before automated send, all steps must pass:

1. Full tests `PASS`.
2. Architecture validation `PASS`.
3. V10 full pipeline dry-run regression `PASS`.
4. Strategy Evaluation `PASS`.
5. Evaluation-First Gate `EVALUATION_GATE_PASSED`.
6. Negative Case Regression `PASS`.
7. Candidate created from valid `TRADE_PROPOSAL`.
8. Human Review status `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
9. Finalized Paper Order Request status `PAPER_ORDER_REQUEST_FINALIZED`.
10. Manual Execution Confirmation status `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
11. Paper Send Preflight status `PAPER_ORDER_SEND_ALLOWED`.
12. Alpaca paper account confirmed.
13. Live endpoint rejected.
14. Automation limits `PASS`.
15. Kill switch not active.
16. Daily order limit not exceeded.
17. Daily notional limit not exceeded.
18. Cooldown satisfied.
19. No unresolved post-mortem issues.
20. No unresolved reconciliation mismatch.

Any missing or failed step blocks automated paper send.

## 6. Required Automated Paper Send Limits

Automated paper send limits:

- Paper trading only.
- One symbol only.
- One order per automation run.
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

## 7. Required New Controls

Automated paper send requires these new controls:

1. Automation kill switch.
2. Daily order limit.
3. Daily notional limit.
4. Cooldown between automated sends.
5. Reconciliation-required-before-next-send rule.
6. Post-mortem-required-before-next-send rule.
7. Unresolved-issue block.
8. Secrets redaction check.
9. Live endpoint block.
10. Paper account confirmation.
11. Automation audit log.

## 8. Automation Kill Switch

The automation kill switch must block all automated paper sends when active.

The kill switch must be checked before any Alpaca paper order submission attempt.

If the kill switch is active, status must be `AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH`.

## 9. Daily Limits

Daily limits:

- Max one automated paper order per day.
- Max daily automated notional `<= 100 USD`.

Daily limits must count only automated paper sends and must not be reset by rerunning the process.

If the daily order limit is exceeded, status must be `AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS`.

If the daily notional limit is exceeded, status must be `AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS`.

## 10. Cooldown Rule

Automated paper send must require a cooldown between automated sends.

The cooldown must be satisfied before any new automated send attempt.

Cooldown failure must block before Alpaca paper order submission.

## 11. Reconciliation And Post-Mortem Dependency

Automated paper send cannot run if the previous controlled or automated send is missing reconciliation.

Automated paper send cannot run if the previous reconciliation has an unresolved mismatch.

Automated paper send cannot run if the previous post-mortem is missing.

Automated paper send cannot run if unresolved post-mortem issues exist.

Missing or failed reconciliation must produce `AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION`.

Missing or unresolved post-mortem must produce `AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM`.

## 12. Required Automated Send Statuses

Allowed automated send statuses:

- `AUTOMATED_PAPER_SEND_ALLOWED`
- `AUTOMATED_PAPER_SEND_BLOCKED`
- `AUTOMATED_PAPER_SEND_SUBMITTED`
- `AUTOMATED_PAPER_SEND_REJECTED_BY_PREFLIGHT`
- `AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS`
- `AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH`
- `AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION`
- `AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM`
- `AUTOMATED_PAPER_SEND_ERROR`

No status may imply live trading approval.

## 13. Required Artifacts

Automated paper send must write:

```text
reports/automated_paper_send/<timestamp>/AUTOMATED_PAPER_SEND_REPORT.md
reports/automated_paper_send/<timestamp>/RECONCILIATION.md
reports/automated_paper_send/<timestamp>/POST_SEND_SAFETY.md
reports/automated_paper_send/<timestamp>/POST_MORTEM.md
reports/automated_paper_send/<timestamp>/AUTOMATION_AUDIT_LOG.md
```

Artifacts must not contain secrets.

## 14. Required Report Content

`AUTOMATED_PAPER_SEND_REPORT.md` must include:

- Automation flags.
- Symbol.
- Full test status.
- Architecture validation status.
- V10 pipeline regression status.
- Strategy evaluation status.
- Evaluation gate status.
- Negative case regression status.
- Candidate status.
- Human review status.
- Finalized request status.
- Manual execution confirmation status.
- Paper send preflight status.
- Automation limit checks.
- Kill switch status.
- Cooldown status.
- Daily order count.
- Daily notional used.
- Paper account confirmation.
- Live endpoint rejection.
- Paper send status.
- Alpaca paper order id if submitted.
- Reconciliation status.
- Post-mortem reference.
- Final status.
- Statement: Automated paper send is paper-only.
- Statement: Live trading remains unsupported.
- Statement: Increasing notional remains prohibited.
- Statement: Batch orders remain prohibited.
- Statement: Cancel/replace remains prohibited.

## 15. Automation Audit Log

`AUTOMATION_AUDIT_LOG.md` must record:

- Timestamp.
- Automation flags as true or false, without secret values.
- Gate statuses.
- Limit check results.
- Kill switch result.
- Cooldown result.
- Reconciliation dependency result.
- Post-mortem dependency result.
- Final automated send decision.
- Whether an Alpaca paper order was submitted.
- Operator-visible reason for block or submission.

The audit log must not contain secrets.

## 16. Hard Blocks

Automated paper send must hard-block on:

- `PAPER_AUTOMATED_SEND_ENABLED` is not true.
- `PAPER_ORDER_EXECUTION_ENABLED` is not true.
- `ALPACA_PAPER` is not true.
- Any V12 gate missing or failed.
- Paper Send Preflight not `PAPER_ORDER_SEND_ALLOWED`.
- Kill switch active.
- Daily order limit exceeded.
- Daily notional limit exceeded.
- Cooldown not satisfied.
- Previous reconciliation missing.
- Previous reconciliation mismatch unresolved.
- Previous post-mortem missing.
- Unresolved issue exists.
- Notional `> 100 USD`.
- Market order.
- Non-day time-in-force.
- Short selling.
- Crypto.
- Options.
- Margin/leverage.
- Extended hours.
- Batch behavior.
- Cancel/replace behavior.
- Live endpoint.
- Live trading assumption.
- Missing paper account confirmation.
- Secret exposure risk.

## 17. Success Criteria

Phase 44 design is successful only if:

- Automated paper send remains disabled by default.
- Automated paper send requires explicit flags.
- Automated paper send can submit at most one paper limit/day order.
- Automated paper send cannot run if previous reconciliation or post-mortem is missing.
- Automated paper send cannot run if kill switch is active.
- Automated paper send cannot run if daily limits are exceeded.
- Automated paper send writes report, reconciliation, post-send safety, post-mortem, and audit log.
- System returns to `DRY_RUN_ONLY` after send.
- `PAPER_ORDER_EXECUTION_ENABLED` and `PAPER_AUTOMATED_SEND_ENABLED` must be unset or disabled after run.
- Live trading remains unsupported.

## 18. Failure Conditions

Automated paper send design or implementation fails if:

- Automated paper send can run by default.
- Automated paper send can run with any required flag missing.
- Automated paper send can run with any V12 gate missing or failed.
- Automated paper send can run without Human Review.
- Automated paper send can run without Manual Execution Confirmation.
- Automated paper send can run without Paper Send Preflight.
- Automated paper send can run without prior reconciliation and post-mortem readiness.
- More than one automated paper order can be submitted per run.
- More than one automated paper order can be submitted per day.
- Notional can exceed `100 USD`.
- Market order, non-day time-in-force, short selling, crypto, options, margin/leverage, extended hours, batch, or cancel/replace can pass.
- Live endpoint or live trading assumption can pass.
- Secrets are printed, logged, committed, or written to reports.

## 19. What Remains Prohibited

The following remain prohibited:

- Live trading.
- Live endpoints.
- Increasing notional.
- Batch orders.
- Cancel/replace.
- Multi-symbol automation.
- Higher frequency.
- Multiple automated sends per day.
- Removing human review.
- Removing manual execution confirmation.
- Bypassing V12 gates.

## 20. Conditions Before Implementation

Before implementing automated paper send:

- Baseline V12 must remain `PASS`.
- Operating Policy After V12 must remain `PASS`.
- The design in this file must pass audit.
- A runner must be blocked by default.
- Tests must use mocked Alpaca clients.
- Real Alpaca paper sends must require explicit flags.
- No live endpoint may be supported.
- No `.env` file may be created.
- Secrets must never be printed.

## 21. Conditions Before Live Trading

Automated paper send does not authorize live trading.

Live trading would require a separate live-readiness program including:

- Long paper automation soak period.
- Clean reconciliation history.
- Clean post-mortem history.
- Drawdown limits.
- Portfolio exposure limits.
- Live broker boundary design.
- Live credentials isolation.
- Legal/tax/account review.
- Separate human approval.
- Separate implementation.
- Separate audit.

## 22. Live Trading Statement

Live trading remains unsupported.

Automated paper send is paper-only. It does not authorize live trading, live endpoints, increasing notional, batch orders, cancel/replace, multi-symbol automation, higher frequency, removing human review, removing Manual Execution Confirmation, or bypassing V12 gates.
