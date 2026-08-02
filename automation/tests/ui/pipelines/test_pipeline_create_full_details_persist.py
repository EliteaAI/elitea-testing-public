"""UI test — Create Pipeline: full details persist after save and reload.

TMS: ELITEA-2021
(test-specs/pipelines/l2_create-pipeline-full-details-persist-after-reload_ELITEA-2021.md)

Creates a pipeline with every available field populated (name, description,
tag, welcome message, chat starter, step limit, attached toolkit, editor
notes). The Tools section and Editor Notes accordion only render on the
pipeline DETAIL page (after the entity has an id) — confirmed live during
AFS analysis — so the flow is: fill the create-form fields -> Save (create)
-> attach toolkit + fill editor notes on the detail page -> Save again ->
reload -> verify every field persisted with its exact value.
"""

import logging
import uuid
from urllib.parse import urlparse

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage
from pages.pipelines_list_page import PipelinesListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

FORM_SAVE_TIMEOUT = 15_000
UI_ELEMENT_TIMEOUT = 10_000

_PIPELINE_DESCRIPTION = "Pipeline with all fields populated"
_TAG_NAME = "automation"
_WELCOME_MESSAGE = "Welcome to the pipeline"
_CHAT_STARTER = "Run analysis"
_STEP_LIMIT = "50"
_EDITOR_NOTES = "Test pipeline for automation"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2021_create-pipeline-full-details.md",
    "onetest-ai Test Case link",
)
@pytest.mark.p2
def test_create_pipeline_full_details_persist_after_reload(page, pipeline_api, github_toolkit):
    """Create a pipeline with all fields populated; verify persistence after reload."""
    # MAX_NAME_LENGTH is 32 (EliteaUI/src/common/constants.js) — keep the
    # required `autotest_` cleanup-fixture prefix (AFS § Test Data) and trim
    # to fit, rather than truncating (which would silently drop uniqueness).
    pipeline_name = f"autotest_pipe_fulldet_{uuid.uuid4().hex[:8]}"
    assert len(pipeline_name) <= 32, f"Pipeline name exceeds MAX_NAME_LENGTH: {pipeline_name!r}"
    toolkit_name = github_toolkit["name"]
    project_id = str(settings.elitea_project_id)

    # PipelineDetailPage subclasses PipelineFormPage and carries every field
    # this case needs (create-form fields + the detail-only Tools/Editor
    # Notes fields) — one page object for the whole flow, per AFS §
    # Automation Hints.
    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors from every step are
    # captured — AFS Expected Results require "no console errors" across
    # both Save actions, not just the final one.
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Navigate to Pipelines dashboard via sidebar"):
        list_page = PipelinesListPage(page)
        list_page.navigate()
        assert list_page.page_header.is_visible(), "Pipelines dashboard header should be visible"

    with allure.step("Step 2 — Click '+ Pipeline' create button; verify create form loads"):
        pipeline_page.navigate_to_create()
        url_path = urlparse(page.url).path
        assert "/pipelines/create" in url_path, f"Should be on the create form, got: {page.url}"

    with allure.step(f"Step 3 — Fill Name: '{pipeline_name}'"):
        pipeline_page.name_input.click()
        pipeline_page.name_input.press_sequentially(pipeline_name, delay=20)
        assert pipeline_page.get_name() == pipeline_name

    with allure.step(f"Step 4 — Fill Description: '{_PIPELINE_DESCRIPTION}'"):
        pipeline_page.description_input.click()
        pipeline_page.description_input.press_sequentially(_PIPELINE_DESCRIPTION, delay=20)
        assert pipeline_page.get_description() == _PIPELINE_DESCRIPTION

    with allure.step(f"Step 5 — Add tag '{_TAG_NAME}'"):
        pipeline_page.add_tag(_TAG_NAME)
        assert pipeline_page.get_tag_chip_text() == _TAG_NAME

    with allure.step(f"Step 6 — Fill Welcome message: '{_WELCOME_MESSAGE}'"):
        pipeline_page.fill_welcome_message(_WELCOME_MESSAGE)
        assert pipeline_page.get_welcome_message() == _WELCOME_MESSAGE

    with allure.step(f"Step 7 — Add Chat starter: '{_CHAT_STARTER}'"):
        pipeline_page.add_conversation_starter(_CHAT_STARTER)
        assert pipeline_page.get_conversation_starter_value(0) == _CHAT_STARTER

    with allure.step(f"Step 8 — Set Step limit to '{_STEP_LIMIT}' (ADVANCED, expanded by default)"):
        pipeline_page.fill_step_limit(_STEP_LIMIT)
        assert pipeline_page.get_step_limit() == _STEP_LIMIT

    with allure.step("Step 9 — Click Save; verify create succeeds (2xx) and navigates to detail page"):
        create_response = pipeline_page.save_and_wait_for_creation(project_id, timeout=FORM_SAVE_TIMEOUT)
        pipeline_id = create_response["id"]
        pipeline_page.wait_for_detail_page_load()
        url_path = urlparse(page.url).path
        assert "/pipelines/all/" in url_path and "create" not in url_path, (
            f"Should navigate to pipeline detail page, got: {page.url}"
        )
        assert not console_errors, f"Create save should not introduce console errors: {console_errors}"

    try:
        with allure.step(f"Step 10 — Open TOOLS section, attach toolkit '{toolkit_name}'"):
            popper = pipeline_page.open_toolkit_popper(timeout=UI_ELEMENT_TIMEOUT)
            pipeline_page.select_toolkit_in_popper(popper, toolkit_name, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.is_toolkit_attached(toolkit_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Toolkit card for '{toolkit_name}' should appear in the TOOLS section"
            )

        with allure.step(f"Step 11 — Fill Editor Notes: '{_EDITOR_NOTES}'"):
            pipeline_page.fill_editor_notes(_EDITOR_NOTES)
            assert pipeline_page.get_editor_notes() == _EDITOR_NOTES

        with allure.step("Step 12 — Click Save again; verify attach + notes persist (2xx)"):
            pipeline_page.save_and_wait_for_update(project_id, pipeline_id, timeout=FORM_SAVE_TIMEOUT)
            assert not console_errors, f"Second save should not introduce console errors: {console_errors}"

        with allure.step("Step 13 — Reload and verify every field persists with its saved value"):
            canonical_url = page.url  # already carries ?destTab=configuration&viewMode=owner
            page.goto(canonical_url)
            pipeline_page.wait_for_detail_page_load()
            pipeline_page.dismiss_banner_if_present()

            assert pipeline_page.get_name() == pipeline_name, "Name should persist after reload"
            assert pipeline_page.get_description() == _PIPELINE_DESCRIPTION, (
                "Description should persist after reload"
            )
            assert pipeline_page.get_tag_chip_text() == _TAG_NAME, "Tag chip should persist after reload"
            assert pipeline_page.is_toolkit_attached(toolkit_name, timeout=UI_ELEMENT_TIMEOUT), (
                "Attached toolkit card should persist after reload"
            )
            assert pipeline_page.get_welcome_message() == _WELCOME_MESSAGE, (
                "Welcome message should persist after reload"
            )
            assert pipeline_page.get_conversation_starter_value(0) == _CHAT_STARTER, (
                "Chat starter should persist after reload"
            )
            assert pipeline_page.get_step_limit() == _STEP_LIMIT, "Step limit should persist after reload"
            pipeline_page.editor_notes_section.scroll_into_view_if_needed()
            assert pipeline_page.get_editor_notes() == _EDITOR_NOTES, "Editor notes should persist after reload"
    finally:
        with allure.step("Cleanup — delete pipeline via API"):
            try:
                pipeline_api.delete_pipeline(pipeline_id)
                logger.info("Deleted pipeline %s", pipeline_id)
            except Exception as cleanup_exc:
                logger.warning("Failed to delete pipeline %s during teardown: %s", pipeline_id, cleanup_exc)
