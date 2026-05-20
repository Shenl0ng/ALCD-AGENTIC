# Baseline Selective Evaluation V3

## 1. Baseline Name

Baseline Selective Evaluation V3.

## 2. Date

2026-05-20.

## 3. Difference From V1 And V2

V1 established the first safe controlled Alpaca paper execution baseline.

V2 added the Evaluation-First Gate as a mandatory control before Human Approval, Paper Order Request creation, and Paper Send.

V3 adds offline negative-case selectivity proof. It verifies that rejected trades, no-trade decisions, weak setups, rubber-stamped approvals, journal failures, evidence failures, and live-trading assumptions are evaluated offline and blocked before they can become approval or execution readiness.

V3 does not expand execution authority. It does not increase notional. It does not add automation. It does not authorize higher frequency.

## 4. Completed Gates

Completed gates through V3:

- Phase 21 Negative Case Dataset Design: `PASS`.
- Phase 22 Negative Case Dataset Implementation: `PASS`.
- Phase 23 Negative Case Regression Design: `PASS`.
- Phase 24 Negative Case Regression Implementation: `PASS`.
- Negative-case dataset validation: `PASS`.
- Negative-case regression: `PASS`.
- Regression recommendation: `CONTINUE_MANUAL_LIMITED_PAPER`.

## 5. Baseline V2 Reference

Baseline V2 reference:

- `docs/BASELINE_SAFE_PAPER_EXECUTION_V2.md`

V3 preserves V2 safety controls and adds negative-case regression as an offline selectivity control.

## 6. Phase 21 Negative Case Dataset Design Result

Phase 21 design result: `PASS`.

Design file:

- `design/06_NEGATIVE_CASE_DATASET_EXPANSION.md`

Phase 21 defined the offline negative-case dataset requirements for rejected trades, no-trade decisions, weak setups, blocked approvals, rubber-stamping, journal failures, evidence failures, and live-trading assumptions.

## 7. Phase 22 Negative Case Dataset Implementation Result

Phase 22 implementation result: `PASS`.

Dataset file:

- `evaluation/negative_cases/negative_case_dataset.json`

Dataset summary:

- `reports/negative_case_dataset/NEGATIVE_CASE_DATASET_SUMMARY.md`

Phase 22 created 33 offline negative cases and validated that all required categories, expected decisions, prohibited outcomes, and safety statements are present.

## 8. Phase 23 Negative Case Regression Design Result

Phase 23 design result: `PASS`.

Design file:

- `design/07_NEGATIVE_CASE_REGRESSION.md`

Phase 23 defined how the Phase 22 negative-case dataset must be tested against the Strategy Evaluation Harness and Evaluation-First Gate.

## 9. Phase 24 Negative Case Regression Implementation Result

Phase 24 implementation result: `PASS`.

Regression runner:

- `runtime/negative_case_regression.py`

Regression tests:

- `tests/test_negative_case_regression.py`

Regression report:

- `reports/negative_case_regression/20260520T014526Z/NEGATIVE_CASE_REGRESSION_REPORT.md`

Phase 24 produced recommendation: `CONTINUE_MANUAL_LIMITED_PAPER`.

## 10. What Phase 24 Proved

Phase 24 proved:

- Every negative case was evaluated.
- Every negative case produced a deterministic evaluation result.
- Every negative case produced a gate result.
- `REJECT` cases did not pass the gate.
- `NO_TRADE` cases were recognized.
- `BLOCK_EVALUATION_GATE` cases were blocked by the Evaluation-First Gate.
- `BLOCK_HUMAN_APPROVAL` cases did not reach human approval.
- `BLOCK_PAPER_REQUEST` cases did not create paper requests.
- No negative case produced paper send readiness.
- No negative case produced broker execution readiness.
- Live trading assumption cases were blocked.
- Rubber-stamping cases were detected or blocked.
- Journal/evidence failure cases were detected or blocked.

The system must prove it can say NO before allowing more paper frequency.

## 11. Negative-Case Dataset Summary

Dataset status: `PASS`.

Dataset size:

- Total cases: 33.

Expected decision counts:

- `BLOCK_EVALUATION_GATE`: 6.
- `BLOCK_HUMAN_APPROVAL`: 4.
- `BLOCK_PAPER_REQUEST`: 2.
- `NO_TRADE`: 10.
- `REJECT`: 11.

Required case counts:

- `NO_TRADE` case count: 10.
- Weak setup rejection count: 11.
- Rubber-stamping case count: 5.
- Journal/evidence failure count: 5.

Negative cases are evaluated offline only.

## 12. Negative-Case Regression Summary

Regression status: `PASS`.

Regression summary:

- Total cases: 33.
- Passed regression cases: 33.
- Failed regression cases: 0.
- Blocked before human approval count: 33.
- Blocked before human approval rate: 1.00.
- `NO_TRADE` recognized count: 10.
- `NO_TRADE` recognition rate: 1.00.
- Weak setup rejected count: 11.
- Weak setup rejection rate: 1.00.
- Rubber-stamping detected count: 5.
- Journal/evidence failure detected count: 5.
- Live trading assumption blocked count: 1.
- Missing journal readiness blocked count: 3.
- Missed blocks: none.
- False passes: none.
- Recommendation: `CONTINUE_MANUAL_LIMITED_PAPER`.

Negative cases cannot create paper order requests. Negative cases cannot reach human approval when blocked. Negative cases cannot create paper send readiness. Negative cases cannot create broker execution readiness.

## 13. Confirmed Safety Controls

Confirmed safety controls:

- Paper trading only.
- Live trading unsupported.
- Negative cases are offline only.
- Negative cases cannot create paper order requests.
- Negative cases cannot reach human approval when blocked.
- Negative cases cannot create paper send readiness.
- Negative cases cannot create broker execution readiness.
- Strategy Evaluation Harness required.
- Evaluation-First Gate required.
- Evaluation-First Gate cannot be bypassed.
- No broker execution from negative cases.
- No Alpaca API use in negative-case regression.
- No order sends from negative-case regression.
- No automation added.
- No LLM calls added.
- No credentials added.
- No `.env` files created.
- Increasing notional remains prohibited.
- Automation remains prohibited.

## 14. What Is Allowed After V3

After V3, the system may:

- Continue manual limited paper only if current gates pass.
- Continue offline strategy quality work.
- Continue expanding negative-case coverage.
- Continue improving rejection quality.
- Continue improving no-trade quality.
- Continue running deterministic offline tests.
- Continue running negative-case regression before future controlled paper decisions.

## 15. What Remains Prohibited

The following remain prohibited after V3:

- Increasing notional.
- Automation.
- Live trading.
- Batch orders.
- Cancel/replace.
- Higher frequency.
- Broker execution from negative cases.
- Any bypass of the Evaluation-First Gate.
- Paper order requests from negative cases.
- Paper send readiness from negative cases.
- Broker execution readiness from negative cases.
- Live endpoints.
- Market orders.
- Short selling.
- Crypto.
- Options.
- Margin or leverage.
- Extended-hours trading.
- Autonomous follow-up trades.
- Creating `.env` files with secrets.
- Printing secrets.
- LLM API calls.

## 16. Conditions Before Another Paper Send

Before another paper send:

- Review Baseline V2.
- Review this V3 baseline.
- Confirm the Phase 22 dataset validator passes.
- Confirm the Phase 24 negative-case regression passes.
- Confirm the latest negative-case regression report has no missed blocks.
- Confirm the latest negative-case regression report has no false passes.
- Confirm Strategy Evaluation status is `PASS` for the proposed trade.
- Confirm Evaluation-First Gate status is `EVALUATION_GATE_PASSED` for the proposed trade.
- Confirm Risk Manager output is `RISK_APPROVED`.
- Confirm Human Approval is independent and not rubber-stamped.
- Confirm journal readiness before any send.
- Confirm manual execution confirmation before any send.
- Confirm `PAPER_ORDER_EXECUTION_ENABLED` remains unset or false until a manual controlled send window.
- Confirm the system starts from `DRY_RUN_ONLY`.
- Confirm the system returns to `DRY_RUN_ONLY`.

Another paper send is not allowed from negative-case artifacts.

## 17. Conditions Before Increasing Notional

Increasing notional is not approved by V3.

Before any notional increase:

- A future design phase must explicitly justify the change.
- Offline review must show approval bias is resolved.
- Negative-case regression must continue to pass.
- Rejection/no-trade quality must improve.
- Risk governance must be updated.
- Deterministic tests must prove the new cap is enforced.
- Human accountability must remain mandatory.

V3 does not recommend increasing notional.

## 18. Conditions Before Automation

Automation is not approved by V3.

Before any automation:

- A future design phase must explicitly justify the change.
- Offline review must show no approval-bias red flag.
- Negative-case regression must continue to pass.
- No-trade recognition must remain strong.
- Weak setup rejection must remain strong.
- Rubber-stamping detection must remain strong.
- Journal/evidence failure detection must remain strong.
- Human accountability requirements must be redesigned and approved.

V3 does not recommend automation.

## 19. Explicit Live Trading Boundary

Live trading remains unsupported.

V3 does not design, imply, prepare, or authorize live trading. Any live trading assumption remains a blocking failure.

## Offline Safety Statement

Baseline Selective Evaluation V3 is an offline selectivity baseline.

No order was sent by this baseline. No code was changed by this baseline. No execution logic was changed by this baseline. No paper order request is authorized by this baseline. No notional increase is authorized by this baseline. No automation is authorized by this baseline. Alpaca remains untouched.
