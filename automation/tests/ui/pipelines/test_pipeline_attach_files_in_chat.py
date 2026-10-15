"""UI test — Pipeline: attach files in the embedded chat panel.

TMS: ELITEA-2059
(test-specs/pipelines/l2_pipeline-attach-files-in-chat_ELITEA-2059.md)
Also covers TMS: ELITEA-2066
(test-specs/pipelines/lextend_pipeline-modules-attachments-toggle-persists_ELITEA-2066.md)

ADJUSTED (issue #2408, human-reviewed triage overturning the parked Class-D
question #2412 — see the AFS § Adjustment): the pre-adjustment version of
this test built a BARE LLM node (`pipeline_with_variable_task_llm_id`) and
accepted a generic "I can't access the contents"-style acknowledgment as a
PASS. The triage found this was behavior drift, not a product fact: for a
chat attachment's actual content to reach the LLM, the pipeline needs an
Artifact toolkit attached in TOOLS *and* wired into the LLM node's Toolkits
select + `tool_names`/`task`/`state` mapping
(`pipeline_with_artifact_toolkit_llm_id` fixture, wired at creation via the
API per the AFS's recommended shape) — a bare node never issues a
`read_file` call at all. This test now proves the corrected flow and the
STRENGTHENED Expected Result: the response must contain the correct fact
extracted from the file's actual content (e.g. "cat"), not merely a
filename-or-acknowledgment keyword.

Steps 1-2 (toolkit attach + Toolkits-select wiring verification) are
NEW this round. Steps 3-9 are the pre-adjustment test's steps 1-7,
renumbered, with step 9's assertion strengthened per the AFS.

ELITEA-2066 extends this file with a second test that proves the "Attachments"
MODULES toggle's ON/OFF state (and its effect on the attach button) is
genuinely persisted server-side across Save + a hard page reload — not
merely a live, unsaved formik value — in both directions
(enable-then-disable). Unaffected by this adjustment.
"""

import logging

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
AI_RESPONSE_TIMEOUT = 60_000
SAVE_RESPONSE_TIMEOUT = 15_000

# Content-resolution question + the literal, unambiguous file content it asks
# about — matches the AFS § Test Data / § Adjustment live-confirmed shape
# ("cat" / "What animal is in the attachment?"), not a generic summarize
# request an honest acknowledgment-only reply could satisfy.
_FILE_CONTENT = "cat"
_MESSAGE_TEXT = "What animal is in the attachment?"


@pytest.mark.tms("ELITEA-2059")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2059_pipeline-attach-files-in-chat.md",
    "onetest-ai Test Case link",
)
def test_attach_files_in_chat(page, pipeline_with_artifact_toolkit_llm_id, tmp_path):
    """Attach a file in the pipeline's embedded chat; pipeline resolves its actual content."""
    pipeline_id = pipeline_with_artifact_toolkit_llm_id["pipeline_id"]
    toolkit_name = pipeline_with_artifact_toolkit_llm_id["toolkit_name"]
    pipeline_page = PipelineDetailPage(page)

    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step(
        "Step 1 — [NEW] Navigate to the pipeline (Artifact toolkit already attached "
        "+ wired into the LLM node via the fixture's API-driven setup); verify the "
        "attached-toolkit card renders"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        assert pipeline_page.configuration_tab.is_visible(), (
            "Configuration panel (General section) should be visible after navigating"
        )
        assert pipeline_page.is_toolkit_attached(toolkit_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"Artifact toolkit {toolkit_name!r} should render as an attached card in "
            "the TOOLS section"
        )

    with allure.step(
        "Step 2 — [NEW] Verify the LLM node's Toolkits select shows the attached "
        "toolkit as a selected chip (wired via tool_names at creation)"
    ):
        toolkits_value = pipeline_page.get_llm_node_toolkits_value()
        assert toolkit_name in toolkits_value, (
            f"LLM node's Toolkits select should show {toolkit_name!r} as a selected "
            f"chip, got: {toolkits_value!r}"
        )

    with allure.step(
        'Step 3 — Turn on the "Attachments" MODULES switch; attach button flips '
        "disabled -> enabled instantly, no Save required"
    ):
        assert pipeline_page.chat_attach_button.is_disabled(), (
            "Attach button should be disabled before the Attachments module is enabled"
        )
        pipeline_page.toggle_attachments_module(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.is_tools_module_toggle_checked("attachments"), (
            "Attachments MODULES toggle should be checked after clicking it"
        )
        assert not pipeline_page.chat_attach_button.is_disabled(), (
            "Attach button should become enabled the instant the Attachments module "
            "is turned on — no page reload or Save needed"
        )

    with allure.step(
        'Step 4 — Locate the "Attach Files (10 left)" button; visible, enabled, '
        "correct tooltip text"
    ):
        assert pipeline_page.chat_attach_button.is_visible(), "Attach button should be visible"
        assert not pipeline_page.chat_attach_button.is_disabled(), "Attach button should be enabled"
        pipeline_page.chat_attach_button.hover()
        tooltip_text = pipeline_page.chat_attach_button_tooltip.text_content(timeout=UI_ELEMENT_TIMEOUT)
        assert tooltip_text == "Attach Files (10 left)", (
            f"Attach button's tooltip should read 'Attach Files (10 left)' before any "
            f"attachment, got: {tooltip_text!r}"
        )

    with allure.step("Step 5 — Click the attach button; native file chooser opens"):
        test_file = tmp_path / "elitea2059_testfile.txt"
        test_file.write_text(_FILE_CONTENT)
        file_chooser = pipeline_page.open_embedded_chat_file_chooser(timeout=UI_ELEMENT_TIMEOUT)
        assert file_chooser is not None, "Clicking the attach button should open a native file chooser"

    with allure.step(
        "Step 6 — Select the .txt file; it appears as an attachment chip with the "
        "exact filename, and the tooltip decrements to '9 left'"
    ):
        file_chooser.set_files(str(test_file))
        pipeline_page.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_embedded_chat_attachment_chip_count() == 1, (
            "Exactly one attachment chip should be present after selecting the file"
        )
        assert pipeline_page.get_embedded_chat_attachment_chip_text(0) == test_file.name, (
            "Attachment chip text should be the exact selected filename"
        )
        pipeline_page.chat_attach_button.hover()
        decremented_tooltip = pipeline_page.chat_attach_button_tooltip.text_content(
            timeout=UI_ELEMENT_TIMEOUT
        )
        assert decremented_tooltip == "Attach Files (9 left)", (
            f"Attach button's tooltip should decrement to 'Attach Files (9 left)' "
            f"after attaching one file, got: {decremented_tooltip!r}"
        )

    with allure.step(
        "Step 7 — Send a message that requires resolving the attachment's actual "
        "content (NOT a generic summarize request); message bubble shows text+chip, "
        "composer's chip count resets to 0"
    ):
        initial_count = pipeline_page.get_embedded_chat_message_count()
        pipeline_page.send_message_in_embedded_chat(_MESSAGE_TEXT, timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.wait_for_embedded_chat_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)

        # Read the message at its FIXED index (not .last) — a transient AI
        # "Waking the agent…" placeholder can already render at
        # initial_count + 1 before the reply arrives, making .last race-prone
        # for reading back the user's own just-sent message.
        sent_message_text = pipeline_page.get_embedded_chat_message_full_text_at(initial_count)
        assert _MESSAGE_TEXT in sent_message_text, (
            f"Sent message bubble should show the typed text {_MESSAGE_TEXT!r}, "
            f"got: {sent_message_text!r}"
        )
        sent_attachment_names = pipeline_page.get_embedded_chat_message_attachment_names_at(initial_count)
        assert test_file.name in sent_attachment_names, (
            f"Sent message bubble should show an attachment card for {test_file.name!r}, "
            f"got attachment cards: {sent_attachment_names!r}"
        )

        assert pipeline_page.get_embedded_chat_attachment_chip_count() == 0, (
            "Composer's attachment chip count should reset to 0 immediately after send "
            "(no residual chips left in the composer)"
        )

    with allure.step(
        "Step 8 — [STRENGTHENED] Verify the pipeline actually resolves the "
        "attachment's content: no execution error, AND the response contains "
        "the correct fact from the file's actual content (not merely the "
        "filename or a generic acknowledgment)"
    ):
        pipeline_page.wait_for_embedded_chat_response(
            initial_count=initial_count + 1, timeout=AI_RESPONSE_TIMEOUT
        )
        response_text = pipeline_page.get_embedded_chat_last_message()
        response_lower = response_text.lower()
        assert "error: error code" not in response_lower, (
            f"Pipeline response should not show an execution error, got: {response_text!r}"
        )
        assert _FILE_CONTENT in response_lower, (
            "Pipeline response should contain the correct fact resolved from the "
            f"attached file's actual content ({_FILE_CONTENT!r}) — not merely the "
            f"filename or a generic acknowledgment, got: {response_text!r}"
        )

    with allure.step("Step 9 — No console errors were introduced at any step"):
        assert not console_errors, f"No step should introduce console errors: {console_errors}"


@pytest.mark.tms("ELITEA-2066")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2066_pipeline-modules-section.md",
    "onetest-ai Test Case link",
)
def test_attachments_toggle_persists_across_save_and_reload(page, pipeline_id):
    """Attachments MODULES toggle + attach-button state survive Save + reload, both directions.

    ELITEA-2059's own test proves the ON-direction, live/unsaved causal link
    (toggle -> attach button, instant, no Save needed). This test proves the
    stronger, Save-gated claim ELITEA-2066's case asks for: after Save and a
    hard page reload, the toggle AND the attach button still reflect the
    persisted state — in both the enable and disable direction.
    """
    pipeline_page = PipelineDetailPage(page)
    project_id = str(settings.elitea_project_id)

    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step(
        "Step 1 — Open the pipeline; MODULES/Attachments toggle and attach button start "
        "unchecked/disabled"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.dismiss_banner_if_present()
        pipeline_page.wait_for_canvas()
        toggle = pipeline_page.get_tools_module_toggle("attachments")
        expect(toggle).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        assert not pipeline_page.is_tools_module_toggle_checked("attachments"), (
            "Attachments MODULES toggle should start unchecked on a fresh pipeline"
        )
        expect(pipeline_page.chat_attach_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.chat_attach_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step('Step 2 — Toggle "Attachments" to enabled; attach button enables instantly'):
        pipeline_page.toggle_attachments_module(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.is_tools_module_toggle_checked("attachments"), (
            "Attachments MODULES toggle should be checked after clicking it"
        )
        expect(pipeline_page.chat_attach_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 3 — Save the pipeline while Attachments is enabled"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"

    with allure.step(
        "Step 4 — Reload the pipeline (hard navigation, not live state); toggle stays checked "
        "and the attach button stays enabled — proves server-side persistence, not just a "
        "live/unsaved formik value"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.wait_for_canvas()
        reloaded_toggle = pipeline_page.get_tools_module_toggle("attachments")
        expect(reloaded_toggle).to_be_checked(timeout=UI_ELEMENT_TIMEOUT)
        # Auto-retrying assertion: the button's `disabled` attribute can lag a couple
        # seconds behind the toggle's already-correct `checked` value right after a
        # hard reload (confirmed live) — `to_be_enabled` polls until it settles.
        expect(pipeline_page.chat_attach_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step('Step 5 — Toggle "Attachments" back to disabled; attach button disables instantly'):
        pipeline_page.toggle_attachments_module(timeout=UI_ELEMENT_TIMEOUT)
        assert not pipeline_page.is_tools_module_toggle_checked("attachments"), (
            "Attachments MODULES toggle should be unchecked after toggling it off"
        )
        expect(pipeline_page.chat_attach_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 6 — Save the pipeline while Attachments is disabled"):
        save_response = pipeline_page.save_and_wait_for_update(
            project_id, pipeline_id, timeout=SAVE_RESPONSE_TIMEOUT
        )
        assert save_response is not None, "Save should return the persisted pipeline version"

    with allure.step(
        "Step 7 — Reload the pipeline again; toggle stays unchecked and the attach button "
        "stays disabled — proves the OFF state persists too"
    ):
        pipeline_page.navigate(pipeline_id)
        pipeline_page.wait_for_canvas()
        reloaded_toggle_off = pipeline_page.get_tools_module_toggle("attachments")
        expect(reloaded_toggle_off).not_to_be_checked(timeout=UI_ELEMENT_TIMEOUT)
        expect(pipeline_page.chat_attach_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step("Step 8 — No console errors were introduced at any step"):
        assert not console_errors, f"No step should introduce console errors: {console_errors}"
