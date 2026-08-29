# Test Case: Invite users dialog opens with correct layout

## Metadata
- **TMS ID**: ELITEA-2295
- **Source case**: `.agents/automation/settings-w09/cases/ELITEA-2295.md`
- **Linked Story**: none
- **Priority**: l3 (`priority: medium`). **pytest marker: `@pytest.mark.p2`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` -> DEV backend, project 400 "UI Testing")
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- Logged in, `admin` in project 400 — the "+" invite button is gated behind
  `PERMISSIONS.users.create` and does not render otherwise.

## Test Data
### reuse-existing
- `${USERS_TEAM_PROJECT_ID}` = `400`.
### generate-per-test
- None. This case only OPENS and CLOSES the dialog; nothing is typed, no
  invite is submitted, no user is created.

## Test Steps
1. Navigate to Settings -> Users.
   - **Verify**: the page loaded (rows visible) and the "+" invite button
     (`users-invite-button`) is visible and enabled.
   - **Verify**: the invite dialog is NOT mounted yet (count 0) — so step 2's
     appearance is a real state change, not a pre-existing condition.
2. Click the "+" button.
   - **Verify**: the Invite-users dialog (`users-invite-dialog`) becomes
     visible.
3-8. **Verify** the dialog's layout, all inside the opened dialog:
   - **Title** (`users-invite-title`) has exact text `"Invite users"`.
   - **Description** (`users-invite-description`) has exact text
     `"Enter user emails(separated by comma) and select roles to define
     permissions for this project."` (verbatim, including the missing space
     before the parenthesis — matches the case text and the source).
   - **Emails field** (`users-invite-emails-input`) is visible, and its label
     (`users-invite-emails-label`) has exact text `"Emails *"` — the trailing
     `*` IS the required marker the case asks for. **Assert innerText, not
     textContent** (implementer amendment, live-diagnosed): the label node
     carries TWO asterisks — the visible one `StyledInputEnhancer` renders
     inside the label's Box (`Emails *`) plus MUI's own `display:none`
     `MuiFormLabel-asterisk` span — so Playwright's default `to_have_text`
     (textContent) reads `"Emails * *"` and fails. Only the visible text is
     the observable the case describes.
   - **Roles dropdown** (`users-invite-role-select-combobox`) is visible;
     opening it shows **exactly three** options — `admin`, `editor`,
     `viewer` — via `select-option-{role}`.
   - **Close (×) button** (`users-invite-close-button`) is visible in the
     dialog title bar.
9. Click the Close (×) button.
   - **Verify**: the dialog unmounts (count 0) and the users table is intact
     — the row count equals the pre-open count (nothing was invited).
10. **Verify** no unexpected console errors across the flow.

## Expected Results
- The "+" button opens a dialog titled "Invite users" carrying the described
  helper text, a required Emails field, a Roles dropdown offering exactly
  admin/editor/viewer, and a Close (×) control that dismisses it without
  side effects.
- No console errors.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — permission-gated "+" renders | asserted |
| 1 Navigate to Settings -> Users as Admin | Target page/section loads successfully | step 1 | `step 1`: rows visible, "+" visible + enabled | asserted |
| 2 Click the "+" button | Control responds; expected next state is shown | step 2 | `step 2`: `users-invite-dialog` visible (count 0 -> visible) | asserted |
| 3 Verify the "Invite users" dialog opens with: (parent bullet) | Condition holds as described | steps 2 + 3-8 | decomposed into the five sub-checks below | asserted |
| 4 Title "Invite users" | Action completes without error and produces the expected UI state | step 3-8 | exact text on `users-invite-title` | asserted |
| 5 Description: "Enter user emails(separated by comma) and select roles to define permissions for this project." | Action completes without error and produces the expected UI state | step 3-8 | exact text on `users-invite-description` | asserted |
| 6 Emails field (marked as required with *) | Action completes without error and produces the expected UI state | step 3-8 | `users-invite-emails-input` visible + `users-invite-emails-label` exact text `"Emails *"` | asserted |
| 7 Roles dropdown showing: admin, editor, viewer | Action completes without error and produces the expected UI state | step 3-8 | combobox visible; opened -> exactly 3 options, texts `admin`/`editor`/`viewer` | asserted |
| 8 Close (×) button in the top right | Action completes without error and produces the expected UI state | steps 3-8 + 9 | visible in 3-8; step 9 CLICKS it and asserts the dialog unmounts | asserted |
| Expected Final State: Close (×) button in the top right | (restates step 8) | step 9 | same as row above | asserted |

**Axis 2 — Analyst additions:**
- Step 1 asserts the dialog is **not mounted** before the click — *added:
  without the before-state, "the dialog is visible" would also pass for a
  dialog that was already open, which is not what "opens" means.*
- Step 9 **clicks** the Close button rather than only asserting its presence
  — *added: the case's own Expected Final State names the Close button as the
  terminal state; a presence-only check would not notice a Close button that
  renders but does nothing. This is the one case element where clicking is
  strictly cheaper than the alternative and carries no side effect.*
- Step 9 asserts the row count is unchanged — *added: proves the
  open-then-close round trip invited nobody.*
- Step 3-8 asserts the roles list has **exactly** three entries, not merely
  that the three named ones are present — *added: the case's phrasing
  ("showing: admin, editor, viewer") is an enumeration; a fourth role
  appearing is a regression the positive-only check would miss.*
- Step 10 no-console-errors side-channel check — *standard discipline;
  confirmed 0 errors live.*

## Cleanup
None. Nothing is typed and no invite is submitted, so no user is created.
The dialog is closed by the case's own step 9.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| "+" invite button | `users-invite-button` | pre-existing (ELITEA-2292) |
| Dialog root | `users-invite-dialog` | **NEW** — EliteaAI/EliteaUI@8f559586 (`dialogTestId` -> `BaseModal`'s already-supported `data-testid`) |
| Dialog title | `users-invite-title` | **NEW** — same commit (`titleTestId` -> `BaseModal.titleTestId`) |
| Description text | `users-invite-description` | **NEW** — same commit (`descriptionTestId` on the existing `Typography`) |
| Emails input | `users-invite-emails-input` | pre-existing (ELITEA-2304) |
| Emails label (carries the required `*`) | `users-invite-emails-label` | **NEW** — same commit (`emailsLabelTestId` -> `StyledInputEnhancer`'s already-supported `InputLabelProps`) |
| Roles combobox | `users-invite-role-select-combobox` | pre-existing (ELITEA-2304) |
| Role options | `select-option-admin` / `-editor` / `-viewer` | pre-existing shared `SingleSelectMenuItem` mechanism |
| Close (×) button | `users-invite-close-button` | **NEW** — same commit (`closeButtonTestId` -> `BaseModal.closeButtonTestId`) |

All five NEW testids are **purely additive prop threading** onto nodes and
props that already existed — no new DOM node, no new hook, no removed line
(zero-functional-impact greps: 0 hits, 17 insertions / 0 deletions).

**⚠️ `select-option-` prefix gotcha (live-discovered).** Counting
`[data-testid^="select-option-"]` is NOT a safe "number of options" measure:
when a role is already selected, `SingleSelect` also renders a checkmark
carrying `select-option-selected-icon`, which the prefix matches. Use the
exclusion selector `[data-testid^="select-option-"]:not([data-testid="select-option-selected-icon"])`.
In the INVITE dialog nothing is preselected so the naive count happens to be
right — but ELITEA-2305's Edit-dialog half proves the trap, so both use the
same exclusion constant.

## Network Behavior
Opening and closing the dialog fires **no request** (confirmed live). Only
the page-mount users/roles GETs fire, both 200 OK.

## Known Defects Found During Exploration
None. Every element the case enumerates renders with exactly the text the
case states.

## Blocked Steps
None.

## Automation Hints
- Page object: extend `AdminUsersPage` — it already has `invite_button`,
  `open_invite_dialog()`, `invite_emails_input`,
  `invite_role_select_combobox`. Add `LocatorDescriptor`s for the five new
  testids plus `close_invite_dialog()` and `get_role_option_texts()`.
- The dialog root testid lands on the MUI `Dialog` root, which **unmounts**
  when closed — so `to_have_count(0)` is the correct closed-state assertion.
- Emails-label assertion: `expect(...).to_have_text("Emails *", use_inner_text=True)`.
  See the Test Steps note on the double asterisk — the default textContent
  comparison reads `"Emails * *"`.
- Opening the roles menu: click the combobox, then read the options; close
  with `Escape` (consumed by the MUI Menu before it reaches the dialog's own
  Escape handler — the dialog stays open, confirmed live and already
  documented in `_surface.md`).
