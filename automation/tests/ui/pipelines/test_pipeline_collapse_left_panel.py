"""UI test — Pipeline: Collapse Left Panel.

TMS: ELITEA-2072
(test-specs/pipelines/l2_pipeline-collapse-left-panel_ELITEA-2072.md)

Seeds a pipeline via the existing ``pipeline_llm_code_end`` fixture (any
already-proven pipeline satisfies this case's precondition — it makes no
assertion about node type/count), then:
1. Confirms the left configuration panel loads expanded (320px) with its
   collapse toggle button visible.
2. Clicks the toggle -> asserts the panel's rendered width strictly
   decreases AND every configuration section (Tools/Advanced/Editor
   Notes/Information) unmounts from the DOM (``to_have_count(0)``).
3. Asserts the canvas area's rendered width grows to fill the freed space.
4. Clicks the same toggle again -> asserts the panel returns to its EXACT
   original width and every section remounts (visible again).

Collapse/expand is a pure client-side ``useState`` toggle (confirmed live via
source read of ``GeneralFormPanel.jsx`` and a live browser probe — no XHR/
fetch fires for either click) — the test asserts zero console errors and
zero pipeline-persist network requests across the whole sequence, same
"pure client-side operation" class as the canvas zoom/pan/control-panel
cases in this suite (ELITEA-2019/2057).
"""

import allure
import pytest

from tests.ui.pipelines.helpers import _navigate_to_canvas

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
# Pipeline persist/fetch endpoints all share this segment — see the canvas
# zoom/pan test's identical constant for the full rationale.
PIPELINE_NETWORK_SUBSTRING = "prompt_lib"

# Configuration-section attribute names (Tools / Advanced / Editor Notes /
# Information) — all pre-existing LocatorDescriptor fields on PipelineDetailPage.
CONFIG_SECTION_ATTRS = [
    "toolkits_section",
    "step_limit_input",
    "editor_notes_section",
    "information_section",
]


def _config_sections(pipeline_page):
    """Yield the pipeline detail page's four configuration-section locators."""
    for attr in CONFIG_SECTION_ATTRS:
        yield attr, getattr(pipeline_page, attr)


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2072_pipeline-collapse-left-panel.md",
    "onetest-ai Test Case link",
)
def test_collapse_and_expand_left_configuration_panel(page, pipeline_llm_code_end):
    """Collapsing the left configuration panel shrinks it and unmounts its
    sections while the canvas grows; expanding it again restores the exact
    original width and remounts every section."""
    with allure.step("Step 1 — Navigate to the pipeline's canvas, verify the left panel is fully visible"):
        pipeline_page = _navigate_to_canvas(page, pipeline_llm_code_end)

        baseline_panel_width = pipeline_page.get_config_panel_width(timeout=UI_ELEMENT_TIMEOUT)
        assert baseline_panel_width == pytest.approx(320, abs=2.0), (
            f"Left configuration panel should load fully expanded (~320px), got {baseline_panel_width:.1f}px"
        )
        pipeline_page.config_panel_collapse_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

        for name, locator in _config_sections(pipeline_page):
            assert locator.first.is_visible(), f"Configuration section {name!r} should be visible before any collapse"

        baseline_canvas_width = pipeline_page.canvas_wrapper.bounding_box(timeout=UI_ELEMENT_TIMEOUT)["width"]

        # Registered right after the step-1 baseline (not before) so the
        # canvas's own initial-load fetch isn't counted — collapse/expand is
        # a pure client-side toggle (AFS Network Behavior) and must fire
        # neither console errors nor pipeline network requests.
        console_errors = pipeline_page.capture_console_errors()
        toggle_requests = pipeline_page.capture_requests_matching(PIPELINE_NETWORK_SUBSTRING)

    with allure.step(
        "Step 3/4 — Click the collapse button, verify the panel shrinks and its sections unmount"
    ):
        pipeline_page.toggle_config_panel_collapse(timeout=UI_ELEMENT_TIMEOUT)

        collapsed_panel_width = pipeline_page.get_config_panel_width(timeout=UI_ELEMENT_TIMEOUT)
        assert collapsed_panel_width < baseline_panel_width, (
            f"Panel width should strictly decrease after collapsing: "
            f"{baseline_panel_width:.1f}px -> {collapsed_panel_width:.1f}px"
        )

        for name, locator in _config_sections(pipeline_page):
            assert locator.count() == 0, (
                f"Configuration section {name!r} should be unmounted (count 0) while the panel is collapsed"
            )
        assert not console_errors, f"Collapsing the panel should not introduce console errors: {list(console_errors)}"
        assert not toggle_requests, (
            "Collapsing the panel is a pure client-side toggle — expected zero "
            f"pipeline network requests, got: {list(toggle_requests)}"
        )

    with allure.step("Step 5 — Verify the canvas area expands to fill the freed space"):
        collapsed_canvas_width = pipeline_page.canvas_wrapper.bounding_box(timeout=UI_ELEMENT_TIMEOUT)["width"]
        assert collapsed_canvas_width > baseline_canvas_width, (
            f"Canvas area should grow once the left panel collapses: "
            f"{baseline_canvas_width:.1f}px -> {collapsed_canvas_width:.1f}px"
        )

    with allure.step(
        "Step 6/7 — Click the toggle again, verify the panel restores its exact width and sections remount"
    ):
        pipeline_page.toggle_config_panel_collapse(timeout=UI_ELEMENT_TIMEOUT)

        restored_panel_width = pipeline_page.get_config_panel_width(timeout=UI_ELEMENT_TIMEOUT)
        assert restored_panel_width == pytest.approx(baseline_panel_width, abs=1.0), (
            f"Panel width should restore its exact original value: "
            f"{baseline_panel_width:.1f}px -> {restored_panel_width:.1f}px"
        )

        for name, locator in _config_sections(pipeline_page):
            assert locator.first.is_visible(), f"Configuration section {name!r} should be visible again after expanding the panel"
        assert not console_errors, f"Expanding the panel should not introduce console errors: {list(console_errors)}"
        assert not toggle_requests, (
            "Expanding the panel is a pure client-side toggle — expected zero "
            f"pipeline network requests, got: {list(toggle_requests)}"
        )
        console_errors.stop()
        toggle_requests.stop()
