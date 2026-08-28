# Test Case: Entry Point Node — Trigger Restricted When HITL/Printer/Interrupts Present

## Metadata
- **TMS ID**: ELITEA-2008
- **Priority**: l3 (medium — see ELITEA-2005 AFS Metadata for the medium→p2 convention citation)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-03 (cluster dispatch with ELITEA-2005/2006/2007)
- **Status**: ready-for-automation
- **surface_key**: `pipeline-entry-point-trigger`

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline exists with an entry point node — satisfied by `pipeline_with_llm_id` (same fixture
  as ELITEA-2005/2006/2007).

## Test Data
| Field | Value |
|-------|-------|
| (none required) | — |

## Test Steps

1. Use `pipeline_with_llm_id`. Navigate to detail page, wait for canvas, click "LLM 1".
   - **Verify**: baseline — Trigger dropdown offers all 3 options (`Chat Message`, `Schedule`,
     `Webhook`) — confirmed live, `_trigger_options() == ['Chat Message', 'Schedule', 'Webhook']`
     before any Printer/HITL/interrupt is added.
2. Add a Printer node (`pipelines.add_node("Printer")`) — **do not connect it to anything; the
   restriction is keyed purely on the node TYPE existing in the pipeline's `nodes:` list, not on
   graph connectivity** (confirmed via source read of `TriggerTypeSelector.jsx`'s
   `hasInteractiveNodes` check: `parsed.nodes.some(node => INTERACTIVE_NODE_TYPES.includes(
   node?.type))`, no edge/connectivity check involved).
   - **Verify**: `pipelines.get_node_ids()` now includes a `Printer 1` id.
3. Click the entry point node ("LLM 1") again and open the Trigger dropdown WITHOUT saving.
   - **CRITICAL PRECONDITION FINDING, confirmed live and NOT mentioned in the case text**: the
     restriction does **NOT** apply yet. `_trigger_options()` still returns all 3 options at this
     point — confirmed live, reproduced this session. Root cause confirmed via source read: the
     restriction (`hasInteractiveElements`) is computed from `values?.version_details?.instructions`
     — the pipeline's **last-SAVED** YAML — not from the live/unsaved ReactFlow canvas state. **The
     case's own steps never mention a Save action, yet the restriction is entirely gated on it** —
     this is the load-bearing precondition gap for this entire case; see § Known Defects for the
     CLARIFICATION filed against the case text.
4. Click the pipeline's Save button (`[data-testid="agent-save-button"]`).
   - **Verify**: `PUT .../application/prompt_lib/{project}/{pipeline_id}` returns `201`.
5. Click the entry point node ("LLM 1") again and open the Trigger dropdown.
   - **Verify**: **only "Chat Message" is available** — confirmed live, `_trigger_options() ==
     ['Chat Message']`, immediately after Save completes, WITHOUT needing a page reload (the
     restriction re-derives from the Formik `values.version_details.instructions` field, which the
     Save response updates in-place — confirmed live this session, no reload was needed for the
     restriction to kick in post-Save).
   - **Also verify (persistence)**: reload the page — restriction still holds
     (`_trigger_options() == ['Chat Message']` after a fresh page load too, confirmed live).
6. Remove the Printer node, add a HITL node instead (`pipelines.add_node("Human-in-the-loop")`),
   Save.
   - **Verify**: same restriction applies — `_trigger_options() == ['Chat Message']` after Save
     (same Save-gating as steps 3–5; not independently re-verified live this session for HITL
     specifically due to time, but the restriction check in the source is IDENTICAL for both node
     types — `INTERACTIVE_NODE_TYPES = [PipelineNodeTypes.Hitl, PipelineNodeTypes.Printer]`, a
     shared array checked by the same `.some()` call, confirmed via source read — see § Blocked
     Steps for the honest disposition of this sub-step).
7. Remove HITL, enable "Interrupt before" on a second (non-entry-point) node in the pipeline, Save.
   - **AMENDED DURING IMPLEMENTATION (docs(afs) commit, PR #1141 round 2) — "Interrupt after"
     substituted for "Interrupt before".** The case text (step 6) and this AFS originally said
     "Interrupt after"; the implementer found it unusable for this step: the pipeline builder
     auto-wires a freshly-added node's output to END, and `CommonInterruptSettings.jsx` disables
     the "Interrupt after" toggle whenever `transition === END` (confirmed live during
     implementation). "Interrupt before" has no such gate — it only disables when the node IS the
     saved entry point, which a freshly-added Code node never is. The substitution is
     spec-equivalent for this case's purpose: `hasInterrupts` (below) OR-combines
     `interrupt_before`/`interrupt_after` identically, so either array being non-empty produces
     the same restriction outcome the case is actually testing.
   - **Verify**: same restriction applies — confirmed via source read (`hasInterrupts` check:
     `Array.isArray(parsed.interrupt_before) && parsed.interrupt_before.length > 0) ||
     (Array.isArray(parsed.interrupt_after) && parsed.interrupt_after.length > 0)`), same
     `hasInteractiveElements` OR-combination as the node-type check — not independently
     re-verified live this session; see § Blocked Steps. Now live-executed by the implementer via
     `toggle_node_interrupt_before()` (green, `test_pipeline_entry_point_trigger_restricted_interactive_nodes.py`
     step 7).
8. Remove all HITL/Printer/interrupt configurations, Save, reload.
   - **Verify**: all 3 trigger types available again — confirmed live,
     `_trigger_options() == ['Chat Message', 'Schedule', 'Webhook']` after removing the Printer
     node + Save + reload (this exact round-trip WAS executed live this session, closing the loop
     on the Printer-node half of the restriction/un-restriction cycle).

## Expected Results
- The Trigger dropdown restricts to Chat-Message-only whenever the pipeline's **last-saved**
  version contains a Printer node, a HITL node, or a non-empty `interrupt_before`/`interrupt_after`
  list — evaluated as a single OR condition (`hasInteractiveElements`). **Implementation note
  (added round 2):** step 7 exercises this via `interrupt_before` specifically (the "Interrupt
  before" toggle) rather than `interrupt_after` — see step 7's amendment note for why "Interrupt
  after" is unusable on a freshly-added, auto-wired-to-END node. Both arrays feed the identical OR
  condition, so this substitution does not change what Expected Result is being verified.
- The restriction is keyed on the SAVED YAML, not the live unsaved canvas — adding a
  restricting element to the canvas has NO effect on the Trigger dropdown until Save.
- Once saved, the restriction takes effect immediately (no reload needed) and survives a reload.
- Removing all restricting elements + Save restores all 3 options.
- There is also an auto-reset mechanism (confirmed via source read, not independently exercised
  live this session — see § Blocked Steps): if a pipeline that currently has Schedule or Webhook
  selected gains a restricting element and is saved, the trigger auto-resets to Chat Message
  server-side with a toast ("Trigger reset to Chat Message (pipeline now contains interactive
  elements)").

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: pipeline with entry point node | setup exists | step 1 | step 1 | asserted |
| 1 Create pipeline with entry point + Printer node | Pipeline has both nodes | steps 1–2 | step 2: node ids | asserted |
| 2 Click entry point node | Config panel opens | step 3 | step 3 | asserted |
| 3 Open Trigger dropdown | Dropdown opens | step 3 | step 3 | asserted |
| 4 Verify only "Chat Message" available (Schedule/Webhook absent) | Only Chat Message listed | steps 3–5 | step 5 (POST-SAVE) | asserted — **CLARIFICATION, load-bearing: the case's own step sequence (add Printer → click node → verify restriction) never mentions a Save action, but the restriction is 100% gated on the pipeline being SAVED with the restricting element present — confirmed live the restriction does NOT apply to an unsaved canvas addition. This is not a defect (the product's actual contract — restrict based on the persisted version, not the working canvas — is a reasonable design), but the case text as written would produce a FALSE NEGATIVE if automated literally (asserting restriction right after adding the node, before Save, would find all 3 options still present and incorrectly fail/flag the case). Recorded here so the AFS's own steps insert the required Save before asserting restriction — see step 4.** |
| 5 Remove Printer, add HITL instead — verify same restriction | Only Chat Message with HITL | step 6 | step 6: source-code parity argument | asserted — **partial**, see § Blocked Steps for why this sub-step wasn't independently re-executed live |
| 6 Remove HITL, enable "Interrupt before" (amended from case's "Interrupt after" — see step 7 note) — verify same restriction | Only Chat Message with interrupt | step 7 | step 7: live-executed (`toggle_node_interrupt_before`) | asserted — live-executed round 2 (was source-code-parity-only at analysis time; see § Blocked Steps for the original disposition) |
| 7 Remove all HITL/Printer/interrupt — verify all 3 available again | All 3 types restored | step 8 | step 8: post-removal, post-Save, post-reload options | asserted — live-executed for the Printer-node cycle |
| Expected Final State: restriction applies for Printer/HITL/interrupt, restores when removed | — | steps 2–8 | steps 2–8 | asserted for Printer node fully; HITL/interrupt asserted via source-code parity, not independently live-executed (see § Blocked Steps) |
| Pass/Fail: trigger restricts correctly, restores when removed | — | all steps | all steps | asserted, with the HITL/interrupt caveat above |

### Axis 2 — Analyst additions

- Step 3's explicit "verify restriction does NOT apply pre-Save" check is an ADDITION beyond the
  case's own steps — *added because this is the single most consequential finding of this case:
  without it, an implementer following the case text literally (add node → immediately assert
  restriction) would write a test that either flakes or requires an accidental Save-before-assert
  ordering that isn't documented anywhere. Making the pre-Save non-restriction an explicit,
  asserted step turns an implicit trap into a documented, intentional part of the test.*
- The auto-reset-on-save-with-incompatible-trigger behavior (mentioned in Expected Results) is
  recorded from a source read (`TriggerTypeSelector.jsx`'s dedicated `useEffect` for this exact
  scenario) but NOT independently live-verified this session — *added as a forward-looking note
  for whoever eventually writes a case that starts from an ALREADY-scheduled/webhook pipeline and
  then adds a Printer/HITL node, since that's a meaningfully different precondition than this
  case's (which starts from Chat Message and never has an incompatible trigger to reset FROM).
  Not in scope for THIS case's own Pass/Fail criteria.*

## Cleanup

1. All pipelines created via `pipeline_with_llm_id` (function-scoped, auto-deletes in teardown).
   No manual cleanup needed — the Printer/Code nodes added mid-test are part of the SAME pipeline
   the fixture owns, so they're deleted along with it; no separate node-level cleanup required.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| Trigger combobox + options | see ELITEA-2005 § Concrete Handles (shared) | same |
| "+ Add node" → "Printer" / "Human-in-the-loop" menu items | `PipelineDetailPage.add_node("Printer")` / `add_node("Human-in-the-loop")` — already exist, confirmed exact display-name strings via `EliteaUI/src/[fsd]/features/pipelines/flow-editor/lib/constants/flowEditor.constants.js` (`PipelineNodeDisplayNames`) | none needed |
| Node deletion | `PipelineDetailPage.delete_node(node_id)` — already exists | none needed |
| Pipeline Save button | `[data-testid="agent-save-button"]` — confirmed present and functional (shared with every other pipeline-editing case in this suite) | none needed |
| "Interrupt before"/"Interrupt after" toggles | Present inline on every node body (confirmed on the LLM node this session, per its own field inventory — `Interrupt before`/`Interrupt after` `Switch` components), no dedicated modal | **CONFIRMED during implementation (round 2 amendment).** Actual testid is **node-ID-parameterized**, not node-type-parameterized as originally recommended here: `pipeline-node-interrupt-before-toggle-{node_id}` (`PipelineDetailPage.NODE_INTERRUPT_BEFORE_TOGGLE = '[data-testid="pipeline-node-interrupt-before-toggle-{}"]'`, `pipeline_detail_page.py:215`, formatted via `.format(node_id)`). Node-TYPE-parameterization (this AFS's original guess) would have collided across multiple same-type nodes in one pipeline — the id-keyed form is correct. Consumed via `PipelineDetailPage.toggle_node_interrupt_before(node_id)`. Relocated mid-implementation from the `MuiSwitch-switchBase` wrapper span onto the real `<input>` via `slotProps.switch.slotProps.input` (`EliteaAI/EliteaUI@85fe6ef3`) — MUI v7 silently drops a legacy `inputProps` testid. |

## Network Behavior

- `PUT .../application/prompt_lib/{project}/{pipeline_id}` (the pipeline's general Save, NOT the
  trigger-specific endpoint) — this is the request that actually changes the restriction's input
  data (`version_details.instructions`). Confirmed live: `201` response, and the Trigger
  dropdown's option set changes immediately after this response resolves, without needing the
  separate `GET .../trigger` call at all (the restriction logic reads Formik `values`, not the
  trigger-config query).
- Adding/removing a Printer/HITL node or toggling an interrupt switch on the LIVE canvas produces
  NO network traffic by itself — confirmed live, these are pure ReactFlow/ Formik client-state
  changes until Save is clicked.

## Known Defects Found During Exploration

**None filed as `bug`.** The restriction logic itself works exactly as the case's Expected Final
State describes — confirmed live for the Printer-node case end-to-end (restrict → un-restrict
round trip). Zero console errors observed. Zero failed (≥400) network requests observed.

**One CLARIFICATION worth filing** (per `.agents/profile.md` § Bug filing routing): the case text
never mentions that the pipeline must be SAVED before the restriction takes effect — a literal
reading implies the restriction reacts to the live canvas state. This is a genuine case-text gap
(reverse-masking guard: the live product's actual behavior — gate on the saved version, not the
working canvas — is confirmed correct/intentional via the dedicated `useEffect` auto-reset logic
that ALSO only fires on save-triggered data, so this is a consistent design choice, not an
oversight) that should be reflected in the TMS case text so a future manual tester isn't confused
by an apparent "nothing happened" result right after adding the restricting node. Filed as issue
— see reference once created by the orchestrator per the seeded bug-filing policy (this analyst
session did not file directly — see notes for routing, same as ELITEA-2006/2007).

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

**Partial live execution — time-boxed, not environment-blocked.** Steps 6 (HITL) and 7 (interrupt)
of the case were NOT independently re-executed live this session; their expected behavior is
asserted via a decisive source-code read (the SAME `hasInteractiveElements` check — a single
`.some()` over `INTERACTIVE_NODE_TYPES = [Hitl, Printer]` OR'd with a non-empty
`interrupt_before`/`interrupt_after` array — governs Printer, HITL, AND interrupts identically;
there is no per-node-type or per-restriction-source special-casing in the source). The
Printer-node half of the cycle (steps 1–5, 8) WAS fully live-executed, including the critical
pre-Save/post-Save/post-reload/un-restrict sequence, which is the part of this case that carries
real behavioral risk (the Save-gating precondition). The HITL and interrupt sub-cases are
mechanically identical per the source and carry materially LOWER risk of behaving differently
(same code path, different input data) — **the implementer should still independently execute
steps 6–7 live during implementation** (per this project's "AFS is a hypothesis until the
implementer's own green run" norm) rather than trusting this source-code argument alone; this AFS
does not claim steps 6–7 are DEFECT-FREE, only that their expected behavior is well-supported by
source and low-risk relative to step 4's Save-gating finding, which received full live coverage.

## Repair work order — the exact assertions to change (added 2026-08-26)

Target file (edit in place, no new spec):
`automation/tests/ui/pipelines/test_pipeline_entry_point_trigger_restricted_interactive_nodes.py`

| # | Current assertion (line) | Change to | Handle |
|---|---|---|---|
| 1 | Step 1 `baseline_options == ["Chat Message","Schedule","Webhook"]` (~L47) | **keep** the name-list check **and add**: all 3 options ENABLED | `[data-testid="select-option-{v}"]:not([aria-disabled="true"])` for `v ∈ {chat_message, schedule, webhook}` |
| 2 | Step 3 `pre_save_options == [...all 3...]` (~L73) | **keep** and add: all 3 still ENABLED (proves Save-gating, not just presence) | same as ① |
| 3 | **Step 5 `post_save_options == ["Chat Message"]` (L91 — the RED one)** | all 3 PRESENT; `chat_message` ENABLED; `schedule` + `webhook` **DISABLED** | `[data-testid="select-option-schedule"][aria-disabled="true"]`, same for `webhook`; `:not(...)` for `chat_message` |
| 4 | Step 5 `post_reload_options == ["Chat Message"]` (~L101) | same split as ③, after the reload | same as ③ |
| 5 | Step 6 `hitl_options == ["Chat Message"]` (~L120) | same split as ③ | same as ③ |
| 6 | Step 7 `interrupt_options == ["Chat Message"]` (~L146) | same split as ③ | same as ③ |
| 7 | **Step 8 `restored_options == [...all 3...]` (~L170) — currently inert** | all 3 PRESENT **and all 3 ENABLED** — this is the whole discriminating content of Step 8 now | `:not([aria-disabled="true"])` × 3 |
| 8 | final `assert not console_errors` | keep; consider migrating to `utils/console_errors.collect_console_errors()` while here (`.agents/testing.md` § Known issues — URL capture) | — |

Implementation notes:

- Add a `PipelineDetailPage` helper next to `get_trigger_options()` — e.g.
  `get_trigger_option_states(...) -> dict[str, bool]` returning `{value: is_enabled}` for the three
  known trigger values — so each step becomes one assertion on a dict instead of six locator checks, and
  the option state is read **while the dropdown is open**, in the same pass as the names.
- The state selectors are **UPPER_CASE class-level constants**, `.format(value)`-ed at the call site
  (`.agents/testing.md` § Locator policy, dynamic-testid pattern). No inline `get_by_test_id(f"…")`.
- **Do not** enumerate via `SELECT_OPTION_PREFIX` for the state check — per-value handles keep the test
  immune to Known Defect ① on both localhost and DEV.
- Enabled = attribute **absent**. Use `:not([aria-disabled="true"])` (or
  `expect(...).not_to_have_attribute("aria-disabled", "true")`), never `== "false"`.
- Docstring must be updated: the module docstring still describes the pre-EL-6128 hidden-option contract.
  State the new contract and cite EliteaAI/EliteaUI@cb70a64e.
- Nothing else about the test changes — same fixture, same 8 steps, same Save-gating, same
  `allure.step` wrapping, no new markers.

### Shipped — implementation record (2026-08-26, PR for issue #1802)

What actually landed, where it differs from the work order above. Amended by the implementer
per `.agents/role-overrides.md` § Implementer slot (the AFS states the SHIPPED truth).

**① The name-list half of rows ①/② was NOT kept — presence is asserted per value instead.**
The work-order table says "keep the name-list check and add the enabled check". Keeping
`get_trigger_options() == [...]` was not possible: that helper enumerates via
`SELECT_OPTION_PREFIX`, which on localhost also matches `select-option-selected-icon`
(Known Defect ① / issue #1806), so the name list reads
`['Chat Message', '', 'Schedule', 'Webhook']` and the assertion is RED on localhost while
green on DEV — reproduced live this session, and confirmed as pre-existing by a control run
against the unmodified page object. Widening the expectation to tolerate the `''` was
explicitly forbidden by the dispatch, and so was fixing the prefix here.

Shipped instead: `PipelineDetailPage.get_trigger_option_states()` returns
`{trigger_value: is_enabled}` read **per value**, and each step asserts one dict equality.
Presence is still asserted — a missing option is an absent key and fails the comparison —
so nothing is lost, and the test is immune to #1806 on **both** localhost and DEV. What
changes is the identity anchor: options are keyed by their testid value
(`chat_message`/`schedule`/`webhook`) rather than their display label ("Chat Message"/…).
That is the same identity the amended § Test Steps and § Concrete Handles already specify,
and it is the more stable of the two.

**② New implementation-time finding — the first click on the Trigger select after a full
page reload is SWALLOWED.** Not previously recorded in this AFS. Reproduced deterministically:
post-reload, `_select_node()` + click leaves the menu closed and the 10 s wait expires with
zero options; an immediate second click opens it (options then render correctly). Mechanism:
selecting the node remounts its config panel, replacing the Select element that the click had
already resolved. This is what made the first repair attempt fail 3/3 at Step 5 — an
infrastructure failure, NOT the product contract (the contract itself was confirmed live in
the same session: `{'chat_message': True, 'schedule': False, 'webhook': False}` post-Save).

Fixed in `open_trigger_select()`: wait `TRIGGER_SELECT_OPEN_PROBE_TIMEOUT` (3 s) for the menu,
and only if **no** option element exists at all (`count() == 0`, i.e. the click never landed)
re-click once and wait the full timeout. The `count() == 0` guard is load-bearing — it stops
the retry from clicking shut a menu that is merely rendering slowly. Strictly more robust than
the previous behaviour (it can only convert a timeout into a success), and the other caller
spec (`test_pipeline_entry_point_trigger_types_persist.py`) was re-run against it.

**③ Console-error capture migrated** to `utils/console_errors.collect_console_errors()` per
work-order row ⑧ and `.agents/testing.md` § Known issues, so a future occurrence of the
recurring background-resource noise class on this spec names the failing resource URL.

**④ `get_trigger_options()` is left in place, untouched** (additive-only on a shared page
object). It now has no caller in this spec but remains the public helper the rest of the
trigger cluster uses; it is the method #1806 will fix.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. This case needs NO new
  `add-data-testid` work of its OWN beyond what ELITEA-2005 already requires for the Trigger
  combobox (this case only reads the option LIST, doesn't need the Webhook/Schedule modal
  testids) — reuse ELITEA-2005's `dataTestId="pipeline-entry-point-trigger-select"` wiring.
- **The Save-before-assert ordering is the load-bearing detail** — any implementation MUST insert
  a Save (and wait for its `201`) between "add the restricting node" and "assert the Trigger
  dropdown restricted", or the assertion will read the WRONG (unrestricted) state. No reload is
  needed post-Save for the restriction to take effect (confirmed live), but a reload IS worth an
  additional assertion for persistence coverage (as done in step 5).
- Suggested new `PipelineDetailPage` helper: `get_trigger_options(node_id)` (open dropdown, read
  `[data-testid^="select-option-"]` texts, close via `Escape`) — reusable across all 4 cases in
  this cluster.
- Use `pipeline_with_llm_id` (existing fixture). No new fixture needed — this case builds its
  Printer/HITL/interrupt state entirely through the UI on top of the existing single-LLM-node
  seed.
- Suggested pytest markers: `@pytest.mark.p2`, `@pytest.mark.pipelines`, `@pytest.mark.regression`.
- Consider parametrizing the 3 restriction sources (Printer / HITL / interrupt) as 3 cases of one
  parametrized test function once the implementer independently confirms steps 6–7 live (per
  § Blocked Steps) — the restrict/un-restrict assertion shape is identical for all 3, only the
  node-add/interrupt-toggle setup action differs.
