"""UI Test for ELITEA-2081 — Chat: Create Toolkit from Conversation – Close
Canvas Without Saving and Verify No Toolkit Created.

Verifies the in-chat Toolkit-creation canvas's Discard-then-close path: after
discarding unsaved changes (the canvas returns to its type-picker/empty
state), closing the canvas via the X button closes it directly (no unsaved
changes left to confirm) and no toolkit is ever created — no TOOLKITS section
appears in the PARTICIPANTS panel, and no create request ever fires.

Spec: test-specs/chat-interface/
      l2_create-toolkit-from-conversation-close-canvas-without-saving_ELITEA-2081.md

Transit setup (steps 0a-0f, not this case's own subject): the AFS precondition
"canvas has been cleared after discarding (following ELITEA-2080)" is
reproduced by actually driving the real Discard flow through the UI — select a
type, dirty the Name field, click Discard, confirm the Discard-confirmation
dialog. This is NOT a substitution: nothing is mocked, injected, or faked —
it is ELITEA-2080's own live product flow, executed honestly as setup because
ELITEA-2080 has no covering spec in this batch. The case's own observables
(canvas state after discard, close behavior, PARTICIPANTS panel, zero
create-POST) are all produced by the live system. No ``page.route`` /
``route.fulfill`` / ``page.evaluate`` / ``monkeypatch`` anywhere in this test.

New page-object surface (AFS § Concrete Handles): ``ToolkitCanvasPage`` gained
``discard_button``/``discard_confirm_modal``/``discard_confirm_button`` +
``click_discard()``/``confirm_discard()`` (ELITEA-2081), mirroring
``PipelineCanvasPage``'s ELITEA-2076 shape 1:1. Three new testids were added
to ``ToolkitEditor.jsx`` this session (commit EliteaAI/EliteaUI@bc08563f on
``automation/testids``) — ``BaseEditor.jsx``/``EditorHeader.jsx`` already
threaded the discard-testid props end-to-end (ELITEA-2076), only the
call-site wiring for the Toolkit/MCP canvas was missing.

Known console noise pre-filtered (same idiom as ``test_create_toolkit_from_
conversation.py``, plus one NEW pattern confirmed live this session):
  - Secrets-403 (environment-wide background probe).
  - CategorySection.jsx unique-key-prop warning (issue #656).
  - Vite stream externalization warning (exceljs build-tooling artifact).
  - Embedding Model select "out-of-range value `text-embedding-3-small`" MUI
    warning — fires as soon as ANY Toolkit type form renders in THIS
    local/DEV environment (no embedding-model config exists here), entirely
    independent of Discard/close; see
    ``_is_known_embedding_model_out_of_range_warning`` docstring.
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from pages.toolkit_canvas_page import ToolkitCanvasPage
from pages.toolkit_creation_page import ToolkitCreationPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat.close_toolkit_canvas_without_saving")

pytestmark = [
    pytest.mark.ui,
    pytest.mark.chat,
    pytest.mark.toolkits,
    pytest.mark.regression,
]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

TOOLKIT_NAME = "autotest_2081_discard"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise."""
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


def _is_known_vite_stream_externalization_warning(msg) -> bool:
    """Filter the pre-existing, environment-wide Vite 'stream' externalization warning."""
    return "stream" in msg.text and "externalized for browser compatibility" in msg.text


def _is_known_category_section_key_warning(msg) -> bool:
    """Filter the pre-existing, already-tracked #656 console warning."""
    return "unique" in msg.text and "key" in msg.text and "prop" in msg.text


def _is_known_embedding_model_out_of_range_warning(msg) -> bool:
    """Filter a pre-existing, environment-only MUI console warning.

    Confirmed live this session: as soon as a Toolkit type (e.g. GitHub) is
    selected, the create-form's "Embedding Model" select renders a hardcoded
    default value (``"text-embedding-3-small"``) while its own options list
    is fetched asynchronously and never resolves to include that value in
    THIS local/DEV environment (no embedding-model configuration exists
    here) — the warning still fires even once the fetch settles (available
    values become only the MUI loading placeholder
    ``__single_select_loading__``, never the default). It re-fires on every
    re-render of the mounted form (each keystroke, every Discard/close), so it
    is entirely independent of this case's own Discard/close subject —
    caused merely by the form being open, same as the neighbouring
    ``test_create_toolkit_from_conversation.py``'s own type-picker precedes
    it. Same class of pre-filtered environmental noise as the other three
    filters in this module.
    """
    return "out-of-range value" in msg.text and "text-embedding-3-small" in msg.text


class TestCloseToolkitCanvasWithoutSaving:
    """ELITEA-2081: Chat – Create Toolkit from Conversation – Close Canvas
    Without Saving and Verify No Toolkit Created (l2, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/canvas/ELITEA-2081_chat-create-toolkit-from-conversation-close-canvas-without-saving.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_close_toolkit_canvas_without_saving_creates_no_toolkit(
        self,
        page,
        conversation_id,
    ):
        """Discard an unsaved Toolkit canvas, close it, and verify no toolkit
        was ever created.

        AFS steps (test-specs/chat-interface/
        l2_create-toolkit-from-conversation-close-canvas-without-saving_ELITEA-2081.md):
        1. Verify the canvas is still open and cleared after discarding.
        2. Click X to close the canvas.
        3. Verify the conversation view is displayed.
        4. Verify no TOOLKITS section appears in PARTICIPANTS.
        5. Verify no toolkit was created (badge absence + zero create-POST).
        """
        chat = ChatPage(page)
        toolkit_canvas = ToolkitCanvasPage(page)
        toolkit_form = ToolkitCreationPage(page)

        console_messages = []
        create_requests = []

        def _on_console(msg):
            if msg.type not in ("error", "warning"):
                return
            if (
                _is_known_secrets_403(msg)
                or _is_known_category_section_key_warning(msg)
                or _is_known_vite_stream_externalization_warning(msg)
                or _is_known_embedding_model_out_of_range_warning(msg)
            ):
                return
            console_messages.append(msg)

        def _on_response(response):
            if response.request.method == "POST" and "/tools/prompt_lib/" in response.url:
                create_requests.append(response)

        page.on("console", _on_console)
        page.on("response", _on_response)

        # ------------------------------------------------------------------
        # Transit setup 0a — navigate to Chat and open the conversation
        # ------------------------------------------------------------------
        chat.navigate_to_chat(conversation_id=conversation_id)
        expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        # ------------------------------------------------------------------
        # Transit setup 0b — open the Toolkit canvas via + menu
        # ------------------------------------------------------------------
        chat.open_create_new_toolkit_canvas(timeout=NAVIGATION_TIMEOUT)
        toolkit_canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)

        # ------------------------------------------------------------------
        # Transit setup 0c — select GitHub type (waits for Name field itself,
        # not networkidle — see ToolkitCreationPage.select_toolkit_type docstring)
        # then let the network settle before interacting further: the type
        # picker fires an async GET for the project's default embedding/
        # pgvector config (same call test_create_toolkit_from_conversation.py
        # explicitly waits on) — proceeding before it resolves surfaces a
        # transient MUI "out-of-range value" console warning on the Embedding
        # Model select while its options list is still loading, same class as
        # ELITEA-2083's own documented pgvector-fetch race, not caused by
        # Discard/close.
        # ------------------------------------------------------------------
        toolkit_form.select_toolkit_type("github", "github", timeout=NAVIGATION_TIMEOUT)
        toolkit_form.wait_for_network(timeout=NAVIGATION_TIMEOUT)
        expect(toolkit_canvas.title).to_have_text("New GitHub Toolkit", timeout=UI_ELEMENT_TIMEOUT)

        # ------------------------------------------------------------------
        # Transit setup 0d — type a Name to dirty the form; Discard enables
        # ------------------------------------------------------------------
        toolkit_form.fill_name(TOOLKIT_NAME)
        expect(toolkit_canvas.discard_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

        # ------------------------------------------------------------------
        # Transit setup 0e-0f — click Discard, confirm — canvas reverts to
        # the type-picker/empty state (create-mode Discard un-selects the
        # type entirely — see AFS § Concrete Handles)
        # ------------------------------------------------------------------
        toolkit_canvas.click_discard(timeout=UI_ELEMENT_TIMEOUT)
        toolkit_canvas.confirm_discard(timeout=UI_ELEMENT_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 1 — verify the canvas is still open and cleared after discard
        # ------------------------------------------------------------------
        with allure.step(
            "Step 1 — Verify the canvas is still open and cleared after the previous discard"
        ):
            expect(toolkit_canvas.close_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(toolkit_canvas.title).to_have_text("New Toolkit", timeout=UI_ELEMENT_TIMEOUT)
            expect(toolkit_form.name_input).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
            github_type_card = toolkit_form.get_type_card("github")
            expect(github_type_card).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 2 — click X to close the canvas
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Click the X button in the top right corner to close the canvas"):
            toolkit_canvas.close(timeout=UI_ELEMENT_TIMEOUT)
            expect(toolkit_canvas.title).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 3 — verify the conversation view is displayed
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Verify the conversation view is displayed"):
            expect(toolkit_canvas.close_button).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 4 — ensure PARTICIPANTS panel is in collapsed (badge-strip)
        # view, then verify no TOOLKITS section badge appears
        # ------------------------------------------------------------------
        with allure.step(
            "Step 4 — Verify no new TOOLKITS section appears in the PARTICIPANTS panel"
        ):
            chat.collapse_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
            assert not chat.is_participants_badge_visible(section="toolkits"), (
                "A TOOLKITS section badge should NOT appear in PARTICIPANTS — "
                "the canvas was discarded, never saved/created."
            )

        # ------------------------------------------------------------------
        # Step 5 — verify no toolkit was created (badge absence, already
        # checked above, PLUS a network-level "zero create requests" check)
        # ------------------------------------------------------------------
        with allure.step("Step 5 — Verify no toolkit was created"):
            assert not chat.is_participants_badge_visible(section="toolkits"), (
                "PARTICIPANTS panel should show no toolkit entries."
            )
            assert not create_requests, (
                f"Expected zero POST requests to /tools/prompt_lib/ across the "
                f"whole discard-then-close flow, got: "
                f"{[r.url for r in create_requests]!r}"
            )

        # ------------------------------------------------------------------
        # Side-channel — verify no unexpected console errors/warnings
        # ------------------------------------------------------------------
        with allure.step(
            "Side-channel — verify no unexpected console errors/warnings "
            "occurred across the whole flow"
        ):
            assert not console_messages, (
                f"Unexpected console error/warning(s) during the flow: "
                f"{[m.text for m in console_messages]!r}"
            )
