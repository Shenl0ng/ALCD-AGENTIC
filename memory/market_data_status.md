# Market Data Status

## ADLC Binding
Phase: Testing & Evaluation, Deployment Monitoring.

## Purpose
Records whether market data is usable for the current routine.

## Required Fields
- Timestamp
- Data source description
- Instruments covered
- Timeframes covered
- Freshness status
- Known gaps
- Data Integrity Agent decision

## Control Rule
If data is stale, missing, or contradictory, downstream agents must stop.

