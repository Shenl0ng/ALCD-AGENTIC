# Market Open Routine

## Purpose
Evaluate whether valid premarket context becomes actionable during approved market-open timing.

## Required ADLC Reads
- governance/00_ADLC_OPERATING_MODEL.md
- governance/02_SCOPE_AND_CONSTRAINTS.md
- governance/03_HUMAN_AGENT_RESPONSIBILITY.md
- governance/04_AUTONOMY_BOUNDARIES.md
- governance/paper_trading_only.md
- strategy/01_SELECTIVE_EXECUTION_SYSTEM.md
- strategy/02_NO_TRADE_RULES.md

## Required Agent Sequence
Orchestrator -> Data Integrity Agent -> Market Context Agent -> Liquidity Agent -> Session Timing Agent -> Confirmation Agent -> Trade Proposal Agent -> Risk Manager Agent -> Execution Gatekeeper Agent -> Journal Agent.

## What it may do
- Create a paper-trade proposal when all setup gates pass
- Reject setups at any gate
- Record paper-trade approval status

## What it may not do
- Connect to a broker
- Place orders
- Override risk or human approval gates
- Continue after a veto

## Memory files it reads
- memory/market_data_status.md
- memory/market_context.md
- memory/liquidity_map.md
- memory/risk_state.md

## Memory files it writes
- memory/trade_proposals.md
- memory/risk_state.md
- memory/rejected_trades.md
- memory/approved_paper_trades.md
- memory/journal.md

## ADLC Compliance Footer
Routine must state whether paper mode, risk approval, journal readiness, and human approval rules were satisfied.

