"""Test for Credential — Create Project Credential from Toolkit Flow.

Verifies a user can create a **project-scoped** credential directly from an
existing toolkit's Configuration credential dropdown (the "New project ...
credentials" CREATE-section option), that it shows up in the toolkit's saved
list after a refresh, is selectable, and is scoped to the active *team*
project rather than the creator's personal project.

Project-scoped mirror of ELITEA-1976 (private-scoped). ``CredentialsSelect.jsx``
resolves the create-form's project as
``option.private ? personal_project_id : selectedProjectId``, so this flow needs
a team project the identity can WRITE credentials in — that is
``settings.users_team_project_id`` (400, "UI Testing"); projects 471/406/25 all
return 403 on ``configurations.configuration.create``.

Substitution declared (TRANSIT only, AFS § Fidelity Declaration): project 400
holds no toolkits at all, so the case's precondition GitHub toolkit — and the
credential its ``github_configuration`` references — are seeded through the API
and deleted in teardown. They merely produce the surface that hosts the
dropdown; every observable this case asserts (the CREATE option, the create
form, the Save response, the refreshed saved list, the selection, the scope) is
produced by the live system through the UI. The Access Token is a placeholder
string, which the case's own Test Data row authorises
("any valid or placeholder token").

Test case: ELITEA-1977
AFS: test-specs/toolkits-credentials/l1_create-project-credential-from-toolkit-dropdown_ELITEA-1977.md
"""

import logging
import re
import time

import allure
import pytest
from api import CredentialAPI, ToolkitAPI
from config import settings
from pages.chat_page import ChatPage
from pages.credential_create_page import CredentialCreatePage
from pages.toolkit_detail_page import ToolkitDetailPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.credentials,
    pytest.mark.toolkits,
    pytest.mark.p1,
    pytest.mark.regression,
    pytest.mark.new,
]

SAVE_RESPONSE_TIMEOUT = 15_000
PLACEHOLDER_TOKEN = "placeholder_token_elitea_1977"  # case Test Data: "any valid or placeholder token"


class TestCredentialCreateProjectFromToolkitDropdown:
    """ELITEA-1977 — Create a project credential from a toolkit's Configuration dropdown."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "toolkits-credentials/ELITEA-1977_create-project-credential-from-toolkit-flow.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_create_project_credential_from_toolkit_dropdown(self, page, _browser_cookies):
        """Create a project GitHub credential via a toolkit's Configuration dropdown
        and verify it is listed, linked, and scoped to the team project."""
        team_project_id = str(settings.users_team_project_id)
        assert team_project_id != str(settings.elitea_project_id), (
            f"The project-credential CREATE option only renders off the personal project — "
            f"users_team_project_id ({team_project_id}) must differ from "
            f"elitea_project_id ({settings.elitea_project_id})"
        )

        ts = int(time.time())
        display_name = f"autotest_proj_cred_{ts}"  # < 32 chars — the form truncates silently
        seed_cred_title = f"autotest_tk_seed_{ts}"
        assert len(display_name) <= 32, f"Display Name must stay under the 32-char cap, got {len(display_name)}"

        team_credential_api = CredentialAPI(browser_cookies=_browser_cookies, project_id=team_project_id)
        team_toolkit_api = ToolkitAPI(browser_cookies=_browser_cookies, project_id=team_project_id)

        credential_id = None
        seed_credential_id = None
        seed_toolkit_id = None
        new_tab = None

        try:
            with allure.step(f"Step 1 — Switch the active project to the writable team project (id {team_project_id})"):
                chat_page = ChatPage(page)
                chat_page.navigate_to_chat()
                chat_page.switch_project(team_project_id)
                selected = chat_page.get_selected_project_text()
                assert team_project_id in page.url or "UI Testing" in selected, (
                    f"Expected the active project to be switched to id={team_project_id}, "
                    f"selector now reads {selected!r}"
                )

            with allure.step(
                "Step 2 — Seed the precondition Github credential + Github toolkit in that "
                "project (TRANSIT), then open the toolkit's detail page"
            ):
                seed_credential = team_credential_api.create_credential(
                    {
                        "type": "github",
                        "elitea_title": seed_cred_title,
                        "label": seed_cred_title,
                        "name": seed_cred_title,
                        "data": {"base_url": "https://api.github.com"},
                    }
                )
                seed_credential_id = seed_credential["id"]
                seed_toolkit = team_toolkit_api.create_toolkit(
                    name=f"autotest_tk_1977_{ts}",
                    description="ELITEA-1977 precondition toolkit (seeded, deleted in teardown)",
                    toolkit_type="github",
                    settings={
                        "github_configuration": {"elitea_title": seed_cred_title, "private": False},
                        "repository": "EliteaAI/elitea-testing-public",
                        "active_branch": "main",
                        "base_branch": "main",
                        "selected_tools": ["get_issues"],
                    },
                )
                seed_toolkit_id = seed_toolkit["id"]
                logger.info(
                    "Seeded precondition toolkit id=%s credential id=%s in project %s",
                    seed_toolkit_id, seed_credential_id, team_project_id,
                )

                toolkit_page = ToolkitDetailPage(page)
                toolkit_page.navigate_to_toolkit(seed_toolkit_id)
                expect(toolkit_page.toolkit_title).to_be_visible()
                expect(toolkit_page.configuration_tab).to_be_attached()
                assert toolkit_page.get_toolkit_title() == seed_toolkit["name"], (
                    f"Expected the detail page to show the seeded toolkit "
                    f"{seed_toolkit['name']!r}, got {toolkit_page.get_toolkit_title()!r}"
                )

            with allure.step('Step 3 — Click the "Github Configuration" credential dropdown'):
                toolkit_page.open_credential_dropdown("github")
                expect(toolkit_page.get_create_option(private=False)).to_be_visible()

            with allure.step(
                'Step 4 — Verify the dropdown shows both sections: "CREATE" and '
                '"Saved github Credentials"'
            ):
                create_header = toolkit_page.get_select_group_header("Create")
                saved_header = toolkit_page.get_select_group_header("Saved github Credentials")
                # The all-caps rendering is CSS text-transform — assert the underlying strings.
                expect(create_header).to_have_text("Create")
                expect(saved_header).to_have_text("Saved github Credentials")

            with allure.step(
                'Step 5 — Verify the CREATE section offers "New project github credentials" '
                "(renders only because the active project differs from personal_project_id)"
            ):
                project_option = toolkit_page.get_create_option(private=False)
                expect(project_option).to_be_visible()
                assert "New project github credentials" in (project_option.text_content() or ""), (
                    f"Expected the project CREATE option to read 'New project github "
                    f"credentials', got {project_option.text_content()!r}"
                )

            with allure.step('Step 6 — Click "New project github credentials"'):
                new_tab = toolkit_page.click_create_option(private=False)
                expected_path = f"/{team_project_id}/credentials/create-credential/github"
                assert expected_path in new_tab.url, (
                    f"Expected the new tab URL to contain {expected_path!r} — the create form is "
                    f"scoped to the SELECTED project, which is the mechanism behind a 'project' "
                    f"credential — got {new_tab.url!r}"
                )

            with allure.step("Step 7 — Fill Display Name, select Token auth, fill the placeholder Access Token"):
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
                assert create_page.display_name_input.input_value() == display_name, (
                    f"Display Name field should still read {display_name!r} after switching "
                    f"auth method — it must not be cleared by the re-render"
                )
                create_page.set_access_token(PLACEHOLDER_TOKEN)

            with allure.step("Step 8 — Click Save"):
                with new_tab.expect_response(
                    lambda r: (
                        f"/configurations/configurations/{team_project_id}" in r.url
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
                assert create_body.get("label") == display_name, (
                    f"Expected the saved credential's label to be {display_name!r}, "
                    f"got {create_body.get('label')!r}"
                )
                assert create_body.get("elitea_title") == display_name, (
                    f"Expected the saved credential's elitea_title to mirror the Display Name "
                    f"{display_name!r}, got {create_body.get('elitea_title')!r}"
                )
                new_tab.wait_for_url(re.compile(r".*/credentials/all/?(\?.*)?$"), timeout=SAVE_RESPONSE_TIMEOUT)

            with allure.step("Step 9 — Close the create tab, return focus to the original toolkit tab"):
                new_tab.close()
                new_tab = None
                page.bring_to_front()

            with allure.step(
                "Step 10 — Reload the toolkit page, re-open the dropdown, click Refresh the "
                "configurations (the menu never auto-closes after a CREATE click — #1047 — so a "
                "fresh load makes the re-open unambiguous)"
            ):
                toolkit_page.navigate_to_toolkit(seed_toolkit_id)
                expect(toolkit_page.toolkit_title).to_be_visible()
                toolkit_page.open_credential_dropdown("github")
                toolkit_page.click_refresh_configurations()

            with allure.step(
                "Step 11 — Verify the new credential appears under Saved github Credentials "
                "as a PROJECT credential (and not as a private one)"
            ):
                # The option list re-mounts after the refresh — web-first expect(), never is_visible().
                new_option = toolkit_page.get_saved_option(elitea_title=display_name, private=False)
                expect(new_option).to_be_visible()
                assert display_name in (new_option.text_content() or ""), (
                    f"Expected the new saved option to display {display_name!r}, "
                    f"got {new_option.text_content()!r}"
                )
                # The credential must not also appear in the private (personal-project) bucket —
                # "private" is isConfigurationPersonal in CredentialsSelect.jsx.
                expect(toolkit_page.get_saved_option(elitea_title=display_name, private=True)).to_have_count(0)

            with allure.step("Step 12 — Select the new project credential"):
                toolkit_page.select_saved_credential(elitea_title=display_name, private=False)
                selected_text = toolkit_page.get_credential_select_text("github")
                assert display_name in selected_text, (
                    f"Expected the Configuration combobox to display {display_name!r} "
                    f"after selection, got {selected_text!r}"
                )

            with allure.step(
                "Step 13 — Verify project scope via the API: project_id is the team project, "
                "not the creator's personal project"
            ):
                assert str(create_body.get("project_id")) == team_project_id, (
                    f"Expected the created credential's project_id to be the active team project "
                    f"({team_project_id}), got {create_body.get('project_id')!r} — this is the "
                    f"concrete mechanism behind 'visible to all project members': the saved list is "
                    f"GET /configurations/configurations/{{selectedProjectId}}, scoped to project "
                    f"membership"
                )
                assert str(create_body.get("project_id")) != str(settings.elitea_project_id), (
                    f"A project credential must NOT land in the creator's personal project "
                    f"({settings.elitea_project_id}), got {create_body.get('project_id')!r}"
                )

        finally:
            with allure.step("Cleanup — delete the created credential and the seeded toolkit/credential"):
                if new_tab is not None:
                    try:
                        new_tab.close()
                    except Exception:
                        pass
                if credential_id is not None:
                    team_credential_api.delete_credential(int(credential_id))
                    logger.info("Deleted credential id=%s", credential_id)
                if seed_toolkit_id is not None:
                    team_toolkit_api.delete_toolkit(int(seed_toolkit_id))
                    logger.info("Deleted seeded toolkit id=%s", seed_toolkit_id)
                if seed_credential_id is not None:
                    team_credential_api.delete_credential(int(seed_credential_id))
                    logger.info("Deleted seeded credential id=%s", seed_credential_id)
