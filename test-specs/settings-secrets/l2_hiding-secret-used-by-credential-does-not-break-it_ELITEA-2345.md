# Test Case: Hiding a secret used by existing credentials does not break those credentials

## Metadata
- **TMS ID**: ELITEA-2345
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2345.md`
- **Linked Story**: none · **Tracking issue**: settings-w05 batch · **Filed this session**: #1905 (clarification), #1907 (question), comment on #656
- **Priority**: l2 (high, per case frontmatter `priority: high`). **pytest marker:
  `@pytest.mark.p1`** — high→l2→p1, per
  `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend), project `Private` / `${ELITEA_PROJECT_ID}` = **399**
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot — cluster session with ELITEA-2346, 2026-08-27
- **Status**: ready-for-automation
- **Surface key**: `secret-visibility-and-consumers`

## Preconditions
- User is logged in; active project `${ELITEA_PROJECT_ID}` (399, "Private").
- **NEVER target a pre-existing/real secret.** Hiding is **irreversible via the UI**
  (no unhide affordance exists — confirmed by ELITEA-2344 and re-confirmed live this
  session), and the project holds 121 real, in-use secrets. This case MUST create its
  own run-unique secret and hide THAT one. A freshly created secret is never
  `isDefault`, so its three-dot menu items are all enabled
  (`SecretActionsMenu.jsx` — `disabled={isDefault}`).
- The case's own step 2 ("identify a secret currently referenced by at least one
  credential") is satisfied by **building** that relationship inside the test, not by
  finding one: the test creates the secret, then creates a credential whose `api_key`
  field references it in Secret mode. Hunting for a real referencing credential would
  mean hiding a real secret — forbidden by the bullet above.

## Test Data
### generated-per-run
- Secret name: `f"autotest_hidden_{uuid4().hex[:8]}"` — must be run-unique; the hide is
  permanent, so a fixed literal would only work once (and would then collide with
  ELITEA-2346's own secret). Confirmed live with `autotest_hidden_a1b2c3`.
- Secret value: any non-empty ASCII string, e.g. `"hidden-secret-value-123"`.
- Credential display name: `f"autotest_cred_hidden_{uuid4().hex[:8]}"`, type **`jira`**
  (chosen because its `api_key` field is a `SecretField` and the rest of the form is
  three plain text inputs — cheapest form that carries a secret field). Confirmed live
  with `autotest_cred_hidden_a1b2c3`.
- Credential filler data (never authenticated against anything real):
  `base_url = "https://example.atlassian.net"`, `username = "autotest@example.com"`.

## Test Steps

1. Navigate to `${BASE_URL}/settings/secrets`.
   - **Verify**: `secrets-page-title` visible, text `"Secrets"`.
   *(Case step 1.)*

2. Create the run-unique secret via the inline "+" flow
   (`secrets-add-button` → `secret-name-input` / `secret-value-input` →
   `secret-row-save-button`).
   - **Verify**: `POST /api/v2/secrets/secrets/default/399` resolves **201 Created**
     (confirmed live). `secrets_page.click_save_button()` already returns the
     `Response` for exactly this assertion.

3. Navigate to `${BASE_URL}/credentials/create-credential/jira` and create a
   credential that REFERENCES the secret created in step 2:
   - fill `toolkit-field-label-input`, `toolkit-field-base_url-input`,
     `toolkit-field-username-input`;
   - click `toolkit-field-api_key-input-toggle-secret` — **the field defaults to
     Password mode; the vault dropdown does not exist until this toggle is clicked**
     (confirmed live);
   - click `toolkit-field-api_key-input-combobox`, wait for
     `select-group-header-Saved Secrets` and the first saved option, then click
     `select-option-{{secret.<name>}}`;
   - click `credential-form-save-button`.
   - **Verify** (baseline, and the precondition the case's step 2 asks for):
     the vault dropdown DOES contain the new secret before it is hidden — confirmed
     live: 123 saved-secret options, the new secret present. Assert
     `saved_secret_option(name)` has count 1 **before** selecting it. This baseline is
     what makes step 7's absence assertion meaningful rather than vacuous.
   - **Verify**: `POST /api/v2/configurations/configurations/399` resolves **200 OK**
     (confirmed live — note: **200**, not 201) and the app redirects to
     `/credentials/all`. Capture the new credential's id from the card click
     (`/credentials/all/<id>?viewMode=owner&name=<display name>`) or from
     `credential_api.list_all_credentials()`.
   *(This step realises case step 2 — "identify a secret referenced by at least one
   credential" — by construction. Decomposed, see § Coverage Map.)*

4. Return to `${BASE_URL}/settings/secrets`, filter with `secrets-search-input` on the
   generated secret name (client-side, per keystroke, no Enter/debounce), then open the
   row's three-dot menu (`secret-row-actions-button`) and click
   `secret-actions-menu-hide`.
   - **Verify**: `alert-dialog-content` reads exactly
     `Are you sure to hide the secret "<name>"? Once hidden, the secret will no longer
     be visible.` and `alert-dialog-confirm-button` reads `"Hide"` (confirmed live
     verbatim this session — same copy ELITEA-2344 recorded).
   - **INHERITED DECLARED IMPROVISATION — keep it.** A plain Playwright `.click()` on
     `secret-row-actions-button` **failed again this session** (menu never mounted;
     `secret-actions-menu-hide` did not exist afterwards) and the existing React-`onClick`
     workaround in `secrets_page.open_row_actions_menu()` opened it first try. Second
     independent reproduction on top of ELITEA-2344's. Use the existing page-object
     method unconditionally; do not "simplify" it. Tracked: `EliteaAI/elitea-testing-public#1222`.
   *(Case step 3.)*

5. Confirm the hide — click `alert-dialog-confirm-button`.
   - **Verify**: `POST /api/v2/secrets/hide/default/399/<name>` resolves **200 OK**
     (confirmed live), followed by a `GET` refetch of the list endpoint.

6. **Verify the secret is removed from the Secrets table** — with the same search
   filter still applied, `secret-row` count is **0** (confirmed live).
   *(Case step 4.)*

7. Open the credential created in step 3 —
   `${BASE_URL}/credentials/all/<id>?viewMode=owner&name=<display name>`.
   - **NOTE — case-text drift (clarification, not a defect):** the case says
     *"Navigate to Settings → Credentials"*. **Credentials is not under Settings** in the
     live product — it is a top-level sidebar entry (`sidebar-menu-item-credentials`)
     routed at `/credentials/all`. Asserting a Settings→Credentials path would assert a
     screen that does not exist. Filed as a clarification — `EliteaAI/elitea-testing-public#1905`.
   - **Verify**: the credential detail form loads with its own values intact —
     `toolkit-field-label-input`, `toolkit-field-base_url-input`,
     `toolkit-field-username-input` all equal what step 3 wrote (confirmed live).
   *(Case step 5.)*

8. **Verify the credential still functions** — i.e. its stored secret reference was NOT
   broken by the hide. Two independent observables, both produced by the system:
   - **Tier 1 (server, decisive):** read the credential back through the API
     (`credential_api` fixture — `list_all_credentials()` and match on `elitea_title`,
     or the page's own `GET /api/v2/configurations/configuration/399/<id>`) and assert
     `data["api_key"] == "{{secret.<name>}}"` — the reference is **unchanged**.
     Confirmed live, verbatim response body:
     `"data": {"api_key": "{{secret.autotest_hidden_a1b2c3}}", "hosting": "Auto",
     "base_url": "https://example.atlassian.net", "username": "autotest@example.com"}`.
   - **Tier 2 (UI, non-destructive):** `credential-form-save-button` is **disabled** on
     load (confirmed live) — the hidden-secret fallback render does NOT dirty the form,
     so nothing was silently rewritten client-side.
   - **DO NOT use "Test Connection" as the oracle.** The credential points at a fake
     Jira host, so `credential-form-test-connection-button` would fail regardless of the
     hide — it cannot distinguish "broken by hiding" from "fake host". A red there would
     be a false defect signal.
   - **Expected UI shape after the hide (assert it, it is the interesting behaviour):**
     the `api_key` field renders in **Password** mode, not Secret mode —
     `toolkit-field-api_key-input-toggle-password` has `aria-pressed="true"`,
     `toolkit-field-api_key-input-combobox` is **absent**, and
     `toolkit-field-api_key-input-field` (a `type="password"` input) is present holding
     the literal secret **name** `autotest_hidden_a1b2c3`. This is **intentional
     product behaviour**, not a defect — `SecretField.jsx` computes
     `isHiddenSecret = isError || !data?.some(i => i.secret_name === value)` and its
     `handleSwitchToSecretTab` only switches to the Secret tab
     `if (isSecret && !isHiddenSecret)`. Before the hide, the same URL rendered the
     combobox displaying the secret name (confirmed live, both states observed).
   *(Case step 6.)*

9. **Verify the hidden secret no longer appears in the secret-selection dropdown** —
   in **both** entry points the case names ("creating or editing"):
   - **Editing** (still on the credential detail from step 7): click
     `toolkit-field-api_key-input-toggle-secret`, then
     `toolkit-field-api_key-input-combobox`, then assert
     `select-option-{{secret.<hidden name>}}` has **count 0**.
     Confirmed live: 122 saved options, hidden secret absent.
   - **Creating**: navigate to `/credentials/create-credential/jira`, same two clicks,
     same absence assertion. Confirmed live: 122 saved options, hidden secret absent.
   - **Control assertion (do include it):** a DIFFERENT, still-visible run-unique secret
     IS present in the same open dropdown. Confirmed live in both probes. Without this,
     a dropdown that failed to load at all would pass the absence assertion. The
     cheapest control is `saved_secret_options.count() > 0` plus an explicit present-check
     on a known-visible secret.
   - ⚠️ **Navigating away from a dirtied credential form raises a native
     `beforeunload` dialog** and a bare `page.goto()` will hang until it is handled
     (cost two 60 s timeouts live). Toggling the field to Secret mode dirties the form.
     Register `page.on("dialog", lambda d: d.accept())` before leaving the edit form, or
     discard via `credential-form-discard-button` first.
   *(Case step 7 and the case's Expected Final State.)*

## Expected Results
- Secret creates (201), credential creates (200) and stores
  `api_key = "{{secret.<name>}}"`.
- Hide fires `POST .../secrets/hide/default/399/<name>` → 200; the secret disappears
  from the Secrets table.
- The credential's stored `api_key` reference is **unchanged** after the hide — nothing
  is rewritten, nothing is nulled; the credential is not broken.
- The credential detail form is pristine on load (Save disabled) and renders the
  `api_key` field in Password mode showing the secret name (intentional fallback).
- The hidden secret is absent from the secret-selection dropdown on BOTH the
  create-credential and edit-credential forms, while other secrets remain selectable.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Secrets | page loads | step 1 | `secrets-page-title` visible, text "Secrets" | asserted |
| 2 Identify a secret referenced by ≥1 credential | completes without error | steps 2–3 | 201 create + 200 credential-create with `api_key = {{secret.<name>}}`, plus the pre-hide dropdown-presence baseline | asserted *(decomposed + realised by construction — see § Preconditions for why "find one" is forbidden)* |
| 3 Three-dot menu → Hide and confirm | control responds, next state shown | steps 4–5 | dialog copy asserted verbatim; `POST .../hide/...` → 200 | asserted |
| 4 Verify the secret is removed from the Secrets table | condition holds | step 6 | filtered `secret-row` count == 0 | asserted |
| 5 Navigate to Settings → Credentials and open the credential that referenced the hidden secret | page loads | step 7 | detail form loads with its three text values intact | asserted *(path corrected — Credentials is top-level, not under Settings; clarification filed)* |
| 6 Verify the credential still functions | condition holds | step 8 | server read: `data.api_key == "{{secret.<name>}}"`; UI: Save disabled | asserted *(interpreted as "the stored auth reference survives"; Test Connection rejected as an oracle — see step 8)* |
| 7 Verify the hidden secret no longer appears in the secret selection dropdown when creating or editing a credential | condition holds | step 9 | `select-option-{{secret.<name>}}` count 0 on BOTH forms | asserted |
| Expected Final State (same as 7) | condition holds | step 9 | as above | asserted |

**Axis 2 — Analyst additions:**
- Step 3 asserts the pre-hide dropdown **presence** baseline — *added: an absence
  assertion whose subject was never present is vacuous; the baseline is what turns
  step 9 into a real check.*
- Step 8's Tier-1 server read of `data.api_key` — *added: "still functions" has no
  UI-only observable that is both honest and available (Test Connection is unusable
  here, see step 8). The stored reference is the thing that would have broken.*
- Step 8's assertion of the **Password-mode fallback shape** — *added: it is the
  visible consequence of hiding a referenced secret and is what a reader will
  mistake for breakage; pinning it makes an unannounced future change to
  `SecretField.isHiddenSecret` fail loudly instead of silently.*
- Step 9 exercises **both** create and edit forms — *added: the case's own wording is
  "creating or editing"; the two render through different routes and different Formik
  parents, so one does not imply the other.*
- Step 9's control assertion on a still-visible secret — *added: guards against a
  false pass from an empty/failed dropdown load.*

## Cleanup
- **Delete the credential** created in step 3 — it is live project data. Either
  `credential_api.delete_credential(<id>)` (fastest, and the fixture already exists),
  or the UI flow: `controls-menu-button` → `delete-credentials-menuitem` →
  type the display name into `delete-confirm-name-input`'s **native `<input>` child**
  (the testid sits on the MUI `FormControl` `<div>`, not the input — a `fill()` on the
  testid itself errors with *"Element is not an `<input>`"*; `credential_detail_page`'s
  `fill_delete_confirm_name()` already handles this) → `delete-confirm-button`.
  Confirmed live via the UI flow this session.
- **The hidden secret cannot be cleaned up** — hiding is irreversible and there is no
  unhide affordance. It leaves one invisible, run-unique row server-side per run. This
  is inherent to the case (ELITEA-2344 has the same property) and is why the secret name
  must be run-unique. No action required, but the AFS records it so nobody hunts for it.

## Concrete Handles (discovered/confirmed during exploration)

Locator policy on this project is **testid-only, no fallback ladder**.
Provenance verified 2026-08-27 after `cd ../EliteaUI && git fetch origin`.

| Element | Testid | Provenance |
|---|---|---|
| Secrets page title | `secrets-page-title` | on-main ✓ |
| Secrets "+" add button | `secrets-add-button` | on-main ✓ |
| Secret name / value inputs | `secret-name-input` / `secret-value-input` | on-main ✓ |
| Secret row save (✓) | `secret-row-save-button` | on-main ✓ |
| Secrets search input | `secrets-search-input` | **on `automation/testids` only** (awaiting human cherry-pick to main) |
| Secret row / name cell | `secret-row` / `secret-name-cell` | on-main ✓ |
| Three-dot actions button | `secret-row-actions-button` | on-main ✓ |
| "Hide" menu item | `secret-actions-menu-hide` | on-main ✓ |
| Hide dialog body / confirm | `alert-dialog-content` / `alert-dialog-confirm-button` | on-main ✓ |
| Credential display name | `toolkit-field-label-input` | runtime-composed from the field key by `ToolBaseProperty.jsx`; present on main ✓ and on `automation/testids` ✓ (bare grep cannot see it — see § Provenance note) |
| Credential base_url / username | `toolkit-field-base_url-input` / `toolkit-field-username-input` | same, on-main ✓ |
| api_key SecretField wrapper | `toolkit-field-api_key-input` | same, on-main ✓ |
| api_key native password input | `toolkit-field-api_key-input-field` | derived by `SecretField.jsx` (`nativeInputTestId`) — on-main ✓ |
| api_key Secret / Password toggles | `toolkit-field-api_key-input-toggle-secret` / `-toggle-password` | derived by `SecretField.jsx` `testIdPrefix` (line 342) — **on `automation/testids` only**; `origin/main`'s SecretField has no `testIdPrefix` (verified by `git diff origin/main origin/automation/testids -- SecretField.jsx`) |
| api_key vault combobox | `toolkit-field-api_key-input-combobox` | derived by `SingleSelect.jsx:662` `SelectDisplayProps` — on-main ✓ |
| Saved-secret option | `select-option-{{secret.<name>}}` | `SingleSelectMenuItem` — on-main ✓ |
| Saved-secrets group header | `select-group-header-Saved Secrets` | on-main ✓ |
| Credential save / discard | `credential-form-save-button` / `credential-form-discard-button` | on-main ✓ |
| Credential card name (list) | `entity-card-name` | on-main ✓ |
| Credential detail three-dot | `controls-menu-button` | on-main ✓ |
| Delete menu item (cleanup) | `delete-credentials-menuitem` | auto-derived by `DotMenu.jsx` from the entity name (bare grep blind) — present on both refs, already used by merged ELITEA-1964 |
| Delete confirm name input / button (cleanup) | `delete-confirm-name-input` / `delete-confirm-button` | on-main ✓ |

**Provenance note:** the `toolkit-field-*` family and `delete-credentials-menuitem` are
**runtime-composed** testids — a bare `git grep` for the literal string returns nothing
on either ref. They were verified by grepping the *composition site* instead
(`SecretField.jsx`, `SingleSelect.jsx`, `ToolBaseProperty.jsx`, `DotMenu.jsx`) and by
live DOM read. This is the failure mode `.agents/workflow.md` § Closure record warns
about; do not read "no grep hit" as "not on main" for these.

**No new testid is needed by this case** — every element it touches already carries one.

## Network Behavior
- `POST /api/v2/secrets/secrets/default/399` — secret create, **201**.
- `POST /api/v2/configurations/configurations/399` — credential create, **200** (not 201).
- `GET /api/v2/configurations/configuration/399/<id>` — credential read (the Tier-1
  oracle for step 8); response `data.api_key` is the assertion target.
- `POST /api/v2/secrets/hide/default/399/<name>` — hide, **200**; followed by a list
  `GET` refetch.
- `GET /api/v2/secrets/secrets/default/399` — the vault list behind the dropdown. It is
  `skip`-gated on the field's mode (`SecretField.jsx:118`), so on first entry into
  Secret mode the menu opens BEFORE the list resolves — wait on the first
  *option*, never on the group header alone (already handled by
  `credential_create_page.open_secret_dropdown()`).

## Known Defects Found During Exploration
- **No product defect blocks this case.** The Password-mode fallback in step 8 is
  intentional (source-confirmed), not a bug.
- **Case-text clarification filed — `EliteaAI/elitea-testing-public#1905`** — case step 5's "Settings → Credentials" path does
  not exist; Credentials is a top-level sidebar route. Reverse-masking guard: assert the
  live route, not the stale case text.
- **Observation raised for a human** — the hidden-secret fallback puts the secret **name**
  into a `type="password"` input, where it looks like a stored password. Any user
  keystroke in that field converts the credential's `{{secret.…}}` reference into that
  literal text. Not reproduced as data loss here (the form stays pristine, Save disabled),
  so **not** filed as a bug; raised as a question card for a product decision — `EliteaAI/elitea-testing-public#1907`.
- `EliteaAI/elitea-testing-public#656` (React "unique key prop" console warning in
  `CategorySection.jsx`) **fires on the create-credential route** — a second occurrence
  commented on that issue this session. It is a **dev-build-only** React warning
  (stripped by `vite build`). A spec asserting "no console errors" while passing through
  `/credentials/create-credential/<type>` WILL see it on localhost. Handle per the
  no-masking decision tree: `expect.soft()` + `# Known defect: #656`, or scope the
  console assertion to the steps that do not touch that route.
- `EliteaAI/elitea-testing-public#1203` (Secrets-page "Maximum update depth exceeded")
  was **not** observed this session — same inconclusive pattern as ELITEA-2337/2338/2344.
  Implementer: check your own run's console rather than assuming either way.
- `EliteaAI/elitea-testing-public#1222` (three-dot menu needs the React-`onClick`
  workaround) — reproduced again, see step 4.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest. Markers: `@pytest.mark.p1`, `@pytest.mark.regression`,
  plus the feature marker used by the other secrets specs
  (`automation/tests/ui/admin/test_secret_*.py` — this case's spec belongs there too,
  e.g. `automation/tests/ui/admin/test_hidden_secret_not_breaking_credentials.py`).
- Page objects — **all reuse, no new page object needed**:
  - `automation/pages/secrets_page.py` — `navigate()`, `click_add_button()`,
    `fill_new_row()`, `click_save_button()`, `search_input`, `get_row_by_name()`,
    `open_row_actions_menu()` (**keep the workaround**), `click_hide_menu_item()`,
    `alert_dialog_content`, `confirm_hide()`.
  - `automation/pages/credential_create_page.py` — `open_type_form("jira")` (NOT
    `navigate_to_type()`: that one calls `wait_for_network()` → `networkidle`, which the
    credentials routes do not reach; see `#1847` and this file's own docstring),
    `secret_toggle(field_key, mode)`, `open_secret_dropdown("api_key")`,
    `saved_secret_option(name)`, `saved_secret_options`, `secret_combobox()`,
    `secret_native_input()`.
  - `automation/pages/credential_detail_page.py` — `open_controls_menu()`,
    `open_delete_dialog()`, `fill_delete_confirm_name()`, `confirm_delete()`.
  - `automation/fixtures/api_fixtures.py::credential_api` — server-side read + cleanup.
- New page-object methods likely needed (additive, on `credential_create_page`):
  a `secret_toggle_is_selected(field_key, mode)` reader (`aria-pressed`) so step 8 can
  assert the Password-mode fallback via a class-level constant rather than an inline
  attribute read.
- Waits: `page.expect_response()` on each of the four calls above. No sleeps. The
  vault-dropdown wait is already correct in `open_secret_dropdown()`.
- Wrap every step in `with allure.step("Step N — …"):`.
- Register the `beforeunload` dialog handler once at the top of the test (step 9's ⚠️).

## Implementation notes (shipped — amended by the implementer, 2026-08-28)

Spec: `automation/tests/ui/admin/test_hidden_secret_not_breaking_credentials.py`
(green first run, 54.48 s, 0 reruns). Every assertion above shipped as specified;
these three are the places where the *how* differs from this file's hints:

1. **Credential id** is captured from the create POST's own response body
   (`id`), not from the card-click URL — the server tells us directly. A
   server-side `list_all_credentials()` lookup by `label` remains as an
   explicit fallback in the spec rather than a guess.
2. **No `secret_toggle_is_selected()` reader was added.** The Password-mode
   fallback is asserted with `expect(secret_toggle(key, mode)).to_have_attribute(
   "aria-pressed", …)` on the EXISTING class-level `FIELD_SECRET_TOGGLE`
   constant — a compliant testid-only handle, so the extra page-object method
   would have been dead weight.
3. **A second, run-unique CONTROL secret is created and deleted** (rather than
   leaning on a pre-existing project secret), so the "other secrets are still
   selectable" control is owned by the run and cannot be invalidated by
   unrelated project data.
4. **The credential DETAIL route's secret-field handles are driven through
   `CredentialCreatePage`** — the detail route renders the same shared
   `SecretField`, and those selectors already live in exactly one page object.
   Promoting that block to `CredentialFormFieldsMixin` (the pattern the file
   used for `FIELD_INPUT`/`AUTH_METHOD_RADIO`) is the cleaner end state but is
   a non-additive edit to a ~20-caller page object — raised to the lead, not
   done in this PR.
5. **No console-error assertion** was added: it is outside this case's Coverage
   Map, and #656 fires deterministically on `/credentials/create-credential/<type>`
   on dev builds, which would have made this spec a sanctioned-RED the case
   never asked for.
