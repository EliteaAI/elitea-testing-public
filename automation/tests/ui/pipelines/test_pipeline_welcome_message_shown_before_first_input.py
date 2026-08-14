"""UI test — Pipeline: welcome message shown before first user input.

TMS: ELITEA-2052
(test-specs/pipelines/l2_pipeline-welcome-message-shown-before-first-input_ELITEA-2052.md)

Creates a disposable pipeline, fills the Welcome message field (the section
renders expanded by default — no accordion click needed, same precedent as
ELITEA-2021's "Advanced" section), saves it, then reloads the detail page
for a pristine "new chat session" and verifies the configured welcome
message renders automatically before any user input — exactly one message,
exact text, through the agent/pipeline-answer code path (not the
user-message path).
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

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

FORM_SAVE_TIMEOUT = 15_000
UI_ELEMENT_TIMEOUT = 10_000

_PIPELINE_DESCRIPTION = "Pipeline for welcome message automation case"
_WELCOME_MESSAGE = "Hello! How can I help you today?"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2052_pipeline-welcome-message.md",
    "onetest-ai Test Case link",
)
@pytest.mark.p2
def test_pipeline_welcome_message_shown_before_first_input(page, pipeline_api):
    """Welcome message renders automatically before any user input."""
    pipeline_name = f"autotest_pipe_welcome_{uuid.uuid4().hex[:8]}"
    assert len(pipeline_name) <= 32, f"Pipeline name exceeds MAX_NAME_LENGTH: {pipeline_name!r}"
    project_id = str(settings.elitea_project_id)

    pipeline_page = PipelineDetailPage(page)

    # Registered before Step 1 so console errors/warnings from every step
    # are captured — AFS Expected Results require "no console errors or
    # warnings at any step", not just at Save.
    console_issues = []
    page.on(
        "console",
        lambda msg: console_issues.append(msg) if msg.type in ("error", "warning") else None,
    )

    with allure.step("Step 1 — Open a pipeline (create form) and fill Name + Description"):
        list_page = PipelinesListPage(page)
        list_page.navigate()
        pipeline_page.navigate_to_create()
        url_path = urlparse(page.url).path
        assert "/pipelines/create" in url_path, f"Should be on the create form, got: {page.url}"

        pipeline_page.name_input.click()
        pipeline_page.name_input.press_sequentially(pipeline_name, delay=20)
        assert pipeline_page.get_name() == pipeline_name

        pipeline_page.description_input.click()
        pipeline_page.description_input.press_sequentially(_PIPELINE_DESCRIPTION, delay=20)
        assert pipeline_page.get_description() == _PIPELINE_DESCRIPTION

    with allure.step('Step 2 — Confirm the "Welcome message" section is visible/expanded'):
        # The section renders expanded by default (no accordion click
        # needed) — asserting the textarea's visibility already proves the
        # section is open, same "always-expanded" precedent as ELITEA-2021's
        # "Advanced" section (AFS Step 2 note).
        pipeline_page.welcome_message_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.welcome_message_input.is_visible()

    with allure.step(f"Step 3 — Fill the welcome-message textbox: '{_WELCOME_MESSAGE}'"):
        pipeline_page.fill_welcome_message(_WELCOME_MESSAGE)
        assert pipeline_page.get_welcome_message() == _WELCOME_MESSAGE

    with allure.step("Step 4 — Click Save; verify create succeeds (2xx) with no console errors/warnings"):
        create_response = pipeline_page.save_and_wait_for_creation(project_id, timeout=FORM_SAVE_TIMEOUT)
        pipeline_id = create_response["id"]
        pipeline_page.wait_for_detail_page_load()
        url_path = urlparse(page.url).path
        assert "/pipelines/all/" in url_path and "create" not in url_path, (
            f"Should navigate to pipeline detail page, got: {page.url}"
        )
        assert not console_issues, f"Create save should not introduce console errors/warnings: {console_issues}"

    try:
        with allure.step(
            "Step 5 — Open a new chat session: full-page reload of the detail page for a pristine load"
        ):
            # The embedded chat panel is already mounted on the detail page
            # right after Save — there is no separate "open chat" action on
            # this route (AFS Step 5 note). A full-page reload (not an SPA
            # route change) gives a pristine "new session" load distinct
            # from any live-preview state carried over from Step 3's typing.
            canonical_url = page.url
            page.goto(canonical_url)
            pipeline_page.wait_for_detail_page_load()
            pipeline_page.dismiss_banner_if_present()
            page.wait_for_load_state("networkidle")

        with allure.step(
            "Step 6 — Verify the welcome message appears automatically, alone, before any user input"
        ):
            pipeline_page.chat_message_list.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            assert pipeline_page.get_embedded_chat_message_item_count() == 1, (
                "Exactly one message should render before any user input"
            )
            assert pipeline_page.get_last_embedded_chat_message_text() == _WELCOME_MESSAGE, (
                "The sole message should be the exact configured welcome message"
            )

            has_read_out, has_answer_marker, has_delete_button = (
                pipeline_page.get_last_embedded_chat_message_agent_markers()
            )
            assert (has_read_out, has_answer_marker, has_delete_button) == (True, True, False), (
                "The welcome message must render via the agent/pipeline-answer code path "
                f"(chat-read-out-button present, answer marker present, no delete button), "
                f"got read_out={has_read_out} answer_marker={has_answer_marker} delete={has_delete_button}"
            )

            assert pipeline_page.chat_input.input_value() == "", (
                "The message input must be empty — no user message has been sent"
            )

            assert not console_issues, (
                f"Post-reload welcome-message render should not introduce console errors/warnings: "
                f"{console_issues}"
            )
    finally:
        with allure.step("Cleanup — delete pipeline via API"):
            try:
                pipeline_api.delete_pipeline(pipeline_id)
                logger.info("Deleted pipeline %s", pipeline_id)
            except Exception as cleanup_exc:
                logger.warning("Failed to delete pipeline %s during teardown: %s", pipeline_id, cleanup_exc)
