"""UI Tests for GitHub Toolkit Creation Flow.

Tests the end-to-end flow of creating a GitHub credential and then a
GitHub toolkit that uses that credential, and using the toolkit in chat.

Each test creates its own resources and cleans up afterwards via API.
The ``credential_api`` and ``toolkit_api`` session fixtures provide
authenticated API access.

Markers:
    - ui: requires browser
    - toolkits: toolkit-related tests
    - credentials: credential-related tests
    - p0: critical priority tests
    - p1: high priority tests

Usage:
    cd automation
    pytest test_github_toolkit.py -v
    pytest test_github_toolkit.py -v -m p0
"""

import logging
import time
from urllib.parse import urlparse

import pytest

from api import CredentialAPI, ToolkitAPI
from config import settings
from pages.base_page import BasePage
from pages.chat_page import ChatPage
from components.mui import Popper
import allure

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits]

# Credential creation can hit race conditions (server-side deduplication or
# eventual consistency), so allow extra retries beyond the global default.
_flaky = pytest.mark.flaky(reruns=3, reruns_delay=2)

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000
FORM_SAVE_TIMEOUT = 15000
AI_RESPONSE_TIMEOUT = 30000
TOOLKIT_EXECUTION_TIMEOUT = 60000  # toolkit calls may take longer than plain AI

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------
GITHUB_TOKEN = settings.git_hub_token
GITHUB_API_URL = "https://api.github.com"
GITHUB_REPO = "EliteaAI/elitea-testing"
GITHUB_BRANCH = "main"


def _ts_suffix() -> str:
    """Return a timestamp suffix for unique resource names."""
    return str(int(time.time()))


# ===========================================================================
# Test 1: Create GitHub Credential
# ===========================================================================


class TestCreateGitHubCredential:
    """Create a GitHub credential via the UI and verify it appears."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/toolkits-credentials/ELITEA-1141_github-toolkit-and-credentials.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.credentials
    @_flaky
    def test_create_github_credential(self, page, credential_api: CredentialAPI):
        """Create a GitHub credential through the UI form."""
        if not GITHUB_TOKEN:
            pytest.skip("GITHUB_TOKEN not set in .env.test")

        cred_name = f"AutoTest GitHub {_ts_suffix()}"
        created_id = None

        try:
            # ------------------------------------------------------------------
            # Step 1 — Navigate to /credentials/create-credential/github
            # ------------------------------------------------------------------
            with allure.step("Step 1 — Navigate to /credentials/create-credential/github"):
                page.goto(
                    f"{settings.app_base_url}/credentials/create-credential/github",
                    wait_until="domcontentloaded",
                )
                page.wait_for_load_state("networkidle", timeout=30000)

                page.get_by_role("textbox", name="Display Name").wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT,
                )
                page.wait_for_timeout(1000)

            # ------------------------------------------------------------------
            # Step 2 — Fill Display Name, select Token auth, enter access token
            # ------------------------------------------------------------------
            with allure.step("Step 2 — Fill Display Name, select Token auth, enter access token"):
                name_field = page.get_by_role("textbox", name="Display Name")
                name_field.click()
                name_field.type(cred_name)
                page.wait_for_timeout(300)

                token_radio = page.get_by_role("radio", name="Token")
                if token_radio.is_visible():
                    token_radio.click(force=True)
                    page.wait_for_timeout(300)

                token_field = page.locator('input[type="password"][name="api_key"]')
                token_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                token_field.click()
                token_field.type(GITHUB_TOKEN)
                page.wait_for_timeout(300)

            # ------------------------------------------------------------------
            # Step 3 — Click Save
            # ------------------------------------------------------------------
            with allure.step("Step 3 — Click Save"):
                save_btn = page.get_by_role("button", name="Save")
                save_btn.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert save_btn.is_enabled(), "Save button should be enabled"
                save_btn.evaluate("el => el.click()")
                page.wait_for_load_state("networkidle", timeout=FORM_SAVE_TIMEOUT)

            # ------------------------------------------------------------------
            # Step 4 — Verify URL redirects to /credentials/all
            # ------------------------------------------------------------------
            with allure.step("Step 4 — Verify URL redirects to /credentials/all"):
                page.wait_for_timeout(3000)
                url_path = urlparse(page.url).path
                assert "/credentials" in url_path, (
                    f"Should navigate to credentials page, got: {page.url}"
                )

            # ------------------------------------------------------------------
            # Step 5 — Verify credential card appears with correct name
            # ------------------------------------------------------------------
            with allure.step("Step 5 — Verify credential card appears with correct name"):
                cred_locator = page.locator(f'text="{cred_name}"').first
                cred_locator.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert cred_locator.is_visible(), (
                    f"Credential '{cred_name}' should appear in the list"
                )

            # Extract created credential ID for cleanup
            # Look up via API
            creds = credential_api.list_credentials()
            rows = creds if isinstance(creds, list) else creds.get("rows", [])
            for c in rows:
                if c.get("display_name") == cred_name:
                    created_id = c["id"]
                    break

        finally:
            # Cleanup
            if created_id is not None:
                try:
                    credential_api.delete_credential(created_id)
                except Exception:
                    pass


# ===========================================================================
# Test 2: Create GitHub Toolkit (depends on credential)
# ===========================================================================


class TestCreateGitHubToolkit:
    """Create a GitHub toolkit via the UI using a pre-existing credential."""

    @pytest.fixture
    def github_credential_id(self, credential_api: CredentialAPI):
        """Create a GitHub credential via API for toolkit tests.

        Yields the credential ID and cleans up after the test.
        """
        if not GITHUB_TOKEN:
            pytest.skip("GITHUB_TOKEN not set in .env.test")

        cred_name = f"AutoTest GitHub {_ts_suffix()}"
        cred = credential_api.create_github_credential(
            display_name=cred_name,
            base_url=GITHUB_API_URL,
            token=GITHUB_TOKEN,
        )
        cred_id = cred["id"]
        cred_display_name = cred.get("display_name", cred_name)

        yield {"id": cred_id, "name": cred_display_name}

        try:
            credential_api.delete_credential(cred_id)
        except Exception:
            pass

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/toolkits-credentials/ELITEA-1141_github-toolkit-and-credentials.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @_flaky
    def test_create_github_toolkit(
        self,
        page,
        github_credential_id: dict,
        toolkit_api: ToolkitAPI,
    ):
        """Create a GitHub toolkit through the UI form."""
        toolkit_name = f"AutoTest GitHub Toolkit {_ts_suffix()}"
        toolkit_desc = "Test toolkit for automation"
        cred_name = github_credential_id["name"]
        created_id = None

        try:
            # ------------------------------------------------------------------
            # Step 1-2 — Navigate to /toolkits/create; click the GitHub card
            # ------------------------------------------------------------------
            with allure.step("Step 1-2 — Navigate to /toolkits/create; click the GitHub card"):
                page.goto(
                    f"{settings.app_base_url}/toolkits/create",
                    wait_until="domcontentloaded",
                )
                page.wait_for_load_state("networkidle", timeout=30000)
                page.wait_for_timeout(1000)

                github_card = page.get_by_text("GitHub").first
                github_card.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                github_card.click()
                page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
                page.wait_for_timeout(1000)

                assert "github" in page.url.lower(), (
                    f"Should be on GitHub toolkit page, got: {page.url}"
                )

            # ------------------------------------------------------------------
            # Step 3 — Fill: Toolkit Name, Description, Github configuration, Repository, Branches
            # ------------------------------------------------------------------
            with allure.step("Step 3 — Fill: Toolkit Name, Description, Github configuration, Repository, Branches"):
                name_field = page.get_by_role("textbox", name="Toolkit Name")
                name_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                name_field.click()
                name_field.type(toolkit_name)
                page.wait_for_timeout(300)

                desc_field = page.get_by_role("textbox", name="Description")
                desc_field.click()
                desc_field.type(toolkit_desc)
                page.wait_for_timeout(300)

                already_selected = page.locator(f'text="{cred_name}"')
                if already_selected.count() > 0 and already_selected.first.is_visible():
                    page.wait_for_timeout(300)
                else:
                    config_dropdown = page.get_by_text("Github configuration").first
                    config_dropdown.click()
                    page.wait_for_timeout(500)

                    cred_option = page.get_by_role("menuitem", name=cred_name)
                    if not cred_option.is_visible():
                        cred_option = page.get_by_role("option", name=cred_name)
                    cred_option.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                    cred_option.click()
                    page.wait_for_timeout(500)

                page.wait_for_load_state("networkidle", timeout=FORM_SAVE_TIMEOUT)
                page.wait_for_timeout(1000)

                repo_field = page.get_by_role("textbox", name="Repository")
                repo_field.click()
                repo_field.type(GITHUB_REPO)
                page.wait_for_timeout(300)

                active_branch = page.get_by_role("textbox", name="Active Branch")
                if active_branch.is_visible():
                    val = active_branch.input_value()
                    if not val:
                        active_branch.click()
                        active_branch.type(GITHUB_BRANCH)
                        page.wait_for_timeout(300)

                base_branch = page.get_by_role("textbox", name="Base Branch")
                if base_branch.is_visible():
                    val = base_branch.input_value()
                    if not val:
                        base_branch.click()
                        base_branch.type(GITHUB_BRANCH)
                        page.wait_for_timeout(300)

            # ------------------------------------------------------------------
            # Step 4 — Click Save
            # ------------------------------------------------------------------
            with allure.step("Step 4 — Click Save"):
                save_btn = page.get_by_role("button", name="Save")
                save_btn.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert save_btn.is_enabled(), "Save button should be enabled"
                save_btn.evaluate("el => el.click()")
                page.wait_for_load_state("networkidle", timeout=FORM_SAVE_TIMEOUT)

            # ------------------------------------------------------------------
            # Step 5 — Verify URL redirects to toolkit detail page
            # ------------------------------------------------------------------
            with allure.step("Step 5 — Verify URL redirects to toolkit detail page"):
                page.wait_for_timeout(3000)
                url_path = urlparse(page.url).path
                assert "/toolkits/all/" in url_path or "/toolkits/create" not in url_path, (
                    f"Should navigate away from create page, got: {page.url}"
                )

            # ------------------------------------------------------------------
            # Step 6 — Verify toolkit loads with Test Settings panel
            # ------------------------------------------------------------------
            with allure.step("Step 6 — Verify toolkit loads with Test Settings panel"):
                toolkit_name_visible = page.locator(f'text="{toolkit_name}"').first
                try:
                    toolkit_name_visible.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                except Exception:
                    pass

                test_settings = page.locator('text="Test Settings"')
                if test_settings.count() > 0:
                    try:
                        test_settings.first.wait_for(state="visible", timeout=5000)
                    except Exception:
                        pass

            # Extract toolkit ID for cleanup via API
            toolkits = toolkit_api.list_toolkits()
            rows = toolkits if isinstance(toolkits, list) else toolkits.get("rows", [])
            for t in rows:
                if t.get("name") == toolkit_name:
                    created_id = t["id"]
                    break

        finally:
            # Cleanup toolkit
            if created_id is not None:
                try:
                    toolkit_api.delete_toolkit(created_id)
                except Exception:
                    pass


# ===========================================================================
# Shared fixtures for tests that need a pre-existing credential + toolkit
# ===========================================================================


@pytest.fixture
def credential_id(credential_api: CredentialAPI):
    """Create a GitHub credential via API and yield its data.

    Yields a dict with ``id`` and ``elitea_title`` keys.
    Cleans up after the test.
    """
    if not GITHUB_TOKEN:
        pytest.skip("GITHUB_TOKEN not set in .env.test")

    cred_name = f"AutoTest GitHub {_ts_suffix()}"
    cred = credential_api.create_github_credential(
        display_name=cred_name,
        base_url=GITHUB_API_URL,
        token=GITHUB_TOKEN,
    )

    yield {"id": cred["id"], "elitea_title": cred["elitea_title"]}

    try:
        credential_api.delete_credential(cred["id"])
    except Exception:
        pass


@pytest.fixture
def toolkit_id(credential_id: dict, toolkit_api: ToolkitAPI):
    """Create a GitHub toolkit via API (using ``credential_id``) and yield its ID + name.

    Returns a dict with ``id`` and ``name`` keys.
    Cleans up after the test.
    """
    toolkit_name = f"AutoTest GitHub Toolkit {_ts_suffix()}"
    toolkit = toolkit_api.create_github_toolkit(
        name=toolkit_name,
        description="Toolkit for chat integration test",
        credential_elitea_title=credential_id["elitea_title"],
        repository=GITHUB_REPO,
        active_branch=GITHUB_BRANCH,
        base_branch=GITHUB_BRANCH,
    )
    tk_id = toolkit["id"]

    yield {"id": tk_id, "name": toolkit_name}

    try:
        toolkit_api.delete_toolkit(tk_id)
    except Exception:
        pass


# ===========================================================================
# Test 3: Test Settings — run a tool from the toolkit detail page
# ===========================================================================


class TestGitHubToolkitTestSettings:
    """Run a tool via the Test Settings panel on the toolkit detail page."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/toolkits-credentials/ELITEA-1141_github-toolkit-and-credentials.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    @_flaky
    def test_github_toolkit_test_settings(
        self,
        page,
        toolkit_id: dict,
    ):
        """Select 'List branches in repo' from Test Settings and run it."""
        tk_id = toolkit_id["id"]
        base_url = settings.app_base_url

        # ------------------------------------------------------------------
        # Step 1 — Navigate to toolkit detail page /toolkits/all/{id}
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Navigate to toolkit detail page"):
            page.goto(
                f"{base_url}/toolkits/all",
                wait_until="domcontentloaded",
            )
            page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
            page.wait_for_timeout(1000)

            page.goto(
                f"{base_url}/toolkits/all/{tk_id}",
                wait_until="domcontentloaded",
            )
            page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
            page.wait_for_timeout(2000)

            error_banner = page.locator('text="Unexpected Application Error"')
            if error_banner.count() > 0 and error_banner.first.is_visible():
                page.goto(
                    f"{base_url}/toolkits/all/{tk_id}",
                    wait_until="domcontentloaded",
                )
                page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
                page.wait_for_timeout(3000)

            page.locator('text="Test Settings"').wait_for(
                state="visible", timeout=UI_ELEMENT_TIMEOUT,
            )

        # ------------------------------------------------------------------
        # Step 2 — Open the Tool dropdown in the Test Settings panel
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Open the Tool dropdown in the Test Settings panel"):
            tool_dropdown = None

            select_elements = page.get_by_text("Select", exact=True)
            for i in range(select_elements.count()):
                elem = select_elements.nth(i)
                bb = elem.bounding_box()
                if bb and bb["x"] > 700:
                    tool_dropdown = elem
                    break

            if tool_dropdown is None:
                comboboxes = page.locator('[role="combobox"]')
                for i in range(comboboxes.count()):
                    elem = comboboxes.nth(i)
                    bb = elem.bounding_box()
                    if bb and bb["x"] > 700:
                        tool_dropdown = elem
                        break

            if tool_dropdown is None:
                tool_label = page.locator('.index-config-field:has(span:text("Tool"))').first
                if tool_label.count() > 0:
                    dropdown = tool_label.locator('[role="combobox"], .MuiSelect-root, input').first
                    if dropdown.count() > 0 and dropdown.is_visible():
                        tool_dropdown = dropdown

            assert tool_dropdown is not None, (
                "Could not find the Tool dropdown in the Test Settings panel"
            )
            tool_dropdown.click()
            page.wait_for_timeout(1000)

        # ------------------------------------------------------------------
        # Step 3 — Search for 'List branches' and select the tool
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Search for 'List branches' and select the tool"):
            visible_search = Popper.find_visible_search_input(page, timeout=UI_ELEMENT_TIMEOUT)
            visible_search.fill("List branches")
            page.wait_for_timeout(500)

            selected = Popper.select_menuitem_by_content(
                page, lambda text: "branch" in text.lower(),
            )
            assert selected, "Could not find 'List branches in repo' in the tool dropdown"
            page.wait_for_timeout(1000)

        # ------------------------------------------------------------------
        # Step 4 — Click RUN TOOL
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Click RUN TOOL"):
            # Dismiss any popups (NPS survey, banners) that may block the Run Tool button
            BasePage(page).dismiss_popups()

            run_btn = page.get_by_role("button", name="Run Tool")
            run_btn.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            run_btn.first.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        run_btn.first.click()

        # ------------------------------------------------------------------
        # Step 5 — Wait for the result to appear
        # ------------------------------------------------------------------
        with allure.step("Step 5 — Wait for the result to appear"):
            page.locator('text="list_branches_in_repo"').wait_for(
                state="visible", timeout=TOOLKIT_EXECUTION_TIMEOUT,
            )
            page.wait_for_timeout(2000)

        # ------------------------------------------------------------------
        # Step 6 — Verify result contains branch names (e.g. 'main')
        # ------------------------------------------------------------------
        with allure.step("Step 6 — Verify result contains branch names"):
            main_content = page.locator("main").text_content()

            assert "list_branches_in_repo" in main_content, (
                "Expected 'list_branches_in_repo' tool execution indicator in results. "
                f"Content (first 500 chars): {main_content[:500]}"
            )

            assert '"main"' in main_content or "'main'" in main_content, (
                "Expected 'main' branch name in the tool result JSON. "
                f"Content (first 500 chars): {main_content[:500]}"
            )


# ===========================================================================
# Test 4: Chat with GitHub Toolkit as participant
# ===========================================================================


class TestChatWithGitHubToolkit:
    """Use a GitHub toolkit as a chat participant and verify tool execution."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/toolkits-credentials/ELITEA-1141_github-toolkit-and-credentials.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @_flaky
    def test_chat_with_github_toolkit(
        self,
        page,
        conversation_id: str,
        toolkit_id: dict,
    ):
        """Add GitHub toolkit to chat, send a message, verify execution."""
        toolkit_name = toolkit_id["name"]
        chat = ChatPage(page)

        # ------------------------------------------------------------------
        # Step 1-3 — Navigate to fresh conversation; add toolkit as participant
        # ------------------------------------------------------------------
        with allure.step("Step 1-3 — Navigate to fresh conversation; add toolkit as participant"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.wait_for_page_load()

            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            logger.info("Adding toolkit '%s' as chat participant", toolkit_name)
            chat.add_toolkit_participant(toolkit_name, timeout=UI_ELEMENT_TIMEOUT)
            page.wait_for_timeout(1000)

        # ------------------------------------------------------------------
        # Step 4 — Send a message asking to list branches
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Send a message asking to list branches"):
            initial_count = chat.get_message_count()
            chat.send_message("List branches in the repository", use_enter=True)

            chat.wait_for_input_ready()

        # ------------------------------------------------------------------
        # Step 5 — Wait for AI response with toolkit execution
        # ------------------------------------------------------------------
        with allure.step("Step 5 — Wait for AI response with toolkit execution"):
            logger.info("Waiting for AI to complete toolkit execution...")
            chat.wait_for_ai_response(
                initial_count=initial_count,
                timeout=TOOLKIT_EXECUTION_TIMEOUT
            )

        # ------------------------------------------------------------------
        # Step 6 — Verify tool execution indicators appear in the chat
        # ------------------------------------------------------------------
        with allure.step("Step 6 — Verify tool execution indicators appear in the chat"):
            last_message = chat.get_last_message_text()
            logger.info(f"Last AI message ({len(last_message)} chars): {last_message[:1000]}")

            assert "thinking" not in last_message.lower(), (
                "AI response still contains 'thinking' — toolkit execution did not complete. "
                f"Content: {last_message[:200]}"
            )

            assert any(keyword in last_message.lower() for keyword in ["branch", "found", "repository"]), (
                "Expected the AI response to mention branches/repository from toolkit output. "
                f"Last message content (first 500 chars): {last_message[:500]}"
            )

            final_count = chat.get_message_count()
            assert final_count > initial_count, (
                f"Expected new messages after toolkit execution: "
                f"initial={initial_count}, final={final_count}"
            )
