# ADLC Traceability Matrix

## ADLC Binding
Phase: Architecture Design / Testing & Evaluation / Deployment Monitoring.
Control Type: Mandatory operating control.
Block Authority: Yes.

## Operational Control
Every component must be traceable to ADLC phase, reads, writes, and authority.

| Component | ADLC Phase | Reads | Writes | Can Approve? | Can Reject? | Can Execute? |
|---|---|---|---|---|---|---|
| Orchestrator | Design / Monitoring | governance/, agents/, routines/ | journal, failure_reports | No | Yes | No |
| Data Integrity Agent | Testing / Evaluation | market_data_status | market_data_status, failure_reports | No | Yes | No |
| Market Context Agent | Design / Evaluation | strategy/, market_data_status | market_context, rejected_trades | No | Yes | No |
| Liquidity Agent | Design / Evaluation | market_context, strategy/ | liquidity_map, rejected_trades | No | Yes | No |
| Session Timing Agent | Scope / Evaluation | market_data_status, strategy/ | journal, rejected_trades | No | Yes | No |
| Confirmation Agent | Evaluation | market_context, liquidity_map | trade_proposals, rejected_trades | No | Yes | No |
| Trade Proposal Agent | Simulation | prior gate outputs | trade_proposals | No | No | No |
| Risk Manager Agent | Scope / Testing | risk_limits, risk_state | risk_state, rejected_trades | Risk only | Yes | No |
| Execution Gatekeeper | Deployment Control | proposal, risk, human approval | approved_paper_trades, rejected_trades | Gate only | Yes | No |
| Journal Agent | Maintenance | all outputs | journal, failure_reports | No | No | No |
| Weekly Review Agent | Maintenance / Learning | journal, lessons | lessons_learned, failure_reports | No | No | No |
| Failure Auditor | Testing / Monitoring | all files | failure_reports, lessons_learned | No | Yes | No |

## Block Condition
Any component acting outside its row violates ADLC and must be stopped.
