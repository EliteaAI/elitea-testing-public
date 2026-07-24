# Surface digest: Credentials (create form + list) — `/credentials/*`

Confirmed handles/waits/quirks from live exploration. This is a cache for
same-surface analysts and the implementer — it does NOT replace live
execution; verify handles as you use them, and update this file (create or
edit) after your own run. Lives on the base branch — commit alongside your
AFS, never on a case branch.

First digest for this surface, written during ELITEA-1978 analysis
(2026-07-24, project `Private`/399, local `http://localhost:5173`). Six
prior AFS on this feature (ELITEA-1962/1963/1965/1971/1972/1974/1975)
already document individual confirmed testids; this digest's main new
contribution is mapping the **dynamic-testid COMPOSITION CHAINS** (source
file:line, hop by hop) — none of those prior AFS traced the chain past the
call site, which is why a bare-substring `git grep` for the full rendered
testid string finds nothing in `EliteaUI/src` (see gotcha below).

Extended during ELITEA-1976 analysis (2026-07-24, same day, projects
`Private`/399 + `Elitea Testing Team`/471) with a **sibling surface** below —
the Toolkit Configuration page's credential-select dropdown
(`CredentialsSelect`), reached from `/toolkits/all/{id}` rather than
`/credentials/*`. Kept as one file since both surfaces share the same
underlying `ToolBaseProperty.jsx` dynamic-testid mechanism documented above,
and the same `CredentialsSelect` component this digest's new section covers
in depth is what actually LINKS a credential to a toolkit (the two surfaces
are two ends of the same feature).

## Gotcha: dynamic testids don't grep as bare substrings

Every credential-form testid is a **template composition**, sometimes
across 2-3 files/hops. A closure-record-style
`git grep -- "toolkit-field-label-input"` returns **zero hits** on
`automation/testids` even though the testid is live and confirmed working —
because the literal string never appears in source; only the template
pattern does. **Verify dynamic testids by grepping the TEMPLATE pattern**
(e.g. `` toolkit-field-${k}-input ``), not the resolved string, and trace
every hop before declaring "not found."

Confirmed composition chains (all hops present on `automation/testids` /
local working tree as of `043ea101`; NONE present on `origin/main` yet —
i.e. every credential-form testid below is awaiting human cherry-pick):

| Rendered testid (example) | Hop 1 | Hop 2 | Hop 3 |
|---|---|---|---|
| `toolkit-type-card-github` | `CategoryItemCard.jsx:14` — `` `toolkit-type-card-${itemKey}` `` | — | — |
| `toolkit-field-label-input` / `toolkit-field-elitea_title-input` / `toolkit-field-base_url-input` / `toolkit-field-username-input` (plain text fields) | `ToolBaseProperty.jsx:615` — `` `toolkit-field-${k}-input` `` (generic fallback render path) | — | — |
| `toolkit-field-auth-radio-token` (auth method radio, per-option) | `ToolSection.jsx:291` — `` `toolkit-field-${sectionKey}-radio` `` (base testId passed to the group) | `RadioButtonGroup.jsx:37` — `` `${testId}-${String(item.value).toLowerCase().replace(/\s+/g,'-')}` `` (per-option suffix, on the `FormControlLabel`, NOT the native `<input>`) | — |
| `toolkit-field-access_token-input-field` / `toolkit-field-api_key-input-field` (secret/password-toggle fields) | `ToolBaseProperty.jsx:340` — `` `toolkit-field-${k}-input` `` (passed as `testId` prop into `SecretManagementInput`) | `SecretManagementInput.jsx:62` — passes `inputProps={{'data-testid': testId}}` through unchanged to `SecretField` | `SecretField.jsx:77` — `` nativeInputTestId = `${inputProps['data-testid']}-field` `` — the `-field` suffix lands on the TextField's **native `<input>`** (`inputProps` prop, distinct from the caller's own `inputProps` which lands on the TextField root) |

Playwright's `is_checked()` / `.click()` on the radio still resolve
correctly through the `FormControlLabel` wrapper (testid is on the label,
not the input) — confirmed live, no extra unwrap needed by callers (same
note ELITEA-1975's AFS already made for this element).

## Create-form field-required indicators — visual asterisk is a reliable signal, but incomplete

Every field genuinely in the credential type's static `schema.required`
renders its label with a trailing `*` (confirmed: "Display Name", "ID",
"Base Url" all show `* *` in `document.body.innerText` on the GitHub
create form). **This asterisk is driven by the SAME static `schema.required`
list `validateRequiredFields()` reads** — so it's a reliable proxy for "will
this field's emptiness gate Save", but it does NOT cover auth-method-
conditional fields (Access Token when Token auth is selected, Username/
Password when Password auth is selected, App private key when that auth is
selected) — none of those carry an asterisk regardless of which auth method
is currently selected, and Save never gates on them either. See Known
Defects below — this is a live, filed, confirmed gap
([#1004](https://github.com/EliteaAI/elitea-testing-public/issues/1004)),
not a documentation nuance.

## Known defects on this surface

- **[#526](https://github.com/EliteaAI/elitea-testing-public/issues/526)**
  — clearing Display Name (`label`) after filling it does not re-disable
  Save, unlike every statically-required field. Root cause:
  `validateRequiredFields()` excludes `label` from its check entirely
  (never in any type's `schema.required`).
- **[#1004](https://github.com/EliteaAI/elitea-testing-public/issues/1004)**
  — selecting "Token" auth (GitHub type) and leaving the resulting "Access
  Token" field empty: no asterisk appears, Save never disables, AND the
  backend independently accepts the empty value (`POST` returns 200,
  persisted record shows `"data": {"access_token": ""}, "status_ok":
  false`). Same root helper (`validateRequiredFields()` only reads the
  static `schema.required` array) but a DIFFERENT field/scenario
  (auth-conditional, not universally-excluded) — filed separately per this
  repo's strict-per-bug policy. Live-confirmed this is NOT cosmetic-only:
  the backend also persists the broken credential, so it's a functional
  gap, not just a missing UI indicator. Not yet verified whether the same
  gap applies to the Password/App private key auth methods' own required
  fields (`username`/`password`/`app_private_key`) — same code path, so
  suspected but not independently reproduced this session; a good target
  for whoever picks up #1004's fix to check as a regression net.
- **Pre-existing console noise, NOT this feature's bugs** (already
  tracked, exclude from any "no new console errors" assertion on this
  surface): `#291` (React key-prop / `<p>`-in-`<p>` dev warnings on the
  type-selector grid), `#518` (`CredentialsList.jsx` double-`onRefetch()`
  crash on `/credentials/all` navigation, ~60-75% reproduction — already
  functionally worked around at the page-object layer via
  `credentials_list_recovery.py`), `#554` (`toolkitTypes` RTK-Query 404
  race on repeated create-credential navigations).

## Duplicate-name error — surfaces via the generic `apiError` banner, no testid (GAP)

Attempting to create a credential with a Display Name that already exists
(`elitea_title` collision) rejects the `POST` and surfaces the backend's
literal message (`Credential with ID '<name>' already exists`) via
`CredentialTabBar.jsx`'s `doSave()` → `setApiError(buildErrorMessage(...))`
path → rendered in `CredentialForm.jsx:352-359` as a bare
`<Typography>{apiError}</Typography>` with **no `data-testid` at all**
(confirmed live: `el.getAttribute('data-testid') === null`). This is a
genuine, not-yet-filled gap — recommended shape
`credential-form-api-error-message`, placed on the SHARED
`CredentialFormFieldsMixin` (both Create and Edit flows render through the
same `CredentialForm.jsx`, passing `apiError`/`setApiError` down from their
respective parent pages).

`doSave()`'s error-routing logic (`CredentialsTabBar.jsx`) has TWO branches
worth knowing before writing a test against any credential-API-error case:
- If `result.error?.data?.field === 'elitea_title'`, `onEnableEditTitle()`
  fires (re-enables the disabled ID field for editing) — did NOT fire for
  the duplicate-name error in this session (ID field stayed disabled),
  meaning the backend's error shape for THIS message doesn't set
  `field: 'elitea_title'`.
- `CredentialErrorHelpers.extractInformationFromCredentialError()` then
  tries to map the message onto a schema property key (by substring match
  against each property's title/description/key) — for the duplicate-name
  message this produces zero matches (no schema property is titled/keyed
  "ID" or "Credential"), so it falls through to the generic `apiError`
  banner rather than a per-field validation message.

## Zero-credential-project auto-redirect — precondition already covered by prior AFS, still true

`CredentialsList.jsx` auto-redirects `/credentials/all` straight to the
create form when the project has ZERO credentials (ELITEA-1963's AFS
documents this, motivating `CredentialCreatePage.navigate_to_type()`'s
direct-URL entry point over the old card-click flow). Confirmed still true
this session; not re-tested independently since the shared DEV project
(`Private`/399) already has ≥1 credential at all times in practice.

## Cleanup discipline — this is a SHARED DEV project

Project `399` ("Private") is shared across concurrent analyst/implementer
sessions — any credential created during exploration MUST be deleted via
the API before the session ends (`DELETE
/configurations/configuration/{project_id}/{id}` → `204`), confirmed
working this session for 2 credentials. Don't leave `autotest_*` credential
litter for the next analyst to trip over.

---

# Surface digest addendum: Toolkit Configuration credential dropdown (`CredentialsSelect`)

Written during ELITEA-1976 analysis (2026-07-24). Covers the credential-select
field rendered by `ToolBaseProperty.jsx`'s `type === 'configuration'` branch
(`<CredentialsSelect>`,
`src/[fsd]/features/credentials/ui/credentials-select/CredentialsSelect.jsx`)
— the SAME component behind every "{Type} Configuration" field across every
toolkit type (`github_configuration`, `gitlab_configuration`,
`jira_configuration`, …), plus AI-credential/vector-storage selects
elsewhere. Confirmed 100% generic in the source — nothing type-specific in
the implementation, only in the schema field key `k` and the
`configuration_types` the caller passes.

## GitHub toolkit type is currently BLOCKED in this DEV deployment

Filed as **EliteaAI/elitea-testing-public#999** (MAJOR, 2026-07-23). Toolkit
type `github` is entirely absent from the "Choose the toolkit type" grid
(`toolkit-type-card-github` does not exist among the rendered
`toolkit-type-card-*` testids); `POST .../elitea_core/tools/prompt_lib/{id}`
with `type: "github"` → `403 {"error": "Toolkit type 'github' is not
available in this deployment"}`. Existing GitHub toolkits (ids 117/150/151 in
project 471) are permanently locked to a read-only Raw-JSON view — the
Form/RawJson toggle itself carries `Mui-disabled`, so the Configuration
section (and this whole credential-dropdown surface) never renders for them
at all. GitHub credential TYPE still works fine (`POST
/configurations/configurations/{project}` with `type: "github"` succeeds) —
this is specific to the toolkit entity, not credentials in general. **Any
case needing a "Github-based toolkit" as its vehicle should substitute
GitLab** (confirmed live: creatable, Form-editable, identical
`CredentialsSelect` mechanics) until #999 resolves.

## Acting identity ("Test Bot") is viewer-only in every non-personal project

Confirmed live via two separate 403s in project `471` ("Elitea Testing
Team"): `configurations.configuration.create` missing (blocks credential
creation) and `models.applications.tools.create` missing (blocks toolkit
creation). The SAME identity has full author rights in its own personal
project (`Private`, id `399` — `personal_project_id`). Every prior
credential/toolkit test in this suite creates its own scratch data in the
default project (`Private`), which is why this constraint was never hit
before — a "private, not visible to other members" claim is meaningless in a
single-user personal project, so any future case needing genuine
multi-member semantics will hit this same wall. Implication: reuse an
EXISTING toolkit/credential in the team project read-only (never Save it —
see below), do the actual create/verify work under the acting user's OWN
personal project instead.

## The CREATE section's two options are conditional on project context

`CredentialsSelect.jsx`'s `createMenuData`: the "New private" option always
renders (unless `onlyPublic`); the "New project" option **only renders when
`selectedProjectId != personal_project_id`** — i.e. you must be in a
non-personal (team) project to see both CREATE options. In the `Private`
project (== personal project), only "New private" would show. Confirmed
live in project 471.

## "New private X credentials" creates under the PERSONAL project, not the active one

Clicking it calls `window.open()` to
`/credentials/create-credential/{type}?section={section}` under
`personal_project_id` (not `selectedProjectId`) — a REAL new tab (not a
route push in the same tab). This IS the privacy mechanism: a private
credential physically lives in the creator's own personal project, which is
why it's structurally invisible to a `GET` scoped to any other project
(confirmed live: a credential list call scoped to project 471 returns 0
matches for a credential created via this flow, while the same call scoped
to the personal project returns it with `shared: false`). Use this
project-scope diff as the single-account-sufficient proxy for "not visible
to other project members" — no second human test account is needed to prove
this claim.

## The Saved-credentials list does NOT auto-refresh

Creating a new credential in the spawned tab does not push into the
already-open dropdown in the original tab — you must close the tab, return,
reopen the dropdown (it fully closes on tab-switch), and click the explicit
Refresh button. Confirmed live (2 dropdown-open cycles needed).

## Additional testid provenance (fresh `git fetch origin` in `../EliteaUI`, 2026-07-24)

Builds on this digest's existing dynamic-testid composition-chain table
above — same `toolkit-field-${k}-*` mechanism, this section covers the
SELECT itself and its menu rows (not previously traced):

| Handle | main | automation/testids |
|---|---|---|
| The Configuration select's own combobox (`Select.SingleSelect`'s `data-testid` prop + `SelectDisplayProps` `-combobox` mechanism) | `data-testid` prop plumbing exists, but the `SelectDisplayProps` line specifically is testids-only | ✓ |
| `SingleSelectMenuItem.jsx`'s `option.testId ?? select-option-${value}` fallback (covers ALL non-action menu rows, e.g. Saved-credential rows) | ✓ (file identical on both branches) | ✓ |
| `SingleSelect.jsx`'s `variant === 'action'` MenuItem (the CREATE-section rows, "New private/project … credentials") | **no testid on EITHER branch** — genuine unaddressed gap | **no testid on EITHER branch** |

**Takeaway:** the Configuration-select combobox itself and the whole
`toolkit-field-${k}-*` dynamic family are testids-only (awaiting human
promotion) — expected, not a new gap, consistent with this digest's existing
table above. The CREATE-section action rows are a genuine gap on BOTH
branches — needs `add-data-testid` in `SingleSelect.jsx` +
`CredentialsSelect.jsx` (see ELITEA-1976 AFS Concrete Handles for the exact
two-part fix: thread a `testId` prop through `CredentialsSelect` →
`optionGroups` → `SingleSelect`'s action-variant `<MenuItem
data-testid={option.testId ?? ...}>`). Saved-credential rows already have a
working, on-main fallback testid via `SingleSelectMenuItem.jsx` — no code
change needed, just compute the JSON-shaped value
(`select-option-{"kind":"saved","elitea_title":"<title>","private":<bool>}`).

## Dynamic testid naming convention for this surface

`toolkit-field-${k}-select` / `-select-create-private` / `-select-create-project`
/ `-select-refresh-button`, where `k` is the schema's configuration field key
(`gitlab_configuration`, `github_configuration`, `jira_configuration`, …) —
one `ToolBaseProperty.jsx` call-site edit (pass `testId={`toolkit-field-${k}-select`}`)
covers every toolkit type through the shared component, no per-type
special-casing.

---

# Surface digest addendum: Toolkit detail/edit page — Save gate + credential-warning modal (GAP-068)

Written during GAP-068 analysis (2026-07-24). Covers `/toolkits/all/{id}`
(`ToolkitDetailPage`/`EditToolkit.jsx`/`ToolkitsTabBar.jsx`) and the
credential-swap-confirmation feature
(`src/[fsd]/entities/credential-warning/`).

## Project permission map (this identity, confirmed live 2026-07-24)

| Project id | Name | Type | Create rights (this identity) |
|---|---|---|---|
| 399 | Private | personal | full (own project) |
| 1 | (public) | public | n/a — `VITE_PUBLIC_PROJECT_ID=1` |
| 400 | UI Testing | team (`isTeam=true`) | **full** — `configurations.configuration.create` + `models.applications.tools.create` both present. Use this project for any case needing team-project write access. |
| 471 | Elitea Testing Team | team | **viewer-only** — confirmed 403 on both permissions above (already documented in this file's ELITEA-1976 addendum) |
| 406 | Bugs & Features | team | **viewer-only** — 403 on `configurations.configuration.create` |
| 25 | Elitea Development | team | **viewer-only** — 403 on `configurations.configuration.create` |

**Takeaway: project `400` ("UI Testing") is the correct team-project fixture
target for this identity** — it was empty (0 toolkits, 1 unrelated credential)
before this run and is the only non-personal project confirmed writable.
Don't default to 471 just because earlier AFS explored it read-only.

## Toolkit edit page — Save is gated by a LIVE backend connectivity check, not just form validity

`ToolkitForm.jsx` fires `useValidateToolkitQuery({toolkitId, projectId}, {skip:
!editToolDetail?.id || !selectedProjectId || !isEditing})` on every EDIT-mode
load (creation mode has no `id` yet ⇒ **always skipped**). Its endpoint —
`GET /elitea_core/toolkit_validator/prompt_lib/{project}/{toolkitId}` — attempts
a REAL connection using the toolkit's PERSISTED credential and returns `400`
with a `settings_errors[].msg` (`__connection_errors__` blob) on failure,
regardless of the credential type's own `check_connection_supported` schema
metadata (confirmed `false` for `gitlab`, check still ran). This `isError` feeds
`serverToolErrors` → `hasErrors` → `EditToolkit.jsx`'s `hasValidationErrors` →
`ToolkitsTabBar.jsx`'s `shouldDisableSave` — **`toolkit-detail-save-button` stays
disabled for the toolkit's entire life until its persisted credential
authenticates**, independent of anything else in the form (confirmed: editing
Description alone does NOT clear it; swapping the in-form credential dropdown to
a DIFFERENT saved credential does NOT clear it either, because the query is
keyed only on `toolkitId` — it reflects the OLD persisted credential until an
actual save round-trip happens, which itself can't happen while Save is
disabled — a real chicken-and-egg the automation needs a genuinely-valid
credential to break).

**No credential-bearing toolkit type can pass this check in the current DEV
deployment** — see [elitea-testing-public#1032](https://github.com/EliteaAI/elitea-testing-public/issues/1032)
for the full breakdown (GitHub blocked by #999, Jira missing `JIRA_BASE_URL`,
GitLab/Bitbucket have zero token test data). **Any future case needing an
ENABLED Save on an edit-mode credentialed toolkit is blocked by this same root
cause** — check #1032's status before re-deriving this from scratch.

`toolkit-form-save-button` (the CREATE-mode Save/Create button — a DIFFERENT
testid from `toolkit-detail-save-button`) is NOT subject to this gate at all
(query skipped in creation mode) — confirmed live: created a GitLab toolkit
with a deliberately-invalid credential pre-selected, Save stayed enabled
throughout, toolkit persisted successfully. Re-entering edit mode on that same
toolkit immediately showed the gate active (`toolkit-detail-save-button.disabled
=== true`) — the create→edit transition is exactly where this behavior flips.

## Credential-warning modal (`useCredentialWarning` / `CredentialWarningModal.jsx`) — zero testids, feature otherwise fully legible

Source fully read (`src/[fsd]/entities/credential-warning/`): `checkBeforeSave`
gates on `!isCreating && isTeamProject && hasCredentialConfigChanged(...)` —
guard fires ONLY on Save-click (confirmed live: swapping the credential
dropdown selection alone never shows "Credential Configuration Change" text
anywhere on the page). `hasCredentialConfigChanged`/`revertCredentialFields`
(`credentialWarning.helpers.js`) are pure functions diffing
`settings[key].elitea_title`/`.private` between Formik's current `values` and
`initialValues` — no hidden async branching.

**Confirmed missing on BOTH `main` and `automation/testids`** (fresh
`git fetch origin` this session): `CredentialWarningModal.jsx` renders its
`BaseModal` + two `Button.BaseBtn`s with **zero `data-testid` props at all** —
needs `add-data-testid` for `credential-warning-modal` /
`credential-warning-confirm-button` / `credential-warning-discard-button`
regardless of which toolkit type eventually unblocks live verification.

**Second call site, not yet explored**: `src/pages/NewChat/ToolkitEditor.jsx`
also wires `useCredentialWarning` (an agent/pipeline-attached toolkit editor,
distinct from the standalone `/toolkits/all/{id}` page this addendum covers) —
its own `editToolDetail`/`originalDetails`/`revertCredentialsRef` plumbing has
NOT been verified live; don't assume it behaves identically without checking.

## Credential-select dropdown — the case-text's "needs a new testid" claim was wrong; reuse the existing dynamic pattern

GAP-068's own case text proposed adding a new generic `credential-select-dropdown`
testid. **Don't** — the per-type dynamic testid documented earlier in this file
(`toolkit-field-${k}-select` / `-select-combobox`, e.g.
`toolkit-field-gitlab_configuration-select-combobox`) already covers this
exact element and is confirmed live on `automation/testids` (not yet on `main`).
Adding a second, differently-named testid on the same element would be
redundant and would corrupt the coverage metric (two testids, one element).
