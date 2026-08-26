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

from api import APIClient, AgentAPI, ArtifactAPI, ConversationAPI, CredentialAPI, PipelineAPI, SkillAPI, ToolkitAPI
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

    On localhost the EliteaUI dev server uses ``VITE_DEV_TOKEN`` for auth —
    there are no meaningful Keycloak cookies in the browser, and the Chat
    page's persistent WebSocket connections prevent ``networkidle`` from ever
    firing.  We therefore return an empty list so that all cookie-based API
    clients automatically fall back to Bearer token auth.

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
    # On localhost, VITE_DEV_TOKEN handles auth — skip cookie extraction.
    # All cookie-based API clients fall back to Bearer token when cookies=[].
    is_localhost = "localhost" in ELITEA_URL or "127.0.0.1" in ELITEA_URL
    if is_localhost:
        logger.info(
            "Localhost detected (%s) — skipping browser-cookie extraction; "
            "API fixtures will use Bearer token auth",
            ELITEA_URL,
        )
        return []

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
def skill_api(_browser_cookies):
    """Session-scoped SkillAPI client for skills management.

    Uses cookie-based auth on remote environments.  On localhost,
    ``_browser_cookies`` returns an empty list (the Chat page's WebSocket
    prevents networkidle), and ``SkillAPI`` automatically falls back to
    Bearer token auth via ``ELITEA_API_TOKEN``.

    Yields:
        SkillAPI: Authenticated skill API client

    Example:
        def test_delete_skill(skill_api):
            skill_api.delete_skill(skill_id)
    """
    api = SkillAPI(browser_cookies=_browser_cookies)
    logger.info("Created session-scoped SkillAPI client")
    yield api
    api.close()
    logger.debug("Closed SkillAPI client")


@pytest.fixture
def artifact_api(_browser_cookies):
    """Function-scoped ArtifactAPI client for artifact bucket management.

    Uses cookie-based authentication. Function-scoped to avoid connection
    pool exhaustion across rapid bucket create/delete cycles.

    Yields:
        ArtifactAPI: Authenticated artifact API client
    """
    api = ArtifactAPI(browser_cookies=_browser_cookies)
    logger.debug("Created function-scoped ArtifactAPI client")
    yield api
    api.close()
    logger.debug("Closed ArtifactAPI client")


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


# ---------------------------------------------------------------------------
# User B fixtures (for multi-user tests)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def _browser_cookies_user_b(browser: Browser, auth_state_user_b):
    """Extract Keycloak cookies for User B (secondary test user).

    Similar to _browser_cookies but for User B. Used in multi-user tests
    such as bucket permission enforcement.

    Args:
        browser: Playwright browser instance
        auth_state_user_b: Authenticated browser storage state for User B

    Returns:
        list[dict]: Browser cookies for User B
    """
    is_localhost = "localhost" in ELITEA_URL or "127.0.0.1" in ELITEA_URL
    if is_localhost:
        logger.info("Localhost detected — skipping User B cookie extraction")
        return []

    ctx = browser.new_context(
        viewport={"width": 1366, "height": 768},
        base_url=ELITEA_URL,
        storage_state=auth_state_user_b,
        permissions=["clipboard-read", "clipboard-write"],
    )
    ctx.set_default_timeout(10000)
    ctx.set_default_navigation_timeout(15000)

    pg = ctx.new_page()
    pg.goto("/", wait_until="domcontentloaded")
    pg.wait_for_load_state("networkidle", timeout=30000)
    cookies = ctx.cookies()
    pg.close()
    ctx.close()

    logger.info("Extracted %d browser cookies for User B", len(cookies))
    return cookies


@pytest.fixture
def artifact_api_user_b(_browser_cookies_user_b):
    """ArtifactAPI client authenticated as User B.

    Used for permission enforcement tests where we need to verify
    that User B (with restricted permissions) gets correct API responses.

    Yields:
        ArtifactAPI: Authenticated artifact API client for User B
    """
    api = ArtifactAPI(browser_cookies=_browser_cookies_user_b)
    logger.debug("Created ArtifactAPI client for User B")
    yield api
    api.close()
    logger.debug("Closed ArtifactAPI client for User B")


@pytest.fixture
def artifact_api_team_project(_browser_cookies):
    """ArtifactAPI client for Team project (not personal/private project).

    Team projects have "Manage Permissions" feature for buckets, unlike
    private projects. Used for multi-user permission tests.

    Requires ELITEA_TEAM_PROJECT_ID to be set in .env.test.

    Yields:
        ArtifactAPI: Authenticated artifact API client for Team project
    """
    team_project_id = settings.elitea_team_project_id
    if not team_project_id:
        pytest.skip(
            "Team project not configured — set ELITEA_TEAM_PROJECT_ID in .env.test "
            "for bucket permission tests"
        )

    api = ArtifactAPI(browser_cookies=_browser_cookies, project_id=str(team_project_id))
    logger.info("Created ArtifactAPI client for Team project (project_id=%s)", team_project_id)
    yield api
    api.close()
    logger.debug("Closed ArtifactAPI client for Team project")


@pytest.fixture
def artifact_api_user_b_team_project(_browser_cookies_user_b):
    """ArtifactAPI client for User B on Team project.

    Used for permission enforcement tests where User B has restricted
    permissions on a Team project bucket.

    Yields:
        ArtifactAPI: Authenticated artifact API client for User B on Team project
    """
    team_project_id = settings.elitea_team_project_id
    if not team_project_id:
        pytest.skip(
            "Team project not configured — set ELITEA_TEAM_PROJECT_ID in .env.test "
            "for bucket permission tests"
        )

    api = ArtifactAPI(browser_cookies=_browser_cookies_user_b, project_id=str(team_project_id))
    logger.info("Created ArtifactAPI client for User B on Team project (project_id=%s)", team_project_id)
    yield api
    api.close()
    logger.debug("Closed ArtifactAPI client for User B on Team project")
