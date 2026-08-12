"""UI test — Pipeline: Multiple (Browser) Tabs (ELITEA-2062).

Verifies that two pipelines opened in separate BROWSER tabs (same
authenticated ``BrowserContext``) keep independent, correctly-labelled
``document.title`` values, that opening/switching one tab has zero effect
on a sibling tab's title or loaded content, and that closing one tab leaves
every other tab's state completely intact.

Case-text interpretation (see AFS): the case's "tab"/"tablist"/"close
button (X)" describes REAL browser tabs, not an in-app tab-bar widget —
confirmed by source read of ``PipelinesListPage.open_pipeline_by_name()``
(a plain SPA route push, no ``target="_blank"``). There is no in-app
"multiple open pipeline tabs" feature to test; what matches the case's
language is the browser's own tab strip, driven here via
``BrowserContext.new_page()`` / ``Page.bring_to_front()`` / ``Page.close()``
— the same idiom already merged in
``test_agent_hub_my_liked_reload_cross_tab_sync.py`` (Tab A / Tab B
pattern).

Spec: test-specs/pipelines/l2_pipeline-multiple-browser-tabs_ELITEA-2062.md
"""

import logging
import time

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage
from pages.pipelines_list_page import PipelinesListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
    "pipelines/ELITEA-2062_pipeline-multiple-tabs.md",
    "onetest-ai Test Case link",
)
@pytest.mark.p2
def test_pipeline_multiple_browser_tabs(page, pipeline_api):
    """Two pipelines opened in separate browser tabs keep independent titles
    and content; switching to / closing one tab has zero effect on the other."""
    ts = int(time.time())
    # Pipeline name has a 32-char server-side limit — keep the prefix short.
    pipeline_1_name = f"autotest_mtab1_{ts}"
    pipeline_2_name = f"autotest_mtab2_{ts + 1}"
    pipeline_1_id = None
    pipeline_2_id = None
    tab_b = None
    console_errors_b = []

    try:
        with allure.step("Setup — Create Pipeline 1 and Pipeline 2 via API"):
            pipeline_1 = pipeline_api.create_pipeline(
                name=pipeline_1_name,
                description="Disposable pipeline 1 for ELITEA-2062 multi-tab test",
            )
            pipeline_1_id = pipeline_1["id"]

            pipeline_2 = pipeline_api.create_pipeline(
                name=pipeline_2_name,
                description="Disposable pipeline 2 for ELITEA-2062 multi-tab test",
            )
            pipeline_2_id = pipeline_2["id"]

            assert pipeline_1_id, "Expected a numeric id for Pipeline 1"
            assert pipeline_2_id, "Expected a numeric id for Pipeline 2"
            logger.info(
                "Created pipelines — 1 id=%s name=%s, 2 id=%s name=%s",
                pipeline_1_id, pipeline_1_name, pipeline_2_id, pipeline_2_name,
            )

        list_page_a = PipelinesListPage(page)
        detail_page_a = PipelineDetailPage(page)

        console_errors_a = []
        page.on("console", lambda msg: console_errors_a.append(msg) if msg.type == "error" else None)

        with allure.step("Step 1 — In Tab A, open Pipeline 1 and verify the tab title"):
            list_page_a.navigate()
            # Capture the active project's real name dynamically from the
            # dashboard's own title ("Pipelines: all - {project_name}") —
            # never hardcode it (AFS Axis 2: it need not match the sidebar's
            # static "Private" badge text).
            project_name = page.title().split(" - ", 1)[1]
            list_page_a.open_pipeline_by_name(pipeline_1_name)
            detail_page_a.wait_for_detail_page_load()
            assert page.title() == f"Pipeline: {pipeline_1_name} - {project_name}", (
                f"Expected Tab A's title to reflect Pipeline 1, got {page.title()!r}"
            )

        with allure.step(
            "Step 2 — Open a second, brand-new browser tab and navigate it to the dashboard; "
            "verify Tab A is unaffected and both tabs coexist"
        ):
            tab_b = page.context.new_page()
            tab_b.on("console", lambda msg: console_errors_b.append(msg) if msg.type == "error" else None)
            list_page_b = PipelinesListPage(tab_b)
            detail_page_b = PipelineDetailPage(tab_b)
            list_page_b.navigate()

            assert page.title() == f"Pipeline: {pipeline_1_name} - {project_name}", (
                "Opening a new tab should not change Tab A's title"
            )
            assert len(page.context.pages) == 2, (
                f"Expected 2 open tabs after opening Tab B, got {len(page.context.pages)}"
            )

        with allure.step("Step 3 — In Tab B, open Pipeline 2 and verify its title"):
            list_page_b.open_pipeline_by_name(pipeline_2_name)
            detail_page_b.wait_for_detail_page_load()
            assert tab_b.title() == f"Pipeline: {pipeline_2_name} - {project_name}", (
                f"Expected Tab B's title to reflect Pipeline 2, got {tab_b.title()!r}"
            )

        with allure.step("Step 4 — Verify both tabs coexist with their own correct, independent titles"):
            assert len(page.context.pages) == 2, (
                f"Expected 2 open tabs, got {len(page.context.pages)}"
            )
            assert page.title() == f"Pipeline: {pipeline_1_name} - {project_name}", (
                "Tab A should still show Pipeline 1's title"
            )
            assert tab_b.title() == f"Pipeline: {pipeline_2_name} - {project_name}", (
                "Tab B should still show Pipeline 2's title"
            )

        with allure.step(
            "Step 5 — Switch back to Tab A and verify it switches back to Pipeline 1 "
            "(title AND the detail page's own Name field, not just the title — catches a tab "
            "that kept its old title but silently navigated/reset its content)"
        ):
            page.bring_to_front()
            assert page.title() == f"Pipeline: {pipeline_1_name} - {project_name}", (
                "Tab A's title should still be Pipeline 1's after switching back"
            )
            assert detail_page_a.name_input.input_value() == pipeline_1_name, (
                "Tab A's Name field should still show Pipeline 1's name after switching back"
            )

        with allure.step("Step 6 — Close Tab B and verify Tab A remains open and fully functional"):
            tab_b.close()
            assert len(page.context.pages) == 1, (
                f"Expected 1 open tab after closing Tab B, got {len(page.context.pages)}"
            )
            assert page.title() == f"Pipeline: {pipeline_1_name} - {project_name}", (
                "Tab A's title should be unaffected by closing Tab B"
            )
            assert detail_page_a.name_input.input_value() == pipeline_1_name, (
                "Tab A's Name field should be unaffected by closing Tab B"
            )

        with allure.step("Step 7 — Side-channel check — zero console errors across the whole multi-tab flow"):
            unexpected_errors_a = [m.text for m in console_errors_a]
            assert not unexpected_errors_a, f"Unexpected console errors in Tab A: {unexpected_errors_a}"
            unexpected_errors_b = [m.text for m in console_errors_b]
            assert not unexpected_errors_b, f"Unexpected console errors in Tab B: {unexpected_errors_b}"

    finally:
        with allure.step("Cleanup — close Tab B if still open, delete both pipelines"):
            if tab_b is not None and not tab_b.is_closed():
                tab_b.close()
            if pipeline_1_id is not None:
                pipeline_api.delete_pipeline(pipeline_1_id)
                logger.info("Deleted pipeline id=%s", pipeline_1_id)
            if pipeline_2_id is not None:
                pipeline_api.delete_pipeline(pipeline_2_id)
                logger.info("Deleted pipeline id=%s", pipeline_2_id)
