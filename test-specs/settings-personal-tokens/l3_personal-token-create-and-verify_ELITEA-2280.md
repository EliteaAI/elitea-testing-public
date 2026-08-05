# Test Case: Create a new personal token and verify it appears in the table

## Metadata
- **TMS ID**: ELITEA-2280
- **Source case**: `.agents/automation/elitea-2280-personal-token-create/cases/ELITEA-2280.md`
  (snapshot; TMS module `settings-personal-tokens`)
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter `priority: medium`). **pytest
  marker: `@pytest.mark.p2`** — same TMS `medium` → AFS `l3_` → pytest `p2`
  convention as ELITEA-2277 (`.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost dev-token auth).
- Active project is `${ELITEA_PROJECT_ID}` (399, "Private") — same project used
  by ELITEA-2277; not required to be non-Public/model-configured for THIS case
  (the `showDownload` icon-count gating from ELITEA-2277 doesn't affect token
  creation), but reusing the same project keeps the two cases' page-object
  usage consistent.
- No precondition on existing token data — this case **creates its own token**
  and is unaffected by whether the table starts empty or populated (unlike
  ELITEA-2277, which needs ≥1 pre-existing row to avoid the `EmptyStatePage`).

## Test Data
### generated-per-run
- Token name: a run-unique value, e.g. `f"autotest-token-{uuid4().hex[:8]}"`
  — **do not hardcode a literal `"autotest-token"`** (the case text's literal
  example). Confirmed live: the create page's Formik `validationSchema` only
  rejects non-`[a-zA-Z0-9_-]` characters and empty names
  (`CreatePersonalToken.jsx` `TOKEN_NAME_PATTERN`) — it does **not** reject a
  duplicate name against another live token, so a hardcoded literal risks
  colliding with real leftover data (`for_ui_tests`, `Levon`, `Marian`, `New`,
  `uautomate` — none currently named exactly `autotest-token`, but a fixed
  literal is also non-idempotent across repeated CI runs of this same test
  before cleanup completes). A per-run-unique name removes both risks and
  keeps the created row unambiguously identifiable for the row-scoped
  assertions and for cleanup.
- Expiration: unit `Days` (`EXPIRATION_MEASURES[1]`, confirmed
  `src/common/constants.js:485`), value `30` — **this is the page's own
  default** (`DEFAULT_TOKEN_EXPIRATION_DAYS = 30`, `constants.js:484`,
  `measure: EXPIRATION_MEASURES[1]` in `CreatePersonalToken.jsx`'s Formik
  `initialValues`). The case's step 5 ("Set expiration: unit 'Days', value
  '30'") is satisfiable by asserting the pre-filled defaults rather than
  changing them — confirmed live (snapshot showed `combobox "Days"` +
  `spinbutton: "30"` immediately after opening the form, before any
  interaction). Automation should still assert these two default values
  explicitly (not skip the step) since that IS the case's step 5 assertion.

## Test Steps
1. From `${BASE_URL}/settings/tokens` (reuse `PersonalTokensPage.navigate()`
   from ELITEA-2277's page object), click the add-token button (testid
   `personal-tokens-add-button`, already exists).
   - **Verify**: navigation to `${BASE_URL}/settings/create-personal-token`
     (a **route change**, confirmed live — see Known Defects / Case-Text Note
     below: this is NOT an inline dialog opening on the same page, contrary
     to how the case's step 3 phrasing ("a 'New Token' form opens") could be
     read).
2. **Verify** the "New Token" form is showing: page title testid
   `create-personal-token-page-title` has exact text `"New Token"`; Name
   input testid `create-personal-token-name-input` is visible and empty;
   Expiration-period unit select testid
   `create-personal-token-expiration-measure-select` shows `"Days"`;
   Expiration-period value input testid
   `create-personal-token-expiration-value-input` shows `"30"` — confirmed
   live these are the pre-filled Formik defaults, not empty fields.
3. Enter token name (the generated-per-run value from § Test Data) into the
   Name input (testid `create-personal-token-name-input`).
   - **Verify**: the Generate button (testid
     `create-personal-token-generate-button`) transitions from disabled to
     enabled — confirmed live: `isGenerateDisabled` is `true` with an empty
     name and becomes `false` once a valid, non-empty name is entered
     (`CreatePersonalToken.jsx`).
4. **Verify** expiration unit still reads `"Days"` and value still reads
   `"30"` (the case's own step 5 assertion; no interaction needed since these
   are already the defaults per § Test Data — see Coverage Map for why this
   is asserted rather than set-then-asserted).
5. Click Generate (testid `create-personal-token-generate-button`).
   - **Verify**: a `POST /api/v2/auth/token/` request fires and resolves
     `200 OK` (confirmed live via network capture) — side-channel proof the
     create actually happened, not just that the dialog rendered from stale
     client state.
6. **Verify** the "New token generated!" dialog appears: dialog-title testid
   `generated-token-dialog-title` has exact text `"New token generated!"`.
7. **Verify** the dialog's warning testid `generated-token-dialog-warning`
   has exact text `"This token will only be shown once, so make sure to copy
   and save it."`.
8. **Verify** the token-name testid `generated-token-dialog-token-name` (text
   = the entered name) appears **above** the token-value testid
   `generated-token-dialog-token-value` (non-empty JWT-shaped string) in the
   dialog — confirmed live via DOM order (both are siblings inside the same
   `tokenContainer` Box, name first).
9. Click the Copy button (testid `generated-token-dialog-copy-button`).
   - **Verify**: a toast/alert containing exact text `"The token has been
     copied to the clipboard."` appears (confirmed live — `useToast`'s
     `toastInfo` call in `GeneratedTokenDialog.jsx`), AND the Copy button's
     own text changes to `"Copied!"` and becomes disabled (confirmed live;
     reverts after ~5s per `COPY_DISABLED_DURATION` — automation should
     assert the immediate post-click state, not wait for the revert).
   - **Verify (clipboard content)**: `page.evaluate("navigator.clipboard.readText()")`
     returns the same token string shown in
     `generated-token-dialog-token-value` — see Automation Hints for the
     required context permission (`conftest.py` already grants
     `clipboard-read`/`clipboard-write` at context creation, confirmed by
     reading `automation/conftest.py:279`; do **not** attempt this read via
     an ad-hoc Playwright MCP browser context, which lacks the permission
     grant and hangs indefinitely waiting on a permission prompt that never
     resolves — confirmed live, see Known Defects / Gotchas below).
10. Close the dialog by clicking its close (X) icon — testid
    `generated-token-dialog-close-button`.
    - **Verify**: navigation back to `${BASE_URL}/settings/tokens` (confirmed
      live — the dialog's `onClose` prop is wired to `CreatePersonalToken`'s
      `onCancel`, which calls `navigate(-1)`; **pressing Escape triggers the
      same `onClose` and also navigates back** — either is a valid "close"
      interaction per the component's `onKeyDown` handler, but the AFS
      specifies the explicit close-icon click as the primary interaction
      since it doesn't depend on keyboard-focus state).
11. **Verify** a token row (testid `token-row`, scoped via
    `.filter(has_text=<generated name>)`) is present in the tokens table with:
    - Name cell (testid `token-name-cell` within that row) exact text = the
      generated name.
    - Value cell (testid `token-value-cell` within that row) matches the
      masked pattern `"..." + <last 4 chars of the token string captured in
      step 8/9>` — confirmed live rendering logic:
      `'...' + row.token.substring(row.token.length - 4)`
      (`TokensTable.jsx` `renderCell`).
12. **Verify** the Expiration cell for that row: testid
    `token-expiration-status` with `data-expiration-state="active"` (the
    green-icon state — confirmed live: `expiryInDays > 7` renders
    `SuccessIcon` with `theme.palette.status.published` fill, hex `#2BD48D`
    confirmed via computed style), and exact text `"in 30 days"`.
13. **Verify no console error** was raised across steps 1–12 (side-channel
    check — confirmed live: 0 console errors, 0 warnings across this full
    create-and-verify flow).

## Cleanup (MANDATORY — this case creates live data)
This case creates one real personal token under `${ELITEA_PROJECT_ID}` (399).
Unlike ELITEA-2277 (read-only), this case must delete what it created:
1. Click the delete icon for the created row (testid
   `token-action-delete-button`, already exists — scoped via the same
   row-filter as step 11).
2. The confirmation modal (`Modal.DeleteEntityModal`, shared component) opens
   — **all its testids already exist, zero new testid work**: type the exact
   generated name into `delete-confirm-name-input` (required — the modal's
   `shouldRequestInputName` default is `true` and disables the confirm button
   until the typed value matches `name` exactly), then click
   `delete-confirm-button`.
3. **Verify**: the row (filtered by generated name) is no longer present in
   the table.
Confirmed live end-to-end (created `autotest-token-e2280`, deleted it via
this exact flow, table returned to its prior 5-row baseline with 0 console
errors throughout).

## Expected Results
- Clicking "+" navigates to a dedicated "New Token" page (not an inline
  dialog) pre-filled with Name (empty) and Expiration period (Days / 30).
- Entering a name enables Generate; clicking it POSTs the new token and opens
  a "New token generated!" dialog showing the warning text, the token name
  above the full token value, and a Copy button.
- Clicking Copy shows a "copied to clipboard" toast, flips the button to
  "Copied!", and actually places the token string on the OS/browser
  clipboard (verified via `clipboard-read` permission, not just the toast).
- Closing the dialog returns to the tokens table, where the new token appears
  with its name, a masked `...XXXX` value, and an Expiration cell showing
  "in 30 days" with the green (`#2BD48D`) success icon.
- No console errors at any step.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Personal Tokens | Target page/section loads successfully | AFS step 1 (navigate) | reuses `PersonalTokensPage.navigate()` | asserted |
| 2 Click the "+" button | Control responds; expected next state is shown | AFS step 1 | route change to `/settings/create-personal-token` | asserted |
| 3 Verify a "New Token" form opens with: Name field and Expiration period (unit dropdown + numeric value) | Condition holds as described | AFS step 2 | page title + 3 field testids visible | asserted |
| 4 Enter token name "autotest-token" | Field accepts the input and displays the entered value | AFS step 3 | name input value + Generate-button enabled transition | asserted *(generated-per-run name substituted for the literal — see Test Data)* |
| 5 Set expiration: unit "Days", value "30" | Action completes without error and produces the expected UI state | AFS step 4 | asserts the pre-filled defaults | asserted *(see Axis 2 — these ARE the defaults, not a value the UI requires changing to)* |
| 6 Click "Generate" | Control responds; expected next state is shown | AFS step 5 | `POST /api/v2/auth/token/` 200 + dialog appears | asserted |
| 7 Verify a "New token generated!" dialog appears | Condition holds as described | AFS step 6 | `generated-token-dialog-title` exact text | asserted |
| 8 Verify the dialog shows a warning | Condition holds as described | AFS step 7 | `generated-token-dialog-warning` exact text | asserted |
| 9 Verify the token name is shown above the full token value | Condition holds as described | AFS step 8 | `generated-token-dialog-token-name` / `-token-value` DOM order | asserted |
| 10 Verify a "Copy" button is present — click it and verify a success confirmation appears | Condition holds as described | AFS step 9 | `generated-token-dialog-copy-button` click + toast text + button state | asserted |
| 11 Close the dialog | Action completes without error and produces the expected UI state | AFS step 10 | `generated-token-dialog-close-button` click + route back to `/settings/tokens` | asserted |
| 12 Verify "autotest-token" appears in the tokens table with masked value "...XXXX" | Condition holds as described | AFS step 11 | `token-row` filtered by name + `token-name-cell` + `token-value-cell` | asserted *(generated-per-run name)* |
| 13 Verify the Expiration column shows a green ✅ icon and "in 30 days" label | Condition holds as described | AFS step 12 | `token-expiration-status[data-expiration-state="active"]` + exact text | asserted |
| 14 Verify that token was copied to clipboard | Condition holds as described | AFS step 9 | `page.evaluate` clipboard readback == dialog token value | asserted |
| Expected Final State: Verify that token was copied to clipboard | (restates step 14) | AFS step 9 | same as step 9 | asserted *(no separate step needed)* |

## Axis 2 — Analyst additions
- **Step 1 adds a route-change assertion**, not just "form opens" — *added:
  the case text is ambiguous between an inline dialog and a page navigation;
  live exploration confirmed it's a navigation to
  `/settings/create-personal-token` (`onAddPersonalToken` in
  `PersonalTokens.jsx`, confirmed in `TokensSection`/route wiring and by
  directly observing the URL change on click). This is documented as a
  case-text ambiguity, not a defect — see Known Defects / Case-Text Note.*
- **Step 4 asserts DEFAULTS rather than performing a set-then-assert** —
  *added: the case's step 5 literally says "Set expiration: unit 'Days',
  value '30'", but live exploration showed these are the page's own
  pre-filled defaults (`DEFAULT_TOKEN_EXPIRATION_DAYS = 30`,
  `EXPIRATION_MEASURES[1]` = `'days'`) — there is nothing to "set" to reach
  that state from a fresh form load. Automation asserts the values are
  correct as-is; this satisfies the case's literal expected result ("Action
  completes without error and produces the expected UI state") without a
  no-op interaction. If a future build changes the default, this step would
  correctly need to become an actual interaction — flagged here so the drift
  is visible if it ever happens.*
- **Step 5 adds a `POST` 200 network assertion** — *added: standard practice
  per `test-case-analysis` § 3 "note the underlying traffic"; distinguishes a
  genuine create from a stale-UI false positive.*
- **Step 9 adds an actual clipboard-content readback**, not just the toast +
  button-state UI signals — *added: the case's own final step (14) and
  "Expected Final State" both explicitly require verifying the clipboard
  content, not just that a confirmation UI appeared. This needed the most
  investigation of any element in this case — see Automation Hints for the
  permission-grant requirement discovered while confirming this is
  practically assertable in this framework.*
- **Step 11/12 add exact-match assertions on cell content** (name, masked
  value pattern, expiration text + state) — *added: the case's own wording
  ("appears... with masked value", "shows a green ✅ icon and 'in 30 days'
  label") already implies exact content checks; ELITEA-2277 explicitly
  scoped cell-content testids as out-of-scope for itself (it never created a
  token) — this case is where they become properly in-scope and are
  requested here for the first time.*
- **Cleanup step added** — *added: this case creates a real, persistent
  entity in shared live project data (`${ELITEA_PROJECT_ID}` = 399, the same
  project ELITEA-2277 reads from); per `.agents/testing.md` § Test data
  strategy ("clean up loudly only when the observable requires fresh state" —
  this case's core observable IS the freshly created token, so cleanup is
  required, not optional). Confirmed the full delete-and-verify round-trip
  live before writing this AFS.*

## Known Defects Found During Exploration
None. All case steps reproduce as authored on this build — see Case-Text Note
below for one wording ambiguity (not a defect) worth flagging to the
implementer and to the case author.

**Case-Text Note (clarification-worthy, not filed as a bug):** the case's
step 3 says a "'New Token' form opens" — read literally this could imply an
inline dialog/modal on the same `/settings/tokens` page. Live exploration
confirms the "+" button actually **navigates to a separate route**
(`/settings/create-personal-token`, `CreatePersonalToken.jsx`), which then
also contains a further dialog (`GeneratedTokenDialog`) after Generate is
clicked. This is a reasonable reading of "a form opens" (a full-page form
did open) and the resulting UI matches every subsequent case step exactly
(Name field, Expiration period unit dropdown + numeric value, Generate
button producing a token dialog) — so this is **not** reverse-masking
drift and **not** filed as a defect or clarification issue per
`.agents/role-overrides.md` § interaction-discovery ladder / reverse-masking
guard (the live behavior satisfies the case's expected results; only the
"form opens" phrasing is ambiguous, not wrong). Noted here for the
implementer's awareness (their page object must model a route change, not a
dialog-wait) and because `test-specs/settings-personal-tokens/_surface.md`
already flagged this exact gotcha from ELITEA-2277 exploration — this AFS is
confirmatory, not a new finding.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: extend `automation/pages/personal_tokens_page.py` (existing,
  from ELITEA-2277) with the create-flow locators, OR add a sibling
  `automation/pages/create_personal_token_page.py` for the
  `/settings/create-personal-token` route + `GeneratedTokenDialog` — either
  is reasonable; the create page and the dialog it opens are tightly coupled
  (one user flow) so a single new page object covering both is likely
  cleaner than splitting them. Reuse `PersonalTokensPage` for steps 1 and 11
  (add-button click, table-row assertions) regardless.
- **Clipboard read requires the context's `clipboard-read`/`clipboard-write`
  permission** (already granted for every test via `automation/conftest.py`
  `context` fixture, line ~279: `permissions=["clipboard-read",
  "clipboard-write"]`) — this is already correct for the pytest suite, no
  fixture change needed. **Do not attempt to verify this manually via an
  ad-hoc/exploratory browser session that wasn't created with this
  permission** — confirmed live: `page.evaluate("navigator.clipboard.readText()")`
  against a context WITHOUT the granted permission hangs indefinitely (the
  browser silently waits on a permission prompt that headless/MCP contexts
  never resolve) rather than rejecting quickly. This cost real exploration
  time and is worth flagging forward — if this test's clipboard assertion
  ever times out, first check the context's granted permissions before
  assuming a product regression.
- Row-scoping for the created token: `token_row.filter(has_text=<generated
  name>)` — sanctioned chaining off an already-testid-scoped
  `LocatorDescriptor` (same pattern as ELITEA-2277's
  `get_first_row_action_icon`), not a raw free-floating selector.
- `token-expiration-status` state assertion:
  `'[data-testid="token-expiration-status"][data-expiration-state="active"]'`
  as a class-level UPPER_CASE constant, scoped within the filtered row —
  same "testid = stable identity, state via `data-*` attribute" pattern as
  the rest of this project's locator policy (`.agents/testing.md`), applied
  here to a 4-branch conditional render (`ExpiryInDays` in `TokensTable.jsx`
  renders one of `SuccessIcon`/`AttentionIcon`/`SuccessIcon`/`RemoveIcon`
  depending on `expiryInDays`) rather than the simpler 2-branch case the
  policy's examples show — the same testid goes on the container `Box` in
  all 4 branches, with `data-expiration-state` values `active` (>7d, green),
  `warning` (1-7d, amber), `never` (no expiry, green), `expired` (past,
  gray). This case only exercises `active`; the other 3 states are already
  visible live on the 5 pre-existing rows (`Never` ×3, `Expired` ×2) but this
  case's own steps never assert them — request the testid+attribute on all 4
  branches anyway (cheap, keeps the component internally consistent) but
  only the `active` value is "touched" by this test's executed path per
  `.agents/role-overrides.md` § "touches" scoping.
- Wait strategy: wait for the `POST /api/v2/auth/token/` response before
  asserting the dialog; wait for the dialog-close route change
  (`/settings/tokens`) before asserting the table row; wait for the deleted
  row to detach before ending cleanup. No `page.wait_for_timeout` anywhere,
  per `.agents/conventions.md`.
- Discard button / back-arrow button on the create-token page are NOT
  touched by this case's steps — no testid requested for them (scope
  discipline, `.agents/role-overrides.md` "touches").

## Concrete Handles (discovered during exploration)

All new testids — **none exist yet** for the create-token page, the
generated-token dialog, or the table's name/value/expiration cell content
(confirmed via source read, not just the ELITEA-2277 digest's earlier
zero-hits grep, since two of the three files below — `CreatePersonalToken.jsx`,
`GeneratedTokenDialog.jsx` — didn't exist as automation targets until now).
Locator policy is testid-only (`.agents/role-overrides.md` /
`.agents/testing.md` § Locator policy) — implementer adds all of these via
`add-data-testid`. **One exception: the delete-confirmation modal's testids
already exist** (see the Cleanup row) — zero new work there.

| Element | File | Recommended testid | How to add |
|---|---|---|---|
| "New Token" page title | `CreatePersonalToken.jsx` → `<DrawerPageHeader title="New Token" ... />` | `create-personal-token-page-title` | `DrawerPageHeader.jsx` **already** accepts `titleTestId` (added in ELITEA-2277) — just pass `titleTestId="create-personal-token-page-title"` at this call site. Zero shared-component change. |
| Name input | `CreatePersonalToken.jsx` → `<Input.InputBase id="name" ... inputProps={{ maxLength: MAX_VARIABLES_LENGTH }} />` | `create-personal-token-name-input` | Add `'data-testid': 'create-personal-token-name-input'` into the existing `inputProps` object (MUI `TextField`'s `inputProps` sets attributes on the native `<input>` — same mechanism `SimpleSearchBar` already uses per the ELITEA-2277 digest). Call-site-only change, no `InputBase.jsx` edit needed. |
| Expiration-period unit select | `CreatePersonalToken.jsx` → `<SingleSelect id="measure" ... />` | `create-personal-token-expiration-measure-select` | `SingleSelect.jsx` **already** accepts a `data-testid` prop (confirmed in source, wires onto the Select root AND `SelectDisplayProps` as `${dataTestId}-combobox`) — just pass `data-testid="create-personal-token-expiration-measure-select"` at this call site. Zero shared-component change. |
| Expiration-period value input | `CreatePersonalToken.jsx` → `<Input.InputBase id="expiration" type="number" ... />` | `create-personal-token-expiration-value-input` | Same mechanism as the Name input — this element currently has no `inputProps` object at all; add one: `inputProps={{ 'data-testid': 'create-personal-token-expiration-value-input' }}`. |
| Generate button | `CreatePersonalToken.jsx` → `<Button.BaseBtn ... onClick={() => formik.handleSubmit()}>Generate</Button.BaseBtn>` | `create-personal-token-generate-button` | `BaseBtn.jsx` spreads `...restProps` directly onto MUI `Button`, which forwards unknown props (including `data-*`) to the native `<button>` — just add `data-testid="create-personal-token-generate-button"` directly on the JSX. Zero shared-component change (confirmed by reading `BaseBtn.jsx` source — no prop allowlist). |
| Dialog title ("New token generated!") | `GeneratedTokenDialog.jsx` → `<Typography sx={styles.title}>New token generated!</Typography>` | `generated-token-dialog-title` | `data-testid="generated-token-dialog-title"` directly on the `Typography` JSX (feature-owned file, not a shared component — direct hardcode is fine here). |
| Dialog warning text | `GeneratedTokenDialog.jsx` → `<Typography variant="bodySmall" color="text.attention">This token will only be shown once...</Typography>` | `generated-token-dialog-warning` | `data-testid="generated-token-dialog-warning"` directly on that `Typography`. |
| Dialog token name | `GeneratedTokenDialog.jsx` → `<Typography variant="bodySmall" color="text.default">{name}</Typography>` (inside `tokenContainer`) | `generated-token-dialog-token-name` | `data-testid="generated-token-dialog-token-name"` directly on that `Typography`. |
| Dialog token value | `GeneratedTokenDialog.jsx` → `<Typography sx={styles.tokenText} variant="bodyMedium" color="text.default">{token}</Typography>` (inside `tokenScrollBox`) | `generated-token-dialog-token-value` | `data-testid="generated-token-dialog-token-value"` directly on that `Typography`. |
| Dialog close (X) icon | `GeneratedTokenDialog.jsx` → `<Box component={CancelIcon} sx={styles.closeIcon} onClick={onClose} />` | `generated-token-dialog-close-button` | `data-testid="generated-token-dialog-close-button"` directly on that `Box`. Confirmed this icon has NO accessible role/name today (a bare `Box` wrapping an SVG icon component with only an `onClick`) — a testid is the only stable handle available, role/text locating is not an option here regardless of policy. |
| Dialog Copy button | `GeneratedTokenDialog.jsx` → `<Button variant="elitea" color="primary" sx={styles.copyButton} onClick={onCopy}>{buttonTitle}</Button>` (plain MUI `Button`, not `BaseBtn`) | `generated-token-dialog-copy-button` | `data-testid="generated-token-dialog-copy-button"` directly on the JSX — MUI `Button` forwards unknown/`data-*` props to the native `<button>` the same as `BaseBtn` does. |
| Table row — name cell | `TokensTable.jsx` → `renderCell`, `column.field === 'name'` branch: `<Text.EllipsisTypography sx={styles.nameCell}>{row.name}</Text.EllipsisTypography>` | `token-name-cell` | `EllipsisTypography.jsx` spreads `...rest` onto MUI `Typography` (confirmed in source) — add `data-testid="token-name-cell"` directly on this JSX (static value, repeated per row — same pattern as `token-row`). |
| Table row — value (masked) cell | `TokensTable.jsx` → `renderCell`, `column.field === 'token'` branch: `<Text.EllipsisTypography>{'...' + row.token.substring(...)}</Text.EllipsisTypography>` | `token-value-cell` | Same mechanism — `data-testid="token-value-cell"` directly on this JSX. |
| Table row — expiration status (4-branch) | `TokensTable.jsx` → `ExpiryInDays` component, all 4 `return` branches' outer `<Box sx={styles.container}>` | `token-expiration-status` + `data-expiration-state="active"｜"warning"｜"never"｜"expired"` | Add BOTH attributes to each of the 4 `<Box sx={styles.container}>` JSX blocks inside `ExpiryInDays` — same testid value across all 4 (stable identity), differing `data-expiration-state` value per branch (state via `data-*`, not via a different testid — `.agents/testing.md` § "Testid = stable identity"). Static per-branch value, not data-derived, so this is a direct hardcode in each branch, not a template constant. |
| Delete-confirmation modal (cleanup only) | `DeleteEntityModal.jsx` (shared) | `delete-confirm-dialog` / `delete-confirm-title` / `delete-confirm-message` / `delete-confirm-name-input` / `delete-confirm-cancel-button` / `delete-confirm-button` | **Already exist — zero new work.** Confirmed by reading `DeleteEntityModal.jsx` source: all six testids are already hardcoded in this shared component today, used across the app's other delete-with-confirmation flows (per the ELITEA-2277 AFS's note on `DeleteEntityButton`). |

Not touched by this case (no testid requested — scope discipline,
`.agents/role-overrides.md` "touches" = actually invoked on this test's
executed path):
- Discard button and back-arrow button on the create-token page (case never
  clicks either — it always completes the create flow or closes the success
  dialog, never abandons the form).
- `token-expiration-status`'s `warning`/`never`/`expired` `data-expiration-state`
  values (the testid+attribute pair is requested on all 4 branches per the
  Automation Hints rationale above, but only `active` is asserted by this
  test's own steps).
- Preview/VSCode/JetBrains action icons for the created row (already have
  testids from ELITEA-2277; this case's own steps never click them, only the
  delete icon during cleanup).
- Column headers, search input, page-level `personal-tokens-*` testids (all
  already exist from ELITEA-2277; reused, not newly requested).

## Network Behavior
- `POST /api/v2/auth/token/` — token creation (`useTokenCreateMutation`),
  fires on Generate click. Confirmed live: `200 OK`, request body
  `{name, expires: {measure: 'days', value: 30}}`, response includes
  `uuid`/`token`/`name` (consumed by `GeneratedTokenDialog`).
- `GET /api/v2/auth/token/` — token list refetch (`useTokenListQuery`,
  `refetch()` called right after a successful create) — fires once
  immediately after the `POST` resolves, confirmed live, so the table is
  already current by the time the dialog closes.
- `DELETE` (cleanup) — fires on delete-confirmation; not separately probed
  by this AFS (out of this case's asserted scope) but confirmed live to
  succeed (the row detaches from the table with 0 console errors).

## Evidence
`test-results/screenshots/ELITEA-2280-step-13-token-created-in-table.png` —
viewport screenshot of the tokens table immediately after dialog close,
showing the newly created `autotest-token-e2280` row (used during live
exploration; automation will use its own generated-per-run name) at the top
of the table with masked value `...ep4w` and Expiration `in 30 days`
alongside the 5 pre-existing rows. Token was deleted immediately after this
screenshot per § Cleanup — table returned to its 5-row baseline, confirmed
live.
