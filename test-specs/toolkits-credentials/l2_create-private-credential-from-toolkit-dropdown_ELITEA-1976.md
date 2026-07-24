# Test Case: Credential — Create Private Credential from Toolkit Flow

## Metadata
- **TMS ID**: ELITEA-1976
- **Linked Story**: none
- **Priority**: l2 (source case frontmatter: `high` — consistent with ELITEA-1877/1892/1893/1897/1901, all `priority: high` → `l2_*` filenames)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`)
- **User set**: `${TEST_USER}` (nominal — localhost's `auth_state` fixture skips interactive login via `VITE_DEV_TOKEN`; the same identity backs both the browser session and the API clients used below — internally "Test Bot", author_id `659`)
- **Analyst**: qa-engineer (agent), 2026-07-24 (redispatch pass 2 — see Classification note #3)
- **Status**: ready-for-automation

## Classification note — THREE declared improvisations (role-overrides.md § Declared-improvisation protocol)

**1. Vehicle substitution: GitHub → GitLab.** The case's precondition and steps
name a "Github-based toolkit" throughout. Live exploration confirmed GitHub
toolkit creation is blocked outright in this DEV deployment (`POST
.../elitea_core/tools/prompt_lib/{project}` with `type=github` → `403
{"error": "Toolkit type 'github' is not available in this deployment"}`), and
the 3 pre-existing GitHub toolkits in the team project are permanently locked
to a read-only Raw-JSON view with no Configuration section at all. **Already
filed as EliteaAI/elitea-testing-public#999** (MAJOR, filed by an earlier pass
on this same case, 2026-07-23) — that issue's own "Suggested next step"
recommends substituting a still-supported "Code Repositories" toolkit type.
No sanctioned canon pattern covers "the named vehicle is blocked by an open,
deterministic, filed defect that prevents even opening the Configuration UI" —
this is broader than the "Analysis-time entry" exception (`testing.md`), which
covers one isolable tail assertion, not an entire vehicle. **Chose GitLab**
because: (a) reading `ToolBaseProperty.jsx` / `CredentialsSelect.jsx` in
`EliteaUI/src` confirms the credential-dropdown mechanic under test
(`type === 'configuration'` → `<CredentialsSelect>`) is 100% generic across
every credential/toolkit type — nothing GitHub-specific in the implementation;
(b) GitLab is live-confirmed creatable + Form-editable in this deployment
(toolkit id 118 "EPAMGitlab", project 471). The case's "Github" wording is
therefore treated as the generic-example vehicle the original author picked,
not a GitHub-specific requirement. Recommend re-adding GitHub as a second
parameterized vehicle once #999 resolves.

**2. Step 13 "linked to the toolkit" verified via form-state, not toolkit
Save-persistence.** Live exploration discovered the acting identity ("Test
Bot") holds only a **viewer-level role** in every non-personal project
(confirmed via two separate live 403s — `configurations.configuration.create`
and `models.applications.tools.create` both missing in project 471's
`current_permissions`, full list captured live). This means: (a) Test Bot
cannot create its own scratch toolkit in a multi-member project — the
existing toolkit (id 118) must be reused read-only; (b) clicking the toolkit's
own **Save** button after selecting the new credential is blocked anyway by
the pre-existing "Authentication failed" gate on the SEED credential itself
(a product behavior already confirmed correct by
`test_toolkit_credential_indicators_e2e` — "Save button disabled when
credentials are invalid" — every credential currently seeded in project 471
is a placeholder/invalid token, so this isn't specific to my change). No
canon pattern covers "the shared vehicle can't be safely Saved by this
identity." Chose to assert the case's literal claim — "credential is linked
to the toolkit" — via the **Configuration field's displayed value updating to
the new credential** (a real, observed, React-state change caused by a real
click), and to explicitly **not** click the toolkit's own Save button in the
final test (discard/navigate away instead) so a shared, other-owned toolkit
is never mutated. This is the more conservative and non-destructive design,
and the case's expected result for this step doesn't require server-side
persistence, only that selecting the credential visibly links it.

**3. Step 11 rewritten — the Configuration dropdown never closes after a
CREATE-action click; it must NOT be re-clicked (redispatch finding,
2026-07-24; filed EliteaAI/elitea-testing-public#1047).** The ORIGINAL pass
through this AFS (and the source TMS case's own step 10, "Click the
credential dropdown again ... Dropdown reopens") assumed the Select's
dropdown auto-closes when Step 6's "New private gitlab credentials" click
opens the new tab, and needs to be re-clicked afterward to "reopen" it.
**Live-disproven** by direct CDP DOM inspection across BOTH browser tabs
simultaneously (isolated `browser-verify` instance, port 9333 — shared
Playwright MCP lane 0 was contended at redispatch time): on the ORIGINAL
tab, the Select's Menu/Popover (`.MuiPopover-root`) never closes at all —
`document.elementFromPoint()` at the trigger's own coordinates resolves to
`.MuiPopover-paper`, not the trigger, confirming the menu is still rendered
on top of it. Root cause, read + confirmed:
`src/[fsd]/shared/ui/select/SingleSelect.jsx`'s `handleChange` sets
`skipNextCloseRef.current = true` before calling any `variant: 'action'`
option's `onActivate()` (~line 172-174), which makes the immediately-
following MUI-driven `handleMenuClose` a no-op (~line 211-215) —
`setMenuOpen(false)` is never reached for action-variant picks. **This is a
deliberate, shared mechanism, not a bug**: the identical `variant: 'action'`
pattern powers in-place "Refresh" actions in `src/components/ToolkitSelect.jsx`
and `src/components/LlmModelSelect.jsx`, where staying open is clearly the
intended UX (the refreshed list is visible without reopening the menu).
`CredentialsSelect.jsx`'s "Create" options reuse the identical mechanism, so
the "stay open" behavior applies even though this particular action
navigates to a new tab instead of refreshing in place. Practical
consequence for automation: re-clicking the Configuration select trigger (as
the case text's step 10 literally describes, and as the first implementer
pass's `open_configuration_dropdown()` call literally did) does **not**
reopen anything — it targets an element now covered by the still-open
menu's own Paper, and in Playwright this produces a genuine `TimeoutError`
(element obscured / not actionable), exactly what the first implementer
pass hit at this step (board history, 2026-07-24T01:29:58Z — reported
`blocked`, correctly declining to guess between test-technique-gap and
product-defect). Live-confirmed the corrected flow works end-to-end
instead: the Refresh button and the (stale, pre-refresh) Saved-credentials
list remain visible and clickable in the SAME still-open menu throughout —
Steps 10-14 below assert against that same open menu directly, with NO
reopen click. Filed as a case-text clarification, not a product defect
(reverse-masking guard, `.agents/testing.md`):
**EliteaAI/elitea-testing-public#1047.**

## Preconditions
- User authenticated — `auth_state` fixture (no-op on localhost, `VITE_DEV_TOKEN`).
- Active project switched to **"Elitea Testing Team"** (id `471`) — a genuine
  multi-member team project, required so BOTH `CredentialsSelect` CREATE
  options render (`Create_Project_Title` only pushes when
  `selectedProjectId != personal_project_id` — confirmed by reading
  `CredentialsSelect.jsx`) and so "private = not visible to other members" is
  a meaningful claim (the "Private" project, id `399`, IS the acting user's own
  `personal_project_id` — single-user by definition, privacy has no content
  there). Project switch: navigate to `http://localhost:5173/471/toolkits/all`
  (URL-prefixed project-id nav — confirmed live to switch
  `localStorage['elitea_ui.project.id']`) or via the project-selector UI.
- At least one existing **GitLab-type** toolkit already present in project 471
  — look it up dynamically (`toolkit_api.list_toolkits()` filtered
  `type == 'gitlab'`, project_id=471), do **NOT** hardcode toolkit id `118`
  ("EPAMGitlab") even though that's what this analysis used — a hardcoded id
  is fragile if that specific toolkit is ever deleted/renamed by its real
  owner (a different team member, author_id `829`, not the test identity).

## Test Data
### reuse-existing
- The team project's pre-existing GitLab toolkit (dynamically looked up, see
  Preconditions) — **read-only interaction only**: open it, work its
  Configuration dropdown, never click its own Save button (see Classification
  note #2).

### generate-per-test (created in test, cleaned up in its own teardown)
- **Display Name / ID**: `autotest_private_cred` — the case pins this as a
  literal string (not templated with a timestamp), same collision-risk
  callout as ELITEA-1962's AFS: if a prior run's teardown failed, this name
  may already exist under the tester's personal project. Recommend checking
  via `credential_api.list_all_credentials()` and deleting any stale match in
  test setup, exactly as this analysis session had to do (found and cleaned
  up 5 stale credentials from an earlier interrupted pass before starting).
- **Credential type**: GitLab (declared improvisation #1 above)
- **Auth method**: GitLab private token (the type's only auth option — no
  radio-group choice needed, unlike GitHub's Anonymous/Token choice)
- **Url**: `https://gitlab.com`
- **Private Token**: a placeholder string is sufficient — this case's
  assertions never require the credential to actually authenticate (no
  `GITLAB_TOKEN`/`GITLAB_URL` env var is needed; do not add one solely for
  this case). Never print the literal placeholder used in this exploration
  session's transcript verbatim into any tracker artifact — same discipline
  as ELITEA-1962.

## Test Steps

1. **[Precondition]** Look up an existing `type == 'gitlab'` toolkit in
   project 471 via `toolkit_api.list_toolkits()`.
   - **Verify**: at least one match returned (id `118` "EPAMGitlab" at
     analysis time — `author_id 829`, NOT the test identity).
2. Switch active project to "Elitea Testing Team" (471) and navigate to
   `/toolkits/all`.
   - **Verify**: Toolkits list page loads; at least one `entity-card` visible
     (the GitLab toolkit from step 1).
3. Open the GitLab toolkit (`/toolkits/all/{id}`).
   - **Verify**: `toolkit-detail-title` visible and matches the toolkit's
     name; Configuration section renders a "Gitlab Configuration *" field
     with some already-selected credential (whatever the toolkit's current
     config is — do not assume a specific value, it's owned by another user).
4. Click the Gitlab Configuration select field (`toolkit-field-gitlab_configuration-select` — **testid needed**, see Concrete Handles).
   - **Verify**: dropdown opens; a "CREATE" section header and a "Saved
     gitlab Credentials" section header (rendered as `SAVED GITLAB
     CREDENTIALS` via CSS `text-transform: uppercase` — actual textContent is
     mixed-case `Saved gitlab Credentials`) are both visible.
5. Verify the CREATE section's two options.
   - **Verify**: "New private gitlab credentials" (person icon,
     `toolkit-field-gitlab_configuration-select-create-private` — **testid
     needed**) and "New project gitlab credentials" (briefcase icon,
     `toolkit-field-gitlab_configuration-select-create-project` — **testid
     needed**) are both visible. (Confirms declared-improvisation #2's
     precondition — this pair only renders because the active project ≠ the
     acting user's personal project.)
6. Click "New private gitlab credentials".
   - **Verify**: a **new browser tab** opens (real `window.open(..., '_blank',
     ...)` — live-confirmed) at
     `/credentials/create-credential/gitlab?section=credentials`, and the
     **project context in that new tab is the acting user's PERSONAL project**
     (live-confirmed: page title read `"Credentials - project_user_659"`,
     sidebar showed "Project: Private" — this IS the privacy mechanism: a
     private credential is physically created under the creator's own
     personal project, never under the team project the toolkit lives in).
     "New GitLab Credential" form renders with GitLab private-token auth
     pre-selected (no radio choice needed).
7. In the new tab, fill Display Name = `autotest_private_cred`
   (`toolkit-field-label-input`).
   - **Verify**: ID field (`toolkit-field-elitea_title-input`, disabled)
     live-mirrors to `autotest_private_cred` (ELITEA-1972 pattern).
8. Fill Url = `https://gitlab.com` (`toolkit-field-url-input`) and Private
   Token = a placeholder string (`toolkit-field-private_token-input-field`;
   note the outer secret-toggle wrapper carries the sibling testid
   `toolkit-field-private_token-input` — the actual `<input>` is the
   `-input-field` suffixed one, confirmed by `get-value` returning the typed
   string only on that element).
   - **Verify**: Save button (`credential-form-save-button`) becomes enabled.
9. Click Save.
   - **Verify**: `POST /api/v2/configurations/configurations/{personal_project_id}`
     → 200/201; response body `label == elitea_title ==
     "autotest_private_cred"`, `type == "gitlab"`, `shared == false`,
     `project_id == ${personal_project_id}` (NOT the team project's id).
     Page redirects to `/credentials/all` (still in the personal-project
     context).
10. Close the new tab; return to the original toolkit tab.
    - **Verify**: the original toolkit detail page is unaffected (still
      shows its pre-existing Configuration value from step 3).
11. **[CORRECTED 2026-07-24 — see Classification note #3, EliteaAI/elitea-testing-public#1047. Do NOT click the Configuration select again — it was never closed.]**
    Verify the dropdown is STILL open from step 4/6 (the "Saved gitlab
    Credentials" list shown is still the pre-refresh set).
    - **Verify**: the Select's `.MuiPopover-root` for this field is still
      present/visible (no click needed to reach this state — clicking a
      CREATE-action option never calls `setMenuOpen(false)`, a deliberate,
      shared `SingleSelect.jsx` mechanism, not a defect); "Saved gitlab
      Credentials" section still shows the pre-refresh list (does NOT yet
      include the new credential — confirms the list is not auto-live).
12. Click the Refresh button next to "Saved gitlab Credentials"
    (`toolkit-field-gitlab_configuration-select-refresh-button` — **testid
    needed**; only existing handle today is `aria-label="Refresh the
    configurations"`, not testid-compliant).
    - **Verify**: list refreshes (a `GET` to the configurations-list endpoint
      fires).
13. Verify `autotest_private_cred` now appears in the Saved list, with a
    person icon (private indicator).
    - **Verify**: locate via
      `[data-testid='select-option-{"kind":"saved","elitea_title":"autotest_private_cred","private":true}']`
      — **this exact fallback testid already exists on `main`, no code
      change needed** (see Concrete Handles). Element visible.
14. Click `autotest_private_cred` in the list to select it.
    - **Verify**: the Gitlab Configuration field's **displayed value**
      updates to `autotest_private_cred` with the person icon — this is the
      case's "credential is linked to the toolkit" claim, satisfied via
      React form-state (see Classification note #2 for why the toolkit's own
      Save is intentionally NOT clicked).
15. Verify private-scope isolation (case step 14) via API, single-account
    proof (no second team-member account exists in this project's test-data
    set — see Automation Hints):
    - **Verify A**: `GET` credentials scoped to the **team project (471)**
      does **NOT** include `autotest_private_cred` (0 matches) — live-confirmed.
    - **Verify B**: `GET` credentials scoped to the **personal project**
      DOES include it, with `shared == false` and `project_id ==
      ${personal_project_id}` (≠ 471) — live-confirmed (id `1919` at analysis
      time, since deleted in teardown).
16. **[Cleanup, not a case step]** Discard the toolkit form's unsaved
    selection (click Discard, or simply navigate away) — never Save a
    shared, other-owned toolkit. Delete `autotest_private_cred` via
    `credential_api.delete_credential()` scoped to the personal project.

## Expected Results
- `autotest_private_cred` is created (200/201 from the create POST) under the
  creator's own personal project, `shared: false`.
- It appears in the toolkit's Saved-credentials dropdown only after an
  explicit Refresh (not live/auto-updating).
- Selecting it updates the toolkit Configuration field's displayed value.
- It is absent from the team project's own credential list (structurally
  private — the mechanism, not just a UI hide) and present only under the
  creator's personal project.
- No new console errors at any step (verified live — only pre-existing
  `sio connected` / `Google analytics init: false` / ASCII-art version-banner
  debug logs observed, no errors).
- The pre-existing, other-owned toolkit's own Configuration is left
  **unmodified** server-side (verified live via `GET
  /elitea_core/tool/prompt_lib/471/118` before and after — unchanged).

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| precond: user logged in | — | — | `auth_state` fixture (no-op on localhost) | asserted |
| precond: project + existing Github toolkit | Credentials/Toolkits sections accessible | AFS steps 1–3 | step 3: toolkit detail loads | asserted *(vehicle substituted to GitLab — Classification note #1, linked EliteaAI/elitea-testing-public#999)* |
| 1 Navigate to Toolkits section | list page loads | AFS step 2 | step 2: `entity-card` visible | asserted |
| 2 Open existing Github toolkit | detail page loads | AFS step 3 | step 3: `toolkit-detail-title` visible | asserted *(GitLab vehicle)* |
| 3 Click credential dropdown | dropdown opens w/ CREATE + Saved sections | AFS step 4 | step 4: both section headers visible | asserted |
| 4 Verify two sections visible | both visible | AFS step 4 | step 4 | asserted |
| 5 Verify CREATE has two options w/ icons | both present | AFS step 5 | step 5: both options + icons visible | asserted |
| 6 Click "New private ... credentials" | creation form opens, type pre-selected | AFS step 6 | step 6: new tab + form render | asserted |
| 7 Fill Display Name + Token | fields accept input | AFS steps 7–8 | steps 7–8: field values + ID mirror + Save-enabled | asserted |
| 8 Save the credential | saved successfully | AFS step 9 | step 9: POST 200/201 + response body | asserted |
| 9 Navigate back to toolkit | config page loads | AFS step 10 | step 10: toolkit unaffected | asserted |
| 10 Click credential dropdown again | dropdown reopens | AFS step 11 | step 11: dropdown was never closed, pre-refresh list shown | asserted *(NOT reopened — the dropdown never closes after a CREATE-action click; case-text drift, Classification note #3, EliteaAI/elitea-testing-public#1047)* |
| 11 Click Refresh button | list refreshes | AFS step 12 | step 12: refresh action fires | asserted |
| 12 Verify new credential appears | visible in list | AFS step 13 | step 13: `select-option-{...}` testid visible | asserted |
| 13 Select the credential | linked to toolkit | AFS step 14 | step 14: field displayed-value updates | asserted *(via form-state, not Save-persistence — Classification note #2)* |
| 14 Verify private scope (not visible to other members) | not visible to others | AFS step 15 | step 15 A+B: project-scoped API list diff | asserted *(single-account API proxy, not a second human account — Automation Hints)* |
| Expected Final State: created, linked, private-scoped | all three true | AFS steps 9, 14, 15 | see above | asserted |

**Axis 2 — Analyst additions**

- AFS step 9 asserts the create POST's full response body (`label`,
  `elitea_title`, `type`, `shared`, `project_id`) beyond the case's bare
  "saved successfully" — *added: matches ELITEA-1962/1972 precedent rigor,
  and `project_id` specifically is the load-bearing field for step 14's
  privacy claim.*
- AFS step 10 asserts the ORIGINAL toolkit's Configuration is unaffected
  after opening/closing the credential-create tab — *added: guards against a
  regression where the create-tab's navigation could bleed into the
  originating tab's state.*
- AFS step 16 asserts (via a before/after API diff, not a UI step) that the
  shared toolkit's own settings are unchanged after this test run — *added:
  direct consequence of Classification note #2's discovery that Save is
  blocked for this identity; guards that a future code change doesn't
  silently start persisting an unintended mutation to another user's asset.*
- Console-message check at every step — *added: standard side-channel
  discipline; confirmed clean throughout (see Expected Results).*

## Cleanup
1. `credential_api.delete_credential(<id>)` scoped to the **personal**
   project — deletes `autotest_private_cred`.
2. Discard (do not Save) any pending edit on the reused team-project
   toolkit.

## Concrete Handles (discovered during exploration)

Provenance verified via fresh `git fetch origin` in `../EliteaUI` at analysis
time (2026-07-24) — `on-main` / `on automation/testids only (awaiting human
promotion to main)` / `needs-adding`.

**Implementer Phase 2 amendment (2026-07-24):** the table below did not
originally cover a handle for AFS step 4's own assertion ("a 'CREATE' section
header and a 'Saved gitlab Credentials' section header ... are both visible")
— a genuine testid gap the analyst's table missed, not a scope change. Added
`toolkit-field-{k}-select-group-header` (row below), wired generically off the
combobox's existing `testId` prop in `SingleSelect.jsx`'s
`buildGroupedMenuBody()` (`EliteaAI/EliteaUI@d3953bb8` on `automation/testids`).
Both group headers share the same testid; the CREATE group renders first
(`Object.entries(menuData)` insertion order — "Create" is always pushed before
"Saved ... Credentials" in `CredentialsSelect.jsx`'s `menuData` `useMemo`), so
`.nth(0)`/`.nth(1)` disambiguate deterministically.

**Implementer redispatch-pass amendment (2026-07-24):** the three rows below
previously marked **needs-adding** (Gitlab Configuration select combobox,
CREATE-section private/project options, Refresh button) were **already
added mid-pass by the FIRST implementer dispatch**
(`EliteaAI/EliteaUI@1fef03f5` on `automation/testids`) — confirmed live via
fresh `git fetch origin` + `git grep` against BOTH `origin/main` (0 hits —
correctly not yet promoted) and `origin/automation/testids` (all present) at
this redispatch pass. No new EliteaUI work was needed. Only the group-header
row (added the pass before this one, `EliteaAI/EliteaUI@d3953bb8`) was
genuinely new at that time; both commits are pre-existing as of this pass.

| Element | Locator | Provenance |
|---|---|---|
| Toolkits list card | `LocatorDescriptor(testid="entity-card")` | on-main ✓ |
| Toolkit detail title | `LocatorDescriptor(testid="toolkit-detail-title")` | on `automation/testids` only |
| Configuration select's group headers ("CREATE" / "Saved gitlab Credentials") | `[data-testid="toolkit-field-gitlab_configuration-select-group-header"]` (both headers share this testid; disambiguate by `.nth(0)`/`.nth(1)` — CREATE renders first) | on `automation/testids` — `EliteaAI/EliteaUI@d3953bb8` |
| Gitlab Configuration select (the combobox itself) | `LocatorDescriptor(testid="toolkit-field-gitlab_configuration-select")` | on `automation/testids` — `EliteaAI/EliteaUI@1fef03f5` (`ToolBaseProperty.jsx` passes `testId={`toolkit-field-${k}-select`}` to `<CredentialsSelect>`, threaded to `<Select.SingleSelect data-testid={testId} ...>`) |
| "New private gitlab credentials" CREATE option | `[data-testid="toolkit-field-gitlab_configuration-select-create-private"]` (class constant, dynamic per configuration-field `k`) | on `automation/testids` — `EliteaAI/EliteaUI@1fef03f5` |
| "New project gitlab credentials" CREATE option | `[data-testid="toolkit-field-gitlab_configuration-select-create-project"]` | on `automation/testids` — `EliteaAI/EliteaUI@1fef03f5` |
| Saved-credential row (e.g. `autotest_private_cred`) | `[data-testid='select-option-{"kind":"saved","elitea_title":"autotest_private_cred","private":true}']` — dynamic, compute via `JSON.stringify({kind:"saved", elitea_title:<title>, private:<bool>})` prefixed `select-option-` | **on-main ✓** — `SingleSelectMenuItem.jsx`'s existing `data-testid={option.testId ?? `select-option-${option.value}`}` fallback already produces this; confirmed live in DOM, zero code change needed. Escape the embedded quotes/braces as a literal attribute-value string in Playwright: `page.locator(f'[data-testid=\'select-option-{{"kind":"saved","elitea_title":"{name}","private":{str(is_private).lower()}}}\']')`. |
| Refresh button ("Saved gitlab Credentials" header) | `[data-testid="toolkit-field-gitlab_configuration-select-refresh-button"]` | on `automation/testids` — `EliteaAI/EliteaUI@1fef03f5` |
| Credential create form: Display Name | `LocatorDescriptor(testid="toolkit-field-label-input")` (existing `CredentialFormFieldsMixin.display_name_input`) | on `automation/testids` only |
| Credential create form: ID (auto-mirror) | `LocatorDescriptor(testid="toolkit-field-elitea_title-input")` (existing `CredentialFormFieldsMixin.id_input`) | on `automation/testids` only |
| Credential create form: Url | `LocatorDescriptor(testid="toolkit-field-url-input")` — new field on `credential_create_page.py`, same class-constant pattern as existing `base_url_input`/`api_key_input`; no EliteaUI JSX change needed (generic `ToolBaseProperty.jsx` string-field renderer) | on `automation/testids` only |
| Credential create form: Private Token (secret input) | `LocatorDescriptor(testid="toolkit-field-private_token-input-field")` — new field, same pattern as existing `access_token_input`; no EliteaUI JSX change needed | on `automation/testids` only |
| Credential create form: Save button | `LocatorDescriptor(testid="credential-form-save-button")` (existing `CredentialFormFieldsMixin.save_button`) | on `automation/testids` only |
| Toolkit's own Save/Discard buttons | `LocatorDescriptor(testid="toolkit-detail-save-button")` / `toolkit-detail-discard-button` (existing `ToolkitDetailPage`) | on `automation/testids` only |

## Network Behavior
- `POST /api/v2/configurations/configurations/{personal_project_id}` — fires
  on credential-create Save; 200/201 on success; response body carries
  `project_id`, the load-bearing privacy field.
- `GET /api/v2/configurations/configurations/{project_id}` (or equivalent
  list-configurations call triggered by the Refresh button / dropdown open)
  — refetches the Saved-credentials list; wait for this before asserting the
  new credential's row is present (do not assume the list live-updates
  without the explicit Refresh click — live-confirmed it does NOT).
- `GET /api/v2/elitea_core/toolkit_validator/prompt_lib/{project}/{toolkit_id}`
  — fires on every toolkit-detail-page load (RTK-Query `validateToolkit`,
  `EliteaUI/src/api/toolkits.js`) to check the toolkit's CURRENTLY-linked
  credential; returns **400** for the reused team-project GitLab toolkit
  (id 118) because that credential is a pre-existing placeholder/invalid
  token (Classification note #2) — the SAME intended validation-failure
  behavior already confirmed correct by `test_toolkit_credential_indicators_e2e`
  (Enhancement #5114's credential-status-indicator feature). Implementer
  finding (redispatch pass): this fires regardless of this case's own
  actions and is filtered as known noise in the automated test's
  side-channel console-error check — see
  `_is_known_reused_toolkit_invalid_credential_400()` in the test file.

## Known Defects Found During Exploration
- **[MAJOR] EliteaAI/elitea-testing-public#999** — GitHub toolkit type
  unavailable for creation (403 `"Toolkit type 'github' is not available in
  this deployment"`); existing GitHub toolkits permanently locked to
  read-only Raw-JSON view, Configuration section entirely absent from the
  DOM. Already filed (by an earlier pass on this same case); this AFS's
  vehicle substitution to GitLab is the filed issue's own recommended
  workaround. No new ticket needed.

One CASE-TEXT-DRIFT clarification was filed (reverse-masking guard — live
product is correct/deliberate, case wording is stale), NOT blocking
automation:
- **`EliteaAI/elitea-testing-public#1047`** — the case's step 10 ("Click the
  credential dropdown again") and this AFS's own prior-pass step 11
  annotation both assumed the Configuration dropdown closes when Step 6's
  CREATE-option click opens the new tab. Live-confirmed (via CDP DOM
  inspection on both tabs) it never closes — a deliberate, shared
  `SingleSelect.jsx` mechanism (`skipNextCloseRef`) also used for in-place
  "Refresh" actions elsewhere in the app. See Classification note #3.

## Blocked Steps
None — every case element has a disposition (see Coverage Map). The two
environment constraints discovered (GitHub toolkit type blocked; acting
identity is viewer-only in non-personal projects) are handled via declared
improvisations, not left as blockers.

## Automation Hints
- Framework: Playwright + pytest, page objects under `automation/pages/`
  (confirmed from `.agents/testing.md`).
- New page-object surface needed: extend `CredentialCreatePage` with
  `url_input` / `private_token_input` `LocatorDescriptor` fields (GitLab
  type's fields — currently only Jira/GitHub fields exist on that class);
  extend `ToolkitDetailPage` (or a new small mixin) with the Configuration
  select's methods: `open_configuration_dropdown()`,
  `click_create_private_credential()`, `click_create_project_credential()`,
  `click_configuration_refresh()`, `select_saved_credential(elitea_title,
  private)` (building the JSON-shaped locator per the Concrete Handles
  table).
- **`open_configuration_dropdown()` is called EXACTLY ONCE per test run — at
  Step 4, never again at Step 11** (Classification note #3,
  EliteaAI/elitea-testing-public#1047). The dropdown never actually closes
  after Step 6's CREATE-action click, so re-invoking
  `open_configuration_dropdown()` after returning from the new tab targets
  an element now covered by the still-open menu's own `.MuiPopover-paper`
  and times out in Playwright exactly the way the first implementer pass
  observed (`TimeoutError` at `toolkit_page.open_configuration_dropdown`,
  board history 2026-07-24T01:29:58Z). Step 11 needs a NEW, non-clicking
  page-object method instead — e.g. `configuration_group_headers(field_key)`
  / `saved_credential_option(...)` presence checks directly against the
  already-open menu (no `.click()` on the trigger). Steps 12-14 (Refresh,
  select) then proceed exactly as already written — both are live-confirmed
  clickable in the same still-open menu with zero changes needed.
- **New-tab handling**: step 6's click opens a real new browser tab/page
  (Playwright: use `context.expect_page()` around the click, matching the
  existing pattern in `test_toolkit_indicators_for_credentials.py`'s
  "Open in new tab" step).
- **No `GITLAB_TOKEN` test-data var needed** — this case's assertions never
  require the credential to actually authenticate; a placeholder string
  satisfies every verification. Do not add one solely for this case.
- **Never click the reused toolkit's own Save button** — it belongs to a
  different real team member (author_id `829` at analysis time); this
  identity's role in team projects is viewer-only for
  create/update-configuration and create-toolkit actions anyway (confirmed
  live via two 403s), so Save would likely fail server-side regardless, but
  more importantly it would be reckless to attempt against a real shared
  asset even if it happened to succeed.
- **Team-project viewer-role finding is broader than this case** — worth
  recording for any future case needing genuine multi-member semantics (this
  is the first case in the suite to touch a non-personal project's
  create/update surface at all; every prior credential/toolkit test creates
  its own scratch data in the default "Private" project). Logged to
  `qa-engineer` memory + this feature's new `_surface.md` digest.
- Dynamic testid derivation for the CREATE-section options and the
  Configuration select itself all key off the schema field name `k` (e.g.
  `gitlab_configuration` for this toolkit type, `github_configuration` for
  GitHub, `jira_configuration` for Jira, etc.) — the naming
  `toolkit-field-${k}-select(-create-private|-create-project|-refresh-button)`
  is generic across every credential-bearing toolkit type through the one
  `ToolBaseProperty.jsx` call site edit; no per-type special-casing needed.
- **Implementer redispatch-pass finding (2026-07-24):** the reused
  team-project GitLab toolkit's (id 118) OWN currently-linked credential is
  itself invalid (a pre-existing placeholder), which fires a `400` from the
  `validateToolkit`/`toolkit_validator` endpoint on every load of its detail
  page — see § Network Behavior. This is filtered as known, already-
  established-correct noise in the test (analogous to the two other
  known-noise filters already needed for this same reused toolkit/project),
  not a new defect.
