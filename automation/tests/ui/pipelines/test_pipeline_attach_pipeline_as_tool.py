"""UI test — Pipeline Tools section: attach another pipeline as a tool.

TMS: ELITEA-2064
(test-specs/pipelines/l2_pipeline-attach-pipeline-as-tool_ELITEA-2064.md)

Attaches a second pipeline (Pipeline B) to a pipeline (Pipeline A) via the
TOOLS section's "+ Pipeline" button, verifies it renders as a flat-list
attached card (no "Pipeline sub-tab" — same root cause as the sibling
Toolkit/MCP/Agent attach flows, EliteaAI/elitea-testing-public#530/#1149),
confirms the attach auto-persists immediately via
``PATCH .../application_relation/prompt_lib/{project}/{id}/{version_id}``
(the same endpoint/mechanism the Agent picker uses, NOT the Toolkit/MCP
picker's ``/tool/prompt_lib/`` PATCH), and verifies the attachment survives a
full page reload.

Step 5's "Save Pipeline A" is a case-text CLARIFICATION, not a state-changing
click: the Save button stays disabled after the attach (nothing left to
persist — step 3's PATCH already did), so this test asserts that disabled
state instead of clicking an inert button.
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000


@pytest.mark.tms("ELITEA-2064")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2064_pipeline-attach-pipeline-as-tool.md",
    "onetest-ai Test Case link",
)
def test_attach_pipeline_as_tool(page, pipeline_id, pipeline_api):
    """Attach a second pipeline as a tool via TOOLS "+ Pipeline"; verify save/reload persistence."""
    project_id = str(settings.elitea_project_id)

    with allure.step("Step 0 (setup) — create Pipeline B via the API (the pipeline attached as a tool)"):
        pipeline_b = pipeline_api.create_pipeline(
            name="autotest_2064_pipeline_b",
            description="ELITEA-2064 Pipeline B — attached as a tool to Pipeline A",
        )
        pipeline_b_id = pipeline_b["id"]
        pipeline_b_name = pipeline_b["name"]

    try:
        pipeline_page = PipelineDetailPage(page)

        # Registered before Step 1 so console errors from every step (navigate,
        # attach, card render, save-state check, reload) are captured — AFS
        # Expected Results require "no console errors at any step".
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

        with allure.step("Step 1 — Open Pipeline A"):
            pipeline_page.navigate(pipeline_id)
            pipeline_page.dismiss_banner_if_present()
            pipeline_page.wait_for_canvas()
            canonical_url = page.url  # captured for the reload step

        with allure.step(
            'Step 2 — Attach a pipeline as a tool: add an Agent node and open its "Agents & Pipelines" picker '
            "(TOOLS '+ Pipeline' button removed, EL-7159)"
        ):
            pipeline_page.add_node("Agent", timeout=UI_ELEMENT_TIMEOUT)
            pipeline_page.wait_for_node_on_canvas("agent", timeout=UI_ELEMENT_TIMEOUT)
            pipeline_page.open_agent_node_picker(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 3 — Select Pipeline B from the picker"):
            pipeline_page.pick_agent_node_application(pipeline_b_name, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.wait_for_agent_node_agent_value(pipeline_b_name, timeout=UI_ELEMENT_TIMEOUT) == pipeline_b_name, (
                f"Agent node picker should show {pipeline_b_name!r} after selection"
            )
            pipeline_page.close_node_panel(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 4 — Verify Pipeline B appears attached as a flat-list card (no 'sub-tab' — "
            "same root cause as EliteaAI/elitea-testing-public#1149/#530)"
        ):
            pipeline_page.ensure_toolkits_section_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.is_toolkit_attached(pipeline_b_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"TOOLS section should show a card for the attached pipeline {pipeline_b_name!r}"
            )
            assert not console_errors, f"Attaching the pipeline should not introduce console errors: {console_errors}"

        with allure.step(
            "Step 5 — Save Pipeline A: the attach is persisted by the Save "
            "(PATCH .../application_relation/prompt_lib/ 201 + pipeline PUT 201); Save is disabled afterwards"
        ):
            # EL-7159 (class A, UI drift): the picker no longer auto-persists on select; the
            # attachment is written when the pipeline is saved. Same endpoint as before
            # (application_relation), so the endpoint regression guard is kept.
            attach_response = pipeline_page.save_and_wait_for_attach(
                "/application_relation/prompt_lib/", project_id, pipeline_id, timeout=UI_ELEMENT_TIMEOUT
            )
            assert attach_response is not None, (
                "Pipeline attach should return the persisted relation payload from the "
                "PATCH .../application_relation/prompt_lib/{project}/{pipeline_b_id}/{version_id} "
                "201 response"
            )
            assert pipeline_page.save_button.is_disabled(), (
                "Save should be disabled again once the attachment and the pipeline are persisted"
            )

        with allure.step("Step 6 — Reload via the canonical URL; the attached pipeline card persists"):
            page.goto(canonical_url)
            pipeline_page.wait_for_detail_page_load()
            pipeline_page.wait_for_canvas()

            assert pipeline_page.is_toolkit_attached(pipeline_b_name, timeout=UI_ELEMENT_TIMEOUT), (
                "TOOLS section should still show the attached pipeline card after reload"
            )
            # The console listener registered before Step 1 stays attached
            # across page.goto() (same Page object, navigation doesn't
            # unsubscribe listeners) — re-assert here so a reload/hydration-only
            # regression doesn't silently escape detection.
            assert not console_errors, f"Reload should not introduce console errors: {console_errors}"
    finally:
        try:
            pipeline_api.delete_pipeline(pipeline_b_id)
        except Exception:
            logger.warning("Failed to delete Pipeline B (id %s) during teardown", pipeline_b_id)
