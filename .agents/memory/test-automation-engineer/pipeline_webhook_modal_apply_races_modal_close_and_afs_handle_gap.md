---
name: pipeline_webhook_modal_apply_races_modal_close_and_afs_handle_gap
description: ELITEA-2006 (Webhook trigger settings modal) — Apply fires an unawaited mutation then closes synchronously (wait on the network response, not modal-hidden); AFS Concrete Handles table missed 3 description-text testids the case's own steps required; Save button is legitimately disabled when the fixture-based setup never dirties the pipeline's own Formik form (trigger config persists via its own endpoint)
type: feedback
---

**Modal "Apply" race — generalizable pattern, watch for it in other modals.**
`PipelineWebhookModal.jsx`'s `applyChanges` callback:
```js
const applyChanges = useCallback(() => {
  onSubmit(selectedWebhookType, pendingSecretValue);  // async, NOT awaited
  onClose();                                           // fires synchronously regardless
}, [...]);
```
`onSubmit` (`handleWebhookSubmit` in the parent) is itself `async` and does
`await updateTrigger(...).unwrap()` — but `applyChanges` never awaits `onSubmit`
itself before calling `onClose()`. So the modal can visually close BEFORE the
PUT resolves. A page-object method that waits only on `modal.wait_for(state=
"hidden")` after clicking Apply is racing the real persistence — an immediate
`page.reload()` right after could read stale server state.

**Fix:** wrap the Apply click in `page.expect_response(lambda r: "<mutation
url substring>" in r.url and r.request.method == "PUT")`, exactly like
`save_and_wait_for_update` already does for the pipeline-level Save button.
This works correctly regardless of whether the app's own JS awaits the
mutation — it's a black-box network observation, not dependent on the
frontend's internal sequencing. Don't trust an AFS's "the mutation is awaited
before close" claim without re-checking the actual source at implementation
time; this one was wrong (traced `applyChanges` → `onSubmit()` → `onClose()`,
no `await` between them).

**AFS Concrete Handles can silently omit an element the case's own steps
require.** ELITEA-2006's case steps 3/4/5 explicitly require verifying
description-text presence/content (Webhook Type description, Payload Format
description, Secret helper text) but the AFS's Concrete Handles table had zero
rows for any of the three Typography elements carrying that text. This isn't a
scope gap (Axis 1 already listed these as asserted) — it's a technique gap:
the analyst's exploration didn't flag they'd need testids. Caught it only
because I tried to write the actual assertion and had no handle to write it
with. Added the 3 testids myself (implementer Phase 2, `add-data-testid`) and
declared it in the PR body as a Concrete-Handles gap fill, not a
`needs-analyst-rerun` — no scope changed, only a handle was missing.
**Takeaway for future implementers:** when the case's own step-text names an
element ("verify X text is present/changes"), don't just check whether the
AFS's Concrete Handles table lists it — if it's missing, that's implementer
work to add, same OR-not-AND rule as `.agents/role-overrides.md`'s general
missing-testid clause; don't silently skip the assertion because the AFS
didn't give you a handle.

**Fixture-based setup can leave the pipeline's own Save button legitimately
disabled — don't force-click it.** When a case's steps say "Save — reload —
verify persists" but the feature under test lives entirely outside the
pipeline's Formik-tracked `values` (confirmed here: trigger/webhook config is
a dedicated `GET`/`PUT .../pipeline_trigger/...` entity, never touches the
pipeline's own `instructions` YAML), and the AFS's recommended setup fixture
(`pipeline_with_llm_id`) never dirties the form (no manual "Add node" round
trip), the pipeline-level Save button can be genuinely disabled
(`is_save_enabled() == False`) with nothing pending to save. `save_button
.evaluate("el => el.click()")` on a real `disabled` HTML button is a no-op —
no click event fires, so a network-response wait after it (like
`save_and_wait_for_update`) hangs until timeout. The correct implementation:
assert the disabled state is itself the CORRECT product behavior (nothing
pending), skip the Save click, and reload directly — the actual thing the
step needs to verify (does the already-independently-persisted config survive
a reload) is unaffected. Declare this explicitly as a declared improvisation
rather than silently diverging from the AFS's literal "clicked Save" narrative
(which was likely written from a DIFFERENT, manually-built session where the
canvas WAS dirtied).

**`is_checked()` on a MUI `RadioButtonGroup`'s `FormControlLabel`-testid'd
locator works directly** (confirms the existing `mui_radio_testid_on_label_is_
checked_works.md` finding, same underlying mechanism — label-associates-with-
input DOM semantics, no unwrap needed) — same as `CredentialCreatePage
.auth_radio`.

**MUI `TextField`/`FormInput`'s `inputProps={{ 'data-testid': '...' }}` puts
the testid on the native `<input>` directly** (established codebase pattern —
`agent-instructions-input`, `chat-folder-name-input`, `artifacts-bucket-
retention-value-input`, etc.) — prefer this over a plain `data-testid` prop on
`<FormInput>`/`<TextField>` itself, which lands on the `MuiFormControl-root`
wrapper and then needs an extra scoped `.locator("input")` sub-selector to
call `.input_value()`. The `inputProps` route needs zero extra scoping.

**Addendum (fix round r1, PR #1015, 3 reviewer findings, all confirmed then fixed):**

1. **A "free" auto-derived testid sibling (`${testid}-combobox` from
   `SingleSelect.jsx`'s own wiring) still needs its own PAGE-OBJECT field
   used by the test, or it's an orphan.** Declared a `trigger_select_combobox`
   `LocatorDescriptor` for the free `-combobox` suffix but never called it
   anywhere — `git grep -n "trigger_select_combobox"` across the WHOLE repo
   (not just the diff) showed exactly one hit, the declaration itself.
   "Free" (no separate JSX edit needed) does not exempt a field from the
   touches-rule; deleted it, no JSX change needed on the way out either since
   nothing was added on the way in.

2. **A Coverage Map "zero failed network requests" claim needs a REAL
   assertion, not just an honest live-observation note carried over from
   analysis.** Had `console_errors` checked once (end of Step 6) and zero
   network-failure assertion anywhere — reviewer caught both. Fix: reused
   the pre-existing `BasePage.capture_requests_matching(url_substring)`
   helper (already used elsewhere, e.g. `test_mcp_attach_via_tools_section.py`)
   scoped to `/pipeline_trigger/` — the ONE endpoint this flow's steps
   depend on — started live from Step 1, asserted (with `console_errors`
   too) in ONE full-flow check after the LAST step, not per-step. Scoping to
   the flow's own endpoint (not every response on the page) avoids false
   positives on unrelated asset/tracking noise — matters for a check that's
   supposed to be a reliable gate, not just an observation.

3. **A source-verified declared-improvisation docstring in the CODE does
   NOT substitute for actually amending the AFS document.** `apply_webhook_
   settings()`'s own docstring already correctly said the trigger PUT isn't
   awaited before `onClose()` — but the AFS's own Automation Hints section
   still said the opposite (stale, uncorrected). A reviewer reads the AFS as
   source of truth; a correct code comment elsewhere doesn't fix a wrong
   claim in the spec file itself. Confirmed the code's claim against
   `PipelineWebhookModal.jsx:161-164` directly (source, not memory) before
   amending the AFS prose to match — general rule: when two artifacts
   (code comment vs AFS) disagree, verify against the actual source file,
   don't just trust whichever one sounds more confident.
