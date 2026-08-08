# Test Case: Pipeline — Three-dot Menu Actions

## Metadata
- **TMS ID**: ELITEA-2049
- **Linked Story**: none
- **Priority**: l2 (medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `pipelines-remaining-w2`
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` on localhost).
- A pipeline exists and is open in the editor (created via
  `pipeline_api.create_pipeline()` for isolation — same pattern as
  ELITEA-2022/ELITEA-2050's tests; no shared/fixture pipeline needed).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- One disposable pipeline, `pipeline_api.create_pipeline(name=..., description=...)`
  — no nodes/config needed, the three-dot menu and Copy-link flow don't depend on
  pipeline content. Cleaned up via `pipeline_api.delete_pipeline(pid)` in a
  `finally` block (the menu-open/Copy-link flow never deletes the pipeline itself,
  unlike ELITEA-2022's case).

## Test Steps

(Live-executed and confirmed this session on pipeline `FullDetailsPipe_probe2`,
id `6754`, base version, project `Private`/399.)

1. Open an existing pipeline (`PipelineDetailPage.navigate(pid)`). **Verify**:
   pipeline is loaded in the editor — confirmed live via `get_name()` matching
   the created pipeline's name (case Step 1).
2. Click the three-dot Actions menu button (`actions_menu_button`, testid
   `agent-actions-menu-button`). **Verify**: the menu opens — confirmed live,
   `[role="menu"]` with testid `agent-actions-menu` becomes visible (case Step 2).
3. **Verify all expected menu items are present**, confirmed live via direct DOM
   query of `[data-testid="agent-actions-menu"] [role="menuitem"]` (exact
   testid/label/disabled map — see § Concrete Handles below). The menu renders
   TWO groups, not the case's flat list — case Step 3's items map onto them as
   follows (**CLARIFICATION filed, see § Known Defects — case-text drift, not a
   defect**):
   - **VERSION group**: "Set as a default" (disabled — always true for the
     currently-open version), "Export" (`agent-actions-export-menuitem`),
     "Share" (`share-version-menuitem` — copies a version-specific link, NOT
     the case's "Copy link" target), "Fork" (`pipeline-actions-fork-menuitem`
     — enabled here; case's "(may be disabled for own pipelines)" hedge never
     actually renders a *disabled* Fork item in this product — permission
     failure hides the item entirely instead, see Axis 2), "Delete"
     (`delete-version-menuitem`, disabled — because the open version is
     `base`; case's "Delete version (when on non-base version)" bullet).
   - **PIPELINE group**: "Share" (`share-agent-menuitem` — copies the generic
     pipeline link; **this is the case's "Copy link" item**, case-text drift,
     see below), "Pin to top" (**no testid — see § Concrete Handles, testid
     needed**), "Delete pipeline" (`delete-agent-menuitem`; case's plain
     "Delete" bullet).
   **Verify**: `export_menuitem`, `share_version_menuitem`, `fork_menuitem`,
   `delete_version_menuitem` (disabled), `share_agent_menuitem`,
   `pin_to_top_menuitem`, `delete_agent_menuitem` are all visible — confirmed
   live for every item above (case Step 3).
4. Click the PIPELINE-group "Share" item (`share_agent_menuitem` —
   functionally "Copy link"; **NOT** `share_version_menuitem`, which is
   visually identical and a very plausible wrong-target mistake — same
   negative-control concern already documented by ELITEA-1898's AFS/test for
   the Agent entity). **Verify**: the copy action fires (case Step 4).
5. **Verify link is copied to clipboard, with toast feedback** (case Step 5):
   - A toast appears: `toast_alert` (testid `toast-alert`,
     `data-severity="info"`) + `toast_message` (testid `toast-message`) with
     text `"The link has been copied to the clipboard."` — confirmed live via
     accessibility snapshot immediately after the click.
   - Clipboard contains the pipeline's URL — **not directly confirmed live
     this session** (a raw `navigator.clipboard.readText()` call via
     `browser_evaluate` hung ~30 min waiting on an un-grantable permission
     prompt in the MCP browser — no interactive dialog handler available
     outside a Playwright test context). The suite already has an established,
     working pattern for this exact assertion:
     `test_agent_copy_version_link.py`'s `_copy_link_via_menuitem()` helper
     (`page.context.grant_permissions(["clipboard-read", "clipboard-write"])`
     once per test, then `page.wait_for_function("async () => { const t =
     await navigator.clipboard.readText(); return t.length > 0; }")` — never
     a blocking direct `readText()` call). The implementer should reuse this
     exact pattern (see § Automation Hints) rather than re-deriving it or
     re-attempting the direct-call approach that hung here.
6. Close the menu by pressing `Escape`. **Verify**: the menu closes — confirmed
   live, `[data-testid="agent-actions-menu"]` becomes absent from the DOM
   immediately after `Escape` (case Step 6).

## Expected Results
- Three-dot menu opens showing the VERSION and PIPELINE groups described
  above, with every item from the case's list represented under its actual
  live label (mapping documented in Step 3).
- Clicking PIPELINE-group "Share" (the case's "Copy link") copies the
  pipeline's URL to the clipboard and shows an info toast confirming it.
- `Escape` closes the menu.
- Zero console errors across the whole flow — confirmed live
  (`browser_console_messages(level="error")` → 0 messages, both mid-session
  and at session end).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open an existing pipeline | Pipeline is loaded in the editor | step 1 | `get_name()` match | asserted |
| 2 Click the three-dot menu button | Three-dot menu opens | step 2 | `agent-actions-menu` visible | asserted |
| 3 Verify menu opens with options: Export, Fork (may be disabled), Copy link, Pin to top, Delete, Delete version (when on non-base version) | All listed options are visible in the menu | step 3 | per-item `LocatorDescriptor` visibility checks (7 items) | asserted — **mapped onto live labels/groups, "Copy link" → PIPELINE-group "Share"; CLARIFICATION filed (#1337), not a defect** |
| 4 Click "Copy link" | Copy link action is triggered | step 4 | click on `share_agent_menuitem` | asserted |
| 5 Verify link is copied to clipboard (toast notification or clipboard content) | Toast notification appears or clipboard contains the pipeline URL | step 5 | toast text assertion (live-confirmed) + clipboard content assertion (pattern reused from ELITEA-1898, not itself live-confirmed this session — see step 5 note) | asserted (toast) / **pattern-reuse, not directly reconfirmed (clipboard read hung in MCP browser)** |
| 6 Close menu | Menu closes | step 6 | `agent-actions-menu` absent after `Escape` | asserted |
| Expected Final State: menu displays all expected actions; Copy link copies with user feedback | — | steps 3–5 | steps 3–5 | asserted |
| Pass/Fail: all steps complete without errors; menu shows all options; Copy link copies with feedback | — | all steps | all steps + console-error check | asserted |

### Axis 2 — Analyst additions

- **Negative control**: assert `share_version_menuitem` is ALSO visible and
  is a DIFFERENT element from `share_agent_menuitem` — *added: both items are
  visually identical "Share" labels: without this, an implementer could wire
  the test to the wrong one and the assertion would still pass on the wrong
  URL shape. Same concern ELITEA-1898's AFS/test already documented for the
  Agent entity's identical pair.*
- **Console-error check across the whole menu-open → copy-link → close flow**
  — *added: zero-cost given the live session was already open; silent errors
  are the worst bugs per skill discipline. Confirmed 0 errors, twice
  (mid-flow and end-of-session).*
- **Fork item's actual disabled-vs-absent behavior** — *added: the case
  hedges "(may be disabled for own pipelines)"; live source
  (`ForkEntityButton.jsx`'s `useForkEntityMenu()`) shows the item is either
  present+enabled or entirely ABSENT (permission check gates whether the
  object exists at all), never rendered in a disabled state. Not filed as a
  defect (this is a paraphrase gap, not a wrong-behavior claim — the case
  doesn't assert Fork's exact disabled mechanism) — noted here so the
  implementer doesn't try to assert a `disabled` attribute on Fork that will
  never be true.*

## Cleanup
- `pipeline_api.delete_pipeline(pid)` in a `finally` block — this flow never
  deletes the pipeline itself (unlike ELITEA-2022), so explicit API cleanup is
  required.
- This analyst session's own probe used a pre-existing pipeline
  (`FullDetailsPipe_probe2`, id `6754`) rather than creating a fresh one —
  no residue created, nothing to clean up from this session.

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only** — see
`.agents/role-overrides.md` / `.agents/testing.md` § Locator policy. Live DOM
query of `[data-testid="agent-actions-menu"] [role="menuitem"]` this session
produced the exact map below (text / testid / `aria-disabled`):

| Element | Testid | LocatorDescriptor field | Provenance |
|---|---|---|---|
| Three-dot Actions menu button | `agent-actions-menu-button` | `actions_menu_button` (existing field, `pipeline_detail_page.py`) | on-main ✓ — confirmed live |
| Actions menu container | `agent-actions-menu` | **NEW field needed**: `actions_menu = LocatorDescriptor(testid="agent-actions-menu")` | on-main ✓ — confirmed live (`DotMenu.jsx`'s `${id}-menu` template, `id="agent-actions"`) |
| VERSION-group "Export" | `agent-actions-export-menuitem` | `export_menuitem` (existing field) | on-main ✓ — confirmed live |
| VERSION-group "Share" (version-specific link — NOT the case's "Copy link") | `share-version-menuitem` | **NEW field needed**: `share_version_menuitem = LocatorDescriptor(testid="share-version-menuitem")` | on-main ✓ — confirmed live (same testid Agent's `ELITEA-1898` AFS/test already uses; shared component, same key) |
| VERSION-group "Fork" | `pipeline-actions-fork-menuitem` | **NEW field needed**: `fork_menuitem = LocatorDescriptor(testid="pipeline-actions-fork-menuitem")` | on-main ✓ — confirmed live. **Gotcha**: this is a DIFFERENT testid from Agent's `agent-actions-fork-menuitem` — `ForkEntityButton.jsx`'s `FORK_MENU_ITEM_KEY_BY_ENTITY` map resolves the key per `entity_name` (`pipelines` → `pipeline-actions-fork`). Do not reuse `AgentDetailPage.fork_menuitem`'s testid value here. |
| VERSION-group "Delete" ("Delete version" in case text) | `delete-version-menuitem` | `delete_version_menuitem` (existing field) | on-main ✓ — confirmed live, disabled (`aria-disabled="true"`) while the open version is `base` |
| PIPELINE-group "Share" (**this IS the case's "Copy link"**) | `share-agent-menuitem` | **NEW field needed**: `share_agent_menuitem = LocatorDescriptor(testid="share-agent-menuitem")` | on-main ✓ — confirmed live. **Gotcha (same as Agent's ELITEA-1898)**: the testid key is `share-agent`, NOT renamed per entity — `ApplicationControls.jsx` reuses the literal key `'share-agent'` for both Agent and Pipeline entities; only the label text is always "Share" for both groups (no per-entity label switch here, unlike the Delete items). |
| PIPELINE-group "Pin to top" | **none — testid needed** | **NEW field, blocked on `add-data-testid`**: `pin_to_top_menuitem = LocatorDescriptor(testid="pipeline-actions-pin-to-top-menuitem")` | **needs-adding.** Confirmed live via direct DOM query: the rendered `[role="menuitem"]` for "Pin to top" has `data-testid: null`. Root cause (source-confirmed, `src/[fsd]/widgets/pin-toggler/lib/hooks/usePinMenu.hooks.jsx`): the returned menu-item object has NO `key` field at all (unlike every sibling menu-item hook in this file, which all set `key: '...'`) — `DotMenu.jsx` wires `testId: item.key`, so an absent `key` means `data-testid` never renders. `usePinMenu()` is a SHARED hook (also consumed by `SkillControls.jsx`, `ToolkitsControls.jsx`, `CredentialsControls.jsx` — 4 call sites total), so the fix must thread a caller-supplied key rather than hardcoding one inside the hook — same shape as `ForkEntityButton.jsx`'s `FORK_MENU_ITEM_KEY_BY_ENTITY` map already uses for exactly this multi-caller situation. Minimal fix for THIS case's scope (only the Pipeline call site is touched by this test): add an optional `key` param to `usePinMenu({ isPinned, onTogglePin, isLoading, key })` (default `undefined` — preserves existing behavior for the other 3 untouched callers) and pass `key: isFromPipeline ? 'pipeline-actions-pin-to-top' : 'agent-actions-pin-to-top'` from `ApplicationControls.jsx`'s existing `usePinMenu({...})` call (mirrors `isFromPipeline` already used two lines below for the Delete label). This yields testid `pipeline-actions-pin-to-top-menuitem` for the Pipeline context (per `DotMenu.jsx`'s `${testId}-menuitem` suffix) — do NOT thread a key into the other 3 call sites, they are untouched by this test (scope discipline per `.agents/role-overrides.md`). |
| PIPELINE-group "Delete pipeline" | `delete-agent-menuitem` | **NEW field needed**: `delete_agent_menuitem = LocatorDescriptor(testid="delete-agent-menuitem")` | on-main ✓ — confirmed live (already known from ELITEA-2022's AFS, but not yet a page-object field — `delete_pipeline_via_menu()` still uses `get_by_role("menuitem", name="Delete pipeline")` text-matching internally, unchanged by this AFS per additive-only contract) |
| Toast alert / message | `toast-alert` (+ `data-severity="info"`) / `toast-message` | `toast_alert` / `toast_message` (existing fields) | on-main ✓ — confirmed live, text "The link has been copied to the clipboard." |

**Summary of new page-object work**: 5 new `LocatorDescriptor` fields on
existing testids (`actions_menu`, `share_version_menuitem`, `fork_menuitem`,
`share_agent_menuitem`, `delete_agent_menuitem` — zero EliteaUI changes, all
confirmed on `main`), plus 1 genuine `add-data-testid` gap (`pin_to_top_menuitem`
— small, scoped, optional-param source change per the exact shape above).

## Network Behavior
- No new network calls are triggered by opening the menu or clicking "Share"
  — the copy is a pure client-side `navigator.clipboard.writeText()`
  (`CopyLinkToEntityButton.jsx`'s `useCopyLink`), confirmed via source read.
  No network capture needed for this case beyond the existing pipeline-load
  `GET`.

## Known Defects Found During Exploration

**CLARIFICATION (case-text drift, filed as
[EliteaAI/elitea-testing-public#1337](https://github.com/EliteaAI/elitea-testing-public/issues/1337)
— NOT a product defect, reverse-masking guard applies).** The case's Step 3/4
wording ("Copy link" as a distinct menu label) does not match the live
product: there is no menu item labelled "Copy link" anywhere in the pipeline
three-dot menu. Two items are both labelled "Share" (VERSION-group
`share-version-menuitem` and PIPELINE-group `share-agent-menuitem`); the
PIPELINE-group one functionally matches the case's "Copy link" step
(confirmed live: copies the generic pipeline URL, shows the toast). This is
the SAME underlying pattern already filed twice for other surfaces —
[#1288](https://github.com/EliteaAI/elitea-testing-public/issues/1288)
(ELITEA-1898, Agent Detail page) and
[#1218](https://github.com/EliteaAI/elitea-testing-public/issues/1218)
(ELITEA-2356, Agent Hub modal) — filed as a sibling (different surface: this
is the Pipeline Detail page's overflow menu), not a duplicate, and
cross-linked both ways per `.agents/profile.md` § Bug filing dedup rules. The
live product's behavior is correct; this AFS asserts the live contract
(`share_agent_menuitem` + toast), not the stale case wording.

## Blocked Steps
None. All 6 case steps automate cleanly against the live product. The single
gap (`pin_to_top_menuitem`'s missing testid) is implementer `add-data-testid`
work, not a blocker to automating the rest of the case — the item is still
visible and its label-based existence could be verified via
`get_actions_menu_items()` (existing role-text-scraping method) as an interim
fallback if the testid work is deferred, though the testid-only locator
policy makes adding it the correct default per `.agents/testing.md`.

## Automation Hints
- Framework: Playwright + pytest (confirmed, matches every other pipeline spec).
- Reuse `pipeline_api.create_pipeline()` / `pipeline_api.delete_pipeline()` for
  test data (same pattern as `test_delete_pipeline_via_ui_menu` /
  `test_pipeline_import_via_file`).
- **Reuse `test_agent_copy_version_link.py`'s clipboard-reading pattern
  directly** — `_copy_link_via_menuitem()`-shaped helper:
  ```python
  page.context.grant_permissions(["clipboard-read", "clipboard-write"])
  page.evaluate("() => navigator.clipboard.writeText('')")
  detail_page.share_agent_menuitem.click()
  detail_page.toast_message.wait_for(state="visible", timeout=timeout)
  page.wait_for_function(
      "async () => { const t = await navigator.clipboard.readText(); return t.length > 0; }",
      timeout=timeout,
  )
  copied_url = page.evaluate("async () => await navigator.clipboard.readText()")
  assert f"/pipelines/all/{pipeline_id}" in copied_url
  ```
  Do NOT call `navigator.clipboard.readText()` directly without the
  `wait_for_function` wrapper and without granting permissions first — a
  direct `browser_evaluate` attempt hung for the analyst this session (~30
  min, aborted) waiting on an un-grantable permission prompt.
- For Step 3's "all options visible" check, prefer the 7 explicit
  `LocatorDescriptor` field visibility assertions listed in § Concrete
  Handles over the existing `get_actions_menu_items()` text-scraping method —
  each item this case names is genuinely touched, so each earns its own
  testid-based field per the project's testid-only locator policy
  (`.agents/testing.md` § Locator policy — "touches" = referenced on the
  test's executed code path, which visibility assertions satisfy).
- `add-data-testid` for `pin_to_top_menuitem`: edit
  `src/[fsd]/widgets/pin-toggler/lib/hooks/usePinMenu.hooks.jsx` (add optional
  `key` param, default `undefined`) and
  `src/[fsd]/entities/application-tab-bar/ui/ApplicationControls.jsx` (pass
  `key: isFromPipeline ? 'pipeline-actions-pin-to-top' : 'agent-actions-pin-to-top'`
  into the existing `usePinMenu({...})` call) — commit + push to
  `automation/testids` per the standard flow. Do not touch the other 3
  `usePinMenu()` call sites (Skill/Toolkits/Credentials controls) — out of
  this test's touched scope.
