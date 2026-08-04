"""UI test — Pipeline State Panel: Default and Custom Variables.

TMS: ELITEA-2042
(test-specs/pipelines/l2_pipeline-state-panel-default-and-custom-variables_ELITEA-2042.md)

Opens the STATE side panel on a fresh pipeline, verifies the two default
immutable variables (`input`/`messages`) render name + a checked toggle with
NO delete control (a structural guarantee, not just an observation — see
below), adds a custom `custom_output` variable via the panel's "+" control,
verifies the type-selector dropdown's exact 4 options (String/Number/List/
Json), keeps the type as String, saves, verifies the YAML `state:` section,
and confirms `custom_output` is selectable in an LLM node's Input combobox.

Case-text CLARIFICATION (AFS Coverage Map / Known Defects Found During
Exploration, filed as `EliteaAI/elitea-testing-public#1154`, not a defect):
the case's step 4 wording ("input (str, toggle on)") implies the panel's
collapsed row visibly shows each variable's TYPE — live UI (and source,
`StateVariableItem.jsx`/`StateVariableItemActions.jsx`) renders ONLY the
name + toggle on default rows, no type indicator at all. This test asserts
what's actually visible on the row (name + checked toggle + structural
no-delete) and defers the type assertion to the YAML step, where it's
genuinely observable.

Testids for the STATE panel's per-row controls (name label, toggle, delete,
type-select button, and the type dropdown's 4 menu items) did not exist
before this case and were added via `add-data-testid`,
EliteaAI/EliteaUI@d120871f.
"""

import logging

import allure
import pytest
import yaml
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p1, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

_CUSTOM_VARIABLE_NAME = "custom_output"
_DEFAULT_VARIABLES = ["input", "messages"]
_EXPECTED_TYPE_OPTIONS = ["String", "Number", "List", "Json"]


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2042_pipeline-state-panel-default-and-custom-variables.md",
    "onetest-ai Test Case link",
)
def test_state_panel_default_and_custom_variables(page, pipeline_id):
    """STATE panel: default vars are immutable, a custom var can be added/typed and is usable downstream."""
    project_id = str(settings.elitea_project_id)
    pipeline_page = PipelineDetailPage(page)

    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Navigate to the pipeline; canvas is displayed"):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.wait_for_canvas()
        assert pipeline_page.is_flow_view_active(timeout=UI_ELEMENT_TIMEOUT), (
            "Pipeline detail page should default to the Flow view with the canvas displayed"
        )

    with allure.step("Step 2 — Click the 'State' button; the STATE panel opens"):
        pipeline_page.open_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.state_add_variable_button.is_visible(), (
            "STATE panel's '+' add-variable control should be visible once the panel is open"
        )

    with allure.step("Step 3 — STATE panel shows a close (X) button"):
        assert pipeline_page.state_drawer_close_button.is_visible(), (
            "STATE panel should render a close ('x') button"
        )

    with allure.step(
        "Step 4 — Default variables 'input'/'messages' are listed, each with a checked "
        "toggle and NO delete control"
    ):
        for variable_name in _DEFAULT_VARIABLES:
            assert pipeline_page.get_state_variable_name_text(variable_name, timeout=UI_ELEMENT_TIMEOUT) == (
                variable_name
            ), f"Default row's name label should read exactly {variable_name!r}"
            assert pipeline_page.is_state_variable_toggle_checked(variable_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Default variable {variable_name!r}'s toggle should be checked"
            )
            assert not pipeline_page.is_state_variable_delete_button_present(variable_name), (
                f"Default variable {variable_name!r} should render NO delete control "
                "(structural guarantee — StateVariableItemActions.jsx's showToggle branch)"
            )

    with allure.step("Step 5 — Click '+' to add a new state variable; a name input appears"):
        pipeline_page.state_add_variable_button.click(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.state_add_variable_name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.state_add_variable_name_input.is_visible(), (
            "STATE panel's new-variable name input should appear inline"
        )

    with allure.step(f"Step 6 — Enter variable name {_CUSTOM_VARIABLE_NAME!r} and commit via Enter"):
        pipeline_page.state_add_variable_name_input.click()
        pipeline_page.state_add_variable_name_input.press_sequentially(_CUSTOM_VARIABLE_NAME, delay=20)
        pipeline_page.state_add_variable_name_input.press("Enter")
        pipeline_page.state_add_variable_name_input.wait_for(state="detached", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_state_variable_name_text(_CUSTOM_VARIABLE_NAME, timeout=UI_ELEMENT_TIMEOUT) == (
            _CUSTOM_VARIABLE_NAME
        ), f"Committed row's name label should read exactly {_CUSTOM_VARIABLE_NAME!r}"

    with allure.step(
        "Step 7 — Click the type button (default 'Abc'/String); dropdown shows exactly "
        "String/Number/List/Json"
    ):
        pipeline_page.click_state_variable_type_select(_CUSTOM_VARIABLE_NAME, timeout=UI_ELEMENT_TIMEOUT)
        type_options = pipeline_page.get_state_type_dropdown_options(timeout=UI_ELEMENT_TIMEOUT)
        assert type_options == _EXPECTED_TYPE_OPTIONS, (
            f"Type dropdown should show exactly {_EXPECTED_TYPE_OPTIONS!r} in order, got {type_options!r}"
        )

    with allure.step("Step 8 — Select String (keep the pre-selected type); verify String type is retained"):
        pipeline_page.select_open_state_type_option("str", timeout=UI_ELEMENT_TIMEOUT)
        # Re-open the dropdown to assert the row's type actually stayed on String
        # ("str") after the selection — StateTypeSelector.jsx marks the
        # currently-selected MenuItem with MUI's `selected` prop (Mui-selected
        # class); re-select the same option afterward to close the dropdown
        # again without changing the row's type.
        pipeline_page.click_state_variable_type_select(_CUSTOM_VARIABLE_NAME, timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.is_state_type_option_selected("str", timeout=UI_ELEMENT_TIMEOUT), (
            "Type dropdown should show String ('str') as the selected option after selection"
        )
        pipeline_page.select_open_state_type_option("str", timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(f"Step 9 — Verify {_CUSTOM_VARIABLE_NAME!r} appears in the STATE panel list"):
        assert pipeline_page.get_state_variable_name_text(_CUSTOM_VARIABLE_NAME, timeout=UI_ELEMENT_TIMEOUT) == (
            _CUSTOM_VARIABLE_NAME
        ), f"{_CUSTOM_VARIABLE_NAME!r} row should remain visible in the STATE panel list"
        for variable_name in _DEFAULT_VARIABLES:
            assert pipeline_page.get_state_variable_name_text(variable_name, timeout=UI_ELEMENT_TIMEOUT) == (
                variable_name
            ), f"Default row {variable_name!r} should still be present alongside the new custom variable"

    with allure.step("Step 10 — Save the pipeline; verify no console errors and a 201 Created response"):
        pipeline_page.close_state_panel(timeout=UI_ELEMENT_TIMEOUT)
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"
        assert not console_errors, f"Save should not introduce console errors: {console_errors}"

    with allure.step(
        "Step 11 — Switch to Yaml view; the 'state:' section lists input (str), "
        "messages (list), custom_output (str, value '')"
    ):
        pipeline_page.switch_to_yaml_view()
        pipeline_page.yaml_editor.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        yaml_text = pipeline_page.get_yaml_content()
        parsed = yaml.safe_load(yaml_text)
        state_section = parsed.get("state") or {}

        assert state_section.get("input", {}).get("type") == "str", (
            f"YAML state.input.type should be 'str', got: {state_section.get('input')!r}"
        )
        assert state_section.get("messages", {}).get("type") == "list", (
            f"YAML state.messages.type should be 'list', got: {state_section.get('messages')!r}"
        )
        custom_output_entry = state_section.get(_CUSTOM_VARIABLE_NAME, {})
        assert custom_output_entry.get("type") == "str", (
            f"YAML state.{_CUSTOM_VARIABLE_NAME}.type should be 'str', got: {custom_output_entry!r}"
        )
        assert custom_output_entry.get("value") == "", (
            f"YAML state.{_CUSTOM_VARIABLE_NAME}.value should be '', got: {custom_output_entry!r}"
        )

        pipeline_page.switch_to_flow_view()
        pipeline_page.wait_for_canvas()

    with allure.step(
        f"Step 12 — Verify {_CUSTOM_VARIABLE_NAME!r} is available in a node's Input combobox"
    ):
        pipeline_page.add_node_button.click(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.select_add_node_menu_item("llm", timeout=UI_ELEMENT_TIMEOUT)
        llm_node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        assert llm_node_id, "LLM node should appear on canvas with a non-empty data-id"

        pipeline_page.open_llm_node_input_select(timeout=UI_ELEMENT_TIMEOUT)
        option_testids = set(pipeline_page.get_open_listbox_option_testids())
        expected_option_testids = {
            "select-option-input",
            "select-option-messages",
            f"select-option-{_CUSTOM_VARIABLE_NAME}",
        }
        assert option_testids == expected_option_testids, (
            f"LLM node's Input select should offer exactly {expected_option_testids!r}, got {option_testids!r}"
        )
        assert not console_errors, f"No step should introduce console errors: {console_errors}"
