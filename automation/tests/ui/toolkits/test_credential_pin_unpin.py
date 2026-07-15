"""Test for Credential — Pin/Unpin.

Verifies that a credential can be pinned to the top of the Credentials list
(list-row "Pin to top" icon button), that the detail page's three-dot menu
reflects the pinned state ("Unpin from top"), and that unpinning reverts
both the menu label and the list position.

Test case: ELITEA-1974
AFS: test-specs/toolkits-credentials/l1_credential-pin-unpin_ELITEA-1974.md
"""

import logging
import time

import allure
import pytest

from config import settings
from pages.credential_detail_page import CredentialDetailPage
from pages.credentials_list_page import CredentialsListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.p1, pytest.mark.regression]


class TestCredentialPinUnpin:
    """ELITEA-1974 — Credential list pin/unpin round trip."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1974_credential-pin-unpin.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_credential_pin_moves_to_top_and_unpin_reverts(self, page, credential_api):
        """Pinning a credential moves it to the top of the list; unpinning reverts it."""
        if not settings.git_hub_token:
            pytest.skip("GIT_HUB_TOKEN not set in .env.test - required for credential test data")

        ts = int(time.time())
        cred_a_name = f"autotest_pin_cred_a_{ts}"[:32]
        cred_b_name = f"autotest_pin_cred_b_{ts + 5}"[:32]
        credential_a_id = None
        credential_b_id = None

        try:
            with allure.step("Setup — Create Credential A and Credential B via API"):
                cred_a = credential_api.create_github_credential(
                    display_name=cred_a_name,
                    base_url=settings.github_base_url,
                    token=settings.git_hub_token,
                )
                credential_a_id = cred_a["id"]

                # Credential B is created second so it sorts above A under the
                # list's default created_at-desc order — this is what gives
                # Steps 2/7 a real "position" to move to/from (AFS Test Data).
                cred_b = credential_api.create_github_credential(
                    display_name=cred_b_name,
                    base_url=settings.github_base_url,
                    token="unused-token-never-validated-by-this-case",
                )
                credential_b_id = cred_b["id"]

                assert credential_a_id, "Expected a numeric id for Credential A"
                assert credential_b_id, "Expected a numeric id for Credential B"
                logger.info(
                    "Created credentials — A id=%s name=%s, B id=%s name=%s",
                    credential_a_id, cred_a_name, credential_b_id, cred_b_name,
                )

            with allure.step("Step 1 — Navigate to the Credentials list and capture the baseline order"):
                list_page = CredentialsListPage(page)
                list_page.navigate()

                console_messages = []
                page.on(
                    "console",
                    lambda msg: console_messages.append(msg) if msg.type in ("error", "warning") else None,
                )

                baseline_order = list_page.get_display_name_order()
                index_a = baseline_order.index(cred_a_name)
                index_b = baseline_order.index(cred_b_name)
                assert index_b < index_a, (
                    f"Expected Credential B above Credential A before pinning, got order: {baseline_order}"
                )
                assert list_page.get_pin_toggle_label(credential_a_id) == "Pin to top", (
                    "Credential A's list-row pin button should read 'Pin to top' before pinning"
                )

            with allure.step("Step 2 — Click 'Pin to top' on Credential A and verify it moves to the top"):
                response = list_page.click_pin_toggle(credential_a_id)
                assert response.status == 201, (
                    f"Expected 201 Created from the pin request, got {response.status}"
                )

                pinned_order = list_page.get_display_name_order()
                index_a = pinned_order.index(cred_a_name)
                index_b = pinned_order.index(cred_b_name)
                assert index_a < index_b, (
                    f"Expected Credential A above Credential B after pinning, got order: {pinned_order}"
                )
                assert list_page.get_pin_toggle_label(credential_a_id) == "Unpin from top", (
                    "Credential A's list-row pin button should flip to 'Unpin from top' after pinning"
                )

            with allure.step("Step 3 — Navigate to the pinned credential's detail page"):
                list_page.click_credential_card(cred_a_name)
                detail_page = CredentialDetailPage(page)
                detail_page.wait_for_page_load()
                assert detail_page.get_display_name() == cred_a_name, (
                    "Detail page should show Credential A's Display Name after navigating from its card"
                )

            with allure.step("Step 4 — Click the three-dot menu"):
                detail_page.open_controls_menu()

            with allure.step("Step 5 — Verify the menu shows 'Unpin from top'"):
                assert detail_page.get_pin_toggle_menu_label() == "Unpin from top", (
                    "Pin-toggle menu item should read 'Unpin from top' while the credential is pinned"
                )

            with allure.step("Step 6 — Click 'Unpin from top'"):
                response = detail_page.click_pin_toggle_menu_item()
                assert response.status == 204, (
                    f"Expected 204 No Content from the unpin request, got {response.status}"
                )

            with allure.step(
                "Step 7a — Re-open the three-dot menu and verify it flips back to 'Pin to top' immediately"
            ):
                detail_page.open_controls_menu()
                assert detail_page.get_pin_toggle_menu_label() == "Pin to top", (
                    "Pin-toggle menu item should flip back to 'Pin to top' immediately after unpinning, "
                    "before navigating away"
                )

            with allure.step(
                "Step 7b — Navigate back to the Credentials list and verify the original order is restored"
            ):
                list_page.navigate()
                reverted_order = list_page.get_display_name_order()
                index_a = reverted_order.index(cred_a_name)
                index_b = reverted_order.index(cred_b_name)
                assert index_b < index_a, (
                    f"Expected Credential B above Credential A again after unpinning, got order: {reverted_order}"
                )
                assert list_page.get_pin_toggle_label(credential_a_id) == "Pin to top", (
                    "Credential A's list-row pin button should read 'Pin to top' again after unpinning"
                )

            with allure.step("Side-channel check — no console errors/warnings across the full flow"):
                assert not console_messages, (
                    f"Unexpected console errors/warnings: {[m.text for m in console_messages]}"
                )

        finally:
            with allure.step("Cleanup — delete both credentials created for this test"):
                if credential_a_id is not None:
                    credential_api.delete_credential(credential_a_id)
                    logger.info("Deleted credential id=%s", credential_a_id)
                if credential_b_id is not None:
                    credential_api.delete_credential(credential_b_id)
                    logger.info("Deleted credential id=%s", credential_b_id)
