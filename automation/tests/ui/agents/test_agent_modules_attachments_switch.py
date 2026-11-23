"""Attachments module switch in "+ Modules" controls the agent chat attach icon
and file attachment (ELITEA-4791).

The gating follows the SAVED agent version (useAgentAttachments.js), so each
state is Save -> reload -> open the Test Agent panel. With the switch OFF the
attach icon is disabled (no click possible); the "Attachments are not allowed."
error appears on drag-and-drop, driven by a synthetic DragEvent (declared
improvisation: Playwright cannot perform an OS drag).

Spec: test-specs/agents/l0_attachments-module-switch-controls-chat-attach-icon-and-file-attachment_ELITEA-4791.md
"""

import uuid

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.agents]

TIMEOUT = 15_000
MODULE = "attachments"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
    "agents/modules/ELITEA-4791_attachments-module-switch-controls-chat-attach-icon.md",
    "onetest-ai Test Case link",
)
@pytest.mark.tms("ELITEA-4791")
@pytest.mark.p0
@pytest.mark.regression
def test_attachments_module_switch_controls_chat_attach(page, agent_id, tmp_path):
    marker = f"ELITEA4791-MARKER-{uuid.uuid4().hex[:8]}"
    sample = tmp_path / "sample.txt"
    sample.write_text(
        f"Project note: the secret codeword for this file is {marker}. "
        "Please mention the codeword when summarizing.\n"
    )
    detail = AgentDetailPage(page)
    detail.navigate(agent_id)
    detail.dismiss_platform_release_banner_if_present()

    def set_attachments(on: bool):
        detail.open_modules_menu(timeout=TIMEOUT)
        if detail.module_is_on(MODULE) != on:
            detail.toggle_module_at_name(MODULE)
        if on:
            expect(detail.module_toggle(MODULE)).to_be_checked(timeout=TIMEOUT)
        else:
            expect(detail.module_toggle(MODULE)).not_to_be_checked(timeout=TIMEOUT)
        page.keyboard.press("Escape")
        expect(detail.modules_menu).to_have_count(0, timeout=TIMEOUT)
        expect(detail.save_button).to_be_enabled(timeout=TIMEOUT)
        detail.click_save()
        expect(detail.save_button).to_be_disabled(timeout=TIMEOUT)
        page.reload()
        detail.wait_for_page_load()
        detail.dismiss_platform_release_banner_if_present()

    with allure.step("Step 1 — Switch Attachments ON in + Modules and Save"):
        set_attachments(True)
        detail.open_modules_menu(timeout=TIMEOUT)
        expect(detail.module_toggle(MODULE)).to_be_checked(timeout=TIMEOUT)
        page.keyboard.press("Escape")
        expect(detail.modules_menu).to_have_count(0, timeout=TIMEOUT)

    with allure.step("Step 2 — Chat panel: attach icon is displayed and enabled"):
        detail.open_test_agent_panel(timeout=TIMEOUT)
        expect(detail.chat_attach_button).to_be_visible(timeout=TIMEOUT)
        expect(detail.chat_attach_button).to_be_enabled(timeout=TIMEOUT)

    with allure.step("Step 3 — Attach sample.txt and send; the Agent replies based on the file"):
        detail.attach_file_via_chat_icon(str(sample))
        expect(detail.chat_attachment_chips()).to_have_count(1, timeout=TIMEOUT)
        assert any("sample.txt" in t for t in detail.chat_attachment_chip_texts())
        detail.send_chat_message("Summarize the attached file")
        text, chips = detail.wait_for_reply_with_tool_chip(marker)
        assert any("Attachments" in c for c in chips), f"no Attachments tool chip: {chips}"
        assert marker in text, f"reply is not based on the file content (marker missing): {text[:300]}"

    with allure.step("Step 4 — Switch Attachments OFF and Save"):
        set_attachments(False)
        detail.open_modules_menu(timeout=TIMEOUT)
        expect(detail.module_toggle(MODULE)).not_to_be_checked(timeout=TIMEOUT)
        page.keyboard.press("Escape")
        expect(detail.modules_menu).to_have_count(0, timeout=TIMEOUT)

    with allure.step("Step 5 — Chat panel: attach icon is disabled"):
        detail.open_test_agent_panel(timeout=TIMEOUT)
        expect(detail.chat_attach_button).to_be_disabled(timeout=TIMEOUT)

    with allure.step("Step 6 — Drop sample.txt into the chat: not attached, error toast shown"):
        detail.drop_file_on_chat_input("sample.txt", marker)
        expect(detail.toast_message.last).to_have_text("Attachments are not allowed.", timeout=TIMEOUT)
        assert detail.chat_attachment_chip_count() == 0, "file attached while Attachments is OFF"
