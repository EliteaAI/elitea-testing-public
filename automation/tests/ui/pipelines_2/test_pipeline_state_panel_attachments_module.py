"""UI test — Pipeline State Panel with Attachments Module.

TMS: ELITEA-2043
(test-specs/pipelines/l2_pipeline-state-panel-attachments-module_ELITEA-2043.md)

Enables the pipeline's "Attachments" MODULES toggle (the same
`agent-canvas-tools-toggle-attachments` switch ELITEA-2059 already documents),
verifies the STATE panel instantly gains an immutable `input_attachments`
(list) variable with a checked toggle and NO delete control (same structural
guarantee ELITEA-2042 documents for the built-in `input`/`messages` rows),
verifies the YAML `state:` section includes `input_attachments` (type: list)
while enabled, disables the module, verifies the variable disappears from the
panel, and verifies the YAML `state:` section reflects the removal — all with
zero Save click and zero network requests (purely client-side formik state,
per the ELITEA-2059 finding for this exact toggle).

Case-text CLARIFICATION (reused, not re-filed): the case's step 3 wording
implies the STATE panel's row visibly shows each variable's type — this is
the SAME already-filed clarification from ELITEA-2042's analysis
(`EliteaAI/elitea-testing-public#1154`); type is asserted via the YAML step
instead, where it genuinely is observable.

No new testids were needed anywhere in this flow — every handle already
existed from ELITEA-2059 (module toggle), ELITEA-2042 (STATE panel rows), and
ELITEA-2026 (Yaml view).
"""

import logging

import allure
import pytest
import yaml
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000

_ATTACHMENTS_VARIABLE = "input_attachments"
_DEFAULT_VARIABLES = ["input", "messages"]


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2043_pipeline-state-panel-with-attachments-module.md",
    "onetest-ai Test Case link",
)
def test_state_panel_attachments_module(page, pipeline_id):
    """Enabling Attachments auto-adds an immutable input_attachments STATE var; disabling removes it."""
    pipeline_page = PipelineDetailPage(page)

    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    api_requests = []
    page.on("request", lambda request: api_requests.append(request.url) if "/api/v2/" in request.url else None)

    with allure.step("Step 1 — Navigate to the pipeline; canvas is displayed"):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.wait_for_canvas()
        assert pipeline_page.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
            "Pipeline detail page should default to the Flow view with the canvas displayed"
        )

    with allure.step(
        'Step 2 — Enable the "Attachments" toggle in MODULES (left panel, TOOLS section); '
        "toggle flips to checked with zero network requests"
    ):
        assert not pipeline_page.is_tools_module_toggle_checked("attachments"), (
            "Attachments MODULES toggle should start unchecked on a fresh pipeline"
        )
        api_requests.clear()
        pipeline_page.toggle_attachments_module(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.is_tools_module_toggle_checked("attachments"), (
            "Attachments MODULES toggle should be checked after clicking it"
        )
        assert not api_requests, (
            f"Toggling the Attachments module on should fire zero API requests (pure client-side "
            f"formik state), got: {api_requests}"
        )

    with allure.step('Step 3 — Click "State" button; the STATE panel opens'):
        pipeline_page.open_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.state_add_variable_button.is_visible(), (
            "STATE panel's '+' add-variable control should be visible once the panel is open"
        )

    with allure.step(
        "Step 4 — STATE panel shows three immutable variables: input, messages, "
        "input_attachments — each with a checked toggle"
    ):
        for variable_name in [*_DEFAULT_VARIABLES, _ATTACHMENTS_VARIABLE]:
            assert pipeline_page.get_state_variable_name_text(variable_name, timeout=UI_ELEMENT_TIMEOUT) == (
                variable_name
            ), f"STATE panel row's name label should read exactly {variable_name!r}"
            assert pipeline_page.is_state_variable_toggle_checked(variable_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Variable {variable_name!r}'s toggle should be checked"
            )

    with allure.step(
        f"Step 5 — Verify {_ATTACHMENTS_VARIABLE!r} was auto-added when Attachments was enabled: "
        "no delete button (immutable)"
    ):
        assert not pipeline_page.is_state_variable_delete_button_present(_ATTACHMENTS_VARIABLE), (
            f"Auto-added variable {_ATTACHMENTS_VARIABLE!r} should render NO delete control "
            "(same structural immutability guarantee as the built-in input/messages rows)"
        )

    with allure.step(
        f"Step 6 — While Attachments is enabled, verify in Yaml view that the state section "
        f"includes {_ATTACHMENTS_VARIABLE!r} (type: list)"
    ):
        pipeline_page.close_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.switch_to_yaml_view()
        pipeline_page.yaml_editor.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        yaml_text_enabled = pipeline_page.get_yaml_content()
        parsed_enabled = yaml.safe_load(yaml_text_enabled)
        state_section_enabled = parsed_enabled.get("state") or {}

        attachments_entry = state_section_enabled.get(_ATTACHMENTS_VARIABLE, {})
        assert _ATTACHMENTS_VARIABLE in state_section_enabled, (
            f"YAML state section should include {_ATTACHMENTS_VARIABLE!r} while Attachments is "
            f"enabled, got state keys: {list(state_section_enabled.keys())!r}"
        )
        assert attachments_entry.get("type") == "list", (
            f"YAML state.{_ATTACHMENTS_VARIABLE}.type should be 'list', got: {attachments_entry!r}"
        )

        pipeline_page.switch_to_flow_view()
        pipeline_page.wait_for_canvas()
        pipeline_page.open_state_panel(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        'Step 7 — Disable the "Attachments" toggle in MODULES; toggle flips to unchecked '
        "with zero network requests"
    ):
        api_requests.clear()
        pipeline_page.toggle_attachments_module(timeout=UI_ELEMENT_TIMEOUT)
        assert not pipeline_page.is_tools_module_toggle_checked("attachments"), (
            "Attachments MODULES toggle should be unchecked after clicking it again"
        )
        assert not api_requests, (
            f"Toggling the Attachments module off should fire zero API requests, got: {api_requests}"
        )

    with allure.step(f"Step 8 — Verify {_ATTACHMENTS_VARIABLE!r} is removed from the STATE panel"):
        for variable_name in _DEFAULT_VARIABLES:
            assert pipeline_page.get_state_variable_name_text(variable_name, timeout=UI_ELEMENT_TIMEOUT) == (
                variable_name
            ), f"Default row {variable_name!r} should still be present after disabling Attachments"
        assert not pipeline_page.is_state_variable_present(_ATTACHMENTS_VARIABLE), (
            f"{_ATTACHMENTS_VARIABLE!r} row should no longer appear in the STATE panel list "
            "after disabling Attachments"
        )

    with allure.step(
        "Step 9 — Verify in Yaml view that the state section does not include input_attachments"
    ):
        pipeline_page.close_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.switch_to_yaml_view()
        pipeline_page.yaml_editor.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        yaml_text = pipeline_page.get_yaml_content()
        parsed = yaml.safe_load(yaml_text)
        state_section = parsed.get("state") or {}

        assert _ATTACHMENTS_VARIABLE not in state_section, (
            f"YAML state section should NOT include {_ATTACHMENTS_VARIABLE!r} after disabling "
            f"Attachments, got state keys: {list(state_section.keys())!r}"
        )

        pipeline_page.switch_to_flow_view()
        pipeline_page.wait_for_canvas()

    with allure.step("Step 10 — No console errors were introduced at any step"):
        assert not console_errors, f"No step should introduce console errors: {console_errors}"
