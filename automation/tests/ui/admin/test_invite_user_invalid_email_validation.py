"""UI test — User with invalid email format shows validation error.

Opens the Invite-users dialog and types two invalid-shaped emails
("notanemail", "user@"), asserting that:
  - immediately after typing (before blur), the field shows the typed text
    and NO error is shown yet (validation is blur-gated, not
    live-as-you-type — confirmed via `InviteUserDialog.jsx` source: `onChange`
    only updates state, `onBlur` calls `parseEmails` and sets `error`);
  - after blur (Tab), an inline `Invalid email: {email}` error renders below
    the Emails field and the Invite (confirm) button is (still) disabled.

Read-only: the Invite button never becomes enabled on this path, so Invite
is never clicked and no user is created — no cleanup of seeded data is
required (`.agents/testing.md` § Test data strategy — prefer read-only
assertions when the observable doesn't require fresh state).

A role IS selected in the dialog (via `select_role_in_invite_dialog`,
pre-existing since ELITEA-2304) before the disabled-button assertions,
even though the case's own steps never mention a role. This is required
for those assertions to isolate what they claim to prove: per
`InviteUserDialog.jsx`, the Invite button's `disabled` prop is
`!emails.length || !selectedRoles.length || error` — with NO role ever
selected, `!selectedRoles.length` alone keeps the button disabled for the
whole flow, so a disabled-button assertion would pass regardless of the
email-validation (`error`) outcome it's meant to exercise. Pre-selecting
a role removes that confound: Step 2's assertion is then driven purely by
`!emails.length` (no emails yet) and Step 4's purely by `error` (the
invalid-email state), matching what each step's docstring claims.
Confirmed live: with a role selected, the Invite button is disabled at
Step 2 for lack of emails, and disabled again at Step 4 specifically
because `error` is true (emails and role are both non-empty by then).
Selecting a role is dialog-setup technique, not a new case assertion —
the case's own steps and their expected results are unchanged.

The dialog is reopened fresh for each of the two example emails (rather
than typing the second over the first in the same open dialog). Live
exploration during implementation found `InviteUserDialog.jsx` re-validates
live (not just on blur) once `error` is already `true`
(`useEffect` keyed on `[error, inputText]`) — so typing a second value into
an already-errored field surfaces the error immediately, which would make
the "no error yet, before blur" assertion for the SECOND example fail for a
reason that isn't the case under test. Reopening the dialog (which resets
all local state per its own `if (!open) {...}` effect) reproduces the
AFS's own live-confirmed methodology, where each example was confirmed
"alone" against a fresh dialog.

Test case: ELITEA-2307
AFS: test-specs/settings-users-and-roles/l3_invite-user-invalid-email-validation_ELITEA-2307.md
"""

import logging

import allure
import pytest
from pages.admin_users_page import AdminUsersPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p3, pytest.mark.regression, pytest.mark.new]

INVALID_EMAILS = ("notanemail", "user@")
# Pre-selected in the dialog so the disabled-button assertions isolate the
# email-validation (`error`) gate rather than the role-selection
# (`!selectedRoles.length`) gate — see module docstring. Same value as
# `test_users_batch_edit_roles.SEEDED_ROLE`; any option works since it's
# never submitted here (Invite is never clicked on this path).
SELECTED_ROLE = "editor"


class TestInviteUserInvalidEmailValidation:
    """ELITEA-2307 — User with invalid email format shows validation error."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2307_user-with-invalid-email-format-shows-validation-error.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.blocked
    def test_invite_user_invalid_email_validation(self, page):
        """For each invalid-shaped email, typing shows the text with no
        error yet; blurring surfaces the exact `Invalid email: {email}`
        error and keeps the Invite button disabled."""
        users_page = AdminUsersPage(page)

        # Registered before Step 1 so console errors from the whole flow
        # are captured (.agents/memory/test-automation-engineer/
        # console_side_channel_checks.md — dual listener, registered early).
        console_errors = []
        page_errors: list[str] = []

        def _on_console(msg):
            if msg.type == "error":
                console_errors.append(msg)

        def _on_pageerror(exc):
            page_errors.append(str(exc))

        page.on("console", _on_console)
        page.on("pageerror", _on_pageerror)

        with allure.step(
            "Step 1 — Navigate to Settings -> Users as Admin: page title "
            "and at least one user row are visible"
        ):
            users_page.navigate()
            assert users_page.page_title.text_content() == "Users", (
                f"Expected page header text 'Users', got "
                f"{users_page.page_title.text_content()!r}"
            )
            row_count = users_page.user_row.count()
            assert row_count > 0, (
                f"Expected the users table to render at least one row, got {row_count}"
            )

        for email in INVALID_EMAILS:
            with allure.step(
                'Step 2 — Click the "+" Invite-users button and pre-select '
                f"a role ({SELECTED_ROLE!r} — isolates the disabled-button "
                "assertions from the role-selection gate, see module "
                "docstring): the Invite dialog opens with the Emails field "
                "visible and the Invite button starts disabled (no emails "
                f"yet) — [{email!r} run]"
            ):
                users_page.open_invite_dialog()
                assert users_page.invite_emails_input.is_visible(), (
                    "Expected the Invite dialog's Emails field to be visible"
                )
                users_page.select_role_in_invite_dialog(SELECTED_ROLE)
                assert users_page.invite_confirm_button.is_disabled(), (
                    "Expected the Invite button to start disabled with no "
                    f"emails entered, even with role {SELECTED_ROLE!r} "
                    "selected"
                )

            with allure.step(
                f"Step 3 — Type invalid email {email!r} into the Emails "
                "field: the field displays the typed text and NO error is "
                "shown yet (validation is blur-gated, not live-as-you-type)"
            ):
                users_page.type_email_in_invite_dialog(email)
                assert users_page.invite_emails_input.input_value() == email, (
                    f"Expected the Emails field to display {email!r} after typing"
                )
                assert users_page.invite_emails_error_text.count() == 0, (
                    f"Expected NO validation error yet for {email!r} before blur"
                )

            with allure.step(
                f"Step 4 — Blur the field (Tab) for {email!r}: an inline "
                f"'Invalid email: {email}' error renders below the Emails "
                "field and the Invite button becomes (or remains) disabled"
            ):
                users_page.blur_invite_emails_field()
                error_text = users_page.invite_emails_error_text.text_content()
                assert error_text == f"Invalid email: {email}", (
                    f"Expected inline error 'Invalid email: {email}', got {error_text!r}"
                )
                assert users_page.invite_confirm_button.is_disabled(), (
                    f"Expected the Invite button to be disabled while the "
                    f"{email!r} validation error is showing (role "
                    f"{SELECTED_ROLE!r} is selected and the field is "
                    "non-empty here, so this failing specifically proves "
                    "the `error` gate — not the role/emails-empty gates)"
                )

            # Close the dialog between examples (not an AFS case step) so
            # the next example starts from a fresh, reset dialog state —
            # see the module docstring for why. Cancel carries no testid
            # (AFS § Cleanup — matches the invite_confirm_button-only scope
            # precedent set in ELITEA-2304's page object); Escape is a
            # keyboard action, not a raw-handle locator.
            page.keyboard.press("Escape")
            users_page.invite_emails_input.wait_for(state="hidden")

        with allure.step("Side-channel check — no console errors during the flow"):
            assert not console_errors and not page_errors, (
                f"Expected no console/JS errors, got console={console_errors!r} "
                f"page_errors={page_errors!r}"
            )
