# Market Close Routine

## Purpose
Close the daily control loop by reviewing decisions, records, and risk state.

## Required ADLC Reads
- governance/00_ADLC_OPERATING_MODEL.md
- governance/05_SUCCESS_METRICS.md
- governance/08_DEPLOYMENT_MONITORING.md
- governance/risk_limits.md

## Required Agent Sequence
Orchestrator -> Risk Manager Agent -> Journal Agent -> Failure Auditor Agent.

## What it may do
- Reconcile journal completeness
- Update risk state
- Record unresolved failures
- Prepare items for weekly review

## What it may not do
- Create new trade proposals
- Authorize late paper trades
- Modify strategy or risk limits

## Memory files it reads
- memory/risk_state.md
- memory/trade_proposals.md
- memory/rejected_trades.md
- memory/approved_paper_trades.md
- memory/journal.md

## Memory files it writes
- memory/risk_state.md
- memory/journal.md
- memory/failure_reports.md

## ADLC Compliance Footer
Routine must confirm all daily decisions are journaled or list the blocking gaps.

