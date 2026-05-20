# V10 Full Pipeline Dry-Run Regression Report

## Summary

- Final status: PASS
- Generated at: 2026-05-20T16:33:39Z
- Pipeline: Automated dry-run -> TRADE_PROPOSAL -> Paper Order Request Candidate -> Human Review Queue -> Finalized Paper Order Request -> Manual Execution Confirmation -> Paper Send Preflight -> stop

## Scenarios Run

- full_valid_v10_pipeline: PAPER_ORDER_SEND_ALLOWED (blocked_stage=none, passed=True)
- candidate_blocked: BLOCKED_BEFORE_REVIEW (blocked_stage=BLOCKED_BEFORE_REVIEW, passed=True)
- human_review_rejected: BLOCKED_BEFORE_FINALIZED_REQUEST (blocked_stage=BLOCKED_BEFORE_FINALIZED_REQUEST, passed=True)
- manual_confirmation_rejected: BLOCKED_BEFORE_PREFLIGHT_ALLOWED (blocked_stage=BLOCKED_BEFORE_PREFLIGHT_ALLOWED, passed=True)
- preflight_blocked: BLOCKED_AT_PREFLIGHT (blocked_stage=BLOCKED_AT_PREFLIGHT, passed=True)
- paper_order_execution_enabled_true: BLOCKED_BEFORE_PROGRESSION (blocked_stage=BLOCKED_BEFORE_PROGRESSION, passed=True)

## Scenario Results

```json
[
  {
    "scenario_id": "full_valid_v10_pipeline",
    "description": "Full valid V10 pipeline reaches Paper Send Preflight allowed.",
    "passed": true,
    "failure_reason": "",
    "blocked_stage": "none",
    "final_status": "PAPER_ORDER_SEND_ALLOWED",
    "dry_run_decision": "TRADE_PROPOSAL",
    "candidate_status": "PAPER_ORDER_CANDIDATE_CREATED",
    "review_status": "HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST",
    "finalized_request_status": "PAPER_ORDER_REQUEST_FINALIZED",
    "manual_confirmation_status": "MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT",
    "preflight_status": "PAPER_ORDER_SEND_ALLOWED",
    "artifacts_created": [
      "TRADE_PROPOSAL",
      "Paper Order Request Candidate",
      "Human Review Queue",
      "Finalized Paper Order Request",
      "Manual Execution Confirmation",
      "Paper Send Preflight"
    ],
    "order_sent": false,
    "alpaca_order_api_called": false,
    "broker_execution_readiness": false,
    "live_trading_readiness": false,
    "batch_behavior": false,
    "cancel_replace_behavior": false,
    "paper_order_execution_enabled_true": false
  },
  {
    "scenario_id": "candidate_blocked",
    "description": "Candidate blocked before human review.",
    "passed": true,
    "failure_reason": "",
    "blocked_stage": "BLOCKED_BEFORE_REVIEW",
    "final_status": "BLOCKED_BEFORE_REVIEW",
    "dry_run_decision": "NO_TRADE",
    "candidate_status": "PAPER_ORDER_CANDIDATE_BLOCKED",
    "review_status": null,
    "finalized_request_status": null,
    "manual_confirmation_status": null,
    "preflight_status": null,
    "artifacts_created": [],
    "order_sent": false,
    "alpaca_order_api_called": false,
    "broker_execution_readiness": false,
    "live_trading_readiness": false,
    "batch_behavior": false,
    "cancel_replace_behavior": false,
    "paper_order_execution_enabled_true": false
  },
  {
    "scenario_id": "human_review_rejected",
    "description": "Human review rejects a created candidate.",
    "passed": true,
    "failure_reason": "",
    "blocked_stage": "BLOCKED_BEFORE_FINALIZED_REQUEST",
    "final_status": "BLOCKED_BEFORE_FINALIZED_REQUEST",
    "dry_run_decision": "TRADE_PROPOSAL",
    "candidate_status": "PAPER_ORDER_CANDIDATE_CREATED",
    "review_status": "HUMAN_REVIEW_REJECTED",
    "finalized_request_status": null,
    "manual_confirmation_status": null,
    "preflight_status": null,
    "artifacts_created": [
      "TRADE_PROPOSAL",
      "Paper Order Request Candidate",
      "Human Review Queue"
    ],
    "order_sent": false,
    "alpaca_order_api_called": false,
    "broker_execution_readiness": false,
    "live_trading_readiness": false,
    "batch_behavior": false,
    "cancel_replace_behavior": false,
    "paper_order_execution_enabled_true": false
  },
  {
    "scenario_id": "manual_confirmation_rejected",
    "description": "Manual confirmation rejects a finalized request.",
    "passed": true,
    "failure_reason": "",
    "blocked_stage": "BLOCKED_BEFORE_PREFLIGHT_ALLOWED",
    "final_status": "BLOCKED_BEFORE_PREFLIGHT_ALLOWED",
    "dry_run_decision": "TRADE_PROPOSAL",
    "candidate_status": "PAPER_ORDER_CANDIDATE_CREATED",
    "review_status": "HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST",
    "finalized_request_status": "PAPER_ORDER_REQUEST_FINALIZED",
    "manual_confirmation_status": "MANUAL_EXECUTION_REJECTED",
    "preflight_status": null,
    "artifacts_created": [
      "TRADE_PROPOSAL",
      "Paper Order Request Candidate",
      "Human Review Queue",
      "Finalized Paper Order Request",
      "Manual Execution Confirmation"
    ],
    "order_sent": false,
    "alpaca_order_api_called": false,
    "broker_execution_readiness": false,
    "live_trading_readiness": false,
    "batch_behavior": false,
    "cancel_replace_behavior": false,
    "paper_order_execution_enabled_true": false
  },
  {
    "scenario_id": "preflight_blocked",
    "description": "Preflight blocks before any send path.",
    "passed": true,
    "failure_reason": "",
    "blocked_stage": "BLOCKED_AT_PREFLIGHT",
    "final_status": "BLOCKED_AT_PREFLIGHT",
    "dry_run_decision": "TRADE_PROPOSAL",
    "candidate_status": "PAPER_ORDER_CANDIDATE_CREATED",
    "review_status": "HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST",
    "finalized_request_status": "PAPER_ORDER_REQUEST_FINALIZED",
    "manual_confirmation_status": "MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT",
    "preflight_status": "PAPER_ORDER_SEND_BLOCKED",
    "artifacts_created": [
      "TRADE_PROPOSAL",
      "Paper Order Request Candidate",
      "Human Review Queue",
      "Finalized Paper Order Request",
      "Manual Execution Confirmation",
      "Paper Send Preflight"
    ],
    "order_sent": false,
    "alpaca_order_api_called": false,
    "broker_execution_readiness": false,
    "live_trading_readiness": false,
    "batch_behavior": false,
    "cancel_replace_behavior": false,
    "paper_order_execution_enabled_true": false
  },
  {
    "scenario_id": "paper_order_execution_enabled_true",
    "description": "Execution flag true blocks before pipeline progression.",
    "passed": true,
    "failure_reason": "",
    "blocked_stage": "BLOCKED_BEFORE_PROGRESSION",
    "final_status": "BLOCKED_BEFORE_PROGRESSION",
    "dry_run_decision": "REJECT",
    "candidate_status": "PAPER_ORDER_CANDIDATE_BLOCKED",
    "review_status": null,
    "finalized_request_status": null,
    "manual_confirmation_status": null,
    "preflight_status": null,
    "artifacts_created": [],
    "order_sent": false,
    "alpaca_order_api_called": false,
    "broker_execution_readiness": false,
    "live_trading_readiness": false,
    "batch_behavior": false,
    "cancel_replace_behavior": false,
    "paper_order_execution_enabled_true": true
  }
]
```

## Artifacts Created

- full_valid_v10_pipeline: TRADE_PROPOSAL, Paper Order Request Candidate, Human Review Queue, Finalized Paper Order Request, Manual Execution Confirmation, Paper Send Preflight
- candidate_blocked: none
- human_review_rejected: TRADE_PROPOSAL, Paper Order Request Candidate, Human Review Queue
- manual_confirmation_rejected: TRADE_PROPOSAL, Paper Order Request Candidate, Human Review Queue, Finalized Paper Order Request, Manual Execution Confirmation
- preflight_blocked: TRADE_PROPOSAL, Paper Order Request Candidate, Human Review Queue, Finalized Paper Order Request, Manual Execution Confirmation, Paper Send Preflight
- paper_order_execution_enabled_true: none

## Blocked Stages

- full_valid_v10_pipeline: none
- candidate_blocked: BLOCKED_BEFORE_REVIEW
- human_review_rejected: BLOCKED_BEFORE_FINALIZED_REQUEST
- manual_confirmation_rejected: BLOCKED_BEFORE_PREFLIGHT_ALLOWED
- preflight_blocked: BLOCKED_AT_PREFLIGHT
- paper_order_execution_enabled_true: BLOCKED_BEFORE_PROGRESSION

## Final Statuses

- full_valid_v10_pipeline: PAPER_ORDER_SEND_ALLOWED
- candidate_blocked: BLOCKED_BEFORE_REVIEW
- human_review_rejected: BLOCKED_BEFORE_FINALIZED_REQUEST
- manual_confirmation_rejected: BLOCKED_BEFORE_PREFLIGHT_ALLOWED
- preflight_blocked: BLOCKED_AT_PREFLIGHT
- paper_order_execution_enabled_true: BLOCKED_BEFORE_PROGRESSION

## Safety Proofs

- Proof no order was sent: True
- Proof no Alpaca order API was called: True
- Proof PAPER_ORDER_EXECUTION_ENABLED was not enabled except blocked scenario: True
- Proof no broker execution readiness was created: True
- Proof no live trading readiness was created: True
- Proof no batch behavior was created: True
- Proof no cancel/replace behavior was created: True

## Required Statements

Live trading remains unsupported.

Increasing notional remains prohibited.

Automation beyond approved dry-run/candidate flow remains prohibited.
