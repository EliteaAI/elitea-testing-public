"""UI Test for ELITEA-2084 — Chat: Create MCP from Conversation – Enter
Configuration Data and Discard Changes.

Verifies the in-chat "+ Create New MCP" canvas's Discard path: filling in a
Remote MCP's Name/Url/Client Secret, clicking Discard, confirming the
discard-confirmation dialog, and verifying the canvas reverts to the
type-picker/empty state (not merely blank form fields) — then closing the
canvas via X and confirming no MCP was ever created (no MCPS section in the
PARTICIPANTS panel, zero create-POST requests).

Spec: test-specs/chat-interface/
      l2_create-mcp-from-conversation-discard-changes_ELITEA-2084.md

Sibling of the already-automated ELITEA-2085 (Save-and-verify) — reuses the
exact same canvas/form page-object surface (``ChatPage`` + ``McpFormPage`` +
``McpCanvasPage``). New page-object surface (AFS § Concrete Handles):
``McpCanvasPage`` gained ``discard_button``/``discard_confirm_modal``/
``discard_confirm_button`` + ``click_discard()``/``confirm_discard()``
(ELITEA-2084), mirroring ``ToolkitCanvasPage``'s ELITEA-2081 shape 1:1. The
three testid strings already existed on ``automation/testids`` before this
change — added as the ``isMcpTestIdScope``-conditional MCP-branch mirror
during ELITEA-2081's own Toolkit-canvas Discard implementation
(``EliteaAI/EliteaUI@bc08563f``); no new ``add-data-testid`` work was
required for this case.

No substitution anywhere in this test — no ``page.route``/``route.fulfill``/
``page.evaluate``/``monkeypatch``. All observables (canvas state after
discard, close behavior, PARTICIPANTS panel, zero create-POST) are produced
by the live system.

Known console noise pre-filtered (same idiom as ``test_create_mcp_from_
conversation.py``/``test_close_toolkit_canvas_without_saving.py``):
  - Secrets-403 (environment-wide background probe).
  - CategorySection.jsx unique-key-prop warning (issue #656).
  - Vite stream externalization warning (exceljs build-tooling artifact).
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from pages.mcp_canvas_page import McpCanvasPage
from pages.mcp_form_page import McpFormPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat.create_mcp_from_conversation_discard_changes")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.toolkits, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

MCP_NAME = "test"
MCP_URL = "https://api.githubcopilot.com/mcp"
MCP_CLIENT_SECRET = "autotest-dummy-secret"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise."""
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


def _is_known_vite_stream_externalization_warning(msg) -> bool:
    """Filter the pre-existing, environment-wide Vite 'stream' externalization warning."""
    return "stream" in msg.text and "externalized for browser compatibility" in msg.text


def _is_known_category_section_key_warning(msg) -> bool:
    """Filter the pre-existing, already-tracked #656 console warning.

    NOT gated on ``msg.type`` — confirmed live (ELITEA-2085's own AFS) that
    React logs this "Warning: ..." text via ``console.error`` in dev mode,
    i.e. ``msg.type == "error"`` at the browser level, despite the text.
    """
    return "unique" in msg.text and "key" in msg.text and "prop" in msg.text


class TestCreateMcpFromConversationDiscardChanges:
    """ELITEA-2084: Chat – Create MCP from Conversation – Enter Configuration
    Data and Discard Changes (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2084_chat-create-mcp-from-conversation-enter-configuration-data-and-discard-changes.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_create_mcp_from_conversation_discard_changes_creates_no_mcp(
        self, page, conversation_id,
    ):
        """Enter Remote MCP configuration data, Discard, verify the canvas
        reverts to the type-picker/empty state, close it, and verify no MCP
        was ever created.

        Steps (AFS
        test-specs/chat-interface/l2_create-mcp-from-conversation-discard-changes_ELITEA-2084.md):
        1. Navigate to Chats and open a conversation.
        2-3. + icon -> MCPs -> + Create New MCP.
        4. Verify Local/Remote tabs shown.
        5. Click Remote tab, select Remote MCP.
        6-8. Fill Name/Url/Client Secret; verify Discard becomes enabled.
        9. Click Discard; verify the confirmation dialog appears.
        10. Confirm Discard; verify the canvas reverts to the type-picker.
        11. Close the canvas via X.
        12. Verify no MCPS participant + zero create-POST.
        """
        chat = ChatPage(page)
        mcp_canvas = McpCanvasPage(page)
        mcp_form = McpFormPage(page)

        console_messages = []
        create_requests = []

        def _on_console(msg):
            if msg.type not in ("error", "warning"):
                return
            if (
                _is_known_secrets_403(msg)
                or _is_known_category_section_key_warning(msg)
                or _is_known_vite_stream_externalization_warning(msg)
            ):
                return
            console_messages.append(msg)

        def _on_response(response):
            if response.request.method == "POST" and "/tools/prompt_lib/" in response.url:
                create_requests.append(response)

        page.on("console", _on_console)
        page.on("response", _on_response)

        with allure.step("Step 1 — Navigate to Chats and open a conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            'Step 2-3 — Click the + icon, select "MCPs", click "+ Create New '
            'MCP" at the top; verify the "New MCP" canvas opens with '
            '"Choose the MCP type" section'
        ):
            # Reuse the existing, already-proven ChatPage helper (used
            # identically by the merged ELITEA-2085 test) rather than
            # re-deriving the plus-menu -> MCPs -> Create-New click chain —
            # it already absorbs the documented MUI-overlay-interception
            # gotcha on plus_menu_button (`.claude/rules/mui-patterns.md`;
            # AFS test-specs/chat-interface/
            # l2_pipeline-discard-changes-clears-canvas_ELITEA-2076.md, step
            # 2 notes) via pytest-rerunfailures' built-in rerun, same as
            # every other in-chat-canvas test in this suite.
            chat.open_create_new_mcp_canvas(timeout=NAVIGATION_TIMEOUT)
            mcp_canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
            expect(mcp_canvas.title).to_have_text("New MCP", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step('Step 4 — Verify "Local" and "Remote" tabs are shown'):
            expect(
                mcp_form.category_filter_tab.filter(has_text="Local")
            ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(
                mcp_form.category_filter_tab.filter(has_text="Remote")
            ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            'Step 5 — Click the "Remote" tab and select "Remote MCP"; verify '
            "the configuration canvas opens"
        ):
            mcp_form.select_remote_category_tab(timeout=UI_ELEMENT_TIMEOUT)
            mcp_form.remote_mcp_type_card.click()
            mcp_form.name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            expect(mcp_canvas.title).to_have_text("New Remote MCP", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(f'Step 6 — Type "{MCP_NAME}" in "Toolkit Name *" field'):
            mcp_form.fill_name(MCP_NAME)
            assert mcp_form.name_input.input_value() == MCP_NAME

        with allure.step(f'Step 7 — Type "{MCP_URL}" in "Url *" field'):
            mcp_form.fill_url(MCP_URL)
            assert mcp_form.url_input.input_value() == MCP_URL

        with allure.step(
            'Step 8 — Enter a test value in "Client Secret" field; verify '
            "Discard becomes enabled"
        ):
            mcp_form.fill_client_secret(MCP_CLIENT_SECRET)
            assert mcp_form.get_client_secret_value() == MCP_CLIENT_SECRET
            assert mcp_canvas.is_discard_enabled(timeout=UI_ELEMENT_TIMEOUT), (
                "Discard button should become enabled once the form is dirty"
            )

        with allure.step(
            'Step 9 — Click the "Discard" button; verify the confirmation '
            "dialog appears"
        ):
            mcp_canvas.click_discard(timeout=UI_ELEMENT_TIMEOUT)
            expect(mcp_canvas.discard_confirm_modal).to_contain_text(
                "Are you sure you want to discard changes?", timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 10 — Confirm Discard; verify the canvas remains open, "
            "reverted to the type-picker with empty/default fields"
        ):
            mcp_canvas.confirm_discard(timeout=UI_ELEMENT_TIMEOUT)
            expect(mcp_canvas.close_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(mcp_canvas.title).to_have_text("New MCP", timeout=UI_ELEMENT_TIMEOUT)
            expect(mcp_canvas.discard_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)
            expect(mcp_canvas.create_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)
            expect(mcp_form.name_input).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
            expect(mcp_form.url_input).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
            expect(mcp_form.remote_mcp_type_card).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 11 — Click X to close the canvas"):
            mcp_canvas.close(timeout=UI_ELEMENT_TIMEOUT)
            expect(mcp_canvas.close_button).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            'Step 12 — Verify no "MCPS" section appears in the PARTICIPANTS '
            "panel and no MCP was created"
        ):
            assert not chat.is_participants_badge_visible(section="mcp"), (
                "An MCPS section badge should NOT appear in PARTICIPANTS — "
                "the canvas was discarded, never saved/created."
            )
            assert not create_requests, (
                f"Expected zero POST requests to /tools/prompt_lib/ across "
                f"the whole discard-then-close flow, got: "
                f"{[r.url for r in create_requests]!r}"
            )

        with allure.step(
            "Side-channel — verify no unexpected console errors/warnings "
            "occurred across the whole flow"
        ):
            assert not console_messages, (
                f"Unexpected console error/warning(s) during the flow: "
                f"{[m.text for m in console_messages]!r}"
            )
