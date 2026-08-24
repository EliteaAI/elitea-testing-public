"""UI test — Remote MCP detail page: Timeout / Cache TTL configuration.

TMS: ELITEA-1956 (Timeout, 300 -> 60), ELITEA-1957 (Cache TTL, 300 -> 600)
AFS: test-specs/mcp/l2_remote-mcp-timeout-and-cache-ttl-configuration_ELITEA-1956-1957.md
     (FAMILY AFS — both cases are pure DATA variants of ONE flow, so they are
     ONE parameterized test, one row per TMS case, each row asserting its OWN
     expected values: its own field, its own new value, its own Raw-Json key
     and its own sibling field that must stay untouched.)

The flow, per row: seed a Remote MCP, open its detail page in Form view, expand
the configuration section, verify the field's default 300 and its info icon,
type the new value, Save, reload, verify persistence, verify the value in the
Raw Json view, then restore 300 and save again.

Declared substitution: NONE. Every asserted observable is produced by the live
system — the create/update PUT responses, the rendered input values and the
Raw Json document the product itself renders.

Case-text clarification (both cases, filed as #1745, NOT a defect and NOT red):
the case texts print the Raw-Json entry as a bare number (`"timeout": 60`),
while the product persists a UI-typed value as a JSON STRING ("60"). An
untouched default stays numeric (300). The case's real requirement — "the JSON
reflects the new value" — is asserted via ``str(...)``, plus an explicit
``isinstance(..., str)`` so a silent product change of the persisted type is
caught rather than absorbed. Same shape as the merged
``test_mcp_create_remote.py`` assertions on these two very fields.
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

pytestmark = [
    pytest.mark.ui,
    pytest.mark.toolkits,
    pytest.mark.p2,
    pytest.mark.regression,
    pytest.mark.new,
]

TOOLKIT_URL = "https://mcp.example.com/sse"
# Both fields ship the same schema default; it is also the value Step 8
# restores, so the seeded MCP is left in its documented state.
DEFAULT_VALUE = "300"


def _unique(base: str) -> str:
    """Toolkit Name is silently truncated at MAX_NAME_LENGTH=32 — keep it short."""
    return f"{base}_{uuid.uuid4().hex[:6]}"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1956_remote-mcp-timeout-configuration.md",
    "onetest-ai Test Case link — ELITEA-1956",
)
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1957_remote-mcp-cache-ttl-configuration.md",
    "onetest-ai Test Case link — ELITEA-1957",
)
@pytest.mark.mcp
@pytest.mark.parametrize(
    (
        "field_label",
        "json_key",
        "input_locator_name",
        "info_icon_locator_name",
        "fill_method_name",
        "new_value",
        "sibling_json_key",
        "sibling_input_locator_name",
    ),
    [
        pytest.param(
            "Timeout",
            "timeout",
            "timeout_input",
            "timeout_info_icon",
            "fill_timeout",
            "60",
            "cache_ttl",
            "cache_ttl_input",
            id="ELITEA-1956",
        ),
        pytest.param(
            "Cache TTL",
            "cache_ttl",
            "cache_ttl_input",
            "cache_ttl_info_icon",
            "fill_cache_ttl",
            "600",
            "timeout",
            "timeout_input",
            id="ELITEA-1957",
        ),
    ],
)
def test_mcp_edit_timeout_cache_ttl(
    page,
    toolkit_api: ToolkitAPI,
    field_label: str,
    json_key: str,
    input_locator_name: str,
    info_icon_locator_name: str,
    fill_method_name: str,
    new_value: str,
    sibling_json_key: str,
    sibling_input_locator_name: str,
):
    """A Remote MCP's numeric config field can be changed, saved, persisted and restored."""
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)

    # Locators are page-object class fields; the parameter row selects WHICH
    # field by name rather than constructing anything here (locators never live
    # in spec files — .agents/testing.md § Locator policy).
    field_input = getattr(form, input_locator_name)
    info_icon = getattr(form, info_icon_locator_name)
    fill_field = getattr(form, fill_method_name)
    sibling_input = getattr(form, sibling_input_locator_name)

    # ------------------------------------------------------------------
    # Console listener — same split-filter shape as the merged ELITEA-1929
    # spec: the two pre-existing React dev-mode warnings tracked in #291 are
    # filtered at capture time, the known MUI-Tabs warning (#549) is collected
    # as a soft failure so it stays visible without blocking the flow, and
    # anything else is a genuinely new, hard-failing regression.
    # ------------------------------------------------------------------
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
        new_549 = [m for m in console_messages if _is_known_549_warning(m)]
        unexpected = [m for m in console_messages if not _is_known_549_warning(m)]
        for msg in new_549:
            soft_failures.append(
                "Known defect github.com/EliteaAI/elitea-testing-public/issues/549: "
                f"{step_label} — MUI Tabs invalid-value console error: {msg.text!r}"
            )
        assert not unexpected, (
            f"{step_label} — unexpected new console errors beyond the pre-existing "
            "dev-mode warnings tracked in #291 and the known #549 Tabs warning, got: "
            f"{[m.text for m in unexpected]}"
        )
        console_messages.clear()

    # ------------------------------------------------------------------
    # Setup — NOT a case step. Materialises the precondition "an existing
    # Remote MCP whose Timeout and Cache TTL are still at their defaults":
    # this family's first assertion is "the field shows 300", which a
    # previously-edited leftover toolkit would silently invalidate.
    # ToolkitAPI.list_all_toolkits() returns [] on this environment regardless
    # of auth method (documented quirk), so the UI create flow is the stable
    # seeding path — same precedent as ELITEA-1929.
    # ------------------------------------------------------------------
    toolkit_name = _unique("autotest_mcp_ttl")
    form.navigate_to_create()
    form.select_remote_mcp_type()
    form.fill_name(toolkit_name)
    form.fill_url(TOOLKIT_URL)
    create_response = form.save_and_wait_for_created(project_id)
    toolkit_id = create_response["id"]

    try:
        with allure.step("Step 1 — Open the Remote MCP detail page in Form view"):
            form.navigate_to_detail(toolkit_id, project_id)
            assert f"/mcps/all/{toolkit_id}" in page.url, (
                f"Expected the MCP detail URL, got: {page.url}"
            )
            expect(form.detail_title).to_have_text(toolkit_name)
            assert form.form_view_toggle.get_attribute("aria-pressed") == "true", (
                "Detail page should load in Form view"
            )
            # Hard precondition of every step below: no `toolkit-field-*`
            # element exists in the DOM until the configuration section is
            # expanded (and the toggle itself mounts ~1s late).
            form.expand_configuration_section()

        with allure.step(f'Step 2 — Verify "{field_label}" shows its default {DEFAULT_VALUE}'):
            # Assert the VALUE, never the placeholder: the element also carries
            # placeholder="300" (schema default), so a genuinely empty field
            # would pass a placeholder-based check.
            assert field_input.input_value() == DEFAULT_VALUE, (
                f"{field_label} should default to {DEFAULT_VALUE}, "
                f"got: {field_input.input_value()!r}"
            )

        with allure.step(f'Step 3 — Verify the info icon is present next to "{field_label}"'):
            expect(info_icon).to_be_visible()

        with allure.step(f'Step 4 — Change "{field_label}" to {new_value}'):
            # Axis 2: the pristine detail page's Save is disabled; the edit is
            # what enables it. Asserting the dirty gate makes the case's
            # "Save MCP" precondition explicit and catches a dead-Save
            # regression.
            expect(form.detail_save_button).to_be_disabled()
            fill_field(new_value)
            assert field_input.input_value() == new_value, (
                f"{field_label} should display {new_value} after typing, "
                f"got: {field_input.input_value()!r}"
            )
            expect(form.detail_save_button).to_be_enabled()

        with allure.step("Step 5 — Save the MCP"):
            # The MCP detail Save renders NO success toast (confirmed live,
            # AFS Step 5) — the PUT 200 and its persisted body are the
            # operation-completed observable. save_and_wait_for_updated()
            # only returns on a matching 200 response.
            save_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            assert str(save_response["settings"][json_key]) == new_value, (
                f"Save response should carry settings.{json_key} == {new_value}, "
                f"got: {save_response['settings'][json_key]!r}"
            )
            _check_no_new_console_errors("Step 5 (Save)")

        with allure.step(
            f'Step 6 — Reload; verify "{field_label}" still shows {new_value}'
        ):
            form.reload_and_wait()
            # The configuration section re-collapses on every reload.
            form.expand_configuration_section()
            assert field_input.input_value() == new_value, (
                f"{field_label} should still show {new_value} after a full page reload "
                f"(server-side persistence, not client state), got: "
                f"{field_input.input_value()!r}"
            )
            # Axis 2: both fields live in one `settings` object saved by one
            # PUT — a serializer bug clobbering the neighbour would otherwise
            # pass this case silently.
            assert sibling_input.input_value() == DEFAULT_VALUE, (
                f"The sibling field {sibling_json_key} should be untouched at "
                f"{DEFAULT_VALUE}, got: {sibling_input.input_value()!r}"
            )

        with allure.step(f'Step 7 — Switch to Raw Json; verify "{json_key}": {new_value}'):
            form.switch_to_raw_json_view()
            # get_raw_json() (non-_full) reads a CodeMirror-virtualized,
            # truncated document on a payload this size.
            raw_settings = form.get_raw_json_full()["settings"]
            assert str(raw_settings[json_key]) == new_value, (
                f"Raw Json settings.{json_key} should reflect {new_value}, "
                f"got: {raw_settings[json_key]!r}"
            )
            # Clarification #1745: a UI-typed value persists as a JSON STRING
            # while the case text prints a bare number. Pin the observed shape
            # so a silent product change of the stored type is caught.
            assert isinstance(raw_settings[json_key], str), (
                f"settings.{json_key} is expected to persist as a JSON string "
                f"(clarification #1745), got: {type(raw_settings[json_key]).__name__}"
            )
            assert str(raw_settings[sibling_json_key]) == DEFAULT_VALUE, (
                f"Raw Json settings.{sibling_json_key} should be untouched at "
                f"{DEFAULT_VALUE}, got: {raw_settings[sibling_json_key]!r}"
            )
            _check_no_new_console_errors("Step 7 (Raw Json)")

        with allure.step(
            f'Step 8 — Restore "{field_label}" to {DEFAULT_VALUE} and save'
        ):
            # ELITEA-1956 carries this as its own case step 8; for ELITEA-1957
            # it is Axis-2 coverage doubling as state restoration (the field is
            # freely re-editable in both directions, and the seeded MCP returns
            # to its documented default before teardown).
            form.switch_to_form_view()
            form.expand_configuration_section()
            fill_field(DEFAULT_VALUE)
            restore_response = form.save_and_wait_for_updated(project_id, toolkit_id)
            assert str(restore_response["settings"][json_key]) == DEFAULT_VALUE, (
                f"Restore response should carry settings.{json_key} == {DEFAULT_VALUE}, "
                f"got: {restore_response['settings'][json_key]!r}"
            )
            _check_no_new_console_errors("Step 8 (restore + Save)")

        if soft_failures:
            pytest.fail(
                "Soft assertion(s) failed (known non-blocking product defect, not "
                "test/infrastructure — rest of the flow passed cleanly):\n"
                + "\n".join(soft_failures)
            )
    finally:
        # Not a case step — teardown for the toolkit seeded above.
        try:
            toolkit_api.delete_toolkit(toolkit_id)
        except Exception:
            logger.warning(
                "Failed to delete seeded MCP toolkit id=%s during cleanup",
                toolkit_id,
                exc_info=True,
            )
