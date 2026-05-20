# Phase 55: Real Market Data Adapter Design

## Current Baseline

Baseline V14 is PASS.

Operating Policy After V14 is PASS.

This design is architecture-only.

This design does not authorize order sending.

This design does not authorize live trading.

This design does not bypass V14 gates.

This design does not increase notional.

This design does not allow multi-symbol automation.

## Current Limitation

`runtime/market_data.py` uses deterministic mock fixtures for Data Integrity validation.

The system can execute controlled automated paper sends under V14 controls, but market input is not yet real market data.

The next architecture step is to define a read-only real market data adapter for paper-only strategy evaluation and proposal generation.

## Purpose

The Real Market Data Adapter loads market data for one configured symbol only and returns a `MarketDataSnapshot` compatible with existing Data Integrity validation.

The adapter exists only to improve paper-only strategy evaluation and proposal generation.

The adapter must not create broker execution readiness.

The adapter must not submit orders.

The adapter must not call the Alpaca order API.

## Scope

In scope:

- Read-only market data loading for one configured symbol.
- Paper-safe market data configuration.
- Data freshness validation.
- Data completeness validation.
- Data Integrity compatibility.
- Report generation for each adapter run.
- Deterministic mock fallback for tests.

Out of scope:

- Order sending.
- Live trading.
- Live endpoints.
- Broker execution readiness.
- Multi-symbol automation.
- Notional increase.
- Runtime order-path changes.
- Credential creation.
- `.env` file creation.

## Adapter Inputs

Required inputs:

- Approved configured symbol.
- Approved timeframe.
- Session context.
- Market data source selection.
- Freshness threshold.
- Completeness threshold.
- Required spread setting.
- Required volume setting.
- Paper-safe/read-only provider configuration.

Optional inputs:

- Deterministic mock fixture selection for tests.
- Last known reconciliation reference for reporting context only.

## Adapter Output

The adapter returns a `MarketDataSnapshot` compatible with existing Data Integrity validation.

The snapshot must include:

- `source`
- `timestamp`
- `symbol`
- `timeframe`
- `session`
- Bid/ask or spread availability
- Volume availability
- Last price if available
- Bar/candle data if available

The snapshot must exclude:

- Secrets.
- API keys.
- Account credentials.
- Order endpoint URLs.
- Broker execution readiness.
- Any order intent.

## Allowed Sources

Allowed sources:

- Alpaca market data read-only endpoint, paper-safe configuration only.
- Existing configured provider if read-only.
- Deterministic mock fallback only for tests.

Disallowed sources:

- Live trading endpoint.
- Alpaca order endpoint.
- Any provider mode that implies broker execution readiness.
- Any provider mode that requires live trading assumptions.

## Required Adapter Behavior

1. Load market data for one configured symbol only.
2. Use paper-safe/read-only market data access.
3. Never call Alpaca order API.
4. Never submit orders.
5. Never create broker execution readiness.
6. Return a `MarketDataSnapshot` compatible with existing Data Integrity validation.
7. Include source, timestamp, symbol, timeframe, session, spread availability, volume availability, last price if available, and bar/candle data if available.
8. Enforce freshness threshold.
9. Enforce completeness threshold.
10. Reject stale data.
11. Reject missing symbol.
12. Reject missing timestamp.
13. Reject missing timeframe.
14. Reject missing spread/volume when required.
15. Reject live endpoint if detected.
16. Reject non-paper account assumptions.
17. Redact secrets from all outputs.

## Freshness Rules

The adapter must compare the snapshot timestamp against the configured freshness threshold.

If the snapshot timestamp is missing, the adapter must reject the data.

If the snapshot timestamp is older than the configured freshness threshold, the adapter must reject the data.

If freshness cannot be evaluated, the adapter must reject the data.

Stale data must not produce a valid strategy evaluation input.

## Completeness Rules

The adapter must evaluate whether required fields are present before Data Integrity validation proceeds.

Required fields:

- Source.
- Timestamp.
- Symbol.
- Timeframe.
- Session.

Conditionally required fields:

- Bid/ask or spread when spread is required.
- Volume when volume is required.
- Bar/candle data when the selected strategy evaluation requires bars.
- Last price when the selected strategy evaluation requires a last price.

Incomplete data must not produce a valid strategy evaluation input.

## Single-Symbol Constraint

The adapter may load data for one configured symbol only.

The configured symbol must have watchlist approval.

More than one symbol is a hard block.

Missing watchlist approval is a hard block.

Multi-symbol automation remains prohibited.

## Paper-Safe Read-Only Constraint

The adapter must operate as a read-only data adapter.

The adapter must not submit orders.

The adapter must not call the Alpaca order API.

The adapter must not create broker execution readiness.

The adapter must reject live endpoint configuration if detected.

The adapter must reject non-paper account assumptions.

Live trading remains unsupported.

## Environment Rules

During data-only adapter runs:

- `PAPER_ORDER_EXECUTION_ENABLED=true` is a hard block.
- `PAPER_AUTOMATED_SEND_ENABLED=true` is a hard block.
- `PAPER_SOAK_TEST_ACCELERATED=true` must not be required.
- No `.env` files may be created.
- Secrets must not be printed.
- Secrets must not be written to reports.
- Secrets must not be logged.

Missing API keys are a hard block when a real provider is selected.

Missing API keys may not be solved by printing, committing, or generating credentials.

## Hard Blocks

The adapter must block on:

- More than one symbol.
- Missing watchlist approval.
- Live trading endpoint.
- Alpaca order endpoint.
- Missing API keys when real provider is selected.
- Secret printing.
- Stale data.
- Missing timestamp.
- Missing symbol.
- Missing timeframe.
- Missing required spread/volume.
- Any attempt to send order.
- Any broker execution readiness.
- Any `PAPER_ORDER_EXECUTION_ENABLED=true` during data-only run.
- Any `PAPER_AUTOMATED_SEND_ENABLED=true` during data-only run.

## Data Integrity Handoff

The adapter may hand off only a validated `MarketDataSnapshot` shape to Data Integrity validation.

The handoff must not include execution state.

The handoff must not include order readiness.

The handoff must not imply trade approval.

Data Integrity remains responsible for validating quality, freshness, completeness, and compatibility.

Any Data Integrity rejection blocks downstream strategy evaluation.

## Strategy Evaluation Handoff

The adapter may support paper-only strategy evaluation and proposal generation only after Data Integrity accepts the snapshot.

A valid market data snapshot does not authorize a trade.

A valid market data snapshot does not bypass Human Review.

A valid market data snapshot does not bypass Manual Execution Confirmation.

A valid market data snapshot does not bypass Paper Send Preflight.

A valid market data snapshot does not bypass V14 gates.

Default decision remains NO_TRADE.

## Deterministic Mock Fallback

Deterministic mock fixtures remain available for tests.

Mock fixtures must be clearly marked as mock source data.

Mock fixtures must not be treated as real market evidence.

Mock fallback must not mask real provider failures outside tests.

## Required Report

Each adapter run must produce:

`reports/real_market_data_adapter/<timestamp>/REAL_MARKET_DATA_ADAPTER_REPORT.md`

The report must include:

- Symbol.
- Source.
- Timestamp.
- Timeframe.
- Session.
- Freshness status.
- Completeness status.
- Data integrity status.
- Live endpoint rejected.
- Order API not used.
- Secrets not printed.
- Final status.
- Statement: No order was sent.
- Statement: Live trading remains unsupported.
- Statement: This adapter is read-only.

The report must not include:

- Secrets.
- API keys.
- Account credentials.
- Order endpoint credentials.
- Raw authentication headers.

## Success Criteria

- Real market data can be loaded for one symbol.
- Data Integrity can validate real data.
- Stale data blocks.
- Incomplete data blocks.
- Mock fixtures remain available for tests.
- No order API is called.
- No live trading is introduced.
- No secrets are printed.

## Failure Modes

Expected failure modes:

- Missing symbol.
- Missing watchlist approval.
- More than one symbol requested.
- Missing timestamp.
- Missing timeframe.
- Missing required spread.
- Missing required volume.
- Stale data.
- Real provider selected without API keys.
- Live endpoint detected.
- Alpaca order endpoint detected.
- Non-paper account assumption detected.
- Execution enablement flag detected during data-only run.
- Automated send enablement flag detected during data-only run.
- Secret redaction failure.

Any failure mode must produce a blocked final status and must not produce broker execution readiness.

## Monitoring And Review

Adapter reports must be reviewed before real market data is used as paper-only strategy evaluation input.

Review must confirm:

- One symbol only.
- Watchlist approval exists.
- Source is read-only.
- Live endpoint was rejected.
- Alpaca order API was not used.
- Freshness passed.
- Completeness passed.
- Data Integrity passed.
- Secrets were not printed.
- No order was sent.
- Live trading remains unsupported.

## Explicit Non-Authorization

This design does not authorize order sending.

This design does not authorize live trading.

This design does not authorize live endpoints.

This design does not authorize increasing notional.

This design does not authorize multi-symbol automation.

This design does not authorize batch orders.

This design does not authorize cancel/replace.

This design does not authorize bypassing V14 gates.

This design does not authorize broker execution readiness.
