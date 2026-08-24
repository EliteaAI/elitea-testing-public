# Test Case: Edit Remote MCP — Client Secret with Secret/Password Toggle

## Metadata
- **TMS ID**: ELITEA-1932
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `priority: critical`; case body says
  "medium" — same pre-existing inconsistency recorded in the ELITEA-1929 /
  ELITEA-1930 AFS; frontmatter authoritative)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids`, DEV backend), project 399
- **User set**: `${TEST_USER}` (localhost: `VITE_DEV_TOKEN` auto-auth)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), session 2026-08-24
- **Status**: ready-for-automation

## Preconditions
- User is authenticated; project id from `${ELITEA_PROJECT_ID}`.
- A Remote MCP exists and its detail page is open in Form view.
- Access to the Elitea secret vault: project 399 exposes a stable saved secret
  named **`auth_token`** — the same read-only vault entry the merged credentials
  case ELITEA-1968 selects (`test_credential_secret_password_toggle.py:72`).

## Test Data

### generate-shared-with-cleanup

Same reasoning as the sibling ELITEA-1930 / ELITEA-1931 AFS: no discoverable
pre-existing Remote MCP on this environment, and writing a client secret is
destructive to whatever toolkit is borrowed → the test seeds its own disposable
Remote MCP through the real UI create flow and deletes it in teardown.

| Field | Value | Why |
|---|---|---|
| Seed name | `autotest_mcp_secret_<6hex>` (26 chars) | ≤ `MAX_NAME_LENGTH = 32` |
| Url | `https://mcp.example.com/sse` | stored only; never dialled |
| Vault secret | `auth_token` | pre-existing project secret, **read only** — never created, never modified, never deleted by this test |

## Test Steps

Live-executed 2026-08-24 against `http://localhost:5173` (seeded toolkit id 3035,
deleted after the run).

| # | Action | Expected (case) | Observed live |
|---|--------|-----------------|---------------|
| 1 | Open a Remote MCP detail page in Form view | Detail page loads in Form view | `toolkit-form-view-toggle` `aria-pressed == "true"`; `toolkit-detail-title` == seeded name |
| 2 | Locate "Client Secret" field | Client Secret field is visible | count == 0 until `expand_configuration_section()` (digest § MCP DETAIL page: configuration fields are COLLAPSED); after expanding, `toolkit-field-client_secret-input` is visible |
| 3 | Verify "secret view toggler" group is visible with "Secret" and "Password" buttons | Toggle group with both buttons displayed | `toolkit-field-client_secret-input-toggle-secret` (text `Secret`) and `...-toggle-password` (text `Password`) both visible — testids come from the shared `Toggle.jsx` via `SecretField.jsx:342` (`testIdPrefix = "<field-testid>-toggle"`), **both `automation/testids`-only — see § Concrete Handles** |
| 4 | Verify "Password" button is pressed (active) by default — field shows masked text | Password mode active, text masked | `...-toggle-password` `aria-pressed == "true"`, `...-toggle-secret` `aria-pressed == "false"`; the real input `toolkit-field-client_secret-input-field` has `type == "password"` (masked) |
| 5 | Click "Secret" button | Toggle switches to Secret mode | click flips `aria-pressed`: secret `true`, password `false` |
| 6 | Verify toggle switches to Secret mode | Secret button is now active | in Secret mode the native `<input>` is **unmounted** and replaced by the vault `SingleSelect`: `...-input-field` count == 0, `toolkit-field-client_secret-input-combobox` count == 1 |
| 7 | Enter a credential reference in Secret mode from Elitea secret vault | Secret reference entered in the field | opening the combobox renders the `CREATE` group (`New Private Secret`) plus the `SAVED SECRETS` group; clicking `select-option-{{secret.auth_token}}` closes the dropdown and the combobox displays `auth_token`; Save/Discard become enabled |
| 8 | Click Save | Operation completes successfully | `PUT /tool/prompt_lib/{project}/{id}` → **200**, response body `settings.client_secret == "{{secret.auth_token}}"`. **No success toast on this surface** (digest). |
| 9 | Reload — verify Client Secret value persisted in chosen mode | Client Secret shown in Secret mode with the saved reference | after `reload_and_wait()` + re-expand: `...-toggle-secret` `aria-pressed == "true"` (the mode is **derived**, not stored — `SecretField.jsx` re-enters Secret mode because the stored value matches `/^{{secret\.([A-Za-z0-9_]+)}}$/` **and** the name is present in the project vault), combobox text `auth_token`, and `get_raw_json_full()["settings"]["client_secret"] == "{{secret.auth_token}}"` |

## Expected Results
- The Client Secret field renders a two-button "secret view toggler" (Secret /
  Password) beside it.
- Password mode is active by default and the value is masked (`type="password"`).
- Clicking "Secret" switches the field to the vault-backed select.
- A saved vault secret can be selected and displayed by name.
- Save persists the reference as `{{secret.<name>}}` under
  `settings.client_secret`.
- After a full reload the field comes back in Secret mode showing the same
  secret name.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: logged in | precondition | framework `auth_state` |
| Precondition: existing Remote MCP open in Form view | precondition (seeded) | seeded via the UI create flow — § Test Data; Form view asserted in step 1 |
| Precondition: access to the Elitea secret vault | asserted | step 7 asserts the SAVED SECRETS group renders and contains `auth_token` |
| Step 1 — detail page loads in Form view | asserted | `form_view_toggle` `aria-pressed == "true"` + `detail_title` == seeded name |
| Step 2 — Client Secret field visible | asserted | `client_secret_input` visible after expanding the configuration section |
| Step 3 — toggle group with Secret + Password visible | asserted | both toggle buttons visible; their texts asserted as `Secret` / `Password` |
| Step 4 — Password pressed by default, text masked | asserted | `aria-pressed` pair + `type == "password"` on the real input |
| Step 5 — click Secret | asserted | the click itself + step 6's assertions |
| Step 6 — Secret button now active | asserted | `aria-pressed` pair flipped; combobox mounted, native input unmounted |
| Step 7 — enter a credential reference from the vault | asserted | dropdown option `select-option-{{secret.auth_token}}` clicked; combobox text == `auth_token` |
| Step 8 — Save completes successfully | asserted | PUT 200 + body `settings.client_secret == "{{secret.auth_token}}"` |
| Step 9 — value persisted in the chosen mode after reload | asserted | post-reload Secret mode `aria-pressed == "true"` + combobox text + Raw Json reference |
| Expected Final State — value retained in Secret mode after save + reload | asserted | steps 8-9 together |
| Pass criterion: no errors during the flow | asserted | console-error listener (known #291 filtered, #549 soft — sibling-spec pattern) |

### Axis 2 — Analyst additions

| Addition | Why grounded |
|---|---|
| Raw Json assertion of the stored `{{secret.auth_token}}` reference | Step 9's "the saved reference" is only shown by *display name* in the combobox; the reference itself is the thing that must persist, and the Raw Json view is the product's own rendering of it (no substitution). |
| Save-button state assertions (disabled pristine → enabled after picking a secret) | Step 8 presupposes Save is clickable; the dirty gate is real on this surface. |
| PUT-response body assertion | Step 8's "operation completes successfully" is otherwise unobservable — no toast is rendered here. |
| Native-input unmount / combobox mount assertion in step 6 | The case's "toggle switches to Secret mode" has a stronger observable than `aria-pressed` alone: the whole input control is swapped. |
| Console-error monitoring | Case Pass criterion "All steps complete without errors". |

## Case-text divergence
None material. Step 7's "Enter a credential reference" is a *selection* from the
vault dropdown, not free typing — Secret mode renders a `SingleSelect`, not a text
input. The step is executed as the product implements it.

## Cleanup
The seeded toolkit is deleted in a `finally:` block via
`ToolkitAPI.delete_toolkit(id)`. The vault secret `auth_token` is **read only** —
never created, edited, or deleted.

## Concrete Handles (discovered during exploration)

| Element | Handle | Provenance |
|---|---|---|
| Client Secret wrapper (SecretField root) | `toolkit-field-client_secret-input` | on-main ✓ |
| Client Secret real `<input>` (Password mode only) | `toolkit-field-client_secret-input-field` | on-main ✓ |
| "Secret" toggle button | `toolkit-field-client_secret-input-toggle-secret` | **on `automation/testids` ONLY** — EliteaAI/EliteaUI@5892ae48 (EL-1967). `SecretField.jsx:342` passes no `testIdPrefix` on `main` **and** `src/components/Toggle.jsx` carries no testid at all on `main`. **Not yet on `main`.** |
| "Password" toggle button | `toolkit-field-client_secret-input-toggle-password` | **on `automation/testids` ONLY** — same commit EliteaAI/EliteaUI@5892ae48. **Not yet on `main`.** |
| Vault select (Secret mode only) | `toolkit-field-client_secret-input-combobox` | on-main ✓ |
| Saved-secret option (dynamic) | `select-option-{{secret.<name>}}` | on-main ✓ (same grammar `CredentialCreatePage.SECRET_SAVED_OPTION` already uses) |
| SAVED SECRETS group header | `select-group-header-Saved Secrets` | on-main ✓ |
| Configuration show-more | `toolkit-configuration-show-more` | on-main ✓ — EliteaAI/EliteaUI@ab757380 (`ToolBase.jsx:375`) |
| Detail Save / Discard buttons | `toolkit-detail-save-button` / `toolkit-detail-discard-button` | on-main ✓ — EliteaAI/EliteaUI@bf4a13ad (`ToolkitsTabBarContainer.jsx:149,159`); promoted since the ELITEA-1929 AFS was written |
| Form / Raw Json view toggles + Raw Json content | `toolkit-form-view-toggle` / `toolkit-raw-json-view-toggle` / `toolkit-raw-json-editor-content` | on-main ✓ |

No new testid is required for this case — but **the case is not deployed-env
promotable yet**: the Secret/Password toggle pair (steps 3-6, 9) exists only on
`automation/testids`. Unblocks when a human cherry-picks EliteaAI/EliteaUI@5892ae48
to `EliteaAI/EliteaUI` `main` and it deploys. Owner: human.

### Provenance verification (run 2026-08-24, fix round 1)

These testids are **template-composed** in shared components
(`` data-testid={`toolkit-field-${k}-input`} ``, `testIdPrefix`, `${dataTestId}-combobox`),
so a bare `git grep '<literal-testid>' origin/main` finds **nothing** and silently
reports "not on `main`" — the #19 false-row failure mode. The provenance column above
is verified by grepping the **composing source file** on each ref, after
`cd ../EliteaUI && git fetch origin`:

```
toolkit-field-<k>-input                        main:YES  testids:YES   (ToolBase/ToolBaseProperty.jsx)
toolkit-field-<k>-editor(-content)             main:YES  testids:YES   (ToolBase/ToolBaseProperty.jsx)
toolkit-configuration-show-more                main:YES  testids:YES   (ToolBase/ToolBase.jsx:375)
toolkit-detail-save-button                     main:YES  testids:YES   (toolkits-tab-bar/ToolkitsTabBarContainer.jsx:149)
toolkit-detail-discard-button                  main:YES  testids:YES   (toolkits-tab-bar/ToolkitsTabBarContainer.jsx:159)
toolkit-form/raw-json-view-toggle              main:YES  testids:YES   (shared/ui/tab-group-button/FormViewToggle.jsx)
toolkit-raw-json-editor-content                main:YES  testids:YES   (toolkits/ui/form/ToolCustom.jsx:218)
toolkit-detail-title                           main:YES  testids:YES   (pages/Toolkits/EditToolkit.jsx:398)
<field>-input-field (native input)             main:YES  testids:YES   (shared/ui/secret-field/SecretField.jsx:77)
<field>-input-toggle-{secret,password}         main:no   testids:YES   (shared/ui/secret-field/SecretField.jsx:342)
Toggle.jsx renders the toggle testids          main:no   testids:YES   (src/components/Toggle.jsx)
<field>-input-combobox                         main:YES  testids:YES   (shared/ui/select/SingleSelect.jsx:661)
select-option-<value>                          main:YES  testids:YES   (shared/ui/select/SingleSelect.jsx:416)
select-group-header-<group>                    main:YES  testids:YES   (shared/ui/select/SingleSelect.jsx:383)
```

## Network Behavior
- `POST /tools/prompt_lib/{project}` → 201 (seed).
- `GET /secrets/...` (vault list) fires only once Secret mode is active
  (`SecretField.jsx` `skip` flag).
- `PUT /tool/prompt_lib/{project}/{id}` → 200 on Save.
- The MCP URL is never dialled.

## Known Defects Found During Exploration
None. Note that the credentials surface's known dropdown-close defect
(#1047 — `skipNextCloseRef`) did **not** reproduce here: selecting a saved secret
closed the dropdown normally on the MCP detail page.

## Blocked Steps
None.

## Automation Hints
- The vault list is fetched lazily — `useSecretsListQuery` is `skip`ped while the
  field is in Password mode with a non-secret value. Open the dropdown and wait on
  the first `select-option-{{secret.` node, not on network idle.
- In Secret mode the native input is **unmounted** — assert its absence with
  `to_have_count(0)`, never `not_to_be_visible()`.
- Secret mode after reload is **derived** from the stored value; if the referenced
  secret ever disappears from the project vault the field falls back to Password
  mode. `auth_token` is a long-standing project secret (used by ELITEA-1968) — if
  step 9 ever fails on the mode, check the vault before suspecting the product.
- `expand_configuration_section()` is required twice: on first load and again
  after `reload_and_wait()`.
