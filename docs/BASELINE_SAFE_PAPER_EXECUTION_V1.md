# Baseline Safe Paper Execution V1

## 1. Baseline Name

Baseline Safe Paper Execution V1.

## 2. Date

2026-05-19.

## 3. Completed Gates

- Proposal validation: completed.
- Risk Manager approval: completed.
- Human approval: completed.
- Manual execution confirmation: completed.
- Journal commit before send: completed.
- Execution Gatekeeper preflight: completed.
- Alpaca paper account mode confirmation: completed.
- ADLC compliance: completed.
- Post-send reconciliation: completed.
- Post-mortem review: completed.

## 4. First Controlled Paper Send Result

`PAPER_ORDER_SUBMITTED`

## 5. Alpaca Paper Order ID

`f4d6e18c-ff4c-4434-b8de-09bdbe8e0721`

## 6. Reconciliation Result

`RECONCILIATION_MATCHED`

## 7. Report Path

`reports/first_controlled_paper_send/20260519T213908Z/FIRST_CONTROLLED_PAPER_SEND_REPORT.md`

## 8. Post-Mortem Path

`reports/first_controlled_paper_send/20260519T213908Z/POST_MORTEM.md`

## 9. Safety Controls Confirmed

- Paper trading only.
- Live endpoint rejected.
- System returned to `DRY_RUN_ONLY`: confirmed.
- `PAPER_ORDER_EXECUTION_ENABLED` unset after run: confirmed.
- Secrets printed: no.
- One order maximum for the run.
- Limit order only.
- Day time-in-force only.
- Max notional capped at `100 USD`.
- No short selling.
- No crypto.
- No options.
- No margin or leverage.
- No extended hours.
- No batch orders.
- No cancel/replace.
- No autonomous follow-up order.

## 10. What Is Allowed After This Baseline

- Continue architecture, governance, and audit documentation.
- Run tests and architecture validation.
- Run `DRY_RUN_ONLY` flows.
- Run mocked paper send flows.
- Review first-send artifacts and post-mortem.
- Run read-only reconciliation or report generation against existing artifacts.

## 11. What Is Still Prohibited

- Live trading.
- Live Alpaca endpoints.
- Autonomous execution.
- Batch orders.
- Cancel/replace.
- Market orders.
- Short selling.
- Options.
- Crypto.
- Margin or leverage.
- Extended-hours trading.
- Increasing order size without a new reviewed phase.
- Creating or committing credentials.

## 12. Conditions Required Before Another Paper Send

- `PAPER_ORDER_EXECUTION_ENABLED` must remain unset or false until the manual send window.
- System must start from `DRY_RUN_ONLY`.
- Full test suite must pass.
- Architecture validation must pass.
- Dry-run flow must pass.
- Mocked paper send must pass.
- Proposal validation must pass.
- Risk Manager output must be `RISK_APPROVED`.
- Human approval must be `HUMAN_APPROVED_FOR_PAPER_ONLY`.
- Manual execution confirmation must be `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY`.
- Journal commit must exist before send.
- Preflight must be `PAPER_ORDER_SEND_ALLOWED`.
- Paper account mode must be confirmed.
- ADLC compliance must be `PASS`.
- Prior post-mortem issues must be reviewed.

## 13. Conditions Required Before Increasing Size

- A new scoped phase must approve the size increase.
- Risk limits must be updated in governance first.
- Tests must prove the new cap is enforced.
- Post-send reconciliation and reporting must remain required.
- Human approval and manual confirmation must remain mandatory.
- The default action must remain no trade / dry run.

## 14. Conditions Required Before Adding Automation

- A new architecture phase must define autonomy boundaries.
- Risk Manager, Human Approval, Journal Agent, and Execution Gatekeeper must remain blocking gates.
- Automation must not bypass manual approval unless explicitly approved by a new governance phase.
- Monitoring, failure handling, and rollback rules must be documented before implementation.
- Tests must prove no autonomous follow-up order can be created unintentionally.

## 15. Live Trading Remains Unsupported

Live trading remains unsupported.

This baseline authorizes only controlled Alpaca paper execution under the documented gates. It does not authorize live trading, live endpoints, autonomous execution, batch orders, cancel/replace, or any increase in order scope.
