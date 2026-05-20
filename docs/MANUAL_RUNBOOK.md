# Manual Operations Runbook

## 1. Current System Status

The system is a controlled Alpaca paper-trading decision and execution workflow. It supports architecture validation, deterministic dry runs, mocked paper sends, one manually confirmed real Alpaca paper send, and read-only post-send reconciliation.

The default action remains `DRY_RUN_ONLY` / send blocked.

No live trading is supported.

## 2. Phase Status

- Architecture and governance phases: PASS
- Paper order request flow: PASS
- Phase 9 controlled paper send: PASS
- Phase 10 post-send reconciliation: PASS

## 3. What The System Can Do Now

- Validate architecture and safety constraints.
- Build a deterministic paper-only order request.
- Run dry-run execution without broker submission.
- Run mocked paper send with all gates enforced.
- Send one controlled real Alpaca paper order only when manually configured.
- Record an execution result.
- Record post-send journal entries.
- Reconcile one submitted paper order using read-only account, positions, and specific order status reads.

## 4. What The System Cannot Do

- It cannot trade live.
- It cannot use live Alpaca endpoints.
- It cannot execute autonomously.
- It cannot submit batch orders.
- It cannot cancel orders.
- It cannot replace orders.
- It cannot submit market orders.
- It cannot short sell.
- It cannot trade options.
- It cannot trade crypto.
- It cannot use margin or leverage.
- It cannot trade extended hours.
- It cannot create follow-up trades after reconciliation.

## 5. Required Safety Assumptions

- All trading behavior is paper-only.
- Human approval and manual execution confirmation are separate gates.
- Risk Manager approval is mandatory.
- Journal commit must exist before any paper send.
- Reconciliation is observe-and-journal only.
- Environment variables are set manually for the single operation and then removed.
- Credentials must never be written to files, logs, reports, journal entries, or prompts.

## 6. Required Environment Variables

Only these variables are allowed for a real Alpaca paper send:

```bash
ALPACA_API_KEY_ID
ALPACA_API_SECRET_KEY
ALPACA_PAPER=true
PAPER_ORDER_EXECUTION_ENABLED=true
```

Do not create `.env` files.

### Local `.env.local` Usage

`.env.local` is allowed for local manual operation only. It must never be committed, copied into reports, printed, or pasted into prompts.

Load local values into the current shell only when preparing a manual paper send:

```bash
set -a
source .env.local
set +a
```

Verify required variables are present without printing values:

```bash
python3 - <<'PY'
import os, json
print(json.dumps({
    "ALPACA_API_KEY_ID_present": bool(os.environ.get("ALPACA_API_KEY_ID")),
    "ALPACA_API_SECRET_KEY_present": bool(os.environ.get("ALPACA_API_SECRET_KEY")),
    "ALPACA_PAPER_is_true": os.environ.get("ALPACA_PAPER", "").lower() == "true",
    "PAPER_ORDER_EXECUTION_ENABLED_is_true": os.environ.get("PAPER_ORDER_EXECUTION_ENABLED", "").lower() == "true",
}, indent=2))
PY
```

After any manual send attempt, disable execution in the current shell:

```bash
unset PAPER_ORDER_EXECUTION_ENABLED
```

## 7. Run Architecture Validation

```bash
python3 -m unittest tests/test_architecture_validator.py
```

## 8. Run Tests

Run the full test suite:

```bash
python3 -m unittest discover -s tests
```

Run Phase 9 tests:

```bash
python3 -m unittest tests/test_alpaca_paper_order_adapter.py tests/test_paper_execution_dry_run.py
```

Run Phase 10 tests:

```bash
python3 -m unittest tests/test_paper_order_reconciliation.py
```

## 9. Run Dry-Run Flow

```bash
python3 runtime/paper_execution_dry_run.py
```

Expected default posture:

- `adapter_mode`: `DRY_RUN_ONLY`
- `final_execution_status`: `DRY_RUN_COMPLETED`
- no broker order submitted

## 10. Run Mocked Paper Send

```bash
python3 runtime/paper_execution_dry_run.py --mode MOCKED_PAPER_SEND --confirm --enabled
```

This uses the mocked paper client and must not contact Alpaca.

## 11. Run One Controlled Real Alpaca Paper Send

Run this only after completing the manual checklist below.

```bash
ALPACA_API_KEY_ID="your-paper-key" \
ALPACA_API_SECRET_KEY="your-paper-secret" \
ALPACA_PAPER=true \
PAPER_ORDER_EXECUTION_ENABLED=true \
python3 runtime/paper_execution_dry_run.py --mode REAL_ALPACA_PAPER_SEND --confirm
```

After the command completes, unset the variables in the shell or close the shell session.

## 12. Run Post-Send Reconciliation

Run deterministic reconciliation:

```bash
python3 runtime/paper_order_reconciliation.py
```

Run pending reconciliation report:

```bash
python3 runtime/paper_order_reconciliation.py --pending
```

Reconciliation is read-only and defaults to `OBSERVE_AND_JOURNAL_ONLY`.

## 13. Inspect Journal Output

Journal information is included in command JSON output under `journal_entry` when a send or reconciliation record is created.

For static memory review, inspect:

```bash
cat memory/journal.md
cat test/sandbox/memory/journal.md
```

Do not write credentials or secrets into journal files.

## 14. Verify No Live Trading Is Enabled

Check that runtime code references only the paper endpoint:

```bash
rg "api.alpaca.markets|paper-api.alpaca.markets|LIVE|live_trade|send_live" runtime tests
```

Expected result:

- `paper-api.alpaca.markets` may appear.
- live endpoint references may appear only in tests that assert rejection.
- no live trading method should exist.

Also verify no cancel, replace, or batch behavior exists:

```bash
rg "cancel_order|replace_order|batch_orders|submit_order|place_order" runtime tests
```

Expected result:

- Runtime should not expose cancel, replace, batch, or uncontrolled submit behavior.
- Test references should only assert those methods do not exist or are not called.

## 15. Emergency Stop Procedure

1. Stop the current command with `Ctrl-C`.
2. Disable execution in the current shell:

```bash
unset PAPER_ORDER_EXECUTION_ENABLED
unset ALPACA_API_KEY_ID
unset ALPACA_API_SECRET_KEY
unset ALPACA_PAPER
```

3. Return to dry-run mode:

```bash
python3 runtime/paper_execution_dry_run.py
```

4. Confirm no cancel/replace action was attempted by this system.
5. Use the Alpaca paper dashboard manually if a paper order needs external review.

## 16. Common Failure Modes

- `PAPER_ORDER_EXECUTION_ENABLED is not true`: execution was not explicitly enabled.
- `adapter mode is DRY_RUN_ONLY`: real paper send mode was not explicitly selected.
- `paper mode is not confirmed`: `ALPACA_PAPER=true` was not set.
- `live endpoint/config rejected`: endpoint is not the Alpaca paper endpoint.
- `missing risk approval`: Risk Manager did not approve.
- `missing human approval`: human approval gate did not pass.
- `missing manual execution confirmation`: final manual confirmation did not pass.
- `missing journal commit`: journal was not committed before send.
- `notional over 100 USD`: order exceeds Phase 9 hard cap.
- `RECONCILIATION_ORDER_NOT_FOUND`: Alpaca paper order status was unavailable.
- `RECONCILIATION_READ_ERROR`: read-only reconciliation call failed.

## 17. Manual Checklist Before Any Paper Send

- Confirm this is paper trading only.
- Confirm Alpaca paper account.
- Confirm live endpoint is not configured.
- Confirm `PAPER_ORDER_EXECUTION_ENABLED=true` only for the manual send.
- Confirm execution mode is `REAL_ALPACA_PAPER_SEND` only for the manual send.
- Confirm proposal validation passed.
- Confirm Risk Manager output is `RISK_APPROVED`.
- Confirm human approval is `HUMAN_APPROVED_FOR_PAPER_ONLY`.
- Confirm manual execution confirmation is `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY`.
- Confirm journal commit exists before send.
- Confirm preflight status is `PAPER_ORDER_SEND_ALLOWED`.
- Confirm max notional is `<= 100 USD`.
- Confirm order type is limit.
- Confirm time in force is day.
- Confirm no short selling.
- Confirm no crypto.
- Confirm no options.
- Confirm no margin/leverage.
- Confirm extended hours disabled.

## 18. Manual Checklist After Any Paper Send

- Confirm execution result was recorded.
- Confirm Alpaca paper order id if returned.
- Confirm post-send journal entry exists.
- Run reconciliation.
- Confirm reconciliation status.
- Confirm no follow-up order was created.
- Confirm no cancel/replace happened.
- Disable `PAPER_ORDER_EXECUTION_ENABLED` after the manual send.
- Return system to `DRY_RUN_ONLY`.

## 19. Rules For Increasing Scope Later

- Add architecture and governance documents before implementation.
- Keep paper trading only unless a separate approved phase explicitly changes scope.
- Add tests before expanding behavior.
- Preserve Risk Manager, human approval, manual confirmation, journal, and gatekeeper controls.
- Do not increase notional, instruments, order types, or automation without a new phase and audit.
- Do not add cancel/replace or batch orders without separate design approval.
- Do not add live trading without a new project mandate.

## 20. No Live Trading Supported

This system does not support live trading.

Any live endpoint, live account mode, live order behavior, autonomous execution, cancel/replace behavior, or batch order behavior is out of scope and must be rejected.
