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

import allure
import pytest
import requests
from api import CredentialAPI, ToolkitAPI
from components.mui import Popper
from config import settings
from pages.base_page import BasePage
from pages.chat_page import ChatPage
from pages.credential_create_page import CredentialCreatePage
from pages.toolkit_creation_page import ToolkitCreationPage
from pages.toolkit_test_settings_page import ToolkitTestSettingsPage
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect
from toolkit_configs import TOOLKIT_CONFIGS, ToolkitConfig
from toolkit_factories import CREDENTIAL_FACTORIES, TOOLKIT_SETTINGS_FACTORIES
from utils.toolkit_output import (
    find_tool_end_frames,
    get_tool_output,
    observed_frame_kinds,
    tool_output_matches_success,
)
from utils.websocket_frames import capture_socketio_frames

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.new_verified]

# Timeout constants (ms)
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
# Budget for the toolkit-create POST to resolve (#2123). NOT a "longer timeout
# to turn a red green": before this repair there was NO wait at all — Step 7 was
# `wait_for_timeout(3000)` and Step 8 read the URL instantly, so a save that took
# 3.1 s was reported as "the form did not navigate" (CI run 34331579791). This is
# the budget for the FIRST real wait on that request. If a save genuinely exceeds
# it, `expect_response` raises at the click and names the missing POST — the
# correct, truthful failure.
TOOLKIT_SAVE_TIMEOUT = 30_000
# The Toolkit Name field is capped by the PRODUCT at 32 characters
# (`MAX_NAME_LENGTH`, EliteaUI src/common/constants.js:66, applied as
# `inputProps={{ maxLength }}` in NameDescriptionInput.jsx). The browser
# TRUNCATES silently at that boundary — no error, no toast. Discovered while
# repairing #2123: the former `f"AutoTest {display} Toolkit {ts}"` was 34-38
# chars for github / gitlab / bitbucket / confluence, so the toolkit was stored
# under a truncated name while the test's API lookup searched for the full one.
# The lookup therefore never matched, `created_id` stayed None and cleanup
# silently skipped — a toolkit leaked on EVERY run of those params, including
# the ones that reported PASS. Names must fit; the Step-3 value assertion is the
# guard that keeps them fitting.
TOOLKIT_NAME_MAX_LEN = 32
AI_RESPONSE_TIMEOUT = 30_000
# Increased from 60s to 120s to handle external API variability (e.g., Confluence)
TOOLKIT_EXECUTION_TIMEOUT = 120_000


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
            create_page = CredentialCreatePage(page)

            with allure.step("Step 1 — Navigate to credential creation page"):
                # Direct-route to the type-specific create form instead of
                # clicking the type card on /credentials/create-credential: that
                # grid is categorised and lazily rendered, so a card (e.g. Jira,
                # under "Project Management") can be present in the DOM yet never
                # become visible within the timeout (ELITEA-1963, re-observed on
                # DEV for #1897). The card click itself is covered for `github`
                # only, by test_credential_create.py Step 3; the grid is a uniform
                # component (CategoryItemCard.jsx renders
                # `toolkit-type-card-{type}` for every type through one code
                # path), so github's click proves the mechanism.
                create_page.navigate_to_type(cfg.url_slug)

            with allure.step(f"Step 2 — Verify the {cfg.display_name} create form rendered"):
                assert f"/credentials/create-credential/{cfg.url_slug}" in page.url, (
                    f"Expected the {cfg.display_name} create form URL, got: {page.url}"
                )
                expect(create_page.display_name_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(create_page.save_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 3 — Fill Display Name"):
                create_page.set_display_name(cred_name)
                # Assert the value LANDED. Without this a transient that wipes or
                # re-initialises the field is invisible here and only surfaces at
                # Step 7 as an opaque "not found via API" (#1897).
                expect(create_page.display_name_input).to_have_value(
                    cred_name, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 4 — Fill auth-specific fields"):
                _fill_credential_auth_fields(page, create_page, cfg, token)

            with allure.step("Step 5 — Click Save button"):
                # Case ELITEA-1140 Step 2's expected result: "The Save button
                # becomes enabled." Asserted here — this is precisely the state
                # that was wrong in the failing run.
                expect(create_page.save_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)
                # A REAL Playwright click, never `evaluate("el => el.click()")`:
                # a JS click on a disabled button is a silent no-op — no POST, no
                # navigation, no exception — which is what destroyed the evidence
                # in #1897. `click()` auto-waits for enabled and raises here, at
                # the true failure point.
                create_page.save_button.click()

            with allure.step("Step 6 — Verify navigation to credentials list"):
                # Case ELITEA-1140 Step 3's expected result: "The page returns to
                # the Credentials list." The former guard (`"/credentials" in
                # page.url`) was vacuous — it is True on
                # /credentials/create-credential/jira, the URL a failed save never
                # leaves (#1897). /credentials/all is the observed post-save
                # destination.
                page.wait_for_url(
                    re.compile(r".*/credentials/all/?(\?.*)?$"), timeout=NAVIGATION_TIMEOUT
                )

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
        """Create a toolkit through the UI form for any toolkit type.

        Repaired under #2123 (ELITEA-1141). The CI red this test produced on
        2026-09-09 (GHA run 34331579791) was a FALSE RED on a *successful* save:
        the toolkit was created, but Step 7 budgeted a fixed 3 s for the backend
        POST and Step 8 then read the URL with no wait at all, so a slow-but-fine
        save was reported as "the toolkit creation flow does not navigate away".
        Because the assert raised before the id lookup ran, teardown deleted
        nothing and both failing params LEAKED a toolkit into the CI project.

        A second, wider leak surfaced during the repair: the generated toolkit
        name exceeded the product's 32-character cap (see
        :data:`TOOLKIT_NAME_MAX_LEN`), so the toolkit was stored under a
        truncated name the API lookup could never match — every github / gitlab
        / bitbucket / confluence run leaked, PASSING runs included.

        The oracle is now the create request itself (a real 201 carrying the new
        toolkit's id), the navigation to that id's detail page, and an API
        read-back — all produced by the system. No substitution of any kind is
        performed here (`.agents/testing.md` § Fidelity policy).
        """
        cfg = toolkit_config
        tk_name = f"AT {cfg.display_name} {_ts()}"
        assert len(tk_name) <= TOOLKIT_NAME_MAX_LEN, (
            f"Generated toolkit name {tk_name!r} is {len(tk_name)} chars — the "
            f"product truncates at {TOOLKIT_NAME_MAX_LEN}, which would make the "
            f"API read-back and the teardown lookup miss it"
        )
        cred_name = managed_credential["name"]
        created_id = None
        toolkit_form = ToolkitCreationPage(page)

        try:
            with allure.step("Step 1 — Navigate to toolkit creation page"):
                toolkit_form.navigate("/toolkits/create")

            with allure.step(f"Step 2 — Select toolkit type card: {cfg.ui_card_text}"):
                # By TESTID (`toolkit-type-card-{type}`), never by card text:
                # the picker renders 71 cards and the former text-matching
                # first-match lookup could land on any of them — and on a
                # non-interactive wrapper <div> at that
                # (ToolkitCreationPage.TOOLKIT_TYPE_CARD).
                toolkit_form.select_toolkit_type(
                    cfg.ui_card_text, cfg.toolkit_type, timeout=NAVIGATION_TIMEOUT
                )

            with allure.step("Step 3 — Fill Toolkit Name"):
                toolkit_form.fill_name(tk_name)
                # Assert the value LANDED — the sibling test_create_credential's
                # Step 3 rationale (#1897): without this, a transient that wipes
                # or re-initialises the field only surfaces much later, with the
                # wrong subsystem named.
                expect(toolkit_form.name_input).to_have_value(
                    tk_name, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 4 — Fill Description"):
                description = f"Test {cfg.display_name} toolkit for automation"
                toolkit_form.fill_description(description)
                expect(toolkit_form.description_input).to_have_value(
                    description, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 5 — Verify the fixture's credential is selected"):
                # The form AUTO-SELECTS the newest saved credential of this type
                # ~0.8-1.0 s after it renders (the backend lists credentials
                # `created_at desc`; `managed_credential` created ours moments
                # ago, so it is that one). The former helper never opened this
                # dropdown either — its 307-324 ms in every CI param was purely
                # its own `wait_for_timeout(300)` — but it also never ASSERTED
                # what was selected, so a toolkit built on the wrong credential
                # passed silently. This is the case's "Toolkit linked to
                # credential" expected result, at the UI level.
                #
                # KNOWN DEFECT #2158 — re-clicking the option that is ALREADY
                # selected toggles the credential OFF in formik state while the
                # select keeps displaying it and shows no error; Save then fires
                # no request at all. So this step ASSERTS and never interacts.
                expect(toolkit_form.get_credential_select(cfg.toolkit_type)).to_contain_text(
                    cred_name, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 6 — Fill type-specific fields"):
                _fill_toolkit_form_fields(toolkit_form, cfg)

            with allure.step("Step 7 — Click Save and wait for the toolkit to be created"):
                # `shouldDisableSave = isLoading || !formik.dirty`
                # (CreateToolkitToolTabBar.jsx) — Save is enabled the moment the
                # credential auto-selects, with every required field still empty
                # (measured live, #2123). This asserts the button is CLICKABLE,
                # NOT that the form is valid. The real oracle is the 201 below.
                expect(toolkit_form.save_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

                # `wait_for_load_state("networkidle")` is NOT a save signal on
                # this app — a persistent /socket.io/ poll means it returned in
                # ~0.05 s in every measured run (#2123, the #1847 family). The
                # former `wait_for_timeout(3000)` that followed it was therefore
                # a hard 3-second budget for a backend POST. Wait on the POST.
                #
                # A REAL Playwright click, never `evaluate("el => el.click()")`:
                # a JS click on a disabled button is a silent no-op — no request,
                # no navigation, no exception — which is what destroyed the
                # evidence in the sibling #1897.
                try:
                    with page.expect_response(
                        lambda r: "/elitea_core/tools/prompt_lib/" in r.url
                        and r.request.method == "POST",
                        timeout=TOOLKIT_SAVE_TIMEOUT,
                    ) as create_response:
                        toolkit_form.save_button.click()
                except PlaywrightTimeoutError as err:
                    # Re-raised as an AssertionError so the red NAMES what is
                    # missing instead of reading "Timeout 30000ms exceeded while
                    # waiting for event 'response'" — a genuine non-save is the
                    # failure this test exists to catch, and it must say so.
                    # (Side effect, per `.agents/testing.md`: this makes the
                    # allure status `failed` rather than `broken`; nothing keys
                    # on that — conftest keys on `report.outcome` — and it also
                    # takes the failure out of pytest.ini's `--only-rerun
                    # TimeoutError` bucket, which is correct: a save that never
                    # fires is deterministic, not a flake to retry.)
                    raise AssertionError(
                        f"No create request (POST .../elitea_core/tools/prompt_lib/...) "
                        f"was observed within {TOOLKIT_SAVE_TIMEOUT} ms of clicking "
                        f"Save — the toolkit was not created. URL: {page.url}"
                    ) from err
                response = create_response.value

                # TEARDOWN GUARD (`.agents/testing.md` § Teardown-guard ordering):
                # the id is captured the instant the toolkit is known to exist,
                # BEFORE any assertion that can raise. The former code set it at
                # the very END of Step 8, after an assert that DID raise — which
                # is exactly how run 34331579791 leaked two toolkits.
                created_body = response.json() if response.status == 201 else None
                if created_body:
                    created_id = created_body.get("id")

                assert response.status == 201, (
                    f"Toolkit create POST returned {response.status}, expected 201 — "
                    f"the toolkit was not created"
                )
                assert created_id is not None, (
                    f"The create response carried no toolkit id: "
                    f"{sorted(created_body or {})}"
                )

            with allure.step("Step 8 — Verify navigation to the new toolkit's detail page"):
                # Observed destination (four live runs, all three params):
                # /toolkits/all/{id}, to which the app then appends
                # ?name=<toolkit name>. The former guard
                # (`"/toolkits/create" not in page.url`) only said "not on the
                # create form" — it never stated where the app actually goes, and
                # it passed on ANY other URL.
                page.wait_for_url(
                    re.compile(rf"/toolkits/all/{created_id}(\?.*)?$"),
                    timeout=NAVIGATION_TIMEOUT,
                )

            with allure.step("Step 9 — Verify the toolkit exists via API and is linked to the credential"):
                # `list_all_toolkits()` paginates; the former `list_toolkits()`
                # read ONE page, so on a busy project a freshly-created toolkit
                # could be absent from it. And the former lookup ASSERTED NOTHING
                # — if the toolkit was never created the test still passed and
                # cleanup silently skipped.
                rows = toolkit_api.list_all_toolkits()
                match = next((t for t in rows if t.get("name") == tk_name), None)
                assert match is not None, (
                    f"Toolkit '{tk_name}' not found via API among {len(rows)} toolkits"
                )
                assert match["id"] == created_id, (
                    f"API returned toolkit id {match['id']} for '{tk_name}', but the "
                    f"create response said {created_id}"
                )

                # The case's second expected result — "Toolkit linked to
                # credential" — closed at the API level. Key shape captured live
                # 2026-09-10 off the real 201 body for github / jira / confluence
                # (`settings["{type}_configuration"]["elitea_title"]`), never
                # inferred.
                config_key = f"{cfg.toolkit_type}_configuration"
                linked = (created_body.get("settings") or {}).get(config_key) or {}
                assert linked.get("elitea_title") == managed_credential["elitea_title"], (
                    f"Created toolkit's {config_key} is {linked.get('elitea_title')!r}, "
                    f"expected the fixture credential "
                    f"{managed_credential['elitea_title']!r}"
                )

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
        base_url = settings.app_base_url
        test_settings = ToolkitTestSettingsPage(page)

        with allure.step("Step 1 — Navigate to toolkit detail page"):
            page.goto(f"{base_url}/toolkits/all", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=NAVIGATION_TIMEOUT)
            # Dismiss NPS survey popup if it appeared on initial load
            BasePage(page).dismiss_popups()
            page.wait_for_timeout(1000)

            page.goto(f"{base_url}/toolkits/all/{tk_id}", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

        with allure.step("Step 2 — Open the Tool select on the Test-Tools empty state"):
            # ORDER CHANGE (EliteaUI EL-5947). The toolkit detail page no longer
            # opens on the Test Settings panel: TestTools.jsx now early-returns
            # `<TestToolsEmptyState/>` while `!selectedTool`, and the panel — with
            # its 'Test Settings' heading and Tool dropdown — only mounts AFTER a
            # tool is chosen. Waiting for the panel first (the old Step 2) is
            # therefore unsatisfiable: the panel cannot appear until this select
            # is used. Selecting first, asserting the panel second.
            #
            # This also retires the old raw-handle hunt — a visible-text probe and
            # a role-based combobox scan, both filtered by horizontal position,
            # plus a CSS class fallback — in favour of a testid, per
            # `.agents/testing.md` § Locator policy.
            test_settings.open_empty_state_tool_select(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(f"Step 3 — Select tool: {cfg.test_tool_name}"):
            visible_search = Popper.find_visible_search_input(page, timeout=UI_ELEMENT_TIMEOUT)
            visible_search.fill(cfg.test_tool_name)
            page.wait_for_timeout(500)

            keyword = cfg.test_tool_name.lower().split()[0]
            selected = Popper.select_menuitem_by_content(
                page, lambda text: keyword in text.lower(),
            )
            assert selected, f"Could not find '{cfg.test_tool_name}' in dropdown"

        with allure.step("Step 4 — Verify the Test Settings panel is now shown"):
            # Anchored on the panel's Tool dropdown testid rather than the
            # 'Test Settings' heading text (raw-text handles are policy-forbidden).
            test_settings.wait_for_panel(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 5 — Fill tool-specific parameters"):
            if cfg.test_tool_params:
                for field_label, value in cfg.test_tool_params.items():
                    _fill_test_settings_param(page, field_label, value)

        with allure.step("Step 6 — Click the Run Test button"):
            # Dismiss any popups (NPS survey, banners) that may block the button
            BasePage(page).dismiss_popups()

            # LABEL DRIFT (EliteaUI EL-5947). The button's visible text changed
            # from "Run Tool" to "Run Test" (TestToolSettings.jsx), which broke
            # the old role+name handle. It already carries
            # data-testid="toolkit-test-run-tool-button", so it is located by
            # testid through the page object and the label no longer matters —
            # also retiring a raw handle from this spec, per
            # `.agents/testing.md` § Locator policy.
            #
            # Playwright's click actionability waits out the button's own
            # `disabledRunTool` guard (!isValidForm || isRunning ||
            # indexNameError || patInvalid), which replaces the old
            # wait_for_function poll on button.disabled — and, unlike the
            # previous force-click, will not fire while the form is invalid.
            test_settings.run_tool(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 7 — Wait for tool execution result"):
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
                pass

            page.wait_for_timeout(2000)

        with allure.step("Step 8 — Verify tool execution success"):
            if error_locator.is_visible():
                error_locator.click()
                page.wait_for_timeout(500)
                content = page.locator("main").text_content()
                error_idx = content.find("Error debugging info")
                error_detail = content[error_idx:error_idx + 300] if error_idx >= 0 else ""
                pytest.fail(
                    f"Tool execution failed for {cfg.display_name}: {error_detail}"
                )

            content = page.locator("main").text_content()
            assert cfg.test_tool_result_indicator in content, (
                f"Expected '{cfg.test_tool_result_indicator}' in page after tool run"
            )

            if cfg.test_tool_result_content:
                result_row = page.locator(f'text="{cfg.test_tool_result_indicator}"').first
                try:
                    result_row.click()
                    page.wait_for_timeout(1000)
                except Exception:
                    pass

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
        """Add toolkit to chat, send a message, verify the tool really ran.

        AFS: ``test-specs/toolkits/lfix_toolkit_chat_error_oracle_ELITEA-1140.md``
        (repair brief for card #1817).

        Step 5's oracle reads the toolkit's own ``tool_output`` off the
        ``agent_tool_end`` Socket.IO frame, because Elitea publishes no
        structural marker for a failed tool execution — success and failure
        share DOM, testids, event sequence and ``finish_reason``, and the
        chat message is LLM prose wrapped around arbitrary user data. The
        free-text guards this replaced scanned that prose for ``"error"``,
        which matched this repository's own branch names (a genuine success,
        GHA run 32931571484) while missing every real 401 (which the model
        narrates as *"authentication error"*, and which still satisfies
        ``chat_response_keywords``). No negative substring scan survives on
        any channel — the ``"thinking"`` scan went with them, for the same
        reason and because it proved nothing Step 4 had not already waited
        for. See ``utils/toolkit_output``.

        A toolkit whose success shape has never been captured SKIPS at Tier 2
        rather than continuing: without it a failed call is indistinguishable
        from a successful one at every remaining tier, so continuing would
        report GREEN on a broken toolkit.

        No substitution: the frames are **passively observed**: nothing is
        routed, fulfilled, injected or fabricated, and every asserted value is
        produced end to end by the real system.
        """
        cfg = toolkit_config
        tk_name = managed_toolkit["name"]
        chat = ChatPage(page)

        # Entered BEFORE any navigation — Playwright's "websocket" page event
        # fires only at connection-open time, so a listener attached later
        # never sees a frame (utils/websocket_frames docstring). Called as the
        # shared util rather than through a ChatPage delegator: this branch
        # targets `main`, and an identically-added *method* lands at a
        # different anchor than base's copy (merge conflict + duplicate
        # definition), where an identically-added *file* merges clean.
        with capture_socketio_frames(page) as frames:
            with allure.step("Step 1 — Navigate to chat"):
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

            with allure.step("Step 5 — Verify the toolkit's tool executed successfully"):
                # Tier 1 — the tool actually ran. Nothing else here proves it:
                # a model answering from memory satisfies every assertion below.
                tool_end_frames = find_tool_end_frames(
                    frames,
                    tool_name=cfg.test_tool_result_indicator,
                    toolkit_display_name=tk_name,
                )
                assert len(tool_end_frames) == 1, (
                    f"Expected exactly one agent_tool_end frame for tool "
                    f"'{cfg.test_tool_result_indicator}' of toolkit '{tk_name}', "
                    f"got {len(tool_end_frames)} of {len(frames)} captured "
                    f"Socket.IO frames. 0 of 0 = the CAPTURE failed (harness); "
                    f"0 of many = the model never called the tool (real signal); "
                    f">1 = a double call. Distinct received (type, tool_name): "
                    f"{observed_frame_kinds(frames)}"
                )
                tool_output = get_tool_output(tool_end_frames[0])
                assert tool_output.strip(), (
                    f"agent_tool_end for '{cfg.test_tool_result_indicator}' carried "
                    f"an empty tool_output"
                )

                # Tier 2 — positive, ANCHORED match against this toolkit's
                # captured success shape. Never a scan for the word "error":
                # the success payload legitimately contains it.
                if cfg.tool_output_success_pattern:
                    assert tool_output_matches_success(
                        tool_output, cfg.tool_output_success_pattern
                    ), (
                        f"{cfg.display_name} tool '{cfg.test_tool_result_indicator}' did "
                        f"not return its captured success shape "
                        f"({cfg.tool_output_success_pattern!r}) — the tool call FAILED. "
                        f"tool_output: {tool_output[:500]}"
                    )
                else:
                    # Fallback rule: no success shape has ever been captured for
                    # this toolkit, so classify nothing rather than invent a
                    # pattern (AFS § Recommended oracle, Tier 2). Structurally
                    # a SKIP, not a warning: without a captured shape a failed
                    # tool call is indistinguishable from a successful one at
                    # every remaining tier, so continuing would report GREEN on
                    # a broken toolkit — strictly worse than the false-RED this
                    # card removes. This masks no product defect and hides no
                    # red; it makes "not verified" visible where a log line in
                    # a GHA transcript is not a gate.
                    pytest.skip(
                        f"{cfg.display_name} has no captured "
                        f"tool_output_success_pattern, so a failed tool call "
                        f"cannot be told from a successful one — capture "
                        f"agent_tool_end.response_metadata.tool_output live for "
                        f"'{cfg.test_tool_result_indicator}' and populate "
                        f"TOOLKIT_CONFIGS['{cfg.toolkit_type}']"
                    )

                # Tier 3 — the UI carried the result through to a new message.
                # No negative substring scan here either: `last_msg` is LLM
                # prose wrapped around the same arbitrary user data, so
                # `"thinking" not in last_msg` would re-create #1817 on a
                # branch named e.g. `tests/ELITEA-XXXX-agent-thinking-...`.
                # It proved nothing anyway — `wait_for_ai_response()` already
                # waits on the Copy button (generation finished), and a
                # "Thinking…" placeholder cannot satisfy the keyword assertion
                # below (AFS § Q3).
                last_msg = chat.get_last_message_text()
                assert any(kw in last_msg.lower() for kw in cfg.chat_response_keywords), (
                    f"Expected keywords {cfg.chat_response_keywords} in response: {last_msg[:500]}"
                )
                assert chat.get_message_count() > initial_count


# ---------------------------------------------------------------------------
# UI form fill helpers
# ---------------------------------------------------------------------------

def _require_env(env_var: str, value: str, cfg: ToolkitConfig) -> str:
    """Return *value*, or skip the test naming the missing environment variable.

    An empty env var behind a **required** credential field is a CONFIGURATION
    gap, not a product verdict. The old code guarded these with a silent
    ``if value:`` and simply left the field empty — which leaves Save disabled
    and turns a config gap into an opaque "not found via API" failure two steps
    downstream (#1897). This is a PRECONDITION skip: it masks no defect, it
    names the variable that is missing.
    """
    if not value:
        pytest.skip(
            f"{env_var} is not set — it is a required field on the "
            f"{cfg.display_name} credential form"
        )
    return value


def _assert_secret_filled(field, value: str, label: str) -> None:
    """Assert a masked field holds *value*, comparing LENGTH only.

    Never interpolate or compare the secret itself — an assertion message ends
    up in logs and CI transcripts. Length is enough to prove the keystrokes
    landed, which is the diagnosis #1897 needed.
    """
    typed = len(field.input_value())
    assert typed == len(value), (
        f"{label} field should contain the full secret ({len(value)} chars), "
        f"got {typed} chars — the value did not land"
    )


def _fill_credential_auth_fields(
    page, create_page: CredentialCreatePage, cfg: ToolkitConfig, token: str
):
    """Fill auth-specific fields on the credential creation form.

    Dispatches based on cfg.credential.type to handle each credential
    type's unique form layout.

    Every value typed into a **required** field is asserted immediately with
    ``to_have_value`` (secrets by length via :func:`_assert_secret_filled`), so
    a transient that wipes or never lands a value fails HERE, naming the field —
    rather than surfacing at Step 7 as "credential not found via API" (#1897).

    Required-field sets differ per type (captured live on DEV 2026-08-28):
    github needs only ``label``/``elitea_title``/``base_url`` and ships
    ``base_url`` pre-filled, which is why ``[github]`` could never fail this
    way; jira and confluence additionally require ``username`` + ``base_url``.

    NOTE: Secret fields (Access Token, Api Key) render as
    ``<input type="password">`` inside a secret-toggle wrapper and are reached
    through the page object's ``toolkit-field-*-input-field`` testids.
    """
    cred_type = cfg.credential.type

    if cred_type == "github":
        # Token auth radio reveals the "Access Token" secret field. Access Token
        # is NOT a required field and base_url ships pre-filled, so Save is
        # already enabled by the Display Name alone — nothing here can disable it.
        create_page.select_auth_method("token")
        expect(create_page.access_token_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        create_page.set_access_token(token)
        _assert_secret_filled(create_page.access_token_input, token, "Access Token")

    elif cred_type == "jira":
        # Jira uses Basic auth: Api Key (secret) + Username + Base Url.
        # Username and Base Url are REQUIRED — an empty env var here is what
        # leaves Save disabled, so it skips loudly instead of falling through.
        username = _require_env("JIRA_USERNAME", settings.jira_username, cfg)
        base_url = _require_env("JIRA_BASE_URL", settings.jira_base_url, cfg)

        create_page.set_api_key(token)
        _assert_secret_filled(create_page.api_key_input, token, "Api Key")

        create_page.set_username(username)
        expect(create_page.username_input).to_have_value(username, timeout=UI_ELEMENT_TIMEOUT)

        create_page.set_base_url(base_url)
        expect(create_page.base_url_input).to_have_value(base_url, timeout=UI_ELEMENT_TIMEOUT)

    elif cred_type == "gitlab":
        # KNOWN DEFECT (#1936, out of scope for #1897): the secret field below is
        # located by name="api_key", but GitLab's is named `private_token`
        # (`toolkit-field-private_token-input-field`). Never fires today — this
        # param is unconditionally skipped (no active GitLab account).
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
        # KNOWN DEFECT (#1936, out of scope for #1897): the secret field below is
        # located by name="api_key", but Bitbucket's is named `password`
        # (`toolkit-field-password-input-field`). Never fires today — this param
        # is unconditionally skipped (no active Bitbucket account).
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
        # Same required set as Jira: Base Url + Username are REQUIRED, Api Key
        # is not. Skip loudly on a missing env var rather than leaving the
        # field empty and the Save button disabled (#1897).
        base_url = _require_env("CONFLUENCE_BASE_URL", settings.confluence_base_url, cfg)
        username = _require_env("CONFLUENCE_USERNAME", settings.confluence_username, cfg)

        create_page.set_base_url(base_url)
        expect(create_page.base_url_input).to_have_value(base_url, timeout=UI_ELEMENT_TIMEOUT)

        create_page.set_api_key(token)
        _assert_secret_filled(create_page.api_key_input, token, "Api Key")

        create_page.set_username(username)
        expect(create_page.username_input).to_have_value(username, timeout=UI_ELEMENT_TIMEOUT)

    # Add more types as needed...


def _fill_toolkit_form_fields(toolkit_form: ToolkitCreationPage, cfg: ToolkitConfig):
    """Fill the type-specific schema-driven fields on the toolkit creation form.

    Keyed by SCHEMA KEY (``cfg.ui_form_fields``), so each field is reached
    through its own ``toolkit-field-{key}-input`` testid via
    :meth:`ToolkitCreationPage.fill_field`. Re-keyed under #2123: the former
    body located fields by their visible UI label (a raw accessible-name
    textbox handle) and then guarded on ``if field.is_visible()`` /
    ``if not existing`` — so a field it could not see, or one it decided was
    already filled, was **silently skipped**. A required field left empty puts this form into a state that is
    hard to diagnose two steps later: Save stays *enabled*
    (``shouldDisableSave = isLoading || !formik.dirty`` — validity is
    deliberately not part of it), the click fires **no request at all**, and
    nothing visible reports an error.

    Each fill is asserted, so a value that does not land fails here rather than
    surfacing at the save with the wrong subsystem named.

    Args:
        toolkit_form: The creation-form page object, already on the form.
        cfg: The toolkit type's configuration.
    """
    for field_key, value in cfg.ui_form_fields.items():
        if not value:
            # A config gap, not a product verdict — skip loudly naming the key
            # rather than falling through into a save that cannot succeed
            # (#1897's rule, applied to the toolkit form).
            pytest.skip(
                f"No configured value for the {cfg.display_name} toolkit form's "
                f"'{field_key}' field — set it in .env.test"
            )
        toolkit_form.fill_field(field_key, value)
        expect(toolkit_form.get_field_locator(field_key)).to_have_value(
            value, timeout=UI_ELEMENT_TIMEOUT
        )


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
