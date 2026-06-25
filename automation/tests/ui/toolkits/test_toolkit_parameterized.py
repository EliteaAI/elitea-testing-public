"""Parameterized toolkit tests — data-driven across all toolkit types.

Usage:
    # Run all enabled toolkits
    pytest test_toolkit_parameterized.py -v

    # Run only GitHub
    pytest test_toolkit_parameterized.py -v -k "github"

    # Run only Code Repository toolkits
    pytest test_toolkit_parameterized.py -v -k "code_repo"
"""

import logging
import re
import time

import pytest
import requests

from api import CredentialAPI, ToolkitAPI
from config import settings
from components.mui import Popper
from pages.chat_page import ChatPage
from toolkit_configs import TOOLKIT_CONFIGS, ToolkitConfig
from toolkit_factories import CREDENTIAL_FACTORIES, TOOLKIT_SETTINGS_FACTORIES

# Import from conftest
from conftest import ELITEA_URL
import allure

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits]

# Timeout constants (ms)
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000
TOOLKIT_EXECUTION_TIMEOUT = 60_000


def _ts() -> str:
    return str(int(time.time()))


def _enabled_toolkit_ids() -> list[str]:
    """Return toolkit IDs whose env token var is set (i.e., credentials available)."""
    enabled = []
    for tk_id, cfg in TOOLKIT_CONFIGS.items():
        if cfg.skip_reason:
            continue
        token = getattr(settings, cfg.credential.env_token_var.lower(), "")
        if token:
            enabled.append(tk_id)
    return enabled


def _all_toolkit_ids() -> list[str]:
    """Return all toolkit IDs for skip-aware parameterization."""
    return list(TOOLKIT_CONFIGS.keys())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def toolkit_config(request) -> ToolkitConfig:
    """Resolve the ToolkitConfig for the current parameterized test."""
    tk_id = request.param
    cfg = TOOLKIT_CONFIGS[tk_id]

    token = getattr(settings, cfg.credential.env_token_var.lower(), "")
    if not token:
        pytest.skip(
            f"{cfg.credential.env_token_var} not set — "
            f"skipping {cfg.display_name} toolkit tests"
        )
    if cfg.skip_reason:
        pytest.skip(cfg.skip_reason)

    # Pre-validate credentials against the external service
    if cfg.credential_check:
        _validate_credentials(cfg, token)

    return cfg


def _validate_credentials(cfg: ToolkitConfig, token: str):
    """Quick HTTP check to verify credentials are still valid.

    Skips the test with a clear message if the external service
    returns 401/403 (expired/revoked credentials).
    """
    check = cfg.credential_check
    url = check.get("url", "")
    if not url:
        return

    try:
        auth = None
        if check.get("auth_type") == "basic":
            _u_key = check.get("username_env", "")
            username = getattr(settings, _u_key.lower(), "") if _u_key else ""
            _p_key = check.get("password_env", "")
            password = getattr(settings, _p_key.lower(), token) if _p_key else token
            auth = (username, password)

        resp = requests.get(url, auth=auth, timeout=10)
        if resp.status_code in (401, 403):
            pytest.skip(
                f"{cfg.display_name} credentials expired/revoked "
                f"(HTTP {resp.status_code} from {url}) — "
                f"regenerate {cfg.credential.env_token_var}"
            )
    except requests.RequestException as exc:
        logger.warning("Credential pre-check failed for %s: %s", cfg.display_name, exc)


@pytest.fixture
def managed_credential(toolkit_config: ToolkitConfig, credential_api: CredentialAPI):
    """Create a credential via API, yield its data, clean up after."""
    cfg = toolkit_config
    token = getattr(settings, cfg.credential.env_token_var.lower(), "")
    cred_name = f"{cfg.display_name} {_ts()}"

    factory = CREDENTIAL_FACTORIES[cfg.credential.create_payload_fn]
    payload = factory(display_name=cred_name, token=token)

    cred = credential_api.create_credential(payload)
    cred_id = cred["id"]
    elitea_title = cred.get("elitea_title", "")

    yield {"id": cred_id, "elitea_title": elitea_title, "name": cred_name}

    try:
        credential_api.delete_credential(cred_id)
    except Exception:
        pass


@pytest.fixture
def managed_toolkit(
    toolkit_config: ToolkitConfig,
    managed_credential: dict,
    toolkit_api: ToolkitAPI,
):
    """Create a toolkit via API, yield its data, clean up after."""
    cfg = toolkit_config
    tk_name = f"{cfg.display_name} Toolkit {_ts()}"

    settings_factory = TOOLKIT_SETTINGS_FACTORIES[cfg.settings_fn]
    settings_payload = settings_factory(managed_credential["elitea_title"])

    toolkit = toolkit_api.create_toolkit(
        name=tk_name,
        description=f"Auto-created {cfg.display_name} toolkit for testing",
        toolkit_type=cfg.toolkit_type,
        settings=settings_payload["settings"],
    )
    tk_id = toolkit["id"]

    yield {"id": tk_id, "name": tk_name}

    try:
        toolkit_api.delete_toolkit(tk_id)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Test 1: Create Credential via UI
# ---------------------------------------------------------------------------

class TestCreateCredential:
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/toolkits-credentials/ELITEA-1140_google-and-bitbucket-toolkit-crud.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.credentials
    @pytest.mark.parametrize("toolkit_config", _all_toolkit_ids(), indirect=True)
    def test_create_credential(
        self, page, toolkit_config: ToolkitConfig, credential_api: CredentialAPI,
    ):
        """Create a credential through the UI form for any toolkit type."""
        cfg = toolkit_config
        token = getattr(settings, cfg.credential.env_token_var.lower(), "")
        cred_name = f"AutoTest {cfg.display_name} {_ts()}"
        created_id = None

        try:
            base_url = settings.elitea_url

            # Step 1: Navigate to credential creation page
            page.goto(
                f"{base_url}/app/credentials/create-credential",
                wait_until="domcontentloaded",
            )
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(1000)

            # Step 2: Click the credential type card (e.g. "GitHub", "Jira")
            type_card = page.get_by_text(cfg.display_name, exact=True).first
            type_card.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            type_card.click()
            page.wait_for_load_state("networkidle", timeout=30000)

            # Wait for form to fully render after page transition
            name_field = page.get_by_role("textbox", name="Display Name")
            name_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            page.wait_for_timeout(1000)  # MUI form render

            # Fill Display Name — use click+type to trigger React onChange
            name_field.click()
            name_field.type(cred_name)
            page.wait_for_timeout(300)

            # Type-specific auth field filling
            _fill_credential_auth_fields(page, cfg, token)

            # Verify Display Name survived auth field filling
            pre_save_value = name_field.input_value()
            logger.info("Pre-save Display Name: %r (expected %r)", pre_save_value, cred_name)
            page.screenshot(path=f"/tmp/cred_form_presave_{cfg.credential.type}.png")

            # Save
            save_btn = page.get_by_role("button", name="Save")
            save_btn.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            save_btn.evaluate("el => el.click()")
            page.wait_for_load_state("networkidle", timeout=FORM_SAVE_TIMEOUT)
            page.wait_for_timeout(3000)
            
            # Screenshot after save to see result
            page.screenshot(path=f"/tmp/cred_after_save_{cfg.credential.type}.png")
            print(f"📸 After save: URL={page.url}")

            # Verify we're back on credentials list (NOT still on create form)
            # UI navigates to /app/credentials/all after successful save
            assert page.url.startswith(f"{ELITEA_URL}/app/credentials"), \
                f"Expected to navigate to /app/credentials but got: {page.url}"

            # Add delay for backend to sync
            logger.info("Waiting 3s for backend to sync credential...")
            page.wait_for_timeout(3000)

            # Verify via API — use FRESH cookies from browser context
            fresh_cookies = page.context.cookies()
            print(f"\n🍪 Using fresh cookies from browser context: {len(fresh_cookies)} cookies")
            fresh_api = CredentialAPI(browser_cookies=fresh_cookies)
            print(f"🔗 CredentialAPI: base_url={fresh_api.base_url} project_id={fresh_api.project_id}")
            try:
                # First check raw API response
                raw_response = fresh_api.list_credentials()
                print(f"📊 Raw API response: {raw_response}")
                
                items = fresh_api.list_all_credentials()
                print(f"✅ API returned {len(items)} credentials total")
                for c in items:
                    if c.get("label") == cred_name:
                        created_id = c["id"]
                        break
                if created_id is None:
                    labels = [c.get("label", "") for c in items[:10]]
                    logger.error("Credential '%s' not found in %d total items. First 10 labels: %s",
                                 cred_name, len(items), labels)
                assert created_id is not None, f"Credential '{cred_name}' not found via API"
            finally:
                fresh_api.close()

        finally:
            if created_id:
                try:
                    # Use fresh cookies for cleanup too
                    cleanup_cookies = page.context.cookies()
                    cleanup_api = CredentialAPI(browser_cookies=cleanup_cookies)
                    cleanup_api.delete_credential(created_id)
                    cleanup_api.close()
                except Exception as e:
                    logger.warning("Cleanup failed for credential %s: %s", created_id, e)


# ---------------------------------------------------------------------------
# Test 2: Create Toolkit via UI
# ---------------------------------------------------------------------------

class TestCreateToolkit:
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/toolkits-credentials/ELITEA-1140_google-and-bitbucket-toolkit-crud.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.parametrize("toolkit_config", _all_toolkit_ids(), indirect=True)
    def test_create_toolkit(
        self, page, toolkit_config: ToolkitConfig,
        managed_credential: dict, toolkit_api: ToolkitAPI,
    ):
        """Create a toolkit through the UI form for any toolkit type."""
        cfg = toolkit_config
        tk_name = f"AutoTest {cfg.display_name} Toolkit {_ts()}"
        cred_name = managed_credential["name"]
        created_id = None

        try:
            page.goto(
                f"{settings.elitea_url}/app/toolkits/create",
                wait_until="domcontentloaded",
            )
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(1000)

            # Click toolkit type card
            card = page.get_by_text(cfg.ui_card_text).first
            card.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            card.click()
            page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
            page.wait_for_timeout(1000)

            # Fill Toolkit Name
            name_field = page.get_by_role("textbox", name="Toolkit Name")
            name_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            name_field.click()
            name_field.type(tk_name)
            page.wait_for_timeout(300)

            # Fill Description
            desc_field = page.get_by_role("textbox", name="Description")
            desc_field.click()
            desc_field.type(f"Test {cfg.display_name} toolkit for automation")
            page.wait_for_timeout(300)

            # Select credential from dropdown
            _select_credential_dropdown(page, cfg, cred_name)

            # Fill type-specific fields
            _fill_toolkit_form_fields(page, cfg)

            # Save
            save_btn = page.get_by_role("button", name="Save")
            save_btn.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            save_btn.evaluate("el => el.click()")
            page.wait_for_load_state("networkidle", timeout=FORM_SAVE_TIMEOUT)
            page.wait_for_timeout(3000)

            assert "/app/toolkits/create" not in page.url

            # Get ID for cleanup
            toolkits = toolkit_api.list_toolkits()
            rows = toolkits if isinstance(toolkits, list) else toolkits.get("rows", [])
            for t in rows:
                if t.get("name") == tk_name:
                    created_id = t["id"]
                    break

        finally:
            if created_id:
                try:
                    toolkit_api.delete_toolkit(created_id)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Test 3: Test Settings panel
# ---------------------------------------------------------------------------

class TestToolkitTestSettings:
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/toolkits-credentials/ELITEA-1140_google-and-bitbucket-toolkit-crud.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    @pytest.mark.parametrize("toolkit_config", _all_toolkit_ids(), indirect=True)
    def test_toolkit_test_settings(
        self, page, toolkit_config: ToolkitConfig, managed_toolkit: dict,
    ):
        """Run a tool via the Test Settings panel on the toolkit detail page."""
        cfg = toolkit_config
        tk_id = managed_toolkit["id"]
        base_url = settings.elitea_url

        # Navigate to toolkit detail
        page.goto(f"{base_url}/app/toolkits/all", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
        page.wait_for_timeout(1000)

        page.goto(f"{base_url}/app/toolkits/all/{tk_id}", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
        page.wait_for_timeout(2000)

        # Wait for Test Settings
        page.locator('text="Test Settings"').wait_for(
            state="visible", timeout=UI_ELEMENT_TIMEOUT,
        )

        # Open tool dropdown (right panel, x > 700)
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

        # Search for the test tool
        visible_search = Popper.find_visible_search_input(page, timeout=UI_ELEMENT_TIMEOUT)
        visible_search.fill(cfg.test_tool_name)
        page.wait_for_timeout(500)

        # Select from menu
        keyword = cfg.test_tool_name.lower().split()[0]
        selected = Popper.select_menuitem_by_content(
            page, lambda text: keyword in text.lower(),
        )
        assert selected, f"Could not find '{cfg.test_tool_name}' in dropdown"
        page.wait_for_timeout(1000)

        # Fill tool-specific parameters in the Test Settings panel (right side)
        if cfg.test_tool_params:
            for field_label, value in cfg.test_tool_params.items():
                _fill_test_settings_param(page, field_label, value)

        # Run tool — wait for button to become enabled, then click
        run_btn = page.get_by_role("button", name="Run Tool")
        run_btn.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        run_btn.first.scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        # Wait for button to be enabled (not disabled)
        try:
            page.wait_for_function(
                """() => {
                    const btn = document.querySelector('button:has(> span)');
                    const buttons = document.querySelectorAll('button');
                    for (const b of buttons) {
                        if (b.textContent.includes('Run Tool') || b.textContent.includes('RUN TOOL')) {
                            return !b.disabled;
                        }
                    }
                    return false;
                }""",
                timeout=UI_ELEMENT_TIMEOUT,
            )
        except Exception:
            logger.warning("Run Tool button may still be disabled — attempting click anyway")

        run_btn.first.click(force=True)

        # Wait for either success result or error indicator
        success_locator = page.locator(f'text="{cfg.test_tool_result_indicator}"')
        error_locator = page.locator('text="Error debugging info"')

        try:
            page.wait_for_function(
                """(indicator) => {
                    const text = document.querySelector('main')?.textContent || '';
                    return text.includes(indicator) || text.includes('Error debugging info');
                }""",
                arg=cfg.test_tool_result_indicator,
                timeout=TOOLKIT_EXECUTION_TIMEOUT,
            )
        except Exception:
            pass  # Fall through to assertions for better error reporting

        page.wait_for_timeout(2000)

        # Check for tool execution error
        if error_locator.is_visible():
            # Expand error details for better diagnostics
            error_locator.click()
            page.wait_for_timeout(500)
            content = page.locator("main").text_content()
            # Extract the error message after "Error debugging info"
            error_idx = content.find("Error debugging info")
            error_detail = content[error_idx:error_idx + 300] if error_idx >= 0 else ""
            pytest.fail(
                f"Tool execution failed for {cfg.display_name}: {error_detail}"
            )

        # Verify success — tool indicator must be visible
        content = page.locator("main").text_content()
        assert cfg.test_tool_result_indicator in content, (
            f"Expected '{cfg.test_tool_result_indicator}' in page after tool run"
        )

        # Expand collapsed tool output if present, then check content
        if cfg.test_tool_result_content:
            # Try clicking the result row to expand collapsed output
            result_row = page.locator(f'text="{cfg.test_tool_result_indicator}"').first
            try:
                result_row.click()
                page.wait_for_timeout(1000)
            except Exception:
                pass  # May not be expandable

            content = page.locator("main").text_content()
            assert cfg.test_tool_result_content in content, (
                f"Expected '{cfg.test_tool_result_content}' in tool output "
                f"for {cfg.display_name}"
            )


# ---------------------------------------------------------------------------
# Test 4: Chat with toolkit as participant
# ---------------------------------------------------------------------------

class TestChatWithToolkit:
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/toolkits-credentials/ELITEA-1140_google-and-bitbucket-toolkit-crud.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.parametrize("toolkit_config", _all_toolkit_ids(), indirect=True)
    def test_chat_with_toolkit(
        self, page, conversation_id: str, toolkit_config: ToolkitConfig,
        managed_toolkit: dict,
    ):
        """Add toolkit to chat, send a message, verify tool execution."""
        cfg = toolkit_config
        tk_name = managed_toolkit["name"]
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)
        chat.wait_for_page_load()

        page.wait_for_load_state("networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Add toolkit
        add_btn = page.locator('button[aria-label="Add toolkit"]')
        add_btn.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        add_btn.click(force=True)
        page.wait_for_timeout(1000)

        search_input = Popper.find_visible_search_input(page, timeout=UI_ELEMENT_TIMEOUT)
        search_input.fill(tk_name[:20])
        page.wait_for_timeout(1000)

        option = page.locator(f'li[role="menuitem"]:has-text("{tk_name[:15]}")').first
        option.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        option.click()
        page.wait_for_load_state("networkidle", timeout=UI_ELEMENT_TIMEOUT)
        page.wait_for_timeout(1000)

        # Send message
        initial_count = chat.get_message_count()
        chat.send_message(cfg.chat_message, use_enter=True)
        chat.wait_for_input_ready()

        # Wait for response
        chat.wait_for_message_content_stable(
            stable_duration_ms=3000,
            timeout=TOOLKIT_EXECUTION_TIMEOUT,
        )

        # Verify
        last_msg = chat.get_last_message_text()
        assert "thinking" not in last_msg.lower()
        assert any(kw in last_msg.lower() for kw in cfg.chat_response_keywords), (
            f"Expected keywords {cfg.chat_response_keywords} in response: {last_msg[:500]}"
        )
        assert chat.get_message_count() > initial_count


# ---------------------------------------------------------------------------
# UI form fill helpers
# ---------------------------------------------------------------------------

def _fill_credential_auth_fields(page, cfg: ToolkitConfig, token: str):
    """Fill auth-specific fields on the credential creation form.

    Dispatches based on cfg.credential.type to handle each credential
    type's unique form layout.

    NOTE: Secret/password fields (Access Token, Private Token, Api Key)
    render as <input type="password"> with name="api_key".  These are NOT
    matched by get_by_role("textbox") — use get_by_label() or
    locator('input[name="api_key"]') instead.  Labels may include
    trailing asterisks for required fields (e.g. "Private Token*").
    """
    cred_type = cfg.credential.type

    if cred_type == "github":
        # Select Token auth radio — reveals "Access Token" password field
        radio = page.get_by_role("radio", name="Token")
        radio.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        radio.click(force=True)
        page.wait_for_timeout(500)
        # Access Token is input[type="password"][name="api_key"]
        # NOTE: get_by_label() doesn't work reliably for password fields;
        # use direct locator on input[type="password"]
        token_field = page.locator('input[type="password"][name="api_key"]')
        token_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        token_field.click()
        token_field.type(token)

    elif cred_type == "jira":
        # Jira uses Basic auth with Api Key (password) + Username + Base Url
        # NOTE: Api Key is input[type="password"] — use direct locator
        api_key_field = page.locator('input[type="password"][name="api_key"]')
        api_key_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        api_key_field.click()
        api_key_field.type(token)
        
        username = settings.jira_username
        if username:
            user_field = page.get_by_role("textbox", name=re.compile(r"Username"))
            user_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            user_field.click()
            user_field.type(username)

        base_url = settings.jira_base_url
        if base_url:
            url_field = page.get_by_role("textbox", name=re.compile(r"Base Url"))
            url_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            url_field.click()
            url_field.type(base_url)

    elif cred_type == "gitlab":
        # Url field (textbox, label "Url *")
        url_field = page.get_by_role("textbox", name=re.compile(r"^Url"))
        url_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        url = settings.gitlab_url
        url_field.click()
        url_field.type(url)
        # Private Token is input[type="password"][name="api_key"]
        # NOTE: get_by_label() doesn't work reliably for password fields
        token_field = page.locator('input[type="password"][name="api_key"]')
        token_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        token_field.click()
        token_field.type(token)

    elif cred_type == "bitbucket":
        # Password field is input[type="password"][name="api_key"]
        pw_field = page.locator('input[type="password"][name="api_key"]')
        pw_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        pw_field.click()
        pw_field.type(token)

        username = settings.bitbucket_username
        if username:
            user_field = page.get_by_role("textbox", name=re.compile(r"Username"))
            user_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            user_field.click()
            user_field.type(username)

        url = settings.bitbucket_url
        url_field = page.get_by_role("textbox", name=re.compile(r"^Url"))
        url_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        url_field.click()
        url_field.type(url)

    elif cred_type == "confluence":
        # Base Url field (textbox, label "Base Url *")
        base_url = settings.confluence_base_url
        if base_url:
            url_field = page.get_by_role("textbox", name=re.compile(r"Base Url"))
            url_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            url_field.click()
            url_field.type(base_url)
        # Api Key is input[type="password"][name="api_key"]
        # NOTE: get_by_label() doesn't work reliably for password fields
        api_key_field = page.locator('input[type="password"][name="api_key"]')
        api_key_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        api_key_field.click()
        api_key_field.type(token)
        username = settings.confluence_username
        if username:
            user_field = page.get_by_role("textbox", name=re.compile(r"Username"))
            user_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            user_field.click()
            user_field.type(username)

    # Add more types as needed...
    page.wait_for_timeout(300)


def _select_credential_dropdown(page, cfg: ToolkitConfig, cred_name: str):
    """Open the credential dropdown on the toolkit form and select by name."""
    # Check if credential is already selected (UI auto-selects when only one exists)
    already_selected = page.locator(f'text="{cred_name}"')
    if already_selected.count() > 0 and already_selected.first.is_visible():
        # Credential already selected, no need to open dropdown
        page.wait_for_timeout(300)
        return

    # The dropdown label varies by type — find the "Configuration" text
    # Common patterns: "Github configuration", "Jira Configuration", etc.
    config_label_patterns = [
        f"{cfg.display_name} configuration",
        f"{cfg.display_name} Configuration",
        f"{cfg.display_name.lower()} configuration",
        f"{cfg.display_name.lower()}_configuration",
        "Configuration",
        "configuration",
    ]
    dropdown_clicked = False
    for label in config_label_patterns:
        dropdown = page.get_by_text(label, exact=False).first
        if dropdown.count() > 0 and dropdown.is_visible():
            dropdown.click()
            page.wait_for_timeout(500)
            dropdown_clicked = True
            break

    if not dropdown_clicked:
        # Fallback: look for any dropdown/combobox on the form
        combobox = page.locator('[role="combobox"]').first
        if combobox.count() > 0 and combobox.is_visible():
            combobox.click()
            page.wait_for_timeout(500)

    # Select credential from popper — MUI uses menuitem or option
    cred_option = page.get_by_role("menuitem", name=cred_name)
    if cred_option.count() == 0 or not cred_option.is_visible():
        # Fallback to option role
        cred_option = page.get_by_role("option", name=cred_name)
    cred_option.wait_for(state="visible", timeout=10000)
    cred_option.click()
    page.wait_for_timeout(500)
    page.wait_for_load_state("networkidle", timeout=15000)


def _fill_toolkit_form_fields(page, cfg: ToolkitConfig):
    """Fill type-specific form fields on the toolkit creation form."""
    for field_label, value in cfg.ui_form_fields.items():
        field = page.get_by_role("textbox", name=field_label)
        if field.is_visible():
            existing = field.input_value()
            if not existing:
                field.click()
                field.type(value)
                page.wait_for_timeout(300)


def _fill_test_settings_param(page, field_label: str, value: str):
    """Fill a parameter field in the Test Settings panel (right side).

    MUI TextField inputs in Test Settings have no accessible name/label
    association. We find them by locating the label span text (e.g.
    "Label *") in the right panel and then finding the sibling input
    inside the same ``index-config-field`` container.
    """
    # Find the config field container that has the label text on the right side
    field_input = page.locator(
        f'.index-config-field:has(span:text("{field_label}")) input'
    )

    # Filter to the right panel (x > 700) if there are duplicates
    target = None
    for i in range(field_input.count()):
        inp = field_input.nth(i)
        if inp.is_visible():
            bb = inp.bounding_box()
            if bb and bb["x"] > 700:
                target = inp
                break

    if target is None:
        logger.warning("Could not find param field '%s' in Test Settings panel", field_label)
        return

    target.scroll_into_view_if_needed()
    target.click()
    target.fill(value)
    page.wait_for_timeout(300)
    logger.info("Filled Test Settings param '%s' = '%s'", field_label, value)
