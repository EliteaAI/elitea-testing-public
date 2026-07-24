# Test Case: Entry Point Node — Trigger Types (Chat Message, Schedule, Webhook)

## Metadata
- **TMS ID**: ELITEA-2005
- **Linked Story**: none
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-07-24
- **Status**: ready-for-automation

**Family/cluster note — ELITEA-2006 overlaps on the Webhook flow, deliberately.**
`test-specs/pipelines/l3_webhook-trigger-settings-modal_ELITEA-2006.md` (same
batch, same session date) is a genuinely separate, deliberately-authored TMS
case that deep-dives the Webhook settings modal's own internals (type
switching GitHub/GitLab/Custom, URL/description live-update, Secret Value
eye/copy/refresh, sub-config persistence) — confirmed by reading both cases'
`source.md`: distinct objectives, not a duplicate. **This case's OWN Webhook
step (4–6) stays intentionally shallow** (open → GitHub default → Apply →
persisted) per this case's own looser wording; the deep modal-internals
verification is ELITEA-2006's job, not re-litigated here. **Testid naming is
aligned to ELITEA-2006's already-specced names for every element we both
touch** (`pipeline-trigger-select`, `pipeline-webhook-modal`,
`pipeline-webhook-type-radio-{value}`, `pipeline-webhook-apply-button`) so a
single `add-data-testid` pass satisfies both AFSs without conflicting names —
see Concrete Handles for the reused rows. Recommend the orchestrator sequence
these two implementer dispatches so whichever lands first does the shared
`add-data-testid` work and the second reuses it rather than re-flagging it.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline exists with a single entry point node, no HITL/Printer nodes and no interrupts configured. This is load-bearing, not decorative: `TriggerTypeSelector.jsx`'s `hasInteractiveElements` check (confirmed via source read) restricts the trigger dropdown to a **Chat-Message-only** option set whenever the pipeline's saved YAML contains a HITL/Printer node or a non-empty `interrupt_before`/`interrupt_after` list — that restricted-options scenario is explicitly out of scope for this case (case precondition avoids it) and is a good candidate for a follow-up case, not filed here since it's an intentional, already-documented restriction, not a defect.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A throwaway pipeline — reuse the existing `pipeline_id` fixture (`automation/fixtures/data_fixtures.py`, function-scoped, auto-creates via `PipelineAPI.create_pipeline` and auto-deletes on teardown). This session instead created and manually deleted its own pipeline via the UI (`QA-ELITEA-2005-EntryTrigger`, id `5684`, project `Private`/`399`) since analysts don't have automation-fixture authority — see Cleanup.
- One `LLM` node added via the canvas `+` menu (becomes the pipeline's sole real node and — confirmed live — is **automatically** the entry point; no explicit "Make entrypoint" action is needed for a pipeline's first/only node).
- One `Code` node added later (case step 9) via the same `+` menu, then explicitly promoted to entry point via the existing `make_node_entrypoint()` three-dot-menu action.

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` = `399` ("Private" project, confirmed live from the webhook URL example this session generated: `.../webhook/prompt_lib/399/5807/github`).

## Test Steps

1. Create a pipeline (Name/Description filled, Save) and, on its detail page, add a single `LLM` node via the canvas `+` menu.
   - **Verify**: pipeline is created with exactly one real node (`.react-flow__node` count = 2, i.e. the new node + the always-present `END`); the new node is automatically the entry point — no separate "Make entrypoint" step needed for a pipeline's first node.
2. Fit-view/zoom the canvas and observe the node's inline card.
   - **Verify**: a "Trigger" field (label + info-tooltip icon) is visible directly on the node card — no click-to-expand action needed, the card renders always-expanded (same finding as the sibling MCP/LLM-node AFSs) — and its select shows "Chat Message" by default.
3. Click the Trigger select to open it.
   - **Verify**: the opened `listbox` lists **exactly 3** options — "Chat Message", "Schedule", "Webhook" — each carrying the project's existing, unconditional `select-option-{value}` testid (`select-option-chat_message` / `select-option-schedule` / `select-option-webhook`, confirmed live; **zero new testid work needed for the options themselves**, see Concrete Handles).
4. Click the "Webhook" option.
   - **Verify**: a "Webhook settings" modal (`role="dialog"`) opens automatically, defaulting to Webhook Type = "GitHub" (radio checked) with its description ("Uses x-hub-signature-256 header with HMAC-SHA256 signature") and Payload-Format copy. The modal's "Webhook URL" / "Secret Value" fields populate a moment after the modal opens (confirmed: an auto-save `PUT .../pipeline_trigger/.../trigger` fires the instant "Webhook" is selected, *before* the modal's Apply button is ever clicked — this differs from the Schedule flow, see step 6).
5. Click "Apply" in the Webhook settings modal.
   - **Verify**: toast "Webhook configured successfully"; the entry-point Trigger select now displays "Webhook" (observed near-instantly in this session, but see Automation Hints for the safe wait strategy — don't assert on the same tick as the click, in general).
6. Click the pipeline's main "Save" button, then reload the page at its canonical URL (with `destTab`/`viewMode`/`name` query params intact).
   - **Verify**: toast "The pipeline has been updated" on Save (`PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}`, `201`); after reload, the Trigger select still shows "Webhook" — persisted.
7. Re-open the Trigger select and click the "Schedule" option.
   - **Verify**: a "Schedule settings" modal opens, defaulting to "At 00:00, only on Saturday" (Default radio checked; `Every [week] on [SAT] at [00]:[00]`). Unlike the Webhook flow, the Trigger select **still shows the previous value ("Webhook") behind the modal** at this point — Schedule has no pre-Apply auto-save (confirmed live; see Automation Hints for why this asymmetry is not a defect).
8. Click "Apply" in the Schedule settings modal.
   - **Verify**: toast "Schedule configured successfully"; the entry-point Trigger select updates to "Schedule" — confirmed to lag the toast by roughly 1–2s in this session (still showed "Webhook" immediately after the toast, updated to "Schedule" after a short wait). Automation must poll/wait for this text, never assert on the same tick as the Apply click (see Automation Hints).
9. Click the pipeline's main "Save" button, then reload the page at its canonical URL.
   - **Verify**: after reload, the Trigger select shows "Schedule" — persisted.
10. Re-open the Trigger select and click the "Chat Message" option (no modal for this type — it saves directly, like Webhook's initial auto-save).
    - **Verify**: toast "Trigger updated to Chat Message"; the Trigger select updates to "Chat Message" — again observed to lag the toast by ~1–2s in this session (same polling caveat as step 8).
11. Add a second node of a different type — a `Code` node — via the canvas `+` menu, then use its three-dot menu's "Make entrypoint" action.
    - **Verify**: the original `LLM` node's Trigger field **disappears** the instant it stops being the entry point (`TriggerTypeSelector` is rendered conditionally, gated on `isEntrypoint` — confirmed live and via source read of `NodeCard.jsx`); `get_entrypoint_node_id()` (existing `PipelineDetailPage` method, reads the YAML `entry_point:` field) now returns the `Code` node's id.
12. Observe the `Code` node's inline card and open its own Trigger select.
    - **Verify**: the SAME "Trigger" field appears on the `Code` node (defaulting to "Chat Message" — the value already persisted from step 10), and opening it again lists **exactly 3** options with the same `select-option-{value}` testids as step 3 — confirming trigger types are available regardless of the entry point node's type.

## Expected Results
- The entry-point node's Trigger dropdown defaults to "Chat Message" and lists exactly 3 options: Chat Message, Schedule, Webhook.
- Selecting Webhook auto-saves immediately (before the settings modal's own Apply) and opens a modal defaulting to Webhook Type = GitHub; selecting Schedule opens a modal defaulting to a weekly-Saturday-midnight cron, but does NOT save until Apply is clicked.
- Each of the three trigger types persists correctly across a pipeline Save + full page reload.
- Switching back to Chat Message saves directly, no modal.
- The Trigger dropdown (and all 3 options) is available on ANY node type used as the pipeline's entry point, not just the node type used to explore steps 1–10 — confirmed on a `Code` node in addition to the `LLM` node.
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: pipeline with single entry point node, no HITL/Printer/interrupts | setup exists | step 1 | step 1: node count + auto-entrypoint | asserted |
| 1 Create a pipeline with a single entry point node | Pipeline created with one node | step 1 | step 1 | asserted |
| 2 Click on the entry point node — locate "Trigger" dropdown (defaults "Chat Message") | Trigger dropdown visible, defaults Chat Message | step 2 | step 2 | asserted |
| 3 Open Trigger dropdown — verify 3 options | All 3 listed | step 3 | step 3: listbox option count + testids | asserted |
| 4 Select and Apply "Webhook" — verify dropdown updates with default webhook settings | Dropdown shows Webhook + settings appear | steps 4–5 | step 4: modal defaults; step 5: dropdown value + toast | asserted *(decomposed)* |
| 5 Save — reload — verify Trigger shows "Webhook" | Webhook persisted | step 6 | step 6: post-reload value | asserted |
| 6 Select and Apply "Schedule" — verify dropdown updates with default schedule settings | Dropdown shows Schedule + settings appear | steps 7–8 | step 7: modal defaults; step 8: dropdown value + toast | asserted *(decomposed)* |
| 7 Save — reload — verify Trigger shows "Schedule" | Schedule persisted | step 9 | step 9: post-reload value | asserted |
| 8 Switch back to "Chat Message" | Dropdown returns to Chat Message | step 10 | step 10: dropdown value + toast | asserted |
| 9 Repeat with a different node type as entry point — verify Trigger dropdown still appears with all 3 options | All 3 trigger types available regardless of node type | steps 11–12 | step 11: entrypoint moved + old node's field disappeared; step 12: new node's field + 3 options | asserted *(decomposed)* |
| Expected Final State: all 3 trigger types supported, each persists, dropdown available for any entry-point node type | — | all steps | all steps | asserted |
| Pass/Fail: all steps complete without errors; all 3 trigger types selectable and persist after save/reload | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Steps 4/7 additionally assert the *absence* of an auto-save for Schedule (Trigger select still shows the previous value behind the just-opened Schedule modal) versus the *presence* of one for Webhook — *added: the case only asks to verify the dropdown eventually updates "with default settings appear," but the two trigger types demonstrably reach that end state via different save timings, and an implementer who assumes symmetric behavior could write a flaky assertion (asserting the dropdown already shows "Schedule" the instant the modal opens, which is false).*
- Step 11 additionally asserts that the PREVIOUS entry-point node's Trigger field disappears when a new node is promoted — *added: the case's step 9 only asks that the NEW entry point shows the dropdown; verifying the OLD one loses it guards the `isEntrypoint`-gated conditional rendering itself, not just the new node's copy of it.*
- No console-error assertion was in the original case text; added it throughout as a side-channel check per this project's standard practice — zero console errors were observed across the whole flow, no defect to report.
- No explicit polling/wait-strategy assertion was in the case text; added as an Automation Hint (not a test assertion per se) after observing the toast-vs-display-update lag in steps 8 and 10 — *added to prevent the implementer from writing a same-tick assertion that flakes intermittently.*

## Cleanup

1. This session created and then fully deleted its own throwaway pipeline (`QA-ELITEA-2005-EntryTrigger`, id `5684`, project `Private`/`399`) via the UI's own three-dot "Delete pipeline" action (typed-name confirmation dialog) — nothing left behind; analyst has no automation-fixture authority per `.agents/workflow.md`.
2. Implementer: use the existing `pipeline_id` fixture (`automation/fixtures/data_fixtures.py`) — function-scoped, auto-creates via `PipelineAPI.create_pipeline`, auto-deletes on teardown. No new fixture is needed for this case.

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only** (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`) — every row below names the stable `data-testid` handle, its PROVENANCE (verified via a fresh `git fetch origin` this session, checked against both `origin/main` and `origin/automation/testids`), and — where missing — the exact wiring point for `add-data-testid`.

| Element | Testid (recommended name where missing) | Provenance |
|---|---|---|
| Entry-point Trigger select | **NO `data-testid` today.** `TriggerTypeSelector.jsx:296` (`<SingleSelect ... onValueChange={handleTriggerTypeChange} options={availableTriggerOptions} ... showBorder className="nopan nodrag" />`) is missing the `data-testid` prop that `SingleSelect.jsx` (`src/[fsd]/shared/ui/select/SingleSelect.jsx:82,658-659`) already destructures and forwards — same mechanism already used for `pipeline-mcp-node-toolkit-select`/`-combobox` (ELITEA-1954/1955). **Flag to `add-data-testid`**: add `data-testid="pipeline-trigger-select"` to the `<SingleSelect>` call. Zero shared-component edits needed. Note: unlike the MCP-node select (page-wide-safe only "as long as a single MCP node"), this select is inherently page-wide-safe **always** — only one node can be the pipeline's entry point at a time, so there is never more than one `TriggerTypeSelector` rendered simultaneously. **Name reused verbatim from `l3_webhook-trigger-settings-modal_ELITEA-2006.md`'s Concrete Handles** — same element, same session date, independently derived to the identical name; do not re-flag under a different name. | needs-adding (mechanism it depends on — `SingleSelect`'s `data-testid` passthrough — is on-main ✓) |
| Entry-point Trigger select's inner combobox (carries `aria-expanded`) | Comes for free once the row above is wired: `SingleSelect.jsx:659` auto-derives `${dataTestId}-combobox` → `pipeline-trigger-select-combobox`. No separate wiring needed. | needs-adding (same prop as above) |
| Trigger option "Chat Message" | `select-option-chat_message` — confirmed live, unconditional per-option testid (`SingleSelectMenuItem.jsx:117`) | on-main ✓ |
| Trigger option "Schedule" | `select-option-schedule` — same mechanism | on-main ✓ |
| Trigger option "Webhook" | `select-option-webhook` — same mechanism | on-main ✓ |
| Schedule settings modal (root) | **NO `data-testid` today.** `PipelineScheduleModal.jsx:46` (`<Modal.BaseModal ...>`) is missing the `dataTestId` prop that `BaseModal.jsx:32,124` already supports (`data-testid={dataTestId}` on the MUI `Dialog` root). **Flag to `add-data-testid`**: add `dataTestId="pipeline-schedule-modal"`. | needs-adding (mechanism on-main ✓) |
| Schedule settings modal — default-cron summary text (e.g. "At 00:00, only on Saturday") | **NO `data-testid` today.** `PipelineScheduleModal.jsx:54-59` (`<Typography variant="headingSmall" ...>{cronState.message}</Typography>`) is a plain Typography. **Flag to `add-data-testid`**: add `data-testid="pipeline-schedule-modal-summary-text"` directly on this element (no shared-component dependency). | needs-adding |
| Schedule settings modal — Apply button | **NO `data-testid` today.** `PipelineScheduleModal.jsx:116-124` builds its own `<Button>` (via the `actions` prop, not `Modal.BaseModal`'s built-in `onConfirm`/`confirmButtonTestId` path, since this modal supplies custom actions). **Flag to `add-data-testid`**: add `data-testid="pipeline-schedule-apply-button"` directly on this `<Button>`. | needs-adding |
| Webhook settings modal (root) | **NO `data-testid` today.** `PipelineWebhookModal.jsx:169` (`<Modal.BaseModal ...>`) — same missing prop as the Schedule modal. **Flag to `add-data-testid`**: add `dataTestId="pipeline-webhook-modal"`. **Name reused verbatim from `l3_webhook-trigger-settings-modal_ELITEA-2006.md`** — same element, same session date, independently derived to the identical name. | needs-adding (mechanism on-main ✓) |
| Webhook Type radio group (dynamic per option, e.g. default-selected "GitHub") | **NO `data-testid` today.** `PipelineWebhookModal.jsx:183-187` (`<Checkbox.RadioButtonGroup value={selectedWebhookType} items={WEBHOOK_TYPE_OPTIONS} onChange={setSelectedWebhookType} />`) is missing the `testId` prop that `RadioButtonGroup.jsx:10,36-38` already supports and composes per-item as `${testId}-${value.toLowerCase()}` on each option's `FormControlLabel` — the SAME dynamic-testid + `.is_checked()` pattern this repo's own `credential_create_page.py` (`AUTH_METHOD_RADIO = '[data-testid="toolkit-field-auth-radio-{}"]'`) already proves works through a `FormControlLabel` wrapper, not just a bare `<input>`. **Flag to `add-data-testid`**: add `testId="pipeline-webhook-type-radio"` → yields `pipeline-webhook-type-radio-github` / `pipeline-webhook-type-radio-gitlab` / `pipeline-webhook-type-radio-custom`. Use `pipeline-webhook-type-radio-github`'s `.is_checked()` to assert the "defaults to GitHub" observable from step 4. **Name reused verbatim from `l3_webhook-trigger-settings-modal_ELITEA-2006.md`'s Concrete Handles** — same element, same session date, independently derived to the identical name; do not re-flag under a different name. **PROVENANCE CAVEAT**: the `testId` prop mechanism on `RadioButtonGroup.jsx` itself is confirmed present on `automation/testids` but **NOT YET on `main`** (added by a prior, unrelated case — verified via `git diff origin/main origin/automation/testids -- RadioButtonGroup.jsx`, which is otherwise empty). Not a blocker (the dev server runs `automation/testids`), but the closure record should note this dependency's own promotion status alongside this case's new testids. | needs-adding — **the prop it depends on is on `automation/testids` only, not yet on `main`** |
| Webhook settings modal — Apply button | **NO `data-testid` today.** `PipelineWebhookModal.jsx:350-358` builds its own `<Button>` (custom `actions` prop, same shape as the Schedule modal). **Flag to `add-data-testid`**: add `data-testid="pipeline-webhook-apply-button"`. **Name reused verbatim from `l3_webhook-trigger-settings-modal_ELITEA-2006.md`** — same element, same session date, independently derived to the identical name. | needs-adding |
| Pipeline's own entry-point node id (YAML `entry_point:` field) | `get_entrypoint_node_id()` — existing `PipelineDetailPage` method, reads the YAML view's `entry_point:` field via regex; no new handle needed | on-main ✓ (existing helper) |
| Pipeline Save button | `save_and_wait_for_update()` — existing `PipelineDetailPage` method, already waits on the `PUT .../application/prompt_lib/{project}/{pipeline_id}` `201` response instead of a fixed timeout | on-main ✓ (existing helper) |

## Network Behavior
- `PUT ${ELITEA_API_BASE}/elitea_core/pipeline_trigger/prompt_lib/${PROJECT_ID}/pipeline/{version_id}/trigger` — fires (a) the instant "Webhook" is selected (before the modal's own Apply), (b) on Schedule modal Apply, (c) on selecting "Chat Message" directly. Confirmed **version-scoped, not pipeline-id-scoped** — `version_id` = `version_details.id`, distinct from the pipeline's own numeric id (observed live this session: pipeline id `5684` vs. version id `5807`). No existing API client surfaces this id; if waiting on the response directly (recommended over a fixed sleep), match the URL by a regex on `/pipeline_trigger/prompt_lib/{project_id}/pipeline/` rather than hard-coding the version id.
- `GET ${ELITEA_API_BASE}/elitea_core/pipeline_trigger/prompt_lib/${PROJECT_ID}/pipeline/{version_id}/trigger` — refetches after the PUT above (RTK-query cache invalidation); this refetch is what the Trigger select's displayed text is waiting on — see the polling note in Automation Hints.
- `PUT ${ELITEA_API_BASE}/elitea_core/application/prompt_lib/${PROJECT_ID}/{pipeline_id}` — fires on the pipeline's own "Save" click (`201` on success); this is the SEPARATE mutation that persists node-graph changes (adding nodes, changing the entry point) — the Trigger *value* itself does not depend on this endpoint at all, confirmed live: adding a `Code` node and calling "Make entrypoint" without clicking pipeline Save was silently lost on a fresh navigation in this session (had to redo it) — see Known Defects for why this is not filed as a bug.

## Known Defects Found During Exploration

**None found in the entry-point Trigger feature itself.** All 9 case steps produced the expected result across both a Chat-Message-default LLM node and a promoted Code node: exactly 3 trigger types listed, Webhook/Schedule/Chat-Message all selectable, each persisting correctly through Save + full reload, and the dropdown available regardless of entry-point node type.

Two observations worth flagging to the implementer, neither a defect:

- **Toast-vs-display-update lag (~1–2s) on Schedule Apply and on a direct Chat-Message reselect** — the success toast fires before the Trigger select's own displayed text updates to the new value (RTK-query cache-invalidation + refetch round-trip). The Webhook flow did not show this lag in this session (likely because its auto-save + refetch already completed earlier, before Apply was even clicked). Final state was correct in every case; only the visual update timing varies. Not filed as a defect — a real user glancing at the screen a moment after clicking would never notice; this only matters for automation's assertion timing (see Automation Hints).
- **Node-graph changes (add node / change entry point) require the pipeline's own "Save" click to persist** — distinct from the Trigger dropdown's own dedicated auto-save endpoint. Making a node the entry point and then navigating away without clicking Save silently discards that change (confirmed: had to redo the Code-node-as-entrypoint step after an unrelated browser-instance restart mid-session lost the unsaved state). This is consistent, documented, expected pipeline-editor behavior (mirrors how adding/deleting/renaming any node already requires Save) — not specific to this feature, not a defect.

## Blocked Steps

None. All 9 case steps were executed to completion against the live local environment, on both an LLM entry-point node and a Code entry-point node.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (per `.agents/testing.md`). **This case requires `add-data-testid` work** — 7 new testids across 3 files (`TriggerTypeSelector.jsx` ×1, `PipelineScheduleModal.jsx` ×3, `PipelineWebhookModal.jsx` ×3, one of which is a `testId` prop yielding 3 dynamic sub-testids) — see Concrete Handles for exact wiring points. All underlying mechanisms already exist except the `RadioButtonGroup.jsx` `testId` prop, whose own promotion-to-`main` status is a separate, already-noted PROVENANCE caveat.
- Reuse, don't rebuild: `PipelineDetailPage.add_node()`, `.make_node_entrypoint()`, `.get_entrypoint_node_id()`, `.wait_for_node_on_canvas()`, `.save_and_wait_for_update()` (already waits on the pipeline-Save `201` response) all already exist and cover everything in this case EXCEPT the Trigger select itself and the two settings modals. The Trigger select's own options reuse the existing `SELECT_OPTION = '[data-testid="select-option-{}"]'` class constant already on `PipelineDetailPage` — no new dynamic-testid pattern needed for them.
- New page-object surface needed on `PipelineDetailPage`: methods to open/read/select the entry-point Trigger select (mirroring the existing `open_mcp_node_toolkit_select()` / `get_mcp_node_toolkit_value()` / `select_mcp_node_toolkit()` triad), plus a small pair of helpers for each settings modal (wait-for-visible via the new modal-root testid, read the default summary/radio state, click Apply via the new Apply-button testid).
- Wait strategy: **never assert the Trigger select's displayed text on the same tick as a click** — use Playwright's auto-retrying `expect(locator).to_have_text(...)` (or equivalent polling), since the display lags the underlying mutation's cache-invalidation by up to ~2s for the Schedule and Chat-Message flows (see Known Defects). For persistence checks (post-reload), wait for the entry-point-select's `GET .../pipeline_trigger/.../trigger` response (or the page's general network-idle) before reading its text, per this project's existing `wait_for_network()` convention.
- The Webhook Type radio's default-selected assertion should use `.is_checked()` on the new `pipeline-webhook-type-radio-github` testid, following the exact precedent already proven in `credential_create_page.py`'s `AUTH_METHOD_RADIO` pattern (testid lands on `FormControlLabel`, not the bare `<input>`, but `is_checked()` still resolves correctly through it).
- **Sequencing with ELITEA-2006**: both cases need the SAME `add-data-testid` work for the Trigger select / Webhook modal root / radio group / Apply button (see the family/cluster note in Metadata) — whichever implementer dispatch runs first should do that shared work once; the second should verify the names match this AFS's Concrete Handles table before re-running `add-data-testid` for the same elements.
