"""Tests for credential indicators on Toolkit, Pipeline, and Agent pages.

Verifies enhancement #5114 and bugs #5183 and #4906.
1. Status indicator appears for invalid credentials with "Authentication failed:" tooltip
2. Warning message "Authentication failed: ..." is displayed
3. Reload button with tooltip "Reload and apply changes"
4. Open in new tab button with tooltip "Open in new tab" (always visible)
5. After fixing credentials and clicking Reload:
   - Status indicator, warning message, and Reload button disappear
   - Open in new tab remains visible

Bug reference: https://github.com/EliteaAI/elitea_issues/issues/4906
Enhancement: https://github.com/EliteaAI/elitea_issues/issues/5114
Bug (Agent/Pipeline): https://github.com/EliteaAI/elitea_issues/issues/5183

Test cases: TC-1778, TC-1782, TC-1784, TC-1785

Usage:
    pytest test_toolkit_indicators_for_credentials.py -v
    pytest test_toolkit_indicators_for_credentials.py -v -k "toolkit"
    pytest test_toolkit_indicators_for_credentials.py -v -k "pipeline"
    pytest test_toolkit_indicators_for_credentials.py -v -k "agent"
"""

import logging
import time

import pytest

from config import settings
from pages.toolkit_detail_page import ToolkitDetailPage
import allure

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits]

TOOL_NAME = "list_projects"


class TestToolkitCredentialIndicators:
    """Tests for credential indicators on Toolkit detail page.
    TC-1778, TC-1784, TC-1785
    """

    @pytest.mark.tms("ELITEA-1180", "ELITEA-1181", "ELITEA-1183")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/toolkits_UI/ELITEA-1180_open-in-new-tab-icon-is-present-for-all-credentials-regardless-of-stat.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/toolkits_UI/ELITEA-1181_verify-reload-applies-fixes-of-credentials-immediately.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/toolkits_UI/ELITEA-1183_toolkit-displays-authentication-warning-and-disables-save-for-invalid.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_toolkit_credential_indicators_e2e(
        self,
        page,
        credential_api,
        toolkit_api,
    ):
        """E2E test: verify all indicators and fix invalid credentials on Toolkit.

        Adjusted 2026-09-18 for EliteaUI EL-6632 (EliteaAI/EliteaUI@f73c22f7, PR #1036,
        Refs #2349): the attention icon (``credential-status-indicator``) no longer
        renders on the SELECTED credential value — the row is flagged via the
        combobox's ``aria-invalid`` + warning underline, and the icon-with-tooltip
        now renders only on the credential's own DROPDOWN OPTION. Steps 4 and 13
        therefore open the dropdown (transit) and assert the icon/tooltip there,
        scoped to this test's credential; what is verified is unchanged.
        """
        if not settings.jira_api_key or not settings.jira_username:
            pytest.skip("JIRA_USERNAME and JIRA_API_KEY not set in .env.test - required for e2e test")

        ts = str(int(time.time()))
        cred_name = f"autotest_tk_cred_{ts}"[:32]
        toolkit_name = f"autotest_toolkit_{ts}"[:32]
        credential_id = None
        toolkit_id = None
        new_tab = None

        try:
            with allure.step("Step 1 — Create Jira credential with invalid token"):
                invalid_payload = {
                    "type": "jira",
                    "elitea_title": f"tk_jira_{ts}",
                    "label": cred_name,
                    "data": {
                        "base_url": settings.jira_base_url,
                        "username": settings.jira_username,
                        "api_key": "invalid_expired_token_12345",
                    },
                    "shared": False,
                }
                cred = credential_api.create_credential(invalid_payload)
                credential_id = cred["id"]
                logger.info("Created invalid Jira credential: %s", credential_id)

            with allure.step("Step 2 — Create toolkit with invalid credential"):
                toolkit = toolkit_api.create_toolkit(
                    name=toolkit_name,
                    description="Toolkit for credential indicators test",
                    toolkit_type="jira",
                    settings={
                        "jira_configuration": {
                            "elitea_title": cred["elitea_title"],
                            "private": True,
                        },
                        "cloud": True,
                        "limit": 5,
                        "api_version": "Auto",
                        "verify_ssl": True,
                    },
                )
                toolkit_id = toolkit["id"]
                logger.info("Created Jira toolkit: %s", toolkit_id)

            with allure.step("Step 3 — Navigate to toolkit detail page"):
                toolkit_page = ToolkitDetailPage(page)
                toolkit_page.navigate_to_toolkit(toolkit_id)

            with allure.step("Step 4 — Verify status indicator with error tooltip"):
                # EL-6632: the credential row itself is flagged invalid (aria-invalid +
                # warning underline) and the attention icon lives on the dropdown option.
                toolkit_page.wait_for_credential_select_invalid_state("jira", invalid=True, timeout=15000)
                toolkit_page.open_credential_dropdown("jira")
                assert toolkit_page.has_saved_option_status_indicator(
                    cred["elitea_title"], private=True, timeout=15000
                ), "Expected status indicator for invalid credential"
                status_tooltip = toolkit_page.get_saved_option_status_indicator_tooltip(
                    cred["elitea_title"], private=True
                )
                assert status_tooltip and any(
                    err in status_tooltip for err in ("Authentication failed:", "Access forbidden:", "Connection error:")
                ), f"Status tooltip should contain error message, got: '{status_tooltip}'"
                toolkit_page.close_credential_dropdown("jira")
                logger.info("Status indicator verified: %s", status_tooltip)

            with allure.step("Step 5 — Verify warning message"):
                warning = toolkit_page.get_authentication_warning(timeout=5000)
                assert warning and any(
                    err in warning for err in ("Authentication failed:", "Access forbidden:", "Connection error:")
                ), f"Warning message should contain error message, got: '{warning}'"
                logger.info("Warning message verified: %s", warning)

            with allure.step("Step 6 — Verify Reload button with tooltip"):
                assert toolkit_page.has_reload_button(timeout=5000), "Expected reload button"
                reload_tooltip = toolkit_page.get_reload_button_tooltip()
                assert reload_tooltip == "Reload and apply changes", (
                    f"Reload tooltip should be 'Reload and apply changes', got: '{reload_tooltip}'"
                )
                logger.info("Reload button verified")

            with allure.step("Step 7 — Verify Open in new tab button"):
                assert toolkit_page.has_open_in_new_tab_button(timeout=5000), (
                    "Expected open-in-new-tab button"
                )
                open_tooltip = toolkit_page.get_open_in_new_tab_button_tooltip()
                assert open_tooltip == "Open in new tab", (
                    f"Open tooltip should be 'Open in new tab', got: '{open_tooltip}'"
                )
                logger.info("Open in new tab button verified")

            with allure.step("Step 8 — Verify Save button is disabled"):
                assert toolkit_page.is_save_button_disabled(), (
                    "Save button should be disabled when credentials are invalid"
                )
                logger.info("Save button is disabled (as expected with invalid credentials)")

            with allure.step("Step 9 — Click Open in new tab and verify"):
                toolkit_page.hover_credential_row()
                open_btn = page.locator('button[aria-label="Open in new tab"]')
                with page.context.expect_page() as new_page_info:
                    open_btn.click()
                new_tab = new_page_info.value
                new_tab.wait_for_load_state("domcontentloaded")
                assert "/credentials/" in new_tab.url or "/configurations/" in new_tab.url, (
                    f"New tab should open credential page, got: {new_tab.url}"
                )
                logger.info("Open in new tab works - opened: %s", new_tab.url)

            with allure.step("Step 10 — Fix credential via API"):
                valid_payload = {
                    "type": "jira",
                    "elitea_title": cred["elitea_title"],
                    "label": cred_name,
                    "data": {
                        "base_url": settings.jira_base_url,
                        "username": settings.jira_username,
                        "api_key": settings.jira_api_key,
                    },
                    "shared": False,
                }
                credential_api.update_credential(credential_id, valid_payload)
                logger.info("Updated credential to valid Jira credentials")
                page.wait_for_timeout(2000)

            with allure.step("Step 11 — Close new tab and return to original"):
                new_tab.close()
                new_tab = None
                page.bring_to_front()
                logger.info("Closed new tab and returned to original page")

            with allure.step("Step 12 — Click Reload button"):
                page.wait_for_timeout(1000)
                toolkit_page.click_credential_reload()
                logger.info("Clicked reload button")

            with allure.step("Step 13 — Verify indicators disappear after fix"):
                # Row-level invalid state clears first (toolkit re-validation), then the
                # option-scoped icon must be gone — asserted where Step 4 read it.
                toolkit_page.wait_for_credential_select_invalid_state("jira", invalid=False, timeout=15000)
                toolkit_page.open_credential_dropdown("jira")
                toolkit_page.wait_for_no_saved_option_status_indicator(
                    cred["elitea_title"], private=True, timeout=15000
                )
                toolkit_page.close_credential_dropdown("jira")
                logger.info("Status indicator disappeared")

                assert not toolkit_page.has_authentication_warning(timeout=3000), (
                    "Warning message should disappear after fixing credentials"
                )
                logger.info("Warning message disappeared")

                assert not toolkit_page.has_reload_button(timeout=3000), (
                    "Reload button should disappear after fixing credentials"
                )
                logger.info("Reload button disappeared")

                assert toolkit_page.has_open_in_new_tab_button(timeout=5000), (
                    "Open in new tab should remain visible after fixing credentials"
                )
                logger.info("Open in new tab button still present - toolkit e2e test passed")

        finally:
            if new_tab:
                try:
                    new_tab.close()
                except Exception:
                    pass
            if toolkit_id:
                try:
                    toolkit_api.delete_toolkit(toolkit_id)
                    logger.info("Cleaned up toolkit %s", toolkit_id)
                except Exception as exc:
                    logger.warning("Failed to delete toolkit: %s", exc)
            if credential_id:
                try:
                    credential_api.delete_credential(credential_id)
                    logger.info("Cleaned up credential %s", credential_id)
                except Exception as exc:
                    logger.warning("Failed to delete credential: %s", exc)


class TestPipelineCredentialIndicators:
    """Tests for credential indicators on Pipeline detail page.

    Bug #5183: Pipeline should display clear warning for invalid credentials.
    TC-1782
    """

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/toolkits_UI/ELITEA-1182_agent-and-pipeline-toolkits-panel-shows-all-three-credential-indicator.md", "onetest-ai Test Case link")
    @pytest.mark.tms("ELITEA-1182")
    @pytest.mark.p2
    def test_pipeline_credential_indicators_e2e(
        self,
        page,
        credential_api,
        toolkit_api,
        pipeline_api,
    ):
        """E2E test: verify all indicators and fix invalid credentials on Pipeline."""
        from pages.pipeline_detail_page import PipelineDetailPage
        from playwright.sync_api import expect

        if not settings.jira_api_key or not settings.jira_username:
            pytest.skip("JIRA_USERNAME and JIRA_API_KEY not set in .env.test - required for e2e test")

        ts = str(int(time.time()))
        cred_name = f"autotest_pipe_cred_{ts}"[:32]
        toolkit_name = f"autotest_pipe_tk_{ts}"[:32]
        pipeline_name = f"autotest_pipeline_{ts}"[:32]
        good_cred_name = f"autotest_pipe_ok_{ts}"[:32]
        good_toolkit_name = f"autotest_pipe_tkok_{ts}"[:32]
        good_pipeline_name = f"autotest_pipeline_b_{ts}"[:32]
        credential_id = None
        toolkit_id = None
        pipeline_id = None
        good_credential_id = None
        good_toolkit_id = None
        good_pipeline_id = None
        new_tab = None

        try:
            with allure.step("Step 1 — Create Jira credential with invalid token"):
                invalid_payload = {
                    "type": "jira",
                    "elitea_title": f"pipe_jira_{ts}",
                    "label": cred_name,
                    "data": {
                        "base_url": settings.jira_base_url,
                        "username": settings.jira_username,
                        "api_key": "invalid_expired_token_12345",
                    },
                    "shared": False,
                }
                cred = credential_api.create_credential(invalid_payload)
                credential_id = cred["id"]
                logger.info("Created invalid Jira credential: %s", credential_id)

            with allure.step("Step 2 — Create toolkit with invalid credential"):
                toolkit = toolkit_api.create_toolkit(
                    name=toolkit_name,
                    description="Toolkit for pipeline indicator test",
                    toolkit_type="jira",
                    settings={
                        "jira_configuration": {
                            "elitea_title": cred["elitea_title"],
                            "private": True,
                        },
                        "cloud": True,
                        "limit": 5,
                        "api_version": "Auto",
                        "verify_ssl": True,
                        "selected_tools": [TOOL_NAME],
                    },
                )
                toolkit_id = toolkit["id"]
                logger.info("Created Jira toolkit: %s", toolkit_id)

            with allure.step("Step 3 — Create valid Jira credential + toolkit and Pipelines A / B (no toolkit nodes yet)"):
                good_cred = credential_api.create_credential({
                    "type": "jira",
                    "elitea_title": f"pipe_jira_ok_{ts}",
                    "label": good_cred_name,
                    "data": {
                        "base_url": settings.jira_base_url,
                        "username": settings.jira_username,
                        "api_key": settings.jira_api_key,
                    },
                    "shared": False,
                })
                good_credential_id = good_cred["id"]
                good_toolkit = toolkit_api.create_toolkit(
                    name=good_toolkit_name,
                    description="Valid toolkit for pipeline indicator test",
                    toolkit_type="jira",
                    settings={
                        "jira_configuration": {"elitea_title": good_cred["elitea_title"], "private": True},
                        "cloud": True,
                        "limit": 5,
                        "api_version": "Auto",
                        "verify_ssl": True,
                        "selected_tools": [TOOL_NAME],
                    },
                )
                good_toolkit_id = good_toolkit["id"]
                pipeline = pipeline_api.create_pipeline(
                    name=pipeline_name,
                    description="Pipeline A for credential indicator test",
                )
                pipeline_id = pipeline["id"]
                good_pipeline = pipeline_api.create_pipeline(
                    name=good_pipeline_name,
                    description="Pipeline B for credential indicator test",
                )
                good_pipeline_id = good_pipeline["id"]
                logger.info("Created pipelines A=%s B=%s", pipeline_id, good_pipeline_id)

            pipeline_page = PipelineDetailPage(page)
            page.set_viewport_size({"width": 1600, "height": 1200})

            with allure.step("Step 12 — Open Pipeline A (Flow tab): TOOLS does not list the invalid toolkit yet"):
                pipeline_page.navigate(pipeline_id)
                pipeline_page.dismiss_banner_if_present()
                assert pipeline_page.is_flow_view_active(10000), "Pipeline canvas (Flow tab) should be displayed"
                assert pipeline_page.tool_card_named(toolkit_name).count() == 0, (
                    "TOOLS section must not list the toolkit before any node uses it"
                )

            with allure.step("Step 13-14 — Add a Toolkit node: select the invalid toolkit and a tool"):
                pipeline_page.add_toolkit_node_with_tool(toolkit_name, TOOL_NAME)

            with allure.step("Step 15-16 — Add an LLM node and add the same toolkit to its tools"):
                pipeline_page.add_llm_node_with_toolkit(toolkit_name)

            with allure.step("Step 17 — TOOLS lists the toolkit with 'Used by' chips for both nodes"):
                pipeline_page.expand_tools_section()
                assert pipeline_page.tool_card_named(toolkit_name).count() == 1
                assert pipeline_page.is_toolkit_card_used_by_node(toolkit_name, "Toolkit 1")
                assert pipeline_page.is_toolkit_card_used_by_node(toolkit_name, "LLM 1")
                # The credential validation runs against the SAVED version: persist, then reload.
                pipeline_page.save_and_reload()

            with allure.step("Step 18-19 — Open in new tab icon present with a meaningful tooltip"):
                pipeline_page.hover_tool_card(toolkit_name)
                open_btn = pipeline_page.tool_card_open_button(toolkit_name)
                assert open_btn.is_visible(), "Expected open-in-new-tab button on the toolkit card"
                open_tooltip = pipeline_page.hover_and_read_tooltip(open_btn)
                assert open_tooltip == "Open toolkit in new tab", (
                    f"Open tooltip should be 'Open toolkit in new tab', got: '{open_tooltip}'"
                )

            with allure.step("Step 20 — Warning message containing 'Authentication failed:'"):
                assert pipeline_page.has_toolkit_warning_message(timeout=15000), (
                    "Expected warning message for invalid credential in pipeline"
                )
                warning_msg = pipeline_page.get_toolkit_warning_message()
                assert warning_msg and "Authentication failed" in warning_msg, (
                    f"Warning message should contain 'Authentication failed', got: '{warning_msg}'"
                )
                logger.info("Warning message verified: %s", warning_msg)

            with allure.step("Step 21-22 — Header warning icon next to VERSION with a hover message"):
                assert pipeline_page.version_warning_icon.is_visible(), (
                    "Expected a warning icon in the pipeline header for a misconfigured pipeline"
                )
                header_tooltip = pipeline_page.hover_and_read_tooltip(pipeline_page.version_warning_icon, reset=True)
                assert header_tooltip.startswith("Toolkit(s) configuration issue"), (
                    f"Header warning tooltip should describe the toolkit configuration issue, got: '{header_tooltip}'"
                )

            with allure.step("Fix 1 — Click Open in new tab and verify"):
                new_tab = pipeline_page.click_tool_card_open_in_new_tab(toolkit_name)
                assert "/toolkits/" in new_tab.url or "/tools/" in new_tab.url, (
                    f"New tab should open toolkit page, got: {new_tab.url}"
                )
                logger.info("Open in new tab works - opened: %s", new_tab.url)

            with allure.step("Fix 2 — Fix credential via API"):
                valid_payload = {
                    "type": "jira",
                    "elitea_title": cred["elitea_title"],
                    "label": cred_name,
                    "data": {
                        "base_url": settings.jira_base_url,
                        "username": settings.jira_username,
                        "api_key": settings.jira_api_key,
                    },
                    "shared": False,
                }
                credential_api.update_credential(credential_id, valid_payload)
                logger.info("Updated credential to valid Jira credentials")

            with allure.step("Fix 3 — Close new tab and return to original"):
                new_tab.close()
                new_tab = None
                page.bring_to_front()
                logger.info("Closed new tab and returned to original page")

            with allure.step("Fix 4 — Reload to re-validate (no Reload icon on the pipeline TOOLS card on DEV)"):
                # Adjusted: the old flow clicked the card's Reload icon; DEV's pipeline card has none, so the
                # re-validation is triggered by a page reload (version validation runs on load).
                page.reload()
                pipeline_page.wait_for_detail_page_load()
                pipeline_page.ensure_toolkits_section_visible(timeout=15000)

            with allure.step("Fix 5 — Verify indicators disappear after fix"):
                pipeline_page.wait_for_no_toolkit_status_indicator(toolkit_name, timeout=15000)
                logger.info("Warning message disappeared")

                assert not pipeline_page.has_toolkit_reload_button(toolkit_name, timeout=3000), (
                    "Reload button should disappear after fixing credentials"
                )
                assert pipeline_page.tool_card_open_button(toolkit_name).is_visible(), (
                    "Open in new tab should remain visible after fixing credentials"
                )
                expect(pipeline_page.version_warning_icon).to_have_count(0, timeout=10000)
                logger.info("Pipeline A: indicators gone, Open in new tab remains")

            with allure.step("Step 23 — Open Pipeline B (Flow tab): TOOLS does not list the valid toolkit yet"):
                pipeline_page.navigate(good_pipeline_id)
                pipeline_page.dismiss_banner_if_present()
                assert pipeline_page.is_flow_view_active(10000), "Pipeline canvas (Flow tab) should be displayed"
                assert pipeline_page.tool_card_named(good_toolkit_name).count() == 0

            with allure.step("Step 24 — Add a Toolkit node with the valid toolkit and a tool"):
                pipeline_page.add_toolkit_node_with_tool(good_toolkit_name, TOOL_NAME)

            with allure.step("Step 25 — Add an LLM node with the valid toolkit attached"):
                pipeline_page.add_llm_node_with_toolkit(good_toolkit_name)

            with allure.step("Step 26 — TOOLS lists the valid toolkit with 'Used by' chips for both nodes"):
                pipeline_page.expand_tools_section()
                assert pipeline_page.tool_card_named(good_toolkit_name).count() == 1
                assert pipeline_page.is_toolkit_card_used_by_node(good_toolkit_name, "Toolkit 1")
                assert pipeline_page.is_toolkit_card_used_by_node(good_toolkit_name, "LLM 1")
                pipeline_page.save_and_reload()

            with allure.step("Step 27 — Open in new tab icon is visible for the valid credential"):
                pipeline_page.hover_tool_card(good_toolkit_name)
                assert pipeline_page.tool_card_open_button(good_toolkit_name).is_visible()

            with allure.step("Step 28 — No Reload icon for the valid credential"):
                assert pipeline_page.tool_card_reload_button.count() == 0, "Reload icon must be absent"

            with allure.step("Step 29 — No warning indicator and no warning message for the valid credential"):
                assert not pipeline_page.has_toolkit_warning_message(timeout=5000), (
                    "No warning message expected for a valid credential"
                )

            with allure.step("Step 30 — No warning icon in the pipeline header"):
                expect(pipeline_page.version_warning_icon).to_have_count(0, timeout=5000)

        finally:
            if new_tab:
                try:
                    new_tab.close()
                except Exception:
                    pass
            for pid in (pipeline_id, good_pipeline_id):
                if pid:
                    try:
                        pipeline_api.delete_pipeline(pid)
                        logger.info("Cleaned up pipeline %s", pid)
                    except Exception as exc:
                        logger.warning("Failed to delete pipeline: %s", exc)
            for tid in (toolkit_id, good_toolkit_id):
                if tid:
                    try:
                        toolkit_api.delete_toolkit(tid)
                        logger.info("Cleaned up toolkit %s", tid)
                    except Exception as exc:
                        logger.warning("Failed to delete toolkit: %s", exc)
            for cid in (credential_id, good_credential_id):
                if cid:
                    try:
                        credential_api.delete_credential(cid)
                        logger.info("Cleaned up credential %s", cid)
                    except Exception as exc:
                        logger.warning("Failed to delete credential: %s", exc)


class TestAgentCredentialIndicators:
    """Tests for credential indicators on Agent detail page.

    Bug #5183: Agent should display clear warning for invalid credentials.
    TC-1782
    """

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/toolkits_UI/ELITEA-1182_agent-and-pipeline-toolkits-panel-shows-all-three-credential-indicator.md", "onetest-ai Test Case link")
    @pytest.mark.tms("ELITEA-1182")
    @pytest.mark.p2
    def test_agent_credential_indicators_e2e(
        self,
        page,
        credential_api,
        toolkit_api,
        agent_api,
    ):
        """E2E test: verify all indicators and fix invalid credentials on Agent."""
        from pages.agent_detail_page import AgentDetailPage

        if not settings.jira_api_key or not settings.jira_username:
            pytest.skip("JIRA_USERNAME and JIRA_API_KEY not set in .env.test - required for e2e test")

        ts = str(int(time.time()))
        cred_name = f"autotest_agent_cred_{ts}"[:32]
        toolkit_name = f"autotest_agent_tk_{ts}"[:32]
        agent_name = f"autotest_agent_{ts}"[:32]
        credential_id = None
        toolkit_id = None
        agent_id = None
        new_tab = None

        try:
            with allure.step("Step 1 — Create Jira credential with invalid token"):
                invalid_payload = {
                    "type": "jira",
                    "elitea_title": f"agent_jira_{ts}",
                    "label": cred_name,
                    "data": {
                        "base_url": settings.jira_base_url,
                        "username": settings.jira_username,
                        "api_key": "invalid_expired_token_12345",
                    },
                    "shared": False,
                }
                cred = credential_api.create_credential(invalid_payload)
                credential_id = cred["id"]
                logger.info("Created invalid Jira credential: %s", credential_id)

            with allure.step("Step 2 — Create toolkit with invalid credential"):
                toolkit = toolkit_api.create_toolkit(
                    name=toolkit_name,
                    description="Toolkit for agent indicator test",
                    toolkit_type="jira",
                    settings={
                        "jira_configuration": {
                            "elitea_title": cred["elitea_title"],
                            "private": True,
                        },
                        "cloud": True,
                        "limit": 5,
                        "api_version": "Auto",
                        "verify_ssl": True,
                    },
                )
                toolkit_id = toolkit["id"]
                logger.info("Created Jira toolkit: %s", toolkit_id)

            with allure.step("Step 3 — Create agent"):
                agent = agent_api.create_agent(
                    name=agent_name,
                    description="Agent for credential indicator test",
                )
                agent_id = agent["id"]
                logger.info("Created agent: %s", agent_id)

            with allure.step("Step 4 — Navigate to agent and add toolkit"):
                agent_page = AgentDetailPage(page)
                agent_page.navigate(agent_id)
                agent_page.add_toolkit(toolkit_name)
                page.wait_for_timeout(2000)
                logger.info("Added toolkit to agent")

            with allure.step("Step 5 — Verify status indicator with error tooltip"):
                assert agent_page.has_toolkit_status_indicator(toolkit_name, timeout=15000), (
                    "Expected status indicator on toolkit in agent"
                )
                status_tooltip = agent_page.get_toolkit_status_indicator_tooltip(toolkit_name)
                assert status_tooltip and any(
                    err in status_tooltip for err in ("Authentication failed:", "Access forbidden:", "Connection error:")
                ), f"Status tooltip should contain error message, got: '{status_tooltip}'"
                logger.info("Status indicator verified: %s", status_tooltip)

            with allure.step("Step 6 — Verify warning message"):
                warning_msg = agent_page.get_toolkit_warning_message(toolkit_name)
                assert warning_msg and any(
                    err in warning_msg for err in ("Authentication failed:", "Access forbidden:", "Connection error:")
                ), f"Warning message should contain error message, got: '{warning_msg}'"
                logger.info("Warning message verified: %s", warning_msg)

            with allure.step("Step 7 — Verify Reload button"):
                assert agent_page.has_toolkit_reload_button(toolkit_name, timeout=5000), (
                    "Expected reload button on toolkit card"
                )
                reload_tooltip = agent_page.get_toolkit_reload_button_tooltip(toolkit_name)
                assert reload_tooltip == "refresh toolkit", (
                    f"Reload tooltip should be 'refresh toolkit', got: '{reload_tooltip}'"
                )
                logger.info("Reload button verified")

            with allure.step("Step 8 — Verify Open in new tab button"):
                assert agent_page.has_toolkit_open_in_new_tab_button(toolkit_name, timeout=5000), (
                    "Expected open-in-new-tab button on toolkit card"
                )
                open_tooltip = agent_page.get_toolkit_open_in_new_tab_button_tooltip(toolkit_name)
                assert open_tooltip == "open in new tab", (
                    f"Open tooltip should be 'open in new tab', got: '{open_tooltip}'"
                )
                logger.info("Open in new tab button verified")

            with allure.step("Step 9 — Click Open in new tab and verify"):
                new_tab_url = agent_page.click_toolkit_open_in_new_tab(toolkit_name)
                assert "/toolkits/" in new_tab_url or "/tools/" in new_tab_url, (
                    f"New tab should open toolkit page, got: {new_tab_url}"
                )
                logger.info("Open in new tab works - opened: %s", new_tab_url)

                all_pages = page.context.pages
                for p in all_pages:
                    if p.url != page.url:
                        new_tab = p
                        break

            with allure.step("Step 10 — Fix credential via API"):
                valid_payload = {
                    "type": "jira",
                    "elitea_title": cred["elitea_title"],
                    "label": cred_name,
                    "data": {
                        "base_url": settings.jira_base_url,
                        "username": settings.jira_username,
                        "api_key": settings.jira_api_key,
                    },
                    "shared": False,
                }
                credential_api.update_credential(credential_id, valid_payload)
                logger.info("Updated credential to valid Jira credentials")
                page.wait_for_timeout(2000)

            with allure.step("Step 11 — Close new tab and return to original"):
                if new_tab:
                    new_tab.close()
                    new_tab = None
                page.bring_to_front()
                logger.info("Closed new tab and returned to original page")

            with allure.step("Step 12 — Click Reload button"):
                agent_page.click_toolkit_reload_button(toolkit_name)
                logger.info("Clicked reload button")
                page.wait_for_timeout(3000)

            with allure.step("Step 13 — Verify indicators disappear after fix"):
                assert not agent_page.has_toolkit_status_indicator(toolkit_name, timeout=5000), (
                    "Status indicator should disappear after fixing credentials"
                )
                logger.info("Status indicator disappeared")

                assert not agent_page.has_toolkit_warning_message(toolkit_name, timeout=3000), (
                    "Warning message should disappear after fixing credentials"
                )
                logger.info("Warning message disappeared")

                assert not agent_page.has_toolkit_reload_button(toolkit_name, timeout=3000), (
                    "Reload button should disappear after fixing credentials"
                )
                logger.info("Reload button disappeared")

                assert agent_page.has_toolkit_open_in_new_tab_button(toolkit_name, timeout=5000), (
                    "Open in new tab should remain visible after fixing credentials"
                )
                logger.info("Open in new tab button still present")
                logger.info("Agent e2e test passed")

        finally:
            if new_tab:
                try:
                    new_tab.close()
                except Exception:
                    pass
            if agent_id:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleaned up agent %s", agent_id)
                except Exception as exc:
                    logger.warning("Failed to delete agent: %s", exc)
            if toolkit_id:
                try:
                    toolkit_api.delete_toolkit(toolkit_id)
                    logger.info("Cleaned up toolkit %s", toolkit_id)
                except Exception as exc:
                    logger.warning("Failed to delete toolkit: %s", exc)
            if credential_id:
                try:
                    credential_api.delete_credential(credential_id)
                    logger.info("Cleaned up credential %s", credential_id)
                except Exception as exc:
                    logger.warning("Failed to delete credential: %s", exc)
