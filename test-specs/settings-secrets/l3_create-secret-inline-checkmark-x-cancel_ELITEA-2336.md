# Test Case: Create secret inline — "+" adds editable row, checkmark saves, X cancels

## Metadata
- **TMS ID**: ELITEA-2336
- **Source case**: `.agents/automation/elitea-2336-secrets-inline-create/cases/` (snapshot MISSING —
  fetched directly from
  `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/settings/secrets/ELITEA-2336_create-secret-inline-adds-editable-row-checkmark-saves-x-can.md`;
  see § Automation Hints "Analysis gap" for the flag)
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter `priority: medium`). **pytest marker:
  `@pytest.mark.p2`** — medium→l3→p2 convention, confirmed against
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
- No precondition on existing secret data — the project already has 100+ secrets
  live (confirmed: "1 - 10 of 103" at exploration start), so this case is
  unaffected by whether the table is populated. **Do not assume an empty table.**

## Test Data
### generated-per-run
- Secret name: a run-unique value, e.g. `f"autotest_secret_{uuid4().hex[:8]}"` —
  **do not hardcode the case's literal example `autotest_secret`** (confirmed live:
  the name field only rejects non-`[A-Za-z0-9_]` characters
  (`SECRET_NAME_PATTERN` in `EditSecretInputGridTable.jsx`), not a duplicate name
  against another live secret — a fixed literal risks colliding with leftover data
  from a prior/failed run and is non-idempotent across repeated CI runs before
  cleanup completes). Use a run-unique name for both the save-flow secret and the
  cancel-flow secret (two different names, since both are created in the same
  session — see Test Steps 7-9).
- Secret value: any non-empty string, e.g. `"my-secret-value-123"` (case's literal
  example) — the value field has no format validation beyond the max-length limit
  (`MAX_VARIABLES_LENGTH`, shared with the name field).

## Test Steps
1. Navigate to `${BASE_URL}/settings/secrets`.
   - **Verify**: page title testid `secrets-page-title` is visible with exact text
     "Secrets"; at least one existing secret row (testid `secret-row`) is visible
     (table is pre-populated in this project, not empty).
2. Click the "+" (add) button — testid `secrets-add-button`.
   - **Verify**: the add button (`secrets-add-button`) becomes disabled immediately
     after click (confirmed live — `DrawerPageHeader`'s `addButton.disabled` prop
     is `true` while any row is in edit mode; re-enables when the row is saved or
     cancelled — step 6/9 verify this).
3. **Verify** a new inline editable row appears **as the FIRST row of the table,
   INSIDE the same `GridTableRow`/table structure (testid `secret-row`) as the
   existing rows** — NOT a modal/dialog (confirmed live: no `role="dialog"`
   element renders; the row is a normal table row containing two textboxes +
   checkmark/X icon buttons, testids `secret-name-input` / `secret-value-input`
   / `secret-row-save-button` / `secret-row-cancel-button`).
   - **Case-text note (filed as clarification, EliteaAI/elitea-testing-public#1202):**
     the case says the row appears "at the current pagination position" — live
     behaviour is different and MUST be asserted as the actual contract, not the
     case's literal wording (reverse-masking guard): clicking "+" **always resets
     pagination to page 1** (`SecretsContent.jsx addSecretRow()` calls
     `resetPaginationRef.current?.()` unconditionally) and inserts the new row as
     page 1's first row, regardless of which page was showing beforehand.
     Automation should assert: pagination indicator reads "1 - N of `<total+1>`"
     after clicking "+" (client-side count includes the still-unsaved pending
     row — confirmed live: table showed "1 - 10 of 103" before, "1 - 10 of 104"
     immediately after clicking "+", before Save/Cancel).
4. Enter name `<generated_name>` into the name input (testid `secret-name-input`,
   auto-focused) and value `"my-secret-value-123"` into the value input (testid
   `secret-value-input`).
   - **Verify**: both inputs display the entered text (confirmed live via
     `input_value()`/snapshot — plain MUI text inputs, no masking while editing).
5. Click the ✓ (checkmark/save) icon — testid `secret-row-save-button`.
   - **Verify**: a `POST /api/v2/secrets/secrets/default/${ELITEA_PROJECT_ID}`
     request fires and resolves **201 Created** (confirmed live via network
     capture — side-channel proof the secret was actually persisted, not just
     that the row re-rendered from stale client state), followed by a `GET`
     refetch of the same collection endpoint.
6. **Verify** the row saves and exits edit mode:
   - The saved row (testid `secret-row`, scoped via `.filter(has_text=<generated_name>)`)
     shows the name cell (testid `secret-name-cell` within that row) with exact
     text `<generated_name>`.
   - The value cell (testid `secret-value-cell` within that row) shows the exact
     masked placeholder text `"{{secret." + <generated_name> + "}}"` — confirmed
     live rendering pattern (`SecretsContent.jsx` builds `secret_name` from the
     API response; `SecretValueCell.jsx` renders it verbatim as the button label).
   - The add button (`secrets-add-button`) is re-enabled (no row in edit mode).
   - The row is positioned alphabetically among existing rows by name, ascending
     (confirmed live: `useTableSort` default `{field: 'name', direction: 'asc'}` —
     the saved row is NOT pinned to the top; only an unsaved/pending row is).
7. Click "+" again (testid `secrets-add-button`) — enter a second, different
   generated name (e.g. `<generated_name_2>`) into `secret-name-input` and any
   value into `secret-value-input`.
   - **Verify**: same new-row behavior as steps 2-4 (add button disabled, row
     appears, inputs accept the typed values).
8. Click the ✗ (close/cancel) icon — testid `secret-row-cancel-button`.
   - **Verify**: **no** `POST` request fires as a result of this click (confirmed
     live via network capture — cancel is purely a client-side state removal, the
     row's data never reaches the backend).
9. **Verify** the row is discarded and no secret is created:
   - No row (testid `secret-row`) with text `<generated_name_2>` exists anywhere
     in the table (search across all pages, or assert row count returns to its
     pre-step-7 value).
   - `GET /api/v2/secrets/secrets/default/${ELITEA_PROJECT_ID}` (re-fetch, e.g.
     after a page reload) does **not** contain `<generated_name_2>` — confirms
     server-side non-existence, not just a stale client render.
   - The add button (`secrets-add-button`) is re-enabled.

## Expected Results
- Clicking "+" adds an inline editable row (not a modal), always at page 1 top,
  resetting pagination if the user was elsewhere.
- Checkmark (✓) persists the secret via `POST .../secrets/secrets/default/{project}`
  (201) and the row settles into its alphabetically-sorted position showing the
  masked `{{secret.<name>}}` placeholder.
- X (✗) discards the pending row client-side only — zero network calls, no secret
  created server-side.
- No console errors across the full create → verify → cancel → verify flow
  (confirmed live: 0 errors, 0 warnings).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Secrets | page/section loads | step 1 | `step 1`: page title + ≥1 existing row visible | asserted |
| 2 Click the "+" button | control responds | step 2 | `step 2`: add button disabled | asserted |
| 3 Verify new inline editable row appears at current pagination position (not modal/dialog) | condition holds | step 3 | `step 3`: row inside table structure, no dialog; pagination resets to page 1 (case wording corrected — see clarification #1202) | asserted *(clarification)* |
| 4 Enter name "autotest_secret" and value "my-secret-value-123" | field accepts + displays input | step 4 | `step 4`: input values match typed text | asserted *(generated names used instead of the literal example — see Test Data)* |
| 5 Click the ✓ (checkmark) icon | control responds | step 5 | `step 5`: POST 201 fires | asserted |
| 6 Verify row saves and shows "autotest_secret" with masked "{{secret.autotest_secret}}" value | condition holds | step 6 | `step 6`: name-cell + value-cell text | asserted |
| 7 Click "+" again — enter any name and value | control responds | step 7 | `step 7`: same new-row assertions with 2nd generated name | asserted |
| 8 Click the ✗ (close/cancel) icon | control responds | step 8 | `step 8`: no POST fires | asserted |
| 9 Verify the row is discarded and no secret is created | condition holds | step 9 | `step 9`: row absent from DOM + absent from re-fetched GET | asserted |

### Axis 2 — Analyst additions

- `step 2`/`step 7` assert the add button's disabled state while a row is in
  edit mode — *added: confirmed live this is a real product guard (only one row
  editable at a time), and it's the mechanism that makes the row-scoped
  locators in step 6 unambiguous (no risk of two simultaneous edit rows).*
- `step 5` asserts the exact `POST` status (201) and endpoint — *added: the
  case only says "control responds"; the network proof is what distinguishes a
  real persisted secret from a client-side-only render, directly relevant given
  step 9 explicitly needs the inverse (no network call) as its proof of
  cancellation.*
- `step 6` asserts alphabetical-sort position of the saved row — *added:
  confirmed live behavior (`useTableSort` default asc-by-name); guards against
  a regression that pins saved rows to the top like pending ones.*
- `step 9` asserts server-side non-existence via a fresh `GET`, not just DOM
  absence — *added: DOM absence alone doesn't rule out a race where the POST
  fired anyway; this closes that gap given step 8's own "no POST" assertion
  should already guarantee it, this is a second, independent proof.*
- No console errors across the whole flow — *added: confirmed live 0
  errors/0 warnings; standard side-channel guard per project convention.*

## Cleanup
This case creates ONE real secret under `${ELITEA_PROJECT_ID}` (399) — the
step-4/6 secret (`<generated_name>`); the step 7-9 secret is never persisted
(that's the assertion), so nothing to clean up there.

1. Delete via the API directly (no UI testids exist for the row's dots-menu /
   Delete-menu-item / hide flow — `SecretActionsMenu.jsx` has zero testids, and
   this case's own steps never exercise delete, so adding new testids for
   cleanup-only UI is out of scope; use the generic API client instead, same
   pattern as e.g. `agent_api.delete_agent()` teardown):
   ```python
   response = api_client.delete(
       f"/secrets/secret/default/{project_id}/{generated_name}"
   )
   assert response.status_code == 204
   ```
   Confirmed live: `DELETE /api/v2/secrets/secret/default/399/autotest_secret` →
   `204 No Content` (exploration cleanup, same endpoint the UI's own delete flow
   calls — verified by triggering it manually through the UI during exploration,
   then confirming the same path via direct API call is equivalent).
2. No cleanup needed for project state, pagination, or search — none of those
   are mutated by this test beyond the one secret.

## Concrete Handles (discovered during exploration)

**AMENDED post-implementation (fix round 1, ELITEA-2336 review) — the table below
originally claimed all handles were "pre-existing testids" and "zero new
`add-data-testid` work required". That claim was FALSE.** All 9 core handles were
actually **uncommitted working-tree JSX edits** in the EliteaUI clone at analysis
time — visible live (hence "confirmed live" in the analyst's notes) but never
committed to `automation/testids`, so from any fresh clone's perspective they did
not exist. The implementer committed all 9 plus one additional NEW testid
(`secrets-pagination-info`, needed for step 3's pagination-reset assertion) as
`EliteaAI/EliteaUI@c2a5b4c7` on `automation/testids` — confirmed via
`git log origin/main..origin/automation/testids -- src/ | grep 2336` (present on
`automation/testids`, absent from `main` as of this amendment). This IS
`add-data-testid` work, not zero-touch reuse of pre-existing identity.

| Element | Testid (LocatorDescriptor) | Provenance | Notes |
|---|---|---|---|
| Page title | `secrets-page-title` | **added** — `EliteaAI/EliteaUI@c2a5b4c7`, on `automation/testids` only (not yet on `main`) | `DrawerPageHeader titleTestId` prop, `SecretsContent.jsx` |
| Add ("+") button | `secrets-add-button` | **added** — `EliteaAI/EliteaUI@c2a5b4c7`, on `automation/testids` only | `DrawerPageHeader` `slotProps.addButton.testId`; also wired as the `SECRETS_TOUR_TARGET_IDS.addButton` interactive-tour anchor — same element, dual purpose |
| Secret row (repeatable) | `secret-row` | **added** — `EliteaAI/EliteaUI@c2a5b4c7`, on `automation/testids` only | `GridTableRow`'s `data-testid` prop, `SecretsTable.jsx`; identical for every row (new + existing) — scope with `.filter(has_text=<name>)`, same pattern as `personal_tokens_page.py`'s `token_row` |
| Name input (edit mode) | `secret-name-input` | **added** — `EliteaAI/EliteaUI@c2a5b4c7`, on `automation/testids` only | `EditSecretInputGridTable.jsx` `inputProps['data-testid']`, `field === 'name'` branch — only rendered for `row.isNew` rows (existing secrets can't rename, only re-value) |
| Value input (edit mode) | `secret-value-input` | **added** — `EliteaAI/EliteaUI@c2a5b4c7`, on `automation/testids` only | Same component, `field === 'value'` branch |
| Save (✓) button | `secret-row-save-button` | **added** — `EliteaAI/EliteaUI@c2a5b4c7`, on `automation/testids` only | `SecretsTable.jsx` `IconButton`, only rendered while the row is in edit mode |
| Cancel (✗) button | `secret-row-cancel-button` | **added** — `EliteaAI/EliteaUI@c2a5b4c7`, on `automation/testids` only | Same |
| Name cell (view mode) | `secret-name-cell` | **added** — `EliteaAI/EliteaUI@c2a5b4c7`, on `automation/testids` only | `Text.EllipsisTypography`, `SecretsTable.jsx`, scope within a `secret_row` locator |
| Value cell (view mode, masked) | `secret-value-cell` | **added** — `EliteaAI/EliteaUI@c2a5b4c7`, on `automation/testids` only | `SecretValueCell.jsx` — button label text, format `"{{secret." + name + "}}"` |
| Pagination info text | `secrets-pagination-info` | **NEW testid, not in original AFS** — `EliteaAI/EliteaUI@c2a5b4c7`, on `automation/testids` only | `pageInfoTestId` prop threaded onto the shared `GridTablePagination.jsx` (`data-testid={pageInfoTestId}` on the `Typography` showing "1 - N of total"), wired at the Secrets call site (`SecretsTable.jsx`); needed to assert step 3's pagination-reset-to-page-1 clarification (#1202) |

**Verification command used for the "on `automation/testids` only" column** (run
from `../EliteaUI` after `git fetch origin`):
```
git log origin/main..origin/automation/testids -- src/ | grep -i 2336
# → c2a5b4c7 test: [EL-2336] add data-testid for Secrets inline create row + pagination info
```
None of the 10 testids above are present on `main` as of this amendment — the
closure record must carry this same verification (fresh fetch, not a stale
clone) rather than copy this AFS's claim forward.

### Scoped sub-selectors (class-level UPPER_CASE constants, per `.agents/testing.md`)

```python
SECRET_NAME_CELL_SELECTOR = '[data-testid="secret-name-cell"]'
SECRET_VALUE_CELL_SELECTOR = '[data-testid="secret-value-cell"]'
```
Chain off an already-testid-scoped row locator (`secret_row.filter(has_text=name)`),
same sanctioned pattern as `personal_tokens_page.py`'s `TOKEN_NAME_CELL_SELECTOR`.

## Network Behavior
- `GET /api/v2/secrets/secrets/default/${ELITEA_PROJECT_ID}` — fires on page
  load/navigation and after every mutating action (create, delete) — the
  table's list query (`useSecretsListQuery`).
- `POST /api/v2/secrets/secrets/default/${ELITEA_PROJECT_ID}` — fires ONLY on
  checkmark/save click. Confirmed 201 on success. Body carries `{name, value}`
  (not captured in detail — not needed for this case's assertions).
- Cancel (✗) fires **zero** network requests — confirmed live via
  `browser_network_requests` diff before/after the cancel click.
- `DELETE /api/v2/secrets/secret/default/${ELITEA_PROJECT_ID}/{name}` —
  cleanup-only, not part of the case's own steps (see § Cleanup).

## Known Defects Found During Exploration
None found. The one live-behaviour divergence from the case text (pagination
reset — see step 3) reads as intentional UX, not a defect; filed as a
clarification (`EliteaAI/elitea-testing-public#1202`), not a bug, per the
reverse-masking guard.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- **No existing page object for this surface** (`test-specs/settings-secrets/`
  and `automation/pages/*secret*` are both new as of this case) — the
  implementer creates `automation/pages/secrets_page.py`. Closest sibling
  pattern to mirror: `automation/pages/personal_tokens_page.py` (same
  `GridTableRow`-based table, same `.filter(has_text=...)` row-scoping idiom,
  same `delete-confirm-*` shared-modal testids if a future case needs the
  UI delete flow — this case's own cleanup uses the API instead, see
  § Cleanup).
- Wait strategy: wait on the `POST .../secrets/secrets/...` response (step 5)
  before asserting the row settled into view mode — the row transitions
  optimistically-adjacent to the request, not purely on a fixed delay.
- **Analysis gap**: `.agents/automation/elitea-2336-secrets-inline-create/cases/ELITEA-2336.md`
  did not exist at analysis time (intake snapshot missing) — fetched the case
  body directly from the TMS repo's markdown file instead
  (`onetest-ai-tm-Elitea/tests/automated-full-regression-ui/settings/secrets/ELITEA-2336_*.md`).
  No blocking impact — the file was reachable and complete — but flagging per
  the skill's snapshot-first contract.
- Existing secret count in the project (`Private`/399) is 100+ (103→104 across
  this session's create/delete). Do not assert an exact row count anywhere;
  assert presence/absence of the run-unique generated name(s) instead.
