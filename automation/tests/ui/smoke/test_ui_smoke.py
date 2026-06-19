"""UI Smoke Tests for Elitea Platform.

Verifies basic page loads and navigation in the Elitea web application.
Requires ``TEST_USER_EMAIL`` and ``TEST_USER_PASSWORD`` in ``.env.test``.

Markers:
    - smoke: quick sanity checks
    - ui: requires a browser

Usage::

    cd automation
    pytest test_ui_smoke.py -v
    HEADLESS=false pytest test_ui_smoke.py -v   # watch the browser
"""

import pytest
from pages import BasePage

pytestmark = [pytest.mark.smoke, pytest.mark.ui]


class TestHomePage:
    """Verify the Elitea home / landing page loads correctly."""

    def test_page_loads(self, page):
        """The home page should load without errors."""
        bp = BasePage(page)
        bp.navigate("/")
        # The page title or a key element should be visible
        assert page.title(), "Page title should not be empty"

    def test_main_content_visible(self, page):
        """The main content area should render after navigation."""
        bp = BasePage(page)
        bp.navigate("/")
        # Wait for any <main> element or a known root container
        main = page.locator("main, #root, #app, [role='main']").first
        main.wait_for(state="visible", timeout=15000)
        assert main.is_visible(), "Main content area should be visible"



