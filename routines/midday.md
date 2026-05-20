# Midday Routine

## Purpose
Monitor existing context, reject poor-quality midday conditions, and prevent forced trades.

## Required ADLC Reads
- governance/00_ADLC_OPERATING_MODEL.md
- governance/02_SCOPE_AND_CONSTRAINTS.md
- governance/06_FAILURE_MODES.md
- strategy/02_NO_TRADE_RULES.md

## Required Agent Sequence
Orchestrator -> Data Integrity Agent -> Market Context Agent -> Session Timing Agent -> Journal Agent.

## What it may do
- Refresh data status
- Update context if structure materially changes
- Record no-trade conditions

## What it may not do
- Force trades during low-quality liquidity
- Approve risk
- Authorize paper trades unless the approved routine and all gates are explicitly re-run

## Memory files it reads
- memory/market_data_status.md
- memory/market_context.md
- memory/liquidity_map.md
- memory/rejected_trades.md

## Memory files it writes
- memory/market_data_status.md
- memory/market_context.md
- memory/rejected_trades.md
- memory/journal.md

## ADLC Compliance Footer
Routine must document whether midday conditions supported observation only or a fully gated paper-trade review.

