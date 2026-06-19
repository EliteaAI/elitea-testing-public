"""Pytest configuration for Elitea platform automation tests.

Configures Playwright browser, environment loading, API clients, and shared fixtures.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

import pytest
from playwright.sync_api import Browser, BrowserContext, Page

from api import AgentAPI, ConversationAPI, CredentialAPI, PipelineAPI, ToolkitAPI
from config import settings

# ---------------------------------------------------------------------------
# Import fixtures from organized modules
# ---------------------------------------------------------------------------
from fixtures.session_fixtures import (
    test_run_id,
    browser,
    auth_state,
)
from fixtures.api_fixtures import (
    api,
    _browser_cookies,
    conversation_api,
    agent_api,
    credential_api,
    toolkit_api,
    pipeline_api,
)
from fixtures.data_fixtures import (
    conversation_id,
    agent_id,
    pipeline_id,
    pipeline_with_llm_id,
    github_credential,
    github_toolkit,
    invalid_jira_credential,
    jira_toolkit_with_invalid_credential,
    invalid_github_credential,
    github_toolkit_with_invalid_credential,
)
from fixtures.cleanup_fixtures import (
    cleanup_autotest_pipelines_at_end,
    cleanup_leaked_credentials,
    cleanup_leaked_toolkits_at_end,
    cleanup_autotest_agents_at_end,
    cleanup_all_conversations_at_end,
)

# ---------------------------------------------------------------------------
# Configuration constants (sourced from settings — backed by .env.test)
# ---------------------------------------------------------------------------
ELITEA_URL = settings.elitea_url
ELITEA_API_BASE = settings.elitea_api_base
ELITEA_API_TOKEN = settings.elitea_api_token
ELITEA_PROJECT_ID = str(settings.elitea_project_id)

TEST_USER_EMAIL = settings.test_user_email
TEST_USER_PASSWORD = settings.test_user_password

# Screenshots directory
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Logger
logger = logging.getLogger("elitea.automation")


# ---------------------------------------------------------------------------
# Pytest configuration hooks
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """Configure report paths and HTML reports.

    Ensures reports always go to automation/reports/ regardless of where
    pytest is invoked from (VS Code uses parent directory as rootdir).

    VS Code pytest runner doesn't support pytest-html plugin, so we only
    enable HTML reports when running from command line or CI/CD.
    """
    # Get absolute path to automation/reports/ directory
    automation_dir = Path(__file__).parent
    reports_dir = automation_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Always set JUnit XML to absolute path in automation/reports/
    junit_path = str(reports_dir / "junit.xml")
    config.option.xmlpath = junit_path

    # Check if running from VS Code test explorer
    is_vscode = any('vscode_pytest' in str(p) for p in config.pluginmanager.get_plugins())

    # Check if HTML flag already provided by user
    has_html_flag = any('--html' in arg for arg in sys.argv)

    # Only add HTML report if not VS Code and not already specified
    if not is_vscode and not has_html_flag:
        # Add HTML report options with absolute path
        config.option.htmlpath = str(reports_dir / "report.html")
        config.option.self_contained_html = True
        logger.info("HTML reporting enabled (command line mode)")

    logger.info("Reports directory: %s", reports_dir)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def perform_login(page: Page) -> bool:
    """Perform UI login with test credentials.

    Waits for a login form, fills in credentials, and waits for redirect.
    Returns True on success, False otherwise.

    Adapt the selectors below to match Elitea's actual login page.
    """
    if not TEST_USER_EMAIL or not TEST_USER_PASSWORD:
        logger.warning("No test credentials configured — skipping login")
        return False

    try:
        # Wait for email/username field (Keycloak uses name="username")
        page.wait_for_selector('input[name="username"], input[name="email"], input[name="identifier"], input[type="email"]', timeout=15000)

        # Fill email/username
        email_input = page.locator('input[name="username"], input[name="email"], input[name="identifier"], input[type="email"]').first
        email_input.fill(TEST_USER_EMAIL)

        # Look for a continue/next button or password field directly
        password_input = page.locator('input[name="password"], input[type="password"]').first
        if not password_input.is_visible():
            page.locator('button:has-text("Continue"), button:has-text("Next"), button[type="submit"]').first.click()
            page.wait_for_selector('input[name="password"], input[type="password"]', timeout=10000)
            password_input = page.locator('input[name="password"], input[type="password"]').first

        password_input.fill(TEST_USER_PASSWORD)

        # Submit
        page.locator('button:has-text("Sign in"), button:has-text("Log in"), button:has-text("Continue"), button[type="submit"]').first.click()

        # Wait for redirect away from login
        page.wait_for_url(lambda url: "sign-in" not in url and "login" not in url, timeout=30000)
        logger.info("Login successful")
        return True
    except Exception as e:
        logger.error("Login failed: %s", e)
        return False


def attach_screenshot(page: Page, name: str, description: str = "") -> Path:
    """Take a screenshot, save locally, and log for reporting.

    Args:
        page: Playwright Page instance.
        name: Base name for the screenshot file.
        description: Optional description for the log entry.

    Returns:
        Path to the saved screenshot file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = SCREENSHOTS_DIR / filename

    screenshot_bytes = page.screenshot(full_page=True)
    with open(filepath, "wb") as f:
        f.write(screenshot_bytes)

    logger.info(
        description or f"Screenshot: {name}",
        extra={"attachment": {"name": filename, "data": screenshot_bytes, "mime": "image/png"}},
    )
    return filepath


# ===========================================================================
# Session-level fixtures (imported from fixtures/session_fixtures.py)
# ===========================================================================
# - test_run_id: Unique UUID for this test session
# - browser: Playwright Chromium browser instance
# - auth_state: Authenticated browser storage state

# ===========================================================================
# API fixtures (imported from fixtures/api_fixtures.py)
# ===========================================================================
# - api: Generic API client with bearer token auth
# - _browser_cookies: Helper for extracting Keycloak cookies
# - conversation_api: ConversationAPI client (session scope)
# - agent_api: AgentAPI client (session scope)
# - credential_api: CredentialAPI client (function scope)
# - toolkit_api: ToolkitAPI client (function scope)
# - pipeline_api: PipelineAPI client (session scope)

# ===========================================================================
# Data fixtures (imported from fixtures/data_fixtures.py)
# ===========================================================================
# - conversation_id: Fresh conversation per test
# - agent_id: Fresh agent per test
# - pipeline_id: Fresh empty pipeline per test
# - pipeline_with_llm_id: Fresh executable pipeline with LLM node

# ===========================================================================
# Cleanup fixtures (imported from fixtures/cleanup_fixtures.py)
# ===========================================================================
# - cleanup_autotest_pipelines_at_end: Delete autotest_ pipelines
# - cleanup_leaked_credentials: Delete ALL credentials (aggressive)
# - cleanup_autotest_agents_at_end: Delete autotest_ agents
# - cleanup_all_conversations_at_end: Delete ALL conversations (aggressive)
#
# All cleanup fixtures use autouse=True (run automatically at session end)

# ===========================================================================
# Browser fixtures (stay in conftest.py - coupled to hooks)
# ===========================================================================

@pytest.fixture
def context(browser: Browser, auth_state) -> BrowserContext:
    """Create a fresh browser context per test, pre-loaded with auth state.

    Configured with optimized timeouts:
    - 10s for actions (click, fill, wait_for, etc.) instead of default 30s
    - 15s for navigation (page.goto) for slower page loads

    Viewport behavior:
    - Headed mode (HEADLESS=false): no_viewport=True → fits browser window
    - Headless mode (HEADLESS=true): fixed 1366x768 for consistency
    """
    is_headless = settings.headless

    if is_headless:
        # Headless: use fixed viewport for consistent screenshots
        ctx = browser.new_context(
            viewport={"width": 1366, "height": 768},
            base_url=ELITEA_URL,
            storage_state=auth_state,
            permissions=["clipboard-read", "clipboard-write"],  # Allow clipboard access
        )
    else:
        # Headed: let viewport match browser window size
        ctx = browser.new_context(
            no_viewport=True,  # Auto-fit to window
            base_url=ELITEA_URL,
            storage_state=auth_state,
            permissions=["clipboard-read", "clipboard-write"],  # Allow clipboard access
        )

    # Set shorter timeouts for faster failure feedback
    ctx.set_default_timeout(10000)              # 10s for most actions
    ctx.set_default_navigation_timeout(15000)   # 15s for page navigation

    yield ctx
    ctx.close()


@pytest.fixture
def page(context: BrowserContext) -> Page:
    """Create a new page for each test."""
    pg = context.new_page()
    yield pg
    pg.close()


# ===========================================================================
# Screenshot hook — captures only on test failures
# ===========================================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture screenshot on test failure/error and save locally.

    Mirrors JUnit's TestWatcher pattern - only captures debugging artifacts
    when tests fail, not on success. Reduces noise and storage usage.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    # Try to find a page fixture in this test
    pg: Page | None = None
    for fixture_name in ("page", "test_page"):
        if fixture_name in item.funcargs:
            pg = item.funcargs[fixture_name]
            break

    if pg is None:
        return

    # Only capture screenshots on failures (failed, error, skipped)
    if report.passed:
        return

    try:
        status = "FAIL" if report.failed else "ERROR" if hasattr(report, "error") else "SKIP"
        screenshot_bytes = pg.screenshot(full_page=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{item.name}_{status}_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename

        with open(filepath, "wb") as f:
            f.write(screenshot_bytes)

        print(f"\n  [{status}] Screenshot: {filepath}")
    except Exception as e:
        print(f"\n  Failed to capture screenshot: {e}")


def pytest_sessionfinish(session, exitstatus):
    """Archive reports after test session completes.

    Creates timestamped copies of report.html and junit.xml in reports/archive/
    so you can keep historical test results.

    Note: HTML report may not exist yet (pytest-html writes after this hook).
    Use pytest_terminal_summary for post-HTML archiving.
    """
    print("Running teardown with pytest sessionfinish...")

    reports_dir = Path(__file__).parent / "reports"
    archive_dir = reports_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Store timestamp for use in terminal_summary hook
    session.config._archive_timestamp = timestamp  # type: ignore

    # Archive JUnit XML (available at this point)
    junit_xml = reports_dir / "junit.xml"
    if junit_xml.exists():
        import shutil
        archived_xml = archive_dir / f"junit_{timestamp}.xml"
        shutil.copy2(junit_xml, archived_xml)
        print(f"  [ARCHIVE] JUnit XML: {archived_xml}")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Archive HTML report after pytest-html writes it."""
    reports_dir = Path(__file__).parent / "reports"
    archive_dir = reports_dir / "archive"

    timestamp = getattr(config, "_archive_timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))

    # Archive HTML report (written by pytest-html after sessionfinish)
    html_report = reports_dir / "report.html"
    if html_report.exists():
        import shutil
        archived_html = archive_dir / f"report_{timestamp}.html"
        shutil.copy2(html_report, archived_html)
        terminalreporter.write_line(f"  [ARCHIVE] HTML report: {archived_html}")
