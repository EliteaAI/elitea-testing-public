# Test Case: Folder count stays accurate after entity deletion and subsequent add/remove

## Metadata
- **TMS ID**: ELITEA-3210
- **Source case**: `.agents/automation/social-folders-critical/cases/ELITEA-3210.md` (snapshot; batch brief `LEAD-BRIEF.md`)
- **Linked Story**: EliteaAI/elitea_issues#5194 (feature), EliteaAI/elitea_issues#6482 (source defect, CLOSED in R-2.0.6 — expected GREEN)
- **Priority**: l1 (case priority: `critical`). **pytest markers: `p0`, `regression`, `social_folders`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` @ d4117a2c → DEV backend, project 399)
- **User set**: `${TEST_USER}`; API seeding/cleanup with `${ELITEA_API_TOKEN}`
- **Analyst**: qa-engineer (Sage), 2026-09-15 — executed end-to-end on `skills` (ids 2211/2212/2213 + 2214, folder id 3); the entity-delete step was executed ONLY on skills (see § Automation Hints — type-specific)
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/social-folders/_surface.md`

## Entity type — randomized per run (lead decision #2301)
Same draw mechanics as ELITEA-3208. This case needs **four disposable entities of the drawn
type** (three filed in step 1, one spare for step 4), created via API (transit), and it
**deletes one of them through the product's own delete UI** in step 2 — that delete is a case
action, never an API call.

## Preconditions
- Logged in as `${TEST_USER}`, project `${ELITEA_PROJECT_ID}` (399).
- Four disposable entities `sf-3210-<type>-{1..4}-<epoch>` exist (API), unfiled. Seed before
  navigating to the list.

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399`; existing entities read-only.
### generate-per-test
- 4 entities (API, transit; e1–e3 filed in step 1, e4 filed in step 4; e3 deleted by the UI in
  step 2); 1 folder `sf-3210-<type>-<epoch>` created via the UI (id from the 201 body).
### generate-shared-with-cleanup
- none.

## Test Steps
0. Navigate to the drawn type's list; wait for `folders-panel-create-btn` and
   `move-to-folder-btn-{e1..e4}` attached.
1. Create the folder via the UI (POST 201 → `folder_id`); move e1, e2, e3 into it via each card's
   `move-to-folder-btn-{eid}` → `move-to-folder-menu-folder-{folder_id}` (PUT 200 each, then the
   `include_counts=true` refetch).
   - **Verify**: `folder-item-count-{folder_id}` reads `(3)` (observed after each PUT: `(1)`,
     `(2)`, `(3)`, ~0.6 s each).
2. Open the folder (`folder-item-{folder_id}`; URL `folder == folder_id`, header `(3)`, 3 cards).
   **From inside the folder view**, delete e3 through the drawn type's **normal entity delete
   action** (resolver-provided; for `skills` executed live: click the card's `entity-card-name`
   → detail page `/skills/all/{e3}` → `skill-controls-menu-button` → `skill-delete-menu-item`
   → type the name into `delete-confirm-name-input` → `delete-confirm-button`, waiting for
   `DELETE /elitea_core/skill/prompt_lib/{pid}/{e3}` → 204). The app redirects to the list
   (`/skills/all`, both `viewMode` and `folder` params dropped) and refetches
   `GET /social/folders/…include_counts=true` on mount.
   - **Verify** ("updates from 3 to 2 without a manual refresh"): **no `page.reload()` /
     `goto` is issued by the test after the confirm click**; `folder-item-{folder_id}` visible
     on the landed list; `folder-item-count-{folder_id}` `to_have_text("(2)")` (observed `(2)`
     at first read, 640 ms after the DELETE, count settled in 2 ms of polling);
     `move-to-folder-btn-{e3}` count 0 on the list.
3. Click `folder-item-{folder_id}` (open) → verify header `(2)`, `entity-card` count 2, the two
   remaining `move-to-folder-btn-{e1|e2}` present; click `folder-view-close-btn` → URL param
   gone; click `folder-item-{folder_id}` again (reopen) → folder view open again (URL `folder`
   param + header rendered — a re-open inside one mount may be served from the RTK cache with NO
   `folder_items` GET; see § Automation Hints implementation notes). For `navigate(-1)` types the
   folder is still open after step 2, so the spec closes it first and then runs open → close → reopen.
   - **Verify**: `folder-item-count-{folder_id}` == `(2)` after close AND after reopen;
     `folder-view-header-count` == `(2)`; cards == 2.
4. Close the folder (`folder-view-close-btn`, URL param gone — e4 is not in the folder so it is
   only reachable on the complete list). Hover e4's card, `move-to-folder-btn-{e4}` →
   `move-to-folder-menu-folder-{folder_id}` (PUT 200, `folder_id == folder_id`), wait for the
   `include_counts=true` refetch.
   - **Verify**: `folder-item-count-{folder_id}` `to_have_text("(3)")` (observed 628 ms).
5. Hover e4's card again, `move-to-folder-btn-{e4}` → `move-to-folder-menu-remove-item`
   (PUT 200 with `folder_id: null`), wait for the refetch.
   - **Verify**: `folder-item-count-{folder_id}` `to_have_text("(2)")` (observed 621 ms), and the
     `GET /social/folders/…include_counts=true` response body has `entities_count == 2` for
     `folder_id` (no drift between panel and backend). Open the folder once more: header `(2)`,
     cards == 2 (e1, e2), `move-to-folder-btn-{e4}` count 0.
6. Cleanup (teardown, API): delete e1, e2, e4 (e3 was deleted by the case — tolerate 404);
   delete the folder.

## Expected Results
- Counts read exactly `(3)` → `(2)` → `(2)`/`(2)` → `(3)` → `(2)` with no intermediate stale
  value surviving an auto-retrying assertion, and the final backend `entities_count` is 2.
- Console: no errors except the URL-scoped known defect below and the project-wide noise set.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Objective: count updates immediately after in-folder entity delete and tracks add/remove | — | steps 2–5 | steps 2–5 | asserted |
| Entities to Test: 6 types, independently | — | setup draw (env-pinnable, logged) | draw | asserted *(randomized per #2301)* |
| 1 Assign three disposable entities to a disposable folder | count `(3)` | step 1 *(decomposed: create folder, move ×3)* | `folder-item-count-{id}` `(3)` | asserted |
| 2 From inside the folder, delete one entity via the normal entity delete action | count updates 3→2 immediately, no manual refresh | step 2 | `(2)` on the landed list, no reload issued, e3 card gone | asserted — **note**: for RightInfoPanel types the delete action lives on the detail page and the app's own redirect closes the folder view; the count is read on the panel row after that redirect, with no test-issued refresh (case intent preserved; recorded as a note, not a clarification — the case does not say the folder view must stay open) |
| 3 Close and reopen the folder | count still `(2)` | step 3 | `(2)` after close and after reopen; header `(2)` | asserted |
| 4 Add one more entity to the folder | count 2→3 | step 4 | `(3)` | asserted |
| 5 Remove one entity from the folder | count 3→2, no drift | step 5 | `(2)` + backend `entities_count == 2` | asserted |
| Expected final state: count reflects two remaining entities, no drift | — | step 5 | same | asserted |
| Cleanup: delete folder and remaining entities | — | step 6 | teardown | asserted (teardown) |

**Axis 2 — Analyst additions**
- `step 1` asserts the intermediate `(1)`/`(2)` — *observed live; a count that only updates on
  the last write would otherwise pass.*
- `step 2` asserts `move-to-folder-btn-{e3}` absent from the list — *proves the entity delete
  really happened (the count could drop for other reasons).*
- `step 5` cross-checks `entities_count` in the folders refetch body — *"no drift" is a
  panel-vs-backend statement; both are read from the same product path.*
- `step 5` re-opens the folder and asserts the membership (e1, e2 present, e4 absent) — *the
  count alone cannot tell "removed e4" from "removed e1".*

## Cleanup
1. Guard flags before each mutation (folder id from the 201; entity ids at creation). Teardown
   deletes e1, e2, e4 (API; 404 tolerated for e3) and the folder (API). Restore nothing else —
   no org/project defaults are touched.

## Concrete Handles (discovered during exploration)
Full table + provenance: `_surface.md` § Handles. In addition to ELITEA-3208/3209's:

| Element | Handle | Provenance |
|---|---|---|
| Move-to-folder → Remove from folder | `move-to-folder-menu-remove-item` (`FolderSection.move_menu_remove_item`; `FolderMenuContent.jsx`; renders only for a filed entity) | on-automation/testids only (EliteaAI/EliteaUI@480f00d6, awaiting human promotion to main) |
| Skill delete path (type `skills`) | `skill-controls-menu-button` → `skill-delete-menu-item` → `delete-confirm-name-input` (root testid; type into its descendant `input` — the existing `SkillDetailPage.delete_skill_via_menu` already does this) → `delete-confirm-button` | on-main ✓ |
| Other types' delete path | resolver `delete_via_ui` (`social_folder_fixtures.py`) → `AgentsListPage.open_card_by_name` + `AgentDetailPage.delete_agent_via_menu`; `PipelinesListPage.open_pipeline_by_name` + `PipelineDetailPage.delete_pipeline_via_menu`; `McpListPage.open_card_by_name` + `McpFormPage` menu/fill + the shared `delete-confirm-button`; `ToolkitsListPage.open_card_by_name` + `ToolkitDetailPage.delete_toolkit_via_menu` (added); `CredentialsListPage.click_credential_card` + `CredentialDetailPage` delete flow — **all six executed live 2026-09-15, green**; landing URLs in `_surface.md` § Implementation notes | existing suite (+ additive methods) |

## Network Behavior
Step 2 (skills): `DELETE /elitea_core/skill/prompt_lib/399/2213` → 204, then a stale
`GET /elitea_core/skill/prompt_lib/399/2213` → **404** (console error, **#2303**), then
`GET /social/folders/prompt_lib/399?entity_type=skill&include_counts=true` and the unfiltered
list GET. Steps 4/5: `PUT /social/move_to_folder/prompt_lib/399` → 200 (`folder_id` set / null),
then the two folders GETs (with/without `include_counts`).

## Fidelity Declaration
| Substitution | Kind | Authority |
|---|---|---|
| Four disposable entities created via API | **transit** — test data; every count/redirect/membership observable is UI/backend-produced | LEAD-BRIEF § Framework work; `.agents/testing.md` § Fidelity policy |
| Teardown via API | transit (cleanup) | test data hygiene |
| The step-2 entity delete | **NOT substituted** — it is the case's own action and goes through the UI | case text: "via the normal entity delete action" |

## Known Defects Found During Exploration
- **#2303** `[MINOR][ELITEA-3210]` — deleting a skill from its detail page fires a stale
  `GET /elitea_core/skill/prompt_lib/{pid}/{id}` → 404 console error (sibling of #1666, the
  credentials twin). Console-error assertion must use
  `utils/console_errors.collect_console_errors()` + `exclude_known_defect_urls(errors,
  f"/elitea_core/skill/prompt_lib/{pid}/{e3}")` with `# Known defect: #2303` (credentials draw:
  `/configurations/configuration/{pid}/{e3}`, `# Known defect: #1666`). Never a status-code
  filter. Another type showing the same stale GET is a NEW sibling to file, not a filter widening.

## Blocked Steps
none.

## Automation Hints
- Spec `automation/tests/ui/social_folders/test_folder_count_accurate_after_entity_deletion.py`.
- **Type-specific risk, stated honestly:** only the `skills` delete flow was executed live. The
  resolver's `delete_entity_via_ui(type, entity)` must reuse each type's existing page-object
  delete helper and must END on the list page (the folder panel is where the count is read).
  If a type's delete flow lands somewhere else (e.g. stays on a detail route), navigate to the
  list route — that is still "no manual refresh" of a mounted list, but declare it in the
  docstring and append the observation to `_surface.md`.
- Step 2's "immediately" is asserted by an auto-retrying `to_have_text("(2)")` on the landed
  panel row — do NOT read the count before the folders refetch resolves (wait on
  `include_counts=true` after the DELETE), and do NOT reload.
- e4 must be moved from the complete list (step 4 closes the folder first) — an entity outside the
  open folder has no card inside it.
- **Implementation notes (2026-09-15, all six types verified green):**
  - Landing after the step-2 delete is type-specific: skills / agents / credentials land on the
    bare list route (folder view closed); pipelines / toolkits / **mcps** redirect with
    `navigate(-1)` back to `…/all?folder=<id>`, i.e. the folder view is still OPEN. Step 3
    therefore normalises to "closed" first (declared in the spec docstring) — the case's "close
    and reopen" is then executed literally. `McpFormPage.confirm_delete()` is NOT used for mcps:
    its `wait_for_url("**/mcps/all")` glob never matches the `?folder=` landing.
  - Re-opening / re-closing a folder inside one list mount may fire NO request at all (RTK Query
    serves `folder_items` and often the list query from cache) — 3/3 timeouts when step 3 waited
    on the network. Re-opens are taken from the product's own signals (URL `folder` param +
    header rendered) and every count/card read auto-retries; only the FIRST open after a
    membership change waits on the list GET with the exact ids.
  - The row's click handler closes over the last-RENDERED `selectedFolderId`: a reopen click that
    lands after the URL param cleared but before React re-rendered is treated as "same folder →
    toggle closed" (reproduced once). `close_folder()` waits for the header to unmount before
    returning.
- Step 0 transit guard for product bug #2305 (first-render empty-list redirect): `binding.open_list` (fixtures) re-navigates a create-route landing and drops ONLY that redirected attempt's console messages; Axis 2 excludes the #1971 project-id-less toolkitTypes 404 by exact URL (`exclude_known_defect_urls`), never by status code.
