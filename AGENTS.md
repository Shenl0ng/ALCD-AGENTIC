# AGENTS.md

## ADLC Binding
Phase: Architecture Design / Scope & Constraints.
Control Type: Root agent operating instructions.
Authority: Defines allowed markdown-only architecture behavior; does not grant execution authority.

## Project Goal

This project is an AI-assisted paper trading system for Alpaca.

The goal is not to build an autonomous live trading bot.

The goal is to design a controlled multi-agent decision system that researches, evaluates, proposes, rejects, journals, and reviews paper trading ideas.

The system must prioritize:

1. Paper trading only
2. Capital preservation
3. Selective execution
4. Multi-agent separation of responsibilities
5. Human accountability
6. Risk control
7. Journaling and review
8. ADLC-based architecture

## Core Strategy

The trading strategy is based on a selective execution system.

A trade idea is only valid when these conditions align:

1. Higher-timeframe context
2. Strong liquidity location
3. Correct session or timing window
4. Simple entry confirmation
5. Fixed risk
6. Journaling and review

The system must not search for one magic signal, one indicator, one pattern, or one secret entry.

Default decision: NO TRADE.

## Architecture Principle

This is not a single-agent system.

No single agent may analyze, propose, approve, execute, and journal a trade.

The system uses specialist agents:

- Orchestrator Agent
- Data Integrity Agent
- Market Context Agent
- Liquidity Agent
- Session Timing Agent
- Confirmation Agent
- Trade Proposal Agent
- Risk Manager Agent
- Execution Gatekeeper Agent
- Journal Agent
- Weekly Review Agent
- Failure Auditor Agent

Each agent must have a narrow role, clear inputs, clear outputs, autonomy limits, failure modes, and stop conditions.

## System Flow

The normal flow is:

1. Orchestrator coordinates the process.
2. Data Integrity Agent verifies data quality and freshness.
3. Risk Manager checks whether trading is allowed for the day.
4. Market Context Agent evaluates higher-timeframe context.
5. Liquidity Agent identifies meaningful liquidity locations.
6. Session Timing Agent checks whether the timing window is valid.
7. Confirmation Agent checks for a simple entry confirmation.
8. Trade Proposal Agent creates a proposal only if prior agents pass.
9. Risk Manager performs final risk approval or rejection.
10. Execution Gatekeeper verifies paper-only, approval, risk, and journal readiness.
11. Journal Agent records the decision.
12. Weekly Review Agent audits process quality and lessons learned.

If any agent rejects, the trade is blocked.

## ADLC Requirement

This project follows the Agentic Development Life Cycle.

Do not jump directly to implementation.

Before writing code, the system must define:

- Problem hypothesis
- Scope and constraints
- Human-agent responsibility
- Autonomy boundaries
- Failure modes
- Evaluation metrics
- Data flow
- Memory flow
- Routine behavior
- Monitoring and review process

Every file must support this architecture.

## Paper Trading Only

This project is paper trading only.

Live trading is prohibited.

Do not add live trading logic.
Do not add real-money execution.
Do not add credentials.
Do not create `.env` files with secrets.
Do not bypass human approval.
Do not bypass risk approval.
Do not bypass journaling.

## Current Phase

The current phase is markdown architecture only.

Allowed:

- Create `.md` files
- Edit `.md` files
- Define agents
- Define governance
- Define strategy
- Define routines
- Define memory structure
- Define evaluation rules

Not allowed:

- No application code
- No `src/`
- No package scaffolding
- No Python trading logic
- No TypeScript trading logic
- No Alpaca integration
- No API calls
- No order execution
- No automation runtime yet

## Required Repository Structure

Use this structure:

```text
CLAUDE.md
AGENTS.md

agents/
strategy/
governance/
memory/
routines/
evaluation/
