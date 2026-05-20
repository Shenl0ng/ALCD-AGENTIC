# Runtime System Design

## ADLC Binding
Phase: Architecture Design / Testing & Evaluation.
Control Type: Runtime design control.
Block Authority: Yes.

## Runtime Purpose
The runtime exists to operate the markdown-defined paper-trading workflow without changing its governance. It coordinates the Orchestrator, specialist agents, memory files, evaluation controls, and review loops as a controlled decision process.

The runtime does not trade. It does not connect to a broker. It does not place live or paper orders directly. It produces auditable markdown-backed decisions where the default action is `NO_TRADE`.

## Markdown Instruction Loading
The Orchestrator is the first runtime authority. Before any specialist agent is invoked, it must load the governing markdown instructions in this order:

1. Root operating instructions from `AGENTS.md` and `CLAUDE.md`.
2. ADLC controls from `governance/00_ADLC_OPERATING_MODEL.md`.
3. Scope, autonomy, human responsibility, paper-only, risk, and traceability controls from `governance/`.
4. Strategy rules from `strategy/`.
5. Routine instructions from `routines/`.
6. Agent role contracts from `agents/`.
7. Current state from `memory/`.

If required instructions are missing, contradictory, or outside paper-trading scope, the Orchestrator must stop with `ADLC_BLOCKED` or `NO_TRADE`.

## Specialist Agent Invocation
Specialist agents are invoked by role, not by convenience. The Orchestrator may not collapse analysis, proposal, risk approval, gatekeeping, and journaling into one agent response.

Each invocation must preserve:

- the agent's role and non-role
- required reads
- required writes
- autonomy boundary
- stop conditions
- output format
- ADLC compliance footer

A downstream agent may not override an upstream veto.

## Required Agent Sequence
The full market-open paper-trade evaluation sequence is:

1. Orchestrator
2. Data Integrity Agent
3. Market Context Agent
4. Liquidity Agent
5. Session Timing Agent
6. Confirmation Agent
7. Trade Proposal Agent
8. Risk Manager Agent
9. Execution Gatekeeper Agent
10. Journal Agent

Premarket, midday, market-close, and weekly-review routines may use shorter sequences only when their routine file explicitly allows it. Any sequence that can produce a paper-trade approval must include Data Integrity, Risk Manager, Execution Gatekeeper, and Journal Agent.

## ADLC Runtime Enforcement
ADLC is enforced as a runtime gate before and after every specialist action.

Before an agent runs, the Orchestrator verifies:

- the requested action is within the routine's ADLC phase
- required governance files are available
- required memory files are available or explicitly marked unavailable
- the agent is not exceeding its role
- the action remains paper trading only
- human responsibility is explicit

After an agent returns output, the Orchestrator verifies:

- the output follows the agent's declared format
- files read and written are traceable
- vetoes are respected
- no execution authority was introduced
- the final decision remains evaluable

Any failed ADLC check returns `ADLC_BLOCKED` or `NO_TRADE`.

## Paper-Trading-Only Enforcement
Paper-trading-only mode is enforced by `governance/paper_trading_only.md`, `governance/02_SCOPE_AND_CONSTRAINTS.md`, and the Execution Gatekeeper.

The runtime must block any workflow that attempts to:

- connect to a broker
- use credentials
- create environment secrets
- place live orders
- place broker paper orders directly
- manage positions through an API
- treat an architectural approval as execution

Every proposal and gate result must explicitly state `Paper Mode: REQUIRED`. If paper mode is missing or ambiguous, the decision is `EXECUTION_BLOCKED`.

## Market Data Integrity Check
The Data Integrity Agent runs before market context, liquidity, timing, confirmation, proposal, or risk analysis.

It checks:

- timestamps
- source description
- instruments covered
- timeframes covered
- freshness
- missing data
- contradictory data
- session status availability

If data quality is insufficient, the workflow stops. Missing data may not be filled by assumption.

## Memory Reads
Memory files are read as state, not as executable instructions. Agents may read only the memory files required by their role and routine.

The runtime must preserve the distinction between:

- `memory/market_data_status.md` for data availability
- `memory/market_context.md` for higher-timeframe state
- `memory/liquidity_map.md` for liquidity location
- `memory/watchlist.md` for observation candidates
- `memory/risk_state.md` for current risk constraints
- `memory/trade_proposals.md` for proposed paper trades
- `memory/rejected_trades.md` for vetoed ideas
- `memory/approved_paper_trades.md` for gate-approved paper-trade records
- `memory/journal.md` for decision traceability
- `memory/lessons_learned.md` for reviewed learning
- `memory/failure_reports.md` for control failures

If required memory is missing, the agent must report the gap instead of inventing state.

## Memory Writes
Memory writes are controlled outputs. An agent may write only to the files listed in its `Required Writes` section.

Every memory write must include:

- date or timestamp context
- originating agent
- routine
- files read
- decision
- reason
- ADLC compliance status

Rejected trades must be written when a veto occurs. Approved paper-trade records may be written only after the Execution Gatekeeper confirms paper mode, risk approval, journal readiness, and human approval rules.

## Trade Proposal Creation
The Trade Proposal Agent creates a proposal only after these prior gates pass:

- Data Integrity Agent returns usable data status
- Market Context Agent validates higher-timeframe context
- Liquidity Agent validates strong location
- Session Timing Agent validates timing window
- Confirmation Agent validates simple confirmation

A proposal must include:

- symbol
- direction
- context
- liquidity location
- timing window
- confirmation
- entry hypothesis
- invalidation
- risk basis
- paper-mode label

A proposal is not approval. A proposal cannot be executed.

## Risk Manager Checks
The Risk Manager performs risk checks at two points.

Initial risk availability check:

- confirms whether new paper-trade review is allowed for the day
- checks daily loss state
- checks current exposure
- checks whether risk state is known

Final proposal risk check:

- verifies defined invalidation
- verifies fixed risk
- verifies proposal risk against limits
- verifies exposure and daily state
- returns `RISK_APPROVED` or `RISK_REJECTED`

Risk approval is risk-only. It is not trade approval, execution approval, broker approval, or live-trading permission.

## Execution Gatekeeper Blocking
The Execution Gatekeeper cannot execute. It only produces gate status.

It must return `EXECUTION_BLOCKED` unless all required conditions are true:

- paper mode is explicit
- Risk Manager returned `RISK_APPROVED`
- journal readiness is confirmed
- human approval rules are satisfied
- proposal is complete
- no unresolved veto exists
- no live-trading or broker-execution implication exists

`PAPER_TRADE_ALLOWED` means the architecture may record an approved paper-trade decision. It does not mean an order is sent anywhere.

## Human Approval
Human approval is governed by `governance/human_approval.md` and `governance/03_HUMAN_AGENT_RESPONSIBILITY.md`.

Human approval is required for:

- risk limit changes
- strategy rule changes
- autonomy expansion
- paper-trade authorization when rules require discretionary confirmation
- any future move toward implementation

Human approval cannot substitute for:

- risk approval
- journal readiness
- paper-mode confirmation
- specialist agent sequencing
- ADLC compliance

Missing required human approval returns `NO_TRADE` or `EXECUTION_BLOCKED`.

## Journal Readiness
Journal readiness must be verified before any paper order request or paper-trade authorization status.

Journal readiness means the Journal Agent can record:

- routine
- agents invoked
- files read
- files written
- proposal ID
- risk decision
- gate decision
- human approval state
- final decision
- ADLC compliance

If the journal cannot be prepared before authorization, the Execution Gatekeeper must return `EXECUTION_BLOCKED`.

## Weekly Review Improvement Loop
Weekly review improves the system through controlled learning, not immediate rule changes.

The Weekly Review Agent reviews:

- journal completeness
- rejected-trade quality
- approved paper-trade quality
- risk compliance
- human approval compliance
- paper-only compliance
- repeated failure modes
- lessons learned

Recommendations are written to `memory/lessons_learned.md`. Any change to strategy, risk, autonomy, routine sequence, or evaluation rules must pass `governance/09_CHANGE_CONTROL.md`.

## Failure Reports
Failure reports are generated by the Failure Auditor, Orchestrator, Journal Agent, or any routine that identifies a control break.

Failure reports are required for:

- missing or stale data used in analysis
- hallucinated market claims
- skipped specialist agents
- overridden vetoes
- missing human approval
- missing risk approval
- missing journal readiness
- paper/live boundary confusion
- any attempted broker or live-execution behavior
- repeated unresolved process gaps

Critical unresolved failures block further paper-trade approvals until reviewed.

## Required Pre-Implementation Tests
Before any implementation code is written, the architecture must pass:

- behavioral test cases in `evaluation/behavioral_test_cases.md`
- no-trade scenarios in `evaluation/no_trade_scenarios.md`
- risk violation scenarios in `evaluation/risk_violation_scenarios.md`
- hallucination checks in `evaluation/hallucination_checks.md`
- paper-trading scorecard in `evaluation/paper_trading_scorecard.md`

Minimum pass conditions:

- all governance files are ADLC-bound
- agents remain role-bound
- Orchestrator blocks single-model collapse
- default action remains `NO_TRADE`
- vetoes cannot be overridden
- paper-only boundary is explicit
- no execution occurs without risk approval
- no execution occurs without journal readiness
- human approval cannot bypass required gates

## Final Runtime Constraint
This design is not implementation permission. It is a markdown architecture control for future evaluation. Until a separate ADLC-approved implementation phase exists, the system remains documentation-only and paper-trading-only.

