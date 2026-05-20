# Phase 14 Evaluation-First Gate Design

## 1. Purpose

Phase 14 defines the Evaluation-First Gate.

The gate makes the Phase 13 Strategy Evaluation Harness a required control before any future proposal may advance to human approval, paper order request creation, or paper send.

This is a design phase only. It does not send orders, enable `PAPER_ORDER_EXECUTION_ENABLED`, call Alpaca, modify execution logic, increase notional limits, add automation, create `.env` files, or authorize live trading.

## 2. Why This Gate Is Needed After Phase 13

Phase 13 implemented deterministic scoring for proposal quality, no-trade quality, rejection quality, journal quality, ADLC compliance, and data integrity.

The next control risk is sequencing. If evaluation remains optional or advisory, a weak proposal could still reach human approval or paper-order preparation before the system has formally scored it.

Phase 14 closes that gap by placing the evaluation result before approval and execution gates. Evaluation must become a blocking prerequisite, not a post-hoc review.

## 3. Where The Gate Sits In The Flow

The Evaluation-First Gate sits after specialist-agent outputs and Risk Manager evaluation, and before human approval.

Required flow:

1. Orchestrator starts a candidate review.
2. Data Integrity Agent verifies data freshness and completeness.
3. Market Context Agent evaluates higher-timeframe context.
4. Liquidity Agent evaluates liquidity location.
5. Session Timing Agent evaluates session or timing window.
6. Confirmation Agent evaluates entry confirmation.
7. Trade Proposal Agent creates a proposal only if prior agents allow it.
8. Risk Manager produces a deterministic risk decision.
9. Strategy Evaluation Harness scores the proposal, rejection, or no-trade decision.
10. Evaluation-First Gate blocks or allows advancement.
11. Human Approval may occur only after the Evaluation-First Gate passes.
12. Journal Agent records the evaluation result and gate decision.
13. Execution Gatekeeper may review a paper order request only after all prior controls pass.

A proposal may not enter human approval unless:

- Strategy Evaluation status is `PASS`.
- No hard-fail condition exists.
- No live trading assumption exists.
- No specialist-agent sequencing violation exists.
- No missing fixed risk exists.
- No missing journal readiness exists.
- No missing data integrity exists.

## 4. Required Inputs

The gate requires:

- Trade proposal record.
- Strategy Evaluation Harness report.
- Dimension scores.
- Rejection reasons.
- Improvement recommendations.
- ADLC compliance status.
- No-trade discipline status.
- Data Integrity Agent output.
- Specialist-agent outputs.
- Risk Manager output.
- Journal readiness signal.
- Proposal validation result.
- Evidence that the proposal remains paper-trading only.

The gate must not read broker account state, call Alpaca, submit orders, cancel orders, replace orders, or inspect live endpoints.

## 5. Required Outputs

The gate must produce:

- Evaluation gate decision: `EVALUATION_GATE_PASSED` or `EVALUATION_GATE_BLOCKED`.
- Strategy evaluation status reference.
- Evaluation score.
- Required dimension scores.
- Hard-fail condition list.
- Block reasons when blocked.
- Required follow-up journal entry reference.
- Report artifact reference.
- ADLC compliance reference.
- Explicit statement that no execution action was taken.

## 6. Minimum Scoring Thresholds

Minimum thresholds before a proposal may advance:

- Final Strategy Evaluation status: `PASS`.
- Overall evaluation score: at least `2.0`.
- Higher-timeframe context quality: at least `2`.
- Liquidity location quality: at least `2`.
- Session/timing quality: at least `2`.
- Entry confirmation quality: at least `2`.
- Fixed risk quality: exactly `3` is required for proposals that may advance.
- Reward/risk quality: at least `2`.
- Journal readiness: exactly `3` is required for proposals that may advance.
- Data freshness: `3`.
- Data completeness: `3`.
- Specialist-agent sequencing: `3`.
- Risk Manager decision quality: at least `2`.
- ADLC compliance status: `PASS`.

No-trade and rejection records may pass evaluation as high-quality decisions, but they must not advance to human approval for paper send. They are journaled as correct waiting or correct rejection outcomes.

## 7. Hard-Fail Conditions

Any hard-fail condition blocks advancement to human approval, paper order request creation, and paper send.

Hard-fail conditions include:

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
- Missing Risk Manager output.
- Risk Manager rejection for a proposed send.
- ADLC compliance failure.
- Any assumption of increased notional.
- Any assumption of automation.
- Any assumption of batch orders.
- Any assumption of cancel/replace.
- Any assumption of live endpoints.

## 8. Required Journal Entries

The Journal Agent must record:

- Evaluation attempted.
- Evaluation report reference.
- Evaluation score.
- Dimension scores summary.
- Gate decision.
- Hard-fail conditions, if any.
- Block reasons, if any.
- Whether the decision was a proposal, rejection, or no-trade outcome.
- Confirmation that no order action was taken by the evaluation gate.
- Confirmation that live trading remains unsupported.

When evaluation fails, the journal entry must clearly state that the proposal did not advance to human approval.

When evaluation passes, the journal entry must clearly state that the proposal may advance only to human approval review, not execution.

## 9. Required Report Artifacts

Phase 14 implementation must produce report artifacts that can be audited before any downstream approval:

- Strategy evaluation report JSON.
- Evaluation gate decision JSON.
- Journal entry JSON or journal reference.
- ADLC compliance reference.
- Data Integrity Agent reference.
- Risk Manager reference.
- Specialist-agent output references.
- Human-readable evaluation gate summary.

Missing report artifacts must block advancement.

## 10. Interaction With Risk Manager

The Risk Manager remains mandatory.

The Evaluation-First Gate does not replace Risk Manager approval. It consumes the Risk Manager output and scores the quality of the risk decision.

Rules:

- Missing Risk Manager output blocks the gate.
- `RISK_REJECTED` blocks a proposal from entering human approval for paper send.
- `RISK_APPROVED` is necessary but not sufficient.
- The gate may still block a risk-approved proposal if strategy quality, data quality, journal readiness, fixed risk, specialist sequencing, or ADLC compliance fails.

## 11. Interaction With Human Approval

Human approval may occur only after the Evaluation-First Gate passes.

Rules:

- Human Approval must not be requested for a blocked proposal.
- Human Approval must receive the evaluation report and gate decision.
- Human Approval must not override hard-fail conditions.
- Human Approval must remain `HUMAN_APPROVED_FOR_PAPER_ONLY` for any later paper-send path.
- Passing evaluation does not imply human approval.

## 12. Interaction With Execution Gatekeeper

The Execution Gatekeeper remains mandatory and downstream.

Rules:

- The Execution Gatekeeper must require a passed Evaluation-First Gate reference.
- A missing evaluation gate reference blocks paper order request creation.
- A blocked evaluation gate decision blocks paper order request creation.
- The Execution Gatekeeper still enforces paper-only mode, manual execution confirmation, journal commit, preflight, ADLC compliance, expiration, request status, one-order-per-run, max notional, limit/day only, and all Phase 9 safety constraints.

The Evaluation-First Gate must never submit orders or prepare broker requests.

## 13. Interaction With ADLC Compliance

ADLC compliance remains a required control.

The Evaluation-First Gate must verify:

- Scope and constraints are respected.
- Agent role separation is preserved.
- Autonomy boundaries are preserved.
- Failure modes are visible.
- Evaluation artifacts exist.
- Paper-only boundary is explicit.
- No implementation leap occurs without design approval.

Any ADLC compliance failure blocks advancement.

## 14. What Happens When Evaluation Fails

When evaluation fails:

- The proposal is blocked.
- Human approval is not requested.
- No paper order request is created.
- No paper send is allowed.
- No broker request is constructed.
- The failure is journaled.
- The evaluation report is preserved.
- Improvement recommendations are recorded.
- Default outcome remains no trade.

Evaluation failure is not treated as a system failure when the system correctly rejects weak setups. Correct rejection and waiting remain positive outcomes.

## 15. What Happens When Evaluation Passes

When evaluation passes:

- The proposal may advance to human approval review only.
- The evaluation report and gate decision must travel with the proposal.
- Human approval may still reject the proposal.
- Risk Manager controls remain in force.
- Journal readiness remains mandatory.
- Execution Gatekeeper controls remain in force.
- Paper send remains disabled by default.

Passing evaluation does not authorize execution, automation, increased notional, batch orders, cancel/replace, market orders, or live trading.

## 16. Required Tests Before Implementation

Implementation must include deterministic tests proving:

- A proposal cannot enter human approval without a Strategy Evaluation report.
- A non-`PASS` Strategy Evaluation status blocks human approval.
- A hard-fail condition blocks human approval.
- Live trading assumption blocks the gate.
- Missing fixed risk blocks the gate.
- Missing journal readiness blocks the gate.
- Bypassed specialist agents block the gate.
- Missing data integrity blocks the gate.
- Forced trade behavior blocks the gate.
- Vague confirmation blocks the gate.
- Weak or missing liquidity location blocks the gate.
- Missing higher-timeframe context blocks the gate.
- Excessive confidence without evidence blocks the gate.
- Passing evaluation allows only advancement to human approval review.
- Passing evaluation does not create a paper order request.
- Passing evaluation does not send an order.
- Passing evaluation does not enable `PAPER_ORDER_EXECUTION_ENABLED`.
- Risk Manager rejection still blocks even if other scores are acceptable.
- Missing ADLC compliance blocks the gate.
- Journal entry is written for pass and fail outcomes.
- Report artifacts are generated.
- No Alpaca API calls occur.
- No broker calls occur.
- No live endpoints are used.
- No automation is added.
- No batch order behavior exists.
- No cancel/replace behavior exists.

## 17. What Remains Prohibited

The following remain prohibited:

- Live trading.
- Live endpoints.
- Increasing notional.
- Automation.
- Batch orders.
- Cancel/replace.
- Higher frequency execution.
- Market orders.
- Short selling.
- Crypto.
- Options.
- Margin or leverage.
- Extended-hours trading.
- Autonomous follow-up trades.
- Bypassing Risk Manager.
- Bypassing Human Approval.
- Bypassing Manual Execution Confirmation.
- Bypassing Journal Agent.
- Bypassing Execution Gatekeeper.
- Creating `.env` files with real values.
- Committing credentials.

This design does not recommend increasing notional, automation, live trading, batch orders, cancel/replace, or higher frequency.

## 18. Live Trading Remains Unsupported

Live trading remains unsupported.

Phase 14 only designs an evaluation-first control before human approval and paper-order progression. It does not authorize live trading, live endpoints, automation, higher notional, batch orders, cancel/replace, or higher frequency.
