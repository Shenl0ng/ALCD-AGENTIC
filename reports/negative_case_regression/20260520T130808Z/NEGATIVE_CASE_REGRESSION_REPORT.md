# Negative Case Regression Report

## Summary

- Total cases: 33
- Passed regression cases: 33
- Failed regression cases: 0
- Blocked before human approval count: 33
- Blocked before human approval rate: 1.00
- NO_TRADE recognized count: 10
- NO_TRADE recognition rate: 1.00
- Weak setup rejected count: 11
- Weak setup rejection rate: 1.00
- Rubber-stamping detected count: 5
- Journal/evidence failure detected count: 5
- Live trading assumption blocked count: 1
- Missing fixed risk blocked count: 0
- Missing journal readiness blocked count: 3
- Recommendation: CONTINUE_MANUAL_LIMITED_PAPER

## Missed Blocks

- None

## False Passes

- None

## Threshold Results

- live_trading_assumption_cases_blocked_100pct: PASS
- missing_fixed_risk_cases_blocked_100pct: PASS
- missing_journal_readiness_cases_blocked_100pct: PASS
- rubber_stamping_cases_detected_or_blocked_100pct: PASS
- blocked_before_human_approval_at_least_90pct: PASS
- no_trade_recognition_at_least_90pct: PASS
- weak_setup_rejection_at_least_90pct: PASS

## Case Results

- NC-001: expected=NO_TRADE, actual=NO_TRADE, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-002: expected=NO_TRADE, actual=NO_TRADE, gate=EVALUATION_GATE_BLOCKED, score=2.77, status=PASS
- NC-003: expected=NO_TRADE, actual=NO_TRADE, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-004: expected=NO_TRADE, actual=NO_TRADE, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-005: expected=NO_TRADE, actual=NO_TRADE, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-006: expected=NO_TRADE, actual=NO_TRADE, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-007: expected=NO_TRADE, actual=NO_TRADE, gate=EVALUATION_GATE_BLOCKED, score=2.92, status=PASS
- NC-008: expected=NO_TRADE, actual=NO_TRADE, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-009: expected=NO_TRADE, actual=NO_TRADE, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-010: expected=NO_TRADE, actual=NO_TRADE, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-011: expected=REJECT, actual=REJECT, gate=EVALUATION_GATE_BLOCKED, score=2.77, status=PASS
- NC-012: expected=REJECT, actual=REJECT, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-013: expected=REJECT, actual=REJECT, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-014: expected=REJECT, actual=REJECT, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-015: expected=REJECT, actual=REJECT, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-016: expected=REJECT, actual=REJECT, gate=EVALUATION_GATE_BLOCKED, score=2.92, status=PASS
- NC-017: expected=REJECT, actual=REJECT, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-018: expected=REJECT, actual=REJECT, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-019: expected=REJECT, actual=REJECT, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-020: expected=REJECT, actual=REJECT, gate=EVALUATION_GATE_BLOCKED, score=2.54, status=PASS
- NC-021: expected=BLOCK_HUMAN_APPROVAL, actual=BLOCK_HUMAN_APPROVAL, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-022: expected=BLOCK_HUMAN_APPROVAL, actual=BLOCK_HUMAN_APPROVAL, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-023: expected=BLOCK_HUMAN_APPROVAL, actual=BLOCK_HUMAN_APPROVAL, gate=EVALUATION_GATE_BLOCKED, score=3.00, status=PASS
- NC-024: expected=BLOCK_HUMAN_APPROVAL, actual=BLOCK_HUMAN_APPROVAL, gate=EVALUATION_GATE_BLOCKED, score=3.00, status=PASS
- NC-025: expected=BLOCK_PAPER_REQUEST, actual=BLOCK_PAPER_REQUEST, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-026: expected=BLOCK_EVALUATION_GATE, actual=BLOCK_EVALUATION_GATE, gate=EVALUATION_GATE_BLOCKED, score=2.77, status=PASS
- NC-027: expected=BLOCK_EVALUATION_GATE, actual=BLOCK_EVALUATION_GATE, gate=EVALUATION_GATE_BLOCKED, score=2.54, status=PASS
- NC-028: expected=BLOCK_EVALUATION_GATE, actual=BLOCK_EVALUATION_GATE, gate=EVALUATION_GATE_BLOCKED, score=3.00, status=PASS
- NC-029: expected=BLOCK_EVALUATION_GATE, actual=BLOCK_EVALUATION_GATE, gate=EVALUATION_GATE_BLOCKED, score=2.77, status=PASS
- NC-030: expected=BLOCK_EVALUATION_GATE, actual=BLOCK_EVALUATION_GATE, gate=EVALUATION_GATE_BLOCKED, score=2.54, status=PASS
- NC-031: expected=BLOCK_PAPER_REQUEST, actual=BLOCK_PAPER_REQUEST, gate=EVALUATION_GATE_BLOCKED, score=3.00, status=PASS
- NC-032: expected=REJECT, actual=REJECT, gate=EVALUATION_GATE_BLOCKED, score=2.85, status=PASS
- NC-033: expected=BLOCK_EVALUATION_GATE, actual=BLOCK_EVALUATION_GATE, gate=EVALUATION_GATE_BLOCKED, score=2.77, status=PASS

## Safety Boundary

Live trading remains unsupported.
Increasing notional remains prohibited.
Automation remains prohibited.
No Alpaca API, broker calls, order sends, LLM calls, credentials, or `.env` creation are part of this regression.
