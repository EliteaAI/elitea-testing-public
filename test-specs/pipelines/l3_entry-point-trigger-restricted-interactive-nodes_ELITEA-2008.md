# Test Case: Entry Point Node — Trigger Restricted When HITL/Printer/Interrupts Present

## Metadata
- **TMS ID**: ELITEA-2008
- **Priority**: l3 (medium — see ELITEA-2005 AFS Metadata for the medium→p2 convention citation)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-03 (cluster dispatch with ELITEA-2005/2006/2007)
- **Amended**: qa-engineer (agent), session **2026-08-26** — failure triage + repair spec after the merged
  test went RED on dev.elitea.ai (GHA run 32931571484). See § AMENDMENT — 2026-08-26 (EL-6128).
- **Status**: **extend-existing** — the merged spec
  `automation/tests/ui/pipelines/test_pipeline_entry_point_trigger_restricted_interactive_nodes.py`
  is repaired IN PLACE (assertions only); no new spec file. Amended here in place rather than emitted
  as a separate `lextend_*.md` by explicit dispatch instruction — the repair belongs with the case's
  own history, not in a second file.
- **surface_key**: `pipeline-entry-point-trigger`

## AMENDMENT — 2026-08-26 (EL-6128 product drift) — READ THIS FIRST

**Trigger.** GHA run [32931571484](https://github.com/EliteaAI/elitea-testing-public/actions/runs/32931571484)
(`UI Tests DEV Stable [main] [all]`, 2026-08-26, target **dev.elitea.ai**) — the merged test failed at
Step 5: `assert post_save_options == ["Chat Message"]` → got `['Chat Message', 'Schedule', 'Webhook']`.
Tracking issue #1802.

**Verdict: `product-drift` (intentional UI change), with consequent `case-drift`.** Not a product bug;
not a test defect at authoring time. The test asserted the contract that existed when it was written.

### What changed in the product

`EliteaAI/EliteaUI` · `src/[fsd]/features/pipelines/flow-editor/ui/settings/TriggerTypeSelector.jsx`,
three commits landed on `origin/main` 2026-08-24/25 (verified independently this session with a fresh
`git fetch origin`, not taken from the dispatch's pre-triage):

- EliteaAI/EliteaUI@cb70a64e — `feat: [EL-6128] restrict pipeline trigger to Chat Message for delegated OAuth toolkits`
- EliteaAI/EliteaUI@15099206 — `fix: [EL-6128] address review on delegated OAuth trigger restriction`
- EliteaAI/EliteaUI@07e0e9b1 — `refactor: [EL-6128] clarify credential gating, scope reset toast reason`

```diff
-    if (hasInteractiveElements) {
-      return TRIGGER_OPTIONS.filter(opt => opt.value === TRIGGER_TYPES.chat_message);
-    }
-    return TRIGGER_OPTIONS;
+    if (!restrictedToChatMessage) return TRIGGER_OPTIONS;
+    return TRIGGER_OPTIONS.map(opt =>
+      opt.value === TRIGGER_TYPES.chat_message ? opt : { ...opt, disabled: true },
+    );
```

Two distinct changes, only the first of which this case sees:

1. **Restricted triggers are now GREYED OUT IN PLACE instead of HIDDEN.** The option list is always all
   three; restriction is expressed as `disabled` on Schedule + Webhook. The `Trigger` label tooltip gained
   an explanatory sentence naming the cause.
2. The restriction predicate widened to `restrictedToChatMessage = hasInteractiveElements ||
   hasDelegatedOauthToolkit` (`useDelegatedOauthToolkits(values?.version_details?.tools, projectId)`).
   **Out of scope for ELITEA-2008** — this case's pipeline has no toolkits. Worth its OWN case
   (see § Known Defects → follow-ups).

**`hasInteractiveElements` itself is UNCHANGED** — still `YAML.load(values.version_details.instructions)`
→ `nodes.some(node => [hitl, printer].includes(node?.type))` OR non-empty
`interrupt_before`/`interrupt_after`. **So this AFS's original load-bearing finding — the restriction is
gated on the last-SAVED YAML, not the live canvas — survives EL-6128 intact and was re-confirmed live.**

### Live re-execution — full 8-step walk, 2026-08-26

Target `http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, which is **0 commits behind
`origin/main`** (verified after `git fetch origin`) and therefore carries EL-6128. Real pipeline created
through the project's own `pipeline_with_llm_id` fixture path; every step driven through the real UI
(node add/delete, real Save with its real `201`, real reload) and the open listbox's DOM dumped per step.
**No substitution of any kind** — see § Fidelity Declaration.

| Step | Option names rendered (DOM order) | `aria-disabled` per option |
|---|---|---|
| 1 baseline (nothing restricting) | Chat Message, Schedule, Webhook | none on any — all enabled |
| 3 Printer added, **NOT saved** | Chat Message, Schedule, Webhook | none on any — Save-gating intact |
| 4→5 Printer **saved** | Chat Message, Schedule, Webhook | Schedule `true`, Webhook `true`; Chat Message none |
| 5b after full page reload | Chat Message, Schedule, Webhook | Schedule `true`, Webhook `true` |
| 6 HITL saved (Printer removed) | Chat Message, Schedule, Webhook | Schedule `true`, Webhook `true` |
| 7 `interrupt_before` saved (HITL removed) | Chat Message, Schedule, Webhook | Schedule `true`, Webhook `true` |
| 8 all removed + saved + reloaded | Chat Message, Schedule, Webhook | none on any — all enabled again |

Restricted option, verbatim rendered DOM:

```html
<li class="MuiButtonBase-root Mui-disabled MuiMenuItem-root Mui-disabled MuiMenuItem-gutters ..."
    tabindex="-1" role="option" aria-disabled="true" aria-selected="false"
    data-value="schedule" data-testid="select-option-schedule" data-selected="false">
```

**An ENABLED option carries NO `aria-disabled` attribute at all** — absent, *not* `"false"`. The enabled
assertion must therefore be an absence/`:not(...)` check, never `to_have_attribute("aria-disabled","false")`.

Evidence (on disk): `test-results/screenshots/ELITEA-2008-step-01-baseline.png`,
`ELITEA-2008-step-05-post-save-restricted.png`, `ELITEA-2008-step-08-restored.png`.

**Steps 6 and 7 are now LIVE-EXECUTED.** This closes the § Blocked Steps gap the original analysis left
open (HITL / interrupt were previously argued from source parity only). § Blocked Steps is retained below
as history, marked resolved.

### Deployed-env cross-check (dev.elitea.ai) — partial, stated honestly

The GHA run above **is** dev.elitea.ai evidence and confirms the *presence* half: the deployed build
returns all three option names post-save, so EL-6128 is live on DEV. I could **not** independently read
`aria-disabled` on dev.elitea.ai from this session — the app sits behind Keycloak/OIDC
(`https://dev.elitea.ai/app/` → `302 .../forward-auth/auth_oidc/login`), so no anonymous DOM read was
possible, and the failing helper reads option *text*, not attributes. Not guessed, not asserted. The
presence change and the disable are produced by the *same* `availableTriggerOptions` map in the shipped
code, so they cannot be deployed apart.

### The trap this repair must not fall into

Under EL-6128 the option **name list** is `['Chat Message','Schedule','Webhook']` in the restricted state
**and** in the unrestricted state. Consequently:

- Step 5's old assertion is wrong (it asserts the pre-EL-6128 hidden-option contract), **and**
- Step 8's old assertion `== ["Chat Message","Schedule","Webhook"]` **no longer distinguishes anything** —
  it now passes identically against a still-restricted pipeline.

**A repair that merely relaxes Step 5 to "all three are present" deletes this case's entire subject while
staying green.** Confirmed and agreed. Every restriction checkpoint must assert the **enabled/disabled
split**, on BOTH sides of the restrict → un-restrict cycle. The amended steps below do exactly that.


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
   - **Verify (AMENDED 2026-08-26)**: baseline — the Trigger dropdown offers all 3 options
     (`Chat Message`, `Schedule`, `Webhook`) **and all 3 are ENABLED** (no `aria-disabled` on any).
     Re-confirmed live 2026-08-26 under EL-6128.
   - *Pre-EL-6128 this step asserted only the name list; the enabled half is new and is what makes the
     baseline distinguishable from the restricted state.*
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
   - **AMENDED 2026-08-26**: under EL-6128 the pre-Save observable is stated as *all 3 options present
     and all 3 ENABLED* — identical to the baseline. Re-confirmed live 2026-08-26: adding the Printer
     node to the canvas without saving leaves every option enabled.
4. Click the pipeline's Save button (`[data-testid="agent-save-button"]`).
   - **Verify**: `PUT .../application/prompt_lib/{project}/{pipeline_id}` returns `201`.
5. Click the entry point node ("LLM 1") again and open the Trigger dropdown.
   - **Verify (AMENDED 2026-08-26 — this is the assertion that went RED)**: all 3 options are
     **present**, and the restriction shows as an **enabled/disabled split**:
     `select-option-chat_message` **enabled**, `select-option-schedule` **disabled**
     (`aria-disabled="true"`), `select-option-webhook` **disabled** (`aria-disabled="true"`).
     Confirmed live 2026-08-26, immediately after Save completes, WITHOUT a page reload (the
     restriction re-derives from the Formik `values.version_details.instructions` field, which the
     Save response updates in-place — re-confirmed live, no reload needed).
   - **Also verify (persistence, AMENDED)**: reload the page — the same split still holds
     (Chat Message enabled, Schedule + Webhook `aria-disabled="true"`). Confirmed live 2026-08-26.
   - *Superseded: the pre-EL-6128 expectation `_trigger_options() == ['Chat Message']` (Schedule and
     Webhook absent from the DOM). That contract no longer exists.*
6. Remove the Printer node, add a HITL node instead (`pipelines.add_node("Human-in-the-loop")`),
   Save.
   - **Verify (AMENDED 2026-08-26)**: the same enabled/disabled split applies after Save —
     Chat Message enabled, Schedule + Webhook `aria-disabled="true"`.
     **Now LIVE-EXECUTED** (2026-08-26): previously this sub-step rested on a source-parity argument
     only (`INTERACTIVE_NODE_TYPES = [PipelineNodeTypes.Hitl, PipelineNodeTypes.Printer]`, one shared
     `.some()` call). It has now been driven end-to-end against the real UI — Printer deleted, HITL
     added, real Save, dropdown re-read — and produced exactly the split above. The § Blocked Steps
     caveat for this sub-step is **resolved**.
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
   - **Verify (AMENDED 2026-08-26)**: the same enabled/disabled split applies after Save —
     Chat Message enabled, Schedule + Webhook `aria-disabled="true"`. **Re-confirmed LIVE 2026-08-26**
     via the `interrupt_before` toggle on a freshly-added Code node.
   - *Original (pre-amendment) note:* same restriction applies — confirmed via source read (`hasInterrupts` check:
     `Array.isArray(parsed.interrupt_before) && parsed.interrupt_before.length > 0) ||
     (Array.isArray(parsed.interrupt_after) && parsed.interrupt_after.length > 0)`), same
     `hasInteractiveElements` OR-combination as the node-type check — not independently
     re-verified live this session; see § Blocked Steps. Now live-executed by the implementer via
     `toggle_node_interrupt_before()` (green, `test_pipeline_entry_point_trigger_restricted_interactive_nodes.py`
     step 7).
8. Remove all HITL/Printer/interrupt configurations, Save, reload.
   - **Verify (AMENDED 2026-08-26 — the silently-weakened assertion)**: all 3 trigger types are
     present **AND ALL 3 ARE ENABLED AGAIN** — no `aria-disabled` on Chat Message, Schedule or
     Webhook. Confirmed live 2026-08-26 after removing every restricting element + Save + reload.
   - ⚠️ **The name-list half of this assertion is now inert.** `['Chat Message','Schedule','Webhook']`
     is what a *restricted* pipeline renders too. The **enabled** half is the entire discriminating
     content of Step 8 under EL-6128 — dropping it turns this step into a no-op that cannot fail.

## Expected Results
### Expected Results — AMENDED 2026-08-26 (EL-6128)

- Whenever the pipeline's **last-saved** version contains a Printer node, a HITL node, or a non-empty
  `interrupt_before`/`interrupt_after` list, the Trigger dropdown **still lists all three options** and
  **disables the unattended ones**: `Chat Message` enabled, `Schedule` and `Webhook` rendered with
  `aria-disabled="true"` (+ MUI's `Mui-disabled` class). Restricted options are **greyed out in place,
  not hidden** — EliteaAI/EliteaUI@cb70a64e.
- The restriction is keyed on the SAVED YAML, not the live unsaved canvas (unchanged by EL-6128,
  re-confirmed live 2026-08-26).
- Once saved, the disabled state applies immediately (no reload needed) and survives a reload.
- Removing all restricting elements + Save + reload **re-enables** all three options (all three lose
  `aria-disabled`). The option *count/name list* is identical in both states and proves nothing on its own.
- An enabled option has **no `aria-disabled` attribute** (absent, not `"false"`).

### Expected Results — ORIGINAL (pre-EL-6128, superseded 2026-08-26, kept for history)

- ~~The Trigger dropdown restricts to Chat-Message-only whenever the pipeline's **last-saved**
  version contains a Printer node, a HITL node, or a non-empty `interrupt_before`/`interrupt_after`
  list — evaluated as a single OR condition (`hasInteractiveElements`).~~ **Implementation note
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

> **AMENDED 2026-08-26.** Rows below are as originally written; the EL-6128 dispositions are stated in
> the amended §§ Test Steps / Expected Results above and summarised here: **row 4** ("only Chat Message
> available / Schedule + Webhook do NOT appear") is now covered by the *enabled-vs-disabled split*, not by
> option absence; **row 7** ("all 3 available again") is now covered by *all 3 present AND all 3 enabled*
> — its name-list half no longer discriminates. Rows 5 and 6 (HITL / interrupt) are upgraded from
> "source-code parity" to **live-executed 2026-08-26**.

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

### Concrete Handles — AMENDED 2026-08-26 (with PROVENANCE)

Provenance verified 2026-08-26 with a fresh `cd ../EliteaUI && git fetch origin` **first**, then
`git grep -- "<t>" origin/main -- src/ | grep -iE '(data-testid|testid[[:space:]]*[:=])'` against
`origin/main` and `origin/automation/testids`. **`automation/testids` was 0 commits behind `origin/main`
at the time of the check.**

| Element | Handle (testid-only, class-level constant) | PROVENANCE |
|---|---|---|
| Trigger select (entry-point node) | `[data-testid="pipeline-entry-point-trigger-select"]` — existing `PipelineDetailPage.trigger_select` | **on-main ✓** |
| Trigger option, per value | `[data-testid="select-option-chat_message"]`, `…-schedule`, `…-webhook` — rendered by the shared template `` data-testid={option.testId ?? `select-option-${option.value}`} `` (`SingleSelectMenuItem.jsx:117`) | **on-main ✓** |
| Trigger option — **DISABLED** state | `'[data-testid="select-option-{}"][aria-disabled="true"]'` (UPPER_CASE class-constant template, `.format(value)`) | **on-main ✓** — emitted by MUI's own `MenuItem` from `option.disabled`; **no EliteaUI change required** |
| Trigger option — **ENABLED** state | `'[data-testid="select-option-{}"]:not([aria-disabled="true"])'` — the attribute is **absent** when enabled, so an absence/`:not()` filter is required (`to_have_attribute(..., "false")` would never match) | **on-main ✓** |
| Pipeline Save button | `[data-testid="agent-save-button"]` — existing `save_and_wait_for_update()` | **on-main ✓** |
| "Interrupt before" node toggle | `'[data-testid="pipeline-node-interrupt-before-toggle-{}"]'` — existing `PipelineDetailPage.NODE_INTERRUPT_BEFORE_TOGGLE`, `.format(node_id)` (`CommonInterruptSettings.jsx:146`) | **on-main ✓** |
| Node add / delete / canvas ids | existing `add_node()` / `delete_node()` / `get_node_ids()` / `wait_for_node_on_canvas()` | **on-main ✓** |

**NO new testids are needed for this repair.** Every handle it requires is already on `origin/main`,
so the repaired test goes green on **dev.elitea.ai** the moment it merges — no promotion gap, no waiting
on a human cherry-pick. That is a deliberate design constraint of this spec, not a coincidence: this
test runs in the DEV Stable GHA suite, and it is currently RED there.

#### 🚫 Handles the implementer must NOT use (they would re-break DEV)

| Handle | Why not | PROVENANCE |
|---|---|---|
| `[data-testid="select-option-*"][data-selected="true"\|"false"]` | Tempting (it is a clean `data-*` state attribute) but it exists **only** on `automation/testids` — added by EliteaAI/EliteaUI@b0a7d61a (2026-08-24, `test: [EL-2240] add select-option-selected-icon testid + data-selected state`). Using it would make the repair green on localhost and **red on dev.elitea.ai** until a human cherry-picks. | **on-`automation/testids` only** (awaiting human promotion to `main`) |
| `[data-testid="select-option-selected-icon"]` | Same provenance gap, **and** it is the cause of Known Defect ① below. | **on-`automation/testids` only** |
| `.Mui-disabled` class | MUI-internal CSS class, not a semantic attribute; `aria-disabled` carries the same signal and is the accessibility contract. | n/a |

#### Canon-gap declaration — `aria-disabled` as the state filter (§ declared-improvisation protocol)

`.agents/testing.md` § Locator policy (PR #581 ruling) says element **state** is asserted by filtering a
testid-keyed selector on a **`data-*`** attribute. The state this case must now read (`disabled`) is
exposed by MUI as **`aria-disabled`**, not as a `data-*` attribute. The canon is silent on ARIA-state
filters, so this is a **canon gap**, declared here rather than resolved silently.

- **Chosen:** `'[data-testid="select-option-{}"][aria-disabled="true"]'` — a testid-keyed selector with a
  semantic-attribute state filter. It satisfies the policy's *substance* (the testid is the identity, the
  attribute is the state, the element stays greppable for the coverage metric) and the reviewer's
  mechanical grep (the line carries a literal `[data-testid=`).
- **Why not add `data-disabled` to `SingleSelectMenuItem.jsx`** (which would be *literally* canon-compliant
  and would mirror the `data-selected` already added there): it would land on `automation/testids` only,
  so the repaired test would be **green on localhost and red on dev.elitea.ai** — reintroducing, as the
  fix for a DEV red, exactly the promotion gap that makes DEV reds expensive. It also edits a **shared**
  component for every select in the product to solve one case's problem.
- **This is a `how` decision, not a `what` decision** — it does not change, weaken, or drop any observable
  (§ declared-improvisation protocol ceiling). It is escalated as an open question (see § Open questions).

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

## Fidelity Declaration (added 2026-08-26)

**No substitutions of any kind — zero rows.** Every observable in the amended steps was produced by the
running system: real pipeline created through the project's own fixture API path (the same precondition
the merged test uses), real node add/delete through the ReactFlow canvas, real `PUT
.../application/prompt_lib/{project}/{pipeline_id}` Save with its real `201`, real full-page reload, and
the option state read from the real rendered DOM. No `page.route`, no `route.fulfill`, no
`page.evaluate`-injected state, no stubbed client. `page.evaluate` was used **read-only**, purely to dump
the already-rendered listbox DOM for evidence — it wrote nothing and drove no interaction. The repair
introduces no substitution either; the implementer must not add one.

## Known Defects / Findings — 2026-08-26 amendment

### ① `select-option-selected-icon` collides with the `select-option-*` option namespace (SUITE-WIDE, latent on `main`)

**Not** a product bug and **not** the cause of the DEV red — a separate, independent defect found while
re-executing. Reported to the lead for filing; **not filed by this analyst session** per dispatch
instruction (the lead owns issue #1802 and the board).

EliteaAI/EliteaUI@b0a7d61a (2026-08-24, on `automation/testids` only) added
`data-testid="select-option-selected-icon"` to the ✓ `ListItemIcon` **inside** the currently-selected
`MenuItem` (`SingleSelectMenuItem.jsx:141`). The page object enumerates options with

```python
SELECT_OPTION_PREFIX = '[data-testid^="select-option-"]'   # pipeline_detail_page.py:1580
```

so the checkmark icon matches the prefix and is counted as an option. `get_open_listbox_option_names()`
therefore returns a **spurious empty string** for whichever option is selected. Live-confirmed 2026-08-26:

```
Baseline on localhost: ['Chat Message', '', 'Schedule', 'Webhook']
                                        ^^ = select-option-selected-icon (text '', not a real option)
```

- **Blast radius:** every caller of `get_open_listbox_option_names()` / `SELECT_OPTION_PREFIX` — ~40
  references in `pages/pipeline_detail_page.py`, and specs including
  `tests/ui/pipelines/test_pipeline_entry_point_trigger_types_persist.py`,
  `tests/ui/pipelines_2/test_pipeline_mcp_node_change_toolkit_and_tool.py`,
  `tests/ui/pipelines_2/test_pipeline_mcp_node_empty_toolkit_before_attach.py`.
- **Today it bites localhost only** (the testid is not on `main`, hence the DEV GHA run saw a clean
  3-name list). **The moment a human cherry-picks b0a7d61a to `main`, it breaks on DEV too.**
- **Recommended root fix:** rename the icon's testid out of the option namespace in EliteaUI —
  e.g. `select-selected-check-icon` — before it is promoted.
- **Optional hardening (defence in depth):** tighten the enumeration to the option element itself,
  `'li[data-testid^="select-option-"]'` or `'[role="option"][data-testid^="select-option-"]'`.
- **Interaction with this repair:** the amended assertions are written per-value
  (`select-option-schedule`, `select-option-webhook`), not by enumerating the whole prefix family, so
  **the repaired ELITEA-2008 test is immune to this defect on both localhost and DEV.** That is
  deliberate — the repair must not depend on the collision being fixed first.

### ② Case-text drift — CLARIFICATION against ELITEA-2008 (recommended, not filed)

`../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/pipelines/ELITEA-2008_entry-point-node-trigger-restricted-hitl-printer.md`
still states the pre-EL-6128 contract:

- Step 4 action: *"Verify only 'Chat Message' is available (Schedule and Webhook **do NOT appear**)"*
- Step 4 expected: *"Only 'Chat Message' is **listed** in the Trigger dropdown"*
- Fail criterion: *"Schedule/Webhook options **appear** when they should be restricted"*

Under EL-6128 they **do** appear, by design, greyed out. Per the reverse-masking guard the **case text**
is what is stale, not the product ⇒ **CLARIFICATION, not a `bug`** (the #40 pattern). Recommended new
wording: *"Schedule and Webhook are listed but **disabled** (greyed out); only Chat Message is
selectable"*, and the fail criterion becomes *"Schedule/Webhook are **selectable** when they should be
restricted, or remain disabled after all restrictions are removed."* The case's step 6 also says
"Interrupt **after**" where the automation uses "Interrupt **before**" for the reason recorded in Step 7
above — worth folding into the same clarification.

### ③ Out-of-scope behaviour EL-6128 introduced (no case covers it) — follow-up candidate

`restrictedToChatMessage = hasInteractiveElements || **hasDelegatedOauthToolkit**`. A pipeline whose
saved `version_details.tools` include a toolkit authenticated by per-user delegated OAuth is now
restricted the same way, with a distinct tooltip naming the toolkits. **ELITEA-2008 does not cover this
and this repair does not add it** (different precondition — needs a delegated-OAuth toolkit fixture).
Recommended as a new TMS case rather than scope creep here.

### ④ Not asserted by this repair, on purpose — the explanatory tooltip

EL-6128 also appends a reason sentence to the `Trigger` label tooltip
(*"This pipeline contains HITL, Printer nodes, or interrupts that require user interaction. Only Chat
Message trigger is available."*). It is a genuine discriminating observable, but the info icon carries
**no testid** (`<span data-info-tooltip="true">` only), so asserting it would require a new EliteaUI
testid and therefore a promotion gap on a test that is currently red on DEV. Deliberately deferred;
noted here so the next person does not think it was overlooked.

## Open questions for a human (analyst recommendation attached)

1. **`aria-disabled` vs. adding `data-disabled`** — see § Canon-gap declaration above.
   *Recommendation:* ship the repair on `aria-disabled` (no promotion gap, DEV goes green immediately);
   optionally add `data-disabled` to `SingleSelectMenuItem.jsx` later as a canon-alignment change,
   decided together with the `select-option-selected-icon` rename since both touch that same file.
2. **Fix `select-option-selected-icon` before or after promotion?**
   *Recommendation:* **before.** It is a one-line rename on `automation/testids`, and fixing it after a
   cherry-pick means debugging a multi-spec DEV red instead.

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

> **RESOLVED 2026-08-26.** Steps 6 (HITL) and 7 (interrupt) were live-executed in the amendment session —
> Printer→HITL→`interrupt_before`→cleanup, each with a real Save and a real dropdown read. The
> source-parity argument below is superseded by direct observation and is kept only as history. No step of
> this case is blocked.

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

> **⚠️ Item ② is SUPERSEDED on `main` by PR #1929 (issue #1895, 2026-08-28) — it remains
> accurate for `automation/base`, which still runs the code it describes.**
>
> Item ② is kept as the dated record of what #1802 actually shipped. Its *mechanism* was
> later disproved by direct measurement, so do not go looking for a remount on `main`:
>
> - **The Select is NOT replaced.** It is present and genuinely `disabled` —
>   `TriggerTypeSelector.jsx` renders `disabled={disabled || isLoading}`, where `isLoading`
>   is `useGetPipelineTriggerQuery`'s `isFetching || isUpdating`. While that round-trip is in
>   flight after a page load, MUI's `SelectInput` ignores the mousedown.
> - **`force=True` skips Playwright's *enabled* actionability check**, so the click is
>   dispatched, silently does nothing, and the caller waits out the whole timeout on a menu
>   nothing ever asked to open. This is a repo-wide trap, not a quirk of this surface.
> - Measured on dev.elitea.ai: clicking while `aria-disabled="true"` was swallowed 3/3;
>   waiting for the enabled state first opened the menu in 1–2 ms, 5/5; the control enabled
>   46 ms after the `pipeline_trigger` GET finished. Observed disabled windows range from
>   0.002 s to **19.99 s** — so the 3 s probe *and* the 10 s budget described above were both
>   provably insufficient on a slow environment.
> - **The `count() == 0` guard described above could not do what this text claims** — it
>   samples the option count milliseconds before the click, so it cannot distinguish a
>   swallowed click from a slow-rendering menu.
>
> On `main`, `open_trigger_select()` is instead a state-driven, deadline-bounded loop with two
> separate budgets — a network-sized ready leg (`TRIGGER_SELECT_READY_TIMEOUT`, 30 s) and the
> caller's click/expand retry budget — that never clicks a disabled Select, re-reads
> `aria-expanded` before every click, and fails with a state-naming message. See
> `PipelineDetailPage.open_trigger_select()` and `test-specs/pipelines/_surface.md`.

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
