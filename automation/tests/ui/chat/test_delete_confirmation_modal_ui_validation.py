"""UI Test for ELITEA-2116 — Chat: Delete Confirmation Modal UI Validation.

Verifies the delete-confirmation dialog's title/body text, button styling
(Cancel = secondary, Delete = red/destructive), and dismissal via Escape and
an outside/backdrop click — neither dismissal path deletes the conversation
or fires the underlying DELETE network call.

Spec: test-specs/chat-interface/l3_delete-confirmation-modal-ui-validation_ELITEA-2116.md

Uses project 400 ("UI Testing") — see module docstring in
test_conversation_deletion_inside_folder.py for the isolation rationale.

Known case-text drift (title/body wording) shared with the already-tracked
EliteaAI/elitea-testing-public#695 (ELITEA-2114) — asserted against the LIVE
product text per the reverse-masking guard, not re-filed.

No product defects found beyond the already-tracked #695 wording drift.
"""

import logging

import allure
import pytest
from api.client import ConversationAPI
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

SANDBOX_PROJECT_ID = "400"


class TestDeleteConfirmationModalUIValidation:
    """ELITEA-2116: Chat – Delete Confirmation Modal UI Validation (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2116_chat-delete-confirmation-modal-ui-validation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_delete_confirmation_modal_title_body_and_button_styling(self, page, _browser_cookies):
        """Modal shows correct title/body text and correctly-styled buttons.

        Steps (AFS
        test-specs/chat-interface/l3_delete-confirmation-modal-ui-validation_ELITEA-2116.md):
        1. Open the delete modal — overlay dims the background.
        2. Verify title text.
        3. Verify body text.
        4. Verify Cancel button is secondary/outlined and on the left (DOM order).
        5. Verify Delete button is red/destructive and on the right (DOM order).
        """
        sandbox_api = ConversationAPI(browser_cookies=_browser_cookies, project_id=SANDBOX_PROJECT_ID)
        chat = ChatPage(page)
        conv_id = None

        try:
            with allure.step("Setup — switch to the sandbox project (400); seed a conversation"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(SANDBOX_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)

                conv = sandbox_api.create_conversation("autotest_2116_modal_check")
                conv_id = conv["id"]

                chat.navigate_to_chat(conversation_id=conv_id)
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Hover, click 3-dot, click Delete; verify the dialog "
                "(with its dimming backdrop) becomes visible"
            ):
                chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_conversation_menu_item("delete", timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.delete_confirm_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_delete_dialog_backdrop_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Delete-confirmation dialog's dimming backdrop should be visible"
                )

            with allure.step("Step 2 — Verify modal title text"):
                expect(chat.delete_confirm_title).to_have_text(
                    "Delete confirmation", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 3 — Verify modal body text"):
                expected_message = f"Are you sure to delete the {conv['name']} chat? It can't be restored."
                expect(chat.delete_confirm_message).to_have_text(
                    expected_message, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 4 — Verify Cancel button is positioned to the LEFT of "
                "Delete (bounding-box X comparison — the literal spatial "
                "claim the case makes) and is styled as a secondary/outlined "
                "button"
            ):
                cancel_box = chat.delete_confirm_cancel_button.bounding_box()
                delete_box = chat.delete_confirm_button.bounding_box()
                assert cancel_box is not None and delete_box is not None, (
                    "Both Cancel and Delete buttons should have a resolvable bounding box"
                )
                assert cancel_box["x"] < delete_box["x"], (
                    f"Cancel button should be positioned left of Delete "
                    f"(cancel x={cancel_box['x']}, delete x={delete_box['x']})"
                )
                cancel_class = chat.delete_confirm_cancel_button.get_attribute("class") or ""
                assert "MuiButton-eliteaSecondary" in cancel_class, (
                    f"Cancel button should carry the secondary MUI style class, got: {cancel_class}"
                )

            with allure.step(
                "Step 5 — Verify Delete button is styled as a red/destructive "
                "button (position already proven relative to Cancel above)"
            ):
                delete_class = chat.delete_confirm_button.get_attribute("class") or ""
                assert "MuiButton-eliteaAlarm" in delete_class, (
                    f"Delete button should carry the alarm/destructive MUI style class, got: {delete_class}"
                )
                bg_color = chat.delete_confirm_button.evaluate(
                    "el => getComputedStyle(el).backgroundColor"
                )
                assert bg_color == "rgb(215, 22, 22)", (
                    f"Delete button background should be the destructive red, got: {bg_color}"
                )

        finally:
            try:
                if conv_id:
                    sandbox_api.delete_conversation(conv_id)
            except Exception as exc:
                logger.warning("Cleanup failed for conversation %s: %s", conv_id, exc)
            sandbox_api.close()

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2116_chat-delete-confirmation-modal-ui-validation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_delete_confirmation_modal_dismisses_via_escape_and_outside_click(
        self, page, _browser_cookies,
    ):
        """Both Escape and an outside/backdrop click dismiss the dialog
        without deleting the conversation or firing the DELETE call.

        Steps (AFS
        test-specs/chat-interface/l3_delete-confirmation-modal-ui-validation_ELITEA-2116.md):
        6. Click outside the modal (then, separately, press Escape) — modal
           closes without deleting.
        7. Verify the conversation remains in the list after each dismissal.
        """
        sandbox_api = ConversationAPI(browser_cookies=_browser_cookies, project_id=SANDBOX_PROJECT_ID)
        chat = ChatPage(page)
        conv_id = None

        try:
            with allure.step("Setup — switch to the sandbox project (400); seed a conversation"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(SANDBOX_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)

                conv = sandbox_api.create_conversation("autotest_2116_dismiss_check")
                conv_id = conv["id"]

                chat.navigate_to_chat(conversation_id=conv_id)
                chat.wait_for_page_load()

            with allure.step(
                "Step 6a — Open the dialog, press Escape; verify it closes "
                "without a DELETE network call"
            ):
                delete_requests = chat.capture_requests_matching(
                    url_substring=f"/conversation/prompt_lib/{SANDBOX_PROJECT_ID}/{conv_id}",
                    method="DELETE",
                )
                chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_conversation_menu_item("delete", timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.delete_confirm_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                chat.page.keyboard.press("Escape")
                expect(chat.delete_confirm_dialog).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
                assert len(delete_requests) == 0, (
                    "Escape dismissal should not fire the DELETE request"
                )

            with allure.step("Step 7a — Verify the conversation remains after Escape dismissal"):
                expect(chat.get_conversation_item(conv_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 6b — Reopen the dialog, dismiss via a real mouse click "
                "outside the dialog Paper (case's own literal 'click outside "
                "the modal' instruction); verify it closes without a DELETE call"
            ):
                chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_conversation_menu_item("delete", timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.delete_confirm_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                chat.dismiss_delete_dialog_via_outside_click(timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
                assert len(delete_requests) == 0, (
                    "Outside-click dismissal should not fire the DELETE request"
                )
                delete_requests.stop()

            with allure.step("Step 7b — Verify the conversation remains after outside-click dismissal"):
                expect(chat.get_conversation_item(conv_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        finally:
            try:
                if conv_id:
                    sandbox_api.delete_conversation(conv_id)
            except Exception as exc:
                logger.warning("Cleanup failed for conversation %s: %s", conv_id, exc)
            sandbox_api.close()
