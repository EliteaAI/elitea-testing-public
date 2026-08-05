# Test Case: User with invalid email format shows validation error

## Metadata
- **TMS ID**: ELITEA-2307
- **Linked Story**: none
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` fixture — localhost skips login, `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (analyst slot)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (`auth_state` fixture).
- Acting user has `admin` role in the active project — required for the
  Users page's batch-Edit/Delete UI and the "Invite users" `+` button to
  render at all (confirmed live: `testbot@elitea.ai` holds `admin` only in
  project `400` "UI Testing"; `viewer`/absent elsewhere — same constraint
  documented in `test-specs/settings-users-and-roles/_surface.md`).

## Test Data
### reuse-existing
- `${USERS_TEAM_PROJECT_ID}` = `400` ("UI Testing") — the only project where
  the acting test account has admin rights on this surface.

### generate-per-test
- None — this case only types into the Emails field and blurs; the invite
  is never submitted (Invite button stays disabled while the field is in an
  error state), so no user is actually created and no cleanup is required.

## Test Steps
1. Navigate to Settings → Users as Admin (`AdminUsersPage.navigate()` —
   switches to project `400` first, then loads `/settings/users`).
   - **Verify**: `users-page-title` visible, at least one row in the table.
2. Click the "+" Invite-users button (`users-invite-button`).
   - **Verify**: the "Invite users" dialog opens (`users-invite-emails-input`
     visible), Invite button (`users-invite-confirm-button`) starts disabled
     (no emails yet).
3. Type an invalid email into the Emails field — case examples `notanemail`
   and `user@`, both confirmed live.
   - **Verify**: the field displays the typed text; **no error is shown yet**
     (see § Automation Hints — validation is blur-gated, not live-as-you-type).
4. Blur the field (Tab out, or click elsewhere in the dialog) to trigger
   validation.
   - **Verify**: an inline error message reading `Invalid email: {email}`
     renders directly below the Emails field, and the Invite button becomes
     (or remains) disabled.

## Expected Results
- After blur, an error message `Invalid email: notanemail` (or
  `Invalid email: user@` for the second example) is visible immediately below
  the Emails field.
- The Invite (confirm) button is disabled while the error is showing.
- No network request fires (client-side yup-style validation blocks
  submission before any request is possible — confirmed by the disabled
  Invite button; the case never reaches Invite anyway since it's never
  clicked).
- No console errors during the flow.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Users as Admin | page/section loads | step 1 | `step 1`: `users-page-title` + row visible | asserted |
| 2 Click "+" | control responds, next state shown | step 2 | `step 2`: dialog + emails input visible | asserted |
| 3 Enter an invalid email (e.g. "notanemail" or "user@") | field accepts input, shows entered value | step 3 | `step 3`: textbox value == typed text, no error yet | asserted |
| 4 Verify a validation error is shown below the Emails field | condition holds | step 4 | `step 4`: error paragraph text == `Invalid email: {email}`, rendered directly below the field | asserted |

Disposition: all four case elements `asserted`. No description/preconditions
prose beyond the steps table exists in this case (Test Data section says
"(none required)").

**Axis 2 — Analyst additions:**
- `step 2` asserts the Invite button starts disabled — *added: cheap,
  observed live, and it's the same disabled-state mechanism the case's
  step 4 outcome depends on (button re-disables once `error` flips true).*
- `step 4` asserts the Invite button is (still) disabled once the error
  shows — *added: directly exercises the `disabled={... || error}` gate in
  `InviteUserDialog.jsx`, the real mechanism preventing an invalid-email
  submission; the case's title promises "shows validation error" but the
  practical guarantee a user cares about is that Invite is blocked too.*
  **Implementer amendment (fix round 1, reviewer finding):** the button's
  actual `disabled` expression is `!emails.length || !selectedRoles.length
  || error` — three independent gates OR'd together. With no role ever
  selected in the dialog, `!selectedRoles.length` alone keeps the button
  disabled throughout, so the step 2/4 assertions as originally
  implemented passed independent of the email/`error` outcome they claim
  to isolate — they were not wrong (the button IS disabled at both
  points) but didn't prove what their prose claimed. Fix: the
  implementation now calls the pre-existing
  `AdminUsersPage.select_role_in_invite_dialog()` (ELITEA-2304) right
  after opening the dialog, so a role is selected throughout steps 2-4.
  This is dialog-setup technique (Phase 2/3, not a scope change) — the
  case's steps and expected results are unchanged; only the confound on
  an *added* (Axis 2) assertion is removed.
- `step 4` runs the case's TWO given example emails (`notanemail`, `user@`)
  as two assertions of the same step rather than picking one — *added:
  confirmed both live, cheap since the dialog is already open, and it
  guards against a regex edge-case regression on just one shape.*
- No console errors during the flow — *added: standard side-channel check
  per skill discipline, confirmed 0 errors live.*

## Cleanup
None. No user was created (Invite was never clicked — it stays disabled for
an invalid-email state), no data was mutated. Close the dialog via Cancel
(`Invite users dialog` → "Cancel" button, no dedicated testid needed — this
case's steps never require closing it, Cancel is exercised only as
post-assertion hygiene, matching the existing `invite_confirm_button`-only
scope precedent set in ELITEA-2304's page object).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Invite-users "+" button | `getByTestId('users-invite-button')` — **pre-existing**, `AdminUsersPage.invite_button` | none needed |
| Invite dialog — Emails field | `getByTestId('users-invite-emails-input')` — **pre-existing**, `AdminUsersPage.invite_emails_input` | none needed |
| Invite dialog — Invite (confirm) button | `getByTestId('users-invite-confirm-button')` — **pre-existing**, `AdminUsersPage.invite_confirm_button` | none needed |
| Invite dialog — inline email-validation error text | **testid needed: `users-invite-emails-error-text`** | none — do not fall back to `getByText('Invalid email:', exact=False)`; the string is dynamic (interpolates every offending email) and CSS-only (`.Mui-error .MuiFormHelperText-root`) would violate the testid-only policy |

## Network Behavior
None to assert — no request fires on this path (client-side validation
blocks `onConfirm` before any `POST /admin/users/default/{project}` call;
confirmed by the Invite button staying disabled throughout).

## Known Defects Found During Exploration
None found. The validation behaves correctly and matches the case's
intent — see § Automation Hints for the one non-obvious implementation
detail (blur-gated, not live-as-you-type) that is NOT a defect, just a
trigger-mechanism fact the implementer needs.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright/pytest, testid-only locators (`.agents/testing.md` §
  Locator policy) — no exceptions apply on this surface.
- Page object: extend `automation/pages/admin_users_page.py`
  (`AdminUsersPage`) — it already has `invite_button`, `invite_emails_input`,
  `invite_role_select_combobox`, `invite_confirm_button`,
  `open_invite_dialog()`. Add one new field
  (`invite_emails_error_text = LocatorDescriptor(testid="users-invite-emails-error-text", ...)`)
  once the testid is added, plus a small helper, e.g.
  `type_invalid_email_and_blur(email: str) -> None` that fills the emails
  input and presses `Tab` (or calls `.blur()` via the standard Playwright
  `page.keyboard.press("Tab")`/`locator.blur()`) — **do not reuse
  `AdminUsersPage.invite_users()`**, it fills-then-selects-role-then-clicks-
  Invite-and-awaits-a-POST-response; this case never reaches that request.
- **Validation trigger is blur-gated, not live-as-you-type** — confirmed via
  source read (`InviteUserDialog.jsx`: `onChange={handleChange}` only
  updates state; `onBlur={handleBlur}` is what calls `parseEmails` and sets
  `error`/`helperText`) and live re-confirmed twice (typing `notanemail` /
  `user@` alone showed no error; pressing `Tab` immediately surfaced
  `Invalid email: {email}`). Automate as: fill → assert NO error visible yet
  → blur (Tab) → assert error visible. Skipping the blur step and asserting
  right after `.fill()` would make the test falsely fail (this is the same
  "Formik/MUI touched-gating" pattern already documented for the Artifacts
  bucket-name form in `test-specs/artifacts/_surface.md`).
- Error text testid, once added, should thread the same way
  `emailsInputTestId` already threads today (`inputProps={{ 'data-testid':
  emailsInputTestId }}` pattern) — but the target here is the sibling
  `<FormHelperText>{helperText}</FormHelperText>` element
  (`InviteUserDialog.jsx`), which currently accepts NO testid prop at all.
  Add a new `emailsErrorTestId` prop, thread it as
  `<FormHelperText data-testid={emailsErrorTestId}>{helperText}</FormHelperText>`,
  and wire it at `Users.jsx`'s `InviteUserDialog` call site alongside the
  three props already wired there (`emailsInputTestId`, `roleSelectTestId`,
  `confirmButtonTestId`).
- Exact error string: `f"Invalid email: {email}"` — assert exact text, not a
  substring match, since the message is fully deterministic
  (`validateEmails()` in `InviteUserDialog.jsx`).
