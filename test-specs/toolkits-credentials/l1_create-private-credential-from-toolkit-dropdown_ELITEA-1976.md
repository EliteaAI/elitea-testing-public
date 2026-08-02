# Test Case: Credential — Create Private Credential from Toolkit Flow

## Metadata
- **TMS ID**: ELITEA-1976
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `high` — consistent with the merged
  `l1_credential-pin-unpin_ELITEA-1974.md`, whose frontmatter is also `high`
  and which shipped as `@pytest.mark.p1`; NOT `l2` — a prior, now-orphaned/
  unmerged local attempt at this same case used `l2` reasoning that
  contradicts the actually-merged convention, see notes below)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`)
- **User set**: `${TEST_USER}` (nominal — localhost's `auth_state` fixture is
  a no-op via `VITE_DEV_TOKEN`; the same identity, "Test Bot"/`author_id 659`,
  backs both the browser session and the Bearer-token API clients used below)
- **Analyst**: qa-engineer (agent), 2026-08-02
- **Status**: ready-for-automation

## Classification notes — declared improvisations (role-overrides.md § Declared-improvisation protocol)

**1. GitHub is used AS-IS — no vehicle substitution needed.** A prior,
never-merged local session (dangling commits, see `_surface.md`) recorded
GitHub toolkit creation as blocked with a 403 ("Toolkit type 'github' is not
available in this deployment", filed `elitea-testing-public#999`, still
OPEN) and substituted GitLab. **Live-reverified 2026-08-02: this no longer
reproduces.** `POST /elitea_core/tools/prompt_lib/399 {"type":"github",...}`
returned 200 and created toolkit id 2154 with a fully-rendered Form view
(Configuration tab, tool chips, credential dropdown — nothing locked to Raw
JSON). The 3 pre-existing GitHub toolkits in project 471 (117/150/151) also
render full Form view today. Using GitHub per the case's literal wording;
`#999` is flagged in the run's findings for a human to re-verify + close,
not acted on further here (closure is human-only).

**2. Step 5's "both CREATE options visible" requires a TEAM project, not
Test Bot's personal project.** Read `CredentialsSelect.jsx`: the "New
project {type} credentials" option only renders when
`selectedProjectId != personal_project_id`. Test Bot's own project (399,
"Private") **is** its `personal_project_id` — opening a toolkit there shows
**only** "New private github credentials"; the project option is absent
from the DOM entirely (not disabled — absent). Live-confirmed switching to
project 471 ("Elitea Testing Team", a genuine multi-member team project)
renders **both** options together. The test therefore opens an existing
GitHub toolkit in a team project for the Step 3-5 dropdown-shape assertion,
then performs the actual "New private..." create flow (steps 6-13), which —
per the same source read — always creates under `personal_project_id`
regardless of which project is currently selected (`createSelectHandler`:
`const projectId = option.private ? personal_project_id : selectedProjectId`).
So the created credential always lands in project 399, even though the
toolkit itself lives in project 471.

**3. Test Bot has only a viewer-level role in every team project** (live
403 on `configurations.configuration.create` when attempting to write to
project 471 as Test Bot). The team-project toolkit used for the dropdown-
shape check (steps 1-5, 9-13) is therefore an **existing, dynamically
looked-up** toolkit — opened read-view-only, its own Save button is never
clicked, so a shared, other-owned toolkit is never mutated server-side.
Steps 6-8 (create the private credential) run against the create-credential
form directly, which Test Bot CAN write to (its own project 399).

**4. Step 14 (private-scope visibility) is asserted via the API response
shape, not a second user session.** `.agents/profile.md` § Roles & sample
users defines only one sample identity (`${TEST_USER}`) — there is no second
account to log in as and observe invisibility firsthand. Live-confirmed via
`GET .../configurations/configuration/399/{id}` that a credential created
through "New private ... credentials" has `project_id == 399`
(== Test Bot's own `personal_project_id`) and `shared: false`. Per
`CredentialsSelect.jsx`'s own visibility logic (`isConfigurationPersonal =
configuration.project_id === personal_project_id`, and the API scopes
`/configurations/configurations/{project_id}` requests to project
membership), a credential whose `project_id` equals ONE user's personal
project is architecturally unreachable to any other identity — no other
user's `GET .../configurations/configurations/{their_project_id}` call can
ever return it. Asserting `project_id == 399 && shared == false` on the
create response is the grounded, source-verified proxy for "private to its
creator" available in this environment.

## Preconditions
- User authenticated (`auth_state` fixture — no-op on localhost).
- Active project switched to a **team project** the identity can at least
  view — this session used **"Elitea Testing Team" (id `471`)**; look up
  dynamically via the project selector rather than hardcoding if a more
  robust discovery is preferred, but `471` is confirmed stable and available.
- At least one existing **GitHub-type** toolkit already present in that team
  project — this session used toolkit id `151` ("ProjectAlita/elitea_core").
  Look up dynamically (`toolkit_api.list_toolkits(params={"toolkit_type":
  "github"})` with `project_id="471"`) rather than hardcoding, in case this
  specific toolkit is renamed/removed by its real owner (a different team
  member).

## Test Data
### reuse-existing
- The team project's pre-existing GitHub toolkit (dynamically looked up) —
  **read-only interaction**: open it, work its Configuration dropdown, never
  click its own Save/Discard.

### generate-per-test (created in test, cleaned up in its own teardown)
- **Display Name**: `autotest_private_cred_${timestamp}` — case pins the
  literal `autotest_private_cred`, but every sibling AFS in this feature
  timestamps names to avoid cross-run collisions (established convention,
  e.g. ELITEA-1962/1965/1974); recommend the same here. Clean up via
  `credential_api.delete_credential(id)` in a `finally` block regardless.
- **Credential type**: Github
- **Auth method**: Token
- **Access Token**: `${GIT_HUB_TOKEN}` — real token so the credential is
  live/valid (this test doesn't require validity, but reusing the shared
  `github_credential`-style fixture pattern keeps it consistent with
  `test_credential_create.py`'s ELITEA-1962 precedent). Never print/log the
  literal token value.

## Test Steps
1. Switch active project to the team project (id `471`) via
   `[data-testid="project-selector-trigger"]` → `[data-testid="select-option-471"]`.
2. Navigate to the Toolkits section, open the existing GitHub toolkit.
   - **Verify**: toolkit detail page loads — `toolkit-detail-title` visible,
     `toolkit-detail-configuration-tab` present.
3. Click the "Github Configuration" credential dropdown.
   - **Verify**: `[role="listbox"]` becomes visible.
4. Verify the dropdown shows two sections: a "Create" subheader (renders
   visually as "CREATE" via CSS `text-transform: uppercase`) and a "Saved
   github Credentials" subheader (renders "SAVED GITHUB CREDENTIALS").
5. Verify the CREATE section has exactly two options, in this order: "New
   private github credentials" (`data-value='{"kind":"create_action",
   "private":true}'`) and "New project github credentials"
   (`data-value='{"kind":"create_action","private":false}'`). Both only
   render together because the active project (471) differs from the
   identity's `personal_project_id` (399) — see Classification note #2.
6. Click "New private github credentials".
   - **Verify**: a new browser tab opens at
     `/{personal_project_id}/credentials/create-credential/github?section=credentials`
     (i.e. `/399/credentials/create-credential/github?section=credentials`),
     independent of the currently-active project (471).
7. In the new tab, fill Display Name (`toolkit-field-label-input`, via
   click+`select_text()`+`type()` — MUI field, `fill()` doesn't trigger
   React `onChange`) and select "Token" auth
   (`toolkit-field-auth-radio-token`), then fill Access Token
   (`toolkit-field-access_token-input-field`) with `${GIT_HUB_TOKEN}`.
   - **Verify**: Display Name field's value persists through the auth-method
     switch (does NOT get cleared by the radio-triggered re-render — a
     naive `.click()+.type()` without `select_text()` first can silently no-op
     on this field, see Automation Hints).
8. Click Save.
   - **Verify**: `POST /configurations/configurations/399` returns 200; the
     new tab navigates to `/credentials/all`.
9. Close the new tab, return focus to the original toolkit tab (still on
   project 471).
10. Re-open (or confirm still-open — see `#1047` in Automation Hints) the
    "Github Configuration" dropdown and click "Refresh the configurations"
    (`button[aria-label="Refresh the configurations"]`).
    - **Verify**: the refresh completes (network settle).
11. Verify the new private credential appears in the "Saved github
    Credentials" section, matched by its display name text within
    `li[role="option"]`.
12. Click the matching option to select it.
    - **Verify**: the Configuration combobox's displayed text now reads the
      new credential's name.
13. (Do NOT click the toolkit's own Save button — see Classification note
    #3; this shared, other-owned toolkit is a read-only vehicle for the
    dropdown-shape assertion.)
14. Verify private scope via the API: `GET
    /configurations/configuration/399/{credential_id}` (or the create
    response itself) has `project_id == 399` and `shared == false` — see
    Classification note #4 for why this is the available proxy for
    "visible only to its creator."

## Expected Results
- CREATE section shows exactly 2 options when the active project differs
  from the identity's personal project; exactly 1 ("New private...") when
  the active project IS the identity's personal project (documented, not
  separately asserted by this case — that's `ELITEA-1976`'s own personal-
  project baseline, not part of its Pass criteria).
- "New private..." always opens the create form under
  `/{personal_project_id}/credentials/create-credential/{type}`, regardless
  of the currently-active project.
- Newly created private credential appears in the SAME toolkit's Saved list
  after Refresh, and is selectable (combobox reflects the new value).
- Created credential's `project_id == personal_project_id` and
  `shared == false`.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Toolkits | list loads | step 2 (precondition nav) | — | asserted |
| 2 Open existing Github toolkit | detail page loads | step 2 | `toolkit-detail-title` visible | asserted |
| 3 Click credential dropdown | dropdown opens showing CREATE + Saved | steps 3 | `[role="listbox"]` visible | asserted |
| 4 Verify two dropdown sections | both visible | step 4 | subheader text (rendered, uppercase) | asserted *(clarification: needs a team project, not the case's implicit "any project" — Classification note #2)* |
| 5 Verify CREATE has 2 options (person/briefcase icons) | both present | step 5 | `data-value` pair; icon SVGs present but not asserted individually (glyph content, not semantic) | asserted *(icon presence asserted via option existing at all, not per-icon SVG path match — see Axis 2)* |
| 6 Click "New private github credentials" | form opens, Github type pre-selected | step 6 | new-tab URL contains `/credentials/create-credential/github` | asserted |
| 7 Fill Display Name + Token | fields accept input | step 7 | `input_value()` echoes typed value | asserted |
| 8 Save the credential | saved successfully | step 8 | POST 200 + tab navigates to `/credentials/all` | asserted |
| 9 Navigate back to toolkit | toolkit page loads | step 9 | tab-switch, no reload needed (page never navigated away) | asserted *(decomposed: case assumed a fresh navigation, live behavior is same-tab-still-there — same page, no reload required)* |
| 10 Click dropdown again, dropdown reopens | "Dropdown reopens" | step 10 | — | clarification *(the menu never closed — filed `#1047`; case's "reopens" wording is stale, live behavior is "was never closed." The AFS's step 10 accounts for both: confirm state, don't blindly re-click into an obscured trigger)* |
| 11 Click Refresh | list refreshes | step 10 | network-settle wait after click | asserted |
| 12 Verify new credential in list | visible | step 11 | `li[role="option"]` text match | asserted |
| 13 Select it | linked to toolkit | step 12 | combobox display text updates | asserted |
| 14 Verify private scope | not visible to other members | step 14 | API `project_id`/`shared` fields | asserted *(declared improvisation — Classification note #4, no second user account available)* |

### Axis 2 — Analyst additions

- Step 6 asserts the new-tab URL is scoped to `personal_project_id` (399)
  even though the toolkit itself lives in project 471 — *added: this is the
  concrete mechanism behind "private," worth guarding as its own assertion
  independent of step 14's terminal check.*
- Step 7 asserts the Display Name field's value survives the auth-method
  radio click — *added: observed during exploration that a naive fill
  sequence (click+type without select_text) can produce an empty field
  post-radio-click in a DIFFERENT script path; guarding this catches a
  regression in the shared MUI-field-fill technique, not a product defect
  (root-caused to script technique, not the app — see Automation Hints).*
- No console-error side-channel check added for this specific case (the
  broader credentials-list crash defect `#518` is already tracked/filtered
  by sibling specs; this case doesn't land on `/credentials/all` except
  transiently after Save, where the existing filter idiom applies if the
  implementer chooses to add one).

## Cleanup
1. Delete the created private credential: `credential_api.delete_credential(id)`.
2. Do not delete or modify the reused team-project toolkit (read-only vehicle).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback / Provenance |
|---|---|---|
| Project selector trigger | `[data-testid="project-selector-trigger"]` | on `automation/testids` (dev server renders it); PROVENANCE not cross-checked against `main` this pass — pre-existing shared-nav element, low risk |
| Project option (dynamic) | `[data-testid="select-option-{project_id}"]` | e.g. `select-option-471`; same provenance note as above |
| Toolkit detail title | `toolkit-detail-title` (`LocatorDescriptor`, already in `toolkit_detail_page.py`) | on-main ✓ (pre-existing page object field, documented there) |
| Configuration dropdown trigger | **testid needed**: `toolkit-credential-select-{type}` (e.g. `toolkit-credential-select-github`) — see `_surface.md` gap table for exact source pointer (`CredentialsSelect.jsx`, pass `dataTestId` prop to `<Select.SingleSelect>`) | needs-adding — currently only `[role="combobox"][aria-labelledby*="Github Configuration"]`, a non-testid handle; DO NOT ship that as the final locator, it's exploration-only |
| CREATE option "New private {type} credentials" | **testid needed**: comes free once `SingleSelect.jsx`'s action-branch gets `data-testid={option.testId ?? \`select-option-${option.value}\`}` (see `_surface.md`) → `select-option-{"kind":"create_action","private":true}` | needs-adding |
| CREATE option "New project {type} credentials" | same mechanism → `select-option-{"kind":"create_action","private":false}` | needs-adding |
| "Refresh the configurations" button | `button[aria-label="Refresh the configurations"]` — no testid currently; PROVENANCE: absent from both refs, needs-adding if implementer wants strict testid-only compliance (currently the ONLY handle for this control anywhere in the suite is the aria-label, used already by the merged `test_toolkit_credential_indicators_e2e` for an analogous refresh button pattern) | needs-adding: `credential-select-refresh-button` |
| Saved-credential option (dynamic) | `select-option-{"kind":"saved","elitea_title":"...","private":true\|false}` (`data-testid`, already present) | on `automation/testids` ✓ (confirmed live) — provenance vs `main` not separately re-checked; this is a generic, pre-existing shared-select mechanism, not case-specific |
| Credential create form: Display Name | `toolkit-field-label-input` (`CredentialFormFieldsMixin.display_name_input`) | on-main ✓ (pre-existing, documented) |
| Credential create form: ID (mirror) | `toolkit-field-elitea_title-input` (`CredentialFormFieldsMixin.id_input`) | on-main ✓ |
| Credential create form: Token radio | `toolkit-field-auth-radio-token` (`CredentialCreatePage.AUTH_METHOD_RADIO` template) | on-main ✓ |
| Credential create form: Access Token field | `toolkit-field-access_token-input-field` (`CredentialCreatePage.access_token_input`) | on-main ✓ |
| Credential create form: Save button | `credential-form-save-button` (`CredentialFormFieldsMixin.save_button`) | on-main ✓ |

## Network Behavior
- `POST /configurations/configurations/{personal_project_id}` — fires on the
  create-form Save click; 200 with the new credential (`id`, `elitea_title`,
  `project_id`, `shared`) in the body.
- Refresh button re-fetches the configurations list (no distinguishing query
  param observed beyond the standard list GET) — wait on network-settle,
  not a specific response predicate.
- `GET /configurations/configuration/{project_id}/{id}` — used for the
  step-14 private-scope check (or read straight off the create response,
  avoiding an extra round-trip).

## Known Defects Found During Exploration
- None blocking THIS case's own flow. `#999` (GitHub toolkit type
  unavailable) no longer reproduces — see Classification note #1 and
  `_surface.md`; not re-filed, flagged as a finding for the report.
  `#1047` (dropdown-stays-open clarification) is already filed and directly
  informs step 10's design — not a new defect.

## Blocked Steps
None — all 14 case steps executed live end-to-end (steps 1-2 are the
precondition/navigation the case's own step 1-2 describe).

## Automation Hints
- Framework: Playwright + pytest, page objects (`.agents/testing.md`).
- Reuse `ToolkitDetailPage` (`automation/pages/toolkit_detail_page.py`) —
  extend with the Configuration-dropdown methods this case needs (open,
  read CREATE options, click a CREATE option and catch the new tab,
  refresh, select a saved option) rather than duplicating; none of that
  exists there yet (the file currently only covers the status-indicator
  family: reload/open-in-new-tab/warning-banner for an ALREADY-linked
  credential, not the dropdown-open/CREATE-option/select flow this case
  needs).
- Reuse `CredentialCreatePage` (`automation/pages/credential_create_page.py`)
  unmodified for filling the new-tab form — its `set_display_name()`
  (`select_text()`+`type()`, NOT `fill()`) already avoids the empty-field
  trap noted in Axis 2.
- `#1047`: do not write "click the trigger to reopen the dropdown" as a
  literal step if staying in the SAME tab/session after the CREATE-action
  click — the menu is already open; re-clicking targets an obscured
  element and throws `TimeoutError`. Either (a) assert `[role="listbox"]`
  is already visible before proceeding to Refresh, or (b) do a fresh
  `navigate_to_toolkit()` reload after closing the new tab, which
  guarantees fresh, unambiguous state (the safer choice for a first
  implementation — this AFS's steps 9-10 are written to make either
  approach work, but recommend (b) to sidestep `#1047` entirely rather than
  asserting around it).
- Use `page.context.expect_page()` around the CREATE-option click to catch
  the new tab (standard Playwright pattern, same as
  `test_toolkit_credential_indicators_e2e`'s "Open in new tab" step).
