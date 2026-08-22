# Test Case: Credential — Secret/Password Storage Toggle

## Metadata
- **TMS ID**: ELITEA-1968
- **Linked Story**: none
- **Priority**: l1 (frontmatter `priority: high`, body header `Priority: high` — consistent)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`), project
  `Private` / `${ELITEA_PROJECT_ID}`=399, identity "Test Bot"
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation
- **Case-gate note**: `status: draft`, `execution_type: manual` — intake-eligible
  per `.agents/test-automation.yaml`. All 7 steps executed live 2026-08-22.

## Preconditions
- User is logged in (localhost `auth_state`).
- Project `Private` (399) selected — the framework default (`ELITEA_PROJECT_ID=399`).
- **At least one saved secret named `auth_token` exists in the project's Secret
  vault.** Live-verified: project 399 carries 120 secrets, `auth_token` among
  them — this is exactly the secret the case names as its test data. The test
  reads it, never mutates it (read-only, Hard Rule 10).
- The credential create form is reachable at `/credentials/create-credential/github`.

## Test Data

### reuse-existing (read-only)
- Saved secret `auth_token` in project 399's vault — selected in Step 5,
  never modified.
- Credential type `github` + auth method `Token` — rendered from the backend
  schema (`GET /configurations/available/?section=credentials`), no seeding.

### generate-per-test
- Plaintext token typed in Step 7: `ghp_autotest_placeholder_123` (a literal
  placeholder — never a real credential, never saved; the form is abandoned).

**Nothing is created, saved or deleted server-side.** The case's Expected Final
State says "both modes store valid token values", but the case has no Save step
and the form is never submitted — see § Coverage Map Axis 1 row for the Final
State, which scopes "store" to *the field holds the value*, the only thing the
case's own steps produce.

## Test Steps

| # | Action | Expected (live-confirmed) |
|---|---|---|
| 1 | Navigate to `/credentials/create-credential/github`; select the `Token` auth radio | The Access Token secret field renders: wrapper `toolkit-field-access_token-input`, native input `toolkit-field-access_token-input-field` |
| 2 | Read the Secret/Password toggle beside the token field | Both toggle buttons present and visible: `…-input-toggle-secret` and `…-input-toggle-password` |
| 3 | Click `Secret`, then open the select | `Secret` becomes `aria-pressed="true"`, `Password` `"false"`; the native password input is gone and a combobox `…-input-combobox` renders. Opening it shows group header `select-group-header-Saved Secrets` (rendered text `SAVED SECRETS`) with ≥1 saved-secret option |
| 4 | Read the CREATE section of the same open dropdown | Group header `select-group-header-Create` (rendered `CREATE`) is present, carrying option `select-option-__create_private_secret__`. **On the personal project its label reads `New Private Secret`, not the case's "New Project Secret"** — see § Case-text divergence |
| 5 | Click the `auth_token` option (`select-option-{{secret.auth_token}}`) | The dropdown closes and the combobox displays `auth_token`; the underlying field value is `{{secret.auth_token}}` |
| 6 | Click `Password` on the toggle | `Password` `aria-pressed="true"`, `Secret` `"false"`; the combobox is gone (count 0) and the native input `…-input-field` is back with `type="password"`, cleared to `""` (the product clears the value on mode switch) |
| 7 | Type `ghp_autotest_placeholder_123` into the token field | `input_value()` equals the typed string AND the input's `type` attribute is still `password` — i.e. the value is accepted and rendered masked |

## Expected Results
- The Secret/Password toggle renders beside the Access Token field of a GitHub
  credential once `Token` auth is selected, and both options are reachable.
- `Secret` mode replaces the plaintext input with a vault-backed select whose
  dropdown carries a `CREATE` group (a create-new-secret action) and a
  `SAVED SECRETS` group listing the project's secrets.
- Selecting a saved secret displays that secret's **name** in the field while
  storing the `{{secret.<name>}}` template as the value.
- `Password` mode restores a masked (`type="password"`) plaintext input which
  accepts typed characters and keeps them masked.
- Switching modes clears whatever the other mode held (product behaviour,
  `SecretField.handleToggleTab`) — asserted in Step 6.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Disposition | Asserted where |
|---|---|---|
| Precondition: logged in | precondition | framework `auth_state` |
| Precondition: project with ≥1 saved secret (`auth_token`) | precondition | asserted implicitly by Step 5's option click; explicit `to_have_count(1)` on the option before clicking |
| Precondition: Credentials section accessible | precondition | Step 1 navigation |
| Step 1 — create Github credential, Token auth → form shows Token input | asserted | Step 1 — `access_token` field + native input visible |
| Step 2 — toggle visible next to the token input | asserted | Step 2 — both toggle buttons visible |
| Step 3 — click Secret → dropdown shows SAVED SECRETS from the vault | asserted | Step 3 — `aria-pressed` flip + `select-group-header-Saved Secrets` visible + ≥1 saved option |
| Step 4 — "New Project Secret" available under a CREATE section | asserted (label divergence declared) | Step 4 — `select-group-header-Create` visible + `select-option-__create_private_secret__` visible, label asserted as the product's live value |
| Step 5 — select existing secret → its name appears in the field | asserted | Step 5 — combobox text `auth_token`, value `{{secret.auth_token}}` |
| Step 6 — switch to Password → masked plaintext input | asserted | Step 6 — combobox count 0, native input visible, `type="password"` |
| Step 7 — type a token → accepted and masked | asserted | Step 7 — `input_value()` equals typed text AND `type` still `password` |
| Expected Final State — "both modes store valid token values" | asserted (scoped) | Steps 5 + 7 — the value each mode holds. The case has no Save step, so "store" cannot mean persistence here; nothing is submitted |
| Pass criterion — "all steps complete without errors" | asserted | every step's own assertions; no console side-channel (see § Automation Hints) |

### Axis 2 — Analyst additions

| Addition | Why grounded |
|---|---|
| `aria-pressed` asserted on BOTH toggle buttons at each switch, not just the clicked one | The Fail criterion is "the toggle does not switch modes". A one-sided check passes on a toggle that lights both buttons; the exclusive pair is the actual contract (`ToggleButtonGroup exclusive`) |
| Combobox asserted `to_have_count(0)` in Password mode, native input `to_have_count(0)` in Secret mode | The two modes render mutually-exclusive elements. Presence-only assertions cannot see "both rendered", which is a real regression shape |
| Dropdown asserted CLOSED after the selection (`to_have_count(0)` on the SAVED SECRETS header) | Step 5's expected result is that the selected secret "appears in the token field"; a select that stays open after a pick has not committed the selection. **Originally specced as an assertion on the underlying `{{secret.auth_token}}` value — DROPPED, see below** |

**Dropped Axis-2 addition (declared).** The stronger check — assert the
combobox displays the secret's NAME while the field stores the
`{{secret.<name>}}` TEMPLATE — has **no compliant handle today**: MUI's
`MuiSelect-nativeInput` (the element carrying the bound value) receives no
testid, and `SingleSelect`'s `inputProps` pass-through does not reach it
(tried live, 2026-08-22, and reverted). Reaching it would require a raw
`.locator("input")` chained off the wrapper, which is NOT one of the two
#579 sanctioned exceptions (this is our own JSX, not a third-party widget
subtree or an editor's internal render nodes) — so it is `CHANGES_REQUESTED`
territory, not a judgement call. Recorded as a **testid gap** in
`_surface.md` for whichever case needs it: `SingleSelect.jsx` would need to
pass the native input's testid via MUI's `slotProps.htmlInput`, which is a
shared-component change bigger than this case warrants. The displayed name
plus the dropdown-closes assertion is what ships.
| Field asserted cleared (`""`) after the Secret→Password switch in Step 6 | The product deliberately clears on mode switch. Asserting it pins live behaviour and makes Step 7's "value is accepted" unambiguous (the typed text, not a leftover) |

## Cleanup
None required — the case creates nothing server-side. The credential form is
abandoned without Save; the typed placeholder token never leaves the browser.
The `auth_token` secret is read-only.

## Concrete Handles (discovered during exploration)

All handles below confirmed live 2026-08-22 on `localhost:5173`, project 399.

| Element | Handle | Provenance |
|---|---|---|
| Auth-method radio (Token) | `[data-testid="toolkit-field-auth-radio-token"]` | on-main ✓ (`RadioButtonGroup.jsx`) |
| Access Token secret-field wrapper | `[data-testid="toolkit-field-access_token-input"]` | on-main ✓ (`ToolBaseProperty.jsx`) |
| Access Token native input (Password mode) | `[data-testid="toolkit-field-access_token-input-field"]` | on-main ✓ (`SecretField.jsx` `nativeInputTestId`) |
| Secret/Password toggle buttons | `[data-testid="toolkit-field-access_token-input-toggle-secret"]` / `…-toggle-password` | on-`automation/testids` only (added by ELITEA-1967, EliteaAI/EliteaUI@5892ae48 — awaiting human cherry-pick to `main`) |
| Secret-mode combobox | `[data-testid="toolkit-field-access_token-input-combobox"]` | on-main ✓ (`SingleSelect.jsx` `SelectDisplayProps`, fed by the same `data-testid` the caller spreads) |
| Dropdown group header — CREATE | `[data-testid="select-group-header-Create"]` | on-main ✓ (`SingleSelect.jsx:383`) |
| Dropdown group header — SAVED SECRETS | `[data-testid="select-group-header-Saved Secrets"]` | on-main ✓ (same) |
| CREATE action option | `[data-testid="select-option-__create_private_secret__"]` | on-main ✓ (`SingleSelect.jsx:416`, action branch) |
| Saved-secret option (dynamic) | `[data-testid="select-option-{{secret.<name>}}"]` | on-main ✓ (`SingleSelectMenuItem.jsx:117`) |

**Rendered text is UPPERCASED by CSS** (`CREATE`, `SAVED SECRETS`); the
underlying strings are `Create` / `Saved Secrets`. Playwright's `inner_text()`
returns the CSS-transformed form — assert `CREATE` / `SAVED SECRETS`.

### Testid work performed (`add-data-testid` discipline)
None needed for ELITEA-1968 — every handle it touches already exists (see the
provenance column). The two testids this unit DID add serve ELITEA-1969 only;
they are recorded in that case's AFS.

### Page object impact
`CredentialCreatePage` (`automation/pages/credential_create_page.py`) gains
class-level template constants + accessors for the secret-mode select
(combobox, group headers, saved-secret option, create option). No existing
method body changes — purely additive.

## Network Behavior
- `GET /configurations/available/?section=credentials` — renders the form.
- `GET /secrets/secrets/default/399` — fires only when the field enters Secret
  mode (`useSecretsListQuery` is `skip`-gated on `activeTab`), and its result is
  RTK-Query-cached for the rest of the page's life. Settle on the saved-secret
  options being visible, not on `networkidle` (see § Automation Hints).
- No write requests at all.

## Known Defects Found During Exploration
None for this case's own flow. Two live-observed behaviours that are **product
behaviour, not defects**, are pinned by assertions above (mode-switch clears the
value; the label is project-scope-dependent).

### Case-text divergence — filed as a clarification, NOT a bug
Step 4's expected result names the option **"New Project Secret"**. The live
product renders that label **only off the personal project**:

```js
// SecretField.jsx createSecretsOptions
label: personal_project_id === selectedProjectId ? 'New Private Secret' : 'New Project Secret'
```

The automation identity's default project (`ELITEA_PROJECT_ID=399`, "Private")
**is** its `personal_project_id`, so the rendered label is `New Private Secret`.
The option itself, its testid, and its behaviour are identical in both scopes.

Per `.agents/role-overrides.md` § Reverse-masking guard the test asserts the
**live** label and the divergence is filed as a case-text clarification — the
case should say "New Private Secret / New Project Secret depending on whether
the active project is the user's personal project". Asserting "New Project
Secret" here would be masking a stale hypothesis.

Running the case on a team project instead was evaluated live and rejected:
project 471 carries **zero** secrets (Step 5 has nothing to select without
seeding a shared team project) and its `/settings/secrets` reproduces the known
defect #1203 render loop.

## Blocked Steps
None — all 7 steps executed live end-to-end.

## Automation Hints
- **Never `networkidle` on the credentials routes** (`.agents/testing.md`,
  ELITEA-1964/1967). Use `CredentialCreatePage.open_type_form()`, which waits on
  `toolkit-field-label-input`.
- **The MUI select must be opened with a real click** (`browser_click` /
  Playwright `.click()`); a DOM `.click()` on the combobox div does not open it.
- **The dropdown does NOT close on a click outside via JS** — use Playwright's
  own click, or press `Escape`, or select an option (selecting a saved secret
  closes it normally, confirmed).
- Selecting a value is confirmed by the combobox's `inner_text()`; the stored
  template lives on the hidden `<input>` inside the wrapper (`input_value()`).
- The saved-secrets list can be long (120 options on project 399) — never
  enumerate it; target the one option by its dynamic testid.
