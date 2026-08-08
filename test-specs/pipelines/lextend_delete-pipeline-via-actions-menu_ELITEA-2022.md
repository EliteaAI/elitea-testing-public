# Test Case: Delete Pipeline — via three-dot Actions menu, verify auto-redirect + removal

## Metadata
- **TMS ID**: ELITEA-2022
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `pipelines-remaining-w2`
- **Status**: extend-existing

## Extension target

**Covering spec**: `automation/tests/ui/pipelines/test_pipeline_management.py`,
class `TestDeletePipeline`, method `test_delete_pipeline_via_ui_menu`
(lines 389–419), merged to `origin/automation/base` (originating commit
`9327052c`, allure-step wrapping added by `7c2d2e5b`; latest touch on this
file is `e7897955`, ELITEA-2020).

**Behavioural overlap (what's already proven).** `test_delete_pipeline_via_ui_menu`
already covers, end-to-end, live-reconfirmed this session:
- Create pipeline via API (`pipeline_api.create_pipeline`) — precondition-equivalent
  to case Steps 1–2 (see note below on why UI-creation isn't re-tested here).
- Navigate to the pipeline detail page.
- Open the three-dot Actions menu (`PipelineDetailPage.open_actions_menu()`,
  reused as-is by `delete_pipeline_via_menu()`) — case Step 3.
- Click "Delete pipeline" (PIPELINE-group item) — case Step 4 (menu opens with
  the correct item).
- Type-to-confirm dialog: fills the pipeline name, clicks "Delete" — case
  Step 5 (deletion submitted).
- Verifies the pipeline is absent from the dashboard list — case Step 7.

**The gap (why this isn't `already-covered`).** Case Step 6 requires verifying
that the app **automatically redirects** to the Pipelines dashboard
(`/pipelines/all`) as a *result of* the delete action. The existing test's
Step 4 (`test_pipeline_management.py:409-414`) does **not** assert this — it
explicitly does `list_page = PipelinesListPage(page); list_page.navigate()`,
i.e. it manually navigates to the dashboard itself rather than asserting the
app already landed there on its own. This masks a real regression class: if a
future change broke the auto-redirect (e.g. left the user on a 404'd detail
page for the now-deleted pipeline, or on some other route), this test would
still pass because it drives its own navigation afterward. Confirmed live this
session (see Test Steps below) that the auto-redirect DOES currently work
correctly — this is a genuine automation gap, not a defect, and the fix is a
missing assertion, not new interaction code.

**Why case Steps 1–2 (UI-driven creation) are not re-tested here.** The case's
Preconditions section already states "A pipeline named 'ToDelete_Pipeline'
exists and is saved" — Steps 1–2 restate that precondition as UI actions.
Pipeline creation via the UI create form is already thoroughly covered by
`ELITEA-2020` (`test-specs/pipelines/lextend_create-pipeline-minimal-sidebar_ELITEA-2020.md`)
and `ELITEA-2021` (`l2_create-pipeline-full-details-persist-after-reload_ELITEA-2021.md`).
Re-driving UI creation here would duplicate that coverage without adding a new
assertion; the covering spec's API-based creation is a faster, equally valid
way to reach the delete flow's precondition (test isolation, not testing
creation). Confirmed live this session anyway (see Test Steps step 1) purely
to validate the case's own precondition text is accurate — no drift found.

## Preconditions
- User is logged in (`auth_state` on localhost).
- A pipeline exists and is saved (created via `pipeline_api.create_pipeline()`
  in the extended test, matching the covering spec's existing pattern —
  no new fixture needed).

## Test Data
- Reuses the covering spec's own pattern: a pipeline named
  `autotest_delete_ui_pipe` (or equivalent per-test name) created via
  `pipeline_api.create_pipeline(name=..., description=...)` in test setup.
  No new test data needed — this AFS adds an assertion to the existing flow,
  it does not need its own fixture.

## Test Steps

(Steps below map onto the *existing* test's flow — the implementer inserts
the new assertion at the marked point; steps 1–5 already pass unmodified.)

1. Create a pipeline via API (existing covering-spec behavior; live-verified
   equivalent via UI create form this session: name `ToDelete_Pipeline_2022`,
   description filled, Save clicked → pipeline id `8222` created, redirected
   to `/pipelines/all/8222?...`). **Verify**: pipeline exists (case Steps 1–2,
   already satisfied by either creation path).
2. Navigate to the pipeline detail page (existing covering-spec behavior).
3. Open the three-dot Actions menu, next to the VERSION controls
   (`PipelineDetailPage.open_actions_menu()`, testid `agent-actions-menu-button`
   — confirmed live: `page.getByTestId('agent-actions-menu-button')` resolves
   and opens `[role="menu"]`). **Verify**: menu opens showing two groups —
   VERSION (Set as a default / Export / Share / Fork / **Delete**, disabled
   while the open version is `base`) and PIPELINE (Share / Pin to top /
   **Delete pipeline**) (case Step 3).
4. Click "Delete pipeline" (PIPELINE-group item; testid resolves to
   `delete-agent-menuitem` — confirmed live via
   `page.getByTestId('delete-agent-menuitem').click()`; the generic
   `delete-agent` key is shared between Agent and Pipeline entity types in
   `ApplicationControls.jsx`, only the visible **label** switches to
   "Delete pipeline" for `isFromPipeline`). **Verify**: "Delete confirmation"
   dialog opens with the type-to-confirm pattern: message
   `Are you sure to delete the {name}? Enter the name to complete the action.`,
   a "Name" textbox, and a "Delete" button disabled until the name is typed
   correctly (case Step 4).
5. Type the exact pipeline name into the confirm textbox
   (`page.getByTestId('delete-confirm-name-input').locator('#name')`, existing
   `Dialog.type_to_confirm()` helper), then click "Delete"
   (`page.getByTestId('delete-confirm-button')`, existing
   `Dialog.click_button()` helper). **Verify**: `DELETE
   /api/v2/elitea_core/application/prompt_lib/{project}/{pipeline_id}` fires
   and returns `204 No Content` (confirmed live via network capture) (case
   Step 5).
6. **[GAP — new assertion, not currently in the covering spec]** Immediately
   after the delete confirms (no manual navigation), assert
   `page.url` resolves to the Pipelines dashboard route (`/pipelines/all` on
   localhost — `APP_PREFIX` is empty there; `/app/pipelines/all` on deployed
   envs per `settings.app_base_url`) **without calling
   `PipelinesListPage.navigate()` first**. Confirmed live this session: the
   URL bar transitioned automatically from
   `http://localhost:5173/pipelines/all/8222?...` to
   `http://localhost:5173/pipelines/all` the instant the delete API call
   settled — no manual navigation involved, no console errors during the
   transition (`browser_console_messages(level="error")` → 0 errors) (case
   Step 6).
7. Verify the deleted pipeline no longer appears in the dashboard list
   (existing covering-spec behavior via `pipeline_exists_in_list()`) (case
   Step 7). Confirmed live: `ToDelete_Pipeline_2022` absent from the grid
   after a 1.5s settle, no manual reload needed.

## Expected Results
- Steps 1–5, 7: unchanged from the existing covering spec — all still pass.
- Step 6 (the gap): the app auto-redirects to the Pipelines dashboard as a
  direct consequence of the delete action, with no manual navigation and no
  console errors. This is the assertion the covering spec is currently
  missing.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create pipeline "ToDelete_Pipeline" | Pipeline is created | step 1 | covering spec's existing API-creation setup | asserted (existing) |
| 2 Save it | Pipeline is saved successfully | step 1 | covering spec's existing setup | asserted (existing) |
| 3 Open the three-dot menu (next to version controls) | Three-dot menu opens | step 3 | covering spec's existing `open_actions_menu()` call | asserted (existing) |
| 4 Click "Delete" option from the menu | Delete confirmation dialog opens | step 4 | covering spec's existing `Dialog.wait_for()` | asserted (existing) |
| 5 Confirm deletion in the confirmation dialog | Deletion is submitted | step 5 | covering spec's existing `Dialog.type_to_confirm()` + `Dialog.click_button()` | asserted (existing) |
| 6 Verify redirect to Pipelines dashboard (URL: /app/pipelines/all) | Browser navigates to the Pipelines dashboard | step 6 | **NEW** — assert `page.url` matches the dashboard route immediately post-delete, before any manual navigation | **gap — needs new assertion** |
| 7 Verify "ToDelete_Pipeline" no longer appears in the pipeline list | The deleted pipeline is not visible in the dashboard list | step 7 | covering spec's existing `pipeline_exists_in_list()` assertion | asserted (existing) |

**Axis 2 — Analyst additions**

- Console-error check across the whole delete flow — *added: zero-cost given
  the live session was already open; silent errors are the worst bugs per
  skill discipline. Confirmed 0 errors.*
- Network-level confirmation of the `DELETE .../application/prompt_lib/{project}/{id}`
  → `204` response — *added: gives the implementer a concrete assertion point
  beyond DOM state if they want one (e.g. via `pipeline_api` or a captured
  response), though the DOM-level redirect + absence checks are sufficient on
  their own for this AFS's Coverage Map.*

## Cleanup
- Covering spec's existing `finally: pipeline_api.delete_pipeline(pid)` block
  is a no-op safety net here (the pipeline is already deleted by the test
  itself) — keep as-is, matches existing pattern.
- This analyst session's own probe pipeline (`ToDelete_Pipeline_2022`, id
  `8222`) was created AND deleted live during this analysis — confirmed
  absent from the dashboard afterward. No residue left behind.

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only** — see
`.agents/role-overrides.md` / `.agents/testing.md` § Locator policy. All
handles below already exist and are already wired in `PipelineDetailPage`
(`automation/pages/pipeline_detail_page.py`) via the existing
`delete_pipeline_via_menu()` method — **no new testid work needed** for this
extension; only a new assertion line in the test.

| Element | Testid | LocatorDescriptor / access path | Provenance |
|---|---|---|---|
| Three-dot Actions menu button | `agent-actions-menu-button` | Not yet a `LocatorDescriptor` field — `open_actions_menu()` uses a bounding-box JS hack (`pipeline_detail_page.py:1744-1770`, pre-existing tech debt per ELITEA-2003's AFS note, unchanged by this extension) | on-main ✓ — confirmed live this session via direct `page.getByTestId('agent-actions-menu-button').click()` resolution |
| "Delete pipeline" menu item (PIPELINE group) | `delete-agent-menuitem` | Not yet a `LocatorDescriptor` field — `delete_pipeline_via_menu()` currently uses `get_by_role("menuitem", name="Delete pipeline")` text-matching (pre-existing tech debt, unchanged by this extension) | on-main ✓ — confirmed live this session via `page.getByTestId('delete-agent-menuitem').click()`. **Gotcha for the next reader**: the testid key is `delete-agent`, NOT `delete-pipeline` — `ApplicationControls.jsx`'s `deleteApplicationMenuItem` is a single shared menu-item object reused for both Agent and Pipeline entities; only the **label** text switches (`Delete ${isFromPipeline ? 'pipeline' : 'agent'}`), the testid does not. Do not go looking for a `delete-pipeline-menuitem` testid — it doesn't exist. |
| Delete confirmation dialog — name input | `delete-confirm-name-input` (container) → `#name` (inner input) | `Dialog.type_to_confirm()` (`components/mui.py`, existing) | on-main ✓ — confirmed live: `page.getByTestId('delete-confirm-name-input').locator('#name').fill(...)` resolved and worked |
| Delete confirmation dialog — Delete button | `delete-confirm-button` | `Dialog.click_button(dialog, "Delete")` (existing) | on-main ✓ — confirmed live: `page.getByTestId('delete-confirm-button').click()` resolved |
| Pipelines dashboard header (redirect-target proxy) | `pipelines-page-header` | `PipelinesListPage.page_header` (existing) | on-main ✓ (pre-existing, per ELITEA-2023's AFS) |

## Network Behavior
- `DELETE /api/v2/elitea_core/application/prompt_lib/{project}/{pipeline_id}`
  → `204 No Content` — confirmed live this session (request #1944 in this
  session's capture, pipeline id `8222`, project `399`).
- No error responses observed on the delete or the subsequent dashboard
  reload (`GET .../applications/prompt_lib/399?agents_type=pipeline...` →
  `200`).

## Known Defects Found During Exploration
None. Case text matches live behavior exactly on all 7 steps — this is a
pure coverage-gap extension (missing assertion in an already-merged spec),
not a product defect or case-text drift.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed, matches covering spec).
- Extend `test_delete_pipeline_via_ui_menu` in-place (or add a sibling
  method in `TestDeletePipeline`, e.g.
  `test_delete_pipeline_via_ui_menu_redirects_to_dashboard`, if the team
  prefers not to touch an already-green test) with the Step 6 assertion:
  ```python
  with allure.step("Step 3 — Delete pipeline via three-dot menu"):
      detail_page.delete_pipeline_via_menu(timeout=NAVIGATION_TIMEOUT)

  with allure.step("Step 4 — Verify automatic redirect to Pipelines dashboard"):
      # NEW — assert BEFORE any manual navigation
      assert page.url.rstrip("/").endswith("/pipelines/all"), (
          f"Expected auto-redirect to the Pipelines dashboard after delete, "
          f"got: {page.url}"
      )

  with allure.step("Step 5 — Verify pipeline removed from dashboard"):
      list_page = PipelinesListPage(page)
      # no list_page.navigate() here — already on the dashboard per the
      # assertion above; navigating would mask a redirect regression
      assert not list_page.pipeline_exists_in_list("autotest_delete_ui_pipe", timeout=3000), (
          "Pipeline 'autotest_delete_ui_pipe' should be gone after UI deletion"
      )
  ```
  Note the removed `list_page.navigate()` call — keeping it would silently
  re-mask the exact gap this extension closes.
- `settings.app_base_url` / `APP_PREFIX` handling: on localhost `APP_PREFIX`
  is empty, so the URL ends `/pipelines/all`; on a deployed env it would be
  `/app/pipelines/all`. Use a suffix-match assertion (`.endswith(...)` or
  regex) rather than an exact string, consistent with the rest of the suite's
  env-agnostic URL assertions.
