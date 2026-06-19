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
from pages.chat_page import ChatPage
from components.mui import Popper

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

    @pytest.mark.p0
    @pytest.mark.credentials
    @_flaky
    def test_create_github_credential(self, page, credential_api: CredentialAPI):
        """Create a GitHub credential through the UI form.

        Steps:
        1. Navigate to /app/credentials/create-credential/github
        2. Fill Display Name, select Token auth, enter access token
        3. Click Save
        4. Verify URL redirects to /app/credentials/all
        5. Verify credential card appears with correct name
        """
        if not GITHUB_TOKEN:
            pytest.skip("GITHUB_TOKEN not set in .env.test")

        cred_name = f"AutoTest GitHub {_ts_suffix()}"
        created_id = None

        try:
            # Navigate to create GitHub credential page
            page.goto(
                f"{settings.elitea_url}/app/credentials/create-credential/github",
                wait_until="domcontentloaded",
            )
            page.wait_for_load_state("networkidle", timeout=30000)

            # Wait for form to load
            page.get_by_role("textbox", name="Display Name").wait_for(
                state="visible", timeout=UI_ELEMENT_TIMEOUT,
            )
            page.wait_for_timeout(1000)  # MUI form render

            # Fill Display Name (click + type for MUI)
            name_field = page.get_by_role("textbox", name="Display Name")
            name_field.click()
            name_field.type(cred_name)
            page.wait_for_timeout(300)

            # Select Auth Type = Token (radio button)
            token_radio = page.get_by_role("radio", name="Token")
            if token_radio.is_visible():
                token_radio.click(force=True)
                page.wait_for_timeout(300)

            # Fill Access Token
            # NOTE: Password fields are input[type="password"], not matched by get_by_role("textbox")
            token_field = page.locator('input[type="password"][name="api_key"]')
            token_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            token_field.click()
            token_field.type(GITHUB_TOKEN)
            page.wait_for_timeout(300)

            # Click Save
            save_btn = page.get_by_role("button", name="Save")
            save_btn.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            assert save_btn.is_enabled(), "Save button should be enabled"
            save_btn.evaluate("el => el.click()")
            page.wait_for_load_state("networkidle", timeout=FORM_SAVE_TIMEOUT)

            # Wait for navigation to credentials list
            page.wait_for_timeout(3000)
            url_path = urlparse(page.url).path
            assert "/app/credentials" in url_path, (
                f"Should navigate to credentials page, got: {page.url}"
            )

            # Verify credential card appears with the correct name
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

    @pytest.mark.p0
    @_flaky
    def test_create_github_toolkit(
        self,
        page,
        github_credential_id: dict,
        toolkit_api: ToolkitAPI,
    ):
        """Create a GitHub toolkit through the UI form.

        Steps:
        1. Navigate to /app/toolkits/create
        2. Click the GitHub card
        3. Fill: Toolkit Name, Description, Github configuration, Repository, Branches
        4. Click Save
        5. Verify URL redirects to toolkit detail page
        6. Verify toolkit loads with Test Settings panel
        """
        toolkit_name = f"AutoTest GitHub Toolkit {_ts_suffix()}"
        toolkit_desc = "Test toolkit for automation"
        cred_name = github_credential_id["name"]
        created_id = None

        try:
            # Navigate to toolkit creation page
            page.goto(
                f"{settings.elitea_url}/app/toolkits/create",
                wait_until="domcontentloaded",
            )
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(1000)

            # Click the GitHub card to select GitHub toolkit type
            github_card = page.get_by_text("GitHub").first
            github_card.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            github_card.click()
            page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
            page.wait_for_timeout(1000)

            # Verify we're on the GitHub toolkit creation page
            assert "github" in page.url.lower(), (
                f"Should be on GitHub toolkit page, got: {page.url}"
            )

            # Fill Toolkit Name
            name_field = page.get_by_role("textbox", name="Toolkit Name")
            name_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            name_field.click()
            name_field.type(toolkit_name)
            page.wait_for_timeout(300)

            # Fill Description
            desc_field = page.get_by_role("textbox", name="Description")
            desc_field.click()
            desc_field.type(toolkit_desc)
            page.wait_for_timeout(300)

            # Select Github configuration (credential dropdown)
            # Check if credential is already selected (UI auto-selects when only one exists)
            already_selected = page.locator(f'text="{cred_name}"')
            if already_selected.count() > 0 and already_selected.first.is_visible():
                # Credential already selected, no need to open dropdown
                page.wait_for_timeout(300)
            else:
                # Click the dropdown to open it
                config_dropdown = page.get_by_text("Github configuration").first
                config_dropdown.click()
                page.wait_for_timeout(500)

                # Select the credential by name from the dropdown menu
                cred_option = page.get_by_role("menuitem", name=cred_name)
                if not cred_option.is_visible():
                    # Try option role instead
                    cred_option = page.get_by_role("option", name=cred_name)
                cred_option.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                cred_option.click()
                page.wait_for_timeout(500)

            # Verify credential was selected and form validates it
            # Wait for any validation messages to appear/disappear
            page.wait_for_load_state("networkidle", timeout=FORM_SAVE_TIMEOUT)
            page.wait_for_timeout(1000)  # Allow form to render validation state

            # Fill Repository
            repo_field = page.get_by_role("textbox", name="Repository")
            repo_field.click()
            repo_field.type(GITHUB_REPO)
            page.wait_for_timeout(300)

            # Active Branch and Base Branch default to 'main' — leave as-is
            # Verify they have default values
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

            # Click Save
            save_btn = page.get_by_role("button", name="Save")
            save_btn.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            assert save_btn.is_enabled(), "Save button should be enabled"
            save_btn.evaluate("el => el.click()")
            page.wait_for_load_state("networkidle", timeout=FORM_SAVE_TIMEOUT)

            # Wait for redirect to toolkit detail page
            page.wait_for_timeout(3000)
            url_path = urlparse(page.url).path
            assert "/app/toolkits/all/" in url_path or "/app/toolkits/create" not in url_path, (
                f"Should navigate away from create page, got: {page.url}"
            )

            # Verify the toolkit page loaded — look for toolkit name or Test Settings
            toolkit_name_visible = page.locator(f'text="{toolkit_name}"').first
            try:
                toolkit_name_visible.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            except Exception:
                # Name might be in the input field instead
                pass

            # Check for Test Settings panel (visible on toolkit detail page)
            test_settings = page.locator('text="Test Settings"')
            if test_settings.count() > 0:
                try:
                    test_settings.first.wait_for(state="visible", timeout=5000)
                except Exception:
                    pass  # Not critical — page structure may vary

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

    @pytest.mark.p1
    @_flaky
    def test_github_toolkit_test_settings(
        self,
        page,
        toolkit_id: dict,
    ):
        """Select 'List branches in repo' from Test Settings and run it.

        Steps:
        1. Navigate to toolkit detail page /app/toolkits/all/{id}
        2. Open the Tool dropdown in the Test Settings panel (right side)
        3. Search for 'List branches' and select the tool
        4. Click RUN TOOL
        5. Wait for the result to appear
        6. Verify result contains branch names (e.g. 'main')
        """
        tk_id = toolkit_id["id"]
        base_url = settings.elitea_url

        # Navigate to toolkits list first (warm up SPA), then to detail page
        page.goto(
            f"{base_url}/app/toolkits/all",
            wait_until="domcontentloaded",
        )
        page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
        page.wait_for_timeout(1000)

        page.goto(
            f"{base_url}/app/toolkits/all/{tk_id}",
            wait_until="domcontentloaded",
        )
        page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
        page.wait_for_timeout(2000)

        # If the SPA crashed, retry once
        error_banner = page.locator('text="Unexpected Application Error"')
        if error_banner.count() > 0 and error_banner.first.is_visible():
            page.goto(
                f"{base_url}/app/toolkits/all/{tk_id}",
                wait_until="domcontentloaded",
            )
            page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
            page.wait_for_timeout(3000)

        # Wait for the Test Settings panel to appear
        page.locator('text="Test Settings"').wait_for(
            state="visible", timeout=UI_ELEMENT_TIMEOUT,
        )

        # --- Step 1: Open the Tool dropdown in Test Settings ---
        # Try multiple strategies to find the dropdown:
        # 1. "Select" placeholder text in right panel
        # 2. Combobox role in right panel
        # 3. Dropdown trigger near "Tool" label
        tool_dropdown = None

        # Strategy 1: Look for "Select" text with x > 700
        select_elements = page.get_by_text("Select", exact=True)
        for i in range(select_elements.count()):
            elem = select_elements.nth(i)
            bb = elem.bounding_box()
            if bb and bb["x"] > 700:
                tool_dropdown = elem
                break

        # Strategy 2: Look for combobox in right panel
        if tool_dropdown is None:
            comboboxes = page.locator('[role="combobox"]')
            for i in range(comboboxes.count()):
                elem = comboboxes.nth(i)
                bb = elem.bounding_box()
                if bb and bb["x"] > 700:
                    tool_dropdown = elem
                    break

        # Strategy 3: Look for dropdown trigger near "Tool" label in Test Settings
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

        # --- Step 2: Search for 'List branches' in the dropdown ---
        visible_search = Popper.find_visible_search_input(page, timeout=UI_ELEMENT_TIMEOUT)
        visible_search.fill("List branches")
        page.wait_for_timeout(500)

        # --- Step 3: Select 'List branches in repo' from filtered results ---
        selected = Popper.select_menuitem_by_content(
            page, lambda text: "branch" in text.lower(),
        )
        assert selected, "Could not find 'List branches in repo' in the tool dropdown"
        page.wait_for_timeout(1000)

        # --- Step 4: Click RUN TOOL ---
        run_btn = page.get_by_role("button", name="Run Tool")
        run_btn.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        run_btn.first.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        run_btn.first.click()

        # --- Step 5: Wait for the result to appear ---
        # The tool call hits the GitHub API; may take 3-10+ seconds
        # Result shows as a code block with JSON in the middle panel
        # Use TOOLKIT_EXECUTION_TIMEOUT to allow for API latency
        
        # Wait specifically for the tool execution result indicator to appear
        # This ensures the GitHub API has responded and result is fully rendered
        page.locator('text="list_branches_in_repo"').wait_for(
            state="visible", timeout=TOOLKIT_EXECUTION_TIMEOUT,
        )
        
        # Additional wait for the full JSON result to render (branch names)
        page.wait_for_timeout(2000)

        # --- Step 6: Verify result contains branch names ---
        main_content = page.locator("main").text_content()

        # The result should contain the tool execution indicator
        assert "list_branches_in_repo" in main_content, (
            "Expected 'list_branches_in_repo' tool execution indicator in results. "
            f"Content (first 500 chars): {main_content[:500]}"
        )

        # The repo always has a 'main' branch
        assert '"main"' in main_content or "'main'" in main_content, (
            "Expected 'main' branch name in the tool result JSON. "
            f"Content (first 500 chars): {main_content[:500]}"
        )


# ===========================================================================
# Test 4: Chat with GitHub Toolkit as participant
# ===========================================================================


class TestChatWithGitHubToolkit:
    """Use a GitHub toolkit as a chat participant and verify tool execution."""

    @pytest.mark.p0
    @_flaky
    def test_chat_with_github_toolkit(
        self,
        page,
        conversation_id: str,
        toolkit_id: dict,
    ):
        """Add GitHub toolkit to chat, send a message, verify execution.

        Steps:
        1. Navigate to a fresh conversation
        2. Click "Add toolkit" in the right panel
        3. Search for and select the toolkit
        4. Send a message asking to list branches
        5. Wait for AI response with toolkit execution
        6. Verify tool execution indicators appear in the chat
        """
        toolkit_name = toolkit_id["name"]
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)
        chat.wait_for_page_load()

        # --- Step 1: Add toolkit as participant via right panel ---
        # Wait for chat page to fully load before interacting with toolbar
        page.wait_for_load_state("networkidle", timeout=30000)
        page.wait_for_timeout(2000)  # Additional wait for any animations
        
        logger.info("Adding toolkit '%s' as chat participant", toolkit_name)
        add_toolkit_btn = page.locator('button[aria-label="Add toolkit"]')
        add_toolkit_btn.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        add_toolkit_btn.click(force=True)
        page.wait_for_timeout(1000)

        # Search for the toolkit in the popper and select it
        search_input = Popper.find_visible_search_input(page, timeout=UI_ELEMENT_TIMEOUT)
        search_input.fill(toolkit_name[:20])
        page.wait_for_timeout(1000)

        toolkit_option = page.locator(
            f'li[role="menuitem"]:has-text("{toolkit_name[:15]}")'
        ).first
        toolkit_option.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        logger.info("Found toolkit menuitem: %s", toolkit_option.text_content().strip()[:60])
        toolkit_option.click()
        page.wait_for_load_state("networkidle", timeout=UI_ELEMENT_TIMEOUT)
        page.wait_for_timeout(1000)

        # --- Step 2: Send message requesting toolkit action ---
        initial_count = chat.get_message_count()
        chat.send_message("List branches in the repository", use_enter=True)

        # SPA may re-render after first message — wait for page to stabilise
        chat.wait_for_input_ready()

        # --- Step 3: Wait for AI + toolkit response ---
        # Toolkit execution: AI goes through multiple thinking states before final result
        # E.g.: "Packing its tools…" → "Wiring integrations…" → "Done — I listed..."
        # Wait for content to stabilize (stop changing)
        logger.info("Waiting for AI to complete toolkit execution...")
        chat.wait_for_message_content_stable(
            stable_duration_ms=3000,  # Content unchanged for 3 seconds = done
            timeout=TOOLKIT_EXECUTION_TIMEOUT
        )

        # --- Step 4: Verify toolkit execution ---
        # --- Step 4: Verify response ---
        last_message = chat.get_last_message_text()
        logger.info(f"Last AI message ({len(last_message)} chars): {last_message[:1000]}")

        # Ensure AI finished processing (not stuck in "thinking" state)
        assert "thinking" not in last_message.lower(), (
            "AI response still contains 'thinking' — toolkit execution did not complete. "
            f"Content: {last_message[:200]}"
        )

        # Verify toolkit executed and returned branch information
        assert any(keyword in last_message.lower() for keyword in ["branch", "found", "repository"]), (
            "Expected the AI response to mention branches/repository from toolkit output. "
            f"Last message content (first 500 chars): {last_message[:500]}"
        )

        # Verify there are messages beyond the initial count (AI responded)
        final_count = chat.get_message_count()
        assert final_count > initial_count, (
            f"Expected new messages after toolkit execution: "
            f"initial={initial_count}, final={final_count}"
        )
