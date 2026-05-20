# Phase 55: Real Market Data Adapter Design

## Current Baseline

Baseline V14 is PASS.

Operating Policy After V14 is PASS.

This phase is design only.

This design does not authorize order sending.

This design does not authorize live trading.

This design does not bypass V14 gates.

This design does not increase notional.

This design does not allow multi-symbol automation.

This design does not remove Human Review.

This design does not remove Manual Execution Confirmation.

## Current Limitation

`runtime/market_data.py` currently uses deterministic mock fixtures through `MockMarketDataAdapter`.

Current fixtures use `source="deterministic_mock"` and `symbol="SIM"`.

The current `MarketDataSnapshot` fields are:

- `source`
- `timestamp`
- `symbol`
- `timeframe`
- `session`
- `spread_available`
- `volume_available`

The current `validate_market_data` function validates freshness, completeness, source, timestamp, symbol, timeframe, and session.

## Purpose

Design a real market data adapter for paper-only strategy evaluation and proposal generation.

The adapter must load real market data in a read-only manner and return a `MarketDataSnapshot` compatible with existing Data Integrity validation.

The adapter must not create execution authority, paper order readiness, broker execution readiness, candidates, Human Review items, finalized requests, manual confirmations, preflight approvals, or sends.

## Required Adapter Behavior

1. Load market data for one configured symbol only.
2. Use read-only market data access.
3. Never call Alpaca order API.
4. Never submit orders.
5. Never create broker execution readiness.
6. Return a `MarketDataSnapshot` compatible with existing Data Integrity validation.
7. Preserve `MockMarketDataAdapter` for tests.
8. Add real adapter separately, not by replacing deterministic fixtures.
9. Include the existing fields: `source`, `timestamp`, `symbol`, `timeframe`, `session`, `spread_available`, and `volume_available`.
10. If real provider supports additional fields, add them only if backward compatible: optional `last_price`, optional `bid`, optional `ask`, optional `volume`, and optional `bars`.
11. Enforce freshness threshold.
12. Enforce completeness threshold.
13. Reject stale data.
14. Reject missing symbol.
15. Reject missing timestamp.
16. Reject missing timeframe.
17. Reject missing session.
18. Reject missing source.
19. Reject missing spread/volume when required.
20. Reject live endpoint if detected.
21. Reject order endpoint if detected.
22. Redact secrets from all outputs.

## Allowed Sources

- Alpaca market data read-only endpoint only.
- Existing configured read-only provider if available.
- Deterministic mock fallback only for tests.

## Required Configuration

- `MARKET_DATA_PROVIDER`
- `MARKET_DATA_SYMBOL`
- `MARKET_DATA_TIMEFRAME`
- `MARKET_DATA_MAX_AGE_SECONDS`
- `MARKET_DATA_REQUIRE_SPREAD=true/false`
- `MARKET_DATA_REQUIRE_VOLUME=true/false`
- `ALPACA_PAPER=true` when Alpaca credentials are present
- No order flags enabled during data-only run

Configuration must not create `.env` files.

Configuration must not print or report secret values.

## Hard Blocks

The adapter must block on:

- More than one symbol.
- Missing configured symbol.
- Symbol not approved by watchlist if watchlist exists.
- Missing provider.
- Unsupported provider.
- Live trading endpoint.
- Alpaca order endpoint.
- Missing API keys when real provider requires credentials.
- Secret printing.
- Stale data.
- Missing timestamp.
- Missing symbol.
- Missing timeframe.
- Missing session.
- Missing source.
- Missing required spread.
- Missing required volume.
- Any attempt to send order.
- Any broker execution readiness.
- `PAPER_ORDER_EXECUTION_ENABLED=true` during data-only run.
- `PAPER_AUTOMATED_SEND_ENABLED=true` during data-only run.
- `PAPER_SOAK_TEST_ACCELERATED=true` during data-only run.

## MarketDataSnapshot Compatibility

The real adapter must preserve compatibility with the current `MarketDataSnapshot` shape:

- `source`
- `timestamp`
- `symbol`
- `timeframe`
- `session`
- `spread_available`
- `volume_available`

Any added fields must have safe defaults and must not break deterministic mock fixtures or existing tests.

`MockMarketDataAdapter` must remain available for tests.

Deterministic fixtures must remain available for tests.

The real adapter must be added separately and must not replace the deterministic mock path.

## Freshness And Completeness

The adapter must enforce the configured freshness threshold from `MARKET_DATA_MAX_AGE_SECONDS`.

The adapter must reject stale data.

The adapter must reject missing source.

The adapter must reject missing timestamp.

The adapter must reject missing symbol.

The adapter must reject missing timeframe.

The adapter must reject missing session.

The adapter must reject missing spread when `MARKET_DATA_REQUIRE_SPREAD=true`.

The adapter must reject missing volume when `MARKET_DATA_REQUIRE_VOLUME=true`.

Invalid or incomplete data must not become a strategy proposal.

## Read-Only Safety

The adapter must use read-only market data access only.

The adapter must never call the Alpaca order API.

The adapter must never call order endpoints.

The adapter must never submit orders.

The adapter must never create broker execution readiness.

The adapter must reject live endpoints.

The adapter must reject Alpaca order endpoints.

Live trading remains unsupported.

## Data Integrity Handoff

The adapter may hand off only `MarketDataSnapshot`-compatible data to existing Data Integrity validation.

The handoff must not imply trade approval.

The handoff must not bypass V14 gates.

The handoff must not remove Human Review.

The handoff must not remove Manual Execution Confirmation.

Default decision remains NO_TRADE.

## Required Report

Each adapter run must produce:

`reports/real_market_data_adapter/<timestamp>/REAL_MARKET_DATA_ADAPTER_REPORT.md`

The report must include:

- Provider.
- Symbol.
- Source.
- Timestamp.
- Timeframe.
- Session.
- Freshness status.
- Completeness status.
- Spread availability.
- Volume availability.
- Data integrity status.
- Live endpoint rejected.
- Order API not used.
- Broker execution readiness not created.
- Secrets not printed.
- Final status.
- Reason.
- Statement: No order was sent.
- Statement: Live trading remains unsupported.
- Statement: This adapter is read-only.
- Statement: Mock fixtures remain available for tests.

The report must not include:

- Secrets.
- API keys.
- Account credentials.
- Authentication headers.
- Order endpoint credentials.

## Allowed Final Statuses

- `REAL_MARKET_DATA_LOADED`
- `REAL_MARKET_DATA_BLOCKED`
- `REAL_MARKET_DATA_INVALID`
- `REAL_MARKET_DATA_STALE`
- `REAL_MARKET_DATA_ERROR`

## Success Criteria

- Real market data can be loaded for one symbol.
- Data Integrity can validate real data.
- Stale/incomplete data blocks.
- Mock fixtures remain available for tests.
- No order API is called.
- No broker execution readiness is created.
- No live trading is introduced.
- No secrets are printed.

## What Remains Prohibited

- Order sending.
- Broker execution readiness.
- Live trading.
- Live endpoints.
- Increasing notional.
- Multi-symbol automation.
- Batch orders.
- Cancel/replace.
- Removing Human Review.
- Removing Manual Execution Confirmation.
- Bypassing V14 gates.

## Explicit Non-Authorization

This design does not authorize order sending.

This design does not authorize live trading.

This design does not authorize live endpoints.

This design does not authorize increasing notional.

This design does not authorize multi-symbol automation.

This design does not authorize batch orders.

This design does not authorize cancel/replace.

This design does not authorize removing Human Review.

This design does not authorize removing Manual Execution Confirmation.

This design does not authorize bypassing V14 gates.

This design does not authorize broker execution readiness.
