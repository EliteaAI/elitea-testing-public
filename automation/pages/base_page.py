"""Base page object with shared navigation and wait helpers.

All page objects should inherit from :class:`BasePage` to get consistent
wait patterns, screenshot helpers, and navigation methods.
"""

import logging
from playwright.sync_api import Page

from config import settings

logger = logging.getLogger("elitea.pages")


class BasePage:
    """Base class for all Elitea page objects.

    Provides:
    - ``navigate(path)`` — go to a relative URL and wait for network idle.
    - ``reload_and_wait()`` — reload and wait for a key selector.
    - ``wait_for_network(timeout)`` — wait for network to settle.
    - ``screenshot(name)`` — save a screenshot via the shared helper.

    Args:
        page: Playwright ``Page`` instance.
    """

    def __init__(self, page: Page):
        self.page = page

    def navigate(self, path: str) -> None:
        """Navigate to *path* relative to ``app_base_url``.

        Args:
            path: URL path (e.g. ``/skills/all``). Absolute URLs are used
                as-is. ``app_base_url`` already includes the app prefix
                (set via ``APP_PREFIX`` in ``.env.test``: ``/app`` on deployed
                envs, ``""`` on localhost), so page objects use bare paths like
                ``/skills/all`` on all targets.
        """
        base = settings.app_base_url
        url = f"{base}{path}" if not path.startswith("http") else path
        logger.info("Navigating to %s", url)
        self.page.goto(url, wait_until="domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            # Pages with persistent WebSocket connections (e.g. Skills, Chat)
            # never reach networkidle.  domcontentloaded is sufficient here;
            # each page object's wait_for_page_load handles the rest.
            logger.debug("networkidle not reached after navigation to %s — continuing", url)
        
        # Wait for any loading spinner to disappear
        spinner = self.page.locator('svg[class*="CircularProgress"], [role="progressbar"], [class*="spinner"]')
        if spinner.count() > 0:
            try:
                spinner.first.wait_for(state="hidden", timeout=10000)
                logger.info("Loading spinner disappeared after navigation")
            except Exception:
                # Spinner might not be present on all pages, continue
                pass

    def reload_and_wait(self, timeout: int = 15000) -> None:
        """Reload the page and wait for it to be ready.

        Combines reload with networkidle wait and page-specific
        load verification if available (wait_for_page_load method).

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.page.reload(wait_until="networkidle", timeout=timeout)
        if hasattr(self, 'wait_for_page_load'):
            self.wait_for_page_load(timeout=timeout)
        else:
            self.wait_for_network(timeout=timeout)
        logger.info("Page reloaded and ready")

    def wait_for_network(self, timeout: int = 15000) -> None:
        """Wait for network activity to settle.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.page.wait_for_load_state("networkidle", timeout=timeout)

    def screenshot(self, name: str, description: str = "") -> None:
        """Take a screenshot using the shared conftest helper.

        Args:
            name: Base file name for the screenshot.
            description: Optional description for log/report entry.
        """
        from conftest import attach_screenshot
        attach_screenshot(self.page, name, description)

    def dismiss_banner_if_present(self) -> None:
        """Dismiss the top banner/notification overlay if it exists.

        The MUI banner overlay (z-index 1200) covers the conversation
        header area and intercepts pointer events on buttons like
        "Search conversations".  Clicking its close button removes
        the overlay from the DOM entirely.
        """
        # Use JS to find and click close buttons in high-z-index overlays
        # that sit above the conversation header area.
        dismissed = self.page.evaluate("""() => {
            const btns = document.querySelectorAll('button[aria-label="close"]');
            for (const btn of btns) {
                // Walk up to check if this button is inside a high-z-index overlay
                let el = btn.parentElement;
                while (el) {
                    const z = parseInt(getComputedStyle(el).zIndex);
                    if (z > 1000) {
                        btn.click();
                        return true;
                    }
                    el = el.parentElement;
                }
            }
            return false;
        }""")
        if dismissed:
            self.page.wait_for_timeout(500)
            logger.info("Dismissed banner overlay")
        else:
            logger.debug("No banner overlay found to dismiss")

    def capture_requests_matching(self, url_substring: str, method: str | None = None) -> list[dict]:
        """Start capturing network requests whose URL contains *url_substring*.

        Attaches ``page.on("request", ...)`` and ``page.on("response", ...)``
        listeners and returns a list that is populated live (append-only) as
        matching requests fire from this point forward — read it any time
        after calling this to see every matching request captured so far,
        including its response status once the response has arrived (status
        is ``None`` until then; responses are matched to entries by URL).

        Args:
            url_substring: Substring to match against each request's URL
                (e.g. ``"skill/prompt_lib"``).
            method: Optional HTTP method filter (e.g. ``"PATCH"``). When
                omitted, all methods are captured.

        Returns:
            A list of ``{"method": str, "url": str, "status": int | None}``
            dicts, appended to live as matching requests occur, with
            ``status`` filled in once the matching response arrives.
        """
        captured: list[dict] = []

        def _on_request(request):
            if url_substring not in request.url:
                return
            if method is not None and request.method.upper() != method.upper():
                return
            captured.append({"method": request.method, "url": request.url, "status": None})

        def _on_response(response):
            if url_substring not in response.url:
                return
            if method is not None and response.request.method.upper() != method.upper():
                return
            # Match to the most recent same-URL entry still awaiting a status.
            for entry in reversed(captured):
                if entry["url"] == response.url and entry["status"] is None:
                    entry["status"] = response.status
                    break

        self.page.on("request", _on_request)
        self.page.on("response", _on_response)
        logger.debug(
            "Started capturing requests matching %r (method=%s)", url_substring, method
        )
        return captured

    def get_clipboard_text(self) -> str:
        """Read text from the system clipboard.

        Uses Playwright's evaluate to access the Clipboard API.
        Requires clipboard permissions to be granted (Playwright handles this automatically).

        Returns:
            Text content from clipboard, or empty string if clipboard is empty or inaccessible.

        Note:
            This reads the actual system clipboard, so it will return whatever
            was last copied, even if it was copied outside the browser.
        """
        try:
            clipboard_text = self.page.evaluate("() => navigator.clipboard.readText()")
            logger.info(f"Read from clipboard: {clipboard_text[:50]}...")
            return clipboard_text
        except Exception as e:
            logger.warning(f"Failed to read clipboard: {e}")
            return ""
