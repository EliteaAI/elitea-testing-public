---
name: Repair of a transient failure needs a negative control, not a green gate
description: For a [Fix] card whose failure does not reproduce, demand a negative control in the implementer dispatch — green runs prove nothing
type: feedback
---

## The trap

A `[Fix]` card lands. You reproduce nothing — the failure is transient (passed on
DEV before and after the red run). The implementer repairs the test, runs it 3×
green, and you gate it 3× green. **All six runs are worthless as evidence.** They
would have been green on the *unrepaired* test too, because the trigger condition
was not present. A green gate on a repair for a non-reproducing failure proves
only that the test still passes when nothing is wrong.

## What to demand instead

Put this in the implementer dispatch, explicitly, as a named deliverable:

> **The negative control.** Inject the failure condition by hand. The OLD shape
> must be shown passing/misreporting under it; the NEW shape must fail loudly at
> the true failure point. Paste both outputs in the Run Report.

Worked example — #1897 / ELITEA-1140, `test_create_credential[jira]` (2026-08-28).
Condition injected: one required field left empty at Save time.

- **A, old shape:** Steps 5 and 6 both `passed`; died at Step 7 on
  `Credential '…' not found via API` — the CI signature, reproduced line for line.
- **B, new shape:** fails at **Step 5** — `Locator expected to be enabled / Actual
  value: disabled`.
- **C, new shape, keystrokes suppressed:** fails at **Step 4, naming the field**.

That is the delivery. The 3× green is hygiene.

## Say what the control does NOT prove

A control injects the condition from the harness, so it proves the **reporting
shape**, not that the original transient's mechanism *was* that condition. Write
that sentence into the closure record. The repair makes the next occurrence
diagnosable in one read; it does not claim to prevent it. Claiming more is how a
repair gets re-opened.

## The class of bug this keeps catching

Assertions that cannot fail, and actions that cannot act:

- **Acted on, never asserted on** — `el.evaluate("el => el.click()")` on a
  disabled button is a *silent no-op*: no exception, no request, no navigation. A
  real Playwright `.click()` auto-waits for *enabled* and raises at the true point.
  Any JS-dispatched interaction bypasses actionability and can silently do nothing.
- **A containment guard whose failure state contains its pass state** —
  `assert "/credentials" in page.url` is *true* on `/credentials/create-credential/jira`.
  Prefer `wait_for_url` on the exact destination.
- **`if value:` around a required field** — a missing precondition is skipped
  silently instead of failing where it happened.

When a `[Fix]` card's error message points at the product but the log shows the
UI never left the form, look here before believing the message.
