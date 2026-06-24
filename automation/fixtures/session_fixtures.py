"""Session-level fixtures for browser and authentication.

These fixtures have session scope and are shared across all tests in a run.
They handle browser lifecycle and authentication state caching.

Fixtures:
- test_run_id: Unique UUID for the test session
- browser: Playwright Chromium browser instance
- auth_state: Authenticated browser storage state (cookies, localStorage, etc.)
"""
import uuid
import logging

import pytest
from playwright.sync_api import Browser, sync_playwright

from config import settings

logger = logging.getLogger("elitea.automation.fixtures.session")

ELITEA_URL = settings.elitea_url
TEST_USER_EMAIL = settings.test_user_email
TEST_USER_PASSWORD = settings.test_user_password


@pytest.fixture(scope="session")
def test_run_id() -> str:
    """Generate a unique ID for this test session.

    This ID is used for artifact naming, log correlation, and test run tracking.
    Also stored in pytest namespace for access from hooks.

    Returns:
        UUID string unique to this test session
    """
    run_id = str(uuid.uuid4())
    pytest.test_run_id = run_id  # type: ignore[attr-defined]
    logger.info("Test run ID: %s", run_id)
    return run_id


@pytest.fixture(scope="session")
def browser():
    """Launch a Chromium browser instance for the session.

    In headed mode (HEADLESS=false), launches maximized to fit the screen.
    In headless mode (HEADLESS=true, default), runs without UI for CI/CD.

    The browser instance is shared across all tests to improve performance.
    Each test gets its own context/page for isolation.

    Yields:
        Browser: Playwright Chromium browser instance
    """
    is_headless = settings.headless

    with sync_playwright() as p:
        launch_args = {
            "headless": is_headless,
        }

        # Maximize window in headed mode for debugging
        if not is_headless:
            args = ["--start-maximized"]
            # Position window on specific monitor if configured
            # Example: BROWSER_WINDOW_POSITION=1920,0 opens on second monitor (right)
            #          BROWSER_WINDOW_POSITION=-1920,0 opens on monitor to the left
            if settings.browser_window_position:
                args.append(f"--window-position={settings.browser_window_position}")
            launch_args["args"] = args

        browser = p.chromium.launch(**launch_args)
        logger.info("Browser launched (headless=%s)", is_headless)
        yield browser
        browser.close()
        logger.info("Browser closed")


@pytest.fixture(scope="session")
def auth_state(browser: Browser):
    """Login once and persist browser storage state for reuse.

    Uses API-based authentication to obtain cookies without opening a browser,
    making tests faster and more reliable. All UI tests share this auth state
    so we only log in once per session.

    For localhost: EliteaUI dev server uses VITE_DEV_TOKEN for auth, so no
    browser authentication is needed. Returns empty storage state.

    The returned storage state includes:
    - Cookies (Keycloak session, CSRF tokens, etc.)
    - localStorage data
    - sessionStorage data

    Args:
        browser: Playwright browser instance (required for type checking)

    Returns:
        dict: Browser storage state compatible with Playwright context creation

    Raises:
        pytest.skip: If authentication fails (missing credentials, API error)
    """
    # Check if running on localhost - EliteaUI dev server handles auth via VITE_DEV_TOKEN
    is_localhost = "localhost" in ELITEA_URL or "127.0.0.1" in ELITEA_URL
    if is_localhost:
        logger.info("Localhost detected (%s) - skipping API auth, EliteaUI uses VITE_DEV_TOKEN", ELITEA_URL)
        return {"cookies": [], "origins": []}

    from api_auth import get_playwright_storage_state

    try:
        # Get storage state via API authentication (no browser needed!)
        auth_url = settings.elitea_auth_url
        logger.info("Authenticating via API against %s (UI URL: %s)", auth_url, ELITEA_URL)
        storage_state = get_playwright_storage_state(
            base_url=auth_url,
            username=TEST_USER_EMAIL,
            password=TEST_USER_PASSWORD,
        )
        logger.info("Successfully authenticated via API (user: %s)", TEST_USER_EMAIL)
        return storage_state
    except Exception as e:
        logger.error("API authentication failed: %s", e)
        pytest.skip(
            f"Authentication failed — check TEST_USER_EMAIL and TEST_USER_PASSWORD: {e}"
        )
