# AI Paper-Trading Multi-Agent Architecture

This repository defines an ADLC-governed, paper-trading-only, multi-agent architecture for selective trade evaluation.

The current active implementation phase is Phase 0: markdown loading and architecture validation only.

Claude must treat this file as the root operating instruction, then read the required control files before taking action.

## Required First Reads

Before making decisions or edits, read:

1. `AGENTS.md`
2. `governance/00_ADLC_OPERATING_MODEL.md`
3. `governance/02_SCOPE_AND_CONSTRAINTS.md`
4. `governance/03_HUMAN_AGENT_RESPONSIBILITY.md`
5. `governance/04_AUTONOMY_BOUNDARIES.md`
6. `governance/paper_trading_only.md`
7. `governance/human_approval.md`
8. `governance/risk_limits.md`
9. `governance/10_ADLC_TRACEABILITY_MATRIX.md`
10. `design/00_RUNTIME_SYSTEM_DESIGN.md`
11. `design/01_IMPLEMENTATION_PLAN.md`

If the task concerns a specific agent, routine, memory file, strategy file, or evaluation file, read that file too.

## Hard Constraints

- The system is paper trading only.
- The default decision is `NO_TRADE`.
- No single agent may analyze, approve, execute, and journal a trade by itself.
- Execution is blocked unless paper mode, risk approval, journal readiness, and human approval rules are satisfied.
- Live trading is prohibited.
- Broker integration is prohibited.
- Alpaca integration is prohibited.
- Market data API integration is prohibited.
- Order execution is prohibited.
- Credentials, API keys, secrets, and `.env` files are prohibited.
- Autonomous trading behavior is prohibited.
- Trade decision logic is prohibited in Phase 0.

## ADLC Lock

ADLC is an operating control, not decoration. Every agent, routine, strategy file, memory file, and evaluation file must preserve:

- explicit scope
- human accountability
- agent autonomy limits
- veto gates
- observable outputs
- failure handling
- review and change control

If an action lacks ADLC phase, scope, owner, input, output, veto path, and human accountability, block it.

## Required Operating Flow

1. Orchestrator selects the routine and validates ADLC scope.
2. Specialist agents run in sequence.
3. Any veto produces `NO_TRADE`.
4. Risk Manager may approve risk only, not execution.
5. Execution Gatekeeper may allow a paper-trade handoff only when all gates pass.
6. Journal Agent records decisions, including rejected trades.
7. Weekly Review Agent and Failure Auditor evaluate behavior and compliance.

## Phase 0 Allowed Work

Allowed:

- Read markdown architecture files.
- Edit markdown architecture files when requested.
- Maintain Phase 0 architecture validation code.
- Maintain tests for architecture validators.
- Run the architecture validator.
- Run validator tests.

Phase 0 validation may check:

- required markdown files exist
- governance files contain `## ADLC Binding`
- agent files contain required sections
- Execution Gatekeeper cannot approve trade quality, risk, broker execution, or live trading
- Orchestrator blocks single-model collapse
- paper-trading-only governance exists
- default action remains `NO_TRADE`

## Prohibited Work

Do not add:

- `src/`
- package files
- runnable trading app scaffolding
- Alpaca clients
- broker clients
- market data clients
- API calls
- order placement
- live trading behavior
- autonomous execution loops
- schedulers
- credentials
- secrets
- `.env` files
- strategy evaluation logic
- position management logic

If a user asks for any prohibited work, stop and explain that the repository is limited to Phase 0 architecture validation unless ADLC change control explicitly approves a new phase.

## Runtime Validator

The current Phase 0 validator is:

```bash
python3 runtime/architecture_validator.py
```

The current validator tests are:

```bash
python3 -m unittest tests/test_architecture_validator.py
```

Run these after any change that could affect architecture controls.

## How Claude Should Act

- Prefer narrow, explicit changes.
- Do not infer permission from paper-trading language to add execution behavior.
- Do not collapse specialist responsibilities into one agent.
- Do not bypass the Orchestrator, Risk Manager, Execution Gatekeeper, or Journal Agent in architecture changes.
- Preserve human accountability.
- Preserve veto gates.
- Preserve the journal and weekly review loop.
- Treat `PAPER_TRADE_ALLOWED` as a recordable architecture status only, not execution.
- Treat missing data, missing risk state, missing journal readiness, or missing human approval as a block.

## Completion Standard

For architecture edits, report:

- files changed
- controls affected
- validation command run
- test command run
- confirmation that no trading, broker, Alpaca, API, credential, market-data, or execution logic was added
