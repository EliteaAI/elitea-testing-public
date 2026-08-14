"""UI test — Pipeline: Three-dot Menu Actions (ELITEA-2049).

Opens the pipeline detail page's three-dot Actions menu, verifies every
expected item is present across its two groups (VERSION / PIPELINE), clicks
the PIPELINE-group "Share" item (functionally the case's "Copy link"),
verifies the toast + clipboard content, then RE-OPENS the menu and closes it
with Escape.

Step 6 re-opens the menu before pressing Escape (review fix round 1): the
Step 4 click already closes the menu (``DotMenu.jsx``'s ``withClose`` fires
on every item click), so pressing Escape against an already-closed menu
would never actually exercise Escape-to-close — the assertion would pass
even if that behavior regressed.

Case-text drift, filed as CLARIFICATION (NOT a product defect — reverse-
masking guard applies): the case's Step 3/4 wording names a standalone
"Copy link" menu label, but the live product has no such label. Two items
are both labelled "Share" (VERSION-group ``share-version-menuitem`` and
PIPELINE-group ``share-agent-menuitem``); the PIPELINE-group one functionally
matches the case's "Copy link" step (copies the generic pipeline URL, shows
the toast). Filed as a sibling to the same pattern already documented for
the Agent Detail page (ELITEA-1898, #1288) and the Agent Hub modal
(ELITEA-2356, #1218) — see
https://github.com/EliteaAI/elitea-testing-public/issues/1337.

Spec: test-specs/pipelines/l2_pipeline-three-dot-menu-actions_ELITEA-2049.md
"""

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
CLIPBOARD_TIMEOUT = 10_000


def _copy_link_via_menuitem(page, detail_page: PipelineDetailPage, menuitem, timeout: int) -> str:
    """Click a "Share" menuitem and return the URL it copies to the clipboard.

    Mirrors ``test_agent_copy_version_link.py``'s ``_copy_link_via_menuitem``
    (ELITEA-1898) per this case's AFS Automation Hints — reused verbatim
    rather than re-derived: clears the clipboard via a real write first (the
    caller must have already granted clipboard permissions on the browser
    context), clicks the menuitem (which also closes the menu —
    ``DotMenu.jsx``'s ``withClose``), waits for the toast confirmation, then
    polls ``navigator.clipboard.readText()`` via ``page.wait_for_function``
    instead of a direct blocking call (a direct call hung ~30 min on an
    un-grantable permission prompt during this case's live exploration).
    """
    page.evaluate("() => navigator.clipboard.writeText('')")
    menuitem.click()
    detail_page.toast_message.wait_for(state="visible", timeout=timeout)
    page.wait_for_function(
        "async () => { const t = await navigator.clipboard.readText(); return t.length > 0; }",
        timeout=timeout,
    )
    return page.evaluate("async () => await navigator.clipboard.readText()")


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2049_pipeline-three-dot-menu-actions.md",
    "onetest-ai Test Case link",
)
@allure.issue(
    "https://github.com/EliteaAI/elitea-testing-public/issues/1337",
    "Case-text drift CLARIFICATION #1337",
)
def test_pipeline_three_dot_menu_actions(page, pipeline_api):
    """Three-dot menu shows all expected items; PIPELINE-group "Share"
    (the case's "Copy link") copies the pipeline URL with a toast
    confirmation; Escape closes the menu."""
    with allure.step("Step 0 (setup) — create a disposable pipeline via API"):
        pipeline = pipeline_api.create_pipeline(
            name="autotest_three_dot_menu_pipe",
            description="Disposable pipeline for ELITEA-2049 three-dot menu actions test",
        )
        pid = pipeline["id"]

    detail_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from the whole menu-open ->
    # copy-link -> close round trip are captured (AFS Expected Results:
    # "Zero console errors across the whole flow").
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    try:
        with allure.step("Step 1 — Open the pipeline; verify it loaded in the editor"):
            detail_page.navigate(pid)
            detail_page.dismiss_banner_if_present()
            assert detail_page.get_name() == "autotest_three_dot_menu_pipe", (
                "Pipeline detail page should show the created pipeline's name"
            )

        with allure.step("Step 2 — Click the three-dot Actions menu button; verify the menu opens"):
            detail_page.actions_menu_button.click()
            detail_page.actions_menu.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            assert detail_page.actions_menu.is_visible(), "Actions menu should be visible after click"

        with allure.step(
            "Step 3 — Verify all expected menu items are present: VERSION-group "
            "Export/Share/Fork/Delete(disabled), PIPELINE-group Share/Pin to top/"
            "Delete pipeline (case text 'Copy link' maps to PIPELINE-group Share — "
            "CLARIFICATION #1337, see module docstring)"
        ):
            assert detail_page.export_menuitem.is_visible(), 'VERSION-group "Export" should be visible'
            assert detail_page.share_version_menuitem.is_visible(), (
                'VERSION-group "Share" should be visible'
            )
            assert detail_page.fork_menuitem.is_visible(), 'VERSION-group "Fork" should be visible'
            assert detail_page.delete_version_menuitem.is_visible(), (
                'VERSION-group "Delete" should be visible'
            )
            assert detail_page.delete_version_menuitem.get_attribute("aria-disabled") == "true", (
                'VERSION-group "Delete" should be disabled while the open version is "base"'
            )
            assert detail_page.share_agent_menuitem.is_visible(), (
                'PIPELINE-group "Share" (case\'s "Copy link") should be visible'
            )
            assert detail_page.pin_to_top_menuitem.is_visible(), (
                'PIPELINE-group "Pin to top" should be visible'
            )
            assert detail_page.delete_agent_menuitem.is_visible(), (
                'PIPELINE-group "Delete pipeline" should be visible'
            )

            # Negative control (AFS Axis 2): the two "Share" items are visually
            # identical labels on DIFFERENT elements — without this, wiring the
            # test to the wrong one would still pass, on the wrong URL shape.
            # Same concern ELITEA-1898's AFS/test documents for the Agent entity.
            # Bounding-box comparison (established repo pattern for "is this a
            # different element" checks, e.g. test_agent_management.py's tag-
            # chip identity check) — the two Share items sit in different menu
            # groups, so their positions must differ.
            version_share_box = detail_page.share_version_menuitem.bounding_box()
            agent_share_box = detail_page.share_agent_menuitem.bounding_box()
            assert version_share_box != agent_share_box, (
                'VERSION-group "Share" and PIPELINE-group "Share" must resolve to '
                "two different DOM elements (different bounding boxes), not the "
                "same node matched twice"
            )

        with allure.step(
            "Precondition (setup) — grant clipboard permissions before exercising "
            "the copy-link action"
        ):
            page.context.grant_permissions(["clipboard-read", "clipboard-write"])

        with allure.step('Step 4 — Click the PIPELINE-group "Share" item ("Copy link")'):
            copied_url = _copy_link_via_menuitem(
                page, detail_page, detail_page.share_agent_menuitem, CLIPBOARD_TIMEOUT
            )

        with allure.step(
            "Step 5 — Verify the link is copied to clipboard, with toast feedback"
        ):
            assert detail_page.toast_message.is_visible(), (
                "Toast confirmation should be visible after copying the link"
            )
            assert "copied to the clipboard" in detail_page.get_toast_text().lower(), (
                "Toast should confirm the link was copied to the clipboard"
            )
            assert f"/pipelines/all/{pid}" in copied_url, (
                f"Copied URL should contain the pipeline's path, got {copied_url!r}"
            )

        with allure.step(
            "Step 6 — Close the menu by pressing Escape; verify it closes"
        ):
            # Step 4's click already closed the menu (DotMenu.jsx's
            # `withClose` fires on every item click), so an Escape press here
            # would be asserting against an already-closed menu — the
            # assertion could never fail even if Escape-to-close regressed.
            # Re-open the menu first so this step exercises the actual
            # Escape-to-close behavior the case asks for (review finding,
            # fix round 1).
            detail_page.actions_menu_button.click()
            detail_page.actions_menu.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            assert detail_page.actions_menu.is_visible(), (
                "Actions menu should be re-open before exercising the Escape-close assertion"
            )

            page.keyboard.press("Escape")
            detail_page.actions_menu.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
            assert detail_page.actions_menu.count() == 0 or not detail_page.actions_menu.is_visible(), (
                "Actions menu should be closed/absent after Escape"
            )

        assert not console_errors, (
            "No console errors expected across the menu-open -> copy-link -> "
            f"close flow, got: {[m.text for m in console_errors]}"
        )
    finally:
        try:
            pipeline_api.delete_pipeline(pid)
        except Exception:
            pass
