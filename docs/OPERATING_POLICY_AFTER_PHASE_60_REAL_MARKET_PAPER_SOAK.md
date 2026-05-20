# Operating Policy After Phase 60 Real Market Paper Soak

## Baseline and Phase Status Context

- Baseline V14 PASS.
- Operating Policy After V14 PASS.
- Phase 55 PASS.
- Phase 56 PASS.
- Phase 57 PASS.
- Phase 58 PASS.
- Phase 59 PASS.
- Phase 60 PASS.

Phase 61 is a policy-only documentation update. Runtime and test files produced by Phases 56-60 are pre-existing phase outputs and are outside the Phase 61 change scope.

## Current system capability

The current system can load real market data read-only for one approved symbol.

The current system can run real-market proposal dry runs.

The current system can produce `NO_TRADE`, `REJECT`, or `TRADE_PROPOSAL`.

The current system can execute gated paper-only sends only through the Phase 58 path.

The current system can reconcile Phase 58 artifacts through Phase 59.

The current system can supervise bounded paper-only soak through Phase 60.

No live trading is supported.

Paper-only execution remains gated.

## What remains unsupported

The following remain unsupported:

- Live trading.
- Autonomous live trading.
- Multi-symbol automation.
- Market scanning.
- Symbol auto-selection.
- Unlimited order loops.
- Bypassing human review.
- Bypassing manual execution confirmation.
- Bypassing preflight.
- Notional above 100 USD.
- Any live endpoint.
- Any `.env` mutation by the agent.
- Secret printing.

Live trading remains unsupported.

Multi-symbol automation remains unsupported.

Market scanning remains unsupported.

The system must not mutate `.env`.

## Required invariants

These invariants are mandatory for every real-market paper-only path:

- `paper_only=true`.
- `max_notional_usd <= 100`.
- Exactly one symbol.
- Symbol must be watchlist-approved.
- Human review required before send.
- Manual execution confirmation required before send.
- Preflight required before send.
- Reconciliation required after send.
- Post-mortem/evidence required after send.
- Kill switch must block soak.
- Order limits must block soak.
- Secrets must be redacted from all reports.

Human review remains required.

Manual execution confirmation remains required.

Preflight remains required.

Secrets must be redacted before persistence.

## Allowed modes

The following modes are allowed under the required invariants:

- Read-only market data validation.
- Real-market proposal dry run.
- Paper-only gated send with all gates.
- Paper-only reconciliation/post-mortem.
- Bounded paper-only soak supervisor.

## Disallowed modes

The following modes are disallowed:

- Live trading.
- Real-money trading.
- Automated live order execution.
- Multi-symbol execution.
- Watchlist bypass.
- Direct order endpoint use outside approved paper-only adapter path.
- Any order send without human review.
- Any order send without manual confirmation.
- Any order send without preflight.
- Any repeated order loop without max limits.
- Any provider output written unredacted.

## Required report paths

The following report paths are required for the corresponding phases:

- `reports/real_market_data_adapter/<timestamp>/REAL_MARKET_DATA_ADAPTER_REPORT.md`
- `reports/real_market_proposal_dry_run/<timestamp>/REAL_MARKET_PROPOSAL_DRY_RUN_REPORT.md`
- `reports/real_market_paper_order_run/<timestamp>/REAL_MARKET_PAPER_ORDER_RUN_REPORT.md`
- `reports/real_market_paper_reconciliation/<timestamp>/REAL_MARKET_PAPER_RECONCILIATION_REPORT.md`
- `reports/real_market_paper_reconciliation/<timestamp>/POST_MORTEM.md`
- `reports/real_market_paper_reconciliation/<timestamp>/EVIDENCE_MANIFEST.md`
- `reports/real_market_paper_soak/<timestamp>/REAL_MARKET_PAPER_SOAK_REPORT.md`
- `reports/real_market_paper_soak/<timestamp>/SOAK_EVIDENCE_MANIFEST.md`

## Required audit language

Phase 61 audits must state whether the Baseline V14, Operating Policy After V14, and Phase 55 through Phase 60 PASS references are present.

Phase 61 audits must state that runtime and test files produced by Phases 56-60 are pre-existing phase outputs and are outside the Phase 61 policy-only change scope.

Phase 61 audits must state whether the policy preserves paper-only execution gates, human review, manual execution confirmation, preflight, notional limits, single-symbol limits, no market scanning, no symbol auto-selection, secret redaction, and no `.env` mutation.

## Operator checklist

### Before Read-Only Run

- Confirm the run is read-only.
- Confirm exactly one symbol is configured.
- Confirm the symbol is watchlist-approved.
- Confirm no order execution flag is required.
- Confirm no live endpoint is configured.
- Confirm secrets will not be printed.

### Before Proposal Dry Run

- Confirm real market data will be consumed read-only.
- Confirm no candidate will be created unless the phase explicitly allows a dry-run proposal object.
- Confirm no human review item will be created by read-only mode.
- Confirm no preflight will be run by read-only mode.
- Confirm no paper order will be sent by read-only mode.

### Before Paper-Only Send

- Confirm `paper_only=true`.
- Confirm `max_notional_usd <= 100`.
- Confirm exactly one watchlist-approved symbol.
- Confirm the source decision is `TRADE_PROPOSAL`.
- Confirm human review approval exists.
- Confirm manual execution confirmation exists.
- Confirm preflight status allows paper send.
- Confirm the approved Phase 58 paper-only path is used.
- Confirm live trading remains unsupported.

### Before Reconciliation

- Confirm the input artifacts come from Phase 58.
- Confirm no new order will be sent by reconciliation.
- Confirm paper-only status is present.
- Confirm live order status is false.
- Confirm provider messages and raw adapter messages will be redacted.
- Confirm post-mortem and evidence artifacts will be produced.

### Before Soak Supervisor Run

- Confirm Phase 60 is bounded by `max_cycles`.
- Confirm `allow_paper_send=false` unless a gated paper-only send is explicitly intended.
- Confirm `max_paper_orders_total` is configured.
- Confirm `max_paper_orders_per_symbol` is configured.
- Confirm the kill switch is checked before cycles start.
- Confirm order limits block before sending if they would be exceeded.
- Confirm no automatic retry after failed sends.
- Confirm exactly one symbol.
- Confirm no market scan or symbol auto-selection is configured.

### After Any Paper Send

- Confirm Phase 59 reconciliation ran.
- Confirm reconciliation status is reviewed.
- Confirm post-mortem exists.
- Confirm evidence manifest exists.
- Confirm no secret appears in reports.
- Confirm no live order was sent.
- Confirm no further send proceeds while reconciliation, post-mortem, or unresolved issue status is incomplete.

### Emergency Stop / Kill Switch

- Activate or keep the kill switch active when safety status is uncertain.
- Treat kill switch activation as a hard block before any soak cycle.
- Do not send any paper order while the kill switch is active.
- Do not resume until human review, manual execution confirmation, preflight, reconciliation, and evidence status are verified.

## Regression checklist

Future phases must verify:

- No live endpoint use.
- No `/v2/orders` direct use outside approved paper adapter.
- No secret leakage.
- No `.env` mutation.
- No multi-symbol automation.
- No watchlist bypass.
- No notional > 100.
- No bypass of human review.
- No bypass of manual confirmation.
- No bypass of preflight.
- No missing reconciliation.
- No missing post-mortem/evidence.

## Final status

Phase 61 Operating Policy Update After Real Market Paper Soak Status: POLICY_DEFINED
