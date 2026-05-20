# Phase 23 Negative Case Regression Design

## 1. Purpose

Phase 23 defines how the Phase 22 negative-case dataset is tested against the Strategy Evaluation Harness and the Evaluation-First Gate.

The purpose is to prove, offline and deterministically, that rejected trades, no-trade decisions, weak setups, rubber-stamped approvals, journal failures, evidence failures, and live-trading assumptions do not pass into approval or paper request readiness.

This phase is design only. It does not send orders, create paper order requests, approve trades, modify execution logic, modify risk limits, increase notional, add automation, create `.env` files, print secrets, use Alpaca, or authorize live trading.

## 2. Why This Phase Follows Phase 22

Phase 22 created the offline negative-case dataset and summary report. Phase 23 defines the regression process that uses that dataset to test selectivity behavior.

The Phase 22 dataset is not useful unless the system can repeatedly prove that negative cases are recognized and blocked. This phase turns the dataset into a regression standard for approval bias, no-trade discipline, weak setup rejection, rubber-stamping detection, and journal/evidence quality.

## 3. Inputs

Required inputs:

- `evaluation/negative_cases/negative_case_dataset.json`
- `reports/negative_case_dataset/NEGATIVE_CASE_DATASET_SUMMARY.md`
- Strategy Evaluation Harness
- Evaluation-First Gate

Inputs must remain local and offline. No Alpaca API, broker calls, LLM calls, credentials, or `.env` files are required or allowed.

## 4. Outputs

Required output:

- `reports/negative_case_regression/<timestamp>/NEGATIVE_CASE_REGRESSION_REPORT.md`

The regression output must be a local report only. It must not create paper order requests, execution artifacts, broker requests, account snapshots, or approval artifacts.

## 5. Regression Flow

The regression flow must be deterministic:

1. Load the Phase 22 negative-case dataset.
2. Validate the dataset schema and category coverage.
3. For every negative case, construct an offline evaluation fixture from the case fields.
4. Run the fixture through the Strategy Evaluation Harness.
5. Run the fixture through the Evaluation-First Gate.
6. Compare the actual evaluation result and gate result against the case's `expected_decision` and `expected_gate_status`.
7. Record whether the case was blocked before human approval.
8. Record whether the case could reach paper request readiness.
9. Record whether the case could reach broker execution readiness.
10. Generate the regression report.

Every negative case must be evaluated. Every negative case must produce a deterministic evaluation result. Every negative case must produce a gate result.

## 6. Expected Outcomes

Required behavior:

- Cases labeled `REJECT` must not pass the gate.
- Cases labeled `NO_TRADE` must be recognized as no-trade.
- Cases labeled `BLOCK_EVALUATION_GATE` must be blocked by the Evaluation-First Gate.
- Cases labeled `BLOCK_HUMAN_APPROVAL` must not reach human approval.
- Cases labeled `BLOCK_PAPER_REQUEST` must not create a paper request.
- No negative case may produce paper send readiness.
- No negative case may produce broker execution readiness.

The correct default outcome for uncertain or incomplete evidence remains no-trade.

## 7. Pass/Fail Criteria

The regression passes only if:

- Every negative case is evaluated.
- Every negative case produces an evaluation result.
- Every negative case produces a gate result.
- No negative case produces paper send readiness.
- No negative case produces broker execution readiness.
- Required blocked outcome rate is met.
- Required no-trade recognition rate is met.
- Required weak setup rejection rate is met.
- Required rubber-stamping detection rate is met.
- Required journal/evidence failure detection rate is met.
- All live trading assumption cases are blocked.
- No recommendation suggests increasing notional or automation.

The regression fails if any negative case bypasses the expected block into paper request readiness or broker execution readiness.

## 8. Required Blocked Outcome Rate

At least 90% of all negative cases must be blocked before human approval.

The blocked-before-human-approval count includes cases with expected decisions:

- `REJECT`
- `NO_TRADE`
- `BLOCK_EVALUATION_GATE`

Cases expected to block at human approval or paper request must still be recorded as blocked outcomes, but they must not be used to hide a weak Evaluation-First Gate.

## 9. Required NO_TRADE Recognition Rate

At least 90% of cases labeled `NO_TRADE` must be recognized correctly as no-trade.

Recognition requires:

- The Strategy Evaluation Harness identifies no-trade as correct.
- The Evaluation-First Gate does not convert the no-trade case into approval readiness.
- No paper request is created.
- No broker execution readiness is produced.

## 10. Required Weak Setup Rejection Rate

At least 90% of weak setup rejection cases must be rejected correctly.

Weak setup rejection includes cases where the expected decision is `REJECT` and the case category involves weak context, weak liquidity, vague confirmation, generic thesis, missing invalidation, forced trade behavior, excessive confidence, or risk-valid-but-weak setup quality.

## 11. Required Rubber-Stamping Detection Rate

100% of rubber-stamping cases must be detected or blocked.

Rubber-stamping cases include:

- Specialist agent rubber-stamping
- Human approval rubber-stamping
- Risk approval without meaningful challenge
- Proposal upgrade from shallow agreement
- Paper request attempt after rubber-stamped approval

Any rubber-stamping case that reaches paper send readiness is a regression failure.

## 12. Required Journal/Evidence Failure Detection Rate

100% of missing journal readiness cases must be blocked.

Journal/evidence failure cases include:

- Journal too weak
- Missing credible invalidation
- Data integrity incomplete
- ADLC compliance incomplete
- Evaluation score inflation
- Missing fixed risk
- Missing journal readiness

Any journal or evidence failure case that passes the gate is a regression failure.

## 13. Required Report Format

The regression report must be written to:

`reports/negative_case_regression/<timestamp>/NEGATIVE_CASE_REGRESSION_REPORT.md`

The report must include:

- Total cases
- Passed regression cases
- Failed regression cases
- Blocked before human approval count
- `NO_TRADE` recognized count
- Weak setup rejected count
- Rubber-stamping detected count
- Journal/evidence failure detected count
- Live trading assumption blocked count
- Missed blocks
- False passes
- Recommendation: `HOLD`, `IMPROVE_GATE`, or `CONTINUE_MANUAL_LIMITED_PAPER`
- Statement: `Live trading remains unsupported.`
- Statement: `Increasing notional remains prohibited.`
- Statement: `Automation remains prohibited.`

The report must not include secrets, credentials, broker responses, account identifiers, paper order identifiers from new activity, or live trading assumptions as acceptable outcomes.

## 14. Required Tests

Implementation must add offline tests proving:

- The regression loads every Phase 22 negative case.
- Every case produces a deterministic evaluation result.
- Every case produces a gate result.
- `REJECT` cases do not pass the gate.
- `NO_TRADE` cases are recognized as no-trade.
- `BLOCK_EVALUATION_GATE` cases are blocked by the gate.
- `BLOCK_HUMAN_APPROVAL` cases do not reach human approval.
- `BLOCK_PAPER_REQUEST` cases do not create paper requests.
- No negative case produces paper send readiness.
- No negative case produces broker execution readiness.
- 100% of live trading assumption cases are blocked.
- 100% of missing fixed risk cases are blocked.
- 100% of missing journal readiness cases are blocked.
- 100% of rubber-stamping cases are detected or blocked.
- At least 90% of all negative cases are blocked before human approval.
- At least 90% of `NO_TRADE` cases are recognized correctly.
- At least 90% of weak setup rejection cases are rejected correctly.
- The report includes all required counts and safety statements.
- The recommendation is `HOLD` if any live trading assumption case passes.
- The recommendation is `HOLD` if any missing fixed risk case passes.
- The recommendation is `IMPROVE_GATE` if blocked-before-human-approval rate is below 90%.
- The recommendation is `IMPROVE_GATE` if `NO_TRADE` recognition is below 90%.
- The recommendation is `IMPROVE_GATE` if weak setup rejection is below 90%.
- No test uses Alpaca API.
- No test sends orders.
- No test enables `PAPER_ORDER_EXECUTION_ENABLED`.
- No test creates `.env` files.
- No test uses LLM API calls.

## 15. What Remains Prohibited

The following remain prohibited:

- Sending orders.
- Creating paper order requests.
- Approving trades from negative cases.
- Enabling `PAPER_ORDER_EXECUTION_ENABLED`.
- Using Alpaca API.
- Calling any broker API.
- Modifying execution logic.
- Modifying risk limits.
- Increasing notional.
- Adding automation.
- Creating `.env` files.
- Printing secrets.
- Adding LLM calls.
- Recommending increasing notional.
- Recommending automation.
- Recommending live trading.
- Producing paper send readiness from any negative case.
- Producing broker execution readiness from any negative case.

## 16. Conditions Before Implementation

Implementation may begin only after this design is accepted and the scope remains offline.

Before implementation:

- The Phase 22 dataset validator must pass.
- The Phase 22 summary report must exist.
- The regression must be wired only to local deterministic fixtures.
- Strategy Evaluation Harness use must not import or call Alpaca.
- Evaluation-First Gate use must not create approval, paper request, or execution artifacts.
- Report generation must write only local markdown artifacts.
- Tests must prove no order path, broker path, LLM path, or `.env` creation is invoked.

Implementation must stop if satisfying the regression requires execution changes, risk limit changes, automation, Alpaca access, secrets, LLM calls, or order creation.

## 17. Explicit Live Trading Boundary

Live trading remains unsupported.

This phase does not design, imply, prepare, or authorize live trading. Any live trading assumption case must be blocked. If any live trading assumption case passes, the regression recommendation must be `HOLD`.

## Recommendation Rules

The regression recommendation must follow these rules:

- If any live trading assumption case passes, recommendation must be `HOLD`.
- If any missing fixed risk case passes, recommendation must be `HOLD`.
- If blocked-before-human-approval rate is below 90%, recommendation must be `IMPROVE_GATE`.
- If `NO_TRADE` recognition is below 90%, recommendation must be `IMPROVE_GATE`.
- If weak setup rejection is below 90%, recommendation must be `IMPROVE_GATE`.
- If all required thresholds pass and no hard-fail condition is present, recommendation may be `CONTINUE_MANUAL_LIMITED_PAPER`.
- The recommendation must not suggest increasing notional.
- The recommendation must not suggest automation.

## Offline Safety Statement

Phase 23 is an offline regression design phase only.

No order is authorized by this design. No paper order request is authorized by this design. No approval is authorized by this design. No execution runtime change is authorized by this design. No notional increase is authorized by this design. No automation is authorized by this design. Alpaca remains untouched.
