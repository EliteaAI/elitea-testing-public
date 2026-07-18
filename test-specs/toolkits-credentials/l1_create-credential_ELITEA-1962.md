# Test Case: Create Credential (GitHub, Token auth) — happy path via sidebar "+" button

## Metadata
- **TMS ID**: ELITEA-1962
- **Linked Story**: none
- **Priority**: l1 (TMS frontmatter `priority: critical`; this project's established
  mapping for `critical` is the `l1` AFS prefix — confirmed against ELITEA-1971,
  ELITEA-1972, ELITEA-1975, all `priority: critical` → `l1_*` filenames)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend, project "Private" / id `399`)
- **User set**: `${TEST_USER}` (nominal — localhost's `auth_state` fixture skips
  interactive login entirely via `VITE_DEV_TOKEN`, so no credential typing is
  actually exercised by this case)
- **Analyst**: qa-engineer (agent), 2026-07-18
- **Status**: ready-for-automation

## Dedup / extend-existing check (why this is a fresh spec, not covered/extend)

Read all 7 existing `automation/tests/ui/toolkits/test_credential_*.py` files plus
`test_toolkit_indicators_for_credentials.py`. Several DO create a GitHub credential
as setup/precondition (`test_credential_id_auto_generation.py`,
`test_credential_edit_rename.py`, `test_credential_search_by_name.py` via UI;
`test_credential_pin_unpin.py`, `test_credential_discard_changes.py`,
`test_toolkit_indicators_for_credentials.py` via API) — but **none** exercises or
asserts the specific things this case's steps require:

- Every UI-driven creation navigates straight to
  `/credentials/create-credential/{type}` (`CredentialCreatePage.navigate_to_type()`),
  bypassing the case's Step 2 (click the sidebar **"+"** button) entirely.
- No existing test selects the **"Token"** (or any non-default) auth-method radio —
  `test_credential_id_auto_generation.py` and `test_credential_edit_rename.py` save
  with the default `Anonymous` auth; `test_credential_required_fields_validation.py`
  never clicks Save at all.
- No existing test reads the **type badge** on the Credentials list-page card
  (`entity-card-tag-chip`) — pin/search/discard tests all read `entity-card-name`
  (the display name) but never the type text next to it.

This is genuinely new coverage on all three axes → `ready-for-automation`, not
`already-covered` or `extend-existing`.

## Preconditions
- User authenticated — `auth_state` fixture (no-op on localhost, `VITE_DEV_TOKEN`).
- `${GIT_HUB_TOKEN}` set in `.env.test` — test `pytest.skip()`s if unset, matching
  `test_credential_pin_unpin.py` / `test_credential_discard_changes.py` precedent.
- **Critical, live-discovered precondition not in the original case text:** the
  project must already contain **at least one credential** before this test's own
  steps run. `CredentialsList.jsx` auto-redirects a **zero-credential** project from
  `/credentials/all` straight to `/credentials/create-credential` (confirmed live —
  see `credential_create_page.py`'s existing `navigate_to_type()` docstring, "Navigate
  to New Credential page for private projects with no credentials"). In that state
  there is no list page and no sidebar "+" button to click — Steps 1–2 as literally
  authored have nothing to act on. This is pre-existing, already-documented product
  behavior, **not a new defect** (reverse-masking guard: the case text assumes a
  list page always renders, which is only true once ≥1 credential exists — "the
  normal state of a shared DEV project" per the same docstring). Seed one throwaway
  credential via `credential_api.create_github_credential(...)` (API, not UI) before
  Step 1 so the real list + "+" button render, matching the seed pattern already used
  by `test_credential_pin_unpin.py`.

## Test Data
### reuse-existing
- none

### generate-per-test (created in test, cleaned up in its own teardown)
- Seed credential (precondition only): `autotest_seed_<slug>` GitHub credential,
  Anonymous auth, created via `credential_api.create_github_credential()`.
- **Display Name**: `autotest_credential` — the case pins this as a literal string
  (not templated with a timestamp). See Automation Hints for the collision-risk
  callout this raises.
- **Credential type**: Github
- **Auth method**: Token
- **Token value**: `${GIT_HUB_TOKEN}` — pass via `settings.git_hub_token` exactly as
  `test_credential_pin_unpin.py` / `test_toolkit_indicators_for_credentials.py`
  already do. Never type or print the real value in any transcript/log outside the
  pytest process — this analyst session used an explicit placeholder string
  (`ghp_placeholder_token_for_afs_exploration`) during manual Playwright-MCP
  exploration for exactly this reason, since MCP tool-call parameters are visible in
  the session transcript.

## Test Steps
1. **[Precondition]** Seed one throwaway GitHub credential via `credential_api`
   (Anonymous auth) so the project has ≥1 credential.
   - **Verify**: API create call returns 200/201 with a numeric `id`.
2. Navigate to `/credentials/all` (sidebar "Credentials" — existing tests use direct
   URL nav; no sidebar-nav-item testid exists, see Concrete Handles).
   - **Verify**: list page renders — at least one `entity-card` visible (the seed
     credential), `sidebar-create-button` visible in the header.
3. Click the `sidebar-create-button` ("+" button, contextual label "Credential"
   while on the Credentials section).
   - **Verify**: URL becomes `/credentials/create-credential?viewMode=owner`;
     "Choose the credentials type" type-selector renders.
4. Click the `toolkit-type-card-github` card.
   - **Verify**: URL becomes `/credentials/create-credential/github`; GitHub-specific
     form renders (Display Name, ID, Base Url, Auth radiogroup, Save/Cancel).
5. Fill Display Name = `autotest_credential` (`toolkit-field-label-input`).
   - **Verify**: field shows the typed value; ID field (`toolkit-field-elitea_title-input`,
     disabled) live-mirrors it as `autotest_credential` (ELITEA-1972 pattern — no
     transform needed here since the input is already lowercase/underscored); Save
     becomes enabled (Base Url ships pre-filled with `https://api.github.com` and
     Anonymous is the default auth, so Display Name alone satisfies required-field
     validation at this point).
6. Click the `toolkit-field-auth-radio-token` radio.
   - **Verify**: "Token" becomes the checked radio; an "Access Token" field appears
     (`toolkit-field-access_token-input-field`).
7. Fill the Access Token field with `${GIT_HUB_TOKEN}`.
   - **Verify**: field accepts and displays the value (masked — `type="password"`
     with a Secret/Password visibility toggle alongside it).
8. Click `credential-form-save-button`.
   - **Verify**: `POST /api/v2/configurations/configurations/{project_id}` → 200;
     response body `label == "autotest_credential"`, `type == "github"`,
     `elitea_title == "autotest_credential"`, numeric `id` present. Page redirects to
     `/credentials/all`.
9. On the list page, locate the `entity-card` matching `autotest_credential`.
   - **Verify**: `entity-card-name` text == `autotest_credential`; the same card's
     `entity-card-tag-chip` text == `Github` (case's Step 8 requirement — the type
     badge).

## Expected Results
- Credential `autotest_credential` is created (200 from the create POST) and
  appears in the `/credentials/all` list immediately (no reload needed — the Save
  redirect lands on a list that already includes it, `created_at desc` puts it
  first).
- Its list card shows both the correct name (`entity-card-name`) and the correct
  type badge (`entity-card-tag-chip` == "Github").
- No new console errors. (The list/type-selector pages emit a pre-existing,
  already-tracked "missing key prop" dev warning from `CredentialTypeSelector.jsx`
  / `GroupedCategory.jsx` — filed as elitea-testing-public#291 per
  `test_credential_search_by_name.py`'s precedent; filter it out, don't assert
  against it as new.)

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| precond: user logged in | — | — | `auth_state` fixture (no-op on localhost) | asserted |
| precond: project + Credentials section accessible | — | AFS step 2 | step 2: list page renders | asserted |
| 1 Navigate to Credentials section | list page loads | AFS steps 1–2 | step 2: `entity-card` + `sidebar-create-button` visible | asserted *(step 1 is a live-discovered precondition, not in original case text — see Preconditions)* |
| 2 Click "+" button | creation form opens | AFS step 3 | step 3: URL + type-selector render | asserted |
| 3 Select "Github" type | Github fields shown | AFS step 4 | step 4: URL + form fields render | asserted |
| 4 Fill Display Name "autotest_credential" | field accepts/displays | AFS step 5 | step 5: field value + Save-enabled | asserted |
| 5 Select "Token" auth method | Token input available | AFS step 6 | step 6: radio checked + field appears | asserted |
| 6 Fill Token value | field accepts input | AFS step 7 | step 7: field value | asserted |
| 7 Click Save | credential saved | AFS step 8 | step 8: POST 200 + redirect | asserted |
| 8 Verify list shows name + Github badge | card present, correct badge | AFS step 9 | step 9: `entity-card-name` + `entity-card-tag-chip` | asserted |

**Axis 2 — Analyst additions**

- AFS step 8 asserts the create POST **response body** (`label`, `type`,
  `elitea_title`, `id`) beyond just the HTTP status — *added: matches this suite's
  established pattern (`test_credential_id_auto_generation.py`,
  `test_credential_discard_changes.py`) of treating the API response as the
  ground-truth check, not just the eventual UI render.*
- AFS step 5 asserts the ID-autogeneration mirror (`autotest_credential` →
  `autotest_credential`) — *added: this project has a known, already-automated
  ID-autogen behavior (ELITEA-1972); asserting it here cheaply guards against a
  regression in the exact flow this case exercises, at zero extra interaction cost.*
- Console-error side-channel check across the whole flow (filtering the known #291
  warning) — *added: standard practice in every sibling test in this file
  (`test_credential_pin_unpin.py`, `test_credential_discard_changes.py`, etc.); the
  case text doesn't mention it but silent regressions are exactly what this guards.*

## Cleanup
1. Delete the case's own credential (`credential_api.delete_credential(id)`,
   `id` captured from the create-POST response body in AFS step 8).
2. Delete the seed credential from AFS step 1.
3. Both in a `try`/`finally` around the test body, matching every sibling test in
   this file (never conditional on test success).

(Analyst-session cleanup: both credentials created during this exploration — ids
`1771` seed, `1772` `autotest_credential` — were deleted via direct
`DELETE /api/v2/configurations/configuration/{project_id}/{id}` calls, both returned
`204`. Re-navigating to `/credentials/all` afterward confirmed the project reverted
to the zero-credential auto-redirect state, i.e. cleanup left no residue.)

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only, no fallback rung**
(`.agents/testing.md` § Locator policy / `.agents/role-overrides.md`) — every row's
"Fallback" is `none` by policy, not by omission.

| Element | Testid | Notes |
|---|---|---|
| Sidebar "+" create button | `sidebar-create-button` | Pre-existing, already used by `agents_list_page.py`. Contextual label text (reads "Credential" while on `/credentials/*`). Not yet declared on `CredentialsListPage` — add it there. |
| GitHub type card | `toolkit-type-card-github` | Pre-existing dynamic template `toolkit-type-card-{type}`, already used by `CredentialCreatePage.navigate_to_type()`'s docstring / `TYPE_CARD_SELECTOR`. |
| Display Name input | `toolkit-field-label-input` | Pre-existing (`CredentialFormFieldsMixin.display_name_input`). Use the mixin's `set_display_name()` (click + select_text + type — MUI onChange quirk), not a raw `.fill()`. |
| ID field (read-only mirror) | `toolkit-field-elitea_title-input` | Pre-existing (`CredentialDetailPage.id_input` — reuse or promote to the mixin if `CredentialCreatePage` needs it too). |
| **Auth "Token" radio** | `toolkit-field-auth-radio-token` | **Brand new this session** — see "New testid" callout below. Dynamic template: `toolkit-field-auth-radio-{slug}` where slug = `item.value.toLowerCase().replace(/\s+/g,'-')`. **Gotcha: label text ≠ underlying value** — "Anonymous" → slug `none` (`toolkit-field-auth-radio-none`), "Token" → `toolkit-field-auth-radio-token` (matches), "Password" → `toolkit-field-auth-radio-password`, "App private key" → `toolkit-field-auth-radio-app-private-key`. This case only needs `token`. |
| Access Token input | `toolkit-field-access_token-input-field` | Pre-existing, **not yet used by any page object**. The outer wrapper `toolkit-field-access_token-input` is a non-fillable `<div class="MuiFormControl-root">` — target the `-field`-suffixed `<input>` directly (same naming family as `api_key_input`'s `toolkit-field-api_key-input-field`, which the underlying DOM confirms is literally the same rendered field — `name="api_key"` — just relabeled "Access Token" for GitHub's Token auth method). |
| Save button | `credential-form-save-button` | Pre-existing (`CredentialFormFieldsMixin.save_button`). |
| Credential card (list) | `entity-card` | Pre-existing (`CredentialsListPage.entity_card`). Scope with `.filter(has_text=display_name)` per the existing `click_credential_card()` pattern. |
| Credential card name | `entity-card-name` | Pre-existing (`CredentialsListPage.entity_card_name`). |
| **Credential type badge** | `entity-card-tag-chip` | **Pre-existing, but not yet used by any page object.** Live-verified: `<span data-testid="entity-card-tag-chip"><span>Github</span></span>` inside the matched `entity-card` — this satisfies the case's Step 8 type-badge requirement with zero new testid work. Add `ENTITY_CARD_TAG_CHIP_SELECTOR = '[data-testid="entity-card-tag-chip"]'` as a scoped UPPER_CASE constant on `CredentialsListPage` (same pattern as `ENTITY_CARD_SELECTOR` on `CredentialDetailPage`) and a `get_type_badge(display_name)` method. |

### New testid landed this session (EliteaUI)

The Auth radiogroup (`Anonymous` / `Token` / `Password` / `App private key`) had
**zero** distinguishing `data-testid` — only generic, repeated MUI icon testids
(`RadioButtonUncheckedIcon` / `RadioButtonCheckedIcon`) and a shared
`name="radio-buttons-group"` with no `id`. Per this project's testid-only policy
("missing testid on the target is work to do, not a reason to rung down"), added:

- `EliteaUI/src/[fsd]/shared/ui/checkbox/RadioButtonGroup.jsx` — new optional
  `testId` prop (backward compatible; the group's other 4 callers — index/pipeline
  schedule/webhook modals, LLM max-tokens section — are unaffected, so no testid
  noise lands on elements this case doesn't touch, per the team's "scope is
  load-bearing" ruling). Templated per-option: `${testId}-${slug(item.value)}`.
- `EliteaUI/src/[fsd]/features/toolkits/ui/form/ToolBase/ToolSection.jsx` — wired
  `testId={`toolkit-field-${sectionKey}-radio`}` at the one call site this case
  exercises (the credential/toolkit Auth section; `sectionKey` is already in scope
  there and happens to be `"auth"` for GitHub's Auth grouping).
- Committed + **pushed** to `EliteaAI/EliteaUI`'s `automation/testids` branch,
  commit `c8d5c6af` (`test: [EL-0000] add data-testid for credential/toolkit Auth
  radio group (ELITEA-1962)`). Live-verified via Vite HMR on localhost:5173 with a
  genuine Playwright click (not a DOM-level click) before committing.
- **Not yet on `EliteaUI` `main`** — a human must cherry-pick this commit before the
  resulting automated test can run against a deployed env; on localhost it's live
  now via `automation/testids`.

## Network Behavior
- `POST /api/v2/configurations/configurations/{project_id}` — fires on Save click;
  200 on success. Response body carries `id`, `label`, `type` ("github"),
  `elitea_title`. Same endpoint/shape as every other credential-create test in this
  suite (`test_credential_id_auto_generation.py` et al.) — no new endpoint.
- Save redirects client-side to `/credentials/all`; the already-rendered list
  includes the new card without a further list-refetch GET being required for the
  assertion (`created_at desc` ordering puts it first — live-confirmed).

## Known Defects Found During Exploration
None found. (The one console entry seen — `CredentialTypeSelector.jsx` /
`GroupedCategory.jsx`'s "missing key prop" warning — is pre-existing and already
tracked as elitea-testing-public#291, not a new finding; filter it, don't assert
against it.)

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md` (nothing non-obvious).
- Page objects to extend (no new page-object *files* needed):
  - `automation/pages/credentials_list_page.py` (`CredentialsListPage`): add
    `create_button = LocatorDescriptor(testid="sidebar-create-button", ...)`;
    `entity_card_tag_chip = LocatorDescriptor(testid="entity-card-tag-chip", ...)`
    (collection locator, mirrors `entity_card_name`); `ENTITY_CARD_TAG_CHIP_SELECTOR`
    scoped constant; `get_type_badge(display_name: str) -> str` method following the
    exact `entity_card.filter(has_text=...)` pattern already in
    `click_credential_card()`.
  - `automation/pages/credential_create_page.py` (`CredentialCreatePage`): add
    `AUTH_METHOD_RADIO = '[data-testid="toolkit-field-auth-radio-{}"]'` dynamic
    template constant; `access_token_input = LocatorDescriptor(testid="toolkit-field-access_token-input-field", ...)`;
    `select_auth_method(method_slug: str)` and `set_access_token(value: str)`
    methods (the latter using click + `press_sequentially()`, matching
    `set_base_url()` / `set_api_key()` / `set_username()`'s existing MUI-onChange
    workaround in the same file — do not use `.fill()`).
- Fixture: `credential_api` (function-scoped, per `.claude/rules/api-patterns.md`)
  for both the seed credential and cleanup — matches `test_credential_pin_unpin.py`.
- **Test-data collision risk**: the case's Display Name (`autotest_credential`) is a
  literal, not timestamped. If a prior run's `finally` cleanup ever fails to run
  (killed process, etc.), a second run's create POST would collide on the
  auto-generated `elitea_title` (same slug both times). Every other test in this
  suite timestamps its display names for exactly this reason
  (`f"autotest_..._{ts}"`). Recommend the implementer either (a) trust the
  try/finally cleanup discipline like the rest of the suite and use the literal
  name so the assertion matches the case's exact wording, or (b) confirm with the
  reviewer whether a timestamp-suffixed variant (`autotest_credential_{ts}`,
  asserted via substring/prefix rather than exact-equals) still satisfies the case's
  Pass/Fail criteria ("`autotest_credential` is listed") — flagging both options
  rather than silently picking one.
- **Never type or log the real `GIT_HUB_TOKEN` value anywhere outside the pytest
  process** — use `settings.git_hub_token` server-side. This AFS's own exploration
  used an explicit placeholder string for that reason (see Test Data).
