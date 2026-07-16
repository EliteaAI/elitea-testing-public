#!/usr/bin/env python3
"""Setup test user tokens and project IDs as GitHub secrets.

This script:
1. Logs in to Elitea as each test user (autotest_user_N)
2. Gets the user's personal project ID
3. Creates a new personal access token (never expires)
4. Stores both as GitHub repository secrets

Usage:
    python setup_test_users.py --env STAGE2 --password "yourpassword" --indexes 1,2,3

Environment variables:
    GITHUB_TOKEN: Required for gh CLI to set secrets

GitHub secrets created:
    TEST_USER_TOKEN_{ENV}_{INDEX}   - Personal access token
    TEST_USER_PROJECT_{ENV}_{INDEX} - Personal project ID
"""

import argparse
import logging
import subprocess
import sys
import time
from typing import Optional

import requests
from urllib.parse import urljoin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

ENV_URLS = {
    "STAGE2": "https://stage2.elitea.ai",
    "STAGE3": "https://stage3.elitea.ai",
    "DEV": "https://dev.elitea.ai",
    "NEXT": "https://next.elitea.ai",
}

USERNAME_TEMPLATE = "autotest_user_{index}"


class EliteaAuth:
    """Handle Elitea authentication and token management."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._logged_in = False

    def login(self) -> bool:
        """Perform Keycloak login via API."""
        logger.info("Logging in as %s to %s", self.username, self.base_url)

        try:
            # Step 1: Initial request to trigger auth redirect
            resp = self.session.get(self.base_url, allow_redirects=True, timeout=30)

            # Step 2: Extract and submit the forward-auth auto-submit form
            form_action, form_data = self._extract_form_data(resp.text)
            if not form_action:
                raise RuntimeError("Could not extract OIDC auth form")

            resp = self.session.post(form_action, data=form_data, allow_redirects=True, timeout=30)

            # Step 3: Extract the login form action URL
            login_endpoint = self._extract_login_form_action(resp.text, resp.url)

            # Step 4: Submit login credentials
            login_data = {
                "username": self.username,
                "password": self.password,
                "credentialId": "",
            }
            logger.debug("Submitting credentials to: %s", login_endpoint)
            resp = self.session.post(login_endpoint, data=login_data, allow_redirects=True, timeout=30)
            logger.debug("Response status: %d, URL: %s", resp.status_code, resp.url)

            # Verify we're logged in
            if "auth" in resp.url.lower() or "login" in resp.url.lower():
                # Try to extract error message from Keycloak page
                error_msg = self._extract_keycloak_error(resp.text)
                if error_msg:
                    logger.error("Keycloak error: %s", error_msg)
                raise RuntimeError(f"Login failed - still on auth page: {resp.url}")

            self._logged_in = True
            logger.info("Login successful")
            return True

        except Exception as e:
            logger.error("Login failed: %s", e)
            return False

    def get_user_info(self) -> dict:
        """Get current user info including personal_project_id."""
        if not self._logged_in:
            raise RuntimeError("Not logged in")

        resp = self.session.get(
            f"{self.base_url}/api/v2/auth/user",
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def create_personal_token(self, name: str) -> dict:
        """Create a new personal access token (never expires).

        Args:
            name: Token name (alphanumeric, underscore, hyphen only)

        Returns:
            dict with 'token' and 'name' keys
        """
        if not self._logged_in:
            raise RuntimeError("Not logged in")

        resp = self.session.post(
            f"{self.base_url}/api/v2/auth/token/",
            json={
                "name": name,
                "expires": None,  # Never expires
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def list_tokens(self) -> list:
        """List existing personal tokens."""
        if not self._logged_in:
            raise RuntimeError("Not logged in")

        resp = self.session.get(
            f"{self.base_url}/api/v2/auth/token/",
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def delete_token(self, token_id: int) -> bool:
        """Delete a personal token by ID."""
        if not self._logged_in:
            raise RuntimeError("Not logged in")

        resp = self.session.delete(
            f"{self.base_url}/api/v2/auth/token/{token_id}/",
            timeout=30,
        )
        return resp.status_code == 200

    def _extract_form_data(self, html: str) -> tuple[Optional[str], dict]:
        """Extract form action and hidden fields from HTML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            form = soup.find("form")
            if not form:
                return None, {}

            action = form.get("action")
            if not action:
                return None, {}

            form_data = {}
            for input_field in form.find_all("input", {"type": "hidden"}):
                name = input_field.get("name")
                value = input_field.get("value", "")
                if name:
                    form_data[name] = value

            return action, form_data
        except ImportError:
            logger.error("BeautifulSoup required: pip install beautifulsoup4")
            return None, {}

    def _extract_keycloak_error(self, html: str) -> Optional[str]:
        """Extract error message from Keycloak login page."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Keycloak shows errors in span with class "kc-feedback-text" or alert
            error_span = soup.find("span", {"class": "kc-feedback-text"})
            if error_span:
                return error_span.get_text(strip=True)

            # Try alert div
            alert = soup.find("div", {"class": lambda x: x and "alert" in x})
            if alert:
                return alert.get_text(strip=True)

            # Try any element with id containing "error"
            error_el = soup.find(id=lambda x: x and "error" in x.lower())
            if error_el:
                return error_el.get_text(strip=True)

            return None
        except Exception:
            return None

    def _extract_login_form_action(self, html: str, fallback_url: str) -> str:
        """Extract the login form POST endpoint from Keycloak HTML."""
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import urlparse

            soup = BeautifulSoup(html, "html.parser")
            form = soup.find("form", {"id": "kc-form-login"})
            if not form:
                form = soup.find("form", {"action": lambda x: x and "login-actions" in x})

            if not form:
                return fallback_url

            action = form.get("action")
            if not action:
                return fallback_url

            if action.startswith("http"):
                return action
            elif action.startswith("/"):
                parsed = urlparse(fallback_url)
                return f"{parsed.scheme}://{parsed.netloc}{action}"
            else:
                return urljoin(fallback_url, action)
        except ImportError:
            return fallback_url


def set_github_secret(name: str, value: str, repo: Optional[str] = None) -> bool:
    """Set a GitHub repository secret using gh CLI.

    Args:
        name: Secret name
        value: Secret value
        repo: Repository in owner/repo format (optional, uses current repo if not set)

    Returns:
        True if successful
    """
    cmd = ["gh", "secret", "set", name]
    if repo:
        cmd.extend(["--repo", repo])

    try:
        # Use stdin to pass value - more reliable for special characters
        result = subprocess.run(
            cmd,
            input=value,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            logger.info("Set secret: %s", name)
            return True
        else:
            logger.error("Failed to set secret %s: %s", name, result.stderr)
            return False
    except subprocess.TimeoutExpired:
        logger.error("Timeout setting secret %s", name)
        return False
    except FileNotFoundError:
        logger.error("gh CLI not found. Install: https://cli.github.com/")
        return False


def setup_user(
    env: str,
    index: str,
    password: str,
    repo: Optional[str] = None,
    dry_run: bool = False,
) -> bool:
    """Setup a single test user: login, get project ID, create token, save to GitHub.

    Args:
        env: Environment name (STAGE2, DEV, etc.)
        index: User index (1, 2, "tst", etc.) - can be numeric or string
        password: User password
        repo: GitHub repository (optional)
        dry_run: If True, don't actually set secrets

    Returns:
        True if successful
    """
    base_url = ENV_URLS.get(env.upper())
    if not base_url:
        logger.error("Unknown environment: %s. Valid: %s", env, list(ENV_URLS.keys()))
        return False

    username = USERNAME_TEMPLATE.format(index=index)
    actual_password = f"{password}{index}"
    token_name = f"automation_{env.lower()}_{index}"

    logger.info("=" * 60)
    logger.info("Setting up user: %s (env=%s, index=%s)", username, env, index)
    logger.info("=" * 60)

    # Login
    auth = EliteaAuth(base_url, username, actual_password)
    if not auth.login():
        return False

    # Get user info with personal_project_id
    try:
        user_info = auth.get_user_info()
        project_id = user_info.get("personal_project_id")
        if not project_id:
            logger.error("User has no personal_project_id")
            return False
        logger.info("Personal project ID: %s", project_id)
    except Exception as e:
        logger.error("Failed to get user info: %s", e)
        return False

    # Check for existing token with same name and delete it
    try:
        existing_tokens = auth.list_tokens()
        for token in existing_tokens:
            if token.get("name") == token_name:
                logger.info("Deleting existing token: %s (id=%s)", token_name, token["id"])
                auth.delete_token(token["id"])
    except Exception as e:
        logger.warning("Could not check existing tokens: %s", e)

    # Create new token
    try:
        token_data = auth.create_personal_token(token_name)
        token_value = token_data.get("token")
        if not token_value:
            logger.error("Token creation returned no token value")
            return False
        logger.info("Created token: %s", token_name)
    except Exception as e:
        logger.error("Failed to create token: %s", e)
        return False

    # Save to GitHub secrets
    token_secret_name = f"TEST_USER_TOKEN_{env.upper()}_{index}"
    project_secret_name = f"TEST_USER_PROJECT_{env.upper()}_{index}"  # "PROJECT" blocked by org policy

    if dry_run:
        logger.info("[DRY RUN] Would set secret: %s = %s...", token_secret_name, token_value[:20])
        logger.info("[DRY RUN] Would set secret: %s = %s", project_secret_name, project_id)
        return True

    success = True
    if not set_github_secret(token_secret_name, token_value, repo):
        success = False
    if not set_github_secret(project_secret_name, str(project_id), repo):
        success = False

    return success


def main():
    parser = argparse.ArgumentParser(
        description="Setup test user tokens and project IDs as GitHub secrets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Setup user 2 on STAGE2
    python setup_test_users.py --env STAGE2 --password "mypassword" --indexes 2

    # Setup users 1,2,4,8 on DEV
    python setup_test_users.py --env DEV --password "mypassword" --indexes 1,2,4,8

    # Dry run (don't actually set secrets)
    python setup_test_users.py --env STAGE2 --password "mypassword" --indexes 1 --dry-run

    # Specify repository explicitly
    python setup_test_users.py --env STAGE2 --password "mypassword" --indexes 1 --repo EliteaAI/elitea-testing-public
        """,
    )
    parser.add_argument(
        "--env",
        required=True,
        help="Environment name (STAGE2, STAGE3, DEV, NEXT)",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Password for test users (same for all)",
    )
    parser.add_argument(
        "--indexes",
        required=True,
        help="Comma-separated user indexes (e.g., 1,2,4,8)",
    )
    parser.add_argument(
        "--repo",
        help="GitHub repository (owner/repo format). Uses current repo if not specified.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually set secrets, just show what would be done",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse indexes (can be numeric or string, e.g., "1,2,tst,4")
    indexes = [i.strip() for i in args.indexes.split(",")]

    # Validate environment
    if args.env.upper() not in ENV_URLS:
        logger.error("Unknown environment: %s. Valid: %s", args.env, list(ENV_URLS.keys()))
        sys.exit(1)

    logger.info("Environment: %s (%s)", args.env.upper(), ENV_URLS[args.env.upper()])
    logger.info("User indexes: %s", indexes)
    if args.dry_run:
        logger.info("DRY RUN MODE - no secrets will be set")

    # Process each user
    results = {}
    for index in indexes:
        success = setup_user(
            env=args.env,
            index=index,
            password=args.password,
            repo=args.repo,
            dry_run=args.dry_run,
        )
        results[index] = success

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    for index, success in results.items():
        status = "OK" if success else "FAILED"
        logger.info("  User %s: %s", index, status)

    failed = [i for i, s in results.items() if not s]
    if failed:
        logger.error("Failed users: %s", failed)
        sys.exit(1)
    else:
        logger.info("All users setup successfully!")


if __name__ == "__main__":
    main()
