# Baseline V15 Operator Runbook

## Scope

This runbook covers:

- One-symbol real market data read-only validation.
- Real-market proposal dry run.
- Gated paper-only send.
- Reconciliation/post-mortem/evidence.
- Bounded paper-only soak supervisor.
- Emergency stop / kill switch.

## Non-Goals

This runbook does not authorize:

- Live trading.
- Real-money orders.
- Autonomous trading.
- Multi-symbol automation.
- Market scanning.
- Symbol auto-selection.
- Bypassing human review.
- Bypassing manual confirmation.
- Bypassing preflight.
- Notional above 100 USD.
- `.env` mutation.
- Secret printing.

## Pre-Operation Checklist

- [ ] Baseline V15 PASS confirmed.
- [ ] Phase 63 Full Regression PASS confirmed.
- [ ] Exactly one symbol selected.
- [ ] Symbol is watchlist-approved.
- [ ] paper_only=true.
- [ ] max_notional_usd <= 100.
- [ ] Human review is available.
- [ ] Manual execution confirmation is available.
- [ ] Preflight is available.
- [ ] Kill switch is available.
- [ ] No live endpoint configured.
- [ ] No secrets will be printed.
- [ ] Reports directory is writable.

## Mode A — Read-Only Market Data Validation

Purpose: validate real market data availability, freshness, completeness, and compatibility for exactly one approved symbol without creating any trade request.

Allowed actions:

- Load real market data from the approved market data endpoint.
- Validate the data as MarketDataSnapshot-compatible.
- Check data integrity, freshness, completeness, and watchlist approval.
- Persist a redacted validation report.

Required inputs:

- Exactly one selected symbol.
- Watchlist approval for the selected symbol.
- Market data provider configuration.
- Report output path.

Expected report path:

- `reports/real_market_data_adapter/<timestamp>/REAL_MARKET_DATA_ADAPTER_REPORT.md`

PASS criteria:

- Exactly one symbol is configured.
- The symbol is watchlist-approved.
- The market data endpoint is read-only and not an order endpoint.
- Data integrity, freshness, and completeness checks pass.
- The report is persisted with secrets redacted.

WARNING/FAIL handling:

- Stop the current run.
- Preserve the report artifact.
- Identify the exact failing validation gate.
- Do not proceed to proposal dry run until PASS.

No order is sent in this mode.

## Mode B — Real-Market Proposal Dry Run

Purpose: evaluate read-only real market data and produce a non-executing strategy decision.

Allowed decisions:

- `NO_TRADE`
- `REJECT`
- `TRADE_PROPOSAL`

Required inputs:

- A valid read-only market data snapshot.
- Exactly one watchlist-approved symbol.
- Dry-run strategy evaluation inputs.
- Report output path.

Expected report path:

- `reports/real_market_proposal_dry_run/<timestamp>/REAL_MARKET_PROPOSAL_DRY_RUN_REPORT.md`

PASS criteria:

- Read-only data validation passed.
- Exactly one watchlist-approved symbol is used.
- Execution flags are not enabled.
- The decision is one of `NO_TRADE`, `REJECT`, or `TRADE_PROPOSAL`.
- No human review queue, manual confirmation, preflight, or order send is triggered by dry-run mode.
- The report is persisted with secrets redacted.

WARNING/FAIL handling:

- Stop the current run.
- Preserve the dry-run report.
- Treat `NO_TRADE` as a normal safe outcome.
- Treat validation errors, safety violations, or unsupported decisions as blockers.
- Do not proceed to a paper send unless the decision is `TRADE_PROPOSAL` and all later gates pass.

A TRADE_PROPOSAL is not an order.

## Mode C — Gated Paper-Only Send

Purpose: send a paper-only order only after the Phase 58 gate chain passes.

Required gates:

- Data integrity PASS.
- Freshness PASS.
- Completeness PASS.
- Strategy decision TRADE_PROPOSAL.
- Evaluation gate PASS.
- Negative regression gate PASS.
- Human review approved.
- Finalized request created.
- Manual execution confirmed.
- Preflight PASS.
- paper_only=true.
- max_notional_usd <= 100.

Expected report path:

- `reports/real_market_paper_order_run/<timestamp>/REAL_MARKET_PAPER_ORDER_RUN_REPORT.md`

STOP conditions:

- Missing or unapproved symbol.
- More than one symbol.
- `max_notional_usd > 100`.
- `paper_only` is not true.
- Strategy decision is not `TRADE_PROPOSAL`.
- Data integrity, freshness, or completeness fails.
- Evaluation gate fails.
- Negative regression gate fails.
- Human review is missing.
- Manual execution confirmation is missing.
- Preflight does not pass.
- A live endpoint, live trading assumption, non-paper account assumption, or live order signal appears.
- Secret output is detected.

Live trading remains unsupported.

## Mode D — Reconciliation/Post-Mortem/Evidence

Purpose: reconcile Phase 58 paper-only order artifacts, generate post-mortem notes, and preserve evidence without sending a new order.

Required inputs from Phase 58:

- Phase 58 source phase.
- Symbol.
- Strategy decision and reason.
- Human review status.
- Manual execution confirmation status.
- Preflight status.
- Paper-only order result.
- Paper-only and live-order safety fields.
- Report output path.

Expected report paths:

- `reports/real_market_paper_reconciliation/<timestamp>/REAL_MARKET_PAPER_RECONCILIATION_REPORT.md`
- `reports/real_market_paper_reconciliation/<timestamp>/POST_MORTEM.md`
- `reports/real_market_paper_reconciliation/<timestamp>/EVIDENCE_MANIFEST.md`

Reconciliation statuses:

- `RECONCILED`
- `RECONCILED_WITH_WARNINGS`
- `BLOCKED`
- `FAILED`

WARNING/FAIL handling:

- Stop the current run.
- Preserve reconciliation, post-mortem, and evidence artifacts.
- Identify whether the issue is an input mismatch, safety gate failure, missing artifact, or broker/result discrepancy.
- Do not continue to soak while reconciliation is `BLOCKED` or `FAILED`.

No new order is sent during reconciliation.

## Mode E — Bounded Paper-Only Soak Supervisor

Purpose: supervise bounded real-market paper-only cycles while preserving Baseline V15 gates and evidence.

Default `allow_paper_send=false` behavior:

- Run proposal cycles without sending paper orders.
- Record `NO_TRADE`, `REJECT`, and `TRADE_PROPOSAL` outcomes.
- Preserve reports and evidence.

`allow_paper_send=true` behavior:

- Permit paper-only send attempts only when every Phase 58 gate passes.
- Require reconciliation after any paper send.
- Stop on failed reconciliation when configured to stop on first reconciliation failure.

Order limits:

- `max_paper_orders_total` must limit total paper sends.
- `max_paper_orders_per_symbol` must limit paper sends for the single approved symbol.
- Unlimited order loops are prohibited.

Kill-switch behavior:

- `kill_switch_enabled=true` must block before any cycle.
- The kill switch is a hard stop when safety status is uncertain.

Stop conditions:

- Missing symbol.
- More than one symbol.
- Missing watchlist approval.
- `paper_only` is not true.
- `max_notional_usd > 100`.
- Required human review, manual confirmation, or preflight is unavailable.
- Kill switch is enabled.
- Live endpoint or live trading assumption appears.
- Secret output is detected.
- Order limit would be exceeded.
- Reconciliation fails.

Expected report paths:

- `reports/real_market_paper_soak/<timestamp>/REAL_MARKET_PAPER_SOAK_REPORT.md`
- `reports/real_market_paper_soak/<timestamp>/SOAK_EVIDENCE_MANIFEST.md`

Soak does not authorize live trading.

## Emergency Stop / Kill Switch

When to activate:

- Any live endpoint is suspected.
- Any secret exposure is suspected.
- Any gate status is unknown.
- Reconciliation is `BLOCKED` or `FAILED`.
- Report artifacts are missing or incomplete.
- Operator confidence is reduced.

Expected behavior:

- The current run stops.
- No new cycle starts.
- No paper send proceeds.
- Evidence and reports are preserved for review.

Required follow-up:

- Preserve all artifacts.
- Run reconciliation/post-mortem if applicable.
- Identify the exact failing gate or unsafe signal.
- Confirm no live order was sent.
- Confirm live trading remains unsupported.
- Do not resume until Baseline V15 gates are verified.

kill_switch_enabled=true must block before any cycle.

## WARNING/FAIL Protocol

- Stop the current run.
- Do not retry automatically.
- Preserve artifacts.
- Run reconciliation/post-mortem if applicable.
- Identify exact failing gate.
- Do not proceed to the next phase until PASS.
- Do not send orders after FAIL.

## Secret Handling

- Never print secrets.
- Never persist unredacted secrets.
- Redact provider messages.
- Redact strategy reasons.
- Redact order messages.
- Redact raw adapter messages.
- Verify reports contain no exact injected secrets.

## Artifact Index

- `docs/BASELINE_V15_REAL_MARKET_PAPER_ONLY_SYSTEM_FREEZE.md`
- `docs/OPERATING_POLICY_AFTER_PHASE_60_REAL_MARKET_PAPER_SOAK.md`
- `reports/baseline_v15_full_regression/<timestamp>/BASELINE_V15_FULL_REGRESSION_AUDIT.md`
- `reports/real_market_data_adapter/<timestamp>/REAL_MARKET_DATA_ADAPTER_REPORT.md`
- `reports/real_market_proposal_dry_run/<timestamp>/REAL_MARKET_PROPOSAL_DRY_RUN_REPORT.md`
- `reports/real_market_paper_order_run/<timestamp>/REAL_MARKET_PAPER_ORDER_RUN_REPORT.md`
- `reports/real_market_paper_reconciliation/<timestamp>/REAL_MARKET_PAPER_RECONCILIATION_REPORT.md`
- `reports/real_market_paper_reconciliation/<timestamp>/POST_MORTEM.md`
- `reports/real_market_paper_reconciliation/<timestamp>/EVIDENCE_MANIFEST.md`
- `reports/real_market_paper_soak/<timestamp>/REAL_MARKET_PAPER_SOAK_REPORT.md`
- `reports/real_market_paper_soak/<timestamp>/SOAK_EVIDENCE_MANIFEST.md`

## Final Exact Statements

Baseline V15 remains paper-only.

Live trading remains unsupported.

Human review remains required.

Manual execution confirmation remains required.

Preflight remains required.

Multi-symbol automation remains unsupported.

Market scanning remains unsupported.

The system must not mutate `.env`.

Secrets must be redacted before persistence.

## Final Status

Phase 64 Baseline V15 Operator Runbook Status: RUNBOOK_DEFINED
