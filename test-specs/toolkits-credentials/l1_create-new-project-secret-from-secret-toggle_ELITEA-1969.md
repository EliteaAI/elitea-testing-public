# Test Case: Credential — Create New Project Secret from Secret Toggle

## Metadata
- **TMS ID**: ELITEA-1969
- **Linked Story**: none
- **Priority**: l1 (frontmatter `priority: high`, body header `Priority: high` — consistent)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`), project
  `Private` / `${ELITEA_PROJECT_ID}`=399, identity "Test Bot"
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation
- **Case-gate note**: `status: draft`, `execution_type: manual` — intake-eligible
  per `.agents/test-automation.yaml`. All 13 steps executed live 2026-08-22.

## Preconditions
- User is logged in (localhost `auth_state`).
- Project `Private` (399) selected — the framework default.
- The credential create form is reachable at `/credentials/create-credential/github`.
- The acting identity holds the `secrets.create` permission on the active
  project — without it `SecretField.createSecretsOptions` is empty and the whole
  CREATE group is absent from the DOM. Live-verified present on project 399.

## Test Data

### generate-per-test (created in the flow, deleted in teardown)
- **New secret** — name `autotest_new_secret_<uuid8>`, value `test_value_123`.
  The case names a fixed `autotest_new_secret`; the test suffixes a run-unique
  token because a fixed name collides with a leftover from a previous run (the
  secret name is the server-side primary key — `POST` on a duplicate name is not
  idempotent) and the project is shared, live data. The case's *observable* —
  "the newly created secret appears in the saved-secrets list after refresh" —
  is unchanged by the suffix. Same discipline as ELITEA-2336/2338 on this
  surface.
- Cleanup: `DELETE /secrets/secret/default/{project}/{name}` → 204, in a
  `finally` block, regardless of outcome.

### reuse-existing (read-only)
- Credential type `github` + auth method `Token` (schema-rendered, no seeding).
- The project's existing 120 secrets — read as list context only.

## Test Steps

| # | Action | Expected (live-confirmed) |
|---|---|---|
| 1 | Navigate to `/credentials/create-credential/github`; select the `Token` auth radio | The Access Token secret field renders (`toolkit-field-access_token-input` + `…-input-field`) |
| 2 | Click `Secret` on the toggle, then open the select | Combobox `…-input-combobox` renders and the dropdown opens |
| 3 | Read both dropdown groups | `select-group-header-Create` (text `Create`) carrying `select-option-__create_private_secret__`, AND `select-group-header-Saved Secrets` (text `Saved Secrets`) with ≥1 saved option — both header strings are CSS-uppercased on screen only; `to_have_text` reads `textContent`. Record the saved-option count as the pre-create baseline |
| 4 | Click the CREATE option | **A NEW BROWSER TAB opens** at `/{project_id}/settings/secrets?createSecret=1` (the app calls `window.open(..., '_blank')`, it is NOT an in-page navigation — see § Case-text divergence). The originating tab stays on the credential form with its dropdown still open |
| 5 | In the new tab, read the secrets table's column headers | Exactly three headers: `secret-column-header-name` = `Name`, `secret-column-header-secretValue` = `Value`, `secret-column-header-actions` = `Actions` |
| 6 | (Case: "click the + button") | The deep link's `?createSecret=1` has **already opened** the inline editable row — `secret-name-input` / `secret-value-input` are present and `secrets-add-button` is `disabled` (only one row editable at a time). The case's step is pre-satisfied by the product; asserted as such — see § Case-text divergence |
| 7 | Fill Name and Value into the pending row | Both inputs hold exactly the typed strings |
| 8 | Click the checkmark (`secret-row-save-button`) | `POST /secrets/secrets/default/{project}` → **201**; the edit row closes and `secrets-add-button` re-enables |
| 9 | Read the table for the new secret | A `secret-row` whose `secret-name-cell` equals the new name exists (count 1); it settles into alphabetical position, not pinned to top |
| 10 | Switch back to the originating tab (credential form) | The form is still on `/credentials/create-credential/github`, still in Secret mode (`…-toggle-secret` `aria-pressed="true"`) |
| 11 | Ensure the saved-secrets dropdown is open | Open. **The dropdown was never closed** by the Step-4 create click (`SingleSelect` sets `skipNextCloseRef` for `variant: 'action'` options — the same mechanism behind known defect #1047). The list is stale: the new secret is absent and the count still equals the Step-3 baseline — asserted, because that staleness is exactly what Step 12's refresh exists to fix |
| 12 | Click the refresh button in the SAVED SECRETS header (`…-input-refresh-secrets-button`) | The `useSecretsListQuery` refetch fires |
| 13 | Read the saved-secrets list again | `select-option-{{secret.<new name>}}` is now present, its text equals the new secret's name, and the saved-option count is exactly baseline + 1 |

## Expected Results
- The credential form's Secret dropdown offers a create-a-secret action that
  lands the user on the project's Secrets settings page with the create row
  already open.
- The Secrets page's inline create flow persists the new secret (201) and lists
  it.
- The credential form's saved-secrets list is **cached** and does not pick the
  new secret up on its own; the group header's refresh button is what
  reconciles it — after refresh the new secret is selectable in the dropdown.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Disposition | Asserted where |
|---|---|---|
| Precondition: logged in | precondition | framework `auth_state` |
| Precondition: project exists, Credentials accessible | precondition | Step 1 navigation |
| Step 1 — Github credential, Token auth → Token input | asserted | Step 1 |
| Step 2 — click Secret toggle → dropdown opens with CREATE + SAVED SECRETS | asserted | Steps 2 + 3 |
| Step 3 — both sections present in the dropdown | asserted | Step 3 — both group headers visible + the create option + ≥1 saved option |
| Step 4 — click "New Project Secret" → navigation to `/settings/secrets` | asserted (mechanism divergence declared) | Step 4 — a new page is captured off `context.expect_page()`, its URL asserted to carry `/settings/secrets` and `createSecret=1` |
| Step 5 — table shows columns Name, Value, Actions | asserted | Step 5 — the three column-header testids, exact text, and `to_have_count(3)` on the header prefix (no fourth column) |
| Step 6 — click "+" → new input row or dialog appears | asserted (pre-satisfied by the deep link; declared) | Step 6 — pending row inputs visible AND add-button disabled |
| Step 7 — fill Name + Value | asserted | Step 7 — `input_value()` on both |
| Step 8 — click checkmark → secret saved | asserted | Step 8 — POST 201 |
| Step 9 — secret appears in the table | asserted | Step 9 — row count 1 by name, name-cell text equality |
| Step 10 — navigate back to the credential form | asserted | Step 10 — tab switch, URL + Secret-mode state |
| Step 11 — click Secret toggle again → dropdown reopens with saved list | asserted (state divergence declared) | Step 11 — the dropdown is *still* open (never closed by step 4); saved list present and asserted STALE |
| Step 12 — click the refresh button next to SAVED SECRETS | asserted | Step 12 — the refresh button clicked by its own testid |
| Step 13 — the new secret appears in the saved list | asserted | Step 13 — option present by dynamic testid, text equality, count == baseline + 1 |
| Expected Final State / Pass criteria | asserted | Steps 8–9 (created) + 13 (visible after refresh) |

### Axis 2 — Analyst additions

| Addition | Why grounded |
|---|---|
| Saved-option **count** captured as a baseline in Step 3 and asserted `baseline + 1` in Step 13 | Step 13's expected result is "appears in the list". A presence-only check cannot distinguish "the list refreshed" from "the list was replaced by something wrong". The delta is the honest proof the refresh reconciled rather than reset |
| Step 11 asserts the list is **stale** (new secret ABSENT, count == baseline) before refreshing | Without it, Step 12–13 would pass even if the list had already self-refreshed, making the refresh button — the actual subject of the case's step 12 — unverified. This is the assertion that gives the refresh click meaning |
| Column-header assertion is `to_have_count(3)` on the prefix, plus per-header text | The case names exactly three columns; a presence-only check cannot see a fourth |
| `POST` status asserted `201` explicitly (Step 8) | "New secret is saved" is otherwise only inferable from the UI, which can lie about a failed write. The response is the product's own ground truth |
| Add-button asserted `disabled` in Step 6 | It is the observable that distinguishes "the pending row is open" from "the row rendered but the table is idle", and it is the product's own one-row-at-a-time invariant |

## Cleanup
`DELETE /secrets/secret/default/{ELITEA_PROJECT_ID}/{secret_name}` → 204, in a
`finally` block, asserted. The credential form itself is abandoned without
Save — nothing else is created.

## Concrete Handles (discovered during exploration)

Credential-form handles are the ELITEA-1968 set (same table, same provenance).
Additional handles for this case:

| Element | Handle | Provenance |
|---|---|---|
| SAVED SECRETS refresh button | `[data-testid="toolkit-field-access_token-input-refresh-secrets-button"]` | **needs-adding → ADDED by this unit** (EliteaAI/EliteaUI@29214bf1, on `automation/testids`) |
| Secrets table column headers | `[data-testid="secret-column-header-{name,secretValue,actions}"]` | **needs-adding → ADDED by this unit** (same commit) |
| Secrets page title | `[data-testid="secrets-page-title"]` | on-`automation/testids` (ELITEA-2336, EliteaAI/EliteaUI@c2a5b4c7) |
| Add ("+") button | `[data-testid="secrets-add-button"]` | same |
| Pending-row name / value inputs | `[data-testid="secret-name-input"]` / `[data-testid="secret-value-input"]` | same |
| Row save (✓) | `[data-testid="secret-row-save-button"]` | same |
| Secret row / name cell | `[data-testid="secret-row"]` / `[data-testid="secret-name-cell"]` | same |

### Testid work performed (`add-data-testid` discipline)
Two additions, both **attribute-only** (no new DOM nodes, no hooks, no
behaviour change) — EliteaAI/EliteaUI@29214bf1 on `automation/testids`,
pushed; a human cherry-picks to `main`:

1. `SecretField.jsx` — `refreshSecretsTestId`, derived from the caller's own
   `data-testid` exactly like the existing `nativeInputTestId` (`-field`) and
   the `-toggle` prefix, giving `{field-testid}-refresh-secrets-button`. The
   shared component hardcodes **no** feature-scoped testid
   (`.agents/testing.md` § Locator policy, shared-components rule), and the
   caller-derived form keeps the handle unique on a page rendering several
   secret fields.
2. `SecretsTable.jsx` — passes `GridTableHeader`'s **already-supported**
   `columnTestIdPrefix="secret"` prop, exactly as `TokensTable.jsx` already
   does for `personal-token-column-header-*`. Side effect of the shared prop:
   `secret-sort-icon-name` also renders, unreferenced — identical to the
   pre-existing `personal-token-sort-icon-*` and `credentials-table-sort-icon-*`
   precedent recorded for ELITEA-1973.

### Page object impact
- `CredentialCreatePage` — additive: secret-mode select constants/accessors
  (shared with ELITEA-1968) plus the refresh-button accessor.
- `SecretsPage` — additive: `SECRET_COLUMN_HEADER` template constant +
  `column_header()` / `column_headers()` accessors. No existing method touched.

## Network Behavior
- `GET /configurations/available/?section=credentials` — credential form render.
- `GET /secrets/secrets/default/{project}` — fires on entering Secret mode and
  again on the refresh click; RTK-Query-cached in between (that cache IS the
  staleness Step 11 asserts).
- `POST /secrets/secrets/default/{project}` → **201** on save, followed by a
  list `GET` refetch.
- `DELETE /secrets/secret/default/{project}/{name}` → **204** (cleanup only,
  singular `secret` segment).

## Known Defects Found During Exploration

- **#1203 (OPEN, known)** — `/settings/secrets` fires a React
  "Maximum update depth exceeded" console error on **every** mount. Re-observed
  this session on both project 399 and project 471. This test deliberately runs
  **no console-error side-channel**, so it is unaffected; do not add one to this
  spec without adopting `test_secret_create_inline_checkmark_x_cancel.py`'s
  `_is_known_defect_1203()` matcher and accepting sanctioned-RED.
- **#1047 (OPEN, `[Clarification]`)** — the select's menu does not close after a
  `variant: 'action'` click. Here that is *load-bearing in our favour*: the
  dropdown is still open when the test returns to the form, so Step 11 needs no
  reopen click. The test asserts the open state explicitly rather than assuming
  it, so if #1047 is ever fixed the assertion fails loudly and points at this
  note instead of failing obscurely on a missing refresh button.

### Case-text divergences — filed as clarifications, NOT bugs

1. **Step 4 says "Navigation … occurs"; the product opens a NEW TAB.**
   `SecretField.createSecretsOptions` calls
   `window.open(url, '_blank', 'noopener,noreferrer')`. The URL also carries a
   project segment and a `?createSecret=1` query the case does not mention.
   The test asserts the real mechanism (a popup page captured off
   `context.expect_page()`), per the reverse-masking guard.
2. **Step 6 says "click the + button"; the deep link already opened the row.**
   `?createSecret=1` auto-invokes the same `addSecretRow()` the "+" button
   calls, and the "+" button is then `disabled`. Clicking it as written is
   impossible. The test asserts the state the case's step is trying to reach
   (pending row open, add button disabled).
3. **Step 11 says "click Secret toggle again … dropdown reopens".** The toggle
   is already in Secret mode and the dropdown never closed (#1047). Clicking
   the toggle again would in fact *destroy* the state (it clears the value and
   re-mounts the field). The test asserts the dropdown is still open.
4. **Label** — same divergence as ELITEA-1968 Step 4: on the personal project
   the create option reads `New Private Secret`, not `New Project Secret`.

## Blocked Steps
None — all 13 steps executed live end-to-end (secret created, listed, and seen
in the dropdown after refresh; deleted afterwards).

## Automation Hints
- **Capture the popup with `context.expect_page()`** around the create-option
  click; the popup's `?createSecret=1` query is stripped by the router shortly
  after load, so assert on the URL captured at open time (or on
  `/settings/secrets` plus the auto-opened row, which is the durable signal).
- **Never `networkidle`** on either route (credentials — ELITEA-1964/1967;
  secrets — the #1203 render loop keeps React busy).
- **Wait on the first saved-secret OPTION, not the group header**, when opening
  the vault dropdown: the headers render before the vault GET resolves.
- The secrets table is server-paged at 10 rows/page and sorts alphabetically;
  the new row is NOT pinned to top. Assert by name-filtered row locator, never
  by index.
- The saved-secrets option list is large (120+) — target the one option by its
  dynamic testid; count via `.count()` on the prefix, never by enumerating text.
- Cleanup must run in `finally` — a leaked secret pollutes a shared live
  project and inflates every later run's baseline count.
