"""API-based authentication for Keycloak without browser.

This module provides functions to login via HTTP API calls instead of
opening a browser, making tests faster and more reliable.

Usage:
    from api_auth import get_auth_cookies

    cookies = get_auth_cookies()
    # Use cookies with requests.Session or Playwright
"""

import os
import logging
from typing import Optional
import requests
from urllib.parse import urljoin, parse_qs, urlparse

from config import settings

logger = logging.getLogger("elitea.api_auth")


class KeycloakAPIAuth:
    """Handle Keycloak authentication via API calls."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
    ):
        """Initialize Keycloak API auth.

        Args:
            base_url: Base URL of Elitea (e.g. https://stage.elitea.ai)
            username: Login username
            password: Login password
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()

    def login(self) -> dict[str, str]:
        """Perform login via API and return authentication cookies.

        Returns:
            Dictionary of cookie name -> value for authenticated session.

        Raises:
            RuntimeError: If login fails.
        """
        logger.info("Starting API-based login for %s", self.username)

        try:
            # Step 1: Initial request to trigger auth redirect
            logger.debug("Step 1: GET %s", self.base_url)
            resp = self.session.get(
                self.base_url,
                allow_redirects=True,
                timeout=30
            )

            # If already logged in (no auth redirect), extract cookies
            if "/forward-auth/" not in resp.url and "auth" not in resp.url.lower():
                logger.info("Already authenticated (no redirect to auth)")
                return self._extract_cookies()

            # Step 2: Extract and submit the forward-auth auto-submit form
            logger.debug("Step 2: On forward-auth page: %s", resp.url)
            form_action, form_data = self._extract_form_data(resp.text)

            if not form_action:
                raise RuntimeError("Could not extract OIDC auth form from forward-auth page")

            logger.debug("Step 3: POST OIDC params to %s", form_action)
            resp = self.session.post(
                form_action,
                data=form_data,
                allow_redirects=True,
                timeout=30
            )

            # Step 4: We should now be on Keycloak login page
            # Extract the login form action URL from the HTML
            keycloak_url = resp.url
            logger.debug("Step 4: On Keycloak login page: %s", keycloak_url)

            # Parse the login form to extract action URL
            login_endpoint = self._extract_login_form_action(resp.text, keycloak_url)
            logger.debug("Step 5: Extracted login endpoint: %s", login_endpoint)

            # Step 6: Submit login credentials
            login_data = {
                "username": self.username,
                "password": self.password,
                "credentialId": "",  # Required by Keycloak, empty for password auth
            }

            logger.debug("Step 6: POST credentials to login endpoint")
            resp = self.session.post(
                login_endpoint,
                data=login_data,
                allow_redirects=True,
                timeout=30
            )

            # Step 7: Verify we're back at main app (not still on auth page)
            if "auth" in resp.url.lower() or "login" in resp.url.lower():
                logger.error("Login failed - still on auth page: %s", resp.url)
                logger.error("Response status: %d", resp.status_code)
                raise RuntimeError(f"Login failed: {resp.status_code} {resp.url}")

            logger.info("Login successful - redirected to %s", resp.url)

            # Step 8: Extract cookies
            cookies = self._extract_cookies()
            logger.info("Extracted %d cookies", len(cookies))

            # Verify we got the main auth cookie
            if "elitea-staging_auth_session" not in cookies:
                logger.warning("Missing elitea-staging_auth_session cookie")
                logger.debug("Available cookies: %s", list(cookies.keys()))

            return cookies

        except Exception as e:
            logger.exception("API login failed")
            raise RuntimeError(f"Login failed: {e}") from e

    def _extract_form_data(self, html: str) -> tuple[Optional[str], dict]:
        """Extract form action and all hidden input fields from HTML.

        Args:
            html: The HTML content containing an auto-submit form

        Returns:
            Tuple of (form_action_url, form_data_dict)
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error("BeautifulSoup required for form extraction")
            return None, {}

        try:
            soup = BeautifulSoup(html, "html.parser")

            # Find the first form element
            form = soup.find("form")
            if not form:
                logger.warning("No form found in HTML")
                return None, {}

            action = form.get("action")
            if not action:
                logger.warning("Form has no action attribute")
                return None, {}

            # Extract all hidden input fields
            form_data = {}
            for input_field in form.find_all("input", {"type": "hidden"}):
                name = input_field.get("name")
                value = input_field.get("value", "")
                if name:
                    form_data[name] = value

            logger.debug("Extracted form with %d fields to %s", len(form_data), action)
            return action, form_data

        except Exception as e:
            logger.exception("Failed to parse form: %s", e)
            return None, {}

    def _extract_login_form_action(self, html: str, fallback_url: str) -> str:
        """Extract the login form POST endpoint from Keycloak HTML.

        Args:
            html: The HTML content of the login page
            fallback_url: URL to return if parsing fails

        Returns:
            Full URL to POST credentials to (with query parameters)
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("BeautifulSoup not installed, using fallback URL")
            return fallback_url

        try:
            soup = BeautifulSoup(html, "html.parser")

            # Find the login form - Keycloak uses id="kc-form-login"
            form = soup.find("form", {"id": "kc-form-login"})
            if not form:
                # Fallback: any form with action containing "login-actions"
                form = soup.find("form", {"action": lambda x: x and "login-actions" in x})

            if not form:
                logger.warning("Could not find login form in HTML")
                return fallback_url

            action = form.get("action")
            if not action:
                logger.warning("Form has no action attribute")
                return fallback_url

            # Action might be relative or absolute
            if action.startswith("http"):
                return action
            elif action.startswith("/"):
                # Relative to domain
                parsed = urlparse(fallback_url)
                return f"{parsed.scheme}://{parsed.netloc}{action}"
            else:
                # Relative to current path
                return urljoin(fallback_url, action)

        except Exception as e:
            logger.exception("Failed to parse login form: %s", e)
            return fallback_url

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


def get_auth_cookies(
    base_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> dict[str, str]:
    """Convenience function to get auth cookies via API login.

    Reads from environment variables if parameters not provided:
    - ELITEA_URL (or defaults to https://stage.elitea.ai)
    - TEST_USER_EMAIL
    - TEST_USER_PASSWORD

    Args:
        base_url: Base URL of Elitea
        username: Login username
        password: Login password

    Returns:
        Dictionary of cookie name -> value

    Example:
        >>> cookies = get_auth_cookies()
        >>> print(cookies.keys())
        dict_keys(['elitea-staging_auth_session', ...])
    """
    base_url = base_url or settings.elitea_url
    username = username or settings.test_user_email
    password = password or settings.test_user_password

    if not username or not password:
        raise ValueError(
            "Username and password required. "
            "Set TEST_USER_EMAIL and TEST_USER_PASSWORD environment variables."
        )

    auth = KeycloakAPIAuth(base_url, username, password)
    return auth.login()


def get_playwright_storage_state(
    base_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> dict:
    """Get Playwright storage state via API login.

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
        >>> from api_auth import get_playwright_storage_state
        >>>
        >>> storage_state = get_playwright_storage_state()
        >>> with sync_playwright() as p:
        ...     browser = p.chromium.launch()
        ...     context = browser.new_context(storage_state=storage_state)
        ...     page = context.new_page()
        ...     page.goto("https://stage.elitea.ai")  # Already logged in!
    """
    base_url = base_url or settings.elitea_url
    username = username or settings.test_user_email
    password = password or settings.test_user_password

    auth = KeycloakAPIAuth(base_url, username, password)
    auth.login()

    return {
        "cookies": auth.get_playwright_cookies(),
        "origins": []  # localStorage/sessionStorage not needed
    }


if __name__ == "__main__":
    # Test the API authentication
    logging.basicConfig(level=logging.DEBUG)

    # Load environment variables from .env.test
    from pathlib import Path
    env_file = Path(__file__).parent / ".env.test"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())

    print("Testing API-based authentication...")
    try:
        cookies = get_auth_cookies()
        print(f"\n[OK] Login successful! Got {len(cookies)} cookies:")
        for name in cookies:
            print(f"  - {name}")

        # Test with Playwright
        print("\nTesting with Playwright...")
        from playwright.sync_api import sync_playwright

        storage_state = get_playwright_storage_state()

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
