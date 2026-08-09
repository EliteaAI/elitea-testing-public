"""UI test — Pipeline: chat starters can be added, saved, and clicked in the
embedded chat panel.

TMS: ELITEA-2053
(test-specs/pipelines/l2_pipeline-chat-starters-visible-and-clickable_ELITEA-2053.md)

Creates a disposable pipeline, expands the "Chat starters" section (renders
expanded by default — no accordion click needed, same precedent as
ELITEA-2021/ELITEA-2052), adds a starter, saves it, then reloads the detail
page for a pristine "before any input" state and verifies: the saved
starter's row shows its exact text plus a "delete starter" button; the
starter renders as a clickable chip (`chat-conversation-starter-tile`) in
the embedded chat panel before any message is sent; and clicking the chip
pre-fills the chat input with the starter's exact text (pre-fill only, no
auto-send — same one-shot `hasStarterBeenSent` mechanic ELITEA-1886
documented for the Agent surface).
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

_PIPELINE_DESCRIPTION = "Automated analysis for ELITEA-2053 chat starters"
_CHAT_STARTER = "Analyze this data"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2053_pipeline-chat-starters.md",
    "onetest-ai Test Case link",
)
@pytest.mark.p2
def test_pipeline_chat_starters_visible_and_clickable(page, pipeline_api):
    """Saved chat starter renders as a clickable chip that pre-fills the chat input."""
    pipeline_name = f"autotest_pipe_chatstart_{uuid.uuid4().hex[:8]}"
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

    with allure.step('Step 2 — Confirm the "Chat starters" section is visible/expanded'):
        # The section renders expanded by default (no accordion click
        # needed) — asserting the "+ Starter" button's visibility already
        # proves the section is open, same "always-expanded" precedent as
        # ELITEA-2021/ELITEA-2052 (AFS Step 2 note).
        pipeline_page.conversation_starter_add_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.conversation_starter_add_button.is_visible()

    with allure.step('Step 3 — Click "+ Starter" and enter text: ' f"'{_CHAT_STARTER}'"):
        pipeline_page.add_conversation_starter(_CHAT_STARTER)
        assert pipeline_page.get_conversation_starter_value() == _CHAT_STARTER

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
        with allure.step("Step 5 — Reload the detail page for a pristine 'before any input' state"):
            # A full-page reload (not an SPA route change) gives a pristine
            # "new session" load, distinct from any live-preview state
            # carried over from Step 3's typing — same discipline as
            # ELITEA-1885/ELITEA-1886/ELITEA-2052.
            canonical_url = page.url
            page.goto(canonical_url)
            pipeline_page.wait_for_detail_page_load()
            pipeline_page.dismiss_banner_if_present()
            pipeline_page.wait_for_network()

        with allure.step(
            "Step 6 — Verify the saved starter row shows its exact text and a 'delete starter' button"
        ):
            pipeline_page.conversation_starter_inputs.first.wait_for(
                state="visible", timeout=UI_ELEMENT_TIMEOUT
            )
            assert pipeline_page.get_conversation_starter_value() == _CHAT_STARTER, (
                "The persisted starter row should show the exact saved text after reload"
            )
            assert pipeline_page.conversation_starter_delete_button.is_visible(), (
                "A 'delete starter' button should be present next to the existing starter"
            )

        with allure.step(
            'Step 7 — In the chat panel, verify the starter renders as a clickable chip, exactly once'
        ):
            starter_tiles = pipeline_page.get_chat_starter_tiles()
            starter_tiles.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            assert starter_tiles.count() == 1, (
                f"Exactly one starter chip should render before any message is sent, got {starter_tiles.count()}"
            )
            assert (starter_tiles.first.text_content() or "").strip() == _CHAT_STARTER, (
                "The chip's text should match the saved starter exactly"
            )
            assert pipeline_page.get_embedded_chat_message_item_count() == 0, (
                "No message should be present before the starter is clicked"
            )
            assert not console_issues, (
                f"Post-reload starter render should not introduce console errors/warnings: {console_issues}"
            )

        with allure.step(
            "Step 8 — Click the starter chip; verify it pre-fills the chat input and disappears"
        ):
            clicked_text = pipeline_page.click_chat_starter_tile(_CHAT_STARTER)
            assert clicked_text == _CHAT_STARTER
            assert pipeline_page.chat_input.input_value() == _CHAT_STARTER, (
                "The chat input should be pre-filled with the exact starter text"
            )
            assert pipeline_page.get_chat_starter_tiles().count() == 0, (
                "The starter chip should disappear immediately after being clicked (one-shot)"
            )
            assert pipeline_page.get_embedded_chat_message_item_count() == 0, (
                "Clicking the starter pre-fills the input only — it must NOT auto-send a message"
            )
            assert not console_issues, (
                f"Clicking the starter chip should not introduce console errors/warnings: {console_issues}"
            )
    finally:
        with allure.step("Cleanup — delete pipeline via API"):
            try:
                pipeline_api.delete_pipeline(pipeline_id)
                logger.info("Deleted pipeline %s", pipeline_id)
            except Exception as cleanup_exc:
                logger.warning("Failed to delete pipeline %s during teardown: %s", pipeline_id, cleanup_exc)
