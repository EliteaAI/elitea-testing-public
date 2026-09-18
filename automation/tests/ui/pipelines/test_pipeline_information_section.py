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
#1045) — filtered from the console-error axis per # Known defect, the
modal/diagram assertions themselves are NOT masked.

Known defect #2367 (https://github.com/EliteaAI/elitea-testing-public/issues/2367,
found via [FIX] card #2366, DEV Stable run #185): the same modal
INTERMITTENTLY renders Mermaid's "Syntax error in text" bomb instead of the
diagram — EliteaUI ``DiagramOutput.jsx`` runs ``initialize({startOnLoad:
true})`` + ``contentLoaded()`` (→ ``mermaid.run()`` over its own ``.mermaid``
container) alongside its explicit ``m.render``; whichever render lands last
wins, and on a cold page (first mermaid import in the document — every fresh
browser context, i.e. every CI attempt) ``run()`` lands last ~1 in 4 opens and
wipes the SVG. Measured 5/22 cold opens on DEV, 2/8 on a pipeline created via
the UI, so it is the product, not this test's API-seeded fixture (whose YAML
is byte-identical to what the UI authors). Step 9 keeps asserting the CORRECT
expected behaviour (diagram nodes rendered, no error bomb) as ``expect.soft()``
with ``# Known defect: #2367`` so the Axis-2 console check still runs and the
red stays visible and correctly attributed — nothing is weakened; a raw
``Locator.wait_for`` timeout on ".node" (the pre-repair shape) named the wrong
subsystem ("element-not-found") and cost a triage session.

Fidelity: the pipeline under test is seeded via ``PipelineAPI`` (transit only —
the case precondition is "an existing pipeline"; every Step-9 observable is
produced by the live UI/Mermaid, nothing is stubbed).
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from tests.ui.pipeline_helpers import _navigate_to_detail

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
TOAST_TIMEOUT = 10_000
COPY_ID_TOAST_TEXT = "The ID has been copied to the clipboard."
COPY_VERSION_ID_TOAST_TEXT = "The Version ID has been copied to the clipboard."
# Toast mechanism (EliteaUI src/components/ToastProvider.jsx:13-21): the
# provider holds ONE `toastProps` state and `openToast` overwrites it in
# place — no queue, no drop. `CopyToClipboardButton.jsx:15-18` dispatches
# `toastInfo(copyMessage)` only AFTER `await navigator.clipboard.writeText()`
# resolves, so right after the second copy click the FIRST toast is still
# mounted and visible on the same `toast-alert` node; a one-shot
# `wait_for(visible)` + `text_content()` read there is anchored to the
# previous click (#2321). Each toast read below is therefore an
# auto-retrying `expect(...).to_contain_text(<this click's text>)` — the
# two messages are not substrings of each other, so the assertion can only
# be satisfied by the toast the clicked button itself produced. (MUI's
# auto-hide timer keys on `open`, not `message` — useSnackbar.js:55-60 — so
# the swapped-in Step 8 text inherits the Step 7 toast's remaining ~3 s
# window, still far above the assertion's 100 ms poll.)
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
        expect(
            pipeline_page.get_toast_alert("info"),
            "Copy ID should raise an info-severity toast",
        ).to_be_visible(timeout=TOAST_TIMEOUT)
        expect(
            pipeline_page.toast_message,
            "Copy ID toast should confirm the clipboard copy",
        ).to_contain_text(COPY_ID_TOAST_TEXT, timeout=TOAST_TIMEOUT)
        clipboard_text = page.evaluate("navigator.clipboard.readText()")
        assert clipboard_text == pipeline_id_text, (
            f"Clipboard should contain the pipeline id {pipeline_id_text!r}, got {clipboard_text!r}"
        )

    with allure.step('Step 8 — Click "Copy version ID"; verify toast feedback and clipboard content'):
        pipeline_page.copy_version_id_button.click()
        # The Step 7 toast may still be open on this same node (replace-in-
        # place, see the module comment) — the retrying assertion waits for
        # the message THIS click produced, not for "a toast is visible".
        expect(
            pipeline_page.get_toast_alert("info"),
            "Copy version ID should raise an info-severity toast",
        ).to_be_visible(timeout=TOAST_TIMEOUT)
        expect(
            pipeline_page.toast_message,
            "Copy version ID toast should confirm the clipboard copy",
        ).to_contain_text(COPY_VERSION_ID_TOAST_TEXT, timeout=TOAST_TIMEOUT)
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
        # Known defect: https://github.com/EliteaAI/elitea-testing-public/issues/2367
        # DiagramOutput.jsx's startOnLoad/contentLoaded() `mermaid.run()` race
        # intermittently wipes the rendered SVG and leaves Mermaid's "Syntax
        # error in text" bomb (no console error, no error text — mermaid
        # swallows it at logLevel 5). Both checks below are the case's OWN
        # Step-9 observable ("visual representation" rendered), asserted as
        # the correct expected behaviour and soft so the Axis-2 console check
        # still runs — an expect.soft failure IS a red (§ Merge gate). The
        # retrying `expect` matters: in the GOOD ordering the bomb flashes for
        # ~1 ms before the real render lands, so a one-shot read of either
        # locator would false-red; the node check first (converges when the
        # real render lands) and the bomb-absence check second (terminal:
        # once nodes are up, a bomb can only mean run() landed last — #2367).
        expect.soft(
            pipeline_page.get_diagram_nodes().first,
            "Known defect: #2367 — Show-link modal should render at least one "
            "Mermaid node (Start → LLM 1 → END); a 'Syntax error in text' bomb "
            "here is DiagramOutput's startOnLoad/run() race, NOT a YAML or "
            "fixture problem (the seeded YAML is byte-identical to UI-authored)",
        ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect.soft(
            pipeline_page.get_diagram_error_icons(),
            "Known defect: #2367 — Mermaid must not have replaced the rendered "
            "diagram with its error bomb (mermaid.run() landing after the "
            "component's own render)",
        ).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
        logger.info("Show-link modal rendered %d Mermaid node(s)", pipeline_page.get_diagram_node_count())

        # Side-channel check across the whole flow (Axis 2 addition, AFS
        # § Coverage Map): zero UNEXPECTED console errors — the deterministic
        # #1368 defect is filtered above, not masked (the modal/diagram
        # assertions above are unaffected either way).
        assert not console_errors, (
            f"No unexpected console errors should occur (known defect #1368 filtered): "
            f"{[e.text for e in console_errors]}"
        )
