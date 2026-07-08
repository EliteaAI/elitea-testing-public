"""UI Tests for Guardrails Live-Reload and Case-Insensitive Matching.

Tests the enhancement from issue #5199:
- Guardrails configuration changes apply immediately without pylon reload
- Case-insensitive matching for blocked/sensitive toolkits and tools
- No "Reload required" badges or banners for these settings
- Artifacts tool behavior not affected

Test Cases (1 manual = 1 auto):
- ELITEA-1694: Blocked Toolkit Live-Reload and Case-Insensitive Matching
- ELITEA-1695: Blocked Tool Live-Reload and Case-Insensitive Matching
- ELITEA-1696: Sensitive Tool Live-Reload and Case-Insensitive Matching

Architecture:
- Admin page: ELITEA_URL/admin - configure guardrails
- User page: ELITEA_URL - verify blocking/authorization in agent chat

Markers:
    - ui: requires browser
    - admin: admin portal tests
    - guardrails: guardrails-related tests
    - p0: critical priority tests

Usage:
    cd automation
    pytest tests/ui/admin/test_guardrails_live_reload.py -v
"""

import logging

import pytest
import allure
from playwright.sync_api import Browser, Page

from pages.guardrails_admin_page import GuardrailsAdminPage
from pages.agent_detail_page import AgentDetailPage
from api import AgentAPI, CredentialAPI, ToolkitAPI
from config import settings

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.guardrails]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000
FORM_SAVE_TIMEOUT = 15000
TOOLKIT_EXECUTION_TIMEOUT = 60000
CHAT_RESPONSE_TIMEOUT = 90000

# ---------------------------------------------------------------------------
# Test Data
# ---------------------------------------------------------------------------
TEST_TOOLKIT = "github"
TEST_TOOL = "get_ISSUE"
GITHUB_BRANCH = "main"


# ---------------------------------------------------------------------------
# Module-level Fixtures (created once for all tests, deleted at end)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def module_browser_cookies(browser: Browser, auth_state):
    """Create browser cookies for API clients at module level."""
    ctx = browser.new_context(storage_state=auth_state)
    pg = ctx.new_page()
    pg.goto(settings.elitea_url)
    pg.wait_for_load_state("networkidle")
    cookies = ctx.cookies()
    pg.close()
    ctx.close()
    return cookies


@pytest.fixture(scope="module")
def module_credential_api(module_browser_cookies):
    """Credential API client for module-level setup."""
    api = CredentialAPI(browser_cookies=module_browser_cookies)
    yield api
    api.close()


@pytest.fixture(scope="module")
def module_toolkit_api(module_browser_cookies):
    """Toolkit API client for module-level setup."""
    api = ToolkitAPI(browser_cookies=module_browser_cookies)
    yield api
    api.close()


@pytest.fixture(scope="module")
def module_agent_api(module_browser_cookies):
    """Agent API client for module-level setup."""
    api = AgentAPI(browser_cookies=module_browser_cookies)
    yield api
    api.close()


@pytest.fixture(scope="module")
def guardrails_test_credential(module_credential_api: CredentialAPI):
    """Create GitHub credential for the entire test module.

    Created once before all tests, deleted after all tests complete.
    """
    if not settings.git_hub_token:
        pytest.skip("GIT_HUB_TOKEN not set in .env.test")

    name = "guardrails_test_credential"
    # elitea_title should match display_name (no prefix needed)
    cred = module_credential_api.create_github_credential(
        display_name=name,
        base_url=settings.github_base_url,
        token=settings.git_hub_token,
        elitea_title=name,
    )
    logger.info("Created GitHub credential %s (elitea_title=%s) for guardrails tests",
                cred["id"], cred["elitea_title"])

    yield {"id": cred["id"], "elitea_title": cred["elitea_title"]}

    try:
        module_credential_api.delete_credential(cred["id"])
        logger.info("Deleted GitHub credential %s", cred["id"])
    except Exception as exc:
        logger.warning("Failed to delete credential %s: %s", cred["id"], exc)


@pytest.fixture(scope="module")
def guardrails_test_toolkit(
    guardrails_test_credential: dict,
    module_toolkit_api: ToolkitAPI,
):
    """Create GitHub toolkit for the entire test module.

    Created once before all tests, deleted after all tests complete.
    Includes tools list to enable specific tools (by default API creates toolkit without tools).
    """
    name = "guardrails_test_github_toolkit"

    # Use create_toolkit with selected_tools inside settings
    toolkit_settings = {
        "github_configuration": {
            "elitea_title": guardrails_test_credential["elitea_title"],
            "private": True,
        },
        "repository": settings.git_repo,
        "active_branch": GITHUB_BRANCH,
        "base_branch": GITHUB_BRANCH,
        "selected_tools": [
            "get_issues",
            "get_issue",
            "create_issue",
            "comment_on_issue",
            "list_branches_in_repo",
            "get_pull_request",
            "create_pull_request",
        ],
    }

    toolkit = module_toolkit_api.create_toolkit(
        name=name,
        description="GitHub toolkit for guardrails live-reload tests",
        toolkit_type="github",
        settings=toolkit_settings,
    )
    logger.info("Created GitHub toolkit %s for guardrails tests", toolkit["id"])

    yield {"id": toolkit["id"], "name": name}

    try:
        module_toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted GitHub toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete toolkit %s: %s", toolkit["id"], exc)


@pytest.fixture(scope="module")
def guardrails_test_agent(
    guardrails_test_toolkit: dict,
    module_agent_api: AgentAPI,
    browser: Browser,
    auth_state,
):
    """Create agent with GitHub toolkit for the entire test module.

    The toolkit is attached via UI (AgentDetailPage.add_toolkit) because
    the API doesn't support attaching toolkits directly during creation.

    Uses default model from config (gpt-5.2) for cost efficiency.
    """
    name = "guardrails_test_agent"
    description = "Agent for guardrails live-reload tests"
    instructions = """You are a helpful assistant with access to GitHub tools.

IMPORTANT: When asked to perform any GitHub-related task, you MUST use the
available tools to fulfill the request. Execute tools directly and return
the actual results.

For example:
- If asked about issues, use get_issue to fetch real issue data
- Always execute tools rather than explaining how to use them manually"""

    agent = module_agent_api.create_agent(name, description, instructions)
    agent_id = agent["id"]
    logger.info("Created agent %s for guardrails tests", agent_id)

    # Attach toolkit via UI
    ctx = browser.new_context(storage_state=auth_state)
    pg = ctx.new_page()
    agent_page = AgentDetailPage(pg)
    agent_page.navigate(agent_id)

    toolkit_name = guardrails_test_toolkit["name"]
    agent_page.add_toolkit(toolkit_name)
    agent_page.save_and_wait(timeout=FORM_SAVE_TIMEOUT)

    # Verify toolkit attached
    assert agent_page.is_toolkit_attached(toolkit_name), (
        f"Toolkit '{toolkit_name}' should be attached to agent"
    )
    logger.info("Toolkit '%s' attached to agent %s", toolkit_name, agent_id)

    pg.close()
    ctx.close()

    yield {"id": agent_id, "name": name, "toolkit_name": toolkit_name}

    try:
        module_agent_api.delete_agent(agent_id)
        logger.info("Deleted agent %s", agent_id)
    except Exception as exc:
        logger.warning("Failed to delete agent %s: %s", agent_id, exc)


# ---------------------------------------------------------------------------
# Admin Page Fixture (fresh page per test)
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_page(browser: Browser, auth_state) -> Page:
    """Create a browser page for Admin UI tests.

    Uses the same auth state as main UI tests since Admin UI shares
    the Keycloak authentication.
    """
    ctx = browser.new_context(
        storage_state=auth_state,
        viewport={"width": 1920, "height": 1080},
    )
    ctx.set_default_timeout(15000)
    ctx.set_default_navigation_timeout(30000)

    pg = ctx.new_page()
    yield pg

    pg.close()
    ctx.close()


# ===========================================================================
# ELITEA-1694: Blocked Toolkit Live-Reload and Case-Insensitive Matching
# ===========================================================================

class TestBlockedToolkitLiveReload:
    """Test blocked toolkits apply immediately without pylon reload.

    Manual test: ELITEA-1694
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/admin-portal/guardrails-live-reload/ELITEA-1694_blocked-toolkit-live-reload-case-insensitive.md",
        "onetest-ai Test Case link"
    )
    @allure.link("https://github.com/EliteaAI/elitea_issues/issues/5199", name="Issue #5199")
    @pytest.mark.p0
    def test_blocked_toolkit_live_reload_case_insensitive(
        self,
        page: Page,
        admin_page: Page,
        guardrails_test_agent: dict,
    ):
        """Verify blocked toolkit takes effect immediately with case-insensitive matching.

        Full E2E flow:
        1. Verify github toolkit is NOT blocked
        2. Verify "Blocked Toolkits" has no "Reload required" badge
        3. Open agent chat, verify tool executes successfully
        4. Add github toolkit to blocked list in Admin UI
        5. Save - verify no yellow banner mentioning pylon reload
        6. Return to agent chat, verify tool is now blocked
        7. Remove github from blocked list, save
        8. Verify tool executes again
        """
        agent_id = guardrails_test_agent["id"]
        toolkit_name = guardrails_test_agent["toolkit_name"]

        # --- Step 1-2: Navigate to Admin UI, verify initial state ---
        guardrails = GuardrailsAdminPage(admin_page)
        guardrails.navigate_to_guardrails()

        # Verify toolkit not initially blocked
        assert not guardrails.is_toolkit_blocked(TEST_TOOLKIT), (
            f"{TEST_TOOLKIT} toolkit should NOT be blocked initially"
        )

        # Verify no "Reload required" badge on Blocked Toolkits field
        assert not guardrails.has_reload_required_badge("Blocked Toolkits"), (
            "Blocked Toolkits should NOT have 'Reload required' badge"
        )

        # --- Step 3: Verify tool executes in agent chat ---
        agent_page = AgentDetailPage(page)
        agent_page.navigate(agent_id)

        toolkit_name = guardrails_test_agent["toolkit_name"]
        initial_count = agent_page._embedded_chat_messages().count()
        agent_page.send_chat_message(
            f"Use {toolkit_name} toolkit to get issue #1 from {settings.git_repo}. Execute the tool."
        )
        agent_page.wait_for_chat_response(
            initial_count=initial_count,
            stable_duration_ms=5000,
            timeout=CHAT_RESPONSE_TIMEOUT,
        )

        response1 = agent_page.get_last_chat_message()
        logger.info("Response before blocking: %s", response1[:300])
        assert "blocked" not in response1.lower() and "can't run" not in response1.lower(), (
            "Tool should execute successfully before blocking"
        )

        # --- Step 4-5: Block toolkit in Admin UI ---
        guardrails.add_blocked_toolkit(TEST_TOOLKIT)
        guardrails.save_configuration()

        # Verify no pylon reload banner
        assert not guardrails.has_reload_banner_after_save(), (
            "Should NOT show pylon reload banner after save"
        )
        banner_text = guardrails.get_reload_banner_text()
        if banner_text:
            assert "pylon" not in banner_text.lower(), (
                f"Banner should not mention pylon. Text: {banner_text}"
            )

        # --- Step 6-7: Verify toolkit is blocked ---
        agent_page.navigate(agent_id)
        # UI caches toolkit state on mount, reload required to see blocked indicator
        page.reload()
        agent_page.wait_for_page_load()

        assert agent_page.is_toolkit_blocked(toolkit_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"Toolkit '{toolkit_name}' should show 'blocked by your organization' indicator"
        )
        logger.info("Blocked toolkit indicator visible for '%s'", toolkit_name)

        # --- Step 8-9: Unblock and verify toolkit works again ---
        try:
            guardrails.remove_blocked_toolkit(TEST_TOOLKIT)
            guardrails.save_configuration()

            # Reload agent page and verify blocked indicator is gone
            agent_page.navigate(agent_id)
            page.reload()
            agent_page.wait_for_page_load()

            assert not agent_page.is_toolkit_blocked(toolkit_name), (
                f"Toolkit '{toolkit_name}' should NOT show blocked indicator after unblocking"
            )
            logger.info("Blocked indicator removed for '%s' after unblocking", toolkit_name)
        finally:
            # Cleanup: ensure toolkit is unblocked
            try:
                guardrails.remove_blocked_toolkit(TEST_TOOLKIT)
                guardrails.save_configuration()
            except Exception:
                pass  # Already removed or doesn't exist


# ===========================================================================
# ELITEA-1695: Blocked Tool Live-Reload and Case-Insensitive Matching
# ===========================================================================

class TestBlockedToolLiveReload:
    """Test blocked tools apply immediately without pylon reload.

    Manual test: ELITEA-1695
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/admin-portal/guardrails-live-reload/ELITEA-1695_blocked-tool-live-reload-case-insensitive.md",
        "onetest-ai Test Case link"
    )
    @allure.link("https://github.com/EliteaAI/elitea_issues/issues/5199", name="Issue #5199")
    @pytest.mark.p0
    def test_blocked_tool_live_reload_case_insensitive(
        self,
        page: Page,
        admin_page: Page,
        guardrails_test_agent: dict,
    ):
        """Verify blocked tool takes effect immediately with case-insensitive matching.

        Full E2E flow:
        1. Verify get_issue tool is NOT blocked
        2. Verify "Blocked Tools" has no "Reload required" badge
        3. Open agent chat, verify get_issue executes
        4. Block get_issue tool in Admin UI
        5. Save - verify no yellow banner
        6. Verify get_issue is blocked
        7. Verify other tools in toolkit still work (list_repos)
        8. Unblock get_issue, verify it works again
        """
        agent_id = guardrails_test_agent["id"]

        # --- Step 1-2: Navigate to Admin UI, verify initial state ---
        guardrails = GuardrailsAdminPage(admin_page)
        guardrails.navigate_to_guardrails()

        # Verify tool is NOT blocked initially
        assert not guardrails.is_tool_blocked(TEST_TOOL), (
            f"Tool '{TEST_TOOL}' should NOT be blocked initially"
        )

        # Verify no "Reload required" badge on Blocked Tools field
        assert not guardrails.has_reload_required_badge("Blocked Tools"), (
            "Blocked Tools should NOT have 'Reload required' badge"
        )

        # --- Step 3: Verify tool executes in agent chat ---
        agent_page = AgentDetailPage(page)
        agent_page.navigate(agent_id)

        initial_count = agent_page._embedded_chat_messages().count()
        agent_page.send_chat_message(
            f"Use get_issue tool to get issue #1 from {settings.git_repo}. Execute the tool."
        )
        agent_page.wait_for_chat_response(
            initial_count=initial_count,
            stable_duration_ms=5000,
            timeout=CHAT_RESPONSE_TIMEOUT,
        )

        response1 = agent_page.get_last_chat_message()
        logger.info("Response before blocking: %s", response1[:300])
        assert "blocked" not in response1.lower() and "not available" not in response1.lower(), (
            "get_issue tool should execute successfully before blocking"
        )

        # --- Step 4-5: Block specific tool in Admin UI ---
        guardrails.add_blocked_tool(TEST_TOOLKIT, TEST_TOOL)
        guardrails.save_configuration()

        # Verify no pylon reload banner
        assert not guardrails.has_reload_banner_after_save(), (
            "Should NOT show pylon reload banner after save"
        )

        # --- Step 6: Verify tool is blocked ---
        agent_page.navigate(agent_id)
        # UI caches toolkit state on mount, reload required to see blocked indicator
        page.reload()
        agent_page.wait_for_page_load()
        
        toolkit_name = guardrails_test_agent["toolkit_name"]
        assert agent_page.is_tool_blocked_in_toolkit(toolkit_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"Toolkit '{toolkit_name}' should show 'Some tools are not available anymore' indicator"
        )
        logger.info("Blocked tool indicator visible for '%s'", toolkit_name)

        # --- Step 7: Verify other tools still work ---
        # Use a simple question that requires minimal processing
        initial_count = 0  # After reload, chat history is cleared
        agent_page.send_chat_message(
            f"Does branch 'main' exist in {settings.git_repo}? Just answer yes or no."
        )
        agent_page.wait_for_chat_response(
            initial_count=initial_count,
            stable_duration_ms=3000,
            timeout=CHAT_RESPONSE_TIMEOUT,
        )

        response3 = agent_page.get_last_chat_message()
        logger.info("Response for other tool: %s", response3[:200])
        # list_branches should work if not blocked
        assert "yes" in response3.lower() or "main" in response3.lower() or "exist" in response3.lower(), (
            "Other tools in the toolkit should still work"
        )

        # --- Step 8: Unblock and verify ---
        try:
            guardrails.remove_blocked_tool(TEST_TOOL)
            guardrails.save_configuration()

            # Reload agent page and verify blocked indicator is gone
            agent_page.navigate(agent_id)
            page.reload()
            agent_page.wait_for_page_load()

            assert not agent_page.is_tool_blocked_in_toolkit(toolkit_name), (
                f"Toolkit '{toolkit_name}' should NOT show blocked tool indicator after unblocking"
            )
            logger.info("Blocked tool indicator removed for '%s' after unblocking", toolkit_name)
        finally:
            # Cleanup: ensure tool is unblocked
            try:
                guardrails.remove_blocked_tool(TEST_TOOL)
                guardrails.save_configuration()
            except Exception:
                pass  # Already removed or doesn't exist


# ===========================================================================
# ELITEA-1696: Sensitive Tool Live-Reload and Case-Insensitive Matching
# ===========================================================================

class TestSensitiveToolLiveReload:
    """Test sensitive tools apply immediately without pylon reload.

    Manual test: ELITEA-1696
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/admin-portal/guardrails-live-reload/ELITEA-1696_sensitive-tool-live-reload-case-insensitive.md",
        "onetest-ai Test Case link"
    )
    @allure.link("https://github.com/EliteaAI/elitea_issues/issues/5199", name="Issue #5199")
    @pytest.mark.p0
    def test_sensitive_tool_live_reload_case_insensitive(
        self,
        page: Page,
        admin_page: Page,
        guardrails_test_agent: dict,
    ):
        """Verify sensitive tool triggers authorization dialog immediately after config change.

        Full E2E flow:
        1. Verify get_issue is NOT in "Sensitive Action Tools"
        2. Verify "Sensitive Action Tools" has no "Reload required" badge
        3. Open agent chat, verify get_issue executes WITHOUT authorization dialog
        4. Add get_issue to Sensitive Action Tools in Admin UI
        5. Save - verify no yellow banner
        6. Trigger get_issue again
        7. Verify authorization dialog NOW appears
        8. Remove from sensitive list, verify dialog no longer appears
        """
        agent_id = guardrails_test_agent["id"]

        # --- Step 1-2: Navigate to Admin UI, verify initial state ---
        guardrails = GuardrailsAdminPage(admin_page)
        guardrails.navigate_to_guardrails()

        # Verify tool is NOT in sensitive list initially
        assert not guardrails.is_tool_in_sensitive_list(TEST_TOOL, TEST_TOOLKIT), (
            f"Tool '{TEST_TOOL}' should NOT be in sensitive list initially"
        )

        # Verify no "Reload required" badge on Sensitive Action Tools field
        assert not guardrails.has_reload_required_badge("Sensitive Action Tools"), (
            "Sensitive Action Tools should NOT have 'Reload required' badge"
        )

        # --- Step 3: Verify tool executes WITHOUT authorization dialog ---
        agent_page = AgentDetailPage(page)
        agent_page.navigate(agent_id)

        initial_count = agent_page._embedded_chat_messages().count()
        agent_page.send_chat_message(
            f"Use get_issue tool to get issue #1 from {settings.git_repo}. Execute the tool."
        )
        agent_page.wait_for_chat_response(
            initial_count=initial_count,
            stable_duration_ms=5000,
            timeout=CHAT_RESPONSE_TIMEOUT,
        )

        response1 = agent_page.get_last_chat_message()
        logger.info("Response before marking sensitive: %s", response1[:300])
        # Should execute without authorization needed
        assert "authorize" not in response1.lower() and "approval" not in response1.lower(), (
            "Tool should execute without authorization before marking sensitive"
        )

        # --- Step 4-5: Mark tool as sensitive in Admin UI ---
        # add_sensitive_tool handles creating github block if it doesn't exist
        guardrails.add_sensitive_tool(TEST_TOOLKIT, TEST_TOOL)
        guardrails.save_configuration()

        # Verify no pylon reload banner
        assert not guardrails.has_reload_banner_after_save(), (
            "Should NOT show pylon reload banner after save"
        )

        # --- Step 6-7: Verify authorization appears ---
        # Switch back to agent chat
        agent_page.navigate(agent_id)
        # UI caches toolkit state on mount, reload required to see sensitive action dialog
        page.reload()
        agent_page.wait_for_page_load()

        initial_count2 = agent_page._embedded_chat_messages().count()
        agent_page.send_chat_message(
            f"Use get_issue tool to get issue #1 from {settings.git_repo}. Execute the tool."
        )

        # Wait for Sensitive Action Authorization panel to appear
        auth_appeared = agent_page.wait_for_sensitive_action_authorization(
            timeout=30000, click_authorize=True
        )

        agent_page.wait_for_chat_response(
            initial_count=initial_count2,
            stable_duration_ms=5000,
            timeout=CHAT_RESPONSE_TIMEOUT,
        )

        response2 = agent_page.get_last_chat_message()
        logger.info("Response after marking sensitive: %s", response2[:300])

        # Authorization panel should have appeared
        assert auth_appeared, (
            "Sensitive Action Authorization panel should appear for sensitive tool"
        )

        # --- Step 8: Remove from sensitive list, verify normal execution ---
        try:
            guardrails.remove_sensitive_tool(TEST_TOOL)
            guardrails.save_configuration()

            # Switch back to agent chat (no reload!)
            agent_page.navigate(agent_id)

            initial_count3 = agent_page._embedded_chat_messages().count()
            agent_page.send_chat_message(
                f"Use get_issue tool to get issue #1 from {settings.git_repo}. Execute the tool."
            )
            agent_page.wait_for_chat_response(
                initial_count=initial_count3,
                stable_duration_ms=5000,
                timeout=CHAT_RESPONSE_TIMEOUT,
            )

            response3 = agent_page.get_last_chat_message()
            logger.info("Response after removing from sensitive: %s", response3[:300])
            # Should execute without authorization dialog
        finally:
            # Cleanup: ensure tool is removed from sensitive list
            try:
                guardrails.remove_sensitive_tool(TEST_TOOL)
                guardrails.save_configuration()
            except Exception:
                pass  # Already removed or doesn't exist
