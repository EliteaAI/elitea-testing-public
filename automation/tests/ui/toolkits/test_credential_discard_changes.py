"""Test for Credential detail — Discard Changes.

Verifies the Credential-detail Save/Discard tab-bar flow: editing the
Display Name enables Discard (and Save), the Discard confirmation modal
shows the expected warning, and confirming Discard reverts the field and
returns Save/Discard to their disabled baseline.

Test case: ELITEA-1971
AFS: test-specs/toolkits-credentials/l1_credential-discard-changes_ELITEA-1971.md
"""

import logging
import time

import allure
import pytest

from config import settings
from pages.credential_detail_page import CredentialDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.p1, pytest.mark.regression]


class TestCredentialDiscardChanges:
    """ELITEA-1971 — Credential detail Discard-changes flow."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1971_credential-discard-changes.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_credential_discard_changes_reverts_display_name(self, page, credential_api):
        """Editing the Display Name and confirming Discard reverts the field."""
        if not settings.git_hub_token:
            pytest.skip("GIT_HUB_TOKEN not set in .env.test - required for credential test data")

        ts = str(int(time.time()))
        cred_name = f"autotest_discard_cred_{ts}"[:32]
        changed_name = "autotest_changed"
        credential_id = None

        try:
            with allure.step("Step 1 — Create GitHub credential via API"):
                cred = credential_api.create_github_credential(
                    display_name=cred_name,
                    base_url=settings.github_base_url,
                    token=settings.git_hub_token,
                )
                credential_id = cred["id"]
                assert cred["label"] == cred_name, f"Expected label {cred_name!r}, got {cred['label']!r}"
                assert cred["type"] == "github", f"Expected type 'github', got {cred['type']!r}"
                assert credential_id, "Expected a numeric credential id in the create response"
                logger.info("Created GitHub credential id=%s label=%s", credential_id, cred_name)

            with allure.step("Step 2 — Open the credential's detail page and verify the baseline state"):
                detail_page = CredentialDetailPage(page)
                detail_page.open_credential_by_name(cred_name)

                # Console listener starts AFTER the list->detail navigation:
                # that precondition step can hit a known, already-filed,
                # out-of-scope defect (elitea-testing-public#518) that the
                # page object recovers from via one reload — the recovery
                # itself logs the error to console. The side-channel check
                # below is scoped to the Discard flow under test (steps 3-9),
                # matching the AFS's own console check (taken after Step 9).
                console_messages = []
                page.on(
                    "console",
                    lambda msg: console_messages.append(msg) if msg.type in ("error", "warning") else None,
                )

                assert detail_page.get_display_name() == cred_name, (
                    "Display Name field should show the created credential's name on load"
                )
                assert not detail_page.is_save_enabled(), "Save should be disabled with no pending changes"
                assert not detail_page.is_discard_enabled(), (
                    "Discard should be disabled with no pending changes"
                )

            with allure.step("Step 3 — Change the Display Name"):
                detail_page.set_display_name(changed_name)
                assert detail_page.get_display_name() == changed_name, (
                    f"Display Name field should show {changed_name!r} after editing"
                )

            with allure.step("Step 4 — Verify Discard (and Save) become enabled"):
                assert detail_page.is_discard_enabled(), "Discard should be enabled after an edit"
                assert detail_page.is_save_enabled(), "Save should also be enabled after an edit"

            with allure.step(
                "Step 5/6 — Click Discard and verify the confirmation modal shows the expected warning"
            ):
                detail_page.click_discard()
                modal_text = detail_page.get_discard_confirm_message()
                assert "Warning" in modal_text, f"Expected modal heading 'Warning', got: {modal_text!r}"
                assert "Are you sure you want to discard changes?" in modal_text, (
                    f"Expected the exact discard-changes warning text, got: {modal_text!r}"
                )

            with allure.step("Step 7 — Confirm Discard inside the modal"):
                detail_page.confirm_discard()

            with allure.step("Step 8 — Verify the Display Name reverted to its original value"):
                assert detail_page.get_display_name() == cred_name, (
                    f"Display Name should revert to {cred_name!r} after confirming Discard"
                )

            with allure.step("Step 9 — Verify Save (and Discard) returned to the disabled state"):
                assert not detail_page.is_save_enabled(), "Save should be disabled again after Discard"
                assert not detail_page.is_discard_enabled(), "Discard should be disabled again after Discard"

            with allure.step("Side-channel check — no console errors/warnings across the flow"):
                assert not console_messages, (
                    f"Unexpected console errors/warnings: {[m.text for m in console_messages]}"
                )

        finally:
            if credential_id is not None:
                with allure.step("Cleanup — delete the credential created for this test"):
                    credential_api.delete_credential(credential_id)
                    logger.info("Deleted credential id=%s", credential_id)
