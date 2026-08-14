"""UI test — Pipeline: Information Section.

TMS: ELITEA-2056
(test-specs/pipelines/l2_pipeline-information-section_ELITEA-2056.md)

Verifies the Information section displays the Pipeline ID, Version ID,
Trigger type, and Pipeline "Show" link, and that the Copy ID / Copy Version ID
buttons produce both a success toast and the correct clipboard content.

Clicking "Show" does NOT navigate anywhere (case-text drift from live
product, see the AFS's Known Defects / clarification section) — it opens a
modal rendering the pipeline as a Mermaid diagram. Opening that modal on a
single-node pipeline deterministically throws a console error from
svg-pan-zoom's resetZoom (filed
https://github.com/EliteaAI/elitea-testing-public/issues/1368, sibling of
#1045) — soft-asserted here per # Known defect, the modal/diagram assertions
themselves are NOT masked.
"""

import logging

import allure
import pytest

from tests.ui.pipelines.helpers import _navigate_to_detail

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
TOAST_TIMEOUT = 10_000
COPY_ID_TOAST_TEXT = "The ID has been copied to the clipboard."
COPY_VERSION_ID_TOAST_TEXT = "The Version ID has been copied to the clipboard."
EXPECTED_TRIGGER_TEXT = "Trigger:Chat Message"

# Known defect: https://github.com/EliteaAI/elitea-testing-public/issues/1368
# (sibling of #1045) — svg-pan-zoom's resetZoom throws an uncaught
# InvalidStateError on a single-node pipeline's Mermaid preview. Filtered
# from the console-error check the same way test_pipeline_entry_point_
# trigger_types_persist.py filters the pre-existing #1021 react-js-cron
# noise — background noise from a filed, tracked defect, not this case's
# own flow.
_KNOWN_1368_ERROR_SNIPPET = "Failed to execute 'inverse' on 'SVGMatrix'"


def _is_known_1368_error(msg) -> bool:
    """Filter the svg-pan-zoom InvalidStateError filed as issue #1368."""
    return _KNOWN_1368_ERROR_SNIPPET in msg.text


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2056_pipeline-information-section.md",
    "onetest-ai Test Case link",
)
def test_pipeline_information_section(page, pipeline_with_llm_id):
    """Information section — Pipeline ID/Version ID/Trigger/Show link + copy buttons."""
    console_errors = []
    page.on(
        "console",
        lambda msg: console_errors.append(msg)
        if msg.type == "error" and not _is_known_1368_error(msg)
        else None,
    )

    with allure.step("Step 1 — Open an existing pipeline; it loads in the editor"):
        pipeline_page = _navigate_to_detail(page, pipeline_with_llm_id)
        assert pipeline_page.canvas_wrapper.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
            "Pipeline should load in the editor (canvas visible) after navigation"
        )

    with allure.step('Step 2 — Expand "Information" section in left panel'):
        assert pipeline_page.information_section.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
            "Information section should be visible (expanded by default on a "
            "freshly opened pipeline detail page)"
        )

    with allure.step('Step 3 — Verify "Pipeline ID:" is shown with a numeric Copy ID button'):
        assert pipeline_page.copy_id_button.is_visible(), "Copy ID button should be visible"
        pipeline_id_text = pipeline_page.get_pipeline_id()
        assert pipeline_id_text == str(pipeline_with_llm_id), (
            f"Pipeline ID text should be {pipeline_with_llm_id!r}, got {pipeline_id_text!r}"
        )

    with allure.step('Step 4 — Verify "Version ID:" is shown with a numeric Copy version ID button'):
        assert pipeline_page.copy_version_id_button.is_visible(), (
            "Copy version ID button should be visible"
        )
        version_id_text = pipeline_page.get_version_id()
        assert version_id_text.isdigit(), f"Version ID should be numeric, got {version_id_text!r}"

    with allure.step('Step 5 — Verify "Trigger:" shows the trigger type ("Chat Message")'):
        assert pipeline_page.information_trigger_row.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
            "Information section's Trigger row should be visible"
        )
        # DOM textContent concatenates label+value with no literal space —
        # the visual gap is CSS flex `gap`, not a text character (same
        # live-contract shape ELITEA-2041 already documented).
        trigger_text = pipeline_page.information_trigger_row.text_content()
        assert trigger_text == EXPECTED_TRIGGER_TEXT, (
            f"Trigger row text should be {EXPECTED_TRIGGER_TEXT!r}, got {trigger_text!r}"
        )

    with allure.step('Step 6 — Verify "Pipeline:" shows a "Show" link'):
        assert pipeline_page.information_show_link.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
            'Information section\'s "Show" link should be visible'
        )
        show_link_text = pipeline_page.information_show_link.text_content()
        assert show_link_text.strip() == "Show", f"Show link text should be 'Show', got {show_link_text!r}"

    with allure.step('Step 7 — Click "Copy ID"; verify toast feedback and clipboard content'):
        pipeline_page.copy_id_button.click()
        toast_alert = pipeline_page.get_toast_alert("info")
        toast_alert.wait_for(state="visible", timeout=TOAST_TIMEOUT)
        toast_text = pipeline_page.get_toast_text(timeout=TOAST_TIMEOUT)
        assert COPY_ID_TOAST_TEXT in toast_text, (
            f"Copy ID toast should confirm the clipboard copy, got: {toast_text!r}"
        )
        clipboard_text = page.evaluate("navigator.clipboard.readText()")
        assert clipboard_text == pipeline_id_text, (
            f"Clipboard should contain the pipeline id {pipeline_id_text!r}, got {clipboard_text!r}"
        )

    with allure.step('Step 8 — Click "Copy version ID"; verify toast feedback and clipboard content'):
        pipeline_page.copy_version_id_button.click()
        toast_alert = pipeline_page.get_toast_alert("info")
        toast_alert.wait_for(state="visible", timeout=TOAST_TIMEOUT)
        toast_text = pipeline_page.get_toast_text(timeout=TOAST_TIMEOUT)
        assert COPY_VERSION_ID_TOAST_TEXT in toast_text, (
            f"Copy version ID toast should confirm the clipboard copy, got: {toast_text!r}"
        )
        clipboard_text = page.evaluate("navigator.clipboard.readText()")
        assert clipboard_text == version_id_text, (
            f"Clipboard should contain the version id {version_id_text!r}, got {clipboard_text!r}"
        )

    with allure.step(
        'Step 9 — Click "Show" link; verify it opens the pipeline\'s visual (Mermaid) representation'
    ):
        # Live-contract correction (reverse-masking guard): the case text says
        # "navigates to pipeline YAML or visual representation" — the product
        # does NOT navigate (no URL change); it opens a modal with the
        # "visual representation" branch of that either/or wording. Assert
        # the modal + diagram, not a navigation.
        pipeline_page.click_information_show_link(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.show_context_diagram_container.is_visible(), (
            "Show-link modal should render the pipeline as a Mermaid diagram"
        )
        node_count = pipeline_page.get_diagram_node_count()
        assert node_count >= 1, "Mermaid diagram should render at least one node"

        # Side-channel check across the whole flow (Axis 2 addition, AFS
        # § Coverage Map): zero UNEXPECTED console errors — the deterministic
        # #1368 defect is filtered above, not masked (the modal/diagram
        # assertions above are unaffected either way).
        assert not console_errors, (
            f"No unexpected console errors should occur (known defect #1368 filtered): "
            f"{[e.text for e in console_errors]}"
        )
