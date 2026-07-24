"""UI test — Create Pipeline: Full Details.

TMS: ELITEA-2021
(test-specs/pipelines/l2_create-pipeline-full-details_ELITEA-2021.md)

Creates a pipeline through the Create Pipeline UI form with every available
field populated (name, description, tag, welcome message, chat starter, step
limit, toolkit attach, editor notes), and verifies every field persists
through a full page reload.

Structural note (see AFS Coverage Map): the live Create-Pipeline form has no
Tools or Editor Notes section — those only mount on the pipeline's post-save
detail page (an id is required before an entity can own toolkit
associations). Toolkit attach and Editor Notes are therefore filled AFTER the
first Save, on the detail page, followed by a second Save — this mirrors the
product's actual create-time vs. detail-page-only field split, not a
deviation from the case's own final-state assertions.
"""

import time

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
SAVE_RESPONSE_TIMEOUT = 15_000

_PIPELINE_NAME = f"FullDetailsPipe_{str(int(time.time()))[-6:]}"
_DESCRIPTION = "Pipeline with all fields populated"
_TAG = "automation"
_WELCOME_MESSAGE = "Welcome to the pipeline"
_CHAT_STARTER = "Run analysis"
_STEP_LIMIT = "50"
_EDITOR_NOTES = "Test pipeline for automation"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2021_create-pipeline-full-details.md",
    "onetest-ai Test Case link",
)
def test_create_pipeline_full_details(page, artifact_toolkit, pipeline_api):
    """Create a pipeline with every field populated; verify persistence after reload."""
    project_id = str(settings.elitea_project_id)
    toolkit_name = artifact_toolkit["name"]

    pipeline_page = PipelineDetailPage(page)
    console_errors = pipeline_page.capture_console_errors()

    pipeline_id = None
    try:
        with allure.step(
            "Step 1 — Navigate to Create Pipeline form; General/Welcome/Starters/"
            "Advanced visible, Tools/Editor-Notes not yet present"
        ):
            pipeline_page.navigate_to_create()
            assert pipeline_page.name_input.is_visible(), "Name field should be visible"
            assert pipeline_page.description_input.is_visible(), "Description field should be visible"
            assert pipeline_page.welcome_message_input.is_visible(), "Welcome message field should be visible"
            assert pipeline_page.conversation_starter_add_button.is_visible(), (
                "'+ Starter' add button should be visible"
            )
            assert pipeline_page.step_limit_input.is_visible(), "Step limit field should be visible"
            # Structural finding (AFS Coverage Map elements 6/10): these sections
            # only mount on the post-save detail page — confirmed absent here.
            assert pipeline_page.toolkits_section.count() == 0, (
                "TOOLS section should not render on the create form"
            )
            assert pipeline_page.editor_notes_section.count() == 0, (
                "EDITOR NOTES section should not render on the create form"
            )

        with allure.step(f"Step 2 — Fill Name: '{_PIPELINE_NAME}'"):
            pipeline_page.name_input.click()
            pipeline_page.name_input.press_sequentially(_PIPELINE_NAME, delay=20)
            assert pipeline_page.get_name() == _PIPELINE_NAME

        with allure.step(f"Step 3 — Fill Description: '{_DESCRIPTION}'"):
            pipeline_page.description_input.click()
            pipeline_page.description_input.press_sequentially(_DESCRIPTION, delay=20)
            assert pipeline_page.get_description() == _DESCRIPTION

        with allure.step(f"Step 4 — Add tag '{_TAG}' in the Tags combobox"):
            pipeline_page.add_tag(_TAG)
            assert pipeline_page.has_tag_chip(_TAG), f"Tag chip '{_TAG}' should be visible"

        with allure.step(f"Step 5 — Fill Welcome message: '{_WELCOME_MESSAGE}'"):
            pipeline_page.fill_welcome_message(_WELCOME_MESSAGE)
            assert pipeline_page.get_welcome_message() == _WELCOME_MESSAGE

        with allure.step(f"Step 6 — Add Chat starter: '{_CHAT_STARTER}'"):
            pipeline_page.add_conversation_starter(_CHAT_STARTER)
            assert pipeline_page.get_conversation_starter_text(0) == _CHAT_STARTER

        with allure.step(f"Step 7 — Set Step limit to '{_STEP_LIMIT}'"):
            pipeline_page.set_step_limit(_STEP_LIMIT)
            assert pipeline_page.get_step_limit() == _STEP_LIMIT

        with allure.step("Step 8 — Click Save; verify navigation to the new pipeline's detail page"):
            pipeline_page.wait_for_form_validation()
            assert pipeline_page.is_save_enabled(), "Save should be enabled with all required fields filled"
            pipeline_page.save_and_wait_for_navigation(timeout=SAVE_RESPONSE_TIMEOUT)
            canonical_url = page.url
            assert "/pipelines/all/" in canonical_url, (
                f"Should navigate to the pipeline detail page, got: {canonical_url}"
            )
            pipeline_id = int(pipeline_page.get_pipeline_id())

        with allure.step(
            f"Step 9 — Attach toolkit '{toolkit_name}' via the TOOLS section '+ Toolkit' popper"
        ):
            popper = pipeline_page.open_toolkit_popper(timeout=UI_ELEMENT_TIMEOUT)
            pipeline_page.select_toolkit_in_popper(
                popper, toolkit_name, project_id, timeout=SAVE_RESPONSE_TIMEOUT
            )
            assert pipeline_page.is_toolkit_attached(toolkit_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Toolkit '{toolkit_name}' should appear as a card in the TOOLS section"
            )

        with allure.step(f"Step 10 — Add Editor Notes: '{_EDITOR_NOTES}'"):
            pipeline_page.fill_editor_notes(_EDITOR_NOTES, timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.get_editor_notes() == _EDITOR_NOTES

        with allure.step("Step 11 — Click Save again; verify update persists Toolkit + Editor Notes"):
            save_response = pipeline_page.save_and_wait_for_update(
                project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
            )
            assert save_response is not None, "Save should return the persisted pipeline version"

        with allure.step(
            "Step 12 — Reload via the canonical URL; every field persists"
        ):
            page.goto(canonical_url)
            pipeline_page.wait_for_detail_page_load()

            assert pipeline_page.get_name() == _PIPELINE_NAME, "Name should persist after reload"
            assert pipeline_page.get_description() == _DESCRIPTION, "Description should persist after reload"
            assert pipeline_page.has_tag_chip(_TAG), f"Tag chip '{_TAG}' should persist after reload"
            assert pipeline_page.get_welcome_message() == _WELCOME_MESSAGE, (
                "Welcome message should persist after reload"
            )
            assert pipeline_page.get_conversation_starter_text(0) == _CHAT_STARTER, (
                "Chat starter should persist after reload"
            )
            assert pipeline_page.get_step_limit() == _STEP_LIMIT, "Step limit should persist after reload"
            assert pipeline_page.get_editor_notes() == _EDITOR_NOTES, "Editor notes should persist after reload"
            assert pipeline_page.is_toolkit_attached(toolkit_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Toolkit '{toolkit_name}' card should still be present after reload"
            )

        assert not console_errors, f"No console errors should occur across the flow: {console_errors}"
    finally:
        console_errors.stop()
        if pipeline_id:
            try:
                pipeline_api.delete_pipeline(pipeline_id)
            except Exception as cleanup_exc:
                print(f"[WARN] Failed to delete pipeline {pipeline_id}: {cleanup_exc}")
