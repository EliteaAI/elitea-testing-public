"""Test for Credential — Create Private Credential from Toolkit Flow.

Verifies a user can create a private credential directly from an existing
toolkit's Configuration credential dropdown (the "New private ... credentials"
CREATE-section option), and that the new credential is scoped private to its
creator (``project_id == personal_project_id``, ``shared: false``).

Uses an existing, shared GitHub toolkit in a TEAM project (id 471, "Elitea
Testing Team") as a read-only vehicle for the dropdown-shape assertion — the
identity has only viewer access there, so the toolkit's own Save button is
never clicked. The actual private-credential create flow (steps 6-8) always
lands in the identity's own personal project (399) regardless of which
project is active, per ``CredentialsSelect.jsx``'s ``createSelectHandler``.

Test case: ELITEA-1976
AFS: test-specs/toolkits-credentials/l1_create-private-credential-from-toolkit-dropdown_ELITEA-1976.md
"""

import logging
import re
import time

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.chat_page import ChatPage
from pages.credential_create_page import CredentialCreatePage
from pages.toolkit_detail_page import ToolkitDetailPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

SAVE_RESPONSE_TIMEOUT = 15_000
TEAM_PROJECT_ID = "471"  # "Elitea Testing Team" — viewer-only, confirmed multi-member team project


class TestCredentialCreatePrivateFromToolkitDropdown:
    """ELITEA-1976 — Create a private credential from a toolkit's Configuration dropdown."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "toolkits-credentials/ELITEA-1976_create-private-credential-from-toolkit-dropdown.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_create_private_credential_from_toolkit_dropdown(
        self, page, credential_api, toolkit_api, _browser_cookies
    ):
        """Create a private GitHub credential via a toolkit's Configuration dropdown
        and verify it is linked, selectable, and scoped private to its creator."""
        if not settings.git_hub_token:
            pytest.skip("GIT_HUB_TOKEN not set in .env.test - required for credential test data")

        ts = int(time.time())
        display_name = f"autotest_private_cred_{ts}"
        credential_id = None
        new_tab = None

        try:
            with allure.step("Step 1 — Switch active project to the team project (id 471)"):
                chat_page = ChatPage(page)
                chat_page.navigate_to_chat()
                chat_page.switch_project(TEAM_PROJECT_ID)
                assert TEAM_PROJECT_ID in page.url or "Elitea Testing Team" in chat_page.get_selected_project_text(), (
                    f"Expected the active project to be switched to id={TEAM_PROJECT_ID}, "
                    f"selector now reads {chat_page.get_selected_project_text()!r}"
                )

            with allure.step("Step 2 — Navigate to the Toolkits section, open the existing Github toolkit"):
                team_toolkit_api = ToolkitAPI(browser_cookies=_browser_cookies, project_id=TEAM_PROJECT_ID)
                github_toolkits = team_toolkit_api.list_all_toolkits(params={"toolkit_type": "github"})
                assert github_toolkits, (
                    f"Expected at least one existing GitHub-type toolkit in project {TEAM_PROJECT_ID} "
                    f"(AFS precondition) — found none"
                )
                toolkit_id = github_toolkits[0]["id"]
                logger.info("Using existing team-project GitHub toolkit id=%s", toolkit_id)

                toolkit_page = ToolkitDetailPage(page)
                toolkit_page.navigate_to_toolkit(toolkit_id)
                expect(toolkit_page.toolkit_title).to_be_visible()
                expect(toolkit_page.configuration_tab).to_be_attached()

            with allure.step('Step 3 — Click the "Github Configuration" credential dropdown'):
                toolkit_page.open_credential_dropdown("github")
                expect(toolkit_page.get_create_option(private=True)).to_be_visible()

            with allure.step(
                'Step 4 — Verify the dropdown shows two sections: "CREATE" and '
                '"Saved github Credentials"'
            ):
                create_header = toolkit_page.get_select_group_header("Create")
                saved_header = toolkit_page.get_select_group_header("Saved github Credentials")
                expect(create_header).to_be_visible()
                expect(saved_header).to_be_visible()
                assert create_header.inner_text().strip().upper() == "CREATE", (
                    f"Expected the CREATE header's rendered text to read 'CREATE' "
                    f"(uppercase via CSS), got {create_header.inner_text()!r}"
                )
                assert saved_header.inner_text().strip().upper() == "SAVED GITHUB CREDENTIALS", (
                    f"Expected the Saved-credentials header's rendered text to read "
                    f"'SAVED GITHUB CREDENTIALS', got {saved_header.inner_text()!r}"
                )

            with allure.step(
                "Step 5 — Verify the CREATE section has exactly two options, in order: "
                '"New private github credentials" then "New project github credentials"'
            ):
                private_option = toolkit_page.get_create_option(private=True)
                project_option = toolkit_page.get_create_option(private=False)
                expect(private_option).to_be_visible()
                expect(project_option).to_be_visible()
                assert "New private github credentials" in (private_option.text_content() or ""), (
                    f"Expected the private CREATE option to read 'New private github "
                    f"credentials', got {private_option.text_content()!r}"
                )
                assert "New project github credentials" in (project_option.text_content() or ""), (
                    f"Expected the project CREATE option to read 'New project github "
                    f"credentials', got {project_option.text_content()!r}"
                )
                private_box = private_option.bounding_box()
                project_box = project_option.bounding_box()
                assert private_box and project_box and private_box["y"] < project_box["y"], (
                    "Expected 'New private ...' to render above 'New project ...' "
                    f"(private y={private_box}, project y={project_box})"
                )

            with allure.step('Step 6 — Click "New private github credentials"'):
                new_tab = toolkit_page.click_create_option(private=True)
                expected_path = f"/{settings.elitea_project_id}/credentials/create-credential/github"
                assert expected_path in new_tab.url, (
                    f"Expected the new tab URL to contain {expected_path!r} "
                    f"(scoped to personal_project_id={settings.elitea_project_id}, independent of the "
                    f"currently-active team project {TEAM_PROJECT_ID}), got {new_tab.url!r}"
                )

            with allure.step("Step 7 — Fill Display Name, select Token auth, fill Access Token"):
                create_page = CredentialCreatePage(new_tab)
                create_page.wait_for_page_load()
                create_page.set_display_name(display_name)
                assert create_page.display_name_input.input_value() == display_name, (
                    f"Display Name field should show {display_name!r} after filling"
                )
                create_page.select_auth_method("token")
                assert create_page.auth_radio("token").is_checked(), (
                    "The 'Token' auth radio should be checked after clicking it"
                )
                # Guard against the shared MUI-field-fill technique silently no-oping
                # on this field across the auth-method radio re-render (Axis 2 addition).
                assert create_page.display_name_input.input_value() == display_name, (
                    f"Display Name field should still read {display_name!r} after "
                    f"switching auth method — it must not be cleared by the re-render"
                )
                create_page.set_access_token(settings.git_hub_token)

            with allure.step("Step 8 — Click Save"):
                with new_tab.expect_response(
                    lambda r: (
                        f"/configurations/configurations/{settings.elitea_project_id}" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=SAVE_RESPONSE_TIMEOUT,
                ) as create_response_info:
                    create_page.save_button.click()
                create_response = create_response_info.value
                assert create_response.status == 200, (
                    f"Expected 200 from the credential-create POST, got {create_response.status}"
                )
                create_body = create_response.json()
                credential_id = create_body.get("id")
                assert credential_id, "Expected a numeric id in the create response"
                new_tab.wait_for_url(re.compile(r".*/credentials/all/?(\?.*)?$"), timeout=SAVE_RESPONSE_TIMEOUT)

            with allure.step("Step 9 — Close the new tab, return focus to the original toolkit tab"):
                new_tab.close()
                new_tab = None
                page.bring_to_front()

            with allure.step(
                "Step 10 — Reload the toolkit page, re-open the dropdown, click Refresh "
                "the configurations (sidesteps the #1047 stays-open clarification by "
                "forcing fresh, unambiguous state)"
            ):
                toolkit_page.navigate_to_toolkit(toolkit_id)
                expect(toolkit_page.toolkit_title).to_be_visible()
                toolkit_page.open_credential_dropdown("github")
                toolkit_page.click_refresh_configurations()

            with allure.step(
                "Step 11 — Verify the new private credential appears in the Saved "
                "github Credentials section"
            ):
                new_option = toolkit_page.get_saved_option(elitea_title=display_name, private=True)
                expect(new_option).to_be_visible()
                assert display_name in (new_option.text_content() or ""), (
                    f"Expected the new saved option to display {display_name!r}, "
                    f"got {new_option.text_content()!r}"
                )

            with allure.step("Step 12 — Select the new private credential"):
                toolkit_page.select_saved_credential(elitea_title=display_name, private=True)
                selected_text = toolkit_page.get_credential_select_text("github")
                assert display_name in selected_text, (
                    f"Expected the Configuration combobox to display {display_name!r} "
                    f"after selection, got {selected_text!r}"
                )

            with allure.step(
                "Step 14 — Verify private scope via the API: project_id == "
                "personal_project_id and shared == false"
            ):
                assert str(create_body.get("project_id")) == str(settings.elitea_project_id), (
                    f"Expected the created credential's project_id to equal the "
                    f"identity's personal_project_id ({settings.elitea_project_id}), "
                    f"got {create_body.get('project_id')!r} — this is the concrete "
                    f"mechanism behind 'private to its creator'"
                )
                assert create_body.get("shared") is False, (
                    f"Expected the created credential's shared flag to be False, "
                    f"got {create_body.get('shared')!r}"
                )

        finally:
            with allure.step("Cleanup — delete the created private credential; leave the team toolkit untouched"):
                if new_tab is not None:
                    try:
                        new_tab.close()
                    except Exception:
                        pass
                if credential_id is not None:
                    credential_api.delete_credential(int(credential_id))
                    logger.info("Deleted credential id=%s", credential_id)
