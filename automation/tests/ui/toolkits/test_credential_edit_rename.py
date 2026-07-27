"""Test for Credential — Edit / Rename.

Verifies that a user can rename an existing credential via the detail page,
that the renamed Display Name persists across a full page reload, and that
the ID (``elitea_title``) field stays disabled throughout while the numeric
URL id — the actually-stable identifier across a rename — does not change.

Case Step 8 as literally authored ("ID field has the original auto-generated
value") is stale/contradicted by live product behavior: the ID field's
*value* live-mirrors the renamed Display Name (confirmed disabled/read-only
throughout, but not value-frozen), matching ELITEA-1972's already-established
finding for the same field. Filed as CLARIFICATION, not a product defect —
see elitea-testing-public#541. This test asserts the corrected/live-true
expectation: ID field stays disabled + the numeric URL id stays stable across
rename+reload, per the AFS's Automation Hints (do NOT assert the ID field's
*value* is frozen — that assertion is false against correct product
behavior).

Test case: ELITEA-1963
AFS: test-specs/toolkits-credentials/l1_edit-credential-rename_ELITEA-1963.md
"""

import logging
import time

import allure
import pytest

from config import settings
from pages.credential_create_page import CredentialCreatePage
from pages.credential_detail_page import CredentialDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.p1, pytest.mark.regression]

SAVE_RESPONSE_TIMEOUT = 15_000


class TestCredentialEditRename:
    """ELITEA-1963 — Edit credential: rename, persist across reload, ID field behavior."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1963_edit-credential-rename.md",
        "onetest-ai Test Case link",
    )
    def test_edit_credential_rename_persists_after_reload(self, page, credential_api):
        """Renaming a credential persists after reload; numeric URL id stays stable, ID field stays disabled."""
        ts = str(int(time.time()))
        initial_name = f"autotest_cred_edit_{ts}"
        renamed_name = f"autotest_cred_renamed_{ts}"
        credential_id = None

        try:
            with allure.step("Step 1 — Create a credential of type Github"):
                create_page = CredentialCreatePage(page)
                create_page.navigate_to_type("github")

                console_messages = []
                page.on(
                    "console",
                    lambda msg: console_messages.append(msg) if msg.type in ("error", "warning") else None,
                )

                assert not create_page.is_save_enabled(), (
                    "Save should be disabled before any Display Name is entered"
                )

                create_page.set_display_name(initial_name)
                assert create_page.is_save_enabled(), "Save should become enabled once Display Name is filled"

                with page.expect_response(
                    lambda r: f"/configurations/configurations/{settings.elitea_project_id}" in r.url
                    and r.request.method == "POST",
                    timeout=SAVE_RESPONSE_TIMEOUT,
                ) as create_response_info:
                    create_page.save_button.click()
                create_response = create_response_info.value
                assert create_response.status == 200, (
                    f"Expected 200 from credential-create POST, got {create_response.status}"
                )
                create_page.wait_for_network()

            with allure.step("Step 2 — Open the credential detail page"):
                detail_page = CredentialDetailPage(page)
                detail_page.open_credential_by_name(initial_name)
                credential_id = detail_page.get_credential_id_from_url()
                assert detail_page.get_display_name() == initial_name, (
                    f"Detail page should show Display Name {initial_name!r}, "
                    f"got {detail_page.get_display_name()!r}"
                )
                assert detail_page.id_input.input_value() == initial_name, (
                    f"ID field should show {initial_name!r} right after creation, "
                    f"got {detail_page.id_input.input_value()!r}"
                )
                assert detail_page.is_id_field_disabled(), "ID field should be disabled at rest"

            with allure.step("Step 3 — Change Display Name to the renamed value"):
                detail_page.set_display_name(renamed_name)
                assert detail_page.get_display_name() == renamed_name, (
                    f"Display Name field should update to {renamed_name!r}, "
                    f"got {detail_page.get_display_name()!r}"
                )

            with allure.step("Step 4 — Verify the Save button becomes enabled"):
                assert detail_page.is_save_enabled(), (
                    "Save should become enabled once Display Name differs from its saved value"
                )

            with allure.step("Step 5 — Click Save"):
                with page.expect_response(
                    lambda r: (
                        f"/configurations/configuration/{settings.elitea_project_id}/{credential_id}" in r.url
                    )
                    and r.request.method == "PUT",
                    timeout=SAVE_RESPONSE_TIMEOUT,
                ) as rename_response_info:
                    detail_page.save_button.click()
                rename_response = rename_response_info.value
                assert rename_response.status == 200, (
                    f"Expected 200 from credential-rename PUT, got {rename_response.status}"
                )
                detail_page.wait_for_network()

            with allure.step("Step 6 — Reload the page"):
                # Save redirects away from the detail page (to /credentials/all), so the
                # detail page must be re-opened before a literal reload has anything to
                # reload — per AFS step 6 note.
                detail_page.open_credential_by_name(renamed_name)
                renamed_credential_id = detail_page.get_credential_id_from_url()
                assert renamed_credential_id == credential_id, (
                    f"Numeric URL id should stay {credential_id!r} across rename, "
                    f"got {renamed_credential_id!r}"
                )

                page.reload()
                detail_page.wait_for_page_load()

            with allure.step("Step 7 — Verify Display Name shows the renamed value"):
                assert detail_page.get_display_name() == renamed_name, (
                    f"Renamed Display Name should persist after reload, "
                    f"got {detail_page.get_display_name()!r}"
                )

            with allure.step(
                "Step 8 — Verify the ID field stays disabled and the numeric URL id "
                "remains unchanged (corrected assertion per elitea-testing-public#541: "
                "the elitea_title *value* live-mirrors the rename by design, matching "
                "ELITEA-1972's already-confirmed behavior — only the disabled state and "
                "the numeric URL id are the stable 'unchanged ID' observables)"
            ):
                assert detail_page.get_credential_id_from_url() == credential_id, (
                    f"Numeric URL id should still be {credential_id!r} after reload, "
                    f"got {detail_page.get_credential_id_from_url()!r}"
                )
                assert detail_page.is_id_field_disabled(), "ID field should remain disabled after reload"

            with allure.step("Side-channel check — no console errors/warnings across the full flow"):
                assert not console_messages, (
                    f"Unexpected console errors/warnings: {[m.text for m in console_messages]}"
                )

        finally:
            if credential_id is not None:
                with allure.step("Cleanup — delete the credential created for this test"):
                    credential_api.delete_credential(int(credential_id))
                    logger.info("Deleted credential id=%s", credential_id)
