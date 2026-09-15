# Test Case: Deleting the currently open entity folder returns to the complete list

## Metadata
- **TMS ID**: ELITEA-3209
- **Source case**: `.agents/automation/social-folders-critical/cases/ELITEA-3209.md` (snapshot; batch brief `LEAD-BRIEF.md`)
- **Linked Story**: EliteaAI/elitea_issues#5194 (feature), EliteaAI/elitea_issues#6484 (source defect, CLOSED in R-2.0.6 — expected GREEN)
- **Priority**: l1 (case priority: `critical`). **pytest markers: `p0`, `regression`, `social_folders`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` @ d4117a2c → DEV backend, project 399)
- **User set**: `${TEST_USER}`; API seeding/cleanup with `${ELITEA_API_TOKEN}`
- **Analyst**: qa-engineer (Sage), 2026-09-15 — executed end-to-end on `skills` (ids 2211/2212, folder id 2); folder-panel handles re-observed on `credentials`
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/social-folders/_surface.md`

## Entity type — randomized per run (lead decision #2301)
Same draw mechanics as ELITEA-3208. This case needs **two disposable entities of the drawn
type**, created via API (transit — see § Fidelity Declaration) through the entity-type resolver
(existing factories: `create_skill`, `create_agent`, `create_pipeline`, `create_credential`,
`create_toolkit`, MCP client), each with its own loud teardown.

## Preconditions
- Logged in as `${TEST_USER}`, project `${ELITEA_PROJECT_ID}` (399).
- Two disposable entities `sf-3209-<type>-1-<epoch>`, `-2-<epoch>` exist (API), **unfiled**
  (`folder_id: null`). Seed BEFORE navigating to the list (an already-mounted list does not show
  API-created rows until it refetches).

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399`; existing entities read-only; page-1 card baseline captured at runtime.
### generate-per-test
- 2 entities (API, transit); 1 folder `sf-3209-<type>-<epoch>` created **via the UI** in step 1;
  folder id from the POST 201 body.
### generate-shared-with-cleanup
- none.

## Test Steps
0. Navigate to the drawn type's list; wait for `folders-panel-create-btn` and both
   `move-to-folder-btn-{e1}` / `move-to-folder-btn-{e2}` attached. Capture `baseline_cards`,
   `baseline_names`. Assert no `folder` URL param.
1. Create the folder via `folders-panel-create-btn` → `create-folder-dialog` → save
   (POST 201 → `folder_id`). Then for each entity: hover its `entity-card`, click
   `move-to-folder-btn-{eid}`, in the menu click `move-to-folder-menu-folder-{folder_id}` while
   waiting for `PUT /social/move_to_folder/prompt_lib/{pid}` → 200 (body `folder_id == folder_id`),
   then wait for `GET /social/folders/…include_counts=true`.
   - **Verify**: `folder-item-count-{folder_id}` reads `(1)` after the first move and `(2)` after
     the second ("the folder count matches (2)").
2. Click `folder-item-{folder_id}`; wait for `GET /social/folder_items/…/{folder_id}` and the list
   GET whose URL contains `ids=`.
   - **Verify**: URL `folder` == `folder_id`; `folder-view-header-name` == folder name;
     `folder-view-header-count` == `(2)`; `entity-card` count == 2; the two
     `move-to-folder-btn-{e1|e2}` present (count 1 each); the list GET's `ids` param is exactly
     the set `{e1, e2}` (order-insensitive); `folder-empty-state` count 0.
3. Hover `folder-item-{folder_id}`, click `folder-item-menu-btn-{folder_id}`, click
   `folder-menu-delete`; in `delete-confirm-dialog` click `delete-confirm-button` while waiting
   for `DELETE /social/folder/prompt_lib/{pid}/{folder_id}` → 204. **Assert no dialog/toast copy.**
   - **Verify** ("immediately returns to the complete unfiltered list"): URL `folder` param gone
     (`expect(page).to_have_url(...)`/`wait_for_function`, observed ~700 ms after the 204);
     `folder-view-close-btn` count 0; the list GET re-fires **without** `ids=`; `entity-card`
     count == `baseline_cards`; `entity-card-name` texts == `baseline_names`;
     `folder-item-{folder_id}` count 0.
4. Inspect both former entities:
   - **Available**: `move-to-folder-btn-{e1}` and `-{e2}` count 1 each on the complete list (page 1).
   - **Unfiled (UI)**: hover each card, click its `move-to-folder-btn-{eid}`; assert
     `move-to-folder-menu-remove-item` **count 0** (it renders only for a filed entity) and no
     `move-to-folder-menu-folder-*` item is active; press Escape.
   - **Unfiled (ground truth)**: from the step-3 list response (or a fresh list GET through the
     entity API client), rows `e1` and `e2` have `folder_id is None` and `folder_name is None`.
5. Cleanup (teardown, API): delete both entities; delete the folder if it still exists (404 ok).

## Expected Results
- Step 1: two PUTs 200; panel count `(2)`.
- Step 2: exactly the two cards; header `(2)`; list `ids=e1,e2`.
- Step 3: DELETE 204; folder param cleared; unfiltered list back to baseline; folder row gone.
- Step 4: both entities present; `folder_id` null; no "Remove from folder" item.
- No console errors beyond the project-wide known-noise set.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Objective: deleting an open folder returns to the complete list; entities remain available and unfiled | — | steps 3–4 | steps 3, 4 | asserted |
| Entities to Test: 6 types, independently | — | setup draw (env-pinnable, logged) | draw | asserted *(randomized per #2301)* |
| 1 Create folder + assign two entities | count matches (2) | step 1 *(decomposed: create, move ×2)* | `folder-item-count-{id}` `(1)`→`(2)` | asserted |
| 2 Open the folder | only its two entities shown | step 2 | cards == 2, ids set == {e1,e2}, header `(2)` | asserted |
| 3 Delete the open folder and confirm | view immediately returns to the complete unfiltered list | step 3 | URL param gone, unfiltered GET, cards == baseline | asserted |
| 4 Inspect the two former entities | both remain available and unfiled | step 4 | presence + menu absence + `folder_id` null | asserted |
| Expected final state: folder gone; complete list; entities unfiled | — | steps 3–4 | `folder-item-{id}` count 0 + step 4 | asserted |
| Cleanup: confirm both unfiled; no further action | — | step 4 (+ teardown deletes the disposable entities) | | asserted |

**Axis 2 — Analyst additions**
- `step 1` asserts the intermediate `(1)` — *observed live; catches a count that only updates
  on the second write.*
- `step 2` asserts the list GET's `ids` set — *"only its two entities" proven at the request
  level, not only by card count (a card count of 2 could be two other entities).*
- `step 3` asserts `folder-item-{id}` count 0 — *the case's final state says the folder no
  longer exists.*
- `step 4` cross-checks `folder_id` null from the list response — *"unfiled" has no
  card-level visual; the row field is the product's own state.*

## Cleanup
1. Teardown guard flags set BEFORE each mutation: `folder_id` captured from the 201 before any
   move; entity ids captured at creation. Teardown: delete entities (API), delete folder (API,
   404 tolerated). A leaked folder pushes the panel toward `VISIBLE_FOLDER_COUNT = 6`.

## Concrete Handles (discovered during exploration)
Full table + provenance: `_surface.md` § Handles. Used here in addition to ELITEA-3208's:

| Element | Handle | Provenance |
|---|---|---|
| Card move-to-folder button | `MOVE_TO_FOLDER_BTN = '[data-testid="move-to-folder-btn-{}"]'` (hover the card first — opacity 0) | on-main ✓ |
| Move-to-folder menu: folder row / remove | `MOVE_TO_FOLDER_MENU_FOLDER = '[data-testid="move-to-folder-menu-folder-{}"]'`, `move-to-folder-menu-remove-item` (`FolderSection.move_menu_folder_item(id)` / `move_menu_remove_item`; `FolderMenuContent.jsx`). `move-to-folder-menu-create-item` was NOT added — no spec references it | on-automation/testids only (EliteaAI/EliteaUI@480f00d6, awaiting human promotion to main) |
| Folder row "⋮" button | `FOLDER_ITEM_MENU_BTN = '[data-testid="folder-item-menu-btn-{}"]'` (`FolderSection.folder_item_menu_button(id)`; hover the row first) | on-automation/testids only (EliteaAI/EliteaUI@480f00d6, awaiting human promotion to main) |
| Folder menu → Delete | `folder-menu-delete` (`FolderActionsMenu.jsx:84`) | on-main ✓ |
| Delete dialog + confirm | `delete-confirm-dialog`, `delete-confirm-button` (shared `DeleteEntityModal`; **`delete-folder-dialog` is dead**) | on-main ✓ |

## Network Behavior
`PUT /social/move_to_folder/prompt_lib/{pid}` `{entity_type, entity_id, folder_id}` → 200 with
`{"message": "<Label> moved to folder", "entity_type", "entity_id", "folder_id"}`; each PUT is
followed by `GET /social/folders/…?entity_type=<t>` and the same with `include_counts=true`
(the count refetch). `DELETE /social/folder/prompt_lib/{pid}/{fid}` → 204, then the folders
refetch and the unfiltered entity-list GET.

## Fidelity Declaration
| Substitution | Kind | Authority |
|---|---|---|
| Two disposable entities created via API before the test | **transit** — they are test data reached before the step under test; every case observable (count, folder view, list restore, unfiled state) is produced by the UI/backend on the real path | LEAD-BRIEF § Framework work ("entities are test data; creating them via API is transit"); `.agents/testing.md` § Fidelity policy |
| Teardown via API | transit (cleanup) | test data hygiene |

## Known Defects Found During Exploration
- none functional. EliteaAI/elitea_issues#6480 (OPEN, copy) — this spec asserts **no** dialog or
  toast copy, by design. Case-text note: the delete dialog needs no type-to-confirm (unlike
  entity deletes) — no clarification needed, the case just says "confirm".

## Blocked Steps
none.

## Automation Hints
- Spec `automation/tests/ui/social_folders/test_deleting_open_folder_returns_complete_list.py`.
- The delete redirect: wait on the URL predicate first (it is the product's `closeFolder()`
  call), THEN on the unfiltered list GET, THEN read cards — reading cards first can catch the
  pre-delete filtered grid.
- Menu items are MUI `MenuItem`s inside `[role="menu"]`; the menu closes itself after a click.
- **Implementation note (2026-09-15):** step 2's "list GET whose URL contains `ids=`" is
  matched by the EXACT ids set `{e1, e2}` — the product first fires a transient `ids=0` list
  GET while `folder_items` is loading (observed on `mcps`; `useFolderEntities.hooks.js` returns
  `idsQueryParam='0'` until items arrive), so the first `ids=` GET can be the sentinel. In
  step 3 the URL `folder` param clears BEFORE the DELETE 204 arrives (the product calls
  `closeFolder()` optimistically) — the spec waits on the 204, the param and the unfiltered GET
  together. Verified green on skills, agents, pipelines, toolkits_and_indexes, mcps, credentials.
