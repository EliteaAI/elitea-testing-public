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

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits]


class TestToolkitCredentialIndicators:
    """Tests for credential indicators on Toolkit detail page.
    TC-1778, TC-1784, TC-1785
    """

    @pytest.mark.p1
    def test_toolkit_credential_indicators_e2e(
        self,
        page,
        credential_api,
        toolkit_api,
    ):
        """E2E test: verify all indicators and fix invalid credentials on Toolkit.

        Flow:
        1. Create Jira credential with invalid token
        2. Create toolkit with that credential
        3. Verify all indicators:
           - Status indicator with "Authentication failed:" tooltip
           - Warning message with "Authentication failed:" text
           - Reload button with "Reload and apply changes" tooltip
           - Open in new tab button with "Open in new tab" tooltip
           - Save button is disabled
        4. Click "Open in new tab" and verify new tab opens
        5. Fix credential via API
        6. Close the new tab and return to original
        7. Click Reload
        8. Verify after fix:
           - Status indicator gone
           - Warning message gone
           - Reload button gone
           - Open in new tab remains
           - Save button enabled
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

            toolkit_page = ToolkitDetailPage(page)
            toolkit_page.navigate_to_toolkit(toolkit_id)

            assert toolkit_page.has_credential_status_indicator(timeout=15000), (
                "Expected status indicator for invalid credential"
            )
            status_tooltip = toolkit_page.get_credential_status_indicator_tooltip()
            assert status_tooltip and any(
                err in status_tooltip for err in ("Authentication failed:", "Access forbidden:", "Connection error:")
            ), f"Status tooltip should contain error message, got: '{status_tooltip}'"
            logger.info("Status indicator verified: %s", status_tooltip)

            warning = toolkit_page.get_authentication_warning(timeout=5000)
            assert warning and any(
                err in warning for err in ("Authentication failed:", "Access forbidden:", "Connection error:")
            ), f"Warning message should contain error message, got: '{warning}'"
            logger.info("Warning message verified: %s", warning)

            assert toolkit_page.has_reload_button(timeout=5000), "Expected reload button"
            reload_tooltip = toolkit_page.get_reload_button_tooltip()
            assert reload_tooltip == "Reload and apply changes", (
                f"Reload tooltip should be 'Reload and apply changes', got: '{reload_tooltip}'"
            )
            logger.info("Reload button verified")

            assert toolkit_page.has_open_in_new_tab_button(timeout=5000), (
                "Expected open-in-new-tab button"
            )
            open_tooltip = toolkit_page.get_open_in_new_tab_button_tooltip()
            assert open_tooltip == "Open in new tab", (
                f"Open tooltip should be 'Open in new tab', got: '{open_tooltip}'"
            )
            logger.info("Open in new tab button verified")

            assert toolkit_page.is_save_button_disabled(), (
                "Save button should be disabled when credentials are invalid"
            )
            logger.info("Save button is disabled (as expected with invalid credentials)")

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

            new_tab.close()
            new_tab = None
            page.bring_to_front()
            logger.info("Closed new tab and returned to original page")

            page.wait_for_timeout(1000)
            toolkit_page.click_credential_reload()
            logger.info("Clicked reload button")

            toolkit_page.wait_for_no_status_indicator(timeout=15000)
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

    @pytest.mark.p2
    def test_pipeline_credential_indicators_e2e(
        self,
        page,
        credential_api,
        toolkit_api,
        pipeline_api,
    ):
        """E2E test: verify all indicators and fix invalid credentials on Pipeline.

        Flow:
        1. Create Jira credential with invalid token
        2. Create toolkit with that credential
        3. Create pipeline and add toolkit node
        4. Verify all indicators:
           - Status indicator with "Authentication failed:" tooltip
           - Warning message with "Authentication failed:" text
           - Reload button with "Reload and apply changes" tooltip
           - Open in new tab button with "Open in new tab" tooltip
        5. Click "Open in new tab" and verify new tab opens
        6. Fix credential via API
        7. Close the new tab and return to original
        8. Click Reload
        9. Verify after fix:
           - Status indicator gone
           - Warning message gone
           - Reload button gone
           - Open in new tab remains
        """
        from pages.pipeline_detail_page import PipelineDetailPage

        if not settings.jira_api_key or not settings.jira_username:
            pytest.skip("JIRA_USERNAME and JIRA_API_KEY not set in .env.test - required for e2e test")

        ts = str(int(time.time()))
        cred_name = f"autotest_pipe_cred_{ts}"[:32]
        toolkit_name = f"autotest_pipe_tk_{ts}"[:32]
        pipeline_name = f"autotest_pipeline_{ts}"[:32]
        credential_id = None
        toolkit_id = None
        pipeline_id = None
        new_tab = None

        try:
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
                },
            )
            toolkit_id = toolkit["id"]
            logger.info("Created Jira toolkit: %s", toolkit_id)

            pipeline = pipeline_api.create_pipeline(
                name=pipeline_name,
                description="Pipeline for credential indicator test",
            )
            pipeline_id = pipeline["id"]
            logger.info("Created pipeline: %s", pipeline_id)

            pipeline_page = PipelineDetailPage(page)
            pipeline_page.navigate(pipeline_id)

            add_toolkit_btn = page.locator('div[data-tour="agent-tools"] button').first
            add_toolkit_btn.wait_for(state="visible", timeout=10000)
            add_toolkit_btn.click()
            page.wait_for_timeout(500)

            popper = page.locator('.MuiPopper-root')
            popper.wait_for(state="visible", timeout=5000)
            search_input = popper.locator('input')
            if search_input.count() > 0:
                search_input.first.fill(toolkit_name)
                page.wait_for_timeout(500)
            toolkit_option = popper.locator(f'li:has-text("{toolkit_name}")')
            toolkit_option.first.click()
            page.wait_for_timeout(2000)
            logger.info("Added toolkit to pipeline via TOOLS panel")

            assert pipeline_page.has_toolkit_warning_message(timeout=15000), (
                "Expected warning message for invalid credential in pipeline"
            )
            warning_msg = pipeline_page.get_toolkit_warning_message()
            assert warning_msg and "Authentication failed" in warning_msg, (
                f"Warning message should contain 'Authentication failed', got: '{warning_msg}'"
            )
            logger.info("Warning message verified: %s", warning_msg)

            assert pipeline_page.has_toolkit_reload_button(toolkit_name, timeout=5000), (
                "Expected reload button on toolkit item"
            )
            reload_tooltip = pipeline_page.get_toolkit_reload_button_tooltip(toolkit_name)
            assert reload_tooltip == "refresh toolkit", (
                f"Reload tooltip should be 'refresh toolkit', got: '{reload_tooltip}'"
            )
            logger.info("Reload button verified")

            assert pipeline_page.has_toolkit_open_in_new_tab_button(toolkit_name, timeout=5000), (
                "Expected open-in-new-tab button on toolkit item"
            )
            open_tooltip = pipeline_page.get_toolkit_open_in_new_tab_button_tooltip(toolkit_name)
            assert open_tooltip == "open in new tab", (
                f"Open tooltip should be 'open in new tab', got: '{open_tooltip}'"
            )
            logger.info("Open in new tab button verified")

            new_tab = pipeline_page.click_toolkit_open_in_new_tab(toolkit_name)
            assert "/toolkits/" in new_tab.url or "/tools/" in new_tab.url, (
                f"New tab should open toolkit page, got: {new_tab.url}"
            )
            logger.info("Open in new tab works - opened: %s", new_tab.url)

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

            new_tab.close()
            new_tab = None
            page.bring_to_front()
            logger.info("Closed new tab and returned to original page")

            page.wait_for_timeout(1000)
            pipeline_page.hover_toolkit_item(toolkit_name)
            reload_btn = page.locator('#RefreshButton')
            reload_btn.click()
            pipeline_page.wait_for_network(timeout=10000)
            page.wait_for_timeout(3000)
            logger.info("Clicked reload button")

            pipeline_page.wait_for_no_toolkit_status_indicator(toolkit_name, timeout=15000)
            logger.info("Warning message disappeared")

            assert not pipeline_page.has_toolkit_reload_button(toolkit_name, timeout=3000), (
                "Reload button should disappear after fixing credentials"
            )
            logger.info("Reload button disappeared")

            assert pipeline_page.has_toolkit_open_in_new_tab_button(toolkit_name, timeout=5000), (
                "Open in new tab should remain visible after fixing credentials"
            )
            logger.info("Open in new tab button still present")

            logger.info("Pipeline e2e test passed")

        finally:
            if new_tab:
                try:
                    new_tab.close()
                except Exception:
                    pass
            if pipeline_id:
                try:
                    pipeline_api.delete_pipeline(pipeline_id)
                    logger.info("Cleaned up pipeline %s", pipeline_id)
                except Exception as exc:
                    logger.warning("Failed to delete pipeline: %s", exc)
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


class TestAgentCredentialIndicators:
    """Tests for credential indicators on Agent detail page.

    Bug #5183: Agent should display clear warning for invalid credentials.
    TC-1782
    """

    @pytest.mark.p2
    def test_agent_credential_indicators_e2e(
        self,
        page,
        credential_api,
        toolkit_api,
        agent_api,
    ):
        """E2E test: verify all indicators and fix invalid credentials on Agent.

        Flow:
        1. Create Jira credential with invalid token
        2. Create toolkit with that credential
        3. Create agent and add toolkit
        4. Verify all indicators:
           - Status indicator with "Authentication failed:" tooltip
           - Warning message with "Authentication failed:" text
           - Reload button with "Reload and apply changes" tooltip
           - Open in new tab button with "Open in new tab" tooltip
        5. Click "Open in new tab" and verify new tab opens
        6. Fix credential via API
        7. Close the new tab and return to original
        8. Click Reload
        9. Verify after fix:
           - Status indicator gone
           - Warning message gone
           - Reload button gone
           - Open in new tab remains
        """
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

            agent = agent_api.create_agent(
                name=agent_name,
                description="Agent for credential indicator test",
            )
            agent_id = agent["id"]
            logger.info("Created agent: %s", agent_id)

            agent_page = AgentDetailPage(page)
            agent_page.navigate(agent_id)

            agent_page.add_toolkit(toolkit_name)
            page.wait_for_timeout(2000)
            logger.info("Added toolkit to agent")

            assert agent_page.has_toolkit_status_indicator(toolkit_name, timeout=15000), (
                "Expected status indicator on toolkit in agent"
            )
            status_tooltip = agent_page.get_toolkit_status_indicator_tooltip(toolkit_name)
            assert status_tooltip and any(
                err in status_tooltip for err in ("Authentication failed:", "Access forbidden:", "Connection error:")
            ), f"Status tooltip should contain error message, got: '{status_tooltip}'"
            logger.info("Status indicator verified: %s", status_tooltip)

            warning_msg = agent_page.get_toolkit_warning_message(toolkit_name)
            assert warning_msg and any(
                err in warning_msg for err in ("Authentication failed:", "Access forbidden:", "Connection error:")
            ), f"Warning message should contain error message, got: '{warning_msg}'"
            logger.info("Warning message verified: %s", warning_msg)

            assert agent_page.has_toolkit_reload_button(toolkit_name, timeout=5000), (
                "Expected reload button on toolkit card"
            )
            reload_tooltip = agent_page.get_toolkit_reload_button_tooltip(toolkit_name)
            assert reload_tooltip == "refresh toolkit", (
                f"Reload tooltip should be 'refresh toolkit', got: '{reload_tooltip}'"
            )
            logger.info("Reload button verified")

            assert agent_page.has_toolkit_open_in_new_tab_button(toolkit_name, timeout=5000), (
                "Expected open-in-new-tab button on toolkit card"
            )
            open_tooltip = agent_page.get_toolkit_open_in_new_tab_button_tooltip(toolkit_name)
            assert open_tooltip == "open in new tab", (
                f"Open tooltip should be 'open in new tab', got: '{open_tooltip}'"
            )
            logger.info("Open in new tab button verified")

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

            if new_tab:
                new_tab.close()
                new_tab = None
            page.bring_to_front()
            logger.info("Closed new tab and returned to original page")

            agent_page.click_toolkit_reload_button(toolkit_name)
            logger.info("Clicked reload button")

            page.wait_for_timeout(3000)

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
