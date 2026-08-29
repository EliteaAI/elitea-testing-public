# Test Case: Invite user without selecting a role

## Metadata
- **TMS ID**: ELITEA-2308
- **Source case**: `.agents/automation/settings-w09/cases/ELITEA-2308.md`
- **Linked Story**: none
- **Priority**: l3 (`priority: medium`). **pytest marker: `@pytest.mark.p2`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` -> DEV backend, project 400 "UI Testing")
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- Logged in, `admin` in project 400 — the "+" invite button is gated behind
  `PERMISSIONS.users.create`.

## Test Data
### generate-per-test
- A syntactically **valid, unique** probe email, e.g.
  `elitea-role-gate-<uuid4-hex-8>@example.com`. It is only ever TYPED — the
  Invite button is never clicked, so **no user is created and no request
  fires**; the uniqueness is hygiene, not a cleanup requirement.

## Test Steps
1. Navigate to Settings -> Users; capture the current row count.
2. Click "+" to open the Invite-users dialog.
   - **Verify**: `users-invite-dialog` visible; the Invite button
     (`users-invite-confirm-button`) is **disabled** at open (nothing typed,
     no role chosen).
3. Type the valid probe email into the Emails field and blur it (Tab).
   - **Verify**: the field displays the typed value.
   - **Verify**: **no** email-validation error renders
     (`users-invite-emails-error-text` count 0) — the email is valid, so the
     only remaining gate is the missing role. This is what isolates the case
     from ELITEA-2307's invalid-email path.
4. Leave the Roles dropdown empty.
   - **Verify**: the Roles combobox displays no selected role.
5. **Verify** the Invite button is **disabled**.
6. **Differentiator** — select a role (`viewer`) in the Roles dropdown.
   - **Verify**: the Invite button becomes **enabled**.
   *(Invite is still never clicked — no user is created.)*
7. Close the dialog with the Close (×) button.
   - **Verify**: the dialog unmounts and the row count equals step 1's — no
     user was invited by this test.
8. **Verify** no unexpected console errors across the flow.

## Expected Results
- With a valid email entered and no role selected, the Invite button is
  disabled.
- Selecting a role flips it to enabled, proving the disabled state in step 5
  was caused by the empty Roles selection.
- No user is created; the table is left as found.
- No console errors.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — permission-gated "+" renders | asserted |
| 1 Navigate to Settings -> Users as Admin | Target page/section loads successfully | step 1 | `step 1`: rows visible | asserted |
| 2 Click "+" | Control responds; expected next state is shown | step 2 | `step 2`: `users-invite-dialog` visible | asserted |
| 3 Enter a valid email address | Field accepts the input and displays the entered value | step 3 | `step 3`: field value == typed email, no validation error | asserted |
| 4 Leave the Roles dropdown empty | Action completes without error and produces the expected UI state | step 4 | `step 4`: combobox shows no selected role | asserted |
| 5 Verify INvite button is disabled | Condition holds as described | step 5 | `step 5`: `users-invite-confirm-button` disabled | asserted |
| Expected Final State: Verify INvite button is disabled | (restates step 5) | step 5 | same as row above | asserted |

**Axis 2 — Analyst additions:**
- **Step 6 is the load-bearing addition.** `InviteUserDialog`'s gate is
  `disabled={!emails.length || !selectedRoles.length || error}` — three
  independent conditions OR'd together. A test that only asserts "disabled"
  proves nothing about WHICH gate fired, and would pass identically against a
  permanently-broken button. Selecting a role and watching it enable is what
  makes step 5's assertion actually about the role. *(This is the same
  confound the ELITEA-2307 reviewer caught on the sibling invalid-email case;
  the fix is applied here proactively rather than in a fix round.)*
- Step 3 asserts **no** validation error — *added: distinguishes this case
  from ELITEA-2307. If the probe email were malformed, the `error` gate would
  keep the button disabled and step 5 would pass for the wrong reason.*
- Step 2 asserts the button starts disabled — *added: cheap, and it
  establishes the before-state so step 6's enable is a real transition.*
- Step 7 asserts the row count is unchanged — *added: this case types a real
  email into a real invite form; proving nothing was submitted is the
  cleanliness guarantee.*
- Step 8 no-console-errors side-channel check — *standard discipline;
  confirmed 0 errors live.*

## Cleanup
None required — the Invite button is never clicked, so no `POST
/admin/users/default/400` ever fires and no user is created. Step 7's
row-count assertion is the proof, not an assumption.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| "+" invite button | `users-invite-button` | pre-existing (ELITEA-2292) |
| Dialog root | `users-invite-dialog` | **NEW** — EliteaAI/EliteaUI@8f559586 (ELITEA-2295) |
| Emails input | `users-invite-emails-input` | pre-existing (ELITEA-2304) |
| Emails validation error | `users-invite-emails-error-text` | pre-existing (ELITEA-2307) — used here as an ABSENCE assertion |
| Roles combobox | `users-invite-role-select-combobox` | pre-existing (ELITEA-2304) |
| Role option `viewer` | `select-option-viewer` | pre-existing shared mechanism |
| Invite (confirm) button | `users-invite-confirm-button` | pre-existing (ELITEA-2304) |
| Close (×) button | `users-invite-close-button` | **NEW** — EliteaAI/EliteaUI@8f559586 |

No new testid is needed beyond the two ELITEA-2295 already added.

## Network Behavior
**No request fires on this path** — confirmed live. Validation is
client-side, and the Invite button is never clicked. Do NOT reuse
`AdminUsersPage.invite_users()`: it clicks Invite and awaits the POST.

## Known Defects Found During Exploration
None. The role gate behaves exactly as the case expects.

## Blocked Steps
None.

## Automation Hints
- Page object: reuse `open_invite_dialog()`,
  `type_email_in_invite_dialog()`, `blur_invite_emails_field()`,
  `select_role_in_invite_dialog()` — all pre-existing on `AdminUsersPage`
  (ELITEA-2304/2307). Add only `close_invite_dialog()` (shared with
  ELITEA-2295) and a `get_invite_selected_role_text()` reader.
- The Roles combobox renders a zero-width space (`​`) when nothing is
  selected — assert "no role selected" by stripping that character, not by
  comparing against `""` naively. Live-observed value: `"​"`.
- Assert the button state with `expect(...).to_be_disabled()` /
  `to_be_enabled()` so the assertion auto-retries through the re-render that
  follows the role selection.

### Console-error assertion — known-defect exclusion (implementer, 2026-08-29)

The final "no unexpected console errors" step excludes ONE exact URL:
`/api/v2/elitea_core/toolkits/prompt_lib/` (project-id-less), via
`utils.console_errors.exclude_known_defect_urls` with a `# Known defect: #1971`
comment. **#1971 is a filed, OPEN product defect** (regression of the closed
#554): during the project switch `AdminUsersPage.navigate()` performs, EliteaUI's
`toolkitTypes` RTK-Query fires before `useSelectedProjectId()` resolves and
requests a project-id-less path, which 404s. Cosmetic in the product, unrelated
to anything this case drives — but it intermittently failed the console step on
2 of 4 full-suite runs of this wave.

The exclusion is keyed to the **exact URL, never the status code** (a "404"
filter would swallow the next genuine one — masking, explicitly ruled out in
`.agents/testing.md` § Unconfirmed). One argument to delete when #1971 ships.
