# Weekly Review Routine

## Purpose
Audit paper-trading behavior, ADLC compliance, risk discipline, veto quality, and lessons learned.

## Required ADLC Reads
- governance/00_ADLC_OPERATING_MODEL.md
- governance/05_SUCCESS_METRICS.md
- governance/06_FAILURE_MODES.md
- governance/07_EVALUATION_PROTOCOL.md
- governance/09_CHANGE_CONTROL.md
- governance/10_ADLC_TRACEABILITY_MATRIX.md

## Required Agent Sequence
Orchestrator -> Weekly Review Agent -> Failure Auditor Agent -> Journal Agent.

## What it may do
- Score process quality
- Identify repeated failure modes
- Recommend change-control candidates
- Update lessons learned

## What it may not do
- Change risk limits directly
- Change strategy rules directly
- Convert paper results into live deployment approval

## Memory files it reads
- memory/journal.md
- memory/rejected_trades.md
- memory/approved_paper_trades.md
- memory/lessons_learned.md
- memory/failure_reports.md

## Memory files it writes
- memory/lessons_learned.md
- memory/failure_reports.md
- memory/journal.md

## ADLC Compliance Footer
Routine must output `ADLC_PASS`, `ADLC_WARNING`, or `ADLC_FAILURE` with change-control candidates.

