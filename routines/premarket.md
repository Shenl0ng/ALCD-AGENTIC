# Premarket Routine

## Purpose
Prepare watchlist, context, and liquidity hypotheses before any active timing or confirmation checks.

## Required ADLC Reads
- governance/00_ADLC_OPERATING_MODEL.md
- governance/01_PROBLEM_HYPOTHESIS.md
- governance/02_SCOPE_AND_CONSTRAINTS.md
- governance/03_HUMAN_AGENT_RESPONSIBILITY.md
- governance/04_AUTONOMY_BOUNDARIES.md
- strategy/01_SELECTIVE_EXECUTION_SYSTEM.md

## Required Agent Sequence
Orchestrator -> Data Integrity Agent -> Market Context Agent -> Liquidity Agent -> Journal Agent.

## What it may do
- Validate data readiness
- Update higher-timeframe context
- Update liquidity map
- Update watchlist

## What it may not do
- Confirm entries
- Approve risk
- Authorize paper trades
- Execute any trade

## Memory files it reads
- memory/market_data_status.md
- memory/watchlist.md

## Memory files it writes
- memory/market_data_status.md
- memory/market_context.md
- memory/liquidity_map.md
- memory/watchlist.md
- memory/journal.md

## ADLC Compliance Footer
Routine must end with files read, files written, agent sequence, vetoes, and final status `ADLC_PASS`, `ADLC_BLOCKED`, or `NO_TRADE`.

