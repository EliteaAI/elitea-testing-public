# Test Case: Delete Pipeline Version — Falls Back to Base

## Metadata
- **TMS ID**: ELITEA-2003
- **Linked Story**: none
- **Priority**: high (case) / l2 (AFS prefix, matches sibling pipeline-version cases
  ELITEA-2002/ELITEA-2020)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), session 2026-08-08, campaign `pipelines-remaining`
  wave-02 (`.agents/automation/pipelines-remaining/cases/ELITEA-2003.md`)
- **Status**: ready-for-automation

## Snapshot-path note
This case's dispatch named `.agents/automation/pipelines-remaining-w2/cases/ELITEA-2003.md`,
which does not exist. The actual snapshot is at
`.agents/automation/pipelines-remaining/cases/ELITEA-2003.md` (no `-w2` suffix — the
campaign's single shared intake folder for all 7 waves, per
`.agents/automation/campaigns/pipelines-remaining.md`). Used that file; no TMS
re-fetch was needed. Flagging so the next dispatch in this wave isn't surprised.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs:
  standard Keycloak login via `${TEST_USER}`).
- A pipeline exists with at least one saved ("base") version — created fresh per test
  via the pre-existing `pipeline_id` fixture (`automation/fixtures/data_fixtures.py`,
  already used by the sibling `test_pipeline_create_version.py`/ELITEA-2002), not via
  UI, per Hard Rule 7 (reuse before create) — same precedent as ELITEA-2002.

## Test Data
### generate-per-test (via the `pipeline_id` fixture, cleaned up in its own teardown)
- Version name to create-then-delete: literal `ver_to_delete` (per case text).

## Test Steps
1. Navigate to the dedicated pipeline's detail page. Click "Save As Version"
   (`agent-save-as-version-button`) — confirmed live not gated on dirtiness (same
   shared `SaveNewVersionButton.jsx` behavior ELITEA-2002 already documented) — type
   `ver_to_delete` into the dialog's Name input (`agent-version-dialog-name-input`),
   click the dialog's Save button (`agent-version-dialog-save-button`).
   - **Verify**: the "Create version" dialog closes; the URL gains a new version-id
     path segment; the VERSION selector (`agent-version-selector-trigger`) now reads
     `"ver_to_delete"`; a `[data-testid="version-option-ver_to_delete"]` option exists
     alongside `version-option-base` in the VERSION dropdown (case Step 1's "appears
     in the VERSION dropdown" expected result).
2. (Folds into Step 1's own auto-navigation — see note below.) Confirm the app is
   currently ON the `ver_to_delete` version (VERSION selector text, URL version-id
   segment, and the Information panel's Version ID all read the new version's id).
   - **Verify**: all three signals agree on `ver_to_delete`'s id (case Step 2's
     "Canvas updates to show ver_to_delete content" — this pipeline has no nodes, so
     "canvas content" is expressed via the Information panel/URL/selector triad
     rather than node presence; see Known Defects/case-text note below).
3. Open the three-dot actions menu (`agent-actions-menu-button`) and click "Delete"
   under the VERSION group (`delete-version-menuitem`).
   - **Verify**: a "Delete confirmation" dialog opens (`delete-confirm-dialog`) with
     message text (`delete-confirm-message`) reading `"Are you sure to delete the
     ver_to_delete version? It can't be restored."` (case Step 3's "confirmation
     dialog opens").
4. Click the dialog's "Delete" button (`delete-confirm-button`).
   - **Verify**: the confirmation dialog closes; a `DELETE
     .../elitea_core/version/prompt_lib/{project}/{pipeline_id}/{ver_to_delete_id}`
     request fires and returns `200` (case Step 4's "deletion request is submitted").
5. Open the VERSION dropdown again (`agent-version-selector-trigger`).
   - **Verify**: `[data-testid="version-option-ver_to_delete"]` no longer exists in
     the dropdown; only `version-option-base` remains (case Step 5).
6. Verify the pipeline has fallen back to `base`.
   - **Verify**: VERSION selector text reads `"base"`; the URL's version-id path
     segment equals the pipeline's original base-version id; the Information panel's
     Version ID matches (case Step 6's "VERSION dropdown shows base and canvas
     displays base state" — again expressed via selector/URL/Information-panel
     triad, this pipeline having no canvas nodes to diff).

## Expected Results
- `ver_to_delete` is created, listed in the VERSION dropdown, then permanently
  removed after confirming deletion via the three-dot menu.
- The pipeline automatically falls back to and displays the `base` version — VERSION
  selector, URL version-id segment, and Information-panel Version ID all agree on
  `base`'s id.
- The deleted version's own detail page (its id) is unreachable — a direct `GET` to
  it returns `400 { "error": "Application[{id}] version[{deleted_id}] not found" }`.
  Note: **one such 400 fires as a side-effect of the delete flow itself**, before the
  fallback settles — see Known Defects below; this is NOT something the test should
  assert should never happen mid-flow, only that the FINAL state (after fallback) is
  clean of it.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1. Create a pipeline and save a non-base version "ver_to_delete" | version appears in the VERSION dropdown | step 1 | `step 1`: dialog closes, URL version-id changes, selector reads "ver_to_delete", `version-option-ver_to_delete` present | asserted |
| 2. Switch to "ver_to_delete" version | canvas updates to show "ver_to_delete" content | step 2 | `step 2`: selector/URL/Information-panel all agree on the new version's id | asserted *(the app auto-navigates to the just-created version — see note below; this step re-confirms rather than performs a separate switch)* |
| 3. Open three-dot menu and click "Delete version" | confirmation dialog opens | step 3 | `step 3`: `delete-confirm-dialog` visible, message text matches | asserted |
| 4. Confirm deletion in the dialog | deletion request submitted | step 4 | `step 4`: dialog closes, `DELETE .../version/.../{id}` returns 200 | asserted |
| 5. Verify version is removed from dropdown | "ver_to_delete" no longer in dropdown | step 5 | `step 5`: `version-option-ver_to_delete` locator count is 0 | asserted |
| 6. Verify pipeline falls back to "base" version | VERSION dropdown shows "base", canvas displays base state | step 6 | `step 6`: selector reads "base", URL/Information-panel version-id match original base id | asserted |

Note on Step 2: the case text implies a distinct "switch to it" action after creation,
but — confirmed live this session, and already documented in the digest's
`agent-save-as-version-button` entry from ELITEA-2002 — the app auto-navigates to the
newly created version immediately after Save As Version succeeds (URL gains the new
version-id segment as part of Step 1's own completion). There is no separate "switch"
gesture available or needed here; Step 2 in this AFS re-asserts the resulting state
(a genuine, distinct check — that the three signals agree) rather than performing a
new interaction. This mirrors how ELITEA-2002's own Step 3 already folded the
post-creation navigation into its own verification.

**Axis 2 — Analyst additions**

- `step 1` asserts the dialog's Name/Save button mechanics (dialog closes, URL
  changes) beyond the case's bare "version appears in dropdown" — *added: reuses the
  already-proven `save_as_version`/`confirm_new_version` page-object methods
  (ELITEA-2002) verbatim; asserting their intermediate mechanics here is free
  (already covered by ELITEA-2002's own test) but the AFS states them for the
  implementer's context, not as new assertions to duplicate in the test body.*
- `step 3` asserts the exact confirmation-dialog message text
  (`"Are you sure to delete the ver_to_delete version? It can't be restored."`) —
  *added: confirmed live this session (`delete-confirm-message`'s rendered text),
  a stable, cheap guard beyond the case's bare "dialog opens."*
- `step 4` asserts the underlying `DELETE` request's status code — *added: a
  network-level signal beyond the case's UI-only "deletion request is submitted",
  same "assert the actual traffic" convention already used in this suite's API-shaped
  assertions.*
- Expected Results section notes the transient 400 on the deleted version's own
  endpoint — *added: this is a genuine finding (Known Defects below), documented so
  the implementer doesn't misread a benign in-flight console error as a step
  regression when they capture their own network trace during implementation.*

## Known Defects Found During Exploration

**Stale GET on the deleted version id fires a visible console 400 (filed:
[EliteaAI/elitea-testing-public#1330](https://github.com/EliteaAI/elitea-testing-public/issues/1330)).**
Confirmed live this session via `browser_network_requests` + `browser_console_messages`
(level=error). Sequence, captured verbatim:

```
[DELETE] /api/v2/elitea_core/version/prompt_lib/399/8219/8473          => 200 OK
[GET]    /api/v2/elitea_core/application/prompt_lib/399/8219           => 200 OK
[GET]    /api/v2/elitea_core/version/prompt_lib/399/8219/8473          => 400 Bad Request
         body: {"error": "Application[8219] version[8473] not found"}
[GET]    /api/v2/elitea_core/version/prompt_lib/399/8219/8472          => 200 OK   (base — fallback settles here)
```

The DELETE itself succeeds and the UI's FINAL state is correct in every run (VERSION
selector reads `base`, dropdown lists only `base`, URL is `/pipelines/all/{id}/{base_id}`)
— no user-visible error/toast, no functional break. This is a client-side race: some
component still holds the just-deleted version id in state/URL for one extra refetch
before the fallback navigation completes. **Reverse-masking check**: this is NOT
case-text drift (the case text says nothing about console cleanliness either way) and
it does NOT block completion of any of the six case steps — deterministic in 1/1
repro this session, single clear cause (a state-sequencing gap in
`VersionDelete.jsx`/`useDeleteVersion.js`), tracked at the ticket above. Per
`.agents/testing.md` § Merge gate's sanctioned-RED criteria this does not need to make
the test itself fail — the implementer should soft-assert / document rather than hard
block:
- **Do not assert zero console errors for the whole flow** (unlike ELITEA-2002, which
  correctly asserts zero because its flow has none) — assert on the FINAL state
  instead (Step 6), and optionally add a `# Known defect: #1330` comment near any
  console-message capture in this test's Step 4/5 area if the implementer chooses to
  inspect console output at all (not required — the AFS's own assertions don't need
  it to prove the case's expected behavior).

No other defects found. Case-text vs live product: matched on all 6 steps (with the
Step 2 "switch" nuance noted above, which is a wording/expectation nuance, not
drift — the FINAL state the case asks to verify is unaffected).

## Blocked Steps
None.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/testing.md` § Locator
policy, `.agents/role-overrides.md`) — no role/label/CSS ladder. All handles below are
`data-testid` (static or dynamic-template). **Zero `add-data-testid` work needed for
this case** — every handle already exists in the live app; all exercised live this
session (2026-08-08) against `http://localhost:5173/pipelines/all/8219` (probe
pipeline, since deleted via `PipelineAPI.delete_pipeline()`).

| Element | Testid (recommended locator) | Provenance | Notes |
|---|---|---|---|
| "Save As Version" button | `agent-save-as-version-button` | on-main ✓ | Already a `PipelineFormPage.save_as_version_button` field (ELITEA-2002) — reuse unmodified. |
| "Create version" dialog Name input | `agent-version-dialog-name-input` | on-main ✓ | Already a `PipelineDetailPage.create_version_name_input` field (ELITEA-2002) — reuse unmodified. |
| "Create version" dialog Save button | `agent-version-dialog-save-button` | on-main ✓ | Already `PipelineDetailPage.create_version_save_button` — reuse unmodified. |
| VERSION selector trigger | `agent-version-selector-trigger` | on-main ✓ | Already `PipelineDetailPage.version_selector` — reuse unmodified. |
| VERSION dropdown option, by name (dynamic) | `[data-testid="version-option-{}"]` (class constant `PipelineDetailPage.VERSION_OPTION`) | on-main ✓ | Already exists — reuse unmodified via `is_version_option_visible("ver_to_delete")` / `.format("ver_to_delete")`. |
| Three-dot actions menu trigger | `agent-actions-menu-button` | on-main ✓ (via `${id}-menu-button` template in `DotMenu.jsx:354` with `id="agent-actions"` passed from `ApplicationControls.jsx:233` — bare-substring grep gives a false negative here, confirmed by reading the template literal directly, per the workflow.md two-stage-grep caveat) | **No `PipelineDetailPage` field yet — needs adding.** `open_actions_menu()` currently exists but uses a bounding-box JS hack (`pipeline_detail_page.py:1606-1634`) instead of this testid — the hack is unmodified tracked tech debt, not blocking, but implementer may simplify `open_actions_menu()` to `self.actions_menu_button.click()` while adding the new field, since the testid demonstrably exists and resolves correctly (confirmed via Playwright MCP's own `getByTestId` resolution this session). Not required for this case's own steps to pass either way — flagging as an opportunistic simplification, not a blocker. |
| "Delete" menu item (VERSION group) | `delete-version-menuitem` | on-main ✓ (`key: 'delete-version'` in `ApplicationControls.jsx:150`, rendered via `DotMenu.jsx`'s `testId: item.key` → `data-testid={testId}-menuitem` mechanism, confirmed present on `origin/main`) | **Needs a new `PipelineDetailPage` field** — this is a DIFFERENT menu item from the existing `PIPELINE`-group `delete-pipeline` item the page object already drives via `get_by_role("menuitem", name="Delete pipeline")` text-matching in `delete_pipeline_via_menu()`. Confirmed live: this same VERSION-group "Delete" item is DISABLED when the currently open version is `base` (source: `ApplicationControls.jsx`'s `disableDelete` — gates on `default_version_id` match OR `name === 'base'`) — not exercised in this case (case always deletes the non-base `ver_to_delete`), but worth a class-constant/note for any future case that needs the disabled-state assertion. |
| Delete confirmation dialog | `delete-confirm-dialog` | **on-`automation/testids` only** (awaiting human promotion to `main`) | Shared `Modal.DeleteEntityModal` component — same testid family already wired on `automation/testids` by several already-merged page objects (`artifacts_page.py`, `secrets_page.py`, `chat_page.py`, `personal_tokens_page.py`, `mcp_form_page.py`, `admin_users_page.py`) for THEIR OWN delete flows — this case needs the SAME testid family added as NEW `PipelineDetailPage` fields (page objects don't share `LocatorDescriptor` fields across files per the project's one-class-per-file convention). Zero new `add-data-testid` work — the underlying JSX (`DeleteEntityModal.jsx`) already carries these attributes on `automation/testids`; only the page-object field is new. |
| Delete confirmation message | `delete-confirm-message` | on-`automation/testids` only | Same component/provenance as above. Live text: `"Are you sure to delete the ver_to_delete version? It can't be restored."` (from `DeleteEntityModal.jsx`'s `textContent` + `name` + `inlineExtraContent` props, as wired by `VersionDelete.jsx`). |
| Delete confirmation confirm button | `delete-confirm-button` | on-`automation/testids` only | Same component/provenance as above. |
| Delete confirmation cancel button | `delete-confirm-cancel-button` | on-`automation/testids` only | Not exercised this case (no cancel step) — exists per source, add the field for completeness/consistency with the other pages that already have it, but no test in THIS case calls it (per-role locator-touches-only rule — do not wire a method that calls it unless a case needs it). |
| Information panel — Version ID | `copy-version-id` | on-main ✓ | Already a `PipelineDetailPage.copy_version_id_button` field (ELITEA-2002) — reuse via `get_version_id()`. |

## Network Behavior
- `POST .../elitea_core/versions/prompt_lib/{project}/{pipeline_id}` → `201` (Save As
  Version — creates `ver_to_delete`).
- `GET .../elitea_core/check_version_in_use/prompt_lib/{project}/{pipeline_id}/{version_id}`
  → `200` fires automatically the moment "Delete" is clicked (before the confirmation
  dialog even opens) — this is how the app decides which confirmation UI to show:
  `{"in_use": false, ...}` → the simple `Modal.DeleteEntityModal` (this case, since
  `ver_to_delete` is a fresh, unreferenced version); `{"in_use": true, ...}` would
  instead open a DIFFERENT modal (`AgentDetails.VersionReplacementModal`, source-read
  in `VersionDelete.jsx`) asking the user to pick a replacement version for whatever
  references the deleted one — **out of scope for this case** (case text and live
  repro both hit the simple `in_use: false` path only) but worth flagging for a future
  case that specifically covers deleting an in-use/referenced pipeline version.
- `DELETE .../elitea_core/version/prompt_lib/{project}/{pipeline_id}/{ver_to_delete_id}`
  → `200` (the actual deletion).
- `GET .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` → `200`
  (refetch immediately after delete).
- `GET .../elitea_core/version/prompt_lib/{project}/{pipeline_id}/{ver_to_delete_id}`
  → `400` — the Known Defect above; a stale refetch of the just-deleted version.
- `GET .../elitea_core/version/prompt_lib/{project}/{pipeline_id}/{base_id}` → `200`
  ×2 — the fallback settling on `base`.

## Cleanup
1. Reuse the pre-existing `pipeline_id` fixture (`automation/fixtures/data_fixtures.py`)
   — it deletes the whole dedicated pipeline (all its versions together) in its own
   teardown, same pattern as `test_pipeline_create_version.py`/ELITEA-2002. No custom
   cleanup needed.

## Automation Hints
- Framework: Playwright + pytest, page object `automation/pages/pipeline_detail_page.py`
  (`PipelineDetailPage`, inherits `PipelineFormPage`).
- Reuse `save_as_version(version_name)` (or the split
  `open_save_as_version_dialog()`/`confirm_new_version()` pair, for asserting
  intermediate dialog state per Step 1) and `open_version_selector()` /
  `is_version_option_visible()` / `get_version_id()` verbatim from ELITEA-2002's work
  — zero changes needed to those.
- New methods needed on `PipelineDetailPage`: something like
  `delete_version_via_menu(timeout=10000)` that opens the actions menu
  (`agent-actions-menu-button` — consider wiring the new testid field instead of
  reusing the existing bounding-box `open_actions_menu()` hack, though either works),
  clicks `delete-version-menuitem`, waits for `delete-confirm-dialog`, and clicks
  `delete-confirm-button`. Mirrors the existing `delete_pipeline_via_menu()`'s shape
  but targets the VERSION-group item and the SIMPLE confirm modal (no type-to-confirm
  — that's the `PIPELINE`-group whole-pipeline delete's `Dialog.type_to_confirm()`
  flow, a different mechanism entirely; don't conflate the two).
- Suggested markers: `@pytest.mark.ui @pytest.mark.pipelines @pytest.mark.p2
  @pytest.mark.regression` (matches ELITEA-2002's sibling test exactly — same
  priority tier, same feature area).
- Suggested test module: `automation/tests/ui/pipelines/test_pipeline_delete_version.py`
  (new file — `test_pipeline_create_version.py` is ELITEA-2002's and stays focused on
  create/switch; delete is a distinct enough flow, with its own new page-object
  methods, to warrant its own file per this suite's one-scenario-family-per-file
  convention observed across the sibling `test_pipeline_*` files).
