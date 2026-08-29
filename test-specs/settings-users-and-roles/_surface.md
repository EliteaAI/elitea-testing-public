# Surface digest — Settings → Users and Roles

Confirmed live 2026-08-05 against `http://localhost:5173` (EliteaUI
`automation/testids`, DEV backend, project "UI Testing" / `${ELITEA_PROJECT_ID}`
= 400). One writer at a time — see `test-case-analysis` § 2b for the
update contract.

## Route
- `/settings/users` (bare path, reachable directly — same pattern as
  `/settings/tokens`, `/settings/notifications`).
- Route registered `src/[fsd]/app/routes/ProtectedRoutes.jsx:359-362` →
  `<Users />` (`src/[fsd]/pages/settings/Users.jsx`).

## Component tree
- `Users.jsx` (page) → `DrawerPage` + `DrawerPageHeader` (shared header:
  title/search/add-button) + `extraContent` (`EditUsersButton` batch-edit,
  `DeleteUserButton` batch-delete) + `UsersTable`.
- `UsersTable.jsx` → shared grid-table primitives:
  `GridTableContainer`/`GridTableHeader`/`GridTableBody`/`GridTableRow`/
  `GridTablePagination` (same stack `TokensTable.jsx`/`SecretsTable.jsx`
  use) + per-row `EditUsersButton`/`DeleteUserButton` (same components as
  the header, different props: no `isBatchEdit`/`useSecondaryButton`).
- Columns (`USERS_COLUMNS`, `UsersTable.jsx`): `name` (sortable), `email`
  (sortable, hides <600px), `last_login` (sortable, hides <800px), `roles`
  → label "Role" (not sortable, hides <1000px), `actions` (not sortable).
  `name` and `actions` are rendered OUTSIDE `GridTableRowDataCell` (name via
  `GridTableRowNameCell`, actions via `GridTableRowActionsCell`) — only
  `email`/`last_login`/`roles` go through `GridTableRowDataCell`.

## Testid state (as of 2026-08-05 exploration)
**Zero testids exist in this component tree today** (`Users.jsx`,
`UsersTable.jsx`, `EditUsersButton.jsx`, `DeleteUserButton.jsx` — confirmed
via grep, no hits). BUT the shared `DrawerPageHeader.jsx`/`GridTableHeader.jsx`/
`GridTableRow.jsx`/`GridTableRowNameCell.jsx` components already carry
testid-prop plumbing (added for `PersonalTokensPage`'s ELITEA-2277 work) —
most of this surface's testids are **call-site-only** additions, no shared
component edit needed:

| Prop (shared component) | Already wired? | Generates |
|---|---|---|
| `DrawerPageHeader.titleTestId` | yes | `data-testid` on header `Typography` |
| `DrawerPageHeader.slotProps.searchInput.testId` | yes | `data-testid` on `SimpleSearchBar` |
| `DrawerPageHeader.slotProps.addButton.testId` | yes | `data-testid` on add `IconButton` |
| `GridTableHeader.selectAllCheckboxTestId` | yes | `data-testid` on select-all checkbox |
| `GridTableHeader.columnTestIdPrefix` | yes | `{prefix}-column-header-{field}` per column |
| `GridTableRow.'data-testid'` | yes | `data-testid` on the row `Box` |
| `GridTableRow.checkboxTestId` | yes | `data-testid` on row checkbox |
| `GridTableRow.nameCellTestId` | yes | `data-testid` on the name cell |
| `GridTableRowDataCell` (email/last_login/roles) | **NO — no testid prop of any kind** | needs new `dataCellTestIdPrefix` prop threaded `GridTableRow` → `GridTableRowDataCell`, mirroring `columnTestIdPrefix`'s `{prefix}-column-header-{field}` shape as `{prefix}-column-value-{field}` |
| `EditUsersButton` / `DeleteUserButton` (feature components, used both header-batch and per-row) | **NO** | needs a new `testId` prop on each, `data-testid={testId}` on the `IconButton` — used TWICE per component (header instance + row instance), each needs its own testid value passed at its own call site |

## Live data observed
- 2 users in project 400 ("UI Testing"): `Levon Dadayan`
  (`levon_dadayan@epam.com`, role `admin`, last_login
  `2026-08-04T11:00:34`), `Test Bot` (`testbot@elitea.ai`, role `admin`,
  last_login `2026-08-05T00:05:24`). This floor is self-guaranteed — the
  acting admin is always a project member — unlike personal-tokens'
  deletable-data risk.
- Last-login format: `YYYY-MM-DDTHH:MM:SS`, no timezone offset/millis, on
  this build.
- Driving fetches: `GET /api/v2/admin/users/default/{projectId}?limit=20&offset=0`,
  `GET /api/v2/admin/roles/default/{projectId}?limit=20&offset=0` — both
  200 OK, fire on every page mount (`refetchOnMountOrArgChange: true`).

## Gotchas
- `EditUsersButton`/`DeleteUserButton` are DUAL-USE components — rendered
  once in the page header (`isBatchEdit`/`useSecondaryButton`, disabled
  until a row is selected) and once per row (plain instance). A future
  testid prop addition must thread a distinct value at EACH call site, or
  header and row instances collide on the same testid.
- Header batch Edit/Delete buttons are correctly DISABLED on initial page
  load (`disabled={!selectedUsers.length}`) — don't assert `is_enabled()`
  there, assert `is_disabled()`. Note (ELITEA-2304): the enabling condition
  is ANY non-empty selection (`disabled={!selectedUsers.length}`), not
  specifically "two or more" — a single selected row already enables it.
- The case source text's per-step "Expected Result" column is largely
  generic/templated boilerplate ("Action completes without error and
  produces the expected UI state" repeated across ~10 rows) — don't treat
  it as literal per-element intent; the live component behavior is the
  ground truth (see ELITEA-2292 AFS § Axis 2 for the worked example on the
  header Delete button).
- **Project-topology constraint (ELITEA-2304, critical for any write-flow
  case on this surface): the acting test account (`testbot@elitea.ai`) has
  `admin` role, and therefore the header/row Edit-Delete UI at all, ONLY in
  project 400 ("UI Testing").** Confirmed live across every other project
  reachable from the sidebar selector — `Elitea Testing Team` (471, 15
  users), `Bugs & Features` (406, 29 users), `Elitea Development` (25, 23
  users) — Test Bot holds `viewer` (or isn't listed on page 1) in all three,
  and the Users page renders **no** batch-Edit/Delete buttons and **no**
  per-row action icons at all there (permission-gated out entirely, not
  merely disabled). Any case needing 3+ safely-mutable users for a
  write-flow (this surface's only write-capable project has exactly 2,
  one of which is the acting account) must seed disposable users via
  "Invite users" rather than relying on existing project-471/406/25 data —
  those projects are unreachable for mutation regardless of user count.
- **Inviting a user works instantly for edit/delete purposes, no
  acceptance needed** (ELITEA-2304): a freshly-invited row appears
  immediately in the table with Name = the invited email, Last login =
  `-`, the selected initial role, and full row-level Edit/Delete actions —
  confirmed live, no login/acceptance step required. Safe, fast seed
  mechanism for any case needing extra mutable user rows on this surface.
- **Edit-roles dialog (`EditUserRolesDialog.jsx`, shared by both the header
  batch-edit and per-row edit instances) had ZERO testids before ELITEA-2304**
  — confirmed via full-file read. Added: `dialogTestId`/`titleTestId` (thread
  onto `Modal.BaseModal`'s pre-existing `data-testid`/`titleTestId` props),
  `roleSelectTestId` (thread onto `Select.SingleSelect`'s pre-existing
  `data-testid` prop — auto-generates a `-combobox` suffix testid too, per
  `SingleSelect.jsx`'s existing `SelectDisplayProps` logic), and
  `saveButtonTestId` (new `data-testid` on the dialog's own custom Save
  `Button.BaseBtn` — this dialog passes a custom `actions` node to
  `BaseModal`, so `BaseModal`'s own `confirmButtonTestId`/`onConfirm`
  mechanism is bypassed and doesn't apply). Wired ONLY at `Users.jsx`'s
  header (`isBatchEdit`) `EditUsersButton` call site — the per-row instance
  in `UsersTable.jsx`'s `renderActions` still has no dialog testids (no
  case has exercised the row-level edit dialog yet).
- Role-select options (`admin`/`editor`/`viewer`) need NO new testid work —
  `SingleSelectMenuItem.jsx` unconditionally renders
  `data-testid={option.testId ?? 'select-option-' + option.value}` on every
  menu item regardless of grouped/flat mode, and `Users.jsx`'s
  `rolesOptions` already maps `{label: name, value: name}` — so
  `select-option-admin`/`-editor`/`-viewer` are live for free, same
  mechanism the project selector and Invite-users dialog already use.
- Batch-edit-roles driving request: `PUT /api/v2/admin/users/default/{projectId}`,
  response body `{"msg": "roles updated"}`, 200 OK — single call for however
  many users are selected (not one call per user).
- Per-user delete (row-level, used for cleanup of seeded users):
  `DELETE /api/v2/admin/users/default/{projectId}?id[]={user_id}` → `204 No
  Content`. Confirmation dialog is the generic `Modal.DeleteEntityModal`
  (testid `delete-confirm-button`, pre-existing, shared with other delete
  flows on this surface and elsewhere).

## AFS on file
- `l2_users-page-layout-and-components_ELITEA-2292.md` — page layout +
  header components + table columns/sortability + row content shape.
- `l2_batch-edit-roles-for-multiple-selected-users_ELITEA-2304.md` —
  header batch-edit-roles flow: select 2+ rows → header Edit enables →
  "Edit roles" dialog → select role → Save → selected rows update,
  unselected rows provably unchanged. Introduced the `users-edit-roles-*`
  dialog testids (see Gotchas above) and the seed-2-disposable-users
  pattern for write-flow cases on this surface.
- `l3_invite-user-invalid-email-validation_ELITEA-2307.md` — Invite-users
  dialog client-side email-format validation (no invite ever submitted).

## Confirmed handles (as of ELITEA-2307 analysis, 2026-08-05)

`InviteUserDialog.jsx` (`src/components/InviteUserDialog.jsx`) source-read +
live-confirmed:

- **Validation is BLUR-gated, not live-as-you-type.** `onChange={handleChange}`
  only updates the `emails`/`inputText` state; `onBlur={handleBlur}` is what
  calls `parseEmails()` and sets `error`/`helperText`. Typing `notanemail` or
  `user@` alone shows NO error (live-confirmed, snapshot right after
  `.fill()`); pressing `Tab` immediately surfaces
  `Invalid email: {email}` as a `<FormHelperText>` paragraph directly below
  the Emails field. Same "touched"-gating family as the Artifacts bucket-name
  form above — don't assert right after fill, blur first.
- Error text: exact, deterministic `Invalid email: {email}` — built by
  `validateEmails()` in the same file (regex-based, one shared prefix, emails
  joined by `, ` when multiple are invalid).
- **Error `<FormHelperText>` has ZERO testid today** — confirmed via
  `document.querySelectorAll('p')` filter live: `class="MuiFormHelperText-root
  Mui-error MuiFormHelperText-sizeSmall css-..."`, `data-testid: null`.
  `testid needed: users-invite-emails-error-text` — thread a new
  `emailsErrorTestId` prop the same way `emailsInputTestId` already threads
  (`Users.jsx`'s `InviteUserDialog` call site), landing on the
  `<FormHelperText>` node itself (a NEW prop — unlike `emailsInputTestId`,
  which uses `inputProps` to reach the nested `<textarea>`, this one is a
  direct prop on the JSX element being tagged, no `slotProps` indirection
  needed).
- Invite (confirm) button (`users-invite-confirm-button`, pre-existing) stays
  disabled while `error` is true (`disabled={!emails.length ||
  !selectedRoles.length || error}`) — no request ever fires for an
  invalid-email attempt; don't reuse `AdminUsersPage.invite_users()` (it
  awaits a POST response) for this path.

---

## Update — settings-w09 (ELITEA-2293/2294/2295/2305/2308), 2026-08-29

Confirmed live against `http://localhost:5173` (EliteaUI `automation/testids`,
DEV backend, project 400 "UI Testing").

### Live data drift since 2026-08-05
Project 400 now holds **4** user rows, not 2:

| Name | Email | Last login | Role |
|---|---|---|---|
| Levon Dadayan | levon_dadayan@epam.com | `2026-08-29T10:29:17` | admin |
| Test Bot | testbot@elitea.ai | `2026-08-29T14:02:40` | admin |
| *(blank)* | elitea-batch-edit-test2-70fda701@example.com | `-` | viewer |
| *(blank)* | elitea-batch-edit-test2-45c8fb8d@example.com | `-` | editor |

The last two are **orphaned seed users from an earlier ELITEA-2304 run whose
cleanup did not complete** (reported as a finding). Consequences for anyone
writing tests here:
- **Never hardcode a row count, a name, an email or a datetime.** Derive every
  expectation from the rendered table at runtime.
- The set exercises BOTH null branches usefully — a blank Name renders as an
  **empty string** in `user-row-name`, while a null last login renders as the
  literal **`-`** in `user-column-value-last_login`. Two different null
  renderings on the same table.

### Sorting (ELITEA-2293) — confirmed live
- Engine is the shared `useTableSort` (`entities/grid-table/lib`), same as
  Personal Tokens / Secrets. `defaultField: 'name'`, `defaultDirection: 'asc'`.
- **The table arrives ALREADY name-ascending**, so the FIRST click on Name
  flips to **descending** and the second returns to ascending. The case text
  (ELITEA-2293 steps 2-4) claims the opposite — stale case text, product is
  correct. Filed as a **sibling of #1880** (byte-identical pattern on the
  Personal Tokens table).
- Switching to a DIFFERENT field always starts at `asc`
  (`prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc'`), so the
  first Email click and the first Last-login click are both ascending.
- **Null placement is part of the contract**: nulls sort LAST ascending, FIRST
  descending. Live-verified on both the blank-Name and blank-last-login rows.
- Sorting is **client-side** — no request fires on a header click, and the row
  count is invariant across every click.

### Search (ELITEA-2294) — confirmed live
- Client-side, per keystroke, no debounce, no Enter, no submit control
  (`SimpleSearchBar` -> `Users.jsx`'s `filteredUsers` memo over the cached array).
- **The matching rule has THREE arms** (`Users.jsx:82-92`): a row matches when
  the lower-cased term is a substring of its **email OR name OR joined roles**.
  A runtime-derived probe must compute expected matches with the same three-arm
  rule — an email-only derivation will over- or under-predict whenever the probe
  is also a substring of `admin`/`editor`/`viewer`.
- Placeholder is exactly `"Search "` (trailing space).
- `ControlOrMeta+a` + `Backspace` clears the field reliably (plain MUI
  `InputBase`, no auto-blur wrapper) — same technique as `PersonalTokensPage`.
- Clearing restores the full set; sort order is orthogonal and survives a clear,
  so compare **sets**, not ordered lists, on the restore assertion.

### ⚠️ `select-option-` prefix is NOT a safe option count (new, important)
`SingleSelect` renders a checkmark carrying **`select-option-selected-icon`**
next to the currently-selected option — and a naive
`[data-testid^="select-option-"]` count matches it. Live evidence from the
**row-Edit** dialog with `admin` preselected:

```
['select-option-admin', 'select-option-selected-icon', 'select-option-editor', 'select-option-viewer']   # 4, not 3
```

The Invite dialog opens with nothing selected, so the naive count *happens* to
be right there — which is exactly how this trap stays hidden until a case
touches a preselected select. Use the exclusion form:

```python
ROLE_OPTION_ANY_SELECTOR = '[data-testid^="select-option-"]:not([data-testid="select-option-selected-icon"])'
```

Also note the prefix is **globally shared** (project selector, page-size
select, …). It is only unambiguous because MUI mounts one menu at a time and
unmounts options on close (live-verified: 0 mounted options with every menu
closed).

### Invite-users dialog (ELITEA-2295 / 2308) — confirmed live
- Exact texts: title `"Invite users"`; description
  `"Enter user emails(separated by comma) and select roles to define permissions for this project."`
  (verbatim, note the missing space before the parenthesis); Emails label
  `"Emails *"` — **the trailing `*` IS the required marker** (MUI writes the
  asterisk into the `<label>` when `required` is set).
- The Invite button's gate is `disabled={!emails.length || !selectedRoles.length || error}`
  — **three independent OR'd conditions**. Asserting only "disabled" proves
  nothing about which one fired. Any case about one gate must isolate it: enter
  a VALID email (so `error` is false), then show the button ENABLES once a role
  is selected. Live-verified: valid email + no role -> disabled; select `viewer`
  -> enabled.
- The Roles combobox renders a **zero-width space** (`​`) when nothing is
  selected — not an empty string.
- Close (×) dismisses the dialog with no request and no side effect.
- Opening/closing the dialog fires **no** request at all.

### New testids added (EliteaAI/EliteaUI@8f559586, 2026-08-29)
All purely additive prop threading onto existing nodes/props — 17 insertions,
0 deletions, no new DOM node, no new hook.

| Testid | Where | How |
|---|---|---|
| `users-invite-dialog` | `InviteUserDialog.jsx` -> `Users.jsx` | new `dialogTestId` prop -> `BaseModal`'s already-supported `data-testid` |
| `users-invite-title` | same | new `titleTestId` prop -> `BaseModal.titleTestId` |
| `users-invite-close-button` | same | new `closeButtonTestId` prop -> `BaseModal.closeButtonTestId` |
| `users-invite-description` | same | new `descriptionTestId` prop on the existing description `Typography` |
| `users-invite-emails-label` | same | new `emailsLabelTestId` prop -> `StyledInputEnhancer`'s already-supported `InputLabelProps` |
| `users-row-edit-roles-dialog` | `UsersTable.jsx` `renderActions` | **call-site only** — `EditUsersButton` already accepted `dialogTestId`; only the HEADER batch-edit instance had been wired (ELITEA-2304) |
| `users-row-edit-roles-select` | same | **call-site only** — `roleSelectTestId`; `SingleSelect` auto-appends `-combobox` |

`BaseModal` already supports `data-testid` / `titleTestId` / `closeButtonTestId`
/ `confirmButtonTestId` / `cancelButtonTestId` — **any dialog built on it needs
only a pass-through prop, never a shared-component edit.** Check that first
before proposing new plumbing for a modal on this codebase.

### Row-level Edit-roles dialog (ELITEA-2305)
- Now addressable: `users-row-edit-roles-dialog` +
  `users-row-edit-roles-select-combobox`. Title / Save / Cancel are still
  **unwired at the row call site** (canon #511 — no case exercises them yet).
- **`Escape` dismisses the dialog** (`BaseModal`'s own `handleKeyDown` calls
  `onClose`). Inside an OPEN roles menu the first `Escape` is consumed by the
  MUI Menu and the dialog stays open — so it is two `Escape` presses from
  "menu open" to "dialog closed". Live-verified, role left unchanged.
- Save stays disabled until a role actually changes, so a read-only visit is
  inherently non-destructive.

### AFS added by this wave
- `l2_users-table-columns-are-sortable_ELITEA-2293.md`
- `l3_users-page-search-filters-the-table-in-real-time_ELITEA-2294.md`
- `l3_invite-users-dialog-opens-with-correct-layout_ELITEA-2295.md`
- `l3_available-roles-in-invite-and-edit-dialogs_ELITEA-2305.md`
- `l3_invite-user-without-selecting-a-role_ELITEA-2308.md`

### Resolved/added during settings-w09 implementation (2026-08-29)

**1. `AdminUsersPage.navigate()`'s project switch was RACY — fixed.**
`ensure_team_project_selected()` waited only on `wait_for_network()`
(`networkidle`), which this app's always-open Socket.IO polling transport makes
a poor proxy for "the switch landed" (the shared `#1847` mechanism). The
following `navigate("/settings/users")` then lost the race against
`Settings.jsx`'s `isPrivateProject` guard and was redirected straight back to
`/settings/project-general` — producing a zero-row page and a mystifying
"`user-row` never became visible" timeout 10 s later. Diagnosed from a failure
screenshot still showing **"Project: Private" / "Project ID: 399"**; it cost
**3 of 10 invocations** in one session before the fix.

The method now waits on the product's own switch signals — the two
project-scoped GETs keyed by the **new** project id, live-captured:
- `GET /api/v2/elitea_core/project_info/prompt_lib/{id}/project-info` (what the
  guard reads)
- `GET /api/v2/auth/permissions/prompt_lib/{id}` (what gates the Users page's
  controls)

and the trailing `wait_for_network()` was **removed** — it was `#1847` itself
(observed timing out raw at 15 s once in an 8-spec run). After the fix: 8 specs,
**8/8 passed, `reruns.json == {}`**, and the run got ~56 s faster.

**2. The selected-option checkmark is a testid-only "is this already active?"
probe.** `SingleSelect` renders `select-option-selected-icon` INSIDE the
currently-selected option, so
`option.locator('[data-testid="select-option-selected-icon"]').count()` answers
"is project N already selected?" without needing the project's display name.
`ensure_team_project_selected` uses it to short-circuit — re-selecting an
already-active project fires no request, so the response wait above would
otherwise hang. Same fact, opposite use, as the option-count trap noted above.

**3. MUI required-field labels carry TWO asterisks — assert innerText.**
`users-invite-emails-label`'s node is:

```html
<label ...><div><span>Emails *</span></div>
  <span aria-hidden="true" class="MuiFormLabel-asterisk" style="display:none"> *</span></label>
```

`StyledInputEnhancer` renders the visible `Emails *` itself AND MUI adds its own
hidden asterisk span. Playwright's `to_have_text` compares **textContent** by
default, which concatenates both into `"Emails * *"`. Use
`to_have_text("Emails *", use_inner_text=True)` — the visible text is the
observable a layout case means. Expect the same trap on any other `required`
field wired through `StyledInputEnhancer`.

**4. Console-noise ledger: the 404 flavor's URL is finally captured.**
`test_users_search_filter` failed one attempt on the recurring unrelated-resource
console error — and because these specs use `utils/console_errors`, the message
carried the resource:

```
error: Failed to load resource: the server responded with a status of 404 (Not Found)
       @ http://localhost:5173/api/v2/elitea_core/toolkits/prompt_lib/
```

Note the **trailing slash with no project id** — the app requests
`toolkits/prompt_lib/` (project id missing) during a project transition, which
404s. That contradicts the long-standing "suspected static font/icon asset"
theory in `.agents/testing.md`: it is an API call with a malformed path. Not
reproduced on the immediate rerun. Recorded in `.agents/testing.md`'s ledger too.

**5. Orphaned seed users.** Project 400 carries two leftover
`elitea-batch-edit-test2-*@example.com` rows from an ELITEA-2304 run whose
cleanup did not complete. Harmless for read-only cases (and useful — they supply
the null-name / null-last-login branches), but they mean **no test on this
surface may hardcode a row count or a user identity.**

**6. Console-error assertions on this surface must exclude #1971.** The project
switch `AdminUsersPage.navigate()` performs reopens EliteaUI's `toolkitTypes`
project-id race, so a project-id-less `GET .../elitea_core/toolkits/prompt_lib/`
404 lands in the console on roughly half of full-suite runs. Filed as **#1971**
(regression of the closed #554). All five settings-w09 specs exclude that ONE
exact URL via `utils.console_errors.exclude_known_defect_urls` with a
`# Known defect: #1971` comment — URL-keyed, never status-code-keyed. Any new
spec on this surface will hit it too.

---

## Update — settings-w09 invite write-flows (ELITEA-2296/2297/2309), 2026-08-29

Confirmed live against `http://localhost:5173` (EliteaUI `automation/testids`,
DEV backend, project 400 "UI Testing"). Six disposable users were invited and
deleted during this exploration; the table was left exactly as found (the same
4 rows the wave-1 update lists).

### The invite SUBMIT path — three outcomes, all live-observed

| Flow | POST `…/admin/users/default/400` | Toast severity | `toast-message` text | Table delta |
|---|---|---|---|---|
| 1 email | **200 OK** | `success` | `The user has been invited` | +1 row |
| 2 comma-separated emails | **200 OK** (ONE call, not one per address) | `success` | `The users have been invited` | +2 rows |
| email already a member | **400 Bad Request** | `error` | `user <email> already exists in project 400` | **+0 rows** |

- Singular/plural is `Users.jsx:181` — `emailCount > 1 ? 'The users have been
  invited' : 'The user has been invited'`. Both observed, not inferred.
- The duplicate-invite error text embeds the **project id**, so a test must
  build it from `settings.users_team_project_id`, never a literal `400`.
- **The dialog closes on the 400 too** — a failed invite discards the typed
  input. Not a filed defect (no case asserts it); recorded so nobody re-derives
  it.
- An invited row appears immediately with Name = **empty string**, Last login =
  literal `-`, and the selected role — reconfirming the wave-1 note, now on the
  invite path specifically.

### ⚠️ The success toast auto-hides after 3 s — assert it FIRST

`TOAST_DURATION_DEFAULTS` (`src/common/constants.js:345`): `success`/`info`
**3000 ms**, `warning` 7000, `error` **10000**. This is short enough that
**three consecutive Playwright-MCP round-trips all missed the success toast
entirely** during this exploration (each click→evaluate pair costs >3 s), which
reads exactly like "the product shows no confirmation". It does. Capturing it
needed a DOM `MutationObserver` recording `toast-alert` appearances:

```js
window.__toastLog = [];
new MutationObserver(() => document.querySelectorAll('[data-testid="toast-alert"]')
  .forEach(a => window.__toastLog.push({severity: a.getAttribute('data-severity'),
    msg: a.querySelector('[data-testid="toast-message"]')?.innerText})))
  .observe(document.body, {childList: true, subtree: true, characterData: true});
```

**Reusable technique for ANY short-lived toast on this product when driving the
UI through MCP.** In a pytest spec the same fact means: assert the toast in the
step right after the driving response resolves, before any table read.

Toast handles are all pre-existing and shared (`src/components/Toast.jsx`):
`toast-alert` (+ `data-severity`), `toast-message`, `toast-dismiss-button`.
**No testid work is needed for any invite-confirmation case.**

### Batch delete works for multi-row cleanup, with a caveat
Selecting N row checkboxes → header `users-header-delete-button` →
`delete-confirm-button` deletes all N in one confirm (toast:
`The user user has been successfully deleted.` — sic, doubled word). During the
post-delete refetch the table transiently renders **0 rows** and the console
fills with errors from the cancelled in-flight queries; a plain reload settles
it. Specs should prefer the per-row `delete_user_row()` teardown ELITEA-2304
established — this is a note about manual exploration, not a recommended
teardown shape.

### AFS added by this wave
- `l3_invite-users-single-and-multiple_ELITEA-2296.md` — **family AFS**
  (ELITEA-2296 + ELITEA-2297), one parameterized spec, a row per case.
- `l3_invite-existing-project-member-shows-error_ELITEA-2309.md`.

### Resolved/added during ELITEA-2296/2297/2309 implementation (2026-08-29)

- **`AdminUsersPage` gained four additive members** for the invite write-flows:
  `toast_alert` / `toast_message` + `TOAST_ALERT_SEVERITY` +
  `get_toast_by_severity()` (all pre-existing product-wide `Toast.jsx` testids,
  no UI change), `get_name_cell_for_row()` / `get_last_login_cell_for_row()`
  (row-scoped siblings of `get_role_cell_for_row()`), and **`submit_invite()`**
  — clicks Invite and returns the driving POST *whatever its status*, which is
  what lets ELITEA-2309 assert the 400. `invite_users()` is unchanged and still
  the one-shot seeding helper.
- `type_email_in_invite_dialog()` accepts the **raw** Emails-field text, so a
  comma-separated multi-address string goes straight in — no new method needed
  for ELITEA-2297.
- `pages/admin_users_page.py` carried a **pre-existing** ruff `I001` import-sort
  error on the wave trunk (masked from `ruff check --stdin-filename`, which does
  not report I001 — see the qa-engineer note from the previous unit). Fixed here
  with `ruff check --fix`. **If you need to lint a file's imports, check the
  file on disk, never via stdin.**
- Unit ran **green 3/3 on the first invocation** (57.31 s, `reruns.json == {}`)
  — no flake surfaced on this surface's write path today.
