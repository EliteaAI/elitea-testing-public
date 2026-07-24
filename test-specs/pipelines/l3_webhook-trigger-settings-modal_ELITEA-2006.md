# Test Case: Entry Point Node — Webhook Trigger Settings Modal

## Metadata
- **TMS ID**: ELITEA-2006
- **Linked Story**: none
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: none needed — localhost `VITE_DEV_TOKEN` auto-auths, no explicit login step
- **Analyst**: qa-engineer (agent), session 2026-07-24
- **Status**: ready-for-automation

**Browser-lane note:** lane 0 (shared Playwright MCP browser) was occupied by a
parallel analyst in this batch. This session used an ISOLATED `browser-verify`
(CDP) Chrome instance on its own `--remote-debugging-port=9422` +
`--user-data-dir=/tmp/chrome-cdp-elitea2006` per the parallel-front rule — no
shared-browser contamination with sibling cases (a `QA-ELITEA-2005-EntryTrigger`
pipeline already existed in the same `Private` project, presumably from a
sibling ELITEA-2005 analyst dispatch; left untouched, own throwaway pipeline
created instead — see Cleanup).

## Preconditions
- User is logged in to the Elitea platform (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline exists with an entry point node and no HITL/Printer/interrupts.
  **Clarification confirmed live:** a brand-new pipeline starts with ONLY an
  `End` node — there is no implicit "entry point" node. Adding ANY node type via
  "Add node" (LLM was used here) makes it the pipeline's `entry_point` (YAML:
  `entry_point: LLM 1`) automatically, the instant it's added, with no separate
  "set as entrypoint" step needed for a single-node pipeline. This matches
  `PipelineDetailPage.make_node_entrypoint()`'s existence for the *multi-node*
  case (explicitly re-designating a different node) but isn't needed here.

## Test Data

### reuse-existing
- `pipeline_with_llm_id` fixture (`automation/fixtures/data_fixtures.py:160`,
  via `PipelineAPI.create_pipeline_with_llm_node`) already creates a pipeline
  whose YAML is `entry_point: LLM 1` / `nodes: [{id: LLM 1, type: llm, ...}]`
  connected to `END` — i.e. exactly the precondition state ("entry point node,
  no HITL/Printer/interrupts"), confirmed byte-for-byte identical in
  `automation/api/client.py:707-719` to what this session built by hand via the
  UI. **Recommended setup** — skips the "Add node → LLM" round trip entirely
  since it isn't the case's own observable.
  - Alternative if "Add node → LLM" must be exercised literally: `pipeline_id`
    fixture (empty pipeline) + `PipelineDetailPage.add_node("LLM")` +
    `wait_for_node_on_canvas("llm")` — already proven by merged specs
    (`test_pipeline_advanced.py`'s `_add_llm_node_and_connect`); no new handle
    work needed for that step.

### Test Data values (from case)
| Field | Value |
|---|---|
| Webhook types | GitHub, GitLab, Custom |

## Test Steps

1. Create a pipeline with an entry-point node, no HITL/Printer/interrupts (see
   Test Data — `pipeline_with_llm_id` fixture).
   - **Verify**: pipeline is ready with a single entry-point node — confirmed
     live via the YAML view (`entry_point: LLM 1`) and the node card showing a
     "Trigger" field (only rendered when `isEntrypoint` is true, source-confirmed
     `NodeCard.jsx:42`).
2. Select "Webhook" from the Trigger dropdown.
   - **Verify**: confirmed live — the Trigger `SingleSelect` (default value
     "Chat Message") opens a 3-item list (`select-option-chat_message`,
     `select-option-schedule`, `select-option-webhook`); clicking
     `select-option-webhook` fires `updateTrigger` (`PUT
     .../pipeline_trigger/prompt_lib/{projectId}/pipeline/{versionId}/trigger`,
     source-confirmed) and opens the Webhook settings modal automatically —
     the Trigger select itself doesn't visibly flip to "Webhook" until the
     modal is later Applied (see step 6); this is correct per source
     (`handleTriggerTypeChange`'s `webhook` branch calls `updateTrigger` then
     `setIsWebhookModalOpen(true)`, matching live behavior exactly).
3. Verify "Webhook settings" modal opens with all listed elements.
   - **Verify**: confirmed live, ALL present —
     - Webhook Type radio buttons: GitHub / GitLab / Custom, **GitHub selected
       by default** ✓
     - Description text (updates per type, see step 4) ✓
     - Webhook URL read-only field with copy button ✓ (full value read live:
       `http://localhost:5173/api/v2/elitea_core/webhook/prompt_lib/399/5808/github`)
     - Secret Value masked field (`•`×N) with eye/copy/refresh buttons ✓ + helper
       text "Enter this secret in your GitHub webhook configuration under
       'Secret'" ✓. Eye toggle independently confirmed functional — clicking it
       revealed the real secret value inline (e.g.
       `Uwd6fAyqF4uA8QGTbkP3h9fcIesotlBVFmCtSv8327A`) and the helper text +
       Example Request block both updated to show the real value in place of
       the mask.
     - Payload Format description ✓ ("Send a POST request with any body
       content. The raw request body will be passed directly to the pipeline
       as user input.")
     - Example Request code block with copy button ✓ (a real `curl` command,
       type-specific — see step 4/5)
     - Cancel / Apply buttons ✓
     - Zero `[role="dialog"] [data-testid]` hits beyond MUI's own internal icon
       component names (`RadioButtonUncheckedIcon` etc., not real testids) —
       every element listed above has **no `data-testid` today** (see Concrete
       Handles).
4. Switch Webhook Type to "GitLab" — verify URL and description text update.
   - **Verify**: confirmed live — description changes to "Uses x-gitlab-token
     header with secret token"; URL changes to
     `.../webhook/prompt_lib/399/5808/gitlab` (only the trailing type segment
     changes, confirmed via `fullWebhookUrl`'s source derivation
     `webhookUrl.replace(/\/[^/]+$/, ...)`); Example Request block updates to
     the GitLab-specific curl form (`X-Gitlab-Token` header).
5. Switch to "Custom" — verify URL updates.
   - **Verify**: confirmed live — URL changes to
     `.../webhook/prompt_lib/399/5808/custom`; description changes to "Uses
     X-Webhook-Token header with secret token"; Example Request updates to the
     Custom curl form (`X-Webhook-Token` header).
6. Click "Apply" — verify modal closes, Trigger shows "Webhook".
   - **Verify**: confirmed live — modal closes, a green
     "Webhook configured successfully" toast appears, and the Trigger select
     now visibly reads "Webhook" with a link-icon "Edit webhook settings"
     button appearing next to it (only rendered when
     `currentTriggerType === 'webhook'`, source-confirmed). Zero console
     errors and zero failed network requests observed in the CDP capture
     window around this action (see Automation Hints for a tooling caveat on
     this observation's scope).
7. Save pipeline — reload — verify Webhook trigger persists.
   - **Verify**: confirmed live via a genuine Save → hard-reload round trip:
     clicked the page's Save button (`agent-save-button`, shared testid), hard
     `page.reload()`-equivalent, and the Trigger select still read "Webhook"
     with the edit-webhook icon present. Went further than the case's literal
     wording: reopened the Webhook settings modal after reload and confirmed
     the **Custom** radio was still selected (the specific webhook_type chosen
     in steps 4–5, not just the top-level trigger type) — i.e. the full
     sub-configuration persists, not only the coarse trigger=webhook flag.
     Persistence is server-side (confirmed via source: `useGetPipelineTriggerQuery`/
     `useUpdatePipelineTriggerMutation` hit a dedicated trigger endpoint, `GET`/`PUT
     .../pipeline_trigger/prompt_lib/{projectId}/pipeline/{versionId}/trigger` — see
     Network Behavior) — **NOT** part of the pipeline's own YAML/`instructions`
     field (confirmed: the YAML view after this whole flow still showed only
     `entry_point: LLM 1` / the LLM node's own `input_mapping`, no
     `trigger`/`webhook` keys anywhere).

## Expected Results
- A fresh pipeline's first added node automatically becomes the entry point and
  renders a Trigger field (no separate entrypoint-designation step needed for a
  single-node pipeline).
- Selecting "Webhook" from the Trigger select persists `type=webhook` server-side
  immediately (generates a secret) and opens the Webhook settings modal.
- The Webhook settings modal shows Webhook Type radio (GitHub default), a
  type-specific description, a read-only Webhook URL with copy, a masked Secret
  Value with working eye/copy/refresh, a Payload Format description, a
  type-specific Example Request code block with copy, and Cancel/Apply buttons.
- Switching Webhook Type live-updates both the URL (trailing path segment) and
  the description/example-request text — no page reload needed.
- Clicking Apply closes the modal, shows a success toast, and the Trigger select
  reflects "Webhook" with an edit-webhook icon.
- Save + hard reload preserves BOTH the top-level trigger type (`webhook`) AND
  the specific `webhook_type` sub-selection (`custom` in this run) — verified by
  reopening the modal after reload, not just reading the Trigger select's label.
- Zero console errors observed across the flow (see Automation Hints caveat).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create pipeline with entry point node, no HITL/Printer/interrupts | Pipeline ready with single entry point node | step 1 | step 1: YAML `entry_point: LLM 1` + Trigger field rendered | asserted |
| 2 Select "Webhook" from Trigger dropdown | Trigger dropdown updates to "Webhook" | step 2 | step 2: `select-option-webhook` click → modal opens | asserted *(the select's OWN displayed label flips to "Webhook" only after Apply, step 6 — see step 2's verify note; this is correct product behavior per source, not a defect)* |
| 3 Verify Webhook settings modal contains: type radios (GitHub default), description, URL+copy, Secret masked+eye/copy/refresh+helper, Payload Format description, Example Request+copy, Cancel/Apply | All listed elements present and correctly displayed | step 3 | step 3: each element individually confirmed live, incl. functional eye-toggle | asserted |
| 4 Switch to GitLab — URL and description update | URL/description reflect GitLab | step 4 | step 4: URL `.../gitlab`, description text confirmed | asserted |
| 5 Switch to Custom — URL updates | URL reflects Custom | step 5 | step 5: URL `.../custom`, description text confirmed | asserted |
| 6 Click Apply — modal closes, Trigger shows "Webhook" | Modal closes, entry point shows Webhook trigger | step 6 | step 6: toast + Trigger select label + edit icon | asserted |
| 7 Save — reload — Webhook trigger persists | Webhook trigger present after reload | step 7 | step 7: Trigger label after reload + reopened modal confirms `webhook_type=custom` persisted too | asserted *(enriched — see Axis 2)* |
| Expected Final State: modal fully functional, all elements present, type switching updates URL/description, trigger persists after reload | — | steps 3–7 | steps 3–7 | asserted |
| Pass/Fail: all steps complete without errors; modal contains all required elements; type switching updates URLs; trigger persists | — | all steps | all steps — zero console errors, zero failed network requests observed (tooling-scope caveat, see Automation Hints) | asserted |

### Axis 2 — Analyst additions

- Step 7 additionally asserts the SPECIFIC `webhook_type` (`custom`) survives
  reload, not just the coarse `trigger=webhook` flag — *added: the case's own
  wording ("Webhook trigger is present after page reload") is satisfied by the
  Trigger label alone, but that's the weaker of two persisted values; verifying
  the sub-selection too catches a regression where the top-level flag persists
  but the modal silently resets to its GitHub default on reload.*
- Noted (not asserted as a case requirement, filed separately) a MINOR,
  non-blocking DOM-id collision distinct from the already-filed `#1006`:
  `id="simple-select-undefined"` (the Trigger select's own native id, since
  its `SingleSelect` call passes no `label` prop) collides with an unrelated
  page-level control (the "Project: Private" switcher) — filed as
  `EliteaAI/elitea-testing-public#1009` — *added: directly relevant to this
  case's own locator choices (confirms why the implementer must use the
  `select-option-webhook` testid rather than the native id) and a genuinely new
  finding (broader blast radius than #1006), not a duplicate.*
- Verified the Secret Value's eye/copy/refresh buttons are all individually
  functional (not just visually present) — *added: the case's Pass/Fail
  criteria says "correctly displayed", which a static screenshot could satisfy
  without proving the controls actually work; clicking eye and confirming the
  real secret renders is a stronger, still-cheap check given the interaction
  was already live.*
- Confirmed (source + live) that trigger/webhook configuration is a SEPARATE
  server-side entity from the pipeline's own YAML `instructions` field —
  *added: this is load-bearing for the implementer's persistence-check design
  (must re-open the modal / re-fetch trigger state, NOT grep the YAML view like
  ELITEA-2004's LLM-node-fields case does) and easy to get wrong by analogy to
  that sibling case.*

## Cleanup

1. If the fixture-based setup (recommended, see Test Data) is used, cleanup is
   automatic via `pipeline_with_llm_id`'s existing teardown
   (`PipelineAPI.delete_pipeline`).
2. This analysis session's own manually-built pipeline
   (`QA-ELITEA-2006-WebhookModal`, id `5685`) was deleted via the UI's own
   "Delete pipeline" flow (three-dot menu → Delete pipeline → type-to-confirm)
   at the end of this session — confirmed gone from the Pipelines list
   afterward (re-navigated to `/pipelines/all` and grepped the page text for
   the pipeline name: zero hits).
3. Observational note (out of this case's cleanup scope, not actioned): other
   stray pipelines from sibling cases (`QA-ELITEA-2005-EntryTrigger`,
   `autotest_GAP007_fstring`, `GAP-007 f-string autocomplete`) are still present
   in the same `Private` project — left untouched since they belong to other
   cases, not this one.

## Concrete Handles (discovered during exploration)

**Fresh ground truth check (2026-07-24):** `cd ../EliteaUI && git fetch origin`
run immediately before this table; every handle below was grepped against BOTH
`origin/main` and `origin/automation/testids` after the fetch (all show
`needs-adding` — zero hits on either ref for every proposed name).

| Element | Recommended Locator | Provenance / Notes |
|---|---|---|
| Trigger select (root, on the entry-point node card) | **NO `data-testid` today.** Native id `#simple-select-undefined` (collides with an unrelated global control — see `EliteaAI/elitea-testing-public#1009`, do NOT use). **Flag to `add-data-testid`**: `SingleSelect.jsx` already accepts a `dataTestId` prop (confirmed source read, same mechanism already used for `pipeline-mcp-node-toolkit-select-combobox` and this session's own confirmed-in-source `pipeline-llm-node-input-select`/`-output-select`) — wiring point is `TriggerTypeSelector.jsx`'s `<SingleSelect value={currentTriggerType} onValueChange={handleTriggerTypeChange} .../>` call (~line 296): add `dataTestId="pipeline-trigger-select"`. Zero shared-component edits needed. Yields `pipeline-trigger-select` (root) + `pipeline-trigger-select-combobox` (the clickable display div, carries `aria-expanded`) for free. | needs-adding — on neither `main` nor `automation/testids` |
| Trigger option (open-listbox item, per value) | `[data-testid="select-option-chat_message"]` / `[data-testid="select-option-schedule"]` / `[data-testid="select-option-webhook"]` (existing `SELECT_OPTION` class constant in `pipeline_detail_page.py`) | on-main ✓ — confirmed live this session (`select-option-webhook` clicked successfully); same shared, already-proven mechanism used across the app (MCP toolkit/tool selects, LLM node Input/Output selects) |
| "Edit webhook settings" icon button (appears next to Trigger select once `trigger=webhook`) | **NO `data-testid` today.** Plain MUI `IconButton` with a `Tooltip` wrapper (title text "Edit webhook settings", not an `aria-label` on the button itself). **Flag to `add-data-testid`**: `TriggerTypeSelector.jsx`'s own `<IconButton onClick={handleWebhookIconClick} ...>` (~line 328) — this is a plain native element in the SAME file, so adding `data-testid="pipeline-trigger-webhook-edit-button"` directly needs no prop-threading through any shared component. | needs-adding |
| Webhook settings modal (dialog root) | **NO `data-testid` today.** `PipelineWebhookModal.jsx` renders via the shared `Modal.BaseModal`, which already accepts `data-testid` / `titleTestId` / `closeButtonTestId` props (confirmed source read, `BaseModal.jsx:32-38,125,139,150`) but `PipelineWebhookModal.jsx`'s own `<Modal.BaseModal>` call (~line 169) passes none of them. **Flag to `add-data-testid`**: add `data-testid="pipeline-webhook-modal"`, `titleTestId="pipeline-webhook-modal-title"`, `closeButtonTestId="pipeline-webhook-modal-close-button"` at that call site. Zero shared-component edits needed. | needs-adding |
| Webhook Type radio buttons (GitHub/GitLab/Custom) | **NO `data-testid` today.** Renders via `Checkbox.RadioButtonGroup`, which already accepts a `testId` prop and derives `${testId}-${value-slug}` per item (confirmed source read, `RadioButtonGroup.jsx:36-38` — e.g. `testId="pipeline-webhook-type-radio"` → `pipeline-webhook-type-radio-github` / `-gitlab` / `-custom`). **Flag to `add-data-testid`**: `PipelineWebhookModal.jsx`'s `<Checkbox.RadioButtonGroup value={selectedWebhookType} items={WEBHOOK_TYPE_OPTIONS} onChange={setSelectedWebhookType} />` (~line 183) is missing the `testId` prop — one-line addition, zero shared-component edits. | needs-adding |
| Webhook URL read-only field | **NO `data-testid` today.** Renders via `FormInput` (`@/components/FormInput`), a thin wrapper spreading `...props` onto MUI `TextField` — passing `data-testid="pipeline-webhook-url-input"` as a direct prop at the call site (~line 205) lands on the `MuiFormControl-root` (TextField forwards unrecognized props to its root, confirmed MUI behavior), which is sufficient to scope a nested `input` locator (`page.get_by_test_id("pipeline-webhook-url-input").locator("input")`) or read `.input_value()` via that scope. **Flag to `add-data-testid`**: one prop at the `<FormInput value={fullWebhookUrl} readOnly .../>` call site. | needs-adding |
| Webhook URL copy button | **NO `data-testid` today.** Plain `IconButton` in the same file (~line 214, `onClick={handleCopyUrl}`). **Flag to `add-data-testid`**: `data-testid="pipeline-webhook-url-copy-button"` — same-file native element, no threading needed. | needs-adding |
| Secret Value masked field | **NO `data-testid` today.** Same `FormInput` pattern as the URL field. **Flag to `add-data-testid`**: `data-testid="pipeline-webhook-secret-input"` at the `<FormInput value={showSecretValue ? ... : '•'.repeat(...)} readOnly .../>` call (~line 237). | needs-adding |
| Secret Value eye (show/hide) button | **NO `data-testid` today.** Plain `IconButton` (~line 246, `onClick={handleToggleSecretVisibility}`), swaps `VisibilityIcon`/`VisibilityOffIcon` by state — the icon SWAPS but this is an icon-only visual change on a single stable button, not a testid-carrying element, so no state-value-switched-testid concern applies (`.agents/testing.md` § Locator policy's outlawed pattern is about a `data-testid` VALUE flipping, not an icon). **Flag to `add-data-testid`**: one stable `data-testid="pipeline-webhook-secret-toggle-visibility-button"` regardless of shown/hidden state. | needs-adding |
| Secret Value copy button | **NO `data-testid` today.** Plain `IconButton` (~line 261, `onClick={handleCopySecret}`). **Flag to `add-data-testid`**: `data-testid="pipeline-webhook-secret-copy-button"`. | needs-adding |
| Secret Value regenerate (refresh) button | **NO `data-testid` today.** Plain `IconButton` (~line 272, `onClick={handleRegenerateClick}`). **Flag to `add-data-testid`**: `data-testid="pipeline-webhook-secret-regenerate-button"`. Functional note: clicking this does NOT immediately persist — it only stages a `pendingSecretValue` client-side (toast: "New secret generated. Click Apply to save.") until Apply is clicked; a test asserting regenerate must also click Apply to observe server-side persistence, matching this session's own read of `handleRegenerateClick`'s source. | needs-adding |
| Example Request code block | **NO `data-testid` today.** Rendered as a `Typography component="pre"` inside a plain `Box` (~line 328). **Flag to `add-data-testid`**: `data-testid="pipeline-webhook-example-request"` on the `Box` (or the inner `Typography`) — plain native elements in this same file, no threading needed. | needs-adding |
| Example Request copy button | **NO `data-testid` today.** Plain `IconButton` (~line 320, `onClick={handleCopyExample}`). **Flag to `add-data-testid`**: `data-testid="pipeline-webhook-example-copy-button"`. | needs-adding |
| Cancel button | **NO `data-testid` today.** `PipelineWebhookModal.jsx` uses a custom `actions={...}` render prop rather than `BaseModal`'s own `onConfirm`/`cancelButtonTestId` mechanism, so `BaseModal`'s existing testid props do NOT apply here — the `<Button variant="elitea" color="secondary" onClick={onClose}>Cancel</Button>` (~line 342) needs its OWN direct `data-testid="pipeline-webhook-cancel-button"` prop. **Flag to `add-data-testid`**. | needs-adding |
| Apply button | **NO `data-testid` today.** Same pattern — `<Button ... onClick={applyChanges} disabled={isLoading}>Apply</Button>` (~line 350) needs `data-testid="pipeline-webhook-apply-button"`. **Flag to `add-data-testid`**. | needs-adding |
| YAML view (used to confirm trigger config is NOT stored there — a negative-control check, not a locator this case's own assertions depend on) | `pipeline-yaml-editor` / `pipeline-yaml-lines` (`PipelineDetailPage.yaml_editor` / `.yaml_lines`, already `LocatorDescriptor` fields) + `get_yaml_content()` (already an existing method) | on-main ✓ — pre-existing page-object surface, zero new work; used only to VERIFY trigger state is absent from YAML, per Axis 2 |

## Network Behavior

- `GET /api/v2/elitea_core/pipeline_trigger/prompt_lib/{project_id}/pipeline/{version_id}/trigger`
  — fires on mount of any entry-point node card (`useGetPipelineTriggerQuery`,
  source-confirmed `applications.js:857-864`); returns the current trigger
  config (`type`, `webhook_type`, `webhook_url`, `secret_value`,
  `secret_header`, `secret_instructions`, `cron`, `timezone` depending on
  type).
- `PUT /api/v2/elitea_core/pipeline_trigger/prompt_lib/{project_id}/pipeline/{version_id}/trigger`
  — fires (a) immediately on selecting "Webhook" from the Trigger select
  (before the modal even opens — generates the secret server-side), and (b)
  again on clicking Apply inside the modal (persists the chosen `webhook_type`
  + optionally a regenerated secret). Source-confirmed
  `applications.js:865-876`; this is the same `TAG_TYPE` (`'PipelineTrigger'`)
  RTK-Query mutation both call sites use.
- **Tooling caveat (not a product-behavior note):** this session's
  `browser-verify`/`cdp.mjs` CLI wrapper spawns a fresh Node process per
  command, so its `consoleMessages`/`networkRequests` capture arrays are
  **module-level and reset every invocation** — a `get-console`/`get-network`
  call issued as a SEPARATE shell command from the action that triggered
  traffic only sees a brief (~500 ms) freshly-opened capture window, not the
  full session history. This session's repeated "zero errors" reads are
  therefore honest spot-checks over short windows (and the UI's own
  error-toast absence + successful reload/re-fetch are the stronger signal
  actually relied on for the "no defect" conclusion), not an exhaustive
  session-wide guarantee. **Does not affect the real Playwright/pytest
  suite** — its `page.on('console')`/`page.on('response')` listeners run
  inside the SAME long-lived browser context for the whole test and are
  unaffected by this analyst-tooling architecture. Logged as a durable
  tooling fact in qa-engineer memory for future `browser-verify`-lane
  analysts.

## Known Defects Found During Exploration

- None blocking. One new, non-blocking MINOR DOM-id collision filed:
  `EliteaAI/elitea-testing-public#1009` (`id="simple-select-undefined"` on the
  Trigger select collides with the unrelated Project-switcher control — see
  Axis 2 and Concrete Handles). Routes around cleanly via the existing
  `select-option-webhook` testid; no impact on this case's own automation.

## Blocked Steps

None. All 7 case steps were executed to completion against the live local
environment, including a genuine Save → hard-reload → re-verify round trip
(step 7) that went beyond the case's literal wording to also confirm the
specific `webhook_type` sub-selection persisted, not just the coarse trigger
flag.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`). **This case requires substantial `add-data-testid`
  work** — literally every interactive element in the Webhook settings modal,
  plus the Trigger select and its edit-webhook icon, lack a testid today; ALL
  have a trivial existing extension point (`dataTestId`/`testId` prop already
  supported by `SingleSelect`/`RadioButtonGroup`, or a direct `data-testid`
  prop on a same-file native MUI element) — none require editing shared-
  component internals. See Concrete Handles for exact line-level wiring
  points per element.
- New page-object surface needed: `automation/pages/pipeline_detail_page.py`
  currently has generic node methods (`add_node`, `wait_for_node_on_canvas`,
  `delete_node`, `make_node_entrypoint`) but nothing for the Trigger select or
  the Webhook settings modal. Suggested shape: `select_trigger_type(value)`
  (opens the Trigger select, clicks `select-option-{value}`), `open_webhook_settings()`
  (clicks the edit-webhook icon — only visible when trigger is already
  webhook), `select_webhook_type(value)` (clicks the radio via
  `RadioButtonGroup`'s testid convention), `get_webhook_url()` /
  `get_webhook_secret(reveal=False)` (read the two `FormInput` values, optionally
  clicking the eye icon first), `apply_webhook_settings()` /
  `cancel_webhook_settings()`.
- **Persistence check design — do NOT copy the ELITEA-2004 pattern verbatim.**
  That sibling case's fields live in the pipeline's own YAML `instructions`
  field, so its persistence check reads the `Yaml` tab. Trigger/webhook config
  is a SEPARATE server-side entity (see Network Behavior) — the YAML view will
  NEVER show it. The correct persistence check is: reload the page, then either
  (a) read the Trigger select's displayed label (`pipeline-trigger-select-combobox`
  text, once added) for the coarse check, or (b) reopen the webhook modal via
  the edit-webhook icon and read back the selected radio + URL/secret fields
  for the full sub-configuration check (this session did (b), recommended for
  a stronger assertion).
- Wait strategy: after clicking a Webhook Type radio, no network wait is
  needed for the URL/description update (pure client-side `useMemo` derivation
  off `selectedWebhookType`); after clicking Apply, wait for the success toast
  (`toastSuccess` text) or for the modal to actually close before asserting
  the Trigger select's new label — the `updateTrigger` mutation is awaited
  before `onClose()` fires (source-confirmed `applyChanges`'s `onSubmit(...)`
  → `onClose()` sequencing in `TriggerTypeSelector.jsx`'s
  `handleWebhookSubmit`), so waiting on modal-closed is sufficient, no fixed
  sleep needed.
- Recommended setup: `pipeline_with_llm_id` fixture (see Test Data) — already
  provisions a connected LLM entry-point node, saving a full node-add round
  trip while still exercising this case's own Trigger/webhook-configuration
  steps.
