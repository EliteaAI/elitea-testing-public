"""Test for Credential — Delete Credential.

Verifies the full delete happy path: creating a credential through the UI
create form, confirming it appears in the Credentials list, opening its
detail page, deleting it via the three-dot menu's "Delete" item + the shared
type-to-confirm confirmation dialog, and confirming it is gone from the list
immediately, after a page reload, and server-side per the API.

Test case: ELITEA-1964
AFS: test-specs/toolkits-credentials/l1_delete-credential_ELITEA-1964.md

No substitution of the system under test: the credential is created through
the real UI form (the case's own step 1), deleted through the real UI flow
(the case's subject), and the "it is really gone" evidence comes from the
product's own DELETE response plus a server-side API read — nothing is
mocked, injected, or fabricated. The API is used only as an independent
read-back oracle and as a defensive teardown for a failed run.
"""

import logging
import re
import time

import allure
import pytest
from config import settings
from pages.credential_create_page import CredentialCreatePage
from pages.credential_detail_page import CredentialDetailPage
from pages.credentials_list_page import CredentialsListPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

CREATE_RESPONSE_TIMEOUT = 15_000


def _is_known_518_warning(msg) -> bool:
    """Filter the pre-existing, already-filed, OPEN CredentialsList.jsx
    double-``onRefetch()`` crash (elitea-testing-public#518) — the same
    filter established by ``test_credential_create.py``; this test lands on
    ``/credentials/all`` three times (post-save redirect, post-delete
    redirect, reload), each an entry point for that race. Both message
    shapes are matched: the raw RTK Query error and React's error-boundary
    companion log.
    """
    text = msg.text
    return (
        "Cannot refetch a query that has not been started yet" in text
        or ("above error occurred" in text and "<CredentialsList>" in text)
    )


def _is_known_1666_error(msg, credential_id) -> bool:
    """Filter the OPEN, already-filed elitea-testing-public#1666 — after a
    successful ``DELETE`` (204) the app re-fetches the credential it just
    deleted (``GET /configurations/configuration/{project}/{id}``), which
    404s and logs a console error inside the happy path. Sibling of #1330
    (same stale-refetch pattern on pipeline versions).

    Matched on ``msg.location.url`` pinned to THIS test's own credential id —
    not a blanket "ignore 404s" — so any other 404 still fails the
    side-channel check (same discipline as ``test_credential_create.py``'s
    ``_is_known_554_warning``). Returns False until the id is known.
    """
    if credential_id is None:
        return False
    location_url = (msg.location or {}).get("url", "")
    expected_suffix = f"/configurations/configuration/{settings.elitea_project_id}/{credential_id}"
    return "404" in msg.text and location_url.rstrip("/").endswith(expected_suffix)


class TestCredentialDelete:
    """ELITEA-1964 — Delete a credential via the detail page's three-dot menu."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1964_delete-credential.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1666", "Known defect #1666")
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/518", "Known defect #518")
    @pytest.mark.p1
    def test_delete_credential_via_three_dot_menu(self, page, credential_api):
        """Create a credential, delete it via the three-dot menu + confirmation
        dialog, and verify it stays gone from the list, after a reload, and in
        the API."""
        ts = int(time.time())
        # Case pins the literal name `autotest_cred_delete`; timestamped per
        # this feature's collision-avoidance convention (AFS Test Data).
        display_name = f"autotest_cred_delete_{ts}"
        credential_id = None

        console_messages = []

        def _on_console(msg):
            if (
                msg.type in ("error", "warning")
                and not _is_known_518_warning(msg)
                and not _is_known_1666_error(msg, credential_id)
            ):
                console_messages.append(msg)

        create_page = CredentialCreatePage(page)
        list_page = CredentialsListPage(page)
        detail_page = CredentialDetailPage(page)

        try:
            page.on("console", _on_console)

            with allure.step(f"Step 1 — Create the credential {display_name!r} via the UI create form"):
                # Github type, default Anonymous auth: Base Url ships pre-filled
                # so a Display Name alone enables Save — no token needed and no
                # secret is ever typed (AFS Test Data).
                create_page.navigate_to_type("github")
                create_page.set_display_name(display_name)

                assert create_page.display_name_input.input_value() == display_name, (
                    f"Display Name field should read {display_name!r} after filling"
                )
                assert create_page.id_input.input_value() == display_name, (
                    f"ID field should live-mirror the Display Name as {display_name!r}, "
                    f"got {create_page.id_input.input_value()!r}"
                )
                assert create_page.is_save_enabled(), (
                    "Save should be enabled once Display Name is filled (Base Url is "
                    "pre-filled and Anonymous is the default auth method)"
                )

                with page.expect_response(
                    lambda r: (
                        f"/configurations/configurations/{settings.elitea_project_id}" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=CREATE_RESPONSE_TIMEOUT,
                ) as create_response_info:
                    create_page.save_button.click()
                create_response = create_response_info.value

                assert create_response.status == 200, (
                    f"Expected 200 from the credential-create POST, got {create_response.status}"
                )
                create_body = create_response.json()
                credential_id = create_body.get("id")
                assert credential_id, "Expected a numeric id in the create response"
                assert create_body.get("label") == display_name, (
                    f"Expected created credential label {display_name!r}, got {create_body.get('label')!r}"
                )
                assert create_body.get("elitea_title") == display_name, (
                    f"Expected created credential elitea_title {display_name!r}, "
                    f"got {create_body.get('elitea_title')!r}"
                )
                page.wait_for_url(
                    re.compile(r".*/credentials/all/?(\?.*)?$"), timeout=CREATE_RESPONSE_TIMEOUT
                )
                logger.info("Created credential id=%s name=%s", credential_id, display_name)

            with allure.step(f"Step 2 — Verify {display_name!r} appears in the credentials list"):
                # Save redirects straight onto a list that already includes the
                # new card (created_at desc) — no extra navigation needed.
                expect(list_page.card_by_name(display_name)).to_have_count(1)

            with allure.step("Step 3 — Open the credential detail page"):
                list_page.click_credential_card(display_name)
                detail_page.wait_for_page_load()

                assert detail_page.get_credential_id_from_url() == str(credential_id), (
                    f"Detail page URL should carry the created credential id {credential_id}, "
                    f"got {page.url}"
                )
                assert detail_page.get_display_name() == display_name, (
                    f"Detail page should show {display_name!r} in the Display Name field"
                )

            with allure.step('Step 4 — Click the three-dot menu and select "Delete"'):
                detail_page.open_controls_menu()
                expect(detail_page.delete_menuitem).to_be_visible()
                assert (detail_page.delete_menuitem.text_content() or "").strip() == "Delete", (
                    "The three-dot menu's delete item should read 'Delete', got "
                    f"{(detail_page.delete_menuitem.text_content() or '').strip()!r}"
                )

                detail_page.open_delete_dialog()

                expect(detail_page.delete_confirm_dialog).to_be_visible()
                assert (detail_page.delete_confirm_title.text_content() or "").strip() == "Delete confirmation", (
                    "Delete-confirmation dialog title should read 'Delete confirmation', got "
                    f"{(detail_page.delete_confirm_title.text_content() or '').strip()!r}"
                )
                assert (detail_page.delete_confirm_entity_name.text_content() or "").strip() == display_name, (
                    "The confirmation dialog should name the credential being deleted, got "
                    f"{(detail_page.delete_confirm_entity_name.text_content() or '').strip()!r}"
                )
                assert display_name in (detail_page.delete_confirm_message.text_content() or ""), (
                    "The confirmation message should include the credential name"
                )
                # The type-to-confirm gate is the point of this dialog
                # (shouldRequestInputName: true, CredentialsControls.jsx) — a
                # regression dropping it would still 'show a dialog'.
                expect(detail_page.delete_confirm_name_input).to_be_visible()
                expect(detail_page.delete_confirm_button).to_be_disabled()

            with allure.step("Step 5 — Confirm deletion in the dialog"):
                detail_page.fill_delete_confirm_name(display_name)
                expect(detail_page.delete_confirm_button).to_be_enabled()

                delete_response = detail_page.confirm_delete(str(credential_id))
                assert delete_response.status == 204, (
                    f"Expected 204 No Content from the credential DELETE, got {delete_response.status}"
                )
                page.wait_for_url(
                    re.compile(r".*/credentials/all/?(\?.*)?$"), timeout=CREATE_RESPONSE_TIMEOUT
                )

            with allure.step(f"Step 6 — Verify {display_name!r} is removed from the list"):
                expect(list_page.card_by_name(display_name)).to_have_count(0)
                # The list page itself still rendered (the delete removed one
                # card, it did not break the route).
                expect(list_page.create_button).to_be_visible()

            with allure.step("Step 7 — Reload the page and verify the credential is still gone"):
                list_page.reload_list()
                expect(list_page.card_by_name(display_name)).to_have_count(0)

                # Independent ground truth — a second DOM read could be served
                # from cache; the API is the authority on "permanently removed".
                remaining = credential_api.list_all_credentials()
                assert not [c for c in remaining if c.get("label") == display_name], (
                    f"Credential {display_name!r} should be absent server-side after deletion"
                )
                assert not [c for c in remaining if c.get("id") == credential_id], (
                    f"Credential id {credential_id} should be absent server-side after deletion"
                )
                credential_id = None  # deleted by the flow under test — nothing to clean up

            with allure.step("Side-channel check — no unexpected console errors/warnings across the flow"):
                assert not console_messages, (
                    f"Unexpected console errors/warnings: {[m.text for m in console_messages]}"
                )

        finally:
            with allure.step("Cleanup — defensively remove the credential if the flow did not"):
                if credential_id is not None:
                    try:
                        credential_api.delete_credential(credential_id)
                        logger.info("Teardown deleted leftover credential id=%s", credential_id)
                    except Exception as exc:  # noqa: BLE001 - teardown must never mask the real failure
                        logger.warning("Teardown could not delete credential id=%s: %s", credential_id, exc)
