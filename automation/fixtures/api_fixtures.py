"""API client fixtures for Elitea services.

Provides authenticated API clients for different service domains:
- api: Generic API client with bearer token auth
- conversation_api: Chat conversations (session scope)
- agent_api: AI agents (session scope)
- toolkit_api: External toolkits (function scope - high churn)
- credential_api: Credentials management (function scope - high churn)
- pipeline_api: Data pipelines (session scope)

Also provides _browser_cookies helper for cookie-based authentication.

Scope strategy:
- Session scope: For read-heavy or low-churn APIs (conversations, agents, pipelines)
- Function scope: For high-churn APIs to avoid connection pool exhaustion (toolkits, credentials)
"""
import logging

import pytest
from playwright.sync_api import Browser

from api import APIClient, AgentAPI, ConversationAPI, CredentialAPI, PipelineAPI, ToolkitAPI
from config import settings

logger = logging.getLogger("elitea.automation.fixtures.api")

ELITEA_URL = settings.elitea_url


@pytest.fixture(scope="session")
def api() -> APIClient:
    """Shared API client with bearer token authentication.

    Uses ELITEA_API_TOKEN from environment for authentication.
    Suitable for API-only tests that don't need browser cookies.

    Yields:
        APIClient: Authenticated API client instance

    Example:
        def test_api_health(api):
            health = api.get_health()
            assert health["status"] == "ok"
    """
    client = APIClient()
    logger.info("Created session-scoped API client")
    yield client
    client.close()
    logger.debug("Closed API client")


@pytest.fixture(scope="session")
def _browser_cookies(browser: Browser, auth_state):
    """Extract Keycloak cookies once per session for reuse by API fixtures.

    Opens a temporary browser context with the stored auth state, navigates
    to populate all cookies, then caches the result for the entire session.

    Some Elitea API endpoints require Keycloak session cookies in addition
    to (or instead of) bearer tokens. This fixture provides those cookies
    for API clients.

    Args:
        browser: Playwright browser instance
        auth_state: Authenticated browser storage state

    Returns:
        list[dict]: Browser cookies suitable for requests.Session

    Note:
        This is a private fixture (prefix: _) meant for internal use by
        other API fixtures. Tests should use the specific API client
        fixtures (conversation_api, agent_api, etc.) instead.
    """
    ctx = browser.new_context(
        viewport={"width": 1366, "height": 768},  # Fixed size for cookie extraction
        base_url=ELITEA_URL,
        storage_state=auth_state,
        permissions=["clipboard-read", "clipboard-write"],
    )

    # Apply timeout configuration for consistency
    ctx.set_default_timeout(10000)
    ctx.set_default_navigation_timeout(15000)

    pg = ctx.new_page()
    pg.goto("/", wait_until="domcontentloaded")
    pg.wait_for_load_state("networkidle", timeout=30000)
    cookies = ctx.cookies()
    pg.close()
    ctx.close()

    logger.info("Extracted %d browser cookies for API authentication", len(cookies))
    return cookies


@pytest.fixture(scope="session")
def conversation_api(_browser_cookies):
    """Session-scoped ConversationAPI client for chat conversations.

    Uses cookie-based authentication. Suitable for most conversation tests
    which are read-heavy or have low entity creation rates.

    Yields:
        ConversationAPI: Authenticated conversation API client

    Example:
        def test_list_conversations(conversation_api):
            convos = conversation_api.list_conversations()
            assert "rows" in convos
    """
    api = ConversationAPI(browser_cookies=_browser_cookies)
    logger.info("Created session-scoped ConversationAPI client")
    yield api
    api.close()
    logger.debug("Closed ConversationAPI client")


@pytest.fixture(scope="session")
def agent_api(_browser_cookies):
    """Session-scoped AgentAPI client for AI agents.

    Uses cookie-based authentication. Suitable for most agent tests
    which are read-heavy or have low entity creation rates.

    Yields:
        AgentAPI: Authenticated agent API client

    Example:
        def test_list_agents(agent_api):
            agents = agent_api.list_agents()
            assert "rows" in agents
    """
    api = AgentAPI(browser_cookies=_browser_cookies)
    logger.info("Created session-scoped AgentAPI client")
    yield api
    api.close()
    logger.debug("Closed AgentAPI client")


@pytest.fixture
def credential_api(_browser_cookies):
    """Function-scoped CredentialAPI client — fresh session per test.

    Credential tests create/delete many entities, so each test gets its own
    ``requests.Session`` to avoid connection pool exhaustion.

    Uses function scope to prevent "Connection pool exhausted" errors that
    can occur when many credentials are created/deleted in rapid succession.

    Yields:
        CredentialAPI: Authenticated credential API client

    Example:
        def test_create_credential(credential_api):
            cred = credential_api.create_credential("test", "github", {...})
            assert cred["name"] == "test"
    """
    api = CredentialAPI(browser_cookies=_browser_cookies)
    logger.debug("Created function-scoped CredentialAPI client")
    yield api
    api.close()
    logger.debug("Closed CredentialAPI client")


@pytest.fixture
def toolkit_api(_browser_cookies):
    """Function-scoped ToolkitAPI client — fresh session per test.

    Toolkit tests create/delete many entities, so each test gets its own
    ``requests.Session`` to avoid connection pool exhaustion.

    Uses function scope to prevent "Connection pool exhausted" errors that
    can occur when many toolkits are installed/uninstalled in rapid succession.

    Yields:
        ToolkitAPI: Authenticated toolkit API client

    Example:
        def test_install_toolkit(toolkit_api):
            toolkit = toolkit_api.install_toolkit("github-toolkit")
            assert toolkit["status"] == "installed"
    """
    api = ToolkitAPI(browser_cookies=_browser_cookies)
    logger.debug("Created function-scoped ToolkitAPI client")
    yield api
    api.close()
    logger.debug("Closed ToolkitAPI client")


@pytest.fixture(scope="session")
def pipeline_api(_browser_cookies):
    """Session-scoped PipelineAPI client for data pipelines.

    Uses cookie-based authentication. Suitable for most pipeline tests
    which have relatively low entity creation rates.

    Yields:
        PipelineAPI: Authenticated pipeline API client

    Example:
        def test_list_pipelines(pipeline_api):
            pipelines = pipeline_api.list_pipelines()
            assert "rows" in pipelines
    """
    api = PipelineAPI(browser_cookies=_browser_cookies)
    logger.info("Created session-scoped PipelineAPI client")
    yield api
    api.close()
    logger.debug("Closed PipelineAPI client")
