# Test Case: Pipeline — Modules Section — Attachments Toggle Persists Across Save/Reload

## Metadata
- **TMS ID**: ELITEA-2066
- **Priority**: l2 (medium, as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-09
- **Status**: extend-existing

## Covering Spec (dedup / extension proof)

- **Covering spec**: `automation/tests/ui/pipelines/test_pipeline_attach_files_in_chat.py`
  (TMS ELITEA-2059), merged to `origin/automation/base` (`9df3375c`).
- **Behavioural overlap**: ELITEA-2059's merged test already proves the causal link this case's
  steps 2–4/6 need — the "Attachments" MODULES toggle (`agent-canvas-tools-toggle-attachments`)
  flips the embedded chat's `chat-attach-button` from `disabled` to enabled **instantly**, no Save
  required (its own step 2) — and asserts the button's visibility/enabled state (step 3).
- **The gap**: ELITEA-2059 never Saves the pipeline with the module toggled, never toggles it back
  OFF, and never reloads to prove the toggle state is genuinely **persisted server-side** rather
  than only a live, unsaved formik value. This case's own steps 5–8 are exactly that: Save while
  enabled → verify the button is still enabled → toggle OFF → Save → verify the button returns to
  disabled. Live exploration this session (fresh pipeline id 8663, created and deleted via UI)
  confirmed all of it works as expected — no product defect — but also surfaced a genuine
  automation gotcha (see § Automation Hints) that ELITEA-2059's instant-check-only test never had
  to deal with: **on the FIRST render after a hard page reload, the toggle's `checked` DOM property
  can read its persisted (post-save) value up to ~2s before the chat's `disabled` attribute on the
  attach button finishes syncing to match it** — a raw one-shot DOM read taken immediately after
  `wait_for_detail_page_load()` can catch that transient window and read the WRONG (pre-sync)
  `disabled` value. A Playwright web-first assertion (auto-retrying `expect(...).not_to_be_disabled()`
  / `.to_be_disabled()`) absorbs this correctly; a bare `.is_disabled()` snapshot read taken and
  asserted without retry does not.
- **Extension shape**: add a **new test function** to the same file
  (`test_pipeline_attach_files_in_chat.py`), using the plain `pipeline_id` fixture (fresh EMPTY
  pipeline via `PipelineAPI.create_pipeline` — no LLM node execution needed here, since this
  extension only exercises the toggle/Save/reload cycle, never sends a chat message), reusing
  `PipelineDetailPage.toggle_attachments_module()`, `is_tools_module_toggle_checked()`,
  `chat_attach_button`, `save_and_wait_for_update()` — all already proven working by ELITEA-2059/
  ELITEA-2043/ELITEA-1954 — plus the existing `navigate()` for the reload. No new page-object
  method and no new testid required. Does not modify ELITEA-2059's existing test body.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: Keycloak via `${TEST_USER}`).
- A pipeline is open for editing — satisfied in-test via the `pipeline_id` fixture (fresh empty
  pipeline, no nodes needed since this case never executes the pipeline).

## Test Data
- (none required, per the source case's own Test Data table) — the `pipeline_id` fixture's
  auto-generated name/description is the only test data, matching ELITEA-2043/ELITEA-2044's
  established pattern for this fixture.

## Test Steps

1. Navigate to the fresh pipeline (`pipeline_id` fixture); wait for canvas/detail load.
   - **Verify**: TOOLS section's "Attachments" MODULES toggle is visible and unchecked; the
     embedded chat's attach button (`chat_attach_button`) is visible and disabled. (Case steps
     1–3: pipeline loaded, MODULES section visible, Attachments toggle visible with its switch.)
2. Toggle "Attachments" to enabled.
   - **Verify**: toggle's `checked` DOM property is `true`; attach button is enabled the instant
     the toggle is clicked (no Save needed for this transition — matches ELITEA-2059's finding).
     (Case step 4.)
3. Save the pipeline (`save_and_wait_for_update`); verify the `201` response and zero console errors.
   (Case step 5.)
4. Reload the pipeline via `navigate()` (fresh page load, not a soft in-app refresh) to prove
   server-side persistence rather than only live formik state.
   - **Verify (web-first, auto-retrying assertion — see § Automation Hints)**: the toggle is still
     checked AND the attach button is not disabled. (Case step 6.)
5. Toggle "Attachments" back to disabled.
   - **Verify**: toggle's `checked` DOM property is `false`; attach button becomes disabled
     instantly. (Case step 7.)
6. Save the pipeline again; verify the `201` response and zero console errors.
7. Reload the pipeline via `navigate()` again.
   - **Verify (web-first, auto-retrying assertion)**: the toggle is unchecked AND the attach
     button is disabled. (Case step 8: "Save — verify Attach Files button returns to disabled
     state.")
8. No console errors were introduced across the whole sequence.

## Expected Results
- The Attachments MODULES toggle and the embedded chat's Attach Files button are visible before
  any interaction; the button starts disabled on a fresh pipeline.
- Toggling Attachments on/off flips the attach button's enabled/disabled state instantly
  (client-side, no Save needed for the immediate UI reaction — reconfirms ELITEA-2059's finding
  from a fresh angle: both directions, not just on).
- Saving while enabled, then reloading, shows the toggle AND the attach button still reflecting
  the enabled state — proving the setting is genuinely persisted server-side, not merely an
  unsaved live value.
- Toggling off, saving, and reloading shows both the toggle and the attach button back to
  disabled — proving the OFF state persists too.
- Zero console errors throughout.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline | Pipeline is loaded in the editor | AFS step 1 | step 1: `navigate()` + canvas load wait | asserted |
| 2 In Tools section, scroll to "MODULES" area | MODULES section is visible | AFS step 1 | step 1: `get_tools_module_toggle("attachments").is_visible()` — the toggle's own visibility proves the MODULES region rendered; no separate MODULES-heading testid needed (scope discipline — this case never asserts the heading text on its own) | asserted |
| 3 Verify "Attachments" module is listed with an on/off switch | Attachments toggle is visible | AFS step 1 | step 1: same visibility check + `is_tools_module_toggle_checked("attachments")` reads the switch state | asserted |
| 4 Toggle "Attachments" switch to enabled | Attachments is enabled | AFS step 2 | step 2: `checked` DOM property `true` + attach button enabled instantly | asserted |
| 5 Save pipeline | Pipeline saves without errors | AFS step 3 | step 3: `save_and_wait_for_update()` returns non-null (`201`) + no console errors | asserted |
| 6 Verify in chat panel that "Attach Files" button becomes active | Attach Files button is enabled in the chat panel | AFS step 4 | step 4: post-reload, `chat_attach_button` not disabled (auto-retrying assertion) | asserted |
| 7 Toggle "Attachments" switch to disabled | Attachments is disabled | AFS step 5 | step 5: `checked` DOM property `false` + attach button disabled instantly | asserted |
| 8 Save — verify "Attach Files" button returns to disabled state | Attach Files button is disabled in the chat panel | AFS steps 6–7 | step 7: post-reload, `chat_attach_button` disabled (auto-retrying assertion) | asserted |

### Axis 2 — Analyst additions
- Step 4 and step 7 reload via a fresh `navigate()` rather than re-reading the DOM in the same
  unreloaded page — *added: the case's own step 6/8 wording ("verify … in the chat panel") is
  satisfiable by a same-page read, which ELITEA-2059 already does for the ON direction; a reload
  is a STRICTLY STRONGER proof (server persistence vs. live client state) and is the only way to
  honestly validate "Save" as meaningfully gating anything at all — otherwise steps 5/6 and 7/8
  would be indistinguishable from steps 4 and 7 alone. Confirmed live this session: skipping the
  reload would still pass even if Save silently failed to persist the module flag, which is
  exactly the risk this case exists to catch.*
- The reload-timing gotcha (toggle's checked state settles before the button's disabled attribute
  syncs, ~2s window observed live) is called out explicitly so the implementer uses a web-first
  auto-retrying assertion, not a one-shot DOM read — *added: a naive one-shot read is not just
  slower, it is WRONG some fraction of the time (a real flake source), confirmed by direct
  reproduction (see § Automation Hints).*
- No console errors across the sequence — *added: standard side-channel check, confirmed 0 errors
  observed live via `browser_console_messages(level="error")`.*

## Cleanup
- The `pipeline_id` fixture deletes the pipeline automatically after the test (existing fixture
  behavior, no extra teardown needed).

## Concrete Handles (discovered during exploration)

All handles are pre-existing — reused verbatim, zero new testid work.

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Attachments MODULES toggle | `[data-testid="agent-canvas-tools-toggle-attachments"]` via `PipelineDetailPage.get_tools_module_toggle("attachments")` / `is_tools_module_toggle_checked("attachments")` / `toggle_attachments_module()` | **on-`automation/testids`, NOT on `main`** (ELITEA-2059's AFS already recorded this; unchanged this session — re-verified via `git grep` after `git fetch origin`, 2026-08-09) | Pre-existing, `pipeline_detail_page.py:6084-6106`. |
| Embedded chat attach button | `[data-testid="chat-attach-button"]` via `PipelineDetailPage.chat_attach_button` | **on-`automation/testids`, NOT on `main`** (added during ELITEA-2059's implementation, `EliteaAI/EliteaUI@2a4aab23`) | Pre-existing, `pipeline_detail_page.py:470-474`. |
| Save button | `[data-testid="agent-save-button"]` via `PipelineDetailPage.save_button` (inherited from `PipelineFormPage`) + `save_and_wait_for_update(project_id, pipeline_id)` | **on-main** (long-pre-existing, used across the whole pipelines suite) | Pre-existing. |
| Pipeline navigate/reload | `PipelineDetailPage.navigate(pipeline_id)` → `/pipelines/all/{id}?viewMode=owner` | n/a (page-object method, not a locator) | Pre-existing; confirmed live this session that the `?viewMode=owner` query param is REQUIRED for a direct/hard navigation to resolve (a bare `/pipelines/all/{id}` with no query params 404s: "Page not found") — the method already handles this correctly, so no implementer action needed, just noted as a live-confirmed fact for the digest. |

## Network Behavior
- Toggling the Attachments MODULES switch (either direction): zero network requests, confirmed
  live via `browser_network_requests` before/after each click (matches ELITEA-2059/ELITEA-2043's
  existing finding — pure client-side formik state).
- Saving the pipeline: `PUT .../elitea_core/application/prompt_lib/{project}/{id}` → `201`
  (matches the existing `save_and_wait_for_update()` helper's contract).
- Reloading: standard page-load GETs for the pipeline detail data; no unexpected calls observed.

## Known Defects Found During Exploration
- None. The full toggle → save → reload → toggle-off → save → reload cycle behaved exactly as
  the case expects on both directions; the only surprise was the transient (~2s) client-side sync
  lag documented above, which is a UI-responsiveness characteristic (not a data-correctness bug —
  the persisted VALUE was always correct on reload, only the DOM's `disabled` attribute took a
  moment to catch up to it) and is fully absorbed by a correctly-written auto-retrying assertion.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Fixture: plain `pipeline_id` (fresh empty pipeline via `PipelineAPI.create_pipeline`) — no LLM
  node needed, this extension never sends a chat message or executes the pipeline.
- **Critical: use Playwright's auto-retrying `expect()` assertions for the post-reload checks**
  (`expect(pipeline_page.chat_attach_button).to_be_disabled(timeout=...)` /
  `.not_to_be_disabled(timeout=...)`), NOT a bare `.is_disabled()` snapshot compared with a plain
  `assert`. A one-shot read taken immediately after `wait_for_detail_page_load()` can observe the
  attach button's `disabled` attribute before it has finished syncing to the (already-correct,
  already-persisted) toggle state — confirmed by direct live reproduction this session (toggle
  read `checked=true` immediately after reload while the button still read `disabled=true`; both
  settled to the consistent, correct pair ~2s later with no further action). The toggle's own
  `checked` read is NOT similarly delayed — only the button's `disabled` attribute lags.
- Reuse `save_and_wait_for_update(project_id, pipeline_id, timeout=...)` exactly as ELITEA-2059/
  ELITEA-1954/others already do — don't hand-roll a new save-and-wait helper.
- `project_id` — reuse whatever fixture/settings value the file's existing test already resolves
  it from (`test_attach_files_in_chat.py`'s own `save_and_wait_for_update` call site is the
  pattern to copy).
