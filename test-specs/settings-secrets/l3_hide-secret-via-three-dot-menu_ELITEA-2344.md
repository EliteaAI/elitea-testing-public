# Test Case: Hide option permanently removes the secret from the Secrets table

## Metadata
- **TMS ID**: ELITEA-2344
- **Source case**: `.agents/automation/elitea-2344-hide-secret/cases/ELITEA-2344.md`
- **Linked Story**: none · **Tracking issue**: EliteaAI/elitea-testing-public#852
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
- **Do not target a pre-existing/real secret for hiding.** The project has 100+
  real secrets in live use (`auth_token`, `default_llm_model_name`, …) — hiding
  one via this flow is NOT reversible via the UI (no unhide affordance was found
  live), so it would permanently corrupt shared test data. This case MUST create
  its own run-unique secret first (via the existing inline "+" flow,
  `secrets_page.py`'s `click_add_button()` / `fill_new_row()` / `click_save_button()`
  — already covered by ELITEA-2336) and hide THAT one. This also sidesteps the
  `isDefault` prop that disables all three actions-menu items for system/default
  secrets (`SecretActionsMenu.jsx` — `disabled={isDefault}` on every `MenuItem`,
  same gate ELITEA-2338 confirmed for Delete) — confirmed live: a freshly-created
  secret is never `isDefault`.

## Test Data
### generated-per-run
- Secret name: a run-unique value, e.g. `f"autotest_hide_{uuid4().hex[:8]}"` —
  same non-idempotent-literal rationale as ELITEA-2336/2338's AFS. Confirmed
  live twice this session with `autotest_hide_2344` (once hidden, once
  recreated with the same name for step 9 — see below).
- Secret value: any non-empty string, e.g. `"hide-test-value-123"` — no format
  validation beyond max-length (shared with name field, `SECRET_NAME_PATTERN`
  only constrains the NAME field).

## Test Steps
1. Navigate to `${BASE_URL}/settings/secrets`.
   - **Verify**: page title testid `secrets-page-title` is visible with exact
     text "Secrets".
2. Create a run-unique secret via the existing inline "+" flow (`secrets-add-button`
   → `secret-name-input` / `secret-value-input` → `secret-row-save-button`) and
   confirm the `POST /api/v2/secrets/secrets/default/${ELITEA_PROJECT_ID}` create
   request resolves **201 Created** (confirmed live, reused mechanics from
   ELITEA-2336/2338's `click_save_button()`, which already returns the
   `Response` for this exact assertion). *(This step also decomposes case
   step 2, "Note the name of the secret to be hidden" — the generated name IS
   the noted name, captured as a Python variable, not a separate UI action.)*
3. Locate the created secret's row (`get_row_by_name(name)` — confirmed live
   working reuse of ELITEA-2338's technique) and click its **three-dot ("more
   actions") button** (`secret-row-actions-button` — pre-existing testid,
   added by ELITEA-2338's implementation, confirmed live present and working
   this session).
   - **Verify**: the actions dropdown menu opens (confirmed live —
     `SecretActionsMenu.jsx`, MUI `<Menu>`, `open={!!anchorEl}`) — same
     signal as ELITEA-2338 uses: `secret-actions-menu-delete` (or any menu
     item) becomes visible.
   - **DECLARED IMPROVISATION reminder (not new — inherited from ELITEA-2338,
     `secrets_page.py`'s existing `open_row_actions_menu()`):** a real
     Playwright `.click()` on this button was **non-deterministic across this
     case's own two menu-opens this session** — the FIRST open (hiding the
     original secret) succeeded with a plain `.click()`; the SECOND open
     (deleting the recreated cleanup secret, same button, same page, no
     reload between) did **not** open the menu with a plain `.click()` and
     required the existing React-`onClick` workaround. This is a **new,
     stronger data point** for the non-determinism ELITEA-2343's digest entry
     already flagged (that session's single re-test succeeded with a normal
     click and called the original root cause "not reproduced either way") —
     this session reproduces the ORIGINAL failure mode a second time, same
     button, same DOM structure, different call. **Implementer: keep using
     the existing `open_row_actions_menu()` workaround unconditionally — do
     not attempt to "simplify" it to a plain click** based on ELITEA-2343's
     single contrary data point; this case's own evidence outweighs it 1
     success vs 1 failure, and the workaround is a safe superset either way
     (see `EliteaAI/elitea-testing-public#1222`, already open, tracking the
     root-cause investigation).
4. Click **"Hide"** (testid `secret-actions-menu-hide` — pre-existing, added by
   ELITEA-2338's implementation for the menu-item-order case; renders only
   `{!isNew}`, irrelevant here since the row is already saved by step 2).
5. **Verify** a confirmation dialog appears, showing the hide warning.
   - **CASE-TEXT DRIFT (filed as clarification, not a defect —
     `EliteaAI/elitea-testing-public#1226`):** the case's step 5 quotes
     *"Once hidden, the secret is completely removed from the Secrets table
     and will no longer be visible in the UI. Hidden secrets cannot be
     unhidden."* The **live** dialog (confirmed via DOM read this session,
     source `SecretsTable.jsx` ~line 615 / `AlertDialog.jsx`) shows:
     - Title: `"Hide secret?"`
     - Body (exact): `Are you sure to hide the secret "<name>"? Once hidden,
       the secret will no longer be visible.`
     - Confirm button text: `"Hide"`
     This AFS asserts the **live** copy, per the reverse-masking guard —
     the case text is what's stale.
   - **Testid needed**: `alert-dialog-content` — the confirmation body text
     (`StyledDialogContentText` in `src/components/AlertDialog.jsx`, styled
     `MuiDialogContentText`) carries **zero** `data-testid` today (confirmed
     in source — only an `id="alert-dialog-description"` ARIA id, which is
     not a valid locator basis per this project's testid-only policy). This
     is a **shared, generic component** (`src/components/AlertDialog.jsx` is
     used by multiple features, not secrets-specific — confirmed via `git grep`
     showing 4+ other call sites: `AttachmentSettingsModal.jsx`,
     `ToolkitsOperationButtons.jsx`, others reference the sibling
     `alert-dialog-title` ARIA id pattern), so the testid must be **generic**
     (`alert-dialog-content`), never feature-scoped (`secret-hide-alert-content`
     would violate `.agents/testing.md`'s "shared components never hardcode
     feature-scoped testids" rule). Uniqueness confirmed — zero existing hits
     for `alert-dialog-content` on `main` or `automation/testids`.
   - Confirm button testid: `alert-dialog-confirm-button` — **pre-existing**,
     confirmed live and in source (`AlertDialog.jsx` line 78) — this is
     ALREADY a generic, shared testid (not row-scoped: the row-scoped
     `id={`alert-dialog-${row.id}`}` prop passed at the `SecretsTable.jsx`
     call site is silently dropped — `AlertDialog.jsx` doesn't destructure or
     forward an `id` prop — confirmed by source read; harmless here because
     MUI only mounts the `open`-gated instance into the DOM, so exactly one
     `[role="dialog"]` exists at a time, confirmed live via
     `document.querySelector('[role="dialog"]')` returning a single match
     immediately after clicking Hide).
6. Confirm the action — click `alert-dialog-confirm-button`.
   - **Verify**: a `POST /api/v2/secrets/hide/default/${ELITEA_PROJECT_ID}/<name>`
     request fires and resolves **200 OK** (confirmed live via network
     capture — side-channel proof of persistence, not just DOM removal),
     followed by a `GET` refetch of the collection endpoint (same
     refetch-after-mutation pattern as create/delete). No success toast text
     was confirmed for this specific flow this session (not asserted — the
     network response + row-count are the stable proof, same discipline as
     ELITEA-2338's DELETE assertion).
7. **Verify** the secret is no longer visible in the Secrets table.
   - Confirmed live via BOTH: (a) `secret_row` count scoped to a search
     filter on the generated name → 0 rows / "No secrets" empty state
     (same testid-only routing as ELITEA-2338 — no testid on the empty-state
     text, assert via row count instead); (b) the unfiltered pagination total
     dropping back to the pre-create baseline (confirmed live: 103 → 104
     after create → 103 after hide).
8. Reload the page (`page.reload()`, wait for the secrets-list GET to resolve —
   `secrets_page.py`'s existing `reload_and_wait()`), re-apply the same search
   filter.
   - **Verify**: the hidden secret still does not reappear — "No secrets" /
     `secret_row` count === 0 (confirmed live: this is a genuine server
     round-trip check — the hide mutation is server-persisted, not a
     client-cache-only removal, same proof shape as ELITEA-2338's delete).
9. **Verify** the "+" button is available to create a new secret with the same
   name if needed.
   - Confirmed live as a CONCRETE re-creation, not just a visibility check:
     clicked `secrets-add-button` (confirmed enabled post-hide, no gating
     logic ties it to row count/state — matches the digest's prior
     ELITEA-2336/2337/2338 observation), typed the **exact same** generated
     name into `secret-name-input`, confirmed `secret-row-save-button` was
     **enabled** with **no** `secret-name-error` (i.e. no client-side
     name-collision validation), clicked Save, and confirmed the
     `POST .../secrets/default/${ELITEA_PROJECT_ID}` create request resolved
     **201 Created** (not a 409/400 conflict) — proving the backend does NOT
     reject a name that was previously hidden. Pagination total rose back to
     104 and the row reappeared with the new (recreated) value. This is a
     stronger assertion than the case's own step 9 text implies (which only
     asks to verify the button is "available") — *added*, because "the
     button is clickable" alone doesn't prove the functional claim in the
     case's own Objective ("verify the '+' button is available to create a
     new secret with the same name if needed" — the value-add is specifically
     THAT the same name is accepted, not merely that a button exists).

## Expected Results
- Three-dot menu opens (same mechanism/caveat as ELITEA-2338).
- Clicking "Hide" opens a confirmation dialog with the live copy (title
  `"Hide secret?"`, body per § step 5 above, confirm button `"Hide"`) — NOT
  the case's quoted text (case-text drift, filed as clarification #1226).
- Confirming fires `POST .../secrets/hide/default/{project_id}/{name}` → 200,
  followed by a list refetch.
- The secret disappears from the table immediately and after a fresh reload
  (server-side persistence confirmed both ways) — no UI affordance to unhide
  was found (consistent with, though not textually confirmed by, the case's
  "cannot be unhidden" claim).
- The "+" button remains available and a NEW secret with the exact same name
  can be created successfully (201, not a conflict) after the original is
  hidden.
- No console errors during the flow (side-channel check — see § Known Defects).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Secrets | page/section loads | step 1 | `step 1`: `secrets-page-title` visible | asserted |
| 2 Note the name of the secret to be hidden | action completes, expected UI state | step 2 | `step 2`: generated name captured as a variable + 201 create proof | asserted *(decomposed — "noting" a name is a Python-side capture, not a separate UI action; see step 2's note)* |
| 3 Click the three-dot menu on that secret row | control responds, next state shown | step 3 | `step 3`: menu opens (existing declared-improvisation workaround) | asserted |
| 4 Click "Hide" | control responds, next state shown | step 4 | `step 4`: `secret-actions-menu-hide` clicked | asserted |
| 5 Verify a confirmation warning is shown stating: "…" | condition holds as described | step 5 | `step 5`: **live copy asserted, NOT the case's quoted text** — see case-text-drift note, clarification #1226 filed | asserted *(text corrected — case text is stale, reverse-masking guard)* |
| 6 Confirm the action | operation completes, state updates, confirmation shown | step 6 | `step 6`: `POST .../hide/...` → 200 + refetch | asserted |
| 7 Verify the secret is no longer visible in the Secrets table | condition holds | step 7 | `step 7`: row count 0 (filtered) + pagination total (unfiltered) | asserted |
| 8 Reload the page — verify the secret does not reappear | action completes, expected UI state | step 8 | `step 8`: fresh-reload row count 0 | asserted |
| 9 Verify the "+" button is available to create a new secret with the same name if needed | condition holds | step 9 | `step 9`: `secrets-add-button` enabled + actual recreate with same name → 201 | asserted *(strengthened — see step 9's note)* |

**Axis 2 — Analyst additions:**
- Step 2 asserts the create-POST resolves 201 before proceeding — *added: same
  rationale as ELITEA-2338 — without this, a slow/failed create would make
  every later step's "which row" ambiguous.*
- Step 5 asserts the LIVE confirmation-dialog copy instead of the case's
  quoted text — *added/corrected: the case text is stale (confirmed via
  source read + live DOM read); asserting the stale text would make the test
  itself lie about what the product actually says. Filed as clarification
  `EliteaAI/elitea-testing-public#1226`, not a defect, per the reverse-masking
  guard.*
- Step 6 asserts the hide-mutation response status (200) via network capture,
  not just the resulting DOM change — *added: same "network is the proof,
  not the DOM alone" discipline as ELITEA-2338's DELETE assertion.*
- Step 7 additionally asserts the unfiltered pagination total, not just the
  filtered empty state — *added: same rationale as ELITEA-2338 — a filtered
  "No secrets" alone doesn't rule out a search-index bug masking a
  still-existing row.*
- Step 9 asserts an ACTUAL recreation with the same name (not just button
  visibility/enabled state) — *added: this is the case's own stated
  "Objective"/"Expected Final State", and a button-visibility-only check
  would not prove the functional claim it exists to verify (see step 9's
  note for the full reasoning).*

## Cleanup
- **Required** (unlike ELITEA-2338, whose own steps delete the target secret):
  step 9 recreates a live, visible secret with the same generated name — this
  one is NOT hidden and WILL pollute shared project data if left behind.
  Delete it via the UI delete flow (three-dot → Delete → type name → confirm
  — reuse ELITEA-2338's `click_delete_menu_item()` / `fill_delete_confirm_name()`
  / `confirm_delete()` verbatim) as the test's own teardown/fixture, OR via
  the documented API shortcut (`DELETE /api/v2/secrets/secret/default/{project_id}/{name}`
  → `204`, same endpoint, per `_surface.md` § Delete flow's cleanup shortcut).
  Confirmed live both work; this session used the UI flow for the final
  cleanup and confirmed the pagination total returned to the exact
  pre-test baseline (103).
- The ORIGINALLY hidden secret (before step 9's recreation) needs no cleanup
  action — it is already removed from the visible table by the case's own
  steps 6–8; no UI affordance to "un-hide" or otherwise touch it was found.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only, no fallback ladder**
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`).

| Element | Testid | Provenance |
|---|---|---|
| Page title | `secrets-page-title` | pre-existing (ELITEA-2336) |
| "+" add button | `secrets-add-button` | pre-existing (ELITEA-2336) |
| Secret row | `secret-row` | pre-existing (ELITEA-2336) |
| Name input (create flow) | `secret-name-input` | pre-existing (ELITEA-2336) |
| Value input (create flow) | `secret-value-input` | pre-existing (ELITEA-2336) |
| Save (✓) button | `secret-row-save-button` | pre-existing (ELITEA-2336) |
| Name validation error | `secret-name-error` | pre-existing (ELITEA-2337) — used in step 9 to confirm NO collision error |
| Three-dot / more-actions button | `secret-row-actions-button` | pre-existing (ELITEA-2338) |
| "Hide" menu item | `secret-actions-menu-hide` | pre-existing (ELITEA-2338) |
| "Delete" menu item (cleanup only) | `secret-actions-menu-delete` | pre-existing (ELITEA-2338) |
| **Hide-confirmation dialog body text** | `alert-dialog-content` | **testid needed** — `src/components/AlertDialog.jsx`, `StyledDialogContentText`, zero testid today. **Generic/shared** — do not scope to secrets. |
| Hide-confirmation confirm button | `alert-dialog-confirm-button` | pre-existing — `AlertDialog.jsx` line 78, already generic/shared |
| Delete confirmation dialog (cleanup only) | `delete-confirm-dialog` | pre-existing — shared `DeleteEntityModal.jsx` |
| Delete confirmation name input (cleanup only) | `delete-confirm-name-input` | pre-existing — shared `DeleteEntityModal.jsx` |
| Delete confirmation button (cleanup only) | `delete-confirm-button` | pre-existing — shared `DeleteEntityModal.jsx` |

No testid needed on the Hide-dialog's title ("Hide secret?") or Cancel
button — neither is exercised by this case's own steps (only the body text
and the confirm button are asserted/clicked); adding either would violate
the "scope = elements the test touches" rule.

## Network Behavior
- `POST /api/v2/secrets/secrets/default/{project_id}` — create (steps 2, 9),
  `201`.
- `GET /api/v2/secrets/secrets/default/{project_id}` — list refetch, fires
  after create, after hide, on navigate/reload.
- `POST /api/v2/secrets/hide/default/{project_id}/{name}` — fires on
  confirming Hide (step 6), `200 OK`. **Distinct URL shape** from the DELETE
  endpoint (`.../secret/...` singular, DELETE method) — this is
  `.../hide/...` (singular "secret" is NOT in this path segment; confirmed
  live full path `secrets/hide/default/399/<name>`), `POST` method.
- `DELETE /api/v2/secrets/secret/default/{project_id}/{name}` — cleanup only
  (step 9's recreated secret), `204`.

## Known Defects Found During Exploration
None newly found. Known defect `EliteaAI/elitea-testing-public#1203` (OPEN —
React "Maximum update depth exceeded" console warning on every
`/settings/secrets` mount) was **NOT observed** during this session — 0
console errors/warnings across the full navigate → create → hide → reload →
recreate → delete-cleanup flow (three full page loads/navigations). Same
inconclusive pattern already documented by ELITEA-2337/2338's AFS. Per the
same decision tree: the implementer should check their own automated run's
console output rather than assume either way — if `#1203` fires, wrap the
console-error assertion(s) with `expect.soft()` + `# Known defect: #1203`
(sanctioned-RED per `.agents/testing.md` § Merge gate); if it doesn't fire,
assert cleanly. This case adds no NEW defect.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: extend `automation/pages/secrets_page.py` — reuse `navigate()`,
  `click_add_button()`, `fill_new_row()`, `click_save_button()`,
  `get_row_by_name()`, `open_row_actions_menu()` (**with its existing
  declared-improvisation workaround — do not simplify to a plain click**, see
  step 3's note) verbatim from ELITEA-2336/2338. Add new methods:
  `click_hide_menu_item()` (click `actions_menu_hide`, wait for
  `alert-dialog-content` visible), `get_hide_confirm_text()` (read
  `alert-dialog-content`'s text content), `confirm_hide()` (click
  `alert-dialog-confirm-button`, `page.expect_response()` for the
  `POST .../hide/...` 200 + the list-GET refetch concurrently — same dual-wait
  shape as ELITEA-2338's `confirm_delete()`).
- Wait strategy: `page.expect_response()` for the create POST (201), the hide
  POST (200), and the GET refetches — never a fixed sleep, per
  `.agents/testing.md`.
- Step 9's recreate-with-same-name flow reuses `click_add_button()` /
  `fill_new_row()` / `click_save_button()` again verbatim — assert the
  returned `Response.status == 201` (not 409/400) as the core proof, plus
  `expect(name_error).to_have_count(0)` (or `not_to_be_visible()`) right
  after typing the name, before Save, as a secondary client-side signal.
- Reuse `secrets_page.py`'s `SECRET_ACTIONS_MENU_ITEM_PREFIX_SELECTOR` if
  asserting the full 3-item menu order is also desired here (not required by
  this case's steps — ELITEA-2338 already covers that assertion — but
  available if the implementer wants a defensive re-check before clicking
  Hide specifically).

## Automation gap this case surfaces (report to the lead)
One testid is net-new work (`alert-dialog-content`) on a **shared** component
(`src/components/AlertDialog.jsx`) used by multiple features beyond Secrets —
standard `add-data-testid` implementer work, flagged here per contract, not
treated as a blocker. Because the component is shared, this testid becomes
available to every other feature using `AlertDialog` the moment it lands,
not just this case.
