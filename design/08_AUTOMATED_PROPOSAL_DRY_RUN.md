# Phase 26 Automated Proposal Dry-Run Design

## 1. Purpose

Phase 26 designs an automated dry-run workflow where the system may run automatically to analyze one symbol and produce one of:

- `NO_TRADE`
- `REJECT`
- `TRADE_PROPOSAL`

This phase is dry-run only. It must not create Paper Order Requests, request Human Approval, request Manual Execution Confirmation, enable `PAPER_ORDER_EXECUTION_ENABLED`, send orders, use Alpaca order API, modify paper execution logic, increase notional limits, add live trading, create `.env` files, or print secrets.

## 2. Context

Operating Policy After V4 is `PASS`.

V4 allows manual limited paper sends under strict gates, but automation remains prohibited until separately designed and audited.

Phase 26 does not approve autonomous execution. It only designs automated analysis in `DRY_RUN_ONLY` mode.

## 3. Allowed Behavior

Allowed behavior:

- Automatically run analysis in `DRY_RUN_ONLY` mode.
- Use one symbol only.
- Use deterministic or configured market data input.
- Run Data Integrity Agent.
- Run Market Context Agent.
- Run Liquidity Agent.
- Run Session Timing Agent.
- Run Confirmation Agent.
- Produce `NO_TRADE`, `REJECT`, or `TRADE_PROPOSAL`.
- Run Strategy Evaluation Harness.
- Run Evaluation-First Gate.
- Run Negative Case Regression checks.
- Run Risk Manager in dry-run/read-only mode.
- Write journal entry.
- Write dry-run report.

Allowed behavior ends at dry-run reporting. It does not continue into approval, paper request, or execution.

## 4. Required Flow

The required flow is:

1. Load V4 operating policy.
2. Confirm `DRY_RUN_ONLY` mode.
3. Confirm `PAPER_ORDER_EXECUTION_ENABLED` is not enabled.
4. Confirm no live trading.
5. Confirm one symbol only.
6. Run data integrity.
7. Run specialist agents.
8. Produce decision:
   - `NO_TRADE`
   - `REJECT`
   - `TRADE_PROPOSAL`
9. Run Strategy Evaluation Harness.
10. Run Evaluation-First Gate.
11. Run Negative Case Regression checks.
12. Run Risk Manager dry-run check.
13. Write journal.
14. Write automated dry-run report.
15. Stop.

The workflow must stop after report generation.

## 5. Agent Responsibilities

Agent responsibilities:

- Data Integrity Agent verifies data source, freshness, completeness, and whether analysis may proceed.
- Market Context Agent evaluates higher-timeframe context.
- Liquidity Agent identifies specific liquidity locations or rejects vague levels.
- Session Timing Agent verifies whether timing is valid.
- Confirmation Agent checks whether confirmation is observable.
- Trade Proposal Agent may produce `TRADE_PROPOSAL` only when prior agents pass.
- Risk Manager performs dry-run/read-only risk evaluation only.
- Journal Agent records the dry-run decision and reasoning.
- Orchestrator stops the workflow before Human Approval, Manual Execution Confirmation, Paper Order Request, or Paper Send.

No single agent may analyze, propose, approve, execute, and journal a trade.

## 6. Decision Outputs

Allowed decisions:

- `NO_TRADE`: evidence is insufficient, timing is invalid, context is unclear, liquidity is weak, confirmation is missing, or waiting is better.
- `REJECT`: a proposal or setup fails required quality, data, risk, ADLC, journal, or negative-case checks.
- `TRADE_PROPOSAL`: a dry-run proposal exists for review, but it is not approved and cannot become a Paper Order Request in Phase 26.

`TRADE_PROPOSAL` is not approval. It is not paper send readiness. It is not broker execution readiness.

## 7. Strategy Evaluation Requirements

Strategy Evaluation Harness must run for any `TRADE_PROPOSAL` and may also score `NO_TRADE` and `REJECT` cases for process quality.

Required checks:

- Higher-timeframe context quality.
- Liquidity location quality.
- Session timing quality.
- Entry confirmation quality.
- Fixed risk quality when a proposal exists.
- Reward/risk quality when a proposal exists.
- Journal readiness.
- Data freshness.
- Data completeness.
- Specialist agent sequencing.
- Risk Manager decision quality.
- No-trade discipline.
- Correct rejection of weak setups.

If Strategy Evaluation fails, final status must be `AUTOMATED_DRY_RUN_BLOCKED` or `AUTOMATED_DRY_RUN_REJECTED`.

## 8. Evaluation-First Gate Requirements

Evaluation-First Gate must run after Strategy Evaluation.

Gate behavior:

- It may block weak or incomplete analysis.
- It may block a dry-run `TRADE_PROPOSAL`.
- It must not unlock Human Approval.
- It must not unlock Paper Order Request creation.
- It must not unlock paper send readiness.
- It must not unlock broker execution readiness.

In Phase 26, `EVALUATION_GATE_PASSED` means only that the dry-run proposal can be recorded as a dry-run proposal. It does not authorize any execution path.

## 9. Negative Case Regression Requirements

Negative Case Regression checks must confirm:

- Negative-case regression artifacts exist.
- Thresholds remain passing.
- No missed blocks exist.
- No false passes exist.
- No negative case produces paper send readiness.
- No negative case produces broker execution readiness.
- The current setup does not match known negative-case failure patterns.
- The current setup is not a weak setup.
- The current setup is not a forced trade.
- The current setup is not rubber-stamped.

If any negative-case regression check fails, final status must be `AUTOMATED_DRY_RUN_BLOCKED`.

## 10. Risk Manager Dry-Run Requirements

Risk Manager may run only in dry-run/read-only mode.

Risk Manager must check:

- Paper-only boundary.
- Fixed risk if a proposal exists.
- Credible invalidation if a proposal exists.
- Max notional remains `<= 100 USD` if a proposal exists.
- No short selling.
- No crypto.
- No options.
- No margin or leverage.
- No extended hours.
- No batch behavior.
- No cancel/replace behavior.
- No live trading assumption.

Risk Manager output in Phase 26 cannot authorize execution.

## 11. Hard Blocks

Hard blocks:

- More than one symbol.
- Any Paper Order Request creation.
- Any Human Approval request.
- Any Manual Execution Confirmation request.
- Any `PAPER_ORDER_EXECUTION_ENABLED=true`.
- Any paper send readiness.
- Any broker execution readiness.
- Any live trading assumption.
- Any batch behavior.
- Any cancel/replace behavior.
- Any automation that sends orders.
- Any Alpaca order API use.
- Any secret printing.
- Any `.env` file creation.

Any hard block produces final status `AUTOMATED_DRY_RUN_BLOCKED`.

## 12. Required Output Artifact

Required output artifact:

`reports/automated_proposal_dry_run/<timestamp>/AUTOMATED_PROPOSAL_DRY_RUN_REPORT.md`

The report must include:

- Symbol.
- Mode.
- Data integrity status.
- Market context result.
- Liquidity result.
- Session timing result.
- Confirmation result.
- Decision.
- Strategy evaluation status.
- Evaluation gate status.
- Negative-case regression status.
- Risk dry-run status.
- Journal reference.
- Final status.
- Reason.
- Statement: `No order was sent.`
- Statement: `No Paper Order Request was created.`
- Statement: `Live trading remains unsupported.`

## 13. Allowed Final Statuses

Allowed final statuses:

- `AUTOMATED_DRY_RUN_NO_TRADE`
- `AUTOMATED_DRY_RUN_REJECTED`
- `AUTOMATED_DRY_RUN_PROPOSAL_CREATED`
- `AUTOMATED_DRY_RUN_BLOCKED`

No final status may imply approval, paper send readiness, broker execution readiness, or live trading readiness.

## 14. Success Criteria

Success criteria:

- System can run automatically in `DRY_RUN_ONLY`.
- System can produce `NO_TRADE`, `REJECT`, or `TRADE_PROPOSAL`.
- System cannot create Paper Order Request.
- System cannot send orders.
- System cannot enable execution flag.
- System writes report and journal.
- Live trading remains unsupported.

## 15. What Remains Prohibited

The following remain prohibited:

- Paper order request creation.
- Human approval request.
- Manual execution confirmation.
- Paper send.
- Live trading.
- Live endpoints.
- Alpaca order API use.
- Batch orders.
- Cancel/replace.
- Notional increase.
- Frequency increase.
- Autonomous execution.
- Any automation that sends orders.
- Any bypass of Evaluation-First Gate.
- Any bypass of Negative Case Regression.
- Any bypass of Risk Manager dry-run checks.
- Creating `.env` files.
- Printing secrets.

## 16. Conditions Before Implementation

Implementation may begin only after this design is accepted.

Before implementation:

- Confirm Operating Policy After V4 remains `PASS`.
- Confirm `DRY_RUN_ONLY` is the default mode.
- Confirm execution flag checks are explicit and fail closed.
- Define one-symbol input validation.
- Define deterministic or configured market data input format.
- Define report schema.
- Define journal schema.
- Add tests proving no Paper Order Request can be created.
- Add tests proving no Human Approval request can be created.
- Add tests proving no Manual Execution Confirmation request can be created.
- Add tests proving no order send can occur.
- Add tests proving no Alpaca order API is called.

## 17. Explicit Live Trading Boundary

Live trading remains unsupported.

Phase 26 does not design, imply, prepare, or authorize live trading. Any live trading assumption must block the automated dry-run.

## 18. Offline Safety Statement

Phase 26 is an automated analysis dry-run design only.

No order was sent by this design. No Paper Order Request is authorized by this design. No Human Approval request is authorized by this design. No Manual Execution Confirmation request is authorized by this design. `PAPER_ORDER_EXECUTION_ENABLED` was not enabled by this design. Alpaca order API was not used by this design. No runtime code was changed by this design. No `.env` file was created by this design. No secrets were printed by this design.
