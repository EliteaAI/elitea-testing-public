"""Alternative API-based authentication using forward-auth endpoint.

This module provides a simpler authentication method that bypasses Keycloak
and uses the forward-auth direct login form instead.

Usage:
    from api_auth_forward import get_auth_cookies_forward, get_playwright_storage_state_forward

    # Get cookies via forward-auth
    cookies = get_auth_cookies_forward()

    # Or get full Playwright storage state
    storage_state = get_playwright_storage_state_forward()
"""

import logging
from typing import Optional
import requests

from config import settings

logger = logging.getLogger("elitea.api_auth_forward")


class ForwardAuthLogin:
    """Handle authentication via forward-auth endpoint (bypasses Keycloak)."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
    ):
        """Initialize forward-auth login.

        Args:
            base_url: Base URL of Elitea (e.g. https://dev.elitea.ai)
            username: Login username
            password: Login password
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()

    def login(self) -> dict[str, str]:
        """Perform login via forward-auth and return cookies.

        Returns:
            Dictionary of cookie name -> value for authenticated session.

        Raises:
            RuntimeError: If login fails.
        """
        logger.info("Starting forward-auth login for %s", self.username)

        try:
            # Step 1: GET the login form (not strictly necessary but good practice)
            login_form_url = f"{self.base_url}/forward-auth/auth_form/login"
            logger.debug("Step 1: GET %s", login_form_url)

            resp = self.session.get(login_form_url, timeout=10)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to load login form: {resp.status_code}")

            # Step 2: POST credentials to authorize endpoint
            authorize_url = f"{self.base_url}/forward-auth/auth_form/authorize"
            logger.debug("Step 2: POST credentials to %s", authorize_url)

            login_data = {
                'login': self.username,  # Field name is 'login' not 'username'
                'password': self.password,
                'target': '/',  # Where to redirect after auth
            }

            resp = self.session.post(
                authorize_url,
                data=login_data,
                allow_redirects=True,
                timeout=10
            )

            # Step 3: Verify we're back at main app (not still on auth page)
            if resp.status_code != 200:
                raise RuntimeError(f"Login POST failed: {resp.status_code}")

            if "auth_form" in resp.url or "login" in resp.url.lower():
                logger.error("Login failed - still on auth page: %s", resp.url)
                raise RuntimeError(f"Login failed: {resp.status_code} {resp.url}")

            logger.info("Login successful - redirected to %s", resp.url)

            # Step 4: Extract cookies
            cookies = self._extract_cookies()
            logger.info("Extracted %d cookies", len(cookies))

            # Verify we got the auth cookie
            if "centry_auth_session" not in cookies:
                logger.warning("Missing centry_auth_session cookie")
                logger.debug("Available cookies: %s", list(cookies.keys()))

            return cookies

        except Exception as e:
            logger.exception("Forward-auth login failed")
            raise RuntimeError(f"Login failed: {e}") from e

    def _extract_cookies(self) -> dict[str, str]:
        """Extract all cookies from the session.

        Returns:
            Dictionary of cookie name -> value
        """
        cookies = {}
        for cookie in self.session.cookies:
            cookies[cookie.name] = cookie.value
            logger.debug("Cookie: %s=%s... (domain=%s)",
                         cookie.name, cookie.value[:20], cookie.domain)

        return cookies

    def get_playwright_cookies(self) -> list[dict]:
        """Convert requests cookies to Playwright format.

        Returns:
            List of cookie dicts for use with Playwright BrowserContext.
        """
        pw_cookies = []
        for cookie in self.session.cookies:
            pw_cookies.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain or self.base_url,
                "path": cookie.path or "/",
                "expires": cookie.expires or -1,
                "httpOnly": bool(cookie._rest.get("HttpOnly")),
                "secure": cookie.secure,
                "sameSite": cookie._rest.get("SameSite", "Lax"),
            })
        return pw_cookies


def get_auth_cookies_forward(
    base_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> dict[str, str]:
    """Convenience function to get auth cookies via forward-auth login.

    Reads from environment variables if parameters not provided:
    - ELITEA_URL (or defaults to https://dev.elitea.ai)
    - TEST_USER_EMAIL
    - TEST_USER_PASSWORD

    Args:
        base_url: Base URL of Elitea
        username: Login username (field is 'login' in the form)
        password: Login password

    Returns:
        Dictionary of cookie name -> value

    Example:
        >>> cookies = get_auth_cookies_forward()
        >>> print(cookies.keys())
        dict_keys(['centry_auth_session', ...])
    """
    base_url = base_url or settings.elitea_url
    username = username or settings.test_user_email
    password = password or settings.test_user_password

    if not username or not password:
        raise ValueError(
            "Username and password required. "
            "Set TEST_USER_EMAIL and TEST_USER_PASSWORD environment variables."
        )

    auth = ForwardAuthLogin(base_url, username, password)
    return auth.login()


def get_playwright_storage_state_forward(
    base_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> dict:
    """Get Playwright storage state via forward-auth login.

    This can be used directly with browser.new_context(storage_state=...)
    without opening a browser for login.

    Args:
        base_url: Base URL of Elitea
        username: Login username
        password: Login password

    Returns:
        Playwright storage state dict with cookies

    Example:
        >>> from playwright.sync_api import sync_playwright
        >>> from api_auth_forward import get_playwright_storage_state_forward
        >>>
        >>> storage_state = get_playwright_storage_state_forward()
        >>> with sync_playwright() as p:
        ...     browser = p.chromium.launch()
        ...     context = browser.new_context(storage_state=storage_state)
        ...     page = context.new_page()
        ...     page.goto("https://dev.elitea.ai")  # Already logged in!
    """
    base_url = base_url or settings.elitea_url
    username = username or settings.test_user_email
    password = password or settings.test_user_password

    auth = ForwardAuthLogin(base_url, username, password)
    auth.login()

    # Include localStorage with project ID - the frontend reads this to construct
    # API URLs. Without it, toolkit list calls are made without project_id → 404.
    # Key names from EliteaUI/src/common/constants.js
    project_id = settings.elitea_project_id
    origin = base_url.rstrip("/")

    return {
        "cookies": auth.get_playwright_cookies(),
        "origins": [
            {
                "origin": origin,
                "localStorage": [
                    {"name": "elitea_ui.project.id", "value": str(project_id)},
                    {"name": "elitea_ui.project.name", "value": "Private"},
                ],
            }
        ],
    }


if __name__ == "__main__":
    # Test the forward-auth authentication
    logging.basicConfig(level=logging.DEBUG)

    print("Testing forward-auth based authentication...")
    try:
        cookies = get_auth_cookies_forward()
        print(f"\n[OK] Login successful! Got {len(cookies)} cookies:")
        for name in cookies:
            print(f"  - {name}")

        # Test with Playwright
        print("\nTesting with Playwright...")
        from playwright.sync_api import sync_playwright

        storage_state = get_playwright_storage_state_forward()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state=storage_state)
            page = context.new_page()

            page.goto(settings.elitea_url)
            page.wait_for_load_state("networkidle", timeout=15000)

            if "login" not in page.url and "auth" not in page.url:
                print("[OK] Playwright test passed - already authenticated!")
            else:
                print("[FAIL] Playwright test failed - still on login page")

            browser.close()

    except Exception as e:
        print(f"\n[FAIL] Login failed: {e}")
        import traceback
        traceback.print_exc()
