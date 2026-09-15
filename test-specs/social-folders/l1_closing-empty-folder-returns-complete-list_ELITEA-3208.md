# Test Case: Closing an empty entity folder returns to the complete list

## Metadata
- **TMS ID**: ELITEA-3208
- **Source case**: `.agents/automation/social-folders-critical/cases/ELITEA-3208.md` (snapshot; batch brief `LEAD-BRIEF.md` in the same folder)
- **Linked Story**: EliteaAI/elitea_issues#5194 (feature), EliteaAI/elitea_issues#6483 (source defect, CLOSED in R-2.0.6 — expected GREEN)
- **Priority**: l1 (case priority: `critical`). **pytest markers: `p0`, `regression`, `social_folders`** (add the feature marker to `pytest.ini`).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` @ d4117a2c → DEV backend, project 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` via `VITE_DEV_TOKEN`); API seeding/cleanup with `${ELITEA_API_TOKEN}`
- **Analyst**: qa-engineer (Sage), 2026-09-15 — executed on `skills` (RightInfoPanel mount) end-to-end and spot-checked on `credentials` (direct mount)
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/social-folders/_surface.md` (handles, traffic, quirks — read it first)

## Entity type — randomized per run (lead decision #2301)
Draw ONE of `agents · skills · pipelines · toolkits_and_indexes · mcps · credentials`
once at setup; `SOCIAL_FOLDER_ENTITY_TYPE=<value>` (pydantic setting, `.env.test` beats
shell env) pins it; log + allure-attach the draw. The folder itself needs **no entities**,
but the drawn type's list must MOUNT: **amended during implementation** — a zero-entity
list redirects to the type's create page and never renders the FOLDERS panel (project 399
holds 0 credentials and 0 toolkits; the `credentials` draw redirected 3/3), so the spec seeds
ONE disposable, unfiled entity via the API (transit) that simply becomes part of the page-1
baseline. The whole flow was executed live on `skills` and re-observed on `credentials`; the
handles are identical on both mount paths. Implementation verified green on all six types.

## Preconditions
- Logged in as `${TEST_USER}` in project `${ELITEA_PROJECT_ID}` (399).
- The drawn type's list page is reachable and renders its FOLDERS panel
  (`folders-panel-create-btn` visible).
- No pre-existing folder with the disposable name (names carry a timestamp).

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399`; whatever entities the list already shows — read-only. The list
  baseline (card count on page 1, ≤ 20) is **captured at runtime in step 0**, never hardcoded.
### generate-per-test (in test setup, cleaned up in its own teardown)
- One disposable entity `sf-3208-<code>-1-<stamp>` of the drawn type (API, transit — see
  § Fidelity Declaration; only there so the list mounts, never filed, part of the baseline).
- Folder name `sf-3208-<code>-<stamp>`; created **via the UI** in step 1 (the case's own action).
  Its id is read from the `POST /social/folders/prompt_lib/{pid}` **201 response body** (`id`) and
  drives every `folder-item-{id}` / `folder-item-count-{id}` locator.
### generate-shared-with-cleanup
- none.

## Test Steps
0. Navigate to the drawn type's list route; wait for `folders-panel-create-btn` and the first
   `entity-card`. Capture `baseline_cards = count(entity-card)` and `baseline_names`
   (`entity-card-name` texts, page 1). Assert the URL has **no** `folder` param.
1. Click `folders-panel-create-btn`; in `create-folder-dialog` fill the name
   (`CREATE_FOLDER_NAME_INPUT_FIELD`, see Handles); click `create-folder-submit-btn` while
   waiting for `POST /social/folders/prompt_lib/{pid}` → **201**; take `folder_id` from the body.
   - **Verify**: dialog hidden; `folder-item-{folder_id}` visible; `folder-item-count-{folder_id}`
     has exact text `(0)`.
2. Click `folder-item-{folder_id}`; wait for `GET /social/folder_items/prompt_lib/{pid}/{folder_id}`.
   - **Verify**: URL search param `folder` == `str(folder_id)`; `folder-view-header-name` has
     text == folder name; `folder-view-header-count` has exact text `(0)`;
     `folder-empty-state` visible with exact text `No items in this folder yet`
     (**product string, no period — clarification #2302**); `entity-card` count == 0;
     `folder-item-count-{folder_id}` still `(0)`.
3. Click `folder-view-close-btn` while waiting for the drawn type's list `GET` whose URL has
   **no** `ids=` param.
   - **Verify** (the "complete unfiltered list, immediately"): URL has no `folder` param;
     `folder-view-close-btn` count 0; `folder-empty-state` count 0; `entity-card` count ==
     `baseline_cards`; `entity-card-name` texts == `baseline_names`;
     `folder-item-{folder_id}` still present with `(0)`.
4. Cleanup (teardown, API): delete the seeded entity; `DELETE /social/folder/prompt_lib/{pid}/{folder_id}` → 204.

## Expected Results
- Step 1: 201 on create; the new folder row shows `(0)`.
- Step 2: empty state text exactly `No items in this folder yet`; header and row counts `(0)`;
  no cards; the list query fired with the `ids=0` sentinel.
- Step 3: the unfiltered list query fires (no `ids=`), the folder param is gone (observed 14 ms),
  cards return to the step-0 baseline.
- No console errors other than the project-wide known-noise set (`.agents/testing.md` § Unconfirmed).

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Objective: empty message exact, zero count, closing restores the complete list | — | steps 2–3 | steps 2, 3 | asserted |
| Entities to Test: 6 entity types, "execute independently" | each type | setup draw (one type per run, env-pinnable; nightly runs accumulate) | draw logged | asserted *(randomized per lead decision #2301 — not parametrized)* |
| 1 Create a disposable empty folder | folder exists with count `(0)` | step 1 | `folder-item-count-{id}` == `(0)` | asserted |
| 2 Open the empty folder | panel reads exactly `No items in this folder yet.` with count `(0)` | step 2 | `folder-empty-state` == `No items in this folder yet`; header + row count `(0)` | asserted — **clarification #2302** (case text has a trailing period; product has none, 5/5 copies) |
| 3 Close the folder | complete unfiltered list shown immediately | step 3 | no `folder` param; list GET without `ids=`; cards == baseline | asserted |
| Expected final state: complete unfiltered list displayed | — | step 3 | same | asserted |
| Cleanup: delete the disposable folder | — | step 4 | teardown DELETE 204 | asserted (teardown) |

**Axis 2 — Analyst additions**
- `step 0/3` capture and compare the card-name baseline, not just the count — *a count alone
  would also pass for a list showing 20 different items.*
- `step 2` asserts the URL `folder` param and the header count in addition to the row count —
  *the URL is the product's own folder-view state (`useFolderView`); the header is the "panel"
  the case refers to.*
- `step 3` waits for the entity list request WITHOUT `ids=` — *the honest oracle for "unfiltered";
  observed live: `GET …/skills/prompt_lib/399?…&limit=20&offset=0` with no `ids`.*
- `step 3` asserts `folder-empty-state` absent — *guards against the empty state lingering.*

## Cleanup
1. Teardown guard: record `folder_id` the moment the 201 arrives; teardown always issues
   `DELETE /social/folder/prompt_lib/{pid}/{folder_id}` (ignore 404 if step 4 already ran).
2. Nothing else is created.

## Concrete Handles (discovered during exploration)
See `_surface.md` § Handles for the full table with provenance. Used by this case:

| Element | Handle | Provenance |
|---|---|---|
| Create-folder button | `folders-panel-create-btn` | on-main ✓ |
| Create dialog / name input / save | `create-folder-dialog` · `CREATE_FOLDER_NAME_INPUT_FIELD = '[data-testid="create-folder-name-input"] input'` (testid is on the TextField root) · `create-folder-submit-btn` | on-main ✓ |
| Folder row | `FOLDER_ITEM = '[data-testid="folder-item-{}"]'` (id from the 201 body) | on-main ✓ |
| Folder row count | `FOLDER_ITEM_COUNT = '[data-testid="folder-item-count-{}"]'` (`FolderSection.folder_item_count(id)`) | on-automation/testids only (EliteaAI/EliteaUI@480f00d6, awaiting human promotion to main) — `FolderItem.jsx`, the `({folder.entities_count})` Typography |
| Folder view header name / count | `folder-view-header-name`, `folder-view-header-count` (`FolderSection.header_name` / `header_count`) | on-automation/testids only (EliteaAI/EliteaUI@480f00d6, awaiting human promotion to main) — `FolderViewHeader.jsx` |
| Close folder | `folder-view-close-btn` | on-main ✓ |
| Empty state | `folder-empty-state` (`FolderSection.empty_state`; added in ALL 5 list components — MCPs render through `ToolkitsList.jsx`) | on-automation/testids only (EliteaAI/EliteaUI@480f00d6, awaiting human promotion to main) |
| Cards | `entity-card`, `entity-card-name` | on-main ✓ |

State is never a testid value: the open folder is asserted through the URL param and the
header's presence, not through a selected-styled row.

## Network Behavior
See `_surface.md` § Backend traffic. This case: `POST /social/folders/prompt_lib/{pid}` (201) →
`GET /social/folders/…include_counts=true` → open: `GET /social/folder_items/…/{id}` + list GET
with `ids=0` → close: list GET without `ids`.

## Fidelity Declaration
| Substitution | Kind | Authority |
|---|---|---|
| one disposable entity seeded via API before the list is opened | **transit** — the list must mount for the FOLDERS panel to exist; the entity is part of the read-only baseline and nothing is asserted about it | LEAD-BRIEF § Framework work (entities are test data); `.agents/testing.md` § Fidelity policy; amended during implementation (zero-entity lists redirect to the create page) |
| folder creation, open, close — all UI | — | — |
| teardown entity + folder delete via API | transit (cleanup only, after every assertion) | test data hygiene; the case's own observables are all UI-produced |

## Known Defects Found During Exploration
- **#2302** `[Clarification][ELITEA-3208]` — case says `No items in this folder yet.`; product
  renders `No items in this folder yet` on all five list types. Assert the product string; cite
  #2302 in the docstring. Not a product bug (copy is internally consistent; not in #6480's list).
- EliteaAI/elitea_issues#6480 (OPEN) — folder toast/dialog copy mismatches: **assert no copy**.

## Blocked Steps
none.

## Automation Hints
- One spec file `automation/tests/ui/social_folders/test_closing_empty_folder_returns_complete_list.py`;
  folder actions through the reusable `automation/components/folder_section.py` (brief); list
  route + page object from the entity-type resolver (`automation/fixtures/social_folder_fixtures.py`,
  `social_folder_binding` — shipped).
- **Implementation note (2026-09-15):** the list GET with `ids=0` is matched by its exact `ids`
  set (`FolderSection.open_folder(..., expected_ids={"0"})`) — a NON-empty folder fires a
  transient `ids=0` GET first while `folder_items` loads (`useFolderEntities.hooks.js`), so
  "first `ids=` GET" is not a safe predicate. `close_folder()` waits for the header to unmount
  after the URL param clears (see `_surface.md` § Implementation notes).
- Waits: `expect_response` on the POST (id) and on the list GET predicate (`'ids=' not in url`);
  `expect(locator).to_have_text("(0)")` auto-retries — never sleep.
- The `folder-item-count-{id}` testid must be added on the Typography, not on the row (the row
  already has `folder-item-{id}`; its text includes the name).
