# Test Case: Entry Point Node — Trigger Types (Chat Message, Schedule, Webhook)

## Metadata
- **TMS ID**: ELITEA-2005
- **Priority**: l3 (medium — as authored in the source TMS case; project convention maps
  medium → `@pytest.mark.p2`, confirmed via `test-specs/artifacts/l3_bucket-name-validation-invalid-name-formats_ELITEA-1811.md` → `test_artifacts_bucket_name_validation_invalid_formats.py:42`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-03 (cluster dispatch with ELITEA-2006/2007/2008 —
  same live session, shared login/navigation/discovery; each case's steps executed and observed
  independently; the 4 cases diverge in STEPS, not only data, so each gets its own AFS per a
  shared `surface_key`)
- **Status**: ready-for-automation
- **surface_key**: `pipeline-entry-point-trigger`

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline exists with a single entry point node (no HITL/Printer/interrupts) — satisfied by
  the existing `pipeline_with_llm_id` fixture (`automation/fixtures/data_fixtures.py:154`), which
  creates a pipeline with exactly one LLM node ("LLM 1") connected to END. **Do not use the
  multi-node `create_pipeline_with_nodes()` helper for this case** — confirmed via the
  `_surface.md` digest's seeding gotcha: a hand-built multi-node pipeline loads with Save already
  enabled (dirty on first render), which would corrupt any assertion that depends on Save being
  disabled beforehand. `pipeline_with_llm_id` loads clean.

## Test Data
| Field | Value |
|-------|-------|
| Trigger options | Chat Message, Schedule, Webhook |

All three confirmed present, in this exact order, with `chat_message` selected by default on a
fresh pipeline.

## Test Steps

1. Use the `pipeline_with_llm_id` fixture (single LLM node, "LLM 1", connected to END — the
   fixture IS the "create a pipeline with a single entry point node" precondition). Navigate to
   the pipeline detail page and wait for the canvas.
   - **Verify**: canvas loads with exactly 2 nodes ("LLM 1", "END"); `pipelines.get_node_ids()`
     returns `["END", "LLM 1"]` (order not guaranteed — content is).
2. Click the "LLM 1" node (single node in the pipeline ⇒ it is the entry point by construction;
   `get_entrypoint_node_id()` — reads the saved `entry_point:` YAML field — confirms this,
   optional extra assertion).
   - **Verify**: the node body shows a "Trigger" label + combobox. Confirmed live: the combobox
     shows "Chat Message" by default, DOM `id="simple-select-undefined"` (no testid — see
     § Concrete Handles), positioned as the FIRST field inside the node body (before SYSTEM/TASK/
     CHAT HISTORY), so `node.locator('[id^="simple-select-"]').first` resolves to the Trigger
     select unambiguously even though 3 more `id="simple-select-Type"` selects exist further down
     the same node (SYSTEM/TASK/CHAT HISTORY Type selects — DOM order confirmed via a full
     `inner_html()` dump this session).
3. Open the Trigger combobox.
   - **Verify**: exactly 3 options render, in DOM order: `Chat Message` (`data-testid=
     "select-option-chat_message"`), `Schedule` (`data-testid="select-option-schedule"`),
     `Webhook` (`data-testid="select-option-webhook"`) — confirmed live via
     `page.locator('[data-testid^="select-option-"]')`. These testids already exist (see
     § Concrete Handles — inherited "for free" from the shared `SingleSelect` component's
     existing `select-option-{value}` auto-derivation, same mechanism already confirmed working
     for the MCP/Toolkit node dropdowns).
4. Select the "Webhook" option.
   - **Verify (network)**: a `PUT ${ELITEA_API_BASE}/elitea_core/pipeline_trigger/prompt_lib/
     {project_id}/pipeline/{pipeline_id}/trigger` fires IMMEDIATELY on selection (before any
     modal appears) and returns `200` with a body containing `type: "webhook"`,
     `webhook_type: "github"`, a generated `webhook_url`, and `secret_value` — confirmed live via
     response-body capture this session. **This PUT is what actually persists the trigger type —
     it fires on mere selection, independent of whether the user goes on to click Apply or
     Cancel in the modal that opens next** (see § Quirks — this matters for step 8 below).
   - **Verify (UI)**: the "Webhook settings" modal (`role="dialog"`) opens. **Wait for network
     idle / the GET response, not a fixed short timeout** — confirmed live that the modal's field
     set is INCOMPLETE for roughly 1.5–3s after opening (only Webhook-Type radios + description +
     Payload Format text are present at first paint; the Webhook URL / Secret Value sections
     render in only after a secondary `GET .../trigger` resolves and repopulates the RTK-Query
     cache the modal's props read from — see the ELITEA-2006 AFS § Quirks for the full mechanism
     and the exact wait condition). For THIS case (2005) it is enough to wait for the dialog and
     then Apply; the full field inventory is ELITEA-2006's job.
   - Click "Apply".
   - **Verify**: modal closes; the Trigger combobox now reads "Webhook".
5. Save is a no-op here — **confirmed live that the pipeline-level Save button (
   `[data-testid="agent-save-button"]`) stays DISABLED after a trigger change**, because the
   trigger is persisted through its own endpoint (step 4), not through the pipeline's general
   Save. Reload the page directly (no Save click needed/possible).
   - **Verify**: after reload, the Trigger combobox reads "Webhook" — confirmed live,
     `TRIGGER_AFTER_RELOAD == "Webhook"` in a fresh page load.
6. Select "Schedule" from the Trigger combobox (repeat steps 3–4's open/select mechanics; see the
   ELITEA-2007 AFS for the Schedule-modal-specific detail — for this case, Apply with the modal's
   *default* cron is sufficient).
   - **Verify (network)**: same `PUT .../trigger` pattern, this time with `type: "schedule"`
     (no immediate secret generation involved for Schedule, unlike Webhook).
   - Click "Apply".
   - **Verify**: modal closes; Trigger combobox reads "Schedule".
7. Reload.
   - **Verify**: Trigger combobox reads "Schedule" — confirmed live,
     `TRIGGER_AFTER_RELOAD == "Schedule"` after a fresh page load, and clicking the small clock
     icon that now renders next to the Trigger combobox (present only while `currentTriggerType
     === "schedule"`) reopens the Schedule modal showing "Schedule settings" — confirming the
     saved cron round-trips, not just the trigger `type` string.
8. Switch back to "Chat Message".
   - **Verify**: selecting `select-option-chat_message` when the combobox ALREADY effectively
     shows chat_message is a no-op in the source (`if (newType === currentTriggerType) return;`
     in `TriggerTypeSelector.jsx`) — **so drive this step from a state where Schedule (or
     Webhook) is the CONFIRMED CURRENT value** (e.g. immediately after step 7's reload, before
     doing anything else) to guarantee the click is a real state transition, not a silent no-op.
     Confirmed live: selecting Chat Message from a genuinely different current trigger fires the
     same `PUT .../trigger` pattern with `type: "chat_message"` and a `toastSuccess('Trigger
     updated to Chat Message')` — no modal opens for this option (only Schedule/Webhook open a
     modal). Combobox reads "Chat Message" immediately after (no async-field-population lag
     applies here — nothing to wait for since there's no modal).
9. Add a second node of a DIFFERENT type (Code) and make it the entry point via the node's
   3-dot menu → "Make entrypoint" (`PipelineDetailPage.make_node_entrypoint()`, already exists).
   - **Verify**: `get_entrypoint_node_id()` now returns the Code node's id. Click the Code node.
   - **Verify**: the SAME "Trigger" label + combobox renders inline on the Code node's body, with
     the SAME 3 options (Chat Message/Schedule/Webhook) — confirmed live,
     `CODE_NODE_TRIGGER_OPTIONS == ['Chat Message', 'Schedule', 'Webhook']`. Root cause confirmed
     by reading the source: `TriggerTypeSelector` is rendered from the NODE-TYPE-AGNOSTIC shared
     `NodeCard.jsx` base component (`{isEntrypoint && <TriggerTypeSelector .../>}` —
     `EliteaUI/src/[fsd]/features/pipelines/flow-editor/ui/nodes/BaseNode/NodeCard.jsx:42`), so
     this is true for every node type, not just LLM/Code — no further per-node-type verification
     needed for this case's purpose.

## Expected Results
- The Trigger combobox on the entry point node always offers exactly 3 options: Chat Message,
  Schedule, Webhook — the option elements themselves already carry stable
  `data-testid="select-option-{value}"` handles inherited from the shared `SingleSelect`
  component (no new testid work needed for the option list itself — only the combobox's OWN
  trigger element needs one, see § Concrete Handles).
- Selecting Schedule or Webhook opens a settings modal; Chat Message does not.
- Every trigger-type change persists through its own dedicated endpoint (`PUT .../trigger`),
  independent of the pipeline's general Save button — which the trigger change does NOT enable.
- The Trigger combobox (and the restriction logic in ELITEA-2008) is rendered by the SAME shared
  component for every node type that can be an entry point — confirmed for LLM and Code nodes
  live this session; the source confirms it is unconditional on node type.
- All persistence survives a full page reload.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: pipeline with single entry point node, no HITL/Printer/interrupts | setup exists | step 1 | step 1: node count/ids | asserted |
| 1 Create pipeline with single entry point node | Pipeline created with one node | step 1 | step 1 | asserted — via `pipeline_with_llm_id` fixture, not a raw UI create flow (see § Automation Hints for why this is preferred over authoring the pipeline via UI clicks) |
| 2 Click entry point node — locate Trigger dropdown, defaults to "Chat Message" | Trigger dropdown visible, default Chat Message | step 2 | step 2: combobox text | asserted |
| 3 Open Trigger dropdown — verify 3 options | All 3 options listed | step 3 | step 3: `select-option-*` count + text | asserted |
| 4 Select and Apply "Webhook" — dropdown updates, webhook settings appear | Dropdown shows Webhook, settings appear | step 4 | step 4: dialog open + Apply + combobox text | asserted |
| 5 Save — reload — verify Trigger shows "Webhook" | Webhook trigger persisted | step 5 | step 5: post-reload combobox text | asserted — **CLARIFICATION: there is no explicit "Save" action available/needed here — the pipeline-level Save button stays disabled after a trigger change, because the trigger persists through its own dedicated endpoint immediately on selection/Apply. The case's "Save pipeline" wording does not match the live product's actual persistence mechanism; the OBSERVABLE the case cares about (trigger survives reload) is still true and asserted** — see § Quirks. Not a defect. |
| 6 Select and Apply "Schedule" — dropdown updates, schedule settings appear | Dropdown shows Schedule, settings appear | step 6 | step 6: dialog open + Apply + combobox text | asserted |
| 7 Save — reload — verify Trigger shows "Schedule" | Schedule trigger persisted | step 7 | step 7: post-reload combobox text + modal reopen | asserted — same "Save" clarification as row 5 |
| 8 Switch back to "Chat Message" | Dropdown returns to Chat Message | step 8 | step 8: combobox text + PUT body | asserted — **added the no-op guard** (see Axis 2) |
| 9 Repeat with a different node type as entry point (e.g., Code node) — verify all 3 options still available | All 3 trigger types available regardless of node type | step 9 | step 9: `CODE_NODE_TRIGGER_OPTIONS` | asserted |
| Expected Final State: all 3 trigger types selectable, persist after save/reload, available for any entry point node type | — | steps 4–9 | steps 4–9 | asserted |
| Pass/Fail: all steps complete without errors; all 3 types selectable and persist | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 8 explicitly drives the "switch back to Chat Message" transition from a state where the
  CURRENT trigger is genuinely NOT `chat_message` (right after step 7's Schedule-persisted
  reload) — *added because `TriggerTypeSelector.jsx`'s `handleTriggerTypeChange` short-circuits
  as a no-op when `newType === currentTriggerType` (confirmed by reading the source), so
  selecting Chat Message from an ALREADY-effectively-chat_message state (e.g. due to a stale
  cached read) would silently pass an assertion without exercising the real code path. This is
  the same class of gap the project's `defect-filing` reverse-masking guard exists to catch —
  not itself a defect, but a real trap for a naively-written automated test.*
- Step 5/7's "Save" clarification is recorded directly in the Coverage Map disposition per the
  project's reverse-masking guard (`.agents/testing.md` — the case text is what's stale, not the
  product) rather than filed as a separate clarification ticket, since it doesn't block or change
  any of the case's own Pass/Fail criteria — the trigger DOES persist after reload exactly as the
  case expects, just via a different mechanism than "Save" implies.
- Step 9 additionally confirms the mechanism (shared `NodeCard.jsx` component, not per-node-type
  duplication) via a source read, not just a second live observation — *added so the implementer
  doesn't need to separately re-verify every node type; the "any node type" claim in the case's
  Expected Final State is backed by an architectural guarantee, not just two data points (LLM,
  Code).*

## Cleanup

1. All pipelines created during this session used the `pipeline_with_llm_id` fixture (function
   scope) — auto-deleted in its own teardown (`PipelineAPI.delete_pipeline()`). No manual cleanup
   needed; confirmed via normal pytest teardown completing without warnings across every
   exploration run this session.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| Trigger combobox (entry point node) | `node.locator('[id^="simple-select-"]').first` — confirmed the Trigger select is always the FIRST `simple-select-*` element inside the node body, ahead of the (also-unstable) `#simple-select-Type` ×3 selects further down | **NO `data-testid` — flag to `add-data-testid`.** The underlying `<SingleSelect>` component (`EliteaUI/src/[fsd]/shared/ui/select/SingleSelect.jsx`) ALREADY accepts a `dataTestId` prop that forwards to `data-testid` on the trigger element AND auto-derives `${dataTestId}-combobox` — **zero new component plumbing needed**, only wiring `dataTestId="pipeline-entry-point-trigger-select"` at the call site in `TriggerTypeSelector.jsx`'s `<SingleSelect ... />` (confirmed via source read, same "prop already exists, just needs wiring" pattern already documented for the HITL node's `InputSelect`/`SingleSelect` fields in the `_surface.md` digest). |
| Trigger option — Chat Message | `[data-testid="select-option-chat_message"]` | **Already exists** — inherited "for free" from `SingleSelectMenuItem.jsx`'s `data-testid={option.testId ?? `select-option-${option.value}`}` auto-derivation. No `add-data-testid` work needed for the 3 options. |
| Trigger option — Schedule | `[data-testid="select-option-schedule"]` | Already exists, same mechanism. |
| Trigger option — Webhook | `[data-testid="select-option-webhook"]` | Already exists, same mechanism. |
| Entry point node (generic) | `[data-id="{node_id}"]` (ReactFlow's own `data-id`, e.g. `"LLM 1"`, `"Code 1"`) / `[data-testid="rf__node-{node_id}"]` | Third-party ReactFlow widget wrapper, testid-only per the #579 sanctioned exception — already the project's established pattern for every node type. |
| "Make entrypoint" action | `PipelineDetailPage.make_node_entrypoint(node_id)` — already exists, uses the node's 3-dot menu → `role="menuitem"` name `"Make entrypoint"` | none needed — production page-object method, confirmed still correct live |
| Current entry point (read) | `PipelineDetailPage.get_entrypoint_node_id()` — already exists, parses the saved `entry_point:` YAML field | none needed |
| "+ Add node" button / node-type menu item | `PipelineDetailPage.add_node(node_type)` — already exists | none needed |

## Network Behavior

- `PUT ${ELITEA_API_BASE}/elitea_core/pipeline_trigger/prompt_lib/{project_id}/pipeline/
  {pipeline_id}/trigger` — fires on EVERY trigger-type selection (including Chat Message), body
  `{"type": "chat_message"|"schedule"|"webhook", ...}`. This is the sole persistence mechanism
  for trigger state — confirmed the pipeline's general `PUT .../application/prompt_lib/...`
  endpoint is NOT involved in trigger persistence at all.
- `GET ${ELITEA_API_BASE}/elitea_core/pipeline_trigger/prompt_lib/{project_id}/pipeline/
  {pipeline_id}/trigger` — fires on page load/reload AND again shortly after a webhook-type PUT
  (to repopulate the RTK-Query cache the modal reads from — see the ELITEA-2006 AFS for the full
  timing detail relevant to webhook field assertions). Wait for this GET's response (not a fixed
  timeout) before asserting the Trigger combobox's post-reload value.

## Known Defects Found During Exploration

**None filed against this case.** All 9 case steps produced the expected observable end-to-end:
all 3 trigger types are selectable, Schedule/Webhook open their respective modals, all changes
persist through reload, and the Trigger control is available on any entry point node type. Zero
console errors observed at any point. Zero failed (≥400) network requests observed.

One case-text CLARIFICATION (not a defect — reverse-masking guard, recorded directly in the
Coverage Map per row 5/7 above): the case's "Save pipeline — reload" wording does not match the
live product's actual persistence mechanism (trigger changes save immediately via their own
endpoint; the pipeline-level Save button stays disabled). The underlying observable the case
cares about — the trigger survives a reload — is true and asserted.

## Quirks observed live (shared across the ELITEA-2005/2006/2007/2008 cluster)

- **The Trigger combobox's visible text can read STALE for up to ~1–2s after certain actions**
  (e.g. right after clicking "Cancel" in the Webhook/Schedule modal) — confirmed live: reading
  `trigger_select.inner_text()` immediately after a Cancel click can show the PRE-selection value
  even though the backend already persisted the new type (the PUT in step 4 fires on mere
  selection, before the modal even opens). The combobox's displayed value is driven by
  `useGetPipelineTriggerQuery` (an RTK-Query GET), which does not always refetch/settle
  synchronously with the mutation. **Always assert persistence via a fresh page reload (or wait
  for the specific GET response), never via an immediate post-click DOM read**, for any assertion
  that must reflect the true backend state.
- **Clicking "Cancel" in the Webhook or Schedule modal does NOT revert the trigger TYPE** — it
  only discards in-modal-only changes (webhook sub-type selection, a pending secret
  regeneration; the cron expression edited but not yet Applied). The trigger type itself was
  already committed by the initial PUT the moment the option was selected from the dropdown, and
  Cancel has no corresponding "revert type" mutation. This is a real UX asymmetry (worth a
  CLARIFICATION note if the team wants "Cancel" to fully abort the trigger-type change — none of
  ELITEA-2005/2006/2007/2008's own Pass/Fail criteria test Cancel, so no ticket filed against this
  cluster) — confirmed live via network capture (only ONE `PUT .../trigger` fires across a
  select→Cancel sequence, with `type` already set to the new value).

## ⚠️ Prior Work Discovered Mid-Session — orchestrator attention needed

**A complete, working, previously-reviewed automation implementation for this exact cluster
already exists in this repo's git history, but is NOT reachable from the current tip of
`origin/automation/base`.** Discovered while dedup-checking before filing a defect (found
issues #1006/#1009/#1013/#1021 already filed against this exact surface by a prior pass) —
followed the trail into `gh pr list --search trigger` and confirmed via `git merge-base
--is-ancestor`:

| Case | PR | State | Base (per GitHub) | Merge commit | Reachable from current `origin/automation/base`? |
|---|---|---|---|---|---|
| ELITEA-2006 | [#1015](https://github.com/EliteaAI/elitea-testing-public/pull/1015) | MERGED (2026-07-24) | `automation/base` | `32fb6fe4` | **NO** |
| ELITEA-2005 | [#1022](https://github.com/EliteaAI/elitea-testing-public/pull/1022) | MERGED (2026-07-24) | `tests/ELITEA-2006-webhook-trigger-settings-modal` (stacked) | `29333bd8` | **NO** |
| ELITEA-2007 | [#1038](https://github.com/EliteaAI/elitea-testing-public/pull/1038) | **CLOSED, not merged** (2026-07-29) | `tests/ELITEA-2005-entry-point-trigger-types` (stacked) | — | N/A — never merged |
| ELITEA-2008 | none found | — | — | — | no prior PR located |

PR #1015's own GitHub metadata says its base was `automation/base`, yet its merge commit is
**not** an ancestor of the CURRENT `origin/automation/base` tip (`68e8f6f4`, 2026-08-03) — it
IS reachable from `origin/automation/base-merged` (a separate, older, diverged branch,
`a895133d`, 2026-07-24) and two unrelated feature branches. This strongly suggests
`automation/base`'s history was rewritten/reset at some point after 2026-07-24, orphaning at
least these two merged PRs (and possibly others merged in the same window) — a serious finding
given `.agents/workflow.md` documents `automation/base` as long-lived and never force-pushed.
**This analyst session did not attempt any git-history recovery or investigation beyond
confirming the above — that is squarely an orchestrator/lead-level decision, not an analyst
one.**

**Why this AFS still classifies `ready-for-automation` rather than `already-covered`**: per this
session's own contract, `already-covered`/`extend-existing` may target ONLY a spec/test merged
to the CURRENT `origin/automation/base` (or, for `extend-existing`, this batch's own trunk) — the
orphaned PRs satisfy neither, so the strict rule is followed and this case proceeds as fresh
`ready-for-automation` work. **But dispatching an implementer to redo this from scratch, without
first checking whether PRs #1015/#1022's actual code can simply be recovered and re-merged
(`git cherry-pick 32fb6fe4`/`29333bd8` onto a fresh `automation/base`-rooted branch, or a direct
branch-history investigation), risks pure duplicated effort for ELITEA-2005/2006** — both PRs'
own descriptions indicate essentially complete, testid'd, reviewed implementations covering the
same case observables this AFS documents. ELITEA-2007's closed PR #1038 also contains a
substantially complete implementation (same multi-select-checkbox finding this AFS independently
rediscovered live) that was abandoned only because its branch stack rested on the now-orphaned
ELITEA-2005 branch — recovering it may be far cheaper than a fresh implementation. ELITEA-2008
appears to have no prior implementation attempt.

**Recommendation for the orchestrator**: before dispatching implementers for this cluster,
have someone (lead or a dedicated git-recovery task) investigate why `automation/base` lost
these commits and whether `32fb6fe4` (ELITEA-2006), `29333bd8` (ELITEA-2005), and PR #1038's
branch tip (ELITEA-2007, closed but not deleted — check `tests/ELITEA-2007-schedule-trigger-settings-modal`
or similar for the actual head ref) can be cherry-picked/rebased onto current `automation/base`
directly, which would likely be far cheaper than fresh implementation for 3 of the 4 cases in
this cluster.

## Blocked Steps

None. All 9 case steps were executed to completion against the live local environment, across a
single LLM-entry-point pipeline plus a second entry-point-swap (Code node) verification.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` per `.agents/testing.md`. **This
  case requires `add-data-testid` work**: the Trigger combobox itself needs `dataTestId=
  "pipeline-entry-point-trigger-select"` wired at its `TriggerTypeSelector.jsx` call site (prop
  plumbing already exists in `SingleSelect` — zero new component code, just pass the prop). The 3
  option elements already have testids for free (see § Concrete Handles) — no work needed there.
- Use `pipeline_with_llm_id` (existing fixture) as the seed — it produces exactly the "single
  entry point node, no HITL/Printer/interrupts" precondition the case needs, with a clean
  Save-disabled baseline (see `_surface.md`'s seeding gotcha).
- Suggested new `PipelineDetailPage` methods (none exist today for the Trigger control):
  `open_entry_point_trigger_select(node_id)`, `get_entry_point_trigger_value(node_id)`,
  `select_entry_point_trigger(node_id, trigger_value)` (value ∈ `chat_message`/`schedule`/
  `webhook`, clicks the matching `select-option-{value}`), `close_trigger_modal(action="apply"|
  "cancel")`. Follow the existing `get_mcp_node_*`/`select_mcp_node_*` naming pattern already in
  `pipeline_detail_page.py`.
- Wait strategy: wait for the `PUT .../pipeline_trigger/.../trigger` response (`200`) before
  asserting the modal opened or the combobox text changed — not a fixed timeout. For
  post-Apply/post-reload persistence assertions, wait for the corresponding `GET .../trigger`
  response, not a fixed timeout either (see § Quirks — a too-short fixed wait produced false
  "reverted" reads multiple times during this exploration).
- Test-data fixture: `pipeline_with_llm_id` (existing). No new fixture needed for this case.
- Suggested pytest markers: `@pytest.mark.p2` (case priority `medium` → project convention, see
  Metadata), `@pytest.mark.pipelines`, `@pytest.mark.regression`.
- This case shares its Trigger-control mechanics with ELITEA-2006 (Webhook modal detail) and
  ELITEA-2007 (Schedule modal detail) — consider a shared test-module-level helper for
  open/select/wait-for-network rather than duplicating the interaction sequence 3×, but keep the
  3 as separate `test_*` functions (or parametrized cases) per their own AFS's Coverage Map, since
  their assertions differ meaningfully (this case: option availability + cross-node-type +
  persistence; 2006: modal field inventory + webhook-type URL switching; 2007: cron widget
  Default/Advanced mode + dynamic summary).
