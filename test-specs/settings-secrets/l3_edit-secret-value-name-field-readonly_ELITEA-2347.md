# Test Case: Edit secret value inline — name field is read-only after creation

## Metadata
- **TMS ID**: ELITEA-2347
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/settings/secrets/ELITEA-2347_edit-secret-value-inline-name-field-is-read-only-after-creat.md`
- **Linked Story**: none · **Tracking issue**: none provided at dispatch
- **Priority**: l3 (medium, per case frontmatter `priority: medium`). **pytest marker:
  `@pytest.mark.p2`** — medium→l3→p2 convention, per
  `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md` (do NOT
  drift to p1).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost dev-token auth).
- Active project is `${ELITEA_PROJECT_ID}` (399, "Private").
- **Do not target a pre-existing/real secret for this flow.** The project has 100+
  real secrets in live use — this case MUST create its own run-unique secret first
  (via the existing inline "+" flow, `secrets_page.py`'s `click_add_button()` /
  `fill_new_row()` / `click_save_button()` — already covered by ELITEA-2336) and
  edit-value THAT one. This also sidesteps the `isDefault` gate that disables all
  three actions-menu items for system/default secrets (`SecretActionsMenu.jsx` —
  `disabled={isDefault}` on every `MenuItem`) — confirmed live: a freshly-created
  secret is never `isDefault`. Same non-idempotency rationale as
  ELITEA-2336/2338/2343/2344's AFS.

## Test Data
### generated-per-run
- Secret name: a run-unique value, e.g. `f"autotest_edit_{uuid4().hex[:8]}"`.
  Confirmed live this session with `autotest_edit_2347_a1b2c3d4`.
- Original value: any non-empty string, e.g. `"original-value-123"` (used only to
  create the row via the ELITEA-2336 flow — this case never asserts the original
  value, only that the edit flow starts empty and the NEW value round-trips).
- New value: any non-empty string, e.g. `"updated-value-456"`.

## Test Steps
1. Navigate to `${BASE_URL}/settings/secrets`.
   - **Verify**: page title testid `secrets-page-title` is visible with exact
     text "Secrets".
2. Create a run-unique secret via the existing inline "+" flow (`secrets-add-button`
   → `secret-name-input` / `secret-value-input` → `secret-row-save-button`) and
   confirm the `POST /api/v2/secrets/secrets/default/${ELITEA_PROJECT_ID}` create
   request resolves **201 Created** (confirmed live, reused mechanics from
   ELITEA-2336/2338/2344's `click_save_button()`). *(Decomposes the case's own
   precondition of "any secret" into a concrete, run-unique, self-cleaning one —
   same rationale as every sibling case in this feature.)*
3. Locate the created secret's row (`get_row_by_name(name)` — confirmed live
   working reuse of ELITEA-2338's technique) and click its three-dot ("more
   actions") button (`secret-row-actions-button`), then click **"Edit value"**
   (`secret-actions-menu-edit-value`).
   - **Verify**: the actions dropdown menu opens with items in DOM order "Edit
     value", "Hide", "Delete" (confirmed live via full-menu snapshot this
     session — same three items ELITEA-2338 already asserts the full set/order
     of; this case only needs "Edit value" to be present and clickable).
   - **DECLARED IMPROVISATION reminder (not new — inherited from ELITEA-2338,
     `secrets_page.py`'s existing `open_row_actions_menu()`):** a real
     Playwright `.click()` on the three-dot button was **non-deterministic**
     this session too — the FIRST open (for this case's own Edit-value flow)
     required the existing React-`onClick` workaround (a plain `.click()` left
     the button in an "active" pressed state with no menu ever mounting); the
     SECOND open (for this case's own cleanup Delete) succeeded with a plain
     `.click()`. This is now the **fourth** documented session reproducing (or
     narrowly avoiding) this non-determinism across ELITEA-2338/2343/2344/2347 —
     net evidence remains mixed. **Implementer: keep using the existing
     `open_row_actions_menu()` workaround unconditionally**, do not simplify to
     a plain click. Root-cause tracking: `EliteaAI/elitea-testing-public#1222`
     (open).
   - **Verify (side-channel)**: clicking "Edit value" fires
     `GET /api/v2/secrets/secret/default/${ELITEA_PROJECT_ID}/<name>` → `200 OK`
     (confirmed live via network capture — the SAME endpoint/method the
     row-level eye-icon reveal uses, ELITEA-2343). This fetch's plaintext
     response is fetched but then **discarded**: confirmed in source
     (`SecretsTable.jsx`'s wrapped `handleEditClick`, lines 221-246 — the
     row's `secretValue` is explicitly cleared to `''` immediately after the
     fetch resolves) and live (the Value input renders EMPTY, not pre-filled
     with the existing plaintext — see step 3's handle verification below).
     Not required by the case's own wording, but load-bearing for step-4/5
     assertions (an implementer who doesn't know this fires a GET might
     mistake it for evidence of pre-filling).
4. **Verify the Value field becomes inline editable, and starts EMPTY (not
   pre-filled with the existing value).**
   - Confirmed live via `browser_evaluate`-equivalent DOM query, scoped to the
     row: `[data-testid="secret-value-input"]` count === 1, `.inputValue()`
     === `""` immediately after entering edit mode (before typing anything).
     This is a stronger, discovered assertion the case's own wording doesn't
     spell out ("becomes inline editable" alone wouldn't catch a regression
     where the field silently pre-fills the OLD plaintext into an editable
     box — a real information-exposure concern this test additionally guards
     against). *Added — see Axis 2 below.*
5. **Verify the Name field is read-only (cannot be edited).**
   - **Concrete mechanism (discovered, not assumed) — read live in
     `SecretsTable.jsx`'s `renderNameCell` (lines 364-396) and confirmed via
     DOM query this session:** for an EXISTING (non-`isNew`) row in edit mode,
     the Name column does **not** render an `<input>` at all — not even a
     disabled one. It renders the exact same `Text.EllipsisTypography`
     component, with the exact same testid (`secret-name-cell`), that the row
     shows in plain VIEW mode. Confirmed live:
     `row.locator('[data-testid="secret-name-input"]').count()` === `0` and
     `row.locator('[data-testid="secret-name-cell"]').count()` === `1` with
     text content exactly the created name, while the row is actively in
     edit mode (Value input visible, Save/Cancel icons visible). Contrast
     with the CREATE flow (ELITEA-2336), where a brand-new (`isNew`) row DOES
     render `secret-name-input` as a live-editable field — `renderNameCell`'s
     own guard is literally `if (isEditing && row.isNew)`.
   - **This satisfies the case's stated intent** ("read-only / cannot be
     edited" holds true — there is no code path by which a user can change an
     existing secret's name from this UI) but via a **different mechanism**
     than the case's wording might suggest to an implementer skimming it (a
     "read-only field" naturally reads as "a disabled/aria-readonly input"
     rather than "no input is rendered, only the same static text cell").
     Not classified as case-text drift/reverse-masking (the assertion itself
     is still correct, just under-specified on mechanism) — documented here
     so the implementer asserts the actual DOM shape (`secret-name-input`
     absent, `secret-name-cell` present + unchanged text) instead of guessing
     at a `disabled`/`readonly` attribute that doesn't exist on any element.
6. Enter a new value into the Value field and click the ✓ (checkmark) icon
   (`secret-row-save-button`).
   - **Verify**: a `PUT /api/v2/secrets/secret/default/${ELITEA_PROJECT_ID}/<name>`
     request fires with body `{"value": "<new value>"}` and resolves **200 OK**
     (confirmed live via network capture — response body confirmed shape
     `{"name": "<name>", "secret_name": "{{secret.<name>}}"}`, same shape as
     the create mutation's response). **Distinct from the create/hide/delete
     endpoints**: singular `secret` (like delete/reveal) but `PUT` method (vs.
     their `DELETE`/`GET`/`POST`).
   - **No list-GET refetch fires after this PUT** (confirmed live via
     before/after `browser_network_requests` diff — zero new
     `GET .../secrets/default/...` requests after the PUT resolves) — confirmed
     in source too: `useSecretRowUpdate.hooks.js`'s `processRowUpdate`, the
     non-`isNew` (edit) branch updates `rows` state directly from the mutation
     response and never calls `refetch()` (only the `isNew`/create branch
     does, on a `setTimeout`). The row settles back into view mode showing the
     masked template string immediately, purely from local state — don't wait
     on a list-GET that will never come.
7. **Verify the secret saves without error.**
   - Confirmed live: `PUT` response `200 OK` (step 6), row returns to view mode
     showing the masked value cell (`secret-value-cell`, template string
     `"{{secret.<name>}}"`), zero console errors/warnings during steps 3-6
     (side-channel check, same discipline as every sibling case).
8. Click the eye icon (`secret-row-visibility-toggle-button`) to reveal —
   verify the value matches the newly entered value.
   - Confirmed live: revealed `secret-value-cell` text content === the exact
     string typed in step 6 (`"updated-value-456"` this session) — proven via
     a **genuine server round-trip**, not a client-cache read: clicking the
     toggle fires `GET /api/v2/secrets/secret/default/${ELITEA_PROJECT_ID}/<name>`
     → `200 OK` (same endpoint/method as step 3's fetch-on-edit-open), and the
     revealed cell renders `response.value` verbatim
     (`useSecretVisibility.hooks.js`'s `handleShowSecret`, same mechanism
     ELITEA-2343 already documents for the reveal-toggle case). This IS the
     case's own "Expected Final State" / Pass criterion — the single
     highest-value assertion in this case, since it is the only step that
     proves the PUT mutation's new value was actually persisted server-side
     (not just optimistically reflected in local React state after step 6).
     Icon state also flips `secret-row-visibility-icon-show` →
     `secret-row-visibility-icon-hide` (same same-element-conditional-pair
     shape canon ruling #277 already covers for ELITEA-2343 — both branches
     pre-exist, both are exercised: SHOW is visible before this step, HIDE
     after).

## Expected Results
- Clicking "Edit value" opens the Value field as an empty editable input
  (`secret-value-input`) while the Name column stays the SAME static-text cell
  (`secret-name-cell`) it shows in view mode — no `secret-name-input` renders
  for an existing row, ever.
- A `GET .../secret/default/{project_id}/{name}` fires on opening edit mode
  (its plaintext result is discarded, not displayed) — same endpoint the
  reveal-toggle uses.
- Saving fires `PUT .../secret/default/{project_id}/{name}` → 200, body
  `{"value": "<new value>"}` — no list-GET refetch follows (local-state-only
  update, confirmed in source).
- The row returns to view mode showing the masked template string.
- Revealing via the eye icon fires a FRESH `GET` to the same singular-secret
  endpoint and displays the exact new value — proving server-side persistence,
  not just optimistic local state.
- No console errors during steps 1-8 (side-channel check — see § Known Defects).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Secrets | page/section loads | step 1 | `step 1`: `secrets-page-title` visible | asserted |
| 2 Click three-dot menu → "Edit value" | control responds, next state shown | steps 2-3 | `step 2`: run-unique secret created (201); `step 3`: menu opens (existing declared-improvisation workaround), `secret-actions-menu-edit-value` clicked, side-channel GET fetch confirmed | asserted *(decomposed — case precondition "any secret" made concrete/self-cleaning, same as every sibling case)* |
| 3 Verify the Value field becomes inline editable | condition holds | step 4 | `step 4`: `secret-value-input` present, count 1, starts empty | asserted *(strengthened — see step 4's note: "editable" alone wouldn't catch a pre-fill regression)* |
| 4 Verify the Name field is read-only (cannot be edited) | condition holds | step 5 | `step 5`: `secret-name-input` absent (count 0), `secret-name-cell` present with unchanged text — concrete DOM mechanism discovered and documented, not assumed | asserted *(mechanism clarified — see step 5's note; not case-text drift, the case's own claim is correct)* |
| 5 Enter a new value and click ✓ | field accepts input, displays entered value | step 6 | `step 6`: `PUT .../secret/...` → 200, body `{"value": "<new>"}` | asserted |
| 6 Verify the secret saves without error | condition holds | step 7 | `step 7`: 200 response + view-mode masked cell + 0 console errors | asserted |
| 7 Click eye icon to reveal — verify value matches newly entered value | control responds, expected next state shown | step 8 | `step 8`: fresh server GET + revealed text === typed value + icon-pair flip | asserted |
| **Objective / Expected Final State** (duplicate of step 7's wording) | value matches newly entered value on reveal | step 8 | same as case element 7 | asserted — no separate coverage needed, this IS step 7 |

**Axis 2 — Analyst additions:**
- Step 2 creates and later deletes a run-unique secret rather than touching a
  real one — *added: same non-idempotency/data-safety rationale as every
  sibling case in this feature (ELITEA-2336/2338/2343/2344).*
- Step 4 additionally asserts the Value field starts EMPTY (not pre-filled with
  the existing plaintext that the entry-into-edit-mode GET fetches and
  discards) — *added: "becomes inline editable" alone doesn't catch a
  regression where the fetched old value leaks into a visible input; this is
  a genuine information-exposure-adjacent guard, not just UI-state trivia.*
- Step 5 documents and asserts the CONCRETE mechanism behind "read-only" (no
  input rendered at all, vs. a disabled/readonly input) — *added: the case's
  claim is correct, but under-specified; asserting the exact DOM shape
  (`secret-name-input` absent + `secret-name-cell` unchanged) is both stronger
  and more implementable than guessing at a `disabled` attribute that doesn't
  exist on any element in this code path.*
- Step 6 asserts the exact PUT request body and the ABSENCE of a follow-up
  list-GET refetch — *added: same "network is the proof, not the DOM alone"
  discipline as every sibling case's mutation assertions; the refetch-absence
  is worth asserting explicitly because it's easy for an implementer to wait
  on a GET that source code proves will never fire (see step 6's source
  citation), producing a flaky/slow test.*
- Step 8 asserts the reveal is a FRESH SERVER round-trip (network capture),
  not just a DOM text match — *added: the whole POINT of this case (per its
  own Objective wording) is proving the new value was actually PERSISTED, not
  just reflected in optimistic local state after step 6's PUT resolves; a
  DOM-only check would pass even if the PUT silently failed to persist
  server-side as long as local state still held the typed value.*

## Cleanup
- **Required**: this case's own steps never delete the created secret. Delete
  it via the UI delete flow (three-dot → Delete → type name → confirm — reuse
  ELITEA-2338's `click_delete_menu_item()` / `fill_delete_confirm_name()` /
  `confirm_delete()` verbatim) as the test's own teardown/fixture, OR via the
  documented API shortcut
  (`DELETE /api/v2/secrets/secret/default/{project_id}/{name}` → `204`).
  Confirmed live this session via the UI flow — pagination total returned to
  the exact pre-test baseline (103).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only, no fallback ladder**
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`).

**Provenance verified fresh this session** (`cd ../EliteaUI && git fetch origin`
then `git grep` against `origin/main` / `origin/automation/testids` — full
per-testid grep output captured, summarized below). **Zero new testid work
needed for this case** — every handle it touches already exists on
`automation/testids` (pushed, dev server serves them); none are on `main` yet
except `delete-confirm-name-input` (cleanup-only, pre-existing app-wide).

| Element | Testid | On `main`? | On `automation/testids`? | Provenance |
|---|---|---|---|---|
| Page title | `secrets-page-title` | no | ✓ | pre-existing (ELITEA-2336) |
| "+" add button | `secrets-add-button` | no | ✓ | pre-existing (ELITEA-2336) — wired via `DrawerPageHeader`'s `slotProps.addButton.testId` prop indirection (not a literal `data-testid=` on the JSX call site — grep for `testId:` too, not just `data-testid`) |
| Secret row | `secret-row` | no | ✓ | pre-existing (ELITEA-2336) |
| Value input (edit mode, any row) | `secret-value-input` | no | ✓ | pre-existing (ELITEA-2336) — `EditSecretInputGridTable.jsx` `inputProps['data-testid']` |
| Name input (CREATE flow only — NOT rendered for an existing row's edit-value mode, see step 5) | `secret-name-input` | no | ✓ | pre-existing (ELITEA-2336) — confirmed this session it does NOT render when editing an existing row |
| Name cell (static text — used in BOTH view mode and an existing row's edit-value mode) | `secret-name-cell` | no | ✓ | pre-existing (ELITEA-2336) — `SecretsTable.jsx` `renderNameCell`, confirmed this session as the mechanism behind step 5 |
| Value cell (masked/revealed, view mode) | `secret-value-cell` | no | ✓ | pre-existing (ELITEA-2343/`SecretValueCell.jsx`) |
| Save (✓) button | `secret-row-save-button` | no | ✓ | pre-existing (ELITEA-2336) |
| Three-dot / more-actions button | `secret-row-actions-button` | no | ✓ | pre-existing (ELITEA-2338) |
| "Edit value" menu item | `secret-actions-menu-edit-value` | no | ✓ | pre-existing (ELITEA-2338) — first case to actually CLICK it (2338/2343/2344 use Delete/Hide) |
| Row-level visibility toggle button | `secret-row-visibility-toggle-button` | no | ✓ | pre-existing (ELITEA-2343) |
| Visibility icon — masked/show state | `secret-row-visibility-icon-show` | no | ✓ | pre-existing (ELITEA-2343) |
| Visibility icon — revealed/hide state | `secret-row-visibility-icon-hide` | no | ✓ | pre-existing (ELITEA-2343) |
| "Delete" menu item (cleanup only) | `secret-actions-menu-delete` | no | ✓ | pre-existing (ELITEA-2338) |
| Delete confirmation dialog (cleanup only) | `delete-confirm-dialog` | no | ✓ | pre-existing — shared `DeleteEntityModal.jsx` |
| Delete confirmation name input (cleanup only) | `delete-confirm-name-input` | **✓ YES** | ✓ | pre-existing — shared `DeleteEntityModal.jsx`, already on `main` |
| Delete confirmation button (cleanup only) | `delete-confirm-button` | no | ✓ | pre-existing — shared `DeleteEntityModal.jsx` |

No testid needed on anything this case touches. `secret-name-input`'s ABSENCE
during edit-value mode is itself the assertion for step 5 — there is no
element to add a testid to for "the read-only name field" because no such
input element exists in this code path.

## Network Behavior
- `POST /api/v2/secrets/secrets/default/{project_id}` — create (step 2), `201`.
- `GET /api/v2/secrets/secrets/default/{project_id}` — list refetch, fires
  after create only (NOT after the edit-value PUT — see step 6).
- `GET /api/v2/secrets/secret/default/{project_id}/{name}` — fires TWICE in
  this case's own flow: once on opening "Edit value" (step 3, result
  discarded), once on revealing via the eye icon (step 8, result displayed
  and asserted). Same endpoint/method the row-level reveal toggle uses
  (ELITEA-2343) — singular "secret", `GET`.
- `PUT /api/v2/secrets/secret/default/{project_id}/{name}` — fires on Save
  (step 6), body `{"value": "<new value>"}`, `200 OK`, response body
  `{"name": "<name>", "secret_name": "{{secret.<name>}}"}`. **No refetch
  follows** (confirmed live + in source — see step 6).
- `DELETE /api/v2/secrets/secret/default/{project_id}/{name}` — cleanup only,
  `204`.

## Known Defects Found During Exploration
None within this case's own steps (1-8). Known defect
`EliteaAI/elitea-testing-public#1203` (OPEN — React "Maximum update depth
exceeded" console warning on every `/settings/secrets` mount) was **NOT
observed** during steps 1-8 this session (0 console errors/warnings across
navigate → create → edit-value → reveal). Same inconclusive pattern already
documented by every sibling AFS in this feature — implementer should check
their own automated run's console output rather than assume either way.

**Observation, NOT a defect in this case's scope:** during CLEANUP only
(after step 8, outside the case's own 7 numbered steps), deleting the test
secret produced one console error — `Failed to load resource: 404` for
`GET .../secret/default/399/<name>` — apparently a stray background request
racing the delete. Not investigated further because it fires strictly after
this case's own assertions are complete and does not affect any step's
pass/fail; flagged here only so an implementer who wraps a blanket
"assert zero console errors for the whole test" doesn't misattribute a
cleanup-phase artifact to the case under test. If the implementer's own run
reproduces this deterministically WITHIN the case's own steps (it did not
this session), treat per the standard decision tree.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: extend `automation/pages/secrets_page.py` — reuse `navigate()`,
  `click_add_button()`, `fill_new_row()`, `click_save_button()`,
  `get_row_by_name()`, `open_row_actions_menu()` (**with its existing
  declared-improvisation workaround — do not simplify to a plain click**),
  `click_delete_menu_item()` / `fill_delete_confirm_name()` / `confirm_delete()`
  verbatim from ELITEA-2336/2338. Add new methods:
  `click_edit_value_menu_item()` (click `actions_menu_edit_value`, wait for
  the row's `secret-value-input` to become visible), `fill_edit_value(row,
  new_value)` (fill the row-scoped `secret-value-input`), `save_edit(row)`
  (reuse the existing save-button click + `page.expect_response()` for the
  `PUT .../secret/...` 200 — a NEW wait shape, distinct from the existing
  create-flow save which waits on `POST`), `reveal_row_value(row)` (click
  `secret-row-visibility-toggle-button` scoped to the row, wait for the
  reveal `GET` response, read `secret-value-cell`'s text — likely already
  exists from ELITEA-2343, reuse verbatim).
- Wait strategy: `page.expect_response()` for the create POST (201), the
  edit-open GET (200, step 3 — optional to wait on since its result is
  discarded, but useful as a synchronization point before asserting the
  empty Value input), the edit PUT (200, step 6), and the reveal GET (200,
  step 8) — never a fixed sleep, per `.agents/testing.md`. **Do NOT** wait on
  a list-GET refetch after the PUT — source confirms none fires (step 6).
- Step 5's assertion is a NEGATIVE + a POSITIVE together:
  `expect(row.locator('[data-testid="secret-name-input"]')).to_have_count(0)`
  AND `expect(row.locator(SecretsPage.SECRET_NAME_CELL_SELECTOR)).to_have_text(name)`
  — both scoped to the row, both while edit mode is active (Value input
  visible / Save button visible).
- Reuse `secrets_page.py`'s `VISIBILITY_ICON_VISIBLE_SELECTOR` /
  `VISIBILITY_ICON_HIDDEN_SELECTOR` class constants for the step 8 icon-flip
  assertion (pre-existing from ELITEA-2343, same same-element-conditional-pair
  shape).

## Automation gap this case surfaces (report to the lead)
None. Every handle this case touches already exists on `automation/testids`
(confirmed fresh this session) — zero `add-data-testid` work required.
