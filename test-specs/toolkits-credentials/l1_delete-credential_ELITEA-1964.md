# Test Case: Credential — Delete Credential

## Metadata
- **TMS ID**: ELITEA-1964
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`),
  project 399 "Private" (`Test Bot`)
- **User set**: `${TEST_USER}` (nominal — `auth_state` no-op on localhost)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), 2026-08-22
- **Status**: ready-for-automation

## Classification note — one NEW, filed defect touches the delete flow

Live-observed on every delete: after the `DELETE` succeeds (204), the app
re-fetches the credential it has just deleted
(`GET /configurations/configuration/{project}/{id}` → **404**), producing a
visible console error inside the happy path. Filed as
**`elitea-testing-public#1666`** (`bug`, MINOR; sibling of `#1330`, the same
stale-refetch pattern on pipeline *versions*). It is **cosmetic** — the
delete itself is correct and every case assertion passes — so this is NOT a
sanctioned-RED case: the test's assertions stay hard, and the *console
side-channel* check carries a narrow, endpoint-specific filter linked to
`#1666` (same idiom as `test_credential_create.py`'s `#518`/`#554` filters).
The filter matches the deleted credential's own URL only, so a genuinely
new console error is never masked.

## Preconditions
- User authenticated (`auth_state` fixture — no-op on localhost).
- Credentials section accessible; the create form is reachable directly at
  `/credentials/create-credential/github` (no zero-credential-project
  redirect concern — the test creates its own credential first, so
  `/credentials/all` always has ≥1 card when it is visited).

## Test Data
### generate-per-test (created in test, deleted BY the test's own subject flow)
- **Display Name**: `autotest_cred_delete_${timestamp}` — the case pins the
  literal `autotest_cred_delete`; timestamped per this feature's established
  collision-avoidance convention (same reasoning as ELITEA-1976/1978).
- **Credential type**: Github (the case says "any, e.g. Github"), **Anonymous**
  auth (the form's default). Deliberately NOT Token auth: the case's subject is
  deletion, Base Url ships pre-filled and Anonymous is the default, so a
  Display Name alone enables Save — this removes any `GIT_HUB_TOKEN`
  dependency (no `pytest.skip` path) and never types a secret.

## Test Steps
1. Navigate to `/credentials/create-credential/github`, fill Display Name
   with `autotest_cred_delete_${ts}` (UI, not API — the case's step 1 is an
   explicit user-visible step with its own expected result), leave the
   default Anonymous auth, click Save.
   - **Verify**: the ID field live-mirrors the Display Name; Save is enabled;
     `POST /configurations/configurations/{project}` → **200** with
     `label == elitea_title == ${name}` and a numeric `id`; the app redirects
     to `/credentials/all`.
2. On the credentials list, verify the new credential is listed.
   - **Verify**: exactly one `entity-card` whose `entity-card-name` text
     equals `${name}` is visible.
3. Click that card to open the credential detail page.
   - **Verify**: URL becomes `/credentials/all/{id}` carrying the SAME id the
     create response returned; the detail form's Display Name field reads
     `${name}`.
4. Click the three-dot menu, then the "Delete" item.
   - **Verify**: the menu renders a `delete-credentials-menuitem` labelled
     "Delete"; after clicking it the delete-confirmation dialog is visible,
     titled "Delete confirmation", its message names `${name}`
     (`delete-confirm-entity-name`), it renders a type-to-confirm Name field,
     and the Delete button is **disabled** while the field is empty.
5. Type the credential's exact name into the dialog's Name field and confirm.
   - **Verify**: the Delete button becomes enabled once the typed name
     matches; clicking it issues
     `DELETE /configurations/configuration/{project}/{id}` → **204**; the app
     navigates back to `/credentials/all`.
6. Verify the credential is removed from the list.
   - **Verify**: zero `entity-card`s named `${name}` (web-first
     `to_have_count(0)`), while the list itself still renders (the deletion
     removed one card, it did not break the page).
7. Reload `/credentials/all` and verify the credential is still gone.
   - **Verify**: zero `entity-card`s named `${name}` after a full page load;
     **and** — independent ground truth, not a second DOM read —
     `credential_api.list_all_credentials()` contains no credential with that
     label or id.
8. Side-channel: no unexpected console errors/warnings across the whole flow
   (filtered for the already-filed `#1666` and `#518`).

## Expected Results
- The credential is created and visible in the list (steps 1-2).
- The three-dot menu exposes Delete; Delete opens a type-to-confirm
  confirmation dialog naming the credential (step 4).
- Confirming issues a real `DELETE` that returns 204 and navigates back to
  the list (step 5).
- The credential is absent from the list immediately (step 6) and after a
  reload (step 7), and absent server-side per the API (step 7).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create a credential "autotest_cred_delete" | created and visible in the list | step 1 | POST 200 + `label`/`elitea_title` match + redirect to `/credentials/all` | asserted |
| 2 Verify it appears in the credentials list | "autotest_cred_delete" is listed | step 2 | `entity-card` filtered by name → `to_have_count(1)` | asserted |
| 3 Open the credential detail page | detail page loads | step 3 | URL contains the created id; Display Name field value equals the name | asserted |
| 4 Click the three-dot menu and select "Delete" | delete confirmation dialog appears | step 4 | `delete-credentials-menuitem` visible + `delete-confirm-dialog` visible, title/entity-name/name-field/disabled-confirm asserted | asserted |
| 5 Confirm deletion in the dialog | credential is deleted | step 5 | DELETE → 204 + navigation back to `/credentials/all` | asserted |
| 6 Verify the credential is removed from the list | no longer appears | step 6 | `to_have_count(0)` on the name-filtered card | asserted |
| 7 Reload the page and verify it is still gone | remains absent after reload | step 7 | `to_have_count(0)` after `page.reload()` + API list contains no such credential | asserted |
| Preconditions: user logged in, Credentials section accessible | — | Preconditions | `auth_state` fixture; direct route reachable | asserted *(setup)* |
| Test Data: "Credential type (any, e.g. Github)" | — | Test Data | Github + Anonymous auth (see rationale) | asserted *(setup)* |
| Expected Final State: permanently removed, does not reappear after reload | — | steps 6-7 | same assertions as 6-7 plus the API cross-check | asserted |

### Axis 2 — Analyst additions

- Step 4 asserts the confirm button is **disabled** before the name is typed
  and **enabled** after — *added: the case says only "confirmation dialog
  appears", but the dialog's whole point on this surface is the
  type-to-confirm gate (`shouldRequestInputName: true` in
  `CredentialsControls.jsx`); a regression dropping that prop would still
  "show a dialog" and pass the case's literal wording.*
- Step 5 asserts the DELETE response status (204) rather than inferring
  deletion from the UI alone — *added: makes the system, not the DOM, the
  producer of the "it was deleted" evidence.*
- Step 7 cross-checks `list_all_credentials()` — *added: a second DOM read
  after a reload can still be served from a stale cache; the API is the
  independent ground truth for "permanently removed", which is the case's own
  Expected Final State.*
- Step 8 console side-channel — *added: this repo's standing idiom for UI
  cases; it is what surfaced `#1666`.*

## Cleanup
- **None needed on the happy path** — the test's own subject flow (step 5)
  deletes the only object it created.
- Defensive teardown only: if the credential still exists (any step failed
  before/at the delete), delete it via `credential_api.delete_credential(id)`
  so a failed run leaks nothing. Must tolerate a 404/already-gone.

## Concrete Handles (discovered during exploration, live-verified 2026-08-22)

| Element | Recommended Locator | Provenance |
|---|---|---|
| Display Name input | `toolkit-field-label-input` (`CredentialFormFieldsMixin.display_name_input`) | on-main ✓ (pre-existing) |
| ID (mirror) input | `toolkit-field-elitea_title-input` (`CredentialFormFieldsMixin.id_input`) | on-main ✓ |
| Save button | `credential-form-save-button` (`CredentialFormFieldsMixin.save_button`) | on-main ✓ |
| Credential card | `entity-card` (`CredentialsListPage.entity_card`) | on-main ✓ |
| Credential card name | `entity-card-name` (`CredentialsListPage.entity_card_name`) | on-main ✓ |
| Three-dot menu button | `controls-menu-button` (`CredentialDetailPage.controls_menu_button`) | on-main ✓ |
| Delete menu item | `delete-credentials-menuitem` — auto-derived by `DotMenu.jsx` from the item `key: 'delete-credentials'` (`CredentialsControls.jsx`) | on-main ✓ (no add-data-testid work needed) |
| Delete-confirm dialog | `delete-confirm-dialog` (shared `DeleteEntityModal.jsx`) | on-main ✓ |
| Dialog title | `delete-confirm-title` | on-main ✓ |
| Dialog message | `delete-confirm-message` | on-main ✓ |
| Dialog entity name | `delete-confirm-entity-name` | on-main ✓ |
| Type-to-confirm Name field | `delete-confirm-name-input` — resolves to the MUI **TextField wrapper**, not the `<input>`; click + `press_sequentially()` per `personal_tokens_page.py` / `mcp_form_page.py` precedent | on-main ✓ |
| Dialog Delete (confirm) button | `delete-confirm-button` | on-main ✓ |
| Dialog Cancel button | `delete-confirm-cancel-button` | on-main ✓ |

**No `testid needed:` rows — every handle this case touches already exists.**

## Network Behavior
- Create: `POST /api/v2/configurations/configurations/{project}` → 200,
  body carries `id`, `label`, `elitea_title`, `type: "github"`.
- Delete: `DELETE /api/v2/configurations/configuration/{project}/{id}` → **204
  No Content** (note the singular `configuration` segment and the id suffix —
  distinct from the plural list endpoint).
- Immediately after the delete the app fires
  `GET /api/v2/configurations/configuration/{project}/{id}` → **404** — the
  `#1666` stale refetch. Deterministic; console-filtered, never asserted-away.
- List refresh: `GET /api/v2/configurations/configurations/{project}?...&section=credentials&section=storage`.

## Known Defects Found During Exploration
- **`#1666`** (OPEN, filed by this analysis) — stale `GET` on the deleted
  credential id → console 404 after a successful delete. Cosmetic; console
  filter only, no soft-assert, no sanctioned-RED.
- **`#518`** (pre-existing) — intermittent `/credentials/all` refetch crash;
  already recovered functionally by `credentials_list_recovery.py`
  (wired into `CredentialsListPage.navigate()`), console-filtered here for
  the same reason the sibling credential specs filter it.

## Blocked Steps
None — all 7 case steps executed live end-to-end, all passed.

## Automation Hints
- Framework: Playwright + pytest; new spec
  `automation/tests/ui/toolkits/test_credential_delete.py`.
- Extend `CredentialDetailPage` additively with the delete-menu + dialog
  handles and a `delete_credential_via_menu(name)`-style flow; do NOT
  duplicate the shared `DeleteEntityModal` handles into a new page object
  when `CredentialDetailPage` is the natural owner (the dialog is opened
  from that page).
- Reuse `CredentialCreatePage.navigate_to_type("github")` +
  `set_display_name()` + `save_button` for step 1 — no new create machinery.
- The delete-confirm Delete button is a `OneClickButton`: click it exactly
  once and wait on the DELETE response, not on a fixed delay.
- After confirming, the app performs a client-side `navigate(..., {replace:true})`
  back to `/credentials/all` — wait on the URL, not on network idle alone.
- **`/credentials/all` does not reliably reach `networkidle`** (implementation
  finding, ELITEA-1964): a `page.reload()` + `wait_for_load_state("networkidle",
  15s)` timed out on one of two implementation runs while the page itself was
  fully rendered. Step 7's reload settles on the credentials-list
  `GET .../configurations/configurations/{project}?...&section=credentials...`
  response instead (`CredentialsListPage.reload_list()`), which is the
  deterministic signal that the reloaded page has real server data.
