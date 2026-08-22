# Test Case: Credential — Create Project Credential from Toolkit Flow

## Metadata
- **TMS ID**: ELITEA-1977
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `high` — same mapping as the merged
  sibling `l1_create-private-credential-from-toolkit-dropdown_ELITEA-1976.md`,
  which shipped as `@pytest.mark.p1`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`)
- **User set**: `${TEST_USER}` (nominal — localhost's `auth_state` fixture is
  a no-op via `VITE_DEV_TOKEN`; the same identity, "Test Bot"/`author_id 659`,
  `personal_project_id 399`, backs both the browser session and the
  Bearer-token API clients)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot),
  2026-08-22
- **Status**: ready-for-automation

This is the **project-scoped mirror** of ELITEA-1976 (private-scoped). Same
dropdown, the *other* CREATE option
(`{"kind":"create_action","private":false}`), a different destination project
and a different scope observable. It is a **new spec**, not an extension of
ELITEA-1976's: the whole flow differs from step 1 (project selection),
requires a writable team project, needs its own seeded toolkit, and its
terminal assertion is the inverse scope.

## Classification notes — declared improvisations (role-overrides.md § Declared-improvisation protocol)

**1. The team project MUST be one the identity can WRITE credentials in —
that is project 400 ("UI Testing"), not 471.** `CredentialsSelect.jsx`'s
`createSelectHandler` resolves the create-form's project as
`option.private ? personal_project_id : selectedProjectId`, so a **project**
credential is created in the *currently selected* project. Two constraints
therefore bind at once:
- The project must differ from `personal_project_id` (399), or the "New
  project …" option is absent from the DOM entirely (`createMenuData`
  `useMemo` — the same mechanism ELITEA-1976 documented).
- The identity must hold `configurations.configuration.create` **there**.

Live-probed all four team projects 2026-08-22 with a real
`POST /configurations/configurations/{p}`:

| project | result |
|---|---|
| 471 "Elitea Testing Team" | **403** `access_denied`, required `configurations.configuration.create` |
| 406 "Bugs & Features" | **403** (same) |
| 25 "Elitea Development" | **403** (same) |
| **400 "UI Testing"** | **200** — credential created (probe deleted afterwards) |

This **corrects `_surface.md`**, which listed 400 as "READ only (same 403
pattern, not individually re-verified)". It is the only writable team project
for this identity today, and it is already wired as
`settings.users_team_project_id` (`config.py:207`, `USERS_TEAM_PROJECT_ID=400`
in `.env.test`) — use that setting, do not hardcode.

**2. The case's precondition toolkit does not exist in project 400 and is
seeded via the API (transit substitution, declared).** Project 400 contains
**zero** toolkits of any type (live-verified). The case's precondition ("a
project exists with an existing toolkit that uses Github credentials") is
therefore built, not found: the test creates a Github credential + a Github
toolkit referencing it via `ToolkitAPI`/`CredentialAPI` and deletes both in
teardown. This is **transit only** — it merely produces the surface that
hosts the dropdown. Every observable the case actually asks about (the
dropdown's CREATE section, the create form, the Save response, the refreshed
saved list, the selection) is produced by the live system through the UI.
`.agents/testing.md` § Fidelity policy, § Fidelity Declaration below.

**3. The Access Token is a placeholder string — case-authorised.** The case's
own Test Data row reads *"Token value | (any valid or placeholder token)"*.
`.env.test`'s `GIT_HUB_TOKEN` is expired (`#1673`), so a *valid* token is not
producible today anyway; the case explicitly permits a placeholder, and
nothing in this case asserts connectivity. No `pytest.skip` gate is needed
(unlike ELITEA-1976, which reused the real token).

**4. Step 12 (project-scope visibility) is asserted through the app's own
scoping mechanism, not a second user session.** `.agents/profile.md` § Roles
& sample users defines exactly one sample identity; `.env.test` carries no
`TEST_USER_B_*` (config.py declares the fields, but they are empty). The
grounded, source-verified proxy — all three produced by the system, all three
live-confirmed:
- the create `POST` lands on `/configurations/configurations/400` and its
  response body carries `project_id == 400`, i.e. **not** the creator's
  `personal_project_id` (399);
- the toolkit dropdown then renders the credential in the **project** bucket:
  its option value encodes `"private":false`, and the *private* variant of the
  same option (`"private":true`) does **not** exist (count 0). `private` is
  `isConfigurationPersonal` (`CredentialsSelect.jsx:249`), i.e. "came from the
  personal project";
- `useOriginalConfigurations` (`src/hooks/useConfigurations.js`) fetches the
  saved list as `GET /configurations/configurations/{selectedProjectId}` —
  a project-membership-scoped endpoint. A row returned for project 400 is by
  construction returned to every member of project 400.

Naming that mechanism is the honest ceiling here; a literal second-member
login is out of reach in this environment and is recorded as a coverage
limit, not asserted.

**5. `shared` is NOT the project-scope discriminator — do not assert it.**
Live-observed: a credential created in team project 400 comes back with
`shared: false`, exactly like a private one. `shared` marks cross-project
sharing, not project scope. The discriminator is `project_id` (+ the
dropdown's `private` encoding). ELITEA-1976 asserts `shared is False` for the
*private* case; copying that assertion here would prove nothing.

## Preconditions
- User authenticated (`auth_state` fixture — no-op on localhost).
- Active project switched to the writable team project
  `settings.users_team_project_id` (**400**, "UI Testing").
- A Github-type toolkit present in that project — **seeded by the test**
  (Classification note 2), together with the Github credential its
  `github_configuration` references.

## Test Data
### generate-per-test (created in test, cleaned up in its own teardown)
- **Seed credential** (transit): Github type, Anonymous auth, Display Name
  `autotest_tk_seed_{ts}`, `data: {"base_url": "https://api.github.com"}` —
  the cheapest honest credential on this surface (`_surface.md`).
- **Seed toolkit** (transit): Github type, `settings.github_configuration =
  {elitea_title: <seed credential>, private: false}`, `repository`
  `EliteaAI/elitea-testing-public`, `active_branch`/`base_branch` `main`,
  `selected_tools: ["get_issues"]`.
- **Credential under test — Display Name**: `autotest_proj_cred_{ts}`
  (29 chars — the form silently truncates at 32, `_surface.md`). The case pins
  the literal `autotest_project_cred`; every sibling AFS in this feature
  timestamps names to avoid cross-run collisions (ELITEA-1962/1965/1974/1976)
  — same convention here.
- **Credential type**: Github · **Auth method**: Token
- **Access Token**: literal placeholder string (Classification note 3). Never
  a real secret.

## Test Steps
1. Switch the active project to the writable team project
   (`settings.users_team_project_id` = 400) via
   `[data-testid="project-selector-trigger"]` →
   `[data-testid="select-option-400"]`.
   - **Verify**: the selector reads the switched project.
2. Seed the precondition credential + Github toolkit in that project via the
   API (transit), then navigate to the toolkit's detail page.
   - **Verify**: toolkit detail page loads — `toolkit-detail-title` visible
     and reading the seeded toolkit's name, `toolkit-detail-configuration-tab`
     attached.
3. Click the "Github Configuration" credential dropdown.
   - **Verify**: the listbox opens — the CREATE-section options are visible.
4. Verify the dropdown shows both sections: a "Create" subheader (renders
   visually "CREATE" via CSS `text-transform`) and a "Saved github
   Credentials" subheader.
   - **Verify**: assert the **underlying** strings (`Create` /
     `Saved github Credentials`) — `to_have_text` reads `textContent` and
     never sees the CSS uppercase (`_surface.md`, cost a rerun on
     ELITEA-1968).
5. Verify the CREATE section offers "New project github credentials"
   (`data-value='{"kind":"create_action","private":false}'`) — present only
   because the active project (400) differs from `personal_project_id` (399).
6. Click "New project github credentials".
   - **Verify**: a new browser tab opens at
     `/400/credentials/create-credential/github?section=credentials` — i.e.
     scoped to the **selected project**, which is the concrete mechanism
     behind "project credential". Github type is pre-selected (the type is in
     the route and the form renders the Github field set).
7. Fill Display Name `autotest_proj_cred_{ts}`, select **Token** auth, fill
   the placeholder Access Token.
   - **Verify**: `input_value()` echoes the typed Display Name; the Token
     radio reads checked; the Display Name still holds its value **after** the
     auth-radio re-render.
8. Click Save.
   - **Verify**: `POST /configurations/configurations/400` → **200**;
     the response body carries a numeric `id`, `elitea_title` /
     `label == <display name>` and `project_id == 400`; the tab then
     navigates to `/credentials/all`.
9. Close the create tab and return focus to the original toolkit tab.
10. Reload the toolkit page, re-open the dropdown, click "Refresh the
    configurations".
    - *Why reload:* the menu does **not** auto-close after a CREATE-action
      click (`#1047`); a fresh load makes the re-open unambiguous instead of
      clicking an obscured trigger. Same idiom as ELITEA-1976 step 10.
11. Verify `autotest_proj_cred_{ts}` appears under "Saved github Credentials"
    as a **project** credential.
    - **Verify**: the option
      `select-option-{"kind":"saved","elitea_title":"<name>","private":false}`
      is visible and displays the name — asserted with a web-first
      `expect(...).to_be_visible()`, **not** a synchronous `is_visible()`
      (the option list re-mounts after the refresh; a synchronous read right
      after returns `False` — observed live 2026-08-22).
    - **Verify (negative)**: the *private* variant of the same option
      (`"private":true`) has count 0 — the credential is not in the personal
      bucket.
12. Select `autotest_proj_cred_{ts}`.
    - **Verify**: the Configuration combobox now displays the credential's
      name — the toolkit's credential field is bound to the new credential.
13. Verify project scope (Classification note 4): the create response's
    `project_id == settings.users_team_project_id` and
    `!= settings.elitea_project_id` (the creator's personal project), and the
    dropdown classified it `private:false` (asserted in step 11).

## Expected Results
- The toolkit's Configuration dropdown renders a CREATE section containing
  "New project github credentials" whenever the active project is not the
  identity's personal project.
- Clicking it opens the credential-create form in a new tab, scoped to the
  **selected project**.
- Saving creates the credential in that project (`POST .../400` → 200,
  `project_id == 400`).
- After "Refresh the configurations", the credential appears in the toolkit's
  Saved-credentials list as a project (`private:false`) entry, and is
  selectable — the combobox then displays it.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: project with an existing Github toolkit | — | step 2 | seeded via API, existence proven by the detail page rendering | asserted *(clarification: no such toolkit exists in the only writable team project — seeded as transit, Classification note 2)* |
| 1 Navigate to Toolkits | list loads | step 2 (direct nav to the toolkit detail route) | — | asserted *(decomposed: the case's list-page hop carries no observable of its own; the detail page load proves the navigation)* |
| 2 Open an existing Github toolkit | detail page loads | step 2 | `toolkit-detail-title` visible + reads the toolkit name | asserted |
| 3 Click the credential dropdown | dropdown opens showing CREATE and Saved sections | steps 3-4 | CREATE option visible; both group headers asserted | asserted |
| 4 Click "New project github credentials" (briefcase) | create form opens, Github pre-selected | steps 5-6 | option `data-value` `"private":false`; new-tab URL `/400/credentials/create-credential/github` | asserted *(icon glyph itself not asserted — the option's encoded value is the semantic identity, same ruling as ELITEA-1976)* |
| 5 Fill Display Name + Token | fields accept the input | step 7 | `input_value()` echoes; Token radio checked | asserted |
| 6 Save the credential | saved successfully | step 8 | POST 200 + `id`/`label` in body + tab navigates to `/credentials/all` | asserted |
| 7 Navigate back to the toolkit | toolkit config page loads | steps 9-10 | tab closed, toolkit page reloaded, title visible | asserted |
| 8 Click the credential dropdown again | dropdown reopens | step 10 | CREATE/refresh controls visible again after the reload | clarification *(the menu never closed — `#1047`; the case's "reopens" wording is stale. Same disposition ELITEA-1976 recorded.)* |
| 9 Click "Refresh the configurations" | list refreshes | step 10 | click + network settle | asserted |
| 10 Verify the credential appears in the saved list | newly created credential visible | step 11 | `expect(option).to_be_visible()` + displayed text | asserted |
| 11 Select the credential | credential is linked to the toolkit | step 12 | combobox display text updates to the credential name | asserted *(scope note: the case does not ask to SAVE the toolkit, and does not; "linked" = the toolkit's credential field is bound to it, same reading as ELITEA-1976 step 13. See Known Defects / findings for the toolkit-form Save observation.)* |
| 12 Verify visible to all project members (project scope) | accessible to all members | steps 11 + 13 | `project_id == 400 != 399`; option encoded `private:false`; private variant count 0 | asserted *(declared improvisation — Classification note 4: no second account exists; asserted through the app's own project-scoping mechanism, not a second login)* |

### Axis 2 — Analyst additions

- **Negative bucket assertion (step 11):** the `"private":true` variant of the
  same saved option has count 0 — *added: presence alone cannot distinguish a
  project credential from a private one with the same name; the pair does. It
  is the cheapest test-enforced form of "this is project-scoped".*
- **Display Name survives the auth-radio re-render (step 7):** inherited from
  ELITEA-1976 — *guards the shared MUI-fill technique, not the product.*
- **Create-tab URL project assertion (step 6):** *added: it is the concrete
  mechanism behind "project credential" and worth guarding independently of
  the terminal scope check, exactly as ELITEA-1976 does for the private path.*
- No console-error side-channel added (same reasoning as ELITEA-1976; the
  flow only transits `/credentials/all`).

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| Precondition Github credential + Github toolkit, created via `CredentialAPI` / `ToolkitAPI` instead of the UI | **Transit** | Produces only the surface that hosts the dropdown. Every case observable — the CREATE option, the create form, the Save response, the refreshed saved list, the selection, the scope — is produced by the live system through the UI. Classification note 2. |
| Access Token value is a placeholder, not a live secret | **Case-authorised** | Case Test Data: *"Token value \| (any valid or placeholder token)"*. Nothing in this case asserts connectivity. |

No terminal substitution. No `page.route`, no `route.fulfill`, no
`page.evaluate`, no monkeypatching.

## Cleanup
1. Delete the credential created through the UI
   (`credential_api.delete_credential(id)` against project 400).
2. Delete the seeded toolkit and the seeded precondition credential.
3. Close the create tab if it is still open.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance |
|---|---|---|
| Project selector trigger | `[data-testid="project-selector-trigger"]` (`ChatPage.switch_project`) | pre-existing, used by the merged ELITEA-1976 spec |
| Project option (dynamic) | `[data-testid="select-option-{project_id}"]` → `select-option-400` | pre-existing |
| Toolkit detail title | `toolkit-detail-title` (`ToolkitDetailPage.toolkit_title`) | on-main ✓ |
| Configuration tab | `toolkit-detail-configuration-tab` (`ToolkitDetailPage.configuration_tab`) | on-main ✓ |
| Configuration dropdown trigger | `toolkit-credential-select-github` (`ToolkitDetailPage.CREDENTIAL_SELECT_TRIGGER`) | added by ELITEA-1976 on `automation/testids` — **re-used as-is, nothing new needed** |
| CREATE option "New project github credentials" | `select-option-{"kind":"create_action","private":false}` (`ToolkitDetailPage.get_create_option(private=False)`) | added by ELITEA-1976 on `automation/testids` |
| Group headers | `select-group-header-Create` / `select-group-header-Saved github Credentials` | pre-existing shared-select mechanism |
| "Refresh the configurations" button | `ToolkitDetailPage.credential_select_refresh_button` | added by ELITEA-1976 on `automation/testids` |
| Saved-credential option (dynamic) | `select-option-{"kind":"saved","elitea_title":"…","private":false}` | pre-existing shared-select mechanism |
| Credential form: Display Name / Token radio / Access Token / Save | `toolkit-field-label-input` · `toolkit-field-auth-radio-token` · `toolkit-field-access_token-input-field` · `credential-form-save-button` | on-main ✓ (`CredentialFormFieldsMixin`, `CredentialCreatePage`) |

**No new testid is required for this case** — the project variant travels on
exactly the handles ELITEA-1976 added for the private variant.

## Network Behavior
- `POST /configurations/configurations/400` — the create-form Save; **200**,
  body carries `id`, `elitea_title`, `label`, `project_id: 400`,
  `shared: false` (see Classification note 5).
- The Refresh button re-fetches the configurations list (project + personal),
  no distinguishing query param — settle on network, not a response predicate.
- `DELETE /configurations/configuration/400/{id}` → 204 (cleanup).
- `POST|DELETE /elitea_core/tools|tool/prompt_lib/400[/{id}]` — seed/teardown
  of the precondition toolkit.

## Known Defects Found During Exploration
- **None for this case's own flow.** All 12 case steps executed live
  end-to-end 2026-08-22 and behaved as the case describes.
- **Observation, deliberately NOT asserted and NOT filed as a bug:** on the
  seeded toolkit's detail page in project 400 the toolkit-form **Save button
  stayed disabled** — on fresh load, after selecting a credential in the
  Configuration dropdown, and even after editing the Description. In an
  earlier probe where it *was* enabled, clicking it left the toolkit's
  persisted `github_configuration` unchanged (still the seed credential).
  The API accepts a `PUT` on that toolkit (400 validation error, **not** 403),
  so it is not a plain permission wall. **Out of scope**: ELITEA-1977 never
  asks to save the toolkit — its step 11 expects the credential to be *linked*
  (selected), which is what ELITEA-1976 also asserts. Reported as a `note`
  finding for the lead; worth its own case/investigation rather than a
  speculative bug filing (interaction-discovery ladder not exhausted).

## Blocked Steps
None.

## Automation Hints
- **Project**: `settings.users_team_project_id` (400). Do **not** use 471 —
  writes 403 there (Classification note 1).
- Reuse `ToolkitDetailPage`'s ELITEA-1976 dropdown API wholesale:
  `open_credential_dropdown` / `get_create_option(private=False)` /
  `click_create_option(private=False)` / `click_refresh_configurations` /
  `get_saved_option(..., private=False)` / `select_saved_credential` /
  `get_credential_select_text`.
- `ToolkitAPI` / `CredentialAPI` must be instantiated with
  `project_id=settings.users_team_project_id` — the default is the personal
  project and the seed/teardown would land in the wrong place.
- Keep the generated Display Name **under 32 chars** (silent truncation,
  `_surface.md`).
- Use `expect(...)`, never `is_visible()`, on the saved option right after the
  refresh click (step 11 note).
- Whole flow measured ~57 s headless.
