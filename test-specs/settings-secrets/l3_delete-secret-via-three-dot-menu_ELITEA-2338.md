# Test Case: Delete a secret via three-dot menu and verify removal

## Metadata
- **TMS ID**: ELITEA-2338
- **Source case**: `.agents/automation/elitea-2338-delete-secret/cases/ELITEA-2338.md`
- **Linked Story**: none
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
- **Do not target a pre-existing/real secret for deletion.** The project has
  100+ real secrets in live use (`auth_token`, `default_llm_model_name`, …) —
  deleting one would corrupt shared test data for the whole suite. This case
  MUST create its own run-unique secret first (via the existing inline "+"
  flow, `secrets_page.py`'s `click_add_button()` / `fill_new_row()` /
  `click_save_button()` — already covered by ELITEA-2336) and delete THAT one.
  This also sidesteps the `isDefault` prop that disables all three menu
  items for system/default secrets (`SecretActionsMenu.jsx` — `disabled={isDefault}`
  on every `MenuItem`) — confirmed live: a freshly-created secret is never
  `isDefault`.

## Test Data
### generated-per-run
- Secret name: a run-unique value, e.g. `f"autotest_delete_target_{uuid4().hex[:8]}"`
  — same rationale as ELITEA-2336's AFS (non-idempotent literal risk across
  repeated/failed CI runs). Confirmed live with `autotest_delete_target_a1b2c3d4`.
- Secret value: any non-empty string, e.g. `"delete-test-value-123"` — no format
  validation beyond max-length (shared with name field).

## Test Steps
1. Navigate to `${BASE_URL}/settings/secrets`.
   - **Verify**: page title testid `secrets-page-title` is visible with exact text
     "Secrets".
2. Create a run-unique secret via the existing inline "+" flow (`secrets-add-button`
   → `secret-name-input` / `secret-value-input` → `secret-row-save-button`) and
   confirm the `POST /api/v2/secrets/secrets/default/${ELITEA_PROJECT_ID}` create
   request resolves **201 Created** (confirmed live, reused mechanics from
   ELITEA-2336's `click_save_button()`, which already returns the `Response`
   for this exact assertion).
3. Locate the created secret's row — confirmed live technique: type its name into
   the search input (`textbox[placeholder="Search"]` — **no dedicated testid
   confirmed on this project**, per `_surface.md`; live-filters with no Enter/
   debounce needed, confirmed via `browser_wait_for` — pagination read
   "1 - 1 of 1" ~2s after typing) so exactly one row remains, then locate the
   **three-dot ("more actions") button** on that row.
   - **Testid needed**: `secret-row-actions-button` — confirmed live this
     control has **zero** testid today (`SecretsTable.jsx:511-518`, a bare
     `IconButton` wrapping `DotsMenuIcon` with no `data-testid`; digest
     `_surface.md` already flagged this gap). App-owned JSX under
     `src/[fsd]/features/settings/ui/secrets/` (not third-party) — this is
     implementer work via `add-data-testid`, not a #579 stop+flag exception.
     Uniqueness confirmed (`git grep` on EliteaUI `main` — zero hits).
   - Click it.
   - **Verify**: the actions dropdown menu opens (confirmed live —
     `SecretActionsMenu.jsx`, MUI `<Menu>`, `open={!!anchorEl}`).
4. **Verify** the dropdown shows exactly three items, in this order: **"Edit
   value"**, **"Hide"**, **"Delete"** (confirmed live via accessibility snapshot
   — `role="menuitem"` × 3, exact text match).
   - **Testids needed** (none exist today — `SecretActionsMenu.jsx` has zero
     `data-testid` on any `MenuItem`, confirmed via source read, lines 34/50/66):
     `secret-actions-menu-edit-value` (line 34), `secret-actions-menu-hide`
     (line 50), `secret-actions-menu-delete` (line 66). All three are static —
     only one instance of this menu is ever open at a time (`anchorEl` is a
     single row-scoped state value), so no per-row parameterization is needed;
     uniqueness confirmed (zero existing hits on EliteaUI `main`).
   - Note: `SecretActionsMenu.jsx`'s `Hide` item only renders `{!isNew}` — not
     relevant here since by the time the menu opens the row is already saved
     (`isNew` is a pending-row-only flag), confirmed live (Hide was present).
5. Click **"Delete"** (testid `secret-actions-menu-delete`).
   - **Verify**: a confirmation dialog appears — reuses the **shared**
     `Modal.DeleteEntityModal` component (confirmed via source read,
     `DeleteEntityModal.jsx`), same testids as every other page using it:
     `delete-confirm-dialog` (dialog root), `delete-confirm-message` (body
     text — confirmed live exact text `"Are you sure to delete the
     <name>? Enter the name to complete the action."`), `delete-confirm-name-input`
     (empty, requires typing the exact secret name), `delete-confirm-cancel-button`,
     `delete-confirm-button`.
   - **Verify**: `delete-confirm-button` renders **disabled** until the typed
     name exactly matches (confirmed live — DOM `disabled` attribute true
     pre-type, false after typing the exact generated name).
6. Type the generated secret's exact name into `delete-confirm-name-input`, then
   click `delete-confirm-button`.
   - **Verify**: a `DELETE /api/v2/secrets/secret/default/${ELITEA_PROJECT_ID}/<name>`
     request fires and resolves **204 No Content** (confirmed live via network
     capture — side-channel proof of persistence, not just DOM removal),
     followed by a `GET` refetch of the collection endpoint. A success toast
     appears with exact text `"The <name> secret has been successfully
     deleted."` (confirmed live, no dedicated testid on the toast — assert via
     the refetch + row-count instead, don't gate on toast text alone).
7. **Verify** the secret is removed from the table: with the search filter still
   active on the generated name, the table renders the empty state text
   **"No secrets"** (confirmed live — no `data-testid` on this empty-state
   `Typography`, source-confirmed; assert via `secret_row` count === 0 scoped
   to the filtered result instead of the untestidded empty-state text, per
   locator policy — testid-only). Pagination total (unfiltered) drops back to
   the pre-create baseline (confirmed live: 103 → 104 after create → 103 after
   delete).
8. Reload the page (`page.reload()`, wait for the secrets-list GET to resolve —
   same technique as `secrets_page.py`'s existing `reload_and_wait()`), re-apply
   the same search filter.
   - **Verify**: the deleted secret still does not reappear — "No secrets" empty
     state / `secret_row` count === 0 (confirmed live: this is a genuine
     server-round-trip check, not a DOM-only assertion — rules out any client-
     cache-only removal race).

## Expected Results
- Three-dot menu opens a dropdown with exactly "Edit value", "Hide", "Delete".
- Clicking Delete opens the shared delete-confirmation modal, requiring the
  exact secret name typed before the Delete button enables.
- Confirming fires `DELETE .../secret/default/{project_id}/{name}` → 204.
- The secret disappears from the table immediately and after a fresh reload
  (server-side deletion confirmed both ways).
- No console errors during the flow (side-channel check, see § Known Defects
  for the one relevant caveat).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Secrets | page loads | step 1 | `step 1`: `secrets-page-title` visible | asserted |
| 2 Click the three-dot menu on any secret row | control responds, next state shown | steps 2–3 | `step 3`: menu opens | asserted *(decomposed — case says "any secret row"; automated as "the row this test itself created", see § Preconditions for why)* |
| 3 Verify dropdown shows Edit value, Hide, Delete | condition holds | step 4 | `step 4`: 3 menuitems, exact text/order | asserted |
| 4 Click "Delete" | control responds, next state shown | step 5 | `step 5`: confirmation dialog appears | asserted |
| 5 Verify a confirmation dialog appears | condition holds | step 5 | `step 5`: `delete-confirm-dialog` visible | asserted |
| 6 Confirm deletion | operation completes, state updates, confirmation shown | step 6 | `step 6`: DELETE 204 + success toast text | asserted |
| 7 Verify the secret is removed from the table | condition holds | step 7 | `step 7`: row count 0 + pagination total | asserted |
| 8 Reload the page — verify the deleted secret does not reappear | action completes, expected UI state | step 8 | `step 8`: fresh-reload row count 0 | asserted |

**Axis 2 — Analyst additions:**
- Step 2 asserts the create-POST resolves 201 before proceeding — *added:
  without this, a slow/failed create would make every later step's "which row"
  ambiguous; reuses ELITEA-2336's own `click_save_button()` return value.*
- Step 5 asserts `delete-confirm-button` is disabled pre-type and enabled only
  on an exact name match — *added: this is the modal's actual safety gate
  (confirmed live) and the case's step 5 text ("verify a confirmation dialog
  appears") under-specifies it; asserting only dialog-visibility would miss a
  regression that let Delete fire without the typed-name gate.*
- Step 6 asserts the DELETE response status (204) via network capture, not just
  the toast — *added: the toast has no testid and its text is a side-channel,
  not proof of persistence; the request/response pair is.*
- Step 7 additionally asserts the unfiltered pagination total, not just the
  filtered empty state — *added: a filtered "No secrets" alone doesn't rule out
  a search-index bug masking a still-existing row; the total count is an
  independent signal.*
- Step 8 asserts via a genuine `page.reload()` server round-trip, not a DOM
  re-check — *added: the case's own step 8 asks for exactly this ("reload the
  page"), made explicit here to prevent an implementer shortcut to a
  client-cache-only check.*

## Cleanup
- None needed — the case's own steps 6–8 delete the generated secret as part
  of the test flow itself (no separate teardown required, unlike ELITEA-2336's
  save-flow secret, which needed manual/API cleanup because the case never
  deletes it).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only, no fallback ladder**
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`) — every
row below is a `data-testid`; three are new (implementer work via
`add-data-testid`), the rest are pre-existing and confirmed live/in-source
this session.

| Element | Testid | Provenance |
|---|---|---|
| Page title | `secrets-page-title` | pre-existing (ELITEA-2336) |
| "+" add button | `secrets-add-button` | pre-existing (ELITEA-2336) |
| Secret row | `secret-row` | pre-existing (ELITEA-2336) |
| Name input (create flow) | `secret-name-input` | pre-existing (ELITEA-2336) |
| Value input (create flow) | `secret-value-input` | pre-existing (ELITEA-2336) |
| Save (✓) button | `secret-row-save-button` | pre-existing (ELITEA-2336), `SecretsTable.jsx:456` |
| **Three-dot / more-actions button** | `secret-row-actions-button` | **testid needed** — `SecretsTable.jsx:511-518`, zero testid today |
| **"Edit value" menu item** | `secret-actions-menu-edit-value` | **testid needed** — `SecretActionsMenu.jsx:34` |
| **"Hide" menu item** | `secret-actions-menu-hide` | **testid needed** — `SecretActionsMenu.jsx:50` |
| **"Delete" menu item** | `secret-actions-menu-delete` | **testid needed** — `SecretActionsMenu.jsx:66` |
| Delete confirmation dialog | `delete-confirm-dialog` | pre-existing — shared `DeleteEntityModal.jsx:129` |
| Delete confirmation message | `delete-confirm-message` | pre-existing — `DeleteEntityModal.jsx:63` |
| Delete confirmation name input | `delete-confirm-name-input` | pre-existing — `DeleteEntityModal.jsx:82` |
| Delete confirmation Cancel button | `delete-confirm-cancel-button` | pre-existing — `DeleteEntityModal.jsx:103` |
| Delete confirmation Delete button | `delete-confirm-button` | pre-existing — `DeleteEntityModal.jsx:112` |

No testid on the search input, the empty-state "No secrets" text, or the
success toast — all confirmed live/in-source. None are needed: the search
input is not asserted on directly (only used as a filter mechanism, matching
the digest's prior note that it's unexercised); the empty state and toast are
BOTH avoidable via the `secret-row` count / network-capture assertions already
specified above (asserting via a state-dependent element with no stable
testid would violate locator policy — this AFS routes around it rather than
requesting testids the case doesn't strictly need).

## Network Behavior
- `POST /api/v2/secrets/secrets/default/{project_id}` — create (step 2), `201`.
- `GET /api/v2/secrets/secrets/default/{project_id}` — list refetch, fires after
  create, after delete, and on every navigate/reload.
- `DELETE /api/v2/secrets/secret/default/{project_id}/{name}` — fires on
  confirming delete (step 6), `204 No Content`. Same endpoint the digest's
  ELITEA-2336 cleanup shortcut already documented for API-side cleanup.

## Known Defects Found During Exploration
None newly found. Known defect `EliteaAI/elitea-testing-public#1203` (OPEN —
React "Maximum update depth exceeded" console warning on every `/settings/secrets`
mount) was **NOT observed** during this session — 0 console errors/warnings
across the full navigate → create → delete → reload flow (two full page loads).
This is the same inconclusive pattern ELITEA-2337's AFS already documented
(fires deterministically in the covering test's own automated run, but not in
every live exploration session). Per the same decision tree that AFS uses: the
implementer should check their own automated run's console output rather than
assume either way — if `#1203` fires, wrap the console-error assertion(s) with
`expect.soft()` + `# Known defect: #1203` (sanctioned-RED per
`.agents/testing.md` § Merge gate); if it doesn't fire, assert cleanly. This
case adds no NEW defect.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: extend `automation/pages/secrets_page.py` — reuse
  `navigate()`, `click_add_button()`, `fill_new_row()`, `click_save_button()`
  verbatim from ELITEA-2336 for step 2 (create the target secret); add new
  methods for the three-dot menu, menu items, and delete-confirmation flow
  (the confirmation modal's testids may already exist as class fields on a
  shared `delete_entity_modal` component/mixin if one exists elsewhere in
  `automation/pages/` — grep `delete-confirm-` before adding new
  `LocatorDescriptor`s to avoid duplicating an existing shared modal page
  object).
- Wait strategy: `page.expect_response()` for the create POST (201), the
  delete DELETE (204), and the two GET refetches — never a fixed sleep, per
  `.agents/testing.md`. The search-filter live-update needs a short
  `browser_wait_for`-equivalent (`expect(locator).to_have_text(...)` /
  polling on pagination text), confirmed live it settles within ~2s with no
  Enter keypress needed.
- Search input has no testid — use `get_by_placeholder("Search")` **only**
  if unavoidable; prefer scoping via `secret_row.filter(has_text=name)`
  directly on the unfiltered table instead, which needs no search interaction
  at all and stays fully testid-based. (Analyst used search live only to keep
  exploration screenshots small — not a mandated automation technique.)

## Automation gap this case surfaces (report to the lead)
Three testids are net-new work (`secret-row-actions-button`,
`secret-actions-menu-edit-value`, `secret-actions-menu-hide`,
`secret-actions-menu-delete` — four, not three; corrected count in the handles
table above) on app-owned JSX (`SecretsTable.jsx`, `SecretActionsMenu.jsx`),
not a #579 exception — standard `add-data-testid` implementer work, flagged
here per contract, not treated as a blocker.
