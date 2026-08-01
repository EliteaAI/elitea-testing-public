# Test Case: Create Credential — Required Fields Validation

## Metadata
- **TMS ID**: ELITEA-1975
- **Linked Story**: none
- **Priority**: l1 (case frontmatter: `critical`; case body table header says
  `priority: medium` — **pre-existing inconsistency in the source case, not
  introduced by this AFS**. Per dispatch instruction, `critical` from the
  frontmatter is treated as authoritative. **CLARIFICATION filed, not a
  defect** (case-authoring nit, not a product bug) — flagged here for the
  TMS case owner to correct the body table upstream. Same pattern as
  ELITEA-1971's AFS.)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`). No credential data is fed in from GitHub/Jira toolkit
  test-data env vars — all field values entered are synthetic/dummy strings,
  since this case never reaches a real `Test connection` or `Save` (Save is
  intentionally never clicked, to avoid persisting a broken/nameless
  credential given the defect found — see Known Defects).
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: defect-found
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual`. `.agents/testing.md` has no documented `TMS
  case-gate` exclusion list for this project, so per the skill's default
  ("if absent, default to fetching all and flag the gap") this run proceeded
  and executed the case end-to-end. Same gap already flagged by ELITEA-1971's
  AFS; not re-filed separately.
- **Testid note (per dispatch instruction):** EL-1971's testid landing was
  confirmed live during this run — `credential-form-save-button` **already
  exists** on the create-credential form's Save button (confirmed via DOM:
  `<button data-testid="credential-form-save-button">Save</button>`), and the
  credential-type-selector cards already carry
  `data-testid="toolkit-type-card-{type}"` (confirmed live:
  `toolkit-type-card-github`). Both are used directly in this AFS's Concrete
  Handles instead of being flagged as gaps.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips
  login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A credential type with at least two required fields is selected.
  **Selection note:** the GitHub credential type (tried first) does **not**
  satisfy this precondition faithfully — its "Base Url" field ships with a
  live default value (`https://api.github.com`) already populated, so only
  Display Name starts genuinely empty. Filling Display Name alone on GitHub
  therefore already satisfies "all required fields non-empty" and Save
  enables at Step 3, contradicting the case's own expected result for that
  step. This is a **test-data/type-selection mismatch, not a product
  defect** — GitHub's sensible default is correct product behavior. **This
  AFS instead uses the Jira credential type**
  (`/credentials/create-credential/jira`), which has three genuinely-empty
  required fields at load (`Base Url *`, `Api Key *`, `Username *`, all with
  only placeholder text, no default value) plus the de-facto-required
  Display Name — a faithful match for the case's "at least two required
  fields" precondition. Recommend the case body be updated to name a
  specific credential type (e.g. Jira) rather than leaving type selection to
  the executor, to avoid this ambiguity recurring. Filed as a
  CLARIFICATION, not a defect.

## Test Data

### Synthetic literals used during this exploration (never submitted — Save
was deliberately never clicked; see Known Defects)
- Display Name: `autotest_reqfields_cred` (first attempt, GitHub type) /
  `autotest_reqfields_cred2` (second attempt, Jira type, fresh page load)
- Base Url: `https://autotest2.atlassian.net` (dummy, not a real Jira
  instance — connection is never tested)
- Api Key: `dummy-api-key-value-2` (dummy secret string)
- Username: `autotest2.user@example.com` (dummy)

No credential is ever persisted by this case — it exercises only the
create-form's client-side Save-button gating, never an actual `POST`. No
API-level test data or cleanup is required.

## Test Steps

1. Navigate to the credential creation form.
   - Navigate to `${BASE_URL}/credentials/all`, then click credential type
     card `getByTestId("toolkit-type-card-jira")` (pattern confirmed live for
     `toolkit-type-card-github`; the `-jira` variant follows the same
     `toolkit-type-card-{type}` convention used across all type cards in
     `CredentialTypeSelector.jsx`/`GroupedCategory.jsx` — confirmed by
     navigating directly to `${BASE_URL}/credentials/create-credential/jira`
     and observing the identical form).
   - **Verify**: form opens with all fields empty — confirmed live via
     snapshot: Display Name empty, Base Url `*` empty (placeholder only, no
     default), Api Key `*` empty, Username `*` empty, Auth defaults to
     `Basic` (radio checked), disabled `ID *` field empty. `Save` and
     `Cancel` buttons both `[disabled]` (confirmed live via snapshot
     immediately after navigation).

2. Leave all fields empty.
   - **Verify**: `getByTestId("credential-form-save-button")` remains
     `[disabled]` — confirmed live via snapshot taken directly after Step 1's
     load, no interaction needed since this is the same as Step 1's baseline.

3. Fill in only the Display Name field
   (`getByTestId("toolkit-field-label-input")`, value
   `autotest_reqfields_cred2`).
   - **Verify**: `getByTestId("credential-form-save-button")` remains
     `[disabled]` — confirmed live via snapshot immediately after the fill
     (Base Url/Api Key/Username all still empty on this Jira-type run,
     unlike the GitHub-type false-start above). **Side-observation** (Axis
     2): the `Cancel` button becomes enabled at this point too (form is now
     "dirty" per `isFormDirtyExcluding`), independent of `Save`'s
     validation-driven disabled state — the two buttons are gated by
     different conditions (`Cancel`/`Discard` by dirty-state alone, `Save`
     by dirty-state **and** required-field validation).

4. Fill in the other required field(s) for the selected type — Base Url
   (`getByTestId("toolkit-field-base_url-input")`,
   `https://autotest2.atlassian.net`), Api Key
   (`getByTestId("toolkit-field-api_key-input-field")`,
   `dummy-api-key-value-2`), Username
   (`getByTestId("toolkit-field-username-input")`,
   `autotest2.user@example.com`).
   - **Verify**: `getByTestId("credential-form-save-button")` becomes
     enabled — confirmed live via snapshot (`button "Save" [ref=...]
     [cursor=pointer]`, no `[disabled]`) and independently via DOM query
     (`document.querySelector('[data-testid="credential-form-save-button"]').disabled
     === false`), immediately after the third field (Username) is filled.

5. Clear the Display Name field
   (`getByTestId("toolkit-field-label-input").fill('')`).
   - **Verify — DEFECT.** Expected: `Save` becomes `[disabled]` again.
     Actual: `Save` **remains enabled**
     (`document.querySelector('[data-testid="credential-form-save-button"]').disabled
     === false` with `labelValue: ""`) — confirmed via **two independent
     observation methods** (accessibility snapshot + raw DOM query) and
     reproduced **twice, on two separate fresh page loads**, using native
     Playwright `.fill()` actions only (no synthetic/dispatched events —
     satisfies the pristine-gesture reproduction gate). See Known Defects #1
     for the full root-cause writeup; filed as GitHub issue
     [#526](https://github.com/EliteaAI/elitea-testing-public/issues/526).
   - **Control check (Axis 2, not a case requirement):** to isolate whether
     the defect is specific to Display Name or affects all required fields
     equally, Display Name was restored and **Username** was cleared
     instead (all other fields left filled): `Save` correctly re-disabled
     (`saveDisabled: true`). Same check repeated by restoring Username and
     clearing **Base Url** instead: `Save` also correctly re-disabled
     (`saveDisabled: true`). This confirms the defect is **isolated to the
     Display Name field specifically** — every other required field
     (`base_url`, `api_key`, `username`) correctly gates `Save`.

## Expected Results
Per the case's Pass criteria, Save should reflect required-field state
exactly: disabled with any required field empty (Steps 1–3), enabled once
all required fields are filled (Step 4), and disabled again the instant any
required field — including Display Name — is cleared (Step 5). **Steps 1–4
pass exactly as specified** (live-verified on the Jira credential type).
**Step 5 fails**: clearing Display Name does not re-disable Save, while
clearing any other required field correctly does. This is the case's
central Pass/Fail criterion ("does not re-disable when a required field is
cleared") and it fails for exactly one field. See Known Defects below.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture (localhost dev token) | asserted |
| Precondition: project + Credentials section accessible | — | AFS Preconditions | project `399` selected, `/credentials/all` loads | asserted |
| Precondition: credential type with ≥2 required fields selected | — | AFS Preconditions | Jira type selected after GitHub type-selection mismatch found (see Preconditions note) | asserted *(type substituted — see CLARIFICATION)* |
| 1 Navigate to credential creation form | form opens, all fields empty | step 1 | step 1: snapshot of empty Display Name/Base Url/Api Key/Username, Save+Cancel disabled | asserted |
| 2 Leave all fields empty | Save remains disabled | step 2 | step 1's own load-state snapshot (no separate interaction needed) | asserted |
| 3 Fill only Display Name | Save remains disabled | step 3 | step 3: snapshot immediately after fill | asserted |
| 4 Fill other required field(s) | Save becomes enabled | step 4 | step 4: snapshot + DOM query after Base Url/Api Key/Username filled | asserted |
| 5 Clear Display Name | Save becomes disabled again | step 5 | step 5: snapshot + DOM query after clearing Display Name | **FAILED — defect, see Known Defects #1** |
| Expected Final State: Save only enabled when all required fields valid, disables on any required field clearing | — | steps 1–5 | steps 1–5 jointly | **partially asserted — true for base_url/api_key/username, false for Display Name** |

### Axis 2 — Analyst additions

- step 3 documents that **Cancel** becomes enabled independently of
  **Save**'s validation state — *added: clarifies the two buttons are gated
  by different conditions (dirty-state alone vs. dirty-state + validation),
  relevant for anyone writing a broader credential-edit case.*
- step 5's control check (clearing Base Url alone, then Username alone,
  with Display Name filled) — *added: isolates the defect precisely to the
  Display Name field rather than leaving "required-field validation is
  broken" as a vague, broader claim than what was actually observed.*
- Root-cause source trace (Known Defects #1) — *added: gives the
  implementer/fixer the exact file:line rather than just a behavioral
  symptom.*
- "zero console errors/warnings across the flow" — *added: side-channel
  check per this skill's standard discipline; confirms this is a silent
  logic gap, not a thrown/logged error.*

## Cleanup
1. No credential is ever created or persisted by this case — Save is
   deliberately never clicked (see Known Defects #1's severity rationale).
   No API cleanup needed.
2. No route interception, mocked network, or browser-context state needs
   explicit teardown beyond the normal per-test browser context lifecycle.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Credentials list → credential type card (`CredentialTypeSelector.jsx`/`GroupedCategory.jsx`) | `page.get_by_test_id("toolkit-type-card-{type}")` — **confirmed live, existing testid** (e.g. `toolkit-type-card-github`; `-jira` variant not independently re-confirmed by click in this run but same code path renders all type cards identically) | `page.get_by_text("Jira", exact=True)` scoped to the type-selector grid |
| Display Name field (`ToolBaseProperty.jsx`, `k === 'label'`) | `page.get_by_test_id("toolkit-field-label-input")` — **confirmed live, existing testid** (shared property-renderer pattern, matches memory note `toolkit_mcp_create_form_quirks`) | `page.get_by_role("textbox", { name: "Display Name" })` |
| Base Url field (Jira, `k === 'base_url'`) | `page.get_by_test_id("toolkit-field-base_url-input")` — **confirmed live** | `page.get_by_role("textbox", { name: "Base Url *" })` |
| Api Key field (Jira, `k === 'api_key'`) | `page.get_by_test_id("toolkit-field-api_key-input-field")` — **confirmed live** (note the `-input-field` suffix differs from the plain `-input` suffix on other fields — this field renders with the secret/password view-toggler wrapper) | `page.get_by_role("textbox", { name: "Api Key *" })` scoped away from the "Secret"/"Password" toggle buttons |
| Username field (Jira, `k === 'username'`) | `page.get_by_test_id("toolkit-field-username-input")` — **confirmed live** | `page.get_by_role("textbox", { name: "Username *" })` |
| ID field (disabled, `elitea_title`) | `page.get_by_test_id("toolkit-field-elitea_title-input")` (inferred from the shared `ToolBaseProperty.jsx` naming pattern, consistent with ELITEA-1971's AFS; not independently re-confirmed live beyond its disabled state in this run) | `page.get_by_role("textbox", { name: "ID *" })` |
| Save button (create form, `CredentialTabBar.jsx`) | `page.get_by_test_id("credential-form-save-button")` — **confirmed live, existing testid** (landed via EL-1971 per dispatch note; same element also used by the Edit/Discard flow AFS in ELITEA-1971) | `page.get_by_role("button", { name: "Save" })` |
| Cancel button (create form — same component renders "Cancel" instead of "Discard" when `isEditing` is false) | **testid needed** — `Button.DiscardButton` receives `dataTestId="credential-form-discard-button"` from the call site regardless of edit-vs-create mode (confirmed via source, `CredentialTabBar.jsx:240`), so the *create*-mode "Cancel" button already carries this same testid live; not independently re-confirmed by click in this run since the case's Pass criteria concern only `Save` | `page.get_by_role("button", { name: "Cancel" })` |
| Auth radio group (Jira: Basic/Bearer; GitHub: Anonymous/Token/Password/App private key) | **testid needed** — plain MUI `Radio`/`FormControlLabel`, no `data-testid` observed on individual radio options | `page.get_by_role("radio", { name: "Basic" })` etc., scoped to the `radiogroup` under the "Auth" label |

## Network Behavior
No network calls are triggered by any step in this case — every observed
interaction (typing into fields, the Save button's enabled/disabled state)
is pure client-side Formik state + the `toolErrors` validation state
computed in `ToolBase.jsx`'s `useEffect` (`validateRequiredFields()`
helper). `Save` is never clicked in this exploration (see Known Defects #1),
so no `POST /configurations/{project_id}` fires. The only network calls
observed were the ambient page-load calls for the credential-type schema
list (`configurationsAsSchema`, loaded once when the Credentials section
first mounts) — not specific to this case's Pass/Fail criteria.

## Known Defects Found During Exploration

1. **[MAJOR — filed as GitHub issue [#526](https://github.com/EliteaAI/elitea-testing-public/issues/526)] Save button does not re-disable when the Display Name field is cleared, while every other required field correctly does.**
   Root cause (source-confirmed):
   `EliteaUI/src/[fsd]/features/toolkits/lib/helpers/toolBase.helpers.js`'s
   `validateRequiredFields()` only iterates `schema.required` — the
   type-specific config schema (e.g. Jira's `base_url`/`api_key`/`username`).
   The generic `label` (Display Name) field is never part of any credential
   type's `schema.required`, so clearing it never produces a
   `toolErrors.label` entry, and `CredentialTabBar.jsx`'s Save-disable logic
   (`hasErrors || shouldDisableSave`,
   `EliteaUI/src/[fsd]/features/credentials/ui/credentials-tab-bar/CredentialsTabBar.jsx:223`)
   never observes it as invalid. The disabled, auto-derived "ID *"
   (`elitea_title`) field is also explicitly excluded from the same
   validation while auto-managed
   (`enableEditEliteaTitle || prop !== 'elitea_title'` filter, same helper
   file). Net effect: **nothing in the Save-gating validation path checks
   that Display Name is non-empty**, even though the field is presented
   without a "not required" affordance and the case (reasonably) treats it
   as required. Reproduced twice on two separate fresh page loads using
   native Playwright `.fill()` (pristine-gesture gate satisfied — see Test
   Steps §5). Console clean throughout (0 errors/0 warnings) — this is a
   silent logic gap, not a thrown error. **Not filed as case-text drift /
   reverse-masking** — the case's expectation ("clearing a required field
   re-disables Save") is the objectively correct behavior demonstrated by
   every *other* required field on the same form; Display Name is the
   outlier, not the case.
   **Open question left for the fixer** (explicitly not exercised in this
   run, to avoid persisting broken test data): whether the backend
   independently rejects an empty `label`/name on `POST`. If it does,
   impact is degraded UX only (a momentarily-clickable Save that still
   fails server-side); if it doesn't, impact extends to actually **creatable
   nameless credentials**.
2. **[CLARIFICATION — not filed as a defect] Case precondition "a credential
   type with at least two required fields" is ambiguous across credential
   types and can silently produce a false pass/fail on Steps 3–4.** GitHub's
   `Base Url` field ships with a live default (`https://api.github.com`)
   already populated, so filling only Display Name already satisfies "all
   required fields have valid input" and Save enables at Step 3 — directly
   contradicting the case's own Step 3 expected result ("remains disabled")
   for that specific type. This is correct, intentional product behavior
   (a sensible default counts as a filled required field), not a defect —
   but it means the case, as authored, is type-selection-sensitive in a way
   its text doesn't surface. Recommend the case body name a specific
   credential type (Jira, or any other type with zero pre-filled required
   fields) rather than leaving the choice to the executor. Not filed as a
   separate GitHub issue per this project's bug-filing policy (routes
   case-text ambiguity as an in-AFS clarification, not a tracker ticket,
   when it doesn't block the case from being executed some other way).
3. **[Non-blocking, informational] Priority mismatch between case
   frontmatter (`critical`) and case body table (`medium`)** — see Metadata
   note above; same pre-existing pattern as ELITEA-1971. Not filed
   separately.

## Blocked Steps
None — all 5 case steps were executed live end-to-end against the real DEV
backend (Jira credential type). Step 5 surfaced a real defect (see Known
Defects #1) but the step itself was fully executed and observed; the
defect is a finding, not a blocker to completing the case's exploration.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/toolkits/test_credential_required_fields_validation.py`
  (new file — grep of `automation/tests/ui/toolkits/` found no existing test
  exercising the Create-Credential form's Save-button required-field
  gating; the closest existing files
  (`test_credential_discard_changes.py`, `test_toolkit_indicators_for_credentials.py`)
  cover the Detail/Edit page's Discard flow and cross-page auth-warning
  indicators respectively, not the Create form's own validation).
- **This test should assert Step 5 as a `expect.soft()` + linked-defect
  pattern per this project's no-masking policy** (`.agents/profile.md` §
  Bug filing: "isolated defect → `expect.soft()` with ticket linked"), since
  issue #526 is an isolated, deterministic, single-cause defect scoped to
  exactly one field. Do **not** weaken the assertion or skip Step 5 — the
  spec should stay RED on Step 5's assertion (`Save` should be disabled and
  currently is not) until #526 is fixed, per `.agents/testing.md` § Merge
  gate's "Sanctioned-RED exception."
- New page object suggested:
  `automation/pages/credential_create_page.py` (parallel to the existing
  `credential_detail_page.py` — no create-form page object currently exists
  in `automation/pages/`), holding `LocatorDescriptor` fields for every
  handle in the Concrete Handles table above. All the Save/Display
  Name/Base Url/Api Key/Username testids are **already live** — no
  `add-data-testid` round-trip is needed for this case's own steps (only
  the Auth radio-group options remain testid-less, and this case never
  needs to assert on them individually).
- Existing `CredentialAPI` (`automation/api/client.py:944`) is **not
  needed** for this case's setup/teardown, since no credential is ever
  created or persisted — this is a pure client-side form-validation case.
- Wait strategy: no network response to await (pure client-side Formik +
  `toolErrors` state, confirmed above) — assert directly on the `Save`
  button's `disabled` attribute/state after each fill/clear action; no
  fixed timeout needed, Playwright's actionability model already waits for
  the DOM to settle before each subsequent interaction.
- Suggested markers: `@pytest.mark.credentials`, `@pytest.mark.regression`,
  plus whatever priority marker corresponds to `l1`/`critical` per
  `pytest.ini`'s `p0`–`p3` scheme (this project's Metadata note flags the
  frontmatter-vs-body priority mismatch — treat as `critical`/highest
  applicable marker per the dispatch instruction's resolution).
