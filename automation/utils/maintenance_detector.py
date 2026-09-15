"""Maintenance page/banner detection utilities.

Detects when the Elitea platform is in maintenance mode via:
1. High z-index maintenance banner overlays
2. Full-page maintenance messages
3. API maintenance HTML responses

Used by conftest.py hooks to automatically retry tests during maintenance.
"""

import logging
import time
from typing import Optional

from playwright.sync_api import Page

logger = logging.getLogger("elitea.maintenance")


class MaintenanceError(Exception):
    """Raised when API returns maintenance page/error."""

    pass


class MaintenanceTimeoutError(Exception):
    """Raised when maintenance doesn't clear within timeout."""

    pass


class MaintenanceState:
    """Represents detected maintenance state.

    Attributes:
        is_maintenance: True if maintenance detected
        message: Extracted maintenance message (truncated)
        banner_present: True if maintenance banner overlay detected
        full_page: True if full-page maintenance message detected
    """

    def __init__(
        self,
        is_maintenance: bool,
        message: Optional[str] = None,
        banner_present: bool = False,
        full_page: bool = False,
    ):
        self.is_maintenance = is_maintenance
        self.message = message
        self.banner_present = banner_present
        self.full_page = full_page

    def __bool__(self):
        """Allow boolean check: if maintenance_state: ..."""
        return self.is_maintenance

    def __repr__(self):
        return (
            f"MaintenanceState(is_maintenance={self.is_maintenance}, "
            f"banner={self.banner_present}, full_page={self.full_page}, "
            f"message={self.message!r})"
        )


def detect_maintenance_ui(page: Page) -> MaintenanceState:
    """Detect if page shows maintenance banner or full maintenance page.

    Detection strategy:
    1. Check for high z-index overlays (>2000) with maintenance keywords
    2. Check for full-page maintenance when normal app structure missing

    Args:
        page: Playwright Page instance

    Returns:
        MaintenanceState with detection results

    Example:
        >>> state = detect_maintenance_ui(page)
        >>> if state:
        ...     logger.warning("Maintenance detected: %s", state.message)
        ...     wait_for_maintenance_clear(page)
    """
    # Check 1: High z-index overlay (maintenance banner)
    # The MaintenanceBanner component renders at z-index 2400
    banner_check = page.evaluate(
        """() => {
        const overlays = document.querySelectorAll('div[class*="MuiBox"], div[role="alert"]');
        for (const overlay of overlays) {
            const zIndex = parseInt(getComputedStyle(overlay).zIndex);
            if (zIndex > 2000) {
                const text = overlay.textContent || '';
                // Check for maintenance/deployment keywords
                if (/maintenance|deploying|deploy|under construction|temporarily unavailable/i.test(text)) {
                    return {
                        present: true,
                        message: text.trim().slice(0, 200)
                    };
                }
            }
        }
        return {present: false, message: null};
    }"""
    )

    if banner_check["present"]:
        return MaintenanceState(
            is_maintenance=True,
            message=banner_check["message"],
            banner_present=True,
            full_page=False,
        )

    # Check 2: Full-page maintenance message
    # When backend is down, nginx/cloudflare may serve a maintenance HTML page
    full_page_check = page.evaluate(
        """() => {
        // Check if main app structure is missing (indicates non-SPA page)
        const hasMainApp = document.querySelector('main') !== null;
        const hasReactRoot = document.querySelector('#root') !== null;

        if (hasMainApp && hasReactRoot) {
            // Normal app structure present
            return {is_maintenance: false};
        }

        // No main app structure → check for maintenance keywords in body
        const body = document.body.textContent || '';
        const keywords = /maintenance|under construction|temporarily unavailable|scheduled downtime|service unavailable/i;

        if (keywords.test(body)) {
            return {
                is_maintenance: true,
                message: body.trim().slice(0, 300)
            };
        }

        return {is_maintenance: false};
    }"""
    )

    if full_page_check["is_maintenance"]:
        return MaintenanceState(
            is_maintenance=True,
            message=full_page_check.get("message"),
            banner_present=False,
            full_page=True,
        )

    return MaintenanceState(is_maintenance=False)


def wait_for_maintenance_clear(
    page: Page, timeout: int = 300000, check_interval: int = 30000
) -> bool:
    """Poll until maintenance state clears or timeout.

    Reloads page every `check_interval` and checks maintenance state.
    Used after detecting maintenance to wait for platform to come back online.

    Args:
        page: Playwright Page instance
        timeout: Maximum wait time in milliseconds (default 5 minutes)
        check_interval: Polling interval in milliseconds (default 30 seconds)

    Returns:
        True if maintenance cleared within timeout
        False if timeout reached while still in maintenance

    Example:
        >>> if detect_maintenance_ui(page):
        ...     cleared = wait_for_maintenance_clear(page, timeout=300000)
        ...     if not cleared:
        ...         raise MaintenanceTimeoutError("Maintenance did not clear")
    """
    start = time.time()

    logger.info(
        "Waiting for maintenance to clear (timeout=%ds, interval=%ds)",
        timeout / 1000,
        check_interval / 1000,
    )

    while (time.time() - start) * 1000 < timeout:
        # Reload page to check current state
        try:
            page.reload(wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            logger.debug("Reload during maintenance wait failed: %s", e)
            time.sleep(check_interval / 1000)
            continue

        # Check if maintenance cleared
        state = detect_maintenance_ui(page)
        if not state:
            elapsed = time.time() - start
            logger.info("Maintenance cleared after %.1fs", elapsed)
            return True

        logger.debug(
            "Still in maintenance (%.1fs elapsed), waiting %ds...",
            time.time() - start,
            check_interval / 1000,
        )
        time.sleep(check_interval / 1000)

    # Timeout reached
    logger.warning("Maintenance did not clear after %.1fs", timeout / 1000)
    return False


def is_maintenance_response(response_status: int, content_type: str, body: str) -> tuple[bool, Optional[str]]:
    """Detect if HTTP response is a maintenance page.

    Maintenance responses:
    - 502/503/504 with HTML body containing maintenance keywords
    - 200 OK with HTML body (when JSON expected) containing maintenance keywords

    Args:
        response_status: HTTP status code
        content_type: Content-Type header value
        body: Response body (first 500 chars sufficient)

    Returns:
        (is_maintenance, message) tuple

    Example:
        >>> is_maint, msg = is_maintenance_response(503, "text/html", "<html>Under maintenance</html>")
        >>> if is_maint:
        ...     raise MaintenanceError(msg)
    """
    body_preview = body[:500].lower()

    # Maintenance keywords to look for
    keywords = [
        "maintenance",
        "under construction",
        "temporarily unavailable",
        "scheduled downtime",
        "service unavailable",
    ]

    # Check 1: Server error (502/503/504) with HTML maintenance page
    if response_status in (502, 503, 504):
        # Check if it's HTML (not JSON error response)
        if "text/html" in content_type:
            # Check for maintenance keywords
            if any(keyword in body_preview for keyword in keywords):
                return True, f"{response_status} - Maintenance page detected"

    # Check 2: 200 OK that's actually maintenance HTML (when JSON expected)
    # This happens when proxy/cloudflare serves maintenance page before reaching app
    if response_status == 200:
        # Expected JSON but got HTML
        if "text/html" in content_type and "application/json" not in content_type:
            # Check for maintenance keywords
            if any(keyword in body_preview for keyword in keywords):
                return True, "200 OK but maintenance HTML returned (expected JSON)"

    return False, None
