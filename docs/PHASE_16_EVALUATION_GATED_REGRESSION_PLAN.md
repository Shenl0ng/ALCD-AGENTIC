# Phase 16 Evaluation-Gated Paper Send Regression Plan

## 1. Purpose

Phase 16 defines one controlled paper send regression after Phase 15.

The purpose is to verify that the Evaluation-First Gate is now mandatory before:

- Human Approval.
- Paper Order Request creation.
- Paper Send.

This plan does not authorize live trading, automation, increased notional, batch orders, cancel/replace, or any new order behavior.

## 2. Entry Criteria

Before the regression may begin:

- Phase 15 Evaluation-First Gate implementation status is `PASS`.
- Full test suite passes.
- Architecture validation passes.
- System starts from `DRY_RUN_ONLY`.
- `PAPER_ORDER_EXECUTION_ENABLED` is unset or false before the manual send window.
- Alpaca paper credentials are present only in local shell environment when needed.
- No secrets are printed or written to reports.
- No `.env` files are created.
- Operator confirms this is paper trading only.

## 3. Required Pre-Send Checks

Run these checks before any controlled paper send:

- Run full tests.
- Run architecture validation.
- Run dry-run flow.
- Run mocked paper send.
- Confirm proposal validation is `PASS`.
- Confirm Strategy Evaluation status is `PASS`.
- Confirm Evaluation-First Gate status is `EVALUATION_GATE_PASSED`.
- Confirm Risk Manager output is `RISK_APPROVED`.
- Confirm Human Approval is `HUMAN_APPROVED_FOR_PAPER_ONLY`.
- Confirm Manual Execution Confirmation is `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY`.
- Confirm journal commit exists before send.
- Confirm preflight status is `PAPER_ORDER_SEND_ALLOWED`.
- Confirm paper account mode.
- Confirm ADLC compliance is `PASS`.

## 4. Evaluation Gate Checks

The regression must prove the Evaluation-First Gate is mandatory.

Required checks:

- Strategy evaluation runs after proposal creation.
- Evaluation gate passes before Human Approval starts.
- Human Approval cannot start without `EVALUATION_GATE_PASSED`.
- Paper Order Request cannot be created without `EVALUATION_GATE_PASSED`.
- Paper Send cannot occur without `EVALUATION_GATE_PASSED`.
- Evaluation score meets the minimum threshold.
- No hard-fail condition exists.
- ADLC compliance is `PASS`.
- Data integrity is `PASS`.
- Fixed risk exists.
- Journal readiness exists.
- Specialist-agent sequencing is valid.
- No live trading assumption exists.

Hard-fail conditions that must block the run:

- Live trading assumption.
- Missing fixed risk.
- Missing journal readiness.
- Bypassed specialist agents.
- Missing data integrity.
- Forced trade behavior.
- Vague confirmation.
- Weak or missing liquidity location.
- Missing higher-timeframe context.
- Excessive confidence without evidence.

## 5. Paper Send Constraints

The controlled regression send must preserve all existing constraints:

- Manual only.
- Paper trading only.
- Max notional `<= 100 USD`.
- Limit order only.
- Time in force: `day`.
- One order only.
- No batch orders.
- No automation.
- No live trading.
- No live endpoints.
- No short selling.
- No crypto.
- No options.
- No margin or leverage.
- No extended hours.
- No cancel/replace.
- No autonomous follow-up trades.
- No notional increase.

## 6. Post-Send Checks

After the send attempt:

- Confirm paper send result JSON exists.
- Confirm execution result was recorded.
- Confirm Alpaca paper order ID if returned.
- Confirm post-send journal entry exists.
- Run reconciliation.
- Confirm reconciliation JSON exists.
- Confirm reconciliation status.
- Confirm no follow-up order was created.
- Confirm no cancel/replace happened.
- Confirm no live trading was touched.
- Create controlled paper send report from real JSON artifacts only.
- Create post-mortem.
- Return system to `DRY_RUN_ONLY`.
- Unset `PAPER_ORDER_EXECUTION_ENABLED`.

## 7. Failure Conditions

The run fails and must stop if any of these occur:

- Full tests fail.
- Architecture validation fails.
- Dry-run flow fails.
- Mocked paper send fails.
- Strategy Evaluation is not `PASS`.
- Evaluation gate is not `EVALUATION_GATE_PASSED`.
- Evaluation gate is missing before Human Approval.
- Evaluation gate is missing before Paper Order Request.
- Evaluation gate is missing before Paper Send.
- Risk Manager output is not `RISK_APPROVED`.
- Human Approval is missing or not `HUMAN_APPROVED_FOR_PAPER_ONLY`.
- Manual Execution Confirmation is missing or not `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY`.
- Journal commit is missing before send.
- Preflight is not `PAPER_ORDER_SEND_ALLOWED`.
- Paper account mode is not confirmed.
- ADLC compliance is not `PASS`.
- Any live endpoint is configured.
- Any order constraint is violated.
- Any secret is printed or written to an artifact.

If a failure occurs before send, no order may be sent.

## 8. Stop Conditions

Stop immediately if:

- Any gate fails.
- Evaluation gate blocks.
- Any live trading assumption appears.
- Alpaca account mode is not paper.
- Live endpoint is detected.
- More than one order would be sent.
- Order notional exceeds `100 USD`.
- Order type is not limit.
- Time in force is not day.
- Short selling, crypto, options, margin/leverage, extended hours, batch orders, or cancel/replace appear.
- Required JSON artifacts are missing.
- Reconciliation cannot run.
- Secrets may have been exposed.

## 9. Success Criteria

The regression passes only if:

- Full tests pass.
- Architecture validation passes.
- Dry-run flow passes.
- Mocked paper send passes.
- Strategy Evaluation returns `PASS`.
- Evaluation gate returns `EVALUATION_GATE_PASSED`.
- Human Approval occurs only after the gate passes.
- Paper Order Request is created only after the gate passes.
- Paper Send occurs only after the gate passes.
- At most one Alpaca paper order is submitted.
- Execution result is recorded.
- Post-send journal entry exists.
- Reconciliation runs and records a final status.
- Post-mortem is created.
- System returns to `DRY_RUN_ONLY`.
- `PAPER_ORDER_EXECUTION_ENABLED` is unset after the run.
- No live trading, live endpoints, automation, batch orders, cancel/replace, credentials, `.env` file creation, or LLM calls occur.

## 10. What Remains Prohibited

The following remain prohibited:

- Live trading.
- Live endpoints.
- Increasing notional.
- Automation.
- Batch orders.
- Cancel/replace.
- Higher frequency.
- Market orders.
- Short selling.
- Crypto.
- Options.
- Margin or leverage.
- Extended-hours trading.
- Autonomous follow-up trades.
- Bypassing Strategy Evaluation.
- Bypassing Evaluation-First Gate.
- Bypassing Risk Manager.
- Bypassing Human Approval.
- Bypassing Manual Execution Confirmation.
- Bypassing Journal Agent.
- Bypassing Execution Gatekeeper.
- Committing credentials.
- Creating `.env` files with real values.
- LLM API calls.

## 11. Live Trading Remains Unsupported

Live trading remains unsupported.

Phase 16 is a paper-only regression plan for verifying the Evaluation-First Gate before one controlled Alpaca paper send. It does not authorize live trading, live endpoints, automation, increased notional, batch orders, cancel/replace, or higher frequency.
