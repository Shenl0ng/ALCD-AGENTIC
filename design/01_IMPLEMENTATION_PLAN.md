# Implementation Plan

## ADLC Binding
Phase: Architecture Design / Testing & Evaluation.
Control Type: Pre-implementation planning control.
Block Authority: Yes.

## Planning Boundary
This file is a plan only. It does not authorize code, broker integration, credentials, live trading, autonomous execution, or runtime shortcuts.

The default action remains `NO_TRADE`.

## Implementation Phases

### Phase 0: Architecture Validation
Validate that the markdown architecture is complete, internally consistent, and ADLC-bound before any implementation work begins.

Required outputs:

- governance audit pass
- agent authority audit pass
- routine sequencing audit pass
- paper-trading-only audit pass
- runtime design audit pass
- implementation plan audit pass

### Phase 1: Runtime Contract Design
Define non-executable runtime contracts that preserve the markdown architecture.

Required outputs:

- component responsibility map
- interface contracts
- memory read/write contract
- journal contract
- failure reporting contract
- evaluation contract

### Phase 2: Test Design Before Code
Define test cases before implementation.

Required outputs:

- behavioral tests
- no-trade tests
- risk violation tests
- hallucination checks
- paper-trading scorecard
- ADLC compliance checks

### Phase 3: Minimum Viable Runtime Planning
Define the narrowest future runtime that can read markdown, invoke separated agent roles, enforce gates, and write memory records.

Required outputs:

- runtime boundary
- allowed inputs
- allowed outputs
- blocked capabilities
- stop conditions

### Phase 4: Human Approval for First Code
No code may be written until the human owner approves the architecture, implementation boundary, risk controls, and evaluation requirements.

Required outputs:

- human approval record
- approved first-code scope
- explicit list of prohibited capabilities

## Components To Build Later

These components are future implementation candidates only. They must not be created in this planning phase.

### Markdown Instruction Loader
Responsibility:
Load root, governance, strategy, routine, agent, memory, evaluation, and design markdown files as operating instructions.

Must not:

- modify governance
- infer missing controls
- bypass missing files

### Orchestrator Runtime
Responsibility:
Select a routine, load required controls, invoke specialist agents in order, enforce ADLC gates, and stop unsafe workflows.

Must not:

- analyze trades directly
- approve risk
- approve execution
- journal final decisions without Journal Agent output
- collapse specialist responsibilities into one response

### Agent Invocation Layer
Responsibility:
Invoke each specialist agent according to its markdown role, inputs, outputs, autonomy boundary, required reads, required writes, stop conditions, and output format.

Must not:

- let an agent exceed its role
- allow downstream agents to override vetoes
- combine proposal, approval, execution gatekeeping, and journaling

### Memory Manager
Responsibility:
Read and write only the markdown memory files allowed by agent and routine contracts.

Must not:

- invent missing memory state
- write to files outside the agent's required writes
- erase rejected trades or failure reports

### Journal Manager
Responsibility:
Ensure journal readiness before any paper-trade authorization status and record all decisions, vetoes, approvals, and failures.

Must not:

- record only approved paper trades
- omit vetoes
- backfill missing approval state by assumption

### Risk Control Component
Responsibility:
Support the Risk Manager's initial and final risk checks using `governance/risk_limits.md` and `memory/risk_state.md`.

Must not:

- change risk limits
- approve execution
- treat paper gains as permission to increase risk

### Execution Gate Component
Responsibility:
Support the Execution Gatekeeper's block-or-allow status for paper-trade records.

Must not:

- place orders
- connect to a broker
- approve trade quality
- approve risk
- approve live trading
- approve broker execution

### Failure Audit Component
Responsibility:
Generate failure reports when controls are missing, violated, ambiguous, or contradicted.

Must not:

- hide unresolved critical failures
- resume blocked workflows
- downgrade live-trading violations

### Evaluation Harness
Responsibility:
Run future tests against behavior, no-trade discipline, risk violations, hallucination checks, paper-only controls, and ADLC compliance.

Must not:

- treat paper PnL as the primary success metric
- skip failed critical controls

## Component Responsibilities

| Component | Primary Responsibility | Prohibited Authority |
|---|---|---|
| Markdown Instruction Loader | Load markdown controls | Cannot interpret missing controls as approval |
| Orchestrator Runtime | Sequence agents and enforce ADLC | Cannot act as a trading agent |
| Agent Invocation Layer | Preserve specialist roles | Cannot merge agent responsibilities |
| Memory Manager | Read and write controlled memory | Cannot invent state |
| Journal Manager | Maintain decision traceability | Cannot authorize trades |
| Risk Control Component | Support risk-only checks | Cannot approve execution |
| Execution Gate Component | Block unsafe paper-trade authorization | Cannot execute or approve risk |
| Failure Audit Component | Report control failures | Cannot resume blocked workflows |
| Evaluation Harness | Validate behavior before code promotion | Cannot waive failed critical tests |

## Required Interfaces Between Components

Interfaces must be explicit contracts, not implicit shared assumptions.

### Orchestrator to Instruction Loader
Required exchange:

- requested routine
- required markdown files
- load status
- missing or conflicting controls

### Orchestrator to Agent Invocation Layer
Required exchange:

- agent identity
- routine context
- allowed reads
- allowed writes
- stop conditions
- expected output format

### Agent Invocation Layer to Memory Manager
Required exchange:

- files requested
- files allowed
- read status
- write target
- write authorization

### Agent Invocation Layer to Journal Manager
Required exchange:

- agent output
- files read
- files written
- decision
- veto status
- ADLC compliance status

### Risk Control Component to Execution Gate Component
Required exchange:

- proposal ID
- risk decision
- rejection reason if any
- risk state timestamp

### Human Approval Control to Execution Gate Component
Required exchange:

- approval required status
- approval present status
- approval scope
- approval limitation

### Failure Audit Component to Orchestrator
Required exchange:

- failure type
- severity
- affected control
- block status
- remediation requirement

## Required Safety Checks

Every future runtime must check:

- requested action is inside markdown-defined scope
- required governance files are loaded
- agent role matches requested action
- no agent combines proposal, approval, execution gatekeeping, and journaling
- upstream vetoes are preserved
- market data status is usable before analysis
- memory state is not invented
- risk state is known before risk approval
- journal readiness exists before paper-trade authorization status
- failure reports are generated for control breaks

## Required Paper-Trading-Only Checks

Every future runtime must block:

- broker connections
- live orders
- broker paper orders
- credentials
- environment secrets
- API-driven position management
- any claim that `PAPER_TRADE_ALLOWED` means an order was placed
- any attempt to treat architecture approval as execution

Every proposal and gate result must include `Paper Mode: REQUIRED`.

## Required ADLC Checks

Before any routine:

- root instructions are loaded
- governance controls are loaded
- routine phase is known
- agent sequence is allowed
- memory requirements are known

Before any agent:

- role is valid
- required reads are available
- required writes are bounded
- autonomy boundary is explicit
- stop conditions are known

After any agent:

- output format is valid
- ADLC compliance is recorded
- vetoes are honored
- writes are traceable
- no execution authority appears

Before any future implementation phase:

- all evaluation categories pass
- human approval is recorded
- first-code scope is limited
- prohibited capabilities remain prohibited

## Required Memory Read/Write Behavior

Memory reads:

- must be limited to files required by the active agent and routine
- must preserve missing state as missing
- must not infer unavailable data

Memory writes:

- must be limited to the active agent's required writes
- must include the originating agent and routine
- must include decision status
- must include files read and written
- must include ADLC compliance status

Rejected-trade writes:

- must occur whenever a veto blocks a trade candidate
- must name the rejecting agent and failed gate

Approved-paper-trade writes:

- may occur only after paper mode, risk approval, journal readiness, and human approval rules are satisfied
- must not represent broker execution

## Required Journal Behavior

The Journal Agent or Journal Manager must record:

- routine
- agent sequence
- files read
- files written
- proposal ID when present
- vetoes
- risk decision
- execution gate status
- human approval status
- final status
- ADLC compliance

Journal readiness must be confirmed before any paper-trade authorization status. If journal readiness is missing, the result is `EXECUTION_BLOCKED`.

## Required Failure Handling

Failure reports must be generated for:

- missing required governance
- missing required memory
- stale or contradictory data
- hallucinated market state
- skipped specialist agents
- role boundary violations
- veto override attempts
- risk approval gaps
- journal readiness gaps
- human approval gaps
- paper/live boundary confusion
- any broker or live-execution implication

Critical unresolved failures block further paper-trade approvals until reviewed.

## Required Test Categories

Before implementation code, tests must cover:

- governance ADLC binding
- agent authority boundaries
- routine sequencing
- single-model collapse prevention
- market data integrity blocking
- no-trade scenarios
- risk violation scenarios
- execution gate blocking
- journal readiness blocking
- human approval boundaries
- hallucination checks
- failure reporting
- weekly review behavior
- paper-trading scorecard

## What Must Not Be Implemented Yet

The following must not be implemented in this phase:

- `src/`
- application runtime
- package files
- broker integration
- Alpaca connection
- API calls
- credentials
- `.env` files
- order placement
- live trading
- autonomous execution
- position management
- background scheduler
- database
- web interface
- notification system
- model provider integration

## Minimum Viable Runtime Boundary

The minimum viable future runtime is limited to:

- reading markdown instructions
- loading markdown memory state
- invoking separated specialist roles
- enforcing ADLC controls
- enforcing paper-only controls
- producing structured decisions
- writing markdown memory records
- writing journal records
- writing failure reports
- running evaluation checks

The minimum viable runtime is not allowed to place orders, connect to brokers, manage positions, or operate live trading.

## Criteria Required Before Writing First Code

First code is blocked until all criteria are met:

- governance controls pass audit
- agent boundaries pass audit
- routine sequences pass audit
- runtime design passes audit
- implementation plan passes audit
- evaluation categories are approved
- human approval is recorded
- first-code scope is explicitly limited
- prohibited capabilities are listed and accepted
- paper-trading-only boundary is reaffirmed
- default action remains `NO_TRADE`

## Final Control

This implementation plan does not authorize implementation. It defines the controls that must be satisfied before implementation can be considered.

