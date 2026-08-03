"""UI Test for ELITEA-2085 — Chat: Create MCP from Conversation – Save
Configuration and Verify MCP is Created.

Verifies the full "+ Create New MCP" in-chat canvas flow: creating a Remote
MCP, verifying the "Not Connected" disconnected-status banner, closing the
canvas, and confirming the MCP is added as an MCPS participant with the
disconnected warning shown in the PARTICIPANTS panel.

Spec: test-specs/chat-interface/l2_create-mcp-from-conversation-save-and-verify_ELITEA-2085.md

New page-object surface (AFS § Automation Hints): the MCP-creation form
itself is the exact same ``ToolkitForm``/``ToolkitTypeSelector`` component
set the standalone ``McpFormPage`` already drives — composed directly on
the same ``page`` alongside ``ChatPage`` (canvas entry point, participants)
and the new ``McpCanvasPage`` (close button, title, Create button),
mirroring ``test_create_agent_via_chat_canvas.py``'s ``ChatPage`` +
``AgentFormPage`` composition.

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``):
- ``mcp-canvas-create-button`` — new optional ``testId`` prop on
  ``CreateToolkitButton.jsx`` (declared improvisation — no prior precedent
  for this specific button; ``ToolkitEditor.jsx`` wires it conditional on
  ``isMCP``, leaving the plain-Toolkit creation path untouched).
- ``mcp-canvas-title`` / ``mcp-canvas-close-button`` — threaded as
  ``ToolkitEditor.jsx``'s ``<BaseEditor titleTestId=... closeButtonTestId=
  ...>`` call, conditional on ``isMCP`` (the props already exist end-to-end,
  same shape as ``agent-canvas-title``/``agent-canvas-close-button`` added
  for ELITEA-2166).
- ``chat-participant-warning-icon`` — added to ``ParticipantItem.jsx``'s
  attention-icon/message row (the actual DOM location of the orange
  warning triangle + disconnected text; the AFS attributed this to
  ``ParticipantWarning.jsx``, which renders only the message text — the
  icon itself lives one component up, in the row that wraps both).
  Unconditional (the component is already entity-type-agnostic, shared
  between MCP and Pipeline participant warnings per issues #684/#687).

Known defect handling: none — this case's happy path is fully clean per the
AFS. A pre-existing, already-tracked React console warning ("unique key
prop" in ``CategorySection.jsx``, issue #656) fires during step 3's
type-selection render — filtered here the same way ``test_edit_instructions``
filters its own known dev-only noise (#538), so it can't mask a genuinely
new console error appearing alongside it.
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from pages.chat_page import ChatPage
from pages.mcp_canvas_page import McpCanvasPage
from pages.mcp_form_page import McpFormPage

logger = logging.getLogger("elitea.tests.chat.create_mcp_from_conversation")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.toolkits, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

MCP_NAME = "test"
MCP_URL = "https://api.githubcopilot.com/mcp"
MCP_CLIENT_SECRET = "autotest-dummy-secret"

DISCONNECTED_PARTICIPANT_TEXT = "Server is disconnected!  Reconnect it to use. Log in."


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_create_agent_via_chat_canvas.py`` — an unrelated
    toolkit/secrets panel probe that fires on every page load in this
    local environment, not caused by this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


def _is_known_vite_stream_externalization_warning(msg) -> bool:
    """Filter the pre-existing, environment-wide Vite "stream" externalization
    warning.

    ``exceljs`` (an artifact/export dependency, unrelated to chat/MCP) pulls in
    ``crypto-browserify``/``cipher-base``, which references the Node builtin
    ``stream`` module; Vite's dev server externalizes it for browser
    compatibility and logs a warning the first time that vendor chunk loads in
    a session. Confirmed via source (`node_modules/.vite/deps/exceljs.js`) to
    be a build-tooling artifact of an unrelated dependency, not something this
    flow (or any single page) triggers deliberately — added here (discovered
    while making the ELITEA-2085 console-message assertion real, not
    previously filtered because nothing asserted on `console_messages` before)
    so it can't mask a genuinely new warning, matching the `_is_known_secrets_403`
    / `_is_known_category_section_key_warning` idiom.
    """
    return "stream" in msg.text and "externalized for browser compatibility" in msg.text


def _is_known_category_section_key_warning(msg) -> bool:
    """Filter the pre-existing, already-tracked #656 console warning.

    ``CategorySection.jsx`` (inside ``ToolkitTypeSelector.jsx``, shared by
    both the standalone Toolkit-creation flow and this MCP-creation flow)
    renders a list without a unique 'key' prop — confirmed via the AFS's
    dedup check to already be tracked as issue #656, filed during
    ELITEA-1868 analysis. Same root cause, same component; not a new
    defect. Matches ``test_edit_instructions``'s own known-noise filter
    (#538) idiom.

    NOT gated on ``msg.type`` — confirmed live (while making the
    ELITEA-2085 console-message assertion real) that React logs this
    "Warning: ..." text via ``console.error`` in dev mode, i.e.
    ``msg.type == "error"`` at the browser level, not ``"warning"``,
    despite the text. A prior version of this filter gated on
    ``msg.type == "warning"`` and was therefore a silent no-op for the
    one message it exists to catch.
    """
    return (
        "unique" in msg.text
        and "key" in msg.text
        and "prop" in msg.text
    )


class TestCreateMcpFromConversation:
    """ELITEA-2085: Chat – Create MCP from Conversation – Save Configuration
    and Verify MCP is Created (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2085_chat-create-mcp-from-conversation-save-configuration-and-verify-mcp-is-created.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_create_mcp_from_conversation_save_and_verify(
        self, page, conversation_id, toolkit_api,
    ):
        """Create a Remote MCP via the in-chat canvas; verify the
        disconnected banner, the composer close, and the PARTICIPANTS
        panel's MCPS section + disconnected warning.

        Steps (AFS
        test-specs/chat-interface/l2_create-mcp-from-conversation-save-and-verify_ELITEA-2085.md):
        1. Navigate to Chats and open a conversation.
        2. + icon -> MCPs -> + Create New MCP.
        3. Click Remote tab, select Remote MCP.
        4-6. Fill Name/Url/Client Secret.
        7. Click Create; verify the creation POST resolves 201 and a
           success toast.
        8. Verify the canvas header shows "test".
        9. Verify the "Not Connected" banner.
        10. Close the canvas.
        11. Verify the MCPS participant section.
        12. Verify the disconnected warning icon + exact text.
        """
        chat = ChatPage(page)
        mcp_canvas = McpCanvasPage(page)
        mcp_form = McpFormPage(page)

        toolkit_id = None

        console_messages = []

        def _on_console(msg):
            # React's dev-mode "key" prop warning is logged via console.error
            # (browser msg.type == "error"), NOT console.warn, despite its
            # "Warning: ..." text — confirmed live while making this
            # assertion real. Gating the #656 filter on msg.type == "warning"
            # (as a prior version of this handler did) is a no-op for that
            # specific message and lets it slip through as an "unexpected
            # error", so every known-noise filter below is checked regardless
            # of msg.type; only genuinely new console.error/warning survives.
            if msg.type not in ("error", "warning"):
                return
            if (
                _is_known_secrets_403(msg)
                or _is_known_category_section_key_warning(msg)
                or _is_known_vite_stream_externalization_warning(msg)
            ):
                return
            console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step("Step 1 — Navigate to Chats and open a conversation"):
                chat.navigate_to_chat(conversation_id=conversation_id)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 2 — Click + icon, select "MCPs", click "+ Create New '
                'MCP"; verify the "New MCP" canvas opens'
            ):
                chat.open_create_new_mcp_canvas(timeout=NAVIGATION_TIMEOUT)
                mcp_canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 3 — Click "Remote" tab and select "Remote MCP"; '
                "verify the Configuration canvas opens"
            ):
                mcp_form.select_remote_category_tab(timeout=UI_ELEMENT_TIMEOUT)
                mcp_form.remote_mcp_type_card.click()
                mcp_form.name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(f'Step 4 — Type "{MCP_NAME}" in "Toolkit Name *" field'):
                mcp_form.fill_name(MCP_NAME)
                assert mcp_form.name_input.input_value() == MCP_NAME

            with allure.step(f'Step 5 — Type "{MCP_URL}" in "Url *" field'):
                mcp_form.fill_url(MCP_URL)
                assert mcp_form.url_input.input_value() == MCP_URL

            with allure.step('Step 6 — Enter a test secret value in "Client Secret" field'):
                mcp_form.fill_client_secret(MCP_CLIENT_SECRET)
                assert mcp_form.get_client_secret_value() == MCP_CLIENT_SECRET

            with allure.step(
                'Step 7 — Click the "Create" button; verify the creation '
                "POST resolves 201 and a success toast appears"
            ):
                with page.expect_response(
                    lambda r: r.request.method == "POST"
                    and "/tools/prompt_lib/" in r.url
                ) as create_resp_info:
                    mcp_canvas.create_button.click()
                create_response = create_resp_info.value
                assert create_response.status == 201, (
                    f"MCP-creation POST should resolve 201, got "
                    f"{create_response.status} for {create_response.url}"
                )
                created_toolkit = create_response.json()
                toolkit_id = created_toolkit.get("id")
                assert toolkit_id, (
                    f"Expected a numeric toolkit id in the creation "
                    f"response, got: {created_toolkit!r}"
                )
                expect(chat.toast_message).to_contain_text(
                    "The toolkit has been created successfully", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step('Step 8 — Verify the canvas header shows "test" as the MCP name'):
                expect(mcp_canvas.title).to_have_text(MCP_NAME, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 9 — Verify a "Not Connected" warning banner appears '
                'with a "Login" button'
            ):
                status_text = mcp_form.get_connection_status_text(timeout=UI_ELEMENT_TIMEOUT)
                assert "Not Connected" in status_text, (
                    f"Connection status should read 'Not Connected', got: {status_text!r}"
                )
                expect(mcp_form.login_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(mcp_form.login_button).to_have_text("Login", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 10 — Click X to close the canvas"):
                mcp_canvas.close(timeout=UI_ELEMENT_TIMEOUT)
                expect(mcp_canvas.close_button).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(mcp_form.name_input).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(mcp_form.url_input).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 11 — Verify a "MCPS" section appears in the '
                'PARTICIPANTS panel with "test" listed'
            ):
                popper = chat.open_participants_popover(
                    timeout=UI_ELEMENT_TIMEOUT, section="mcp"
                )
                # Live DOM text is "MCPs" (ParticipantSection.jsx's own
                # `${entityType.toLowerCase() !== 'mcp' ? entityType : 'MCP'}s`
                # title logic — a trailing lowercase 's', not the case's
                # all-caps "MCPS" wording) — asserting the live text per the
                # reverse-masking guard rather than the case's literal casing.
                expect(popper).to_contain_text("MCPs", timeout=UI_ELEMENT_TIMEOUT)
                expect(popper).to_contain_text(MCP_NAME, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 12 — Verify the orange warning triangle icon and "
                'exact disconnected text: "Server is disconnected! '
                'Reconnect it to use. Log in."'
            ):
                # ParticipantItem.jsx only applies the row-level
                # `chat-participant-row-{uniqueId}` testid on its HEALTHY
                # rendering branch (`content`, gated on
                # `!mcpIsDisconnected && !remoteMcpLoggedOut && ...`) — a
                # freshly-created, never-logged-in MCP renders through the
                # attention/warning branch instead, which carries no
                # row-level testid at all (confirmed live, ELITEA-2085; the
                # AFS's Concrete Handles table did not verify a row testid
                # for this specific disconnected state). Exactly one
                # participant exists in this fresh conversation, so no
                # per-row disambiguation is needed — scope directly on the
                # popper via the warning-icon testid already added for
                # this case.
                warning_icon = popper.locator(chat.PARTICIPANT_WARNING_ICON)
                expect(warning_icon).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(warning_icon).to_contain_text(
                    DISCONNECTED_PARTICIPANT_TEXT.strip(), timeout=UI_ELEMENT_TIMEOUT
                )
                chat.dismiss_participants_popover()

            with allure.step(
                "Side-channel — verify no unexpected console errors/warnings "
                "occurred across the whole flow (known secrets-403 noise and "
                "the pre-existing #656 key-prop warning are pre-filtered by "
                "_on_console, so any survivor here is a genuinely new issue)"
            ):
                assert not console_messages, (
                    f"Unexpected console error/warning(s) during the flow: "
                    f"{[m.text for m in console_messages]!r}"
                )
        finally:
            with allure.step("Cleanup — delete the created MCP/toolkit"):
                # conversation_id fixture handles conversation cleanup —
                # the MCP is an independent entity that does NOT
                # cascade-delete from conversation deletion (AFS § Cleanup).
                if toolkit_id:
                    try:
                        toolkit_api.delete_toolkit(toolkit_id)
                        logger.info("Deleted toolkit %s", toolkit_id)
                    except Exception as exc:
                        logger.warning(
                            "Cleanup failed for toolkit %s: %s", toolkit_id, exc
                        )
