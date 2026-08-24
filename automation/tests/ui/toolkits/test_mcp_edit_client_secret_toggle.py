"""UI test — Remote MCP Client Secret with the Secret/Password storage toggle.

TMS: ELITEA-1932
(test-specs/mcp/l1_edit-remote-mcp-client-secret-secret-password-toggle_ELITEA-1932.md)

Verifies the Client Secret field's "secret view toggler" on a Remote MCP's detail
page: Password mode is active by default (value masked), switching to Secret mode
swaps the native input for the project's secret-vault select, and a selected vault
reference persists in Secret mode across a save and a full page reload.

No substitution of the system under test is performed: every asserted value — the
toggle's `aria-pressed` state, the input's `type`, the rendered vault options, the
displayed secret name, the update PUT's own response body, the rendered Raw Json —
is produced by the live product against the DEV backend. Nothing is routed,
fulfilled, injected or monkeypatched.

Test data: the case's own Test Data table is empty and its precondition is "access
to the Elitea secret vault". The vault secret `auth_token` is a long-standing
project secret, used **read-only** here (never created, edited or deleted) — the
same entry the merged credentials case ELITEA-1968 selects. The Remote MCP itself
is seeded through the real UI create flow and deleted in teardown, because no
pre-existing MCP is discoverable at runtime on this environment (AFS § Test Data).
"""

import logging
import uuid

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

UI_TIMEOUT = 10_000
EXISTING_SECRET_NAME = "auth_token"
EXPECTED_SECRET_REFERENCE = "{{secret.auth_token}}"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1932_edit-remote-mcp-client-secret-toggle.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
def test_mcp_edit_client_secret_secret_password_toggle(page, toolkit_api: ToolkitAPI):
    """Client Secret toggles Password<->Secret; a vault reference persists in Secret mode."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)

    # Seed a dedicated, disposable Remote MCP (AFS § Test Data) — MAX_NAME_LENGTH
    # = 32 truncates the Toolkit Name field client-side; this name is 26 chars.
    toolkit_name = f"autotest_mcp_secret_{uuid.uuid4().hex[:6]}"

    form.navigate_to_create()
    form.select_remote_mcp_type()
    form.fill_name(toolkit_name)
    # Stored only — this case never clicks Load Tools, so the URL is never dialled.
    form.fill_url("https://mcp.example.com/sse")
    toolkit_id = form.save_and_wait_for_created(project_id)["id"]

    # Console listener — identical pattern to the sibling MCP edit specs (#291
    # dev-mode warnings filtered, known #549 Tabs warning soft-failed) so a real
    # regression in this flow can't hide behind an already-tracked warning.
    console_messages = []
    soft_failures = []

    def _is_known_291_warning(msg) -> bool:
        text = msg.text
        return (
            'unique "key" prop' in text
            or ("validateDOMNesting" in text and "<p>" in text)
            or ("validateDOMNesting" in text and "%s" in text)
        )

    def _is_known_549_warning(msg) -> bool:
        return "Tabs component is invalid" in msg.text

    page.on(
        "console",
        lambda msg: console_messages.append(msg)
        if msg.type == "error" and not _is_known_291_warning(msg)
        else None,
    )

    def _check_no_new_console_errors(step_label: str) -> None:
        """Split captured console errors: known #549 -> soft; anything else -> hard fail."""
        new_549 = [m for m in console_messages if _is_known_549_warning(m)]
        unexpected = [m for m in console_messages if not _is_known_549_warning(m)]
        for msg in new_549:
            soft_failures.append(
                "Known defect github.com/EliteaAI/elitea-testing-public/issues/549: "
                f"{step_label} — MUI Tabs invalid-value console error: {msg.text!r}"
            )
        assert not unexpected, (
            f"{step_label} — unexpected new console errors beyond the two "
            "pre-existing dev-mode warnings tracked in #291 and the known "
            f"#549 Tabs warning, got: {[m.text for m in unexpected]}"
        )
        console_messages.clear()

    try:
        with allure.step("Step 1 — Open the Remote MCP detail page in Form view"):
            form.navigate_to_detail(toolkit_id, project_id)
            assert form.form_view_toggle.get_attribute("aria-pressed") == "true", (
                "Detail page should load in Form view"
            )
            assert form.get_detail_heading_text() == toolkit_name, (
                f"Detail title should show the toolkit's name, "
                f"got: {form.get_detail_heading_text()!r}"
            )

        with allure.step('Step 2 — Locate the "Client Secret" field'):
            # The detail page renders NO toolkit-field-* node until the
            # configuration section is expanded (digest § MCP DETAIL page).
            assert form.client_secret_input.count() == 0, (
                "The Client Secret field should not be in the DOM before the "
                "configuration section is expanded"
            )
            form.expand_configuration_section()
            expect(form.client_secret_input).to_be_visible(timeout=UI_TIMEOUT)

        with allure.step('Step 3 — Verify the "secret view toggler" shows Secret and Password'):
            expect(form.client_secret_toggle_secret).to_be_visible(timeout=UI_TIMEOUT)
            expect(form.client_secret_toggle_password).to_be_visible(timeout=UI_TIMEOUT)
            expect(form.client_secret_toggle_secret).to_have_text("Secret")
            expect(form.client_secret_toggle_password).to_have_text("Password")

        with allure.step('Step 4 — Verify "Password" is pressed by default and the value is masked'):
            expect(form.client_secret_toggle_password).to_have_attribute("aria-pressed", "true")
            expect(form.client_secret_toggle_secret).to_have_attribute("aria-pressed", "false")
            # "Masked text" is the native input's own type — read off the real
            # <input> the SecretField renders in Password mode.
            expect(form.client_secret_input_field).to_have_attribute("type", "password")

        with allure.step('Step 5 — Click the "Secret" button'):
            form.switch_client_secret_to_secret_mode()

        with allure.step("Step 6 — Verify the toggle switched to Secret mode"):
            expect(form.client_secret_toggle_secret).to_have_attribute("aria-pressed", "true")
            expect(form.client_secret_toggle_password).to_have_attribute("aria-pressed", "false")
            # Secret mode swaps the whole control: the native input is UNMOUNTED
            # (not hidden) and the vault select takes its place.
            expect(form.client_secret_input_field).to_have_count(0)
            expect(form.client_secret_combobox).to_be_visible(timeout=UI_TIMEOUT)

        with allure.step(
            f"Step 7 — Enter a credential reference from the vault ({EXISTING_SECRET_NAME})"
        ):
            form.open_client_secret_vault_dropdown()
            # The case's precondition is "access to the Elitea secret vault" —
            # assert the vault actually rendered before picking from it.
            expect(form.saved_secrets_group_header()).to_be_visible(timeout=UI_TIMEOUT)
            expect(form.saved_secret_option(EXISTING_SECRET_NAME)).to_be_visible(timeout=UI_TIMEOUT)
            form.select_client_secret_saved_secret(EXISTING_SECRET_NAME)
            assert form.get_client_secret_display_text() == EXISTING_SECRET_NAME, (
                f"Client Secret should display the selected secret's name, "
                f"got: {form.get_client_secret_display_text()!r}"
            )
            assert not form.detail_save_button.is_disabled(), (
                "Save should be enabled once a vault secret has been selected"
            )

        with allure.step("Step 8 — Click Save"):
            # save_and_wait_for_updated() returns only on the PUT's 200; no
            # success toast is rendered on this surface (AFS § Test Steps step 8).
            save_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            assert save_response.get("id") == toolkit_id, (
                f"Save response should reference the same toolkit id, "
                f"got: {save_response.get('id')!r}"
            )
            saved_secret = save_response.get("settings", {}).get("client_secret")
            assert saved_secret == EXPECTED_SECRET_REFERENCE, (
                f"Save response should carry the vault reference under "
                f"settings.client_secret, got: {saved_secret!r}"
            )
            _check_no_new_console_errors("Step 8 (Save)")

        with allure.step("Step 9 — Reload; verify the value persisted in Secret mode"):
            form.reload_and_wait()
            # The configuration section re-collapses on every load.
            form.expand_configuration_section()
            # Secret mode is DERIVED after a reload (SecretField.jsx re-enters it
            # when the stored value matches {{secret.<name>}} AND that name is
            # still in the project vault) — so this assertion covers both the
            # mode and the stored reference being intact.
            expect(form.client_secret_toggle_secret).to_have_attribute(
                "aria-pressed", "true", timeout=UI_TIMEOUT
            )
            expect(form.client_secret_toggle_password).to_have_attribute("aria-pressed", "false")
            expect(form.client_secret_combobox).to_have_text(
                EXISTING_SECRET_NAME, timeout=UI_TIMEOUT
            )
            # The combobox shows only the display NAME; the reference itself is
            # the thing that had to persist — read it from the product's own Raw
            # Json rendering.
            form.switch_to_raw_json_view()
            raw_json = form.get_raw_json_full()
            raw_secret = raw_json.get("settings", {}).get("client_secret")
            assert raw_secret == EXPECTED_SECRET_REFERENCE, (
                f"Raw Json settings.client_secret should carry the vault reference, "
                f"got: {raw_secret!r}"
            )
            _check_no_new_console_errors("Step 9 (reload + Raw Json)")

        if soft_failures:
            pytest.fail(
                "Soft assertion(s) failed (known non-blocking product defect, "
                "not test/infrastructure — rest of the flow passed cleanly):\n"
                + "\n".join(soft_failures)
            )
    finally:
        # Not a case step — teardown for the toolkit seeded above. The vault
        # secret is read-only and is never touched.
        try:
            toolkit_api.delete_toolkit(toolkit_id)
        except Exception:
            logger.warning(
                "Failed to delete seeded MCP toolkit id=%s during cleanup", toolkit_id, exc_info=True
            )
