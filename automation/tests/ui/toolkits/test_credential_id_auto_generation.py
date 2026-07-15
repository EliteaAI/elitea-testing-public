"""Test for Credential — ID Auto-Generation.

Verifies that a credential's ID field (``elitea_title``) is auto-generated
from the Display Name via a lowercase + underscore transform at creation
time and on every subsequent Display Name edit, remains genuinely disabled
throughout, and that the numeric URL-path ID (``id``, distinct from
``uuid``) is stable across a Display Name rename.

Test case: ELITEA-1972
AFS: test-specs/toolkits-credentials/l1_credential-id-auto-generation_ELITEA-1972.md
"""

import logging
import time

import allure
import pytest

from pages.credential_create_page import CredentialCreatePage
from pages.credential_detail_page import CredentialDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.p1, pytest.mark.regression]


class TestCredentialIdAutoGeneration:
    """ELITEA-1972 — Credential ID auto-generation + URL stability."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1972_credential-id-auto-generation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_credential_id_auto_generation_and_url_stability(self, page, credential_api):
        """The ID field auto-generates from the Display Name and the URL id is stable across rename."""
        ts = str(int(time.time()))
        initial_name = f"My Test Credential {ts}"
        renamed_name = f"My Renamed Credential {ts}"
        expected_initial_id = f"my_test_credential_{ts}"
        expected_renamed_id = f"my_renamed_credential_{ts}"
        credential_id = None

        try:
            with allure.step("Step 1 — Navigate to the GitHub credential-type create form"):
                create_page = CredentialCreatePage(page)
                create_page.navigate_to_type("github")
                assert not create_page.is_save_enabled(), (
                    "Save should be disabled before any Display Name is entered"
                )

            with allure.step("Step 2 — Fill the Display Name field"):
                create_page.set_display_name(initial_name)
                assert create_page.display_name_input.input_value() == initial_name, (
                    f"Display Name field should show {initial_name!r} after filling"
                )
                assert create_page.is_save_enabled(), "Save should become enabled once Display Name is filled"

            with allure.step("Step 3 — Save the credential"):
                create_page.save_button.click()
                create_page.wait_for_network()

            with allure.step(
                "Step 4 — Open the credential detail page and verify the auto-generated ID slug"
            ):
                detail_page = CredentialDetailPage(page)
                detail_page.open_credential_by_name(initial_name)
                credential_id = detail_page.get_credential_id_from_url()
                assert detail_page.id_input.input_value() == expected_initial_id, (
                    f"Expected auto-generated ID {expected_initial_id!r}, "
                    f"got {detail_page.id_input.input_value()!r}"
                )

            with allure.step("Step 5 — Verify the ID field is disabled (read-only)"):
                assert detail_page.is_id_field_disabled(), "ID field should be disabled right after creation"

                page.reload()
                detail_page.wait_for_page_load()
                assert detail_page.is_id_field_disabled(), (
                    "ID field should still be disabled on a fresh page reload"
                )

            with allure.step("Step 6 — Verify a numeric ID appears in the URL path"):
                assert credential_id.isdigit(), f"Expected a numeric credential id, got {credential_id!r}"

            with allure.step("Step 7 — Change the Display Name and Save again"):
                detail_page.set_display_name(renamed_name)
                assert detail_page.id_input.input_value() == expected_renamed_id, (
                    "ID field should live-mirror the new Display Name before Save "
                    f"(expected {expected_renamed_id!r}, got {detail_page.id_input.input_value()!r})"
                )
                assert detail_page.is_id_field_disabled(), "ID field should remain disabled while live-mirroring"

                detail_page.save_button.click()
                detail_page.wait_for_network()

            with allure.step(
                "Step 8 — Re-open the credential and verify the numeric URL ID did NOT change"
            ):
                detail_page.open_credential_by_name(renamed_name)
                renamed_credential_id = detail_page.get_credential_id_from_url()
                assert renamed_credential_id == credential_id, (
                    f"Numeric URL id should stay {credential_id!r} after rename, "
                    f"got {renamed_credential_id!r}"
                )
                assert detail_page.id_input.input_value() == expected_renamed_id, (
                    f"Expected persisted ID {expected_renamed_id!r} after reload, "
                    f"got {detail_page.id_input.input_value()!r}"
                )
                assert detail_page.is_id_field_disabled(), "ID field should remain disabled after reload"

        finally:
            if credential_id is not None:
                with allure.step("Cleanup — delete the credential created for this test"):
                    credential_api.delete_credential(int(credential_id))
                    logger.info("Deleted credential id=%s", credential_id)
