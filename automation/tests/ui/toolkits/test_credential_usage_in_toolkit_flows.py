"""Test for Credential — Usage in Toolkit Flows.

Verifies a credential can be linked to a toolkit (pre-filled at creation
time and confirmed via the Configuration dropdown), that the linked
credential actually authenticates a real toolkit operation
(``list_branches_in_repo`` against the live GitHub API), and that deleting
the credential mid-flow leaves the toolkit's Configuration field in a
visible red/error mismatch state (not blank).

Test case: ELITEA-1979
AFS: test-specs/toolkits-credentials/l1_credential-usage-in-toolkit-flows_ELITEA-1979.md
"""

import logging
import re
import time

import allure
import pytest
from config import settings
from pages.toolkit_detail_page import ToolkitDetailPage
from pages.toolkit_test_settings_page import ToolkitTestSettingsPage
from pages.toolkits_list_page import ToolkitsListPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression]

RUN_TOOL_TIMEOUT = 20_000


class TestCredentialUsageInToolkitFlows:
    """ELITEA-1979 — Credential linked to a toolkit, authenticates a real
    operation, and the toolkit reflects a mismatch state after deletion."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "toolkits-credentials/ELITEA-1979_credential-usage-in-toolkit-flows.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_credential_usage_and_deletion_mismatch(self, page, credential_api, toolkit_api):
        """Credential is pre-filled + linked on toolkit creation, authenticates a
        real GitHub API call, and its deletion produces a visible mismatch state."""
        if not settings.git_hub_token:
            pytest.skip("GIT_HUB_TOKEN not set in .env.test - required for credential test data")

        ts = int(time.time())
        credential_name = f"autotest_toolkit_cred_{ts}"
        toolkit_name = f"autotest_toolkit_tk_{ts}"
        credential_id = None
        toolkit_id = None
        credential_deleted = False

        try:
            with allure.step(f"Step 1 — Create a valid Github credential {credential_name!r}"):
                cred = credential_api.create_github_credential(
                    display_name=credential_name,
                    base_url=settings.github_base_url,
                    token=settings.git_hub_token,
                    elitea_title=credential_name,
                )
                credential_id = cred["id"]
                elitea_title = cred["elitea_title"]
                assert credential_id and elitea_title, "Expected an id + elitea_title in the create response"

            with allure.step("Step 2 — Navigate to the Toolkits section"):
                toolkits_list = ToolkitsListPage(page)
                toolkits_list.navigate()

            with allure.step(
                "Step 3 — Create a Github toolkit linked to the step-1 credential, "
                "navigate to its detail page"
            ):
                # NOT ToolkitAPI.create_github_toolkit() — it hardcodes
                # github_configuration.private=False, which mismatches a
                # credential created in the identity's OWN (personal) project
                # (CredentialsSelect.jsx's selectedOption lookup requires an
                # exact private-flag match) and would show the mismatch
                # footer immediately, before step 7 ever runs. private=True
                # correctly reflects that this credential is personal-scoped.
                toolkit = toolkit_api.create_toolkit(
                    name=toolkit_name,
                    description=f"Auto-created for {toolkit_name}",
                    toolkit_type="github",
                    settings={
                        "github_configuration": {
                            "elitea_title": elitea_title,
                            "private": True,
                        },
                        "repository": settings.git_repo,
                        "active_branch": "main",
                        "base_branch": "main",
                    },
                )
                toolkit_id = toolkit["id"]

                toolkit_page = ToolkitDetailPage(page)
                toolkit_page.navigate_to_toolkit(toolkit_id)
                expect(toolkit_page.toolkit_title).to_be_visible()
                expect(toolkit_page.configuration_tab).to_be_attached()

            with allure.step(
                "Step 4/5 — Confirm the credential selection: Configuration combobox "
                "displays the step-1 credential's name"
            ):
                selected_text = toolkit_page.get_credential_select_text("github")
                assert credential_name in selected_text, (
                    f"Expected the Configuration combobox to display "
                    f"{credential_name!r} pre-filled at toolkit creation, got "
                    f"{selected_text!r}"
                )

            with allure.step(
                "Step 6 — Open Test Settings, select list_branches_in_repo, run it: "
                "proves the linked credential actually authenticates"
            ):
                test_settings = ToolkitTestSettingsPage(page)
                test_settings.select_tool_from_empty_state("list_branches_in_repo")
                test_settings.wait_for_panel()
                test_settings.run_tool()
                result_text = test_settings.wait_for_tool_result(timeout=RUN_TOOL_TIMEOUT)
                assert "✅ list_branches_in_repo" in result_text, (
                    f"Expected list_branches_in_repo to succeed (✅ marker), got: {result_text!r}"
                )
                assert re.search(r'"name"\s*:', result_text), (
                    f"Expected the result to contain real branch objects with a "
                    f"'name' key (not just 'no error'), got: {result_text!r}"
                )

            with allure.step(f"Step 7 — Navigate back to Credentials, delete {credential_name!r}"):
                credential_api.delete_credential(credential_id)
                credential_deleted = True
                remaining = credential_api.list_all_credentials()
                remaining_ids = [c.get("id") for c in remaining]
                assert credential_id not in remaining_ids, (
                    f"Expected credential id={credential_id} to be gone after delete, "
                    f"still present in {remaining_ids}"
                )

            with allure.step(
                "Step 8 — Return to the toolkit's detail page (reload): Configuration "
                "field shows the red mismatch state, not blank"
            ):
                toolkit_page.navigate_to_toolkit(toolkit_id)
                assert toolkit_page.is_credential_select_mismatched("github"), (
                    "Expected the Configuration combobox to carry "
                    "aria-invalid=\"true\" after its linked credential was deleted"
                )
                mismatch_text = toolkit_page.get_credential_select_text("github")
                assert credential_name in mismatch_text, (
                    f"Expected the combobox to still render the now-orphaned "
                    f"credential name {credential_name!r} (NOT a blank field), "
                    f"got {mismatch_text!r}"
                )
                expect(toolkit_page.credential_select_mismatch_footer).to_be_visible()
                assert "does not match any available configurations" in (
                    toolkit_page.credential_select_mismatch_footer.text_content() or ""
                ), (
                    f"Expected the mismatch footer text to read 'Your configuration "
                    f"does not match any available configurations.', got "
                    f"{toolkit_page.credential_select_mismatch_footer.text_content()!r}"
                )

        finally:
            with allure.step("Cleanup — delete the toolkit (credential already deleted in step 7)"):
                if toolkit_id is not None:
                    toolkit_api.delete_toolkit(toolkit_id)
                    logger.info("Deleted toolkit id=%s", toolkit_id)
                if credential_id is not None and not credential_deleted:
                    credential_api.delete_credential(credential_id)
                    logger.info("Deleted credential id=%s (fallback — step 7 didn't run)", credential_id)
