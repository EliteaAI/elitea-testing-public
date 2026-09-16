# Test Case: Create Pipeline Version — Save, List, and Switch Preserves Canvas State

## Metadata
- **TMS ID**: ELITEA-2002
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-07
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard
  Keycloak login via `${TEST_USER}`).
- A pipeline exists with at least one saved ("base") version and NO nodes yet — created fresh
  per test via `PipelineAPI.create_pipeline()` (existing helper, `automation/api/client.py:616`),
  not via UI, to keep the flow's own steps (name/description entry) out of this case's assertions
  — Step 1 asserts pipeline creation itself only as a precondition-setup detail; the case's real
  observable is versioning (Steps 3–6). **Do NOT use `create_pipeline_with_nodes()`** — the
  digest's "Seeding gotcha" (`test-specs/pipelines/_surface.md`) warns it seeds Save/Discard
  already-enabled (empty `pipeline_settings.nodes`/`edges`), which would make Step 2's "Save
  becomes enabled after adding a node" trivially true for the wrong reason. `create_pipeline()`
  (zero-node, real empty `pipeline_settings`) is confirmed live this session to load with
  Save/Save-As-Version/Discard correctly **disabled** (clean baseline).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Dedicated pipeline via `PipelineAPI.create_pipeline(name=f"autotest_ver_<8hex>", description=...)`
  — name kept ≤32 chars total per the digest's confirmed `MAX_NAME_LENGTH` truncation gotcha
  (e.g. `autotest_ver_a1b2c3d4` = 22 chars, safe).
- Version name for Step 3: literal `v1_test` (per case text) — no uniqueness constraint observed
  on version names within a pipeline (confirmed live: dialog Save button only gates on
  non-empty Name, no duplicate-name validation surfaced in this session; if a future run reuses
  a pipeline this could matter, but per-test-dedicated pipelines above make it moot).

## Test Steps
1. Precondition-setup — create a dedicated pipeline via `PipelineAPI.create_pipeline()`, navigate
   to its detail page (`/pipelines/all/{id}?destTab=configuration&viewMode=owner`).
   - **Verify**: VERSION selector (`agent-version-selector-trigger`) shows `"base"`; Save
     (`agent-save-button`) and Discard (`discard-button`) are disabled (clean baseline);
     Save As Version (`agent-save-as-version-button`) is **enabled** — corrected during
     implementation (2026-08-07): `ApplicationTabBar.jsx` (source read) passes
     `SaveNewVersionButton` no `disabled` prop, so it is never gated on form dirtiness —
     it stays available at any time (only mid-request state disables it), unlike Save/
     Discard. Re-verified live on a fresh zero-node pipeline (immediate + after a 3s
     settle). See `test-specs/pipelines/_surface.md`'s 2026-08-07 CORRECTION bullet.
2. Click the canvas "Add node" button (`pipeline-add-node-button`) → click the "LLM" menu item
   (`pipeline-add-node-menu-item-llm`).
   - **Verify**: exactly one `[data-testid^="rf__node-LLM"]` element renders on canvas; Save
     becomes enabled (dirty state). (Save As Version was already enabled per the corrected
     step 1 baseline — not re-asserted here as a "becomes enabled" transition; it remains
     enabled through this step.)
3. Click "Save As Version" (`agent-save-as-version-button`).
   - **Verify**: the "Create version" dialog opens — Name input (`agent-version-dialog-name-input`)
     visible, Save button (`agent-version-dialog-save-button`) disabled while Name is empty.
   - Type `v1_test` into the Name input, click the dialog's Save button.
   - **Verify**: the Information panel's version id (`copy-version-id`) changes (new version
     created — see Automation Hints for how to wait for it); VERSION selector
     now shows `"v1_test"`; the LLM node added in Step 2 is still present (1 `rf__node-LLM*`
     element) — i.e. the edit is preserved in the new version, not reset; Save (main) returns to
     disabled (persisted, not a dangling local edit).
4. Open the VERSION dropdown (click `agent-version-selector-trigger`).
   - **Verify**: both `version-option-base` and `version-option-v1_test` (dynamic
     `VERSION_OPTION` testid template, `[data-testid="version-option-{name}"]`) are present in
     the popper.
5. Click `version-option-base`.
   - **Verify**: VERSION selector text reverts to `"base"`; URL's version-id path segment reverts
     to the original (pre-Step-3) value; canvas shows **zero** `rf__node-LLM*` elements (the LLM
     node from Step 2 does not leak into `base` — versions hold independent canvas state).
6. Open the VERSION dropdown again, click `version-option-v1_test`.
   - **Verify**: VERSION selector text shows `"v1_test"`; URL's version-id path segment matches
     the Step-3 new-version id; canvas shows exactly one `rf__node-LLM*` element again (the node
     config is restored, not re-created empty).

## Expected Results
- `v1_test` version is created, listed in the VERSION dropdown alongside `base`, and persists the
  LLM node added before saving.
- Switching to `base` shows the original (node-less) topology; switching back to `v1_test` shows
  the LLM node again — each version's canvas state is independently preserved and restored on
  selection, with no cross-version leakage in either direction.
- No console errors during the flow (see § Network Behavior — Save As Version is a plain
  synchronous create, not observed to be network-flaky in this session).

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1. Create a pipeline with name and description via UI | pipeline created and saved | step 1 | `step 1`: VERSION selector shows "base", form clean | asserted *(seeded via API, not UI — see note below)* |
| 2. Modify instructions (add + configure an LLM node) | node added/configured on canvas | step 2 | `step 2`: 1 `rf__node-LLM*` present, Save enabled | asserted |
| 3. Click "Save as Version", provide version name "v1_test" | version saved | step 3 | `step 3`: dialog fields, `copy-version-id` changes, Save re-disabled | asserted |
| 4. Verify "v1_test" appears in the VERSION dropdown | listed | step 4 | `step 4`: `version-option-v1_test` present alongside `version-option-base` | asserted |
| 5. Switch back to "base" version | canvas shows original topology (no LLM node) | step 5 | `step 5`: 0 `rf__node-LLM*`, URL version-id reverts | asserted |
| 6. Switch to "v1_test" | canvas shows the LLM node + its configuration | step 6 | `step 6`: 1 `rf__node-LLM*` again, URL version-id matches new version | asserted |

Note on Step 1: the case text says "via UI", but per the digest's "Two distinct pipeline form
surfaces" entry, creating via UI vs API produces an identical detail-page starting state for
this case's purposes (a saved, node-less "base" version) — API seeding is used here purely to
keep the test's assertions focused on *versioning* (the case's actual subject) rather than
re-proving pipeline-creation-via-UI, which is already covered by
`lextend_create-pipeline-minimal-sidebar_ELITEA-2020.md` / `test_pipeline_creation.py`. This is
the same "seed via API, exercise the case's actual behavior via UI" pattern
`test_agent_save_as_version.py` (agents' closely analogous ELITEA-1888) already uses.

**Axis 2 — Analyst additions**

- `step 1` asserts Save/Discard start disabled and Save As Version starts **enabled** —
  *added: confirms the clean API-seeded baseline before the dirty-state assertions in
  step 2 are meaningful (same "seeding gotcha" the digest already flags for a different
  pipeline case). Corrected during implementation (2026-08-07) — Save As Version is
  NOT dirty-gated (see step 1's note and the digest CORRECTION); asserting it enabled at
  baseline is still a meaningful guard, just not a "becomes enabled on edit" one.*
- `step 3` asserts the dialog's Save button is disabled while Name is empty — *added: a stable,
  cheap guard on the dialog's own validation, confirmed live this session, that the case text
  doesn't explicitly ask for but that guards the precondition for successfully typing "v1_test".*
- `step 3` asserts main Save returns to disabled after Save-As-Version — *added: confirms the
  new version is truly persisted (not a lingering unsaved edit), same distinction the Agents
  sibling test (ELITEA-1888) already asserts.*
- `step 5`/`step 6` assert the URL's version-id path segment in addition to the VERSION selector
  text — *added: confirmed live this session that switching versions changes
  `/pipelines/all/{pipeline_id}/{version_id}` — a second, independent signal beyond the trigger's
  textContent, cheap and load-bearing given the digest's own note elsewhere that trigger-text
  reads can lag ~1–2s behind the true state on other version-consuming pages.*

## Cleanup
1. Delete the dedicated pipeline via `PipelineAPI.delete_pipeline(pipeline_id)` (deletes all its
   versions together — confirmed via existing sibling tests' cleanup pattern, e.g.
   `test_agent_save_as_version.py`'s `agent_api.delete_agent()`).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`) — no role/label/CSS ladder. All handles below are `data-testid`
(static or dynamic-template) or a sanctioned #579 third-party-widget exception (ReactFlow node
wrapper). All were exercised live this session (2026-08-07) against
`http://localhost:5173/pipelines/all/8066` (probe pipeline, since deleted).

| Element | Testid (recommended locator) | Notes / fallback |
|---|---|---|
| VERSION selector trigger | `agent-version-selector-trigger` | Already a `PipelineDetailPage.version_selector` `LocatorDescriptor` field + `get_version_display()` method — reuse unmodified. Threaded via `testId` PROP (`ApplicationVersionSelect.jsx:228`), NOT a literal `data-testid=` string — see digest's two-stage-grep caveat if re-verifying provenance. |
| "Save As Version" button | `agent-save-as-version-button` | **No `PipelineDetailPage`/`PipelineFormPage` field yet — needs adding.** Confirmed live present + correctly enabled/disabled with dirty state; shared `SaveNewVersionButton.jsx` rendered via `ApplicationTabBar.jsx`, which `EditPipeline.jsx` uses (same component Agents already wires as `AgentFormPage.save_as_version_button`). Zero `add-data-testid` work needed — testid already exists in the DOM. |
| "Create version" dialog — Name input | `agent-version-dialog-name-input` | **Needs a `PipelineDetailPage` field** (mirrors `AgentDetailPage.create_version_name_input`). Confirmed live; `SaveNewVersionButton.jsx:120`. |
| "Create version" dialog — Save/confirm button | `agent-version-dialog-save-button` | **Needs a field** (mirrors `AgentDetailPage.create_version_save_button`). Confirmed live; disabled while Name is empty. |
| "Create version" dialog — Cancel button | `agent-version-dialog-cancel-button` | Not exercised this case (no cancel step) — exists per source (`SaveNewVersionButton.jsx:113`), add the field for completeness/consistency with `AgentDetailPage` but no test in THIS case calls it (per-role locator-touches-only rule — do not wire a method that calls it unless a case needs it). |
| "Create version" dialog — X close button | `agent-version-dialog-close-button` | Same as Cancel — not exercised, exists per source, don't add a call site. |
| VERSION dropdown option, by name (dynamic) | `[data-testid="version-option-{name}"]` (class constant `VERSION_OPTION`, e.g. `VERSION_OPTION.format("v1_test")`) | **Needs a `PipelineDetailPage` class constant** (mirrors `AgentDetailPage.VERSION_OPTION`). Confirmed live for both `version-option-base` and `version-option-v1_test`. |
| Add-node "+" button | `pipeline-add-node-button` | Already exists (`PipelineDetailPage`, ELITEA-2018/2030 work) — reuse unmodified. |
| Add-node menu item, LLM | `pipeline-add-node-menu-item-llm` (pattern: `pipeline-add-node-menu-item-{type}`) | Already exists — reuse unmodified. |
| Added LLM node on canvas | `[data-testid^="rf__node-LLM"]` (ReactFlow node wrapper, per-node-id suffix e.g. `rf__node-LLM 1`) | Sanctioned #579 third-party-widget exception (ReactFlow internal DOM) — same precedent already used elsewhere in this suite for node-presence checks. Use a `starts_with`/prefix count (`page.locator('[data-testid^="rf__node-LLM"]').count()`), not an exact id match, since the node's numeric suffix (`LLM 1` vs `LLM 2`) is assigned by the app, not the test. |
| Main Save button | `agent-save-button` | Pre-existing field. |
| Discard button | `discard-button` | Pre-existing field — **confirmed live present and correctly wired on the Pipeline detail page** (unlike the Agent detail page, where the digest notes this testid is NOT actually rendered — a pipeline-vs-agent divergence worth flagging to whoever eventually revisits the Agent-side gap). |

## Network Behavior
- No dedicated network call observed for Save As Version distinct from the pipeline's general
  persistence mechanism — confirmed via `browser_network_requests` was not separately isolated
  this session (time-boxed); the implementer should capture the actual request/response pair
  during implementation (Hard Rule per `test-automation-implementation`) and note it in the Run
  Report rather than assume none exists. Not a gap in THIS AFS's confidence about the UI-level
  observable (all six steps' UI state was independently confirmed via DOM reads + URL changes,
  which is what the case actually asks to verify).

## Known Defects Found During Exploration
None found. All six case steps executed cleanly end-to-end; zero console errors observed
throughout (`browser_console_messages`, level=error, 0 hits after the full flow).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, page object `automation/pages/pipeline_detail_page.py`
  (`PipelineDetailPage`, extends `PipelineFormPage`).
- **This case's own version-switching methods do not exist yet on `PipelineDetailPage`** — the
  implementer should port the pattern already proven on `AgentDetailPage`
  (`open_save_as_version_dialog()`, `confirm_new_version()`, `open_version_selector()`,
  `is_version_option_visible()`, `is_version_option_active()`, `close_versions_menu()`,
  `select_version_by_name()`, `get_version_selector_value()`) rather than inventing a new shape —
  same shared components (`SaveNewVersionButton.jsx`, `ApplicationVersionSelect.jsx`,
  `version.helpers.jsx`'s `version-option-{}` mechanism), same race conditions
  (`select_version_by_name()`'s trigger-text/URL convergence polling directly applies to the
  URL-version-id check this AFS's Steps 5–6 rely on).
- For the "canvas shows the LLM node" observable specifically (this case's addition over the
  Agent sibling, which only checks a text field), poll on the `rf__node-LLM*` count rather than a
  bare `is_visible()` — ReactFlow re-renders the canvas on version switch and a raw single-read
  can catch the node mid-unmount/mid-remount (same class of race as `select_version_by_name`'s
  own documented convergence-polling need).
- **Reading `copy-version-id` after a version change needs a convergence wait, not a bare read**
  (issue #1893): the VERSION trigger and the URL are not backed by Formik's `version_details`, so
  both can already show the new version while the Information panel still renders the PREVIOUS
  version's id (~660 ms window) — a bare read there returns a stale value and Step 3's
  "id changes" assertion compares an id with itself. Wait on the three-way convergence predicate
  (trigger text === name AND `copy-version-id` non-empty AND URL last segment === that id);
  `PipelineDetailPage.VERSION_CONVERGED_JS` implements it and `confirm_new_version()` applies it.
- Seed via `PipelineAPI.create_pipeline()` (zero-node) per the Preconditions note — do not reuse
  `create_pipeline_with_nodes()` or a shared/pooled pipeline (parallel test runs would corrupt
  each other's version list).

## Adjustment — 2026-09-09 (repair triage for `#2077`, nightly run 34331579791)

**Triage class: A — UI drift.** Same mechanism, same shared component and same testid as the
already-repaired Agent-side half (`#2052` / PR #2058); this is the pipelines half that PR
explicitly routed out of scope (`AgentDetailPage.close_versions_menu` docstring names it, and
so does PR #2058 § "Out of scope — for routing, not fixed here").

**Expected-result changes: NONE.** Nothing in § Test Steps, § Expected Results or § Coverage
Map changes. The case still verifies exactly what it verified before; only *how* the test
closes the VERSION dropdown and re-opens it changes.

### What the nightly actually did, per attempt (settled from allure, not inferred)

`caplog`/allure attachments accumulate the previous attempt's ERROR line across reruns, which
is why the reported traceback (Step 1) and the reported error text (Step 5's backdrop) came
from *different* attempts. Per-attempt truth, from
`allure-results-dev-stable-user3-114` (the pipelines shard):

| Attempt | UTC | Duration | Failed at | Cause |
|---|---|---|---|---|
| 1 | 09:12:07 | 21.6 s | **Step 5** — `select_version_by_name("base")` → `open_version_selector()` → `version_selector.click()` | `MuiBackdrop-root … from <div id="menu-"> subtree intercepts pointer events` — the VERSION dropdown Step 4 opened was never actually closed. **This is the defect.** |
| 2 | 09:12:44 | 16.8 s | Step 1 — `wait_for_detail_page_load()` (`input#name` never gets a value) | Branded full-page **500 Internal Server Error** gateway page (screenshot) — the platform outage that produced this run's sibling `[FIX]` cards (`#2074` et al.). Not this test. |
| 3 | 09:13:10 | 16.8 s | Step 1, identical | Same gateway 500 — attempt-2 and attempt-3 screenshots are **byte-identical** (`md5 4d92c1a87bb2df2e8e71fb4f5e4418a0`). |

Attempts 2–3 are class **D / environment**, not drift: by 09:17:51 the same shard was healthy
again (`test_delete_pipeline_version` failed 3/3 on the *backdrop* signature, not on a 500).
Nothing is owed for them beyond noting that `PipelineDetailPage.navigate()` swallows a
top-level non-OK status and surfaces it 15 s later as a wrong-subsystem `input#name` timeout —
which is exactly the suite-wide gap tracked as `#2089`, out of scope here.

### The mechanism, re-verified live on the PIPELINE surface (not transferred from the Agent case)

`ApplicationVersionSelect.jsx:230` is the single call site of the VERSION selector
(`testId="agent-version-selector-trigger"`), shared by Agents, Skills and Pipelines, and it
renders through `SingleSelect.jsx:662`
(`SelectDisplayProps={{ 'data-testid': `${dataTestId}-combobox` }}`) with the searchable
dropdown from `SingleSelectDropdown.jsx:40` (`<SimpleSearchBar onKeyDown={e => e.stopPropagation()} />`,
`SimpleSearchBar.jsx:13,30,41` — `autoFocus = true`, a 100 ms `setTimeout` re-focus, and an
Escape handler that clears the search box *before* calling the external `onKeyDown`).

Observed live on `http://localhost:5173/pipelines/all/9421` (2026-09-09, Playwright MCP), on
the pipeline detail page itself:

| State | Action | `aria-expanded` | options | backdrops |
|---|---|---|---|---|
| focus on the menu Paper | page-level Escape | `false` | 0 | 0 |
| focus in the **search field** | page-level Escape | **`true`** | 1 | 1 |
| same stuck state | page-level Escape **again** | **`true`** | 1 | 1 |
| same stuck state | Escape **on an option** (`Locator.press()`) | `false` | 0 | 0 — URL unchanged, trigger still reads `base` (no version selected) |

So a bare `page.keyboard.press("Escape")` is a coin-flip on focus, and retrying it fixes
nothing; pressing on an option is deterministic because `Locator.press()` focuses the element
first, so the keydown originates inside the `MenuList` and reaches MUI's `Modal`.

### Reproduction on DEV (the environment the nightly runs)

```
cd automation && AUTOMATION_DIR=$PWD DEV_ELITEA_URL=https://dev.elitea.ai \
  DEV_APP_PREFIX=/app PYTHONPATH=/tmp/devenv_harness HEADLESS=true \
  ../.venv/bin/pytest -p devenv "tests/ui/pipelines/test_pipeline_create_version.py::test_create_pipeline_version_save_list_switch_preserves_canvas_state" \
  -v -p no:cacheprovider --reruns=0 --log-cli-level=INFO
```
Target proven by the run's own INFO lines (`Authenticating via API against https://dev.elitea.ai`
· `redirected to https://dev.elitea.ai/app/` · `Navigating to https://dev.elitea.ai/app/pipelines/all/10404?viewMode=owner`).
Result: **1 failed in 37.03s**, `test_pipeline_create_version.py:146` (Step 5) →
`pipeline_detail_page.py:2168` `select_version_by_name` → `:2099` `open_version_selector` →
`Locator.click: Timeout 10000ms exceeded … MuiBackdrop-root … intercepts pointer events`.
Byte-identical to nightly attempt 1.

### Promotion-gap pre-check (class F ruled out)

After `git fetch origin` in `../EliteaUI`:

```
agent-version-selector-trigger      main:YES  testids:YES
version-option                      main:YES  testids:YES
origin/main:src/[fsd]/shared/ui/select/SingleSelect.jsx:662:  SelectDisplayProps={dataTestId ? { 'data-testid': `${dataTestId}-combobox` } : undefined}
```

Every handle the repair needs is on EliteaUI `main`. **No new testid is required.** (This
supersedes the stale note in `pipeline_detail_page.py`'s `version_selector` comment block,
which recorded `-combobox` as "`automation/testids` only, not yet on `main` as of 2026-08-07" —
it has been on `main` since PR #2058's window.)

### The adjustment (page-object only — no spec file changes)

All three call sites of `PipelineDetailPage.close_versions_menu()` drive the **same** VERSION
dropdown, so unlike `AgentDetailPage` (whose method is shared with the skill card's `Menu`,
forcing PR #2058 to add a new method) this class can be fixed **in place**:

1. **New class constants**, ported verbatim from `AgentDetailPage` with a cross-reference
   comment (matching the existing `VERSION_OPTION` precedent at `pipeline_detail_page.py:235`):
   - `VERSION_OPTION_ANY = '[data-testid^="version-option-"]:not([data-testid="version-option-pin-icon"]):not([data-testid^="version-option-set-default-"])'`
     — both exclusions verified applicable here (the pipeline dropdown renders the pin icon).
   - `VERSION_SELECTOR_COMBOBOX{,_EXPANDED,_COLLAPSED}` on
     `agent-version-selector-trigger-combobox` with an `[aria-expanded="…"]` state filter —
     the testid-keyed + state-attribute shape `.agents/testing.md` § Locator policy prescribes.
2. **`close_versions_menu()` gains a confirmed close** (signature becomes
   `(timeout: int = 5000, attempts: int = 3)`, both defaulted, so no caller changes):
   press Escape on `VERSION_OPTION_ANY.first` while the trigger still reports
   `aria-expanded="true"`; fall back to the page-level press only when zero options render;
   then require **both** `_COLLAPSED` attached **and** `expect(options).to_have_count(0)` before
   returning. The count term is not redundant — `aria-expanded` flips at the *start* of the MUI
   `Grow` exit transition while the backdrop survives it. On give-up, raise naming the live
   `aria-expanded` value and the remaining option count, so a genuine "this menu cannot be
   dismissed" defect fails *here* instead of as an unrelated click timeout downstream.
3. **`open_version_selector()` gains idempotence + a post-condition**
   (`timeout: int = 10000`, defaulted): click the trigger only while `_EXPANDED` is absent, then
   wait for `_EXPANDED`. Clicking an already-open dropdown cannot succeed by construction — the
   invisible backdrop intercepts it, which *is* the observed failure.

Nothing in the spec file changes; no assertion, count, threshold, comparison or step is touched.

### Shared-file regression protocol

`PipelineDetailPage.close_versions_menu()` — 3 call sites, all the VERSION dropdown:
`test_pipeline_create_version.py:140` (this case), `test_pipeline_delete_version.py:93` and
`:156`. `open_version_selector()` — `test_pipeline_create_version.py:133`,
`test_pipeline_delete_version.py:86,149`, plus internally in `select_version_by_name:2168`.
Both specs must be re-run after the change. `AgentDetailPage` / `SkillDetailPage` have their own
same-named methods and are untouched.
