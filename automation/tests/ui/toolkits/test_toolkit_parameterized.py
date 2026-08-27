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
from playwright.sync_api import expect

from api import CredentialAPI, ToolkitAPI
from config import settings
from pages.base_page import BasePage
from pages.chat_page import ChatPage
from pages.toolkit_detail_page import ToolkitDetailPage
from pages.toolkit_test_settings_page import ToolkitTestSettingsPage
from toolkit_configs import TOOLKIT_CONFIGS, ToolkitConfig
from toolkit_factories import CREDENTIAL_FACTORIES, TOOLKIT_SETTINGS_FACTORIES

# Import from conftest
from conftest import ELITEA_URL
import allure

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.new_verified]

# Timeout constants (ms)
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000
# Increased from 60s to 120s to handle external API variability (e.g., Confluence)
TOOLKIT_EXECUTION_TIMEOUT = 120_000
# Page-load-scale budget for a freshly-created toolkit's detail view to finish
# loading far enough to mount its action bar. See Step 1b: the breadcrumb title
# is NOT a readiness signal for that bar, so the bar's own button is waited on
# with a navigation-sized budget rather than a UI-interaction-sized one.
TOOLKIT_DETAIL_READY_TIMEOUT = 30_000


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
            base_url = settings.app_base_url

            with allure.step("Step 1 — Navigate to credential creation page"):
                page.goto(
                    f"{base_url}/credentials/create-credential",
                    wait_until="domcontentloaded",
                )
                page.wait_for_load_state("networkidle", timeout=30000)
                page.wait_for_timeout(1000)

            with allure.step(f"Step 2 — Click credential type card: {cfg.display_name}"):
                type_card = page.get_by_text(cfg.display_name, exact=True).first
                type_card.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                type_card.click()
                page.wait_for_load_state("networkidle", timeout=30000)

            with allure.step("Step 3 — Fill Display Name"):
                name_field = page.get_by_role("textbox", name="Display Name")
                name_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                page.wait_for_timeout(1000)
                name_field.click()
                name_field.type(cred_name)
                page.wait_for_timeout(300)

            with allure.step("Step 4 — Fill auth-specific fields"):
                _fill_credential_auth_fields(page, cfg, token)
                pre_save_value = name_field.input_value()
                logger.info("Pre-save Display Name: %r (expected %r)", pre_save_value, cred_name)
                page.screenshot(path=f"/tmp/cred_form_presave_{cfg.credential.type}.png")

            with allure.step("Step 5 — Click Save button"):
                save_btn = page.get_by_role("button", name="Save")
                save_btn.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                save_btn.evaluate("el => el.click()")
                page.wait_for_load_state("networkidle", timeout=FORM_SAVE_TIMEOUT)
                page.wait_for_timeout(3000)
                page.screenshot(path=f"/tmp/cred_after_save_{cfg.credential.type}.png")
                print(f"📸 After save: URL={page.url}")

            with allure.step("Step 6 — Verify navigation to credentials list"):
                assert "/credentials" in page.url, \
                    f"Expected to navigate to /credentials but got: {page.url}"
                logger.info("Waiting 3s for backend to sync credential...")
                page.wait_for_timeout(3000)

            with allure.step("Step 7 — Verify credential exists via API"):
                fresh_cookies = page.context.cookies()
                print(f"\n🍪 Using fresh cookies from browser context: {len(fresh_cookies)} cookies")
                fresh_api = CredentialAPI(browser_cookies=fresh_cookies)
                print(f"🔗 CredentialAPI: base_url={fresh_api.base_url} project_id={fresh_api.project_id}")
                try:
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
            with allure.step("Step 1 — Navigate to toolkit creation page"):
                page.goto(
                    f"{settings.app_base_url}/toolkits/create",
                    wait_until="domcontentloaded",
                )
                page.wait_for_load_state("networkidle", timeout=30000)
                page.wait_for_timeout(1000)

            with allure.step(f"Step 2 — Click toolkit type card: {cfg.ui_card_text}"):
                card = page.get_by_text(cfg.ui_card_text).first
                card.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                card.click()
                page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
                page.wait_for_timeout(1000)

            with allure.step("Step 3 — Fill Toolkit Name"):
                name_field = page.get_by_role("textbox", name="Toolkit Name")
                name_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                name_field.click()
                name_field.type(tk_name)
                page.wait_for_timeout(300)

            with allure.step("Step 4 — Fill Description"):
                desc_field = page.get_by_role("textbox", name="Description")
                desc_field.click()
                desc_field.type(f"Test {cfg.display_name} toolkit for automation")
                page.wait_for_timeout(300)

            with allure.step("Step 5 — Select credential from dropdown"):
                _select_credential_dropdown(page, cfg, cred_name)

            with allure.step("Step 6 — Fill type-specific fields"):
                _fill_toolkit_form_fields(page, cfg)

            with allure.step("Step 7 — Click Save button"):
                save_btn = page.get_by_role("button", name="Save")
                save_btn.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                save_btn.evaluate("el => el.click()")
                page.wait_for_load_state("networkidle", timeout=FORM_SAVE_TIMEOUT)
                page.wait_for_timeout(3000)

            with allure.step("Step 8 — Verify navigation away from create form"):
                assert "/toolkits/create" not in page.url

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
        """Run a tool via the Test Settings panel on the Test Toolkit surface.

        AFS: test-specs/toolkits-credentials/ladjust_toolkit_test_settings_ELITEA-1140.md

        Repaired for elitea-testing-public#1816 (class A UI drift): the #1616
        redesign moved the Test Settings surface off /toolkits/all/{id} onto its
        own /toolkits/{tab}/{id}/test route, reached via the detail view's
        action-bar Test button (Step 1b).

        No substitution: every observable below is produced by the live system —
        the tool is chosen, run and read through the product's own UI, and the
        navigation goes through the product's own control rather than a forced URL.
        """
        cfg = toolkit_config
        tk_id = managed_toolkit["id"]
        base_url = settings.app_base_url
        toolkit_detail = ToolkitDetailPage(page)
        test_settings = ToolkitTestSettingsPage(page)

        with allure.step("Step 1 — Navigate to toolkit detail page"):
            page.goto(f"{base_url}/toolkits/all", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
            # Dismiss NPS survey popup if it appeared on initial load
            BasePage(page).dismiss_popups()

            page.goto(f"{base_url}/toolkits/all/{tk_id}", wait_until="domcontentloaded")
            # Confirms we landed on the toolkit's own detail route, replacing the
            # previous fixed two-second sleep — a sleep is not a readiness signal
            # (`.agents/conventions.md` § Hard don'ts).
            #
            # This is a route check, NOT a load-complete gate: `toolkit-detail-title`
            # is a BREADCRUMB entry (breadcrumb.constants.js), rendered from route
            # params as soon as the route resolves — well before the toolkit's data
            # has loaded and the form's action bar has mounted. Step 1b therefore
            # does its own wait on the control it actually needs.
            expect(toolkit_detail.toolkit_title).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 1b — Open the Test Toolkit surface via the detail view's "
            "action-bar 'Test' button"
        ):
            # NEW STEP (elitea-testing-public#1616 redesign, tracked as #1816).
            # The whole TEST SETTINGS surface has LEFT the toolkit detail view and
            # now lives on its own route, /toolkits/{tab}/{toolkit_id}/test
            # (routes.js:36 -> ToolkitTest -> ToolkitTest.jsx renders
            # <ToolkitTestPanel/>). Without this navigation, Step 2 can never pass:
            # `toolkit-test-empty-tool-select` is simply not rendered on
            # /toolkits/all/{id}. That is exactly the timeout this repair fixes.
            #
            # Reached through the product's OWN action-bar button rather than a
            # forced `page.goto()` of the /test URL: the navigation is part of what
            # the case exercises, and forcing the URL would substitute it
            # (`.agents/testing.md` § Fidelity policy).
            #
            # Reused verbatim from the sibling repair ELITEA-1866 / #1815
            # (`ToolkitDetailPage.open_test_surface()`, already on main via
            # c25113893) — it waits for the button to mount before clicking, which
            # absorbs the "action bar not mounted at domcontentloaded" race without
            # re-introducing a sleep — it waits for the button before clicking.
            #
            # That wait is given a PAGE-LOAD-scale budget here, not the default
            # UI-interaction one. The action bar renders only once the toolkit form's
            # own data load resolves (ToolkitForm.jsx: the button is gated behind
            # `isDetailsActionBar && handleShowTest`), which on a freshly API-created
            # toolkit has been observed to take longer than 10s — one such timeout was
            # seen on `[jira]` during this repair. The button IS the readiness signal
            # for this step, so it is waited on directly with a budget sized for a
            # page load (`.agents/testing.md` § networkidle/#1847: wait on the element
            # the caller actually needs). Costs nothing when the bar is already there.
            toolkit_detail.open_test_surface(timeout=TOOLKIT_DETAIL_READY_TIMEOUT)

        with allure.step("Step 2 — Verify the Test-Tools empty state offers the Tool select"):
            # ORDER CHANGE (EliteaUI EL-5947). The Test Settings panel is gated
            # behind tool selection: TestTools.jsx early-returns
            # `<TestToolsEmptyState/>` while `!selectedTool`, and the panel — with
            # its 'Test Settings' heading and Tool dropdown — only mounts AFTER a
            # tool is chosen. Waiting for the panel first is therefore
            # unsatisfiable: the panel cannot appear until this select is used.
            #
            # The observable of this step is that the tool-selection entry point is
            # PRESENT on the (now relocated) Test surface, so it is asserted
            # explicitly here and the popover is opened by Step 3's page-object
            # call. Opening it here as well would click the trigger twice and
            # toggle the popover shut.
            expect(test_settings.empty_state_tool_select).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(f"Step 3 — Select tool: {cfg.test_tool_name}"):
            # HANDLE CHANGE. The old flow typed into a raw
            # `input[placeholder*="Search"]` and then scanned raw
            # `[role="menuitem"]` nodes for a display-name keyword. Both are
            # raw handles (`.agents/testing.md` § Locator policy) and both are
            # display-name coupled — the labels have already drifted
            # ("List branches" -> "List branches in repo", "List pages" ->
            # "List pages with label"), which is precisely the brittleness the
            # testid policy exists to remove.
            #
            # The dropdown options carry `select-option-{tool_schema_key}` (shared
            # SingleSelectMenuItem.jsx / PopoverSelect.jsx, already on main), and
            # the tool's schema key is exactly what `test_tool_result_indicator`
            # already holds — so selection is now testid-driven and immune to
            # display-name drift. No search typing is needed.
            test_settings.select_tool_from_empty_state(
                cfg.test_tool_result_indicator, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step("Step 4 — Verify the Test Settings panel is now shown"):
            # Anchored on the panel's Tool dropdown testid rather than the
            # 'Test Settings' heading text (raw-text handles are policy-forbidden).
            test_settings.wait_for_panel(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 5 — Fill tool-specific parameters"):
            # HANDLE CHANGE + LATENT-BUG FIX. The old `_fill_test_settings_param()`
            # helper located inputs by a raw `.index-config-field:has(span:text(...))`
            # CSS chain and then filtered the candidates by bounding box `x > 700`
            # ("the right panel"). The #1616 redesign puts Test Settings in the LEFT
            # column (ToolkitTestPanel.jsx — `styles.leftColumn`), so that filter
            # matches nothing and the helper's `if target is None:` branch logged a
            # warning and RETURNED WITHOUT FILLING — silently. The run button is
            # disabled until required params are filled, so this would have surfaced
            # as an unrelated actionability failure at Step 6, one step after the
            # symptom. Replaced by the `toolkit-test-param-{schema_key}-input`
            # testid family (already on main), keyed by schema key.
            for schema_key, value in cfg.test_tool_params.items():
                test_settings.fill_param_field(
                    schema_key, value, timeout=UI_ELEMENT_TIMEOUT,
                )

        with allure.step("Step 6 — Click the Run Test button"):
            # Dismiss any popups (NPS survey, banners) that may block the button
            BasePage(page).dismiss_popups()

            # LABEL DRIFT (EliteaUI EL-5947). The button's visible text changed
            # from "Run Tool" to "Run Test", which broke the old role+name handle.
            # It carries data-testid="toolkit-test-run-tool-button", so it is
            # located by testid through the page object and the label no longer
            # matters.
            #
            # Playwright's click actionability waits out the button's own
            # `disabledRunTool` guard (!isValidForm || isRunning || indexNameError
            # || patInvalid), which replaces the old wait_for_function poll on
            # button.disabled — and, unlike the previous force-click, will not fire
            # while the form is invalid.
            test_settings.run_tool(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 7 — Wait for tool execution result"):
            # The old wait polled `document.querySelector('main').textContent` via
            # `page.wait_for_function`, wrapped the whole thing in a bare
            # `except: pass`, and then slept 2s. A swallowed timeout meant Step 8
            # asserted against whatever happened to be on screen — a stalled run
            # could pass or fail for the wrong reason. Replaced by the page
            # object's scoped wait, which polls the result message item for its
            # ✅/❌ prefix with an auto-retrying assertion and RAISES on timeout.
            #
            # `tool_key` enables the page object's ELITEA-1979 mid-wait
            # panel-remount recovery (re-select the tool, re-click Run Test once).
            # That recovery deliberately does NOT refill parameter fields, so it is
            # only passed for parameterless tools; for a tool with required params
            # a remount must raise rather than re-run an invalid form.
            result_text = test_settings.wait_for_tool_result(
                timeout=TOOLKIT_EXECUTION_TIMEOUT,
                tool_key=None if cfg.test_tool_params else cfg.test_tool_result_indicator,
            )

        with allure.step("Step 8 — Verify tool execution success"):
            # Every assertion below reads the SAME system-produced result text
            # returned by Step 7, scoped to the result message item, instead of
            # the text content of the whole <main> element as before. That element
            # also contains the Test Settings form, the tool name in the combobox
            # and the page chrome, any of which could satisfy a substring check
            # without the tool having produced it. This is a strengthening, not a
            # change of what is verified.
            #
            # The diagnostic error branch is preserved: it used to be a raw
            # visible-text handle on the error-details row, and is now the same
            # check expressed against the system-produced result text.
            if "❌" in result_text or "Error debugging info" in result_text:
                pytest.fail(
                    f"Tool execution failed for {cfg.display_name}: {result_text[:300]}"
                )

            assert cfg.test_tool_result_indicator in result_text, (
                f"Expected '{cfg.test_tool_result_indicator}' in the tool result "
                f"for {cfg.display_name}, got: {result_text[:300]}"
            )

            if cfg.test_tool_result_content:
                # NOTE: the ✅ marker is NOT a success oracle — it means the tool
                # RAN, not that the call succeeded. A GitHub run has been observed
                # returning `✅ list_branches_in_repo (0.213s) Failed to list
                # branches: 401 {"message": "Bad credentials"}`. This content
                # assertion is the only real oracle in this test; do not substitute
                # the marker for it.
                assert cfg.test_tool_result_content in result_text, (
                    f"Expected '{cfg.test_tool_result_content}' in tool output "
                    f"for {cfg.display_name}, got: {result_text[:300]}"
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

        with allure.step("Step 1 — Navigate to chat"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.wait_for_page_load()
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(2000)

        with allure.step(f"Step 2 — Add toolkit participant: {tk_name}"):
            chat.add_toolkit_participant(tk_name, timeout=UI_ELEMENT_TIMEOUT)
            page.wait_for_timeout(1000)

        with allure.step("Step 3 — Send message to invoke toolkit"):
            initial_count = chat.get_message_count()
            chat.send_message(cfg.chat_message, use_enter=True)
            chat.wait_for_input_ready()

        with allure.step("Step 4 — Wait for AI response"):
            chat.wait_for_ai_response(
                initial_count=initial_count,
                timeout=TOOLKIT_EXECUTION_TIMEOUT,
            )

        with allure.step("Step 5 — Verify response contains expected keywords"):
            last_msg = chat.get_last_message_text()

            # Check for tool execution errors first
            assert "authorization error" not in last_msg.lower(), (
                f"Tool execution failed with authorization error. "
                f"Check credentials in .env.test. Response: {last_msg[:500]}"
            )
            assert "error" not in last_msg.lower() or "no results" in last_msg.lower(), (
                f"Tool execution returned an error. Response: {last_msg[:500]}"
            )

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
        # NOTE: Jira API tokens can be 120+ characters; use a generous timeout to
        #       avoid the default 10s expiring before all keystrokes are sent.
        api_key_field = page.locator('input[type="password"][name="api_key"]')
        api_key_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        api_key_field.click()
        api_key_field.type(token, timeout=60_000)
        
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
