# Phase 42 Controlled V10 Paper Send Design

## 1. Purpose

Design one controlled real Alpaca paper send from the V10 pipeline.

This phase is design only.

This is not general automation.
This is not auto-send.
This is not live trading.
This is one controlled manual paper send using the V10 pipeline.

This phase must not send orders.
This phase must not enable `PAPER_ORDER_EXECUTION_ENABLED`.
This phase must not use Alpaca API.
This phase must not modify runtime code.
This phase must not add live trading.
This phase must not create `.env` files.
This phase must not print secrets.

## 2. Context

Baseline V11 is `PASS`.

V11 proves the full V10 pipeline can reach `PAPER_ORDER_SEND_ALLOWED` in dry-run regression without sending orders.

V11 allows:

- Automated dry-run analysis.
- Automated Paper Order Request Candidate creation.
- Human Review Queue.
- Finalized Paper Order Request creation from human-approved candidates.
- Manual Execution Confirmation.
- Paper Send Preflight.
- Full pipeline dry-run regression.
- Manual limited paper sends under V4-V11 gates.
- Design one controlled V10 paper send.

V11 does not allow:

- Automated Paper Send.
- Broker execution readiness outside a controlled send phase.
- Increasing notional.
- Live trading.
- Batch orders.
- Cancel/replace.
- Multi-symbol automation.
- Higher frequency.
- Bypassing V4-V11 gates.

## 3. Scope

Controlled V10 Paper Send is a single manually initiated Alpaca paper order send after the full V10 pipeline passes and `PAPER_ORDER_SEND_ALLOWED` exists.

The design allows exactly one paper limit/day order attempt in a controlled phase.

The design does not allow:

- General automation.
- Recurring sends.
- Multi-symbol sends.
- Batch sends.
- Cancel/replace.
- Live trading.
- Live endpoints.
- Higher notional.
- Runtime behavior in this design phase.

## 4. Required Pipeline Before Send

The required pipeline before send is:

1. Automated dry-run.
2. Strategy Evaluation Harness.
3. Evaluation-First Gate.
4. Negative Case Regression.
5. Paper Order Request Candidate.
6. Human Review Queue.
7. Finalized Paper Order Request.
8. Manual Execution Confirmation.
9. Paper Send Preflight.
10. Controlled Alpaca Paper Send.
11. Reconciliation.
12. Post-mortem.

No stage may be skipped.
If any stage blocks, the controlled send must not occur.

## 5. Required Pre-Send Checks

Before Controlled Alpaca Paper Send, all checks must pass:

- Full tests `PASS`.
- Architecture validation `PASS`.
- V10 full pipeline dry-run regression `PASS`.
- Strategy Evaluation `PASS`.
- Evaluation-First Gate `PASS`.
- Negative Case Regression `PASS`.
- Candidate created from valid `TRADE_PROPOSAL`.
- Human Review status `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
- Finalized Paper Order Request status `PAPER_ORDER_REQUEST_FINALIZED`.
- Manual Execution Confirmation status `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
- Paper Send Preflight status `PAPER_ORDER_SEND_ALLOWED`.
- Alpaca paper account confirmed.
- Live endpoint rejected.
- `PAPER_ORDER_EXECUTION_ENABLED=true` only for this manual send.

`PAPER_ORDER_EXECUTION_ENABLED=true` is not a general operating mode. It is a temporary condition for the one controlled manual send attempt only, and must be unset after the run.

## 6. Required Paper Send Constraints

Controlled V10 Paper Send must enforce:

- One order only.
- Paper trading only.
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
- No automation beyond approved pipeline stages.

## 7. Controlled Send Behavior

The adapter may send exactly one Alpaca paper limit/day order only after all gates pass.

The adapter must:

- Reject live endpoint or live configuration.
- Reject non-paper account.
- Reject if `PAPER_ORDER_EXECUTION_ENABLED` is not true for the manual run.
- Reject if preflight status is not `PAPER_ORDER_SEND_ALLOWED`.
- Reject if any required reference is missing.
- Reject if any V4-V11 gate is missing or failed.
- Reject if notional is `> 100 USD`.
- Reject market orders.
- Reject non-day time-in-force.
- Reject short selling, crypto, options, margin/leverage, and extended hours.
- Reject batch orders.
- Reject cancel/replace behavior.
- Write send result artifact.
- Write journal entry.
- Run reconciliation after send attempt.
- Write post-send safety artifact.
- Create post-mortem.
- Return the system to `DRY_RUN_ONLY`.
- Unset `PAPER_ORDER_EXECUTION_ENABLED` after run.

The adapter must not print secrets.

## 8. Required Artifacts

Controlled V10 Paper Send must create these artifacts:

```text
reports/v10_controlled_paper_send/<timestamp>/V10_CONTROLLED_PAPER_SEND_REPORT.md
reports/v10_controlled_paper_send/<timestamp>/POST_MORTEM.md
reports/v10_controlled_paper_send/<timestamp>/RECONCILIATION.md
reports/v10_controlled_paper_send/<timestamp>/POST_SEND_SAFETY.md
```

The artifacts must not contain secrets.

## 9. Controlled Send Report Requirements

`V10_CONTROLLED_PAPER_SEND_REPORT.md` must include:

- Timestamp.
- Baseline reference.
- Pipeline stage references.
- Full tests status.
- Architecture validation status.
- V10 full pipeline dry-run regression status.
- Strategy Evaluation status.
- Evaluation-First Gate status.
- Negative Case Regression status.
- Candidate id and status.
- Human Review id and status.
- Finalized Paper Order Request id and status.
- Manual Execution Confirmation id and status.
- Paper Send Preflight id and status.
- Alpaca paper account confirmation.
- Live endpoint rejection proof.
- Execution flag handling proof.
- Order request summary with no secrets.
- Send status.
- Block reason if blocked.
- Reconciliation status.
- Post-send safety status.
- Post-mortem status.
- Statement: Live trading remains unsupported.

## 10. Reconciliation Requirements

Reconciliation must run after the send attempt.

If an order is submitted, reconciliation must verify:

- Broker-side paper order id exists.
- Submitted symbol matches finalized request.
- Side matches finalized request.
- Order type is limit.
- Time in force is day.
- Notional is `<= 100 USD`.
- Quantity or notional matches the controlled request.
- No extra orders were created.
- No batch orders were created.
- No cancel/replace occurred.
- No live endpoint was used.

If the send is blocked before submission, reconciliation must record:

- No order was sent.
- No broker-side paper order id exists.
- Block reason is explicit.
- No Alpaca order API call occurred unless the controlled adapter reached the approved send step.

Allowed reconciliation statuses:

- `RECONCILIATION_MATCHED`
- `RECONCILIATION_BLOCKED_NO_ORDER`
- `RECONCILIATION_MISMATCH`
- `RECONCILIATION_FAILED`

## 11. Post-Send Safety Requirements

Post-send safety must confirm:

- System returned to `DRY_RUN_ONLY`.
- `PAPER_ORDER_EXECUTION_ENABLED` is unset after run.
- No live trading flag remains enabled.
- No live endpoint is configured.
- No broker execution readiness remains active outside the controlled send phase.
- No batch behavior was created.
- No cancel/replace behavior was created.
- Secrets were not printed.

## 12. Post-Mortem Requirements

The post-mortem must include:

- Whether the send was submitted or blocked.
- Exact gate statuses.
- Exact block reason if blocked.
- Reconciliation result.
- Post-send safety result.
- Any unexpected behavior.
- Any missing artifact.
- Any human review concerns.
- Whether future sends should remain blocked, remain manual, or require redesign.
- Statement: Live trading remains unsupported.

## 13. Success Criteria

Phase 42 design is successful only if the design defines:

- Full V10 pipeline prerequisites.
- Required pre-send checks.
- Required paper send constraints.
- Controlled one-order send behavior.
- Required artifacts.
- Reconciliation.
- Post-send safety.
- Post-mortem.
- Failure conditions.
- Explicit continuing prohibitions.

Controlled V10 Paper Send implementation is successful later only if:

- If sent, paper send status is `PAPER_ORDER_SUBMITTED`.
- If sent, reconciliation is `RECONCILIATION_MATCHED`.
- If blocked, block reason is explicit and no order is sent.
- Secrets are not printed.
- System returns to `DRY_RUN_ONLY`.
- `PAPER_ORDER_EXECUTION_ENABLED` is unset after run.
- Live trading remains unsupported.

## 14. Failure Conditions

Controlled V10 Paper Send must fail or block on:

- Any missing gate.
- Any failed gate.
- Any live endpoint.
- Non-paper account.
- Notional `> 100 USD`.
- Market order.
- Non-day time-in-force.
- Short selling.
- Crypto.
- Options.
- Margin/leverage.
- Extended hours.
- Batch orders.
- Cancel/replace.
- Missing reconciliation.
- Missing post-mortem.
- Secret exposure.
- Missing send result artifact.
- Missing post-send safety artifact.
- Failure to return to `DRY_RUN_ONLY`.
- Failure to unset `PAPER_ORDER_EXECUTION_ENABLED` after run.

## 15. What Remains Prohibited

The following remain prohibited:

- Automated paper send.
- Live trading.
- Live endpoints.
- Increasing notional.
- Batch orders.
- Cancel/replace.
- Multi-symbol automation.
- Higher frequency.
- Bypassing V4-V11 gates.
- General broker execution readiness.
- Any uncontrolled order submission.

## 16. Autonomy Boundary

The system may prepare artifacts, validate gates, and perform deterministic checks.

The system may not independently decide to send.

The one controlled paper send requires explicit manual initiation after all V4-V11 gates pass.

No future run may inherit send permission from this design or from a prior controlled send.

## 17. Secret Handling

Secrets must not be committed, printed, logged, or written to artifacts.

No `.env` file may be created by this design.

Credentials, if required by a future controlled send implementation, must come from the operator environment and must be redacted from all outputs.

## 18. Live Trading Statement

Live trading remains unsupported.

Controlled V10 Paper Send is paper trading only and does not authorize live endpoints, live accounts, real-money execution, automated paper send, notional increase, batch orders, cancel/replace, multi-symbol automation, higher frequency, or bypassing V4-V11 gates.
