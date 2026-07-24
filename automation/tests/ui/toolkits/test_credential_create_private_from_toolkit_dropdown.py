"""Test for Credential — Create Private Credential from Toolkit Flow.

Verifies that a user can create a private credential directly from a
toolkit's Configuration credential dropdown, and that the new private
credential is only visible to its creator (structurally, via the API)
once linked to the toolkit.

Test case: ELITEA-1976
AFS: test-specs/toolkits-credentials/l2_create-private-credential-from-toolkit-dropdown_ELITEA-1976.md

Two declared improvisations (see AFS § Classification note):
1. Vehicle substitution GitHub -> GitLab. GitHub toolkit creation is blocked
   in this DEV deployment (403 "Toolkit type 'github' is not available in
   this deployment", already filed as elitea-testing-public#999); the
   credential-dropdown mechanic under test (ToolBaseProperty.jsx's
   `type === 'configuration'` branch -> CredentialsSelect) is 100% generic
   across every credential/toolkit type, and GitLab is live-confirmed
   creatable/Form-editable in this deployment.
2. Step 13 ("linked to the toolkit") is verified via the Configuration
   field's displayed value updating (real React form-state change), NOT via
   clicking the shared toolkit's own Save button — the acting identity is
   viewer-only in this multi-member project (two independent 403s on
   `configurations.configuration.create` / `models.applications.tools.create`),
   so the shared toolkit is only ever read + the form's unsaved selection is
   discarded (never Saved) at the end of the test.

Testids (EliteaAI/EliteaUI, automation/testids) — ALREADY PRESENT, verified
live via fresh `git fetch origin` + `git grep` against both `main` and
`automation/testids` at implementer time (redispatch pass): commits
EliteaAI/EliteaUI@1fef03f5 (combobox + CREATE-section options + Refresh
button) and EliteaAI/EliteaUI@d3953bb8 (grouped-select group headers) were
already pushed by the FIRST implementer pass on this case — no new EliteaUI
work was needed this pass. See AFS § Concrete Handles for the full wiring.
"""

import logging
import re

import allure
import pytest
from api import CredentialAPI, ToolkitAPI
from config import settings
from pages.credential_create_page import CredentialCreatePage
from pages.toolkit_detail_page import ToolkitDetailPage
from pages.toolkits_list_page import ToolkitsListPage

logger = logging.getLogger("elitea.tests.toolkits")

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.credentials, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
SAVE_RESPONSE_TIMEOUT = 15_000

# Team project — the ONLY project in this environment where a toolkit is
# genuinely multi-member (so BOTH CredentialsSelect CREATE options render —
# `Create_Project_Title` only pushes when `selectedProjectId != personal_
# project_id` — and "private = not visible to other members" is a
# meaningful claim). See AFS § Preconditions.
TEAM_PROJECT_ID = "471"

# Configuration schema field name for a GitLab-type toolkit's credential
# select (ToolBaseProperty.jsx's `k`) — see AFS § Automation Hints.
FIELD_KEY = "gitlab_configuration"

GITLAB_URL = "https://gitlab.com"
PLACEHOLDER_TOKEN = "autotest-never-authenticated-placeholder-token"  # noqa: S105 - not a real secret


def _is_known_project_471_secrets_403(msg) -> bool:
    """Filter the pre-existing, already-documented project-471 ``secrets`` 403.

    Project 471 ("Elitea Testing Team") surfaces a ``403 Forbidden`` on
    ``GET .../secrets/secrets/default/471`` on every page load, regardless of
    any action taken — an environment/permission-scoping artifact of that
    specific project, not a symptom of anything this case's automation
    touches. Same filter/idiom already established by
    ``test_open_conversation_today_section.py``; this test also switches the
    active project to 471 for its entire Toolkits/Configuration-dropdown flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default/471" in (text + location_url)


def _is_known_554_warning(msg) -> bool:
    """Filter the pre-existing, already-filed elitea-testing-public#554 — an
    RTK-Query timing race in ``EliteaUI/src/api/toolkits.js``'s
    ``toolkitTypes`` endpoint firing before ``useSelectedProjectId()``
    resolves (empty-projectId URL, 404s). Established general — already
    confirmed on two independent entry points by
    ``test_credential_create.py`` — and this test's Step 6 lands on the
    same create-credential surface in a new tab.
    """
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "elitea_core/toolkits/prompt_lib/" in location_url


def _is_known_reused_toolkit_invalid_credential_400(msg) -> bool:
    """Filter the reused team-project GitLab toolkit's OWN pre-existing
    credential-validation 400 (``EliteaUI/src/api/toolkits.js``'s
    ``validateToolkit`` RTK-Query call -> ``GET
    .../toolkit_validator/prompt_lib/{project}/{toolkit_id}``), fired on
    every load of this toolkit's detail page regardless of any action this
    case's automation takes.

    Root cause (AFS Classification note #2): every credential currently
    seeded in project 471 — including the one already linked to the reused
    GitLab toolkit BEFORE this test ever opens it — is a placeholder/invalid
    token. This is the SAME backend validation path, and the SAME intended
    product behavior, already confirmed correct by
    ``test_toolkit_credential_indicators_e2e``
    (``test_toolkit_indicators_for_credentials.py`` — deliberately-invalid
    credential -> "Authentication failed:"/"Access forbidden:"/"Connection
    error:" surfaced via the credential-status-indicator feature,
    Enhancement #5114) — not a defect, and not something this case's own
    Steps 1-16 cause or could avoid short of mutating the shared toolkit's
    credential (forbidden by Classification note #2).
    """
    location_url = (msg.location or {}).get("url", "")
    return "400" in msg.text and "elitea_core/toolkit_validator/prompt_lib/" in location_url


class TestCreatePrivateCredentialFromToolkitDropdown:
    """ELITEA-1976 — Create a private credential from a toolkit's Configuration dropdown."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "toolkits-credentials/ELITEA-1976_credential-create-private-credential-from-toolkit-flow.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/999", "Known defect #999")
    @pytest.mark.p2
    def test_create_private_credential_from_toolkit_configuration_dropdown(self, page, _browser_cookies):
        """Create a private credential from a GitLab toolkit's Configuration
        dropdown; verify it's created under the personal project, appears
        only after Refresh, links via the displayed value, and is
        structurally invisible to the team project (private scope).
        """
        team_toolkit_api = ToolkitAPI(browser_cookies=_browser_cookies, project_id=TEAM_PROJECT_ID)
        team_credential_api = CredentialAPI(browser_cookies=_browser_cookies, project_id=TEAM_PROJECT_ID)
        personal_credential_api = CredentialAPI(browser_cookies=_browser_cookies)  # default = personal project

        display_name = "autotest_private_cred"
        credential_id = None
        toolkit_id = None
        toolkit_before = None
        new_page = None

        console_messages = []
        page_errors: list[str] = []

        def _on_console(msg):
            if (
                msg.type == "error"
                and not _is_known_project_471_secrets_403(msg)
                and not _is_known_554_warning(msg)
                and not _is_known_reused_toolkit_invalid_credential_400(msg)
            ):
                console_messages.append(msg)

        def _on_pageerror(exc):
            page_errors.append(str(exc))

        page.on("console", _on_console)
        page.on("pageerror", _on_pageerror)

        try:
            with allure.step(
                "Setup — clean up any stale 'autotest_private_cred' left by a "
                "previously-interrupted run (personal project)"
            ):
                for stale in personal_credential_api.list_all_credentials():
                    if stale.get("elitea_title") == display_name:
                        personal_credential_api.delete_credential(stale["id"])
                        logger.info("Deleted stale credential id=%s", stale["id"])

            with allure.step(
                "Step 1 [Precondition] — Look up an existing GitLab-type toolkit "
                "in the team project (471)"
            ):
                gitlab_toolkits = [
                    t for t in team_toolkit_api.list_all_toolkits() if t.get("type") == "gitlab"
                ]
                assert gitlab_toolkits, (
                    "Expected at least one GitLab-type toolkit in project 471 "
                    "(precondition for this case)"
                )
                toolkit_id = gitlab_toolkits[0]["id"]
                toolkit_before = team_toolkit_api.get_toolkit(toolkit_id)
                logger.info("Using GitLab toolkit id=%s for this case", toolkit_id)

            toolkits_list = ToolkitsListPage(page)
            toolkit_page = ToolkitDetailPage(page)

            with allure.step("Step 2 — Switch active project to the Team project (471); navigate to /toolkits/all"):
                toolkits_list.navigate(project_id=TEAM_PROJECT_ID)
                assert toolkits_list.count_visible_cards() > 0, (
                    "Expected at least one toolkit card visible in project 471"
                )

            with allure.step("Step 3 — Open the GitLab toolkit"):
                toolkit_page.navigate_to_toolkit(toolkit_id)
                assert toolkit_page.toolkit_title.is_visible(), "Toolkit detail title should be visible"
                assert toolkit_page.configuration_select(FIELD_KEY).is_visible(), (
                    "Gitlab Configuration select should be visible on the toolkit detail page"
                )
                display_text_before = toolkit_page.get_configuration_display_text(FIELD_KEY)

            with allure.step('Step 4 — Click the Gitlab Configuration select; verify CREATE + Saved headers'):
                toolkit_page.open_configuration_dropdown(FIELD_KEY)
                headers = toolkit_page.configuration_group_headers(FIELD_KEY)
                assert headers.count() == 2, (
                    f"Expected exactly 2 group headers (CREATE + Saved), got {headers.count()}"
                )
                assert headers.nth(0).text_content().strip().lower() == "create", (
                    f"First group header should be 'Create', got: {headers.nth(0).text_content()!r}"
                )
                assert "saved" in headers.nth(1).text_content().strip().lower(), (
                    f"Second group header should be the 'Saved ... Credentials' "
                    f"header, got: {headers.nth(1).text_content()!r}"
                )

            with allure.step("Step 5 — Verify the CREATE section's two options with their labels"):
                private_option = toolkit_page.configuration_create_private_option(FIELD_KEY)
                project_option = toolkit_page.configuration_create_project_option(FIELD_KEY)
                assert private_option.is_visible(), "'New private gitlab credentials' option should be visible"
                assert project_option.is_visible(), "'New project gitlab credentials' option should be visible"
                assert private_option.text_content().strip() == "New private gitlab credentials", (
                    f"Unexpected private-option label: {private_option.text_content()!r}"
                )
                assert project_option.text_content().strip() == "New project gitlab credentials", (
                    f"Unexpected project-option label: {project_option.text_content()!r}"
                )

            with allure.step('Step 6 — Click "New private gitlab credentials"'):
                new_page = toolkit_page.click_create_private_credential(FIELD_KEY, timeout=NAVIGATION_TIMEOUT)
                new_page.on(
                    "console",
                    lambda msg: (
                        console_messages.append(msg)
                        if msg.type == "error"
                        and not _is_known_project_471_secrets_403(msg)
                        and not _is_known_554_warning(msg)
                        and not _is_known_reused_toolkit_invalid_credential_400(msg)
                        else None
                    ),
                )
                new_page.on("pageerror", lambda exc: page_errors.append(str(exc)))

                expected_personal_prefix = f"/{settings.elitea_project_id}/credentials/create-credential/gitlab"
                assert expected_personal_prefix in new_page.url, (
                    f"New tab should open the create form under the PERSONAL project "
                    f"({settings.elitea_project_id}), got: {new_page.url}"
                )
                assert "section=credentials" in new_page.url, f"Expected section=credentials, got: {new_page.url}"

                create_page = CredentialCreatePage(new_page)
                create_page.wait_for_page_load()

            with allure.step(f"Step 7 — Fill Display Name: {display_name!r}"):
                create_page.set_display_name(display_name)
                assert create_page.display_name_input.input_value() == display_name, (
                    f"Display Name field should show {display_name!r} after filling"
                )
                assert create_page.id_input.input_value() == display_name, (
                    "ID field should live-mirror the Display Name (ELITEA-1972 pattern), "
                    f"got {create_page.id_input.input_value()!r}"
                )

            with allure.step("Step 8 — Fill Url + Private Token"):
                create_page.set_url(GITLAB_URL)
                assert create_page.url_input.input_value() == GITLAB_URL, (
                    f"Url field should show {GITLAB_URL!r} after filling"
                )
                create_page.set_private_token(PLACEHOLDER_TOKEN)
                assert create_page.private_token_input.get_attribute("type") == "password", (
                    "Private Token field should be masked (type=password)"
                )
                assert len(create_page.private_token_input.input_value()) == len(PLACEHOLDER_TOKEN), (
                    "Private Token field should contain the full placeholder value"
                )
                assert create_page.is_save_enabled(), "Save should be enabled once required fields are filled"

            with allure.step("Step 9 — Click Save"):
                with new_page.expect_response(
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
                assert create_body.get("label") == display_name
                assert create_body.get("elitea_title") == display_name
                assert create_body.get("type") == "gitlab"
                assert create_body.get("shared") is False, "New credential should be shared: false (private)"
                assert create_body.get("project_id") == settings.elitea_project_id, (
                    f"New credential should be created under the personal project "
                    f"({settings.elitea_project_id}), got project_id="
                    f"{create_body.get('project_id')!r}"
                )
                new_page.wait_for_url(
                    re.compile(r".*/credentials/all/?(\?.*)?$"), timeout=SAVE_RESPONSE_TIMEOUT
                )

            with allure.step("Step 10 — Close the new tab; return to the original toolkit tab"):
                new_page.close()
                new_page = None
                page.bring_to_front()
                display_text_after_close = toolkit_page.get_configuration_display_text(FIELD_KEY)
                assert display_text_after_close == display_text_before, (
                    "Original toolkit tab's Configuration display value should be "
                    f"unaffected by the credential-create tab: before="
                    f"{display_text_before!r} after={display_text_after_close!r}"
                )

            with allure.step(
                "Step 11 [CORRECTED — AFS Classification note #3, "
                "EliteaAI/elitea-testing-public#1047] — Verify the dropdown is STILL "
                "open from step 4/6 (the Select never closes after a CREATE-action "
                "click); the pre-refresh Saved list is stale"
            ):
                headers_still_open = toolkit_page.configuration_group_headers(FIELD_KEY)
                assert headers_still_open.count() == 2, (
                    "Configuration dropdown should still be open/rendered (CREATE + "
                    f"Saved group headers), got {headers_still_open.count()}"
                )
                assert headers_still_open.first.is_visible(), (
                    "First group header should be visible — the menu is still open, "
                    "not merely present in the DOM"
                )

                pre_refresh_option = toolkit_page.saved_credential_option(display_name, private=True)
                assert pre_refresh_option.count() == 0, (
                    "New credential should NOT appear before an explicit Refresh"
                )

            with allure.step("Step 12 — Click the Refresh button; verify a refetch GET fires"):
                with page.expect_response(
                    lambda r: (
                        r.request.method == "GET"
                        and f"/configurations/configurations/{TEAM_PROJECT_ID}" in r.url
                    ),
                    timeout=UI_ELEMENT_TIMEOUT,
                ) as refresh_response_info:
                    toolkit_page.click_configuration_refresh(FIELD_KEY)
                assert refresh_response_info.value.status == 200, (
                    "Configurations refetch GET should succeed"
                )

            with allure.step(f"Step 13 — Verify {display_name!r} now appears in the Saved list"):
                saved_option = toolkit_page.saved_credential_option(display_name, private=True)
                saved_option.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert saved_option.is_visible(), (
                    f"{display_name!r} should be visible in the Saved credentials list after Refresh"
                )

            with allure.step(f"Step 14 — Select {display_name!r}; verify the Configuration display value updates"):
                toolkit_page.select_saved_credential(display_name, private=True)
                displayed = toolkit_page.get_configuration_display_text(FIELD_KEY)
                assert display_name in displayed, (
                    f"Configuration field's displayed value should update to include "
                    f"{display_name!r}, got: {displayed!r}"
                )

            with allure.step("Step 15 — Verify private-scope isolation via the API"):
                team_matches = [
                    c for c in team_credential_api.list_all_credentials()
                    if c.get("elitea_title") == display_name
                ]
                assert len(team_matches) == 0, (
                    f"{display_name!r} should NOT appear in the team project's (471) "
                    f"own credential list, got {len(team_matches)} match(es)"
                )

                personal_matches = [
                    c for c in personal_credential_api.list_all_credentials()
                    if c.get("elitea_title") == display_name
                ]
                assert len(personal_matches) == 1, (
                    f"{display_name!r} should appear exactly once in the personal "
                    f"project's credential list, got {len(personal_matches)} match(es)"
                )
                assert personal_matches[0].get("shared") is False
                assert personal_matches[0].get("project_id") == settings.elitea_project_id, (
                    "Personal-project credential's project_id should be the personal "
                    f"project ({settings.elitea_project_id}), got "
                    f"{personal_matches[0].get('project_id')!r}"
                )

            with allure.step(
                "Step 16 [Cleanup verification, AFS Axis 2] — Verify the shared, "
                "other-owned toolkit's own settings are unaffected (Save was never "
                "clicked on it — AFS Classification note #2)"
            ):
                toolkit_after = team_toolkit_api.get_toolkit(toolkit_id)
                assert toolkit_after.get("settings") == toolkit_before.get("settings"), (
                    "The shared, other-owned toolkit's own settings should be "
                    "unchanged by this test run (Save was never clicked on it)"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors or "
                "uncaught exceptions across the full flow"
            ):
                assert not console_messages and not page_errors, (
                    f"Unexpected side-channel errors: "
                    f"console={[m.text for m in console_messages]!r} page_errors={page_errors!r}"
                )

        finally:
            # Cleanup only — no assertions here (a failed cleanup step must
            # never mask a real assertion failure from the try block above).
            if new_page is not None:
                try:
                    new_page.close()
                except Exception:
                    pass

            # Navigate away WITHOUT clicking the toolkit's own Save button —
            # discards the unsaved Configuration selection client-side (never
            # Save a shared, other-owned toolkit — AFS Classification note #2).
            try:
                ToolkitsListPage(page).navigate(project_id=TEAM_PROJECT_ID)
            except Exception as exc:
                logger.warning("Failed to navigate away from the toolkit form: %s", exc)

            if credential_id is not None:
                try:
                    personal_credential_api.delete_credential(int(credential_id))
                    logger.info("Deleted credential id=%s", credential_id)
                except Exception as exc:
                    logger.warning("Failed to delete credential %s: %s", credential_id, exc)

            # Close the manually-constructed, project-scoped API sessions —
            # they're built ad hoc here (not via the shared `credential_api`/
            # `toolkit_api` fixtures) precisely because this case needs THREE
            # distinct project scopings, so no fixture teardown closes them.
            for api_client in (team_toolkit_api, team_credential_api, personal_credential_api):
                try:
                    api_client.close()
                except Exception as exc:
                    logger.warning("Failed to close API client %s: %s", api_client, exc)
