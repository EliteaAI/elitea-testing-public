---
name: toast_fires_with_mutation_not_with_display_refetch_lag
description: When a reviewer finding demands a toast-text assertion right after an awaited mutation, verify in source whether toastSuccess() is called in the SAME continuation as the mutation the page object already waits on — a documented "displayed value lags by ~2s" caveat on a SIBLING assertion does not automatically extend to the toast itself
type: feedback
---

**Context (ELITEA-2005 fix round r2, PR #1022).** A reviewer flagged that
Steps 5/8/10 were missing toast-text assertions ("Webhook configured
successfully" / "Schedule configured successfully" / "Trigger updated to
Chat Message") the AFS had explicitly claimed as covered. Before wiring the
assertion, the open question was: is the toast itself subject to the SAME
cache-invalidation lag the AFS's own Automation Hints already documented for
the Trigger select's *displayed value* (up to ~2s after Apply/select,
requiring a polling `expect(...).to_have_text(...)` rather than a same-tick
read)?

**Answer: no, verified by reading `TriggerTypeSelector.jsx` directly.** In
every one of the 3 flows, `toastSuccess(...)` is called in the exact same
`async` continuation as the `await updateTrigger(...).unwrap()` the page
object's `apply_webhook_settings()` / `apply_schedule_settings()` /
`select_trigger_type()` methods already wait on via
`page.expect_response(...)`. The *displayed* Trigger-select text is a
SEPARATE RTK-Query cache tag that re-fetches independently (a `GET
.../pipeline_trigger/.../trigger` after the mutating `PUT`) and can lag
behind by up to ~2s — that lag is real and already correctly handled by
`expect(trigger_select).to_have_text(...)` — but the toast has no such
second network round-trip: it fires the moment the mutation's own promise
resolves, which is the same moment the page object's `expect_response`
already resolves. So `expect(page_obj.trigger_toast_message).to_have_text(...)`
right after the existing apply/select call (no extra wait needed) was
correct and green on 4/4 local runs (including a run with an unrelated
transient rerun on an earlier step).

**Generalizable check before adding a "missing assertion" fix for anything
timing-adjacent to a documented lag:** don't assume every side-effect of the
same mutation shares the same lag characteristics. Read the actual handler
in source — is the flagged observable set in the SAME awaited continuation
the test already waits on, or does it depend on a SEPARATE
query/refetch/subscription? Only the latter needs its own poll/wait
strategy; the former is already covered by the existing wait.

**Reusable locator shape confirmed AGAIN (4th page object now):** a generic
app-wide `data-testid="toast-message"` Toast/Snackbar component (source:
`Toast.jsx`, one global instance via `ToastProvider`'s context) is reused
verbatim across `artifacts_page.py` (`success_toast_message`),
`skills_list_page.py` (`import_success_toast_message`),
`skill_detail_page.py` (`version_toast_message`), and now
`pipeline_detail_page.py` (`trigger_toast_message`) — same testid, each page
object gives it its own semantic field name and docstring rather than a
single shared base-class field (matches this repo's established
per-page-object-field convention, not centralized).
