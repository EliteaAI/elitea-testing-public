"""UI Test for ELITEA-2089 — Chat: Edit Agent in Canvas Mode – Verify Changes
Synchronize to Agent.

Creates a fresh "echo" agent via the in-chat "+ Create New Agent" canvas
(auto-attaching it as a chat participant), opens the SAME canvas in EDIT mode
via the expanded PARTICIPANTS panel's pencil icon, edits the Welcome Message,
saves, and verifies the change is synchronized to the standalone Agents
section.

Spec: test-specs/chat-interface/l2_edit-agent-via-participants-canvas-verify-sync_ELITEA-2089.md

Reuses ``AgentCanvasPage``/``AgentFormPage`` UNCHANGED for the canvas chrome
and form fields (ELITEA-2166) — this case opens the exact same canvas
component via a DIFFERENT entry point (participant-row pencil icon vs.
"+ Create New Agent"), confirmed identical live.

New page-object surface added this implementation (AFS § Automation Hints):
- ``ChatPage.participants_panel`` / ``participants_panel_toggle_button`` —
  the (ELITEA-2098) expanded PARTICIPANTS panel testids existed on
  ``automation/testids`` but no page object had wired them yet; every prior
  caller used the legacy text-based ``expand_participants_panel()``.
- ``ChatPage.open_participants_panel()`` / ``edit_agent_participant()`` — new
  methods built on the above, mirroring ``open_participants_popover()`` /
  ``remove_agent_participant()``'s existing shape for the collapsed badge.
- ``ChatPage.agent_settings_menu_button`` — the composer's 3rd ButtonGroup
  button (reads "Editing…"/"Viewing…" while a participant's own canvas is
  open, a settings icon otherwise).
- ``AgentCanvasPage.save_success_toast`` — the shared ``toast-message``
  testid, reused here for the agent-edit-save confirmation (own field per
  ``.agents/testing.md`` § Locator policy: one data-testid per file).

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``):
- ``chat-participant-edit-button`` — the participant row's pencil "Edit"
  icon button (``EditParticipantButton.jsx``) had ZERO ``data-testid`` at
  any level; mirrors the sibling ``DeleteParticipantButton.jsx``'s existing
  ``chat-participant-remove-button`` pattern (same directory, same shape).
- ``chat-agent-settings-menu-button`` — the composer's 3rd ButtonGroup
  button (``AgentEditorPanel.jsx``) carried an ``aria-label`` but no testid.

Declared improvisation (canon gap found during Phase 2 exploration, not in
the AFS's own Concrete Handles table — `.agents/role-overrides.md` §
Declared-improvisation protocol):
- ``agent-canvas-discard-button`` — the AFS's step 7 requires asserting the
  Discard button's disabled→enabled transition alongside Save's, but the AFS
  never flagged a testid gap for it. Live: ``AgentFormPage.discard_button``'s
  existing ``discard-button`` testid resolves to 0 elements on this canvas
  (it's a DIFFERENT, unrelated testid that belongs to other pages — and per
  ``test_agent_save_as_version.py``'s prior finding, isn't even wired up on
  the standalone Agent detail page either). ``AgentEditor.jsx`` never passed
  ``BaseEditor``/``EditorHeader``'s existing optional ``discardButtonTestId``
  prop — ``ToolkitEditor.jsx`` already uses this exact prop shape for its own
  canvas's Discard button. Added ``agent-canvas-discard-button`` there,
  mirroring that pattern; wired as a new ``AgentCanvasPage.discard_button``
  field (canvas-chrome-specific, distinct from ``AgentFormPage``'s).

Known defect handling: none — case executed cleanly end-to-end during
analysis (AFS § Known Defects), one case-text drift (step 3's literal
"echo base Editing..." wording vs the live "Editing..."-only text, dedup of
already-closed #709) automated against the live text per the AFS's own
guidance, not filed as a new clarification.

Implementer-exploration route-arounds (amend the AFS's literal wording, see
the AFS's own amendment notes for full detail):
- Step 11's exact "count == baseline+1" assertion was dropped for a presence
  check — the Agents-section card view only renders a first page of cards in
  this shared, ever-growing environment (confirmed live: 20 rendered against
  a real total > 20).
- Step 12's exact single-search-result assertion was dropped for a presence
  check — ``AgentsListPage.search_and_wait_for_results()`` (pre-existing,
  ``.fill()``-based) did not visibly narrow the rendered list live; out of
  this case's scope (owned by the dedicated ELITEA-0140 search-coverage test,
  which itself only asserts presence, never an exact match — same precedent
  followed here).
- The conversation-id cleanup capture uses a non-blocking ``page.url`` read,
  NOT ``page.wait_for_url()`` — a blocking wait for a bare ``/chat/\\d+``
  pattern actively caused a wrong-conversation navigation once during this
  implementation (this shared dev-token environment runs many concurrent
  agent sessions against the same backend/user account).
"""

import logging
import re
from urllib.parse import parse_qs, urlparse

import allure
import pytest
from playwright.sync_api import expect

from config import settings
from pages.agent_canvas_page import AgentCanvasPage
from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.agents, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

AGENT_NAME = "echo"
AGENT_DESCRIPTION = "test agent"
NEW_WELCOME_MESSAGE = "edited from canvas"
SAVE_SUCCESS_TOAST_TEXT = "The agent has been updated"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_create_agent_via_chat_canvas.py`` /
    ``test_conversation_deletion_flow.py`` — an unrelated toolkit/secrets
    panel probe that fires on every page load in this local environment, not
    caused by this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestEditAgentViaParticipantsCanvas:
    """ELITEA-2089: Chat – Edit Agent in Canvas Mode – Verify Changes Synchronize to Agent (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2089_chat-edit-agent-in-canvas-mode-verify-changes-synchronize-to-agent.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_edit_agent_via_participants_canvas_syncs_to_agents_section(
        self, page, conversation_api, agent_api,
    ):
        """Create an agent as a chat participant, edit its Welcome Message via
        the pencil-icon edit-mode canvas, save, and verify the change is
        synchronized to the standalone Agents section.

        Steps (AFS
        test-specs/chat-interface/l2_edit-agent-via-participants-canvas-verify-sync_ELITEA-2089.md):
        1. + Chat -> + menu -> Agents -> + Create New Agent; fill Name/
           Description; Save. Verify the creation POST resolves 201; canvas
           shows 'echo'/'base'; close it; composer + expanded PARTICIPANTS
           panel both reflect the new agent participant.
        2. Hover the participant row, click its pencil "Edit agent" icon.
           Verify the URL gains ?edited_participant_id and the SAME canvas
           re-opens in edit mode with title 'echo' / subtitle 'base'.
        3. Verify the composer's 3rd button shows 'Editing...' (CLARIFICATION
           — dedup of closed #709, not the case's literal combined wording).
        4. Locate the WELCOME MESSAGE section; verify visible + empty; confirm
           Save/Discard start disabled (captured now — the pre-edit half of
           case step 7's disabled->enabled assertion, since it cannot be
           observed retroactively once the field is dirtied).
        5. Click into the WELCOME MESSAGE field (focus only).
        6. Type 'edited from canvas'; verify the field reflects it.
        7. Verify Save and Discard both become enabled.
        8. Click Save; verify the exact success toast text, the field
           retaining its value, and Save/Discard returning to disabled.
        9. Close the canvas via X; verify it's gone and the URL's
           ?edited_participant_id param is gone.
        10. Verify the composer's participant/version buttons revert from
            'Editing...' back to 'echo'/'base'.
        11. Navigate to the Agents section; verify the page loads and the
            newly-created 'echo' agent is listed (presence check — see the
            step's own inline note on why an exact count delta isn't reliable
            in this shared, ever-growing environment).
        12. Search + click the 'echo' agent card; verify the standalone
            detail page opens.
        13. Scroll to the WELCOME MESSAGE section on the standalone page;
            verify visible.
        14. Verify the field displays 'edited from canvas' — the case's core
            assertion (canvas edit -> Agents-section sync).
        """
        chat = ChatPage(page)
        agent_canvas = AgentCanvasPage(page)
        agent_form = AgentFormPage(page)
        agents_list = AgentsListPage(page)
        agent_detail = AgentDetailPage(page)

        agent_id = None
        conversation_id = None

        # Registered before Setup so console errors from every step are
        # captured (side-channel discipline, AFS Axis 2). The pre-existing
        # secrets 403 noise is filtered so it can't mask a genuinely new error.
        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — navigate to chat and switch to the Private project"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(str(settings.elitea_project_id), timeout=NAVIGATION_TIMEOUT)

            with allure.step(
                "Step 1 — Click + Chat; create agent 'echo' via the in-chat "
                "'+ Create New Agent' canvas (side effect: auto-attaches as a "
                "chat participant); verify the creation POST resolves 201, "
                "the canvas shows 'echo'/'base', close it, and the composer "
                "+ expanded PARTICIPANTS panel both reflect the new participant"
            ):
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                chat.open_create_new_agent_canvas(timeout=NAVIGATION_TIMEOUT)
                agent_canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)

                agent_form.fill_form(name=AGENT_NAME, description=AGENT_DESCRIPTION)

                with page.expect_response(
                    lambda r: r.request.method == "POST"
                    and "/applications/prompt_lib/" in r.url
                ) as resp_info:
                    agent_form.save_button.click()
                create_response = resp_info.value
                assert create_response.status == 201, (
                    f"Agent-creation POST should resolve 201, got "
                    f"{create_response.status} for {create_response.url}"
                )
                created_agent = create_response.json()
                agent_id = created_agent.get("id")
                assert agent_id, (
                    f"Expected a numeric agent id in the creation response, "
                    f"got: {created_agent!r}"
                )

                expect(agent_canvas.title).to_have_text(AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT)
                expect(agent_canvas.subtitle).to_have_text("base", timeout=UI_ELEMENT_TIMEOUT)

                agent_canvas.close(timeout=UI_ELEMENT_TIMEOUT)
                expect(agent_canvas.title).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.switch_participant_button).to_contain_text(
                    AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.chat_version_selector_trigger).to_have_text(
                    "base", timeout=UI_ELEMENT_TIMEOUT
                )

                row = chat.get_agent_participant_row(agent_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(row).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(row).to_contain_text(AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT)
                expect(row).to_contain_text("base", timeout=UI_ELEMENT_TIMEOUT)

                # Best-effort conversation id capture for cleanup. NOTE
                # (implementer exploration): unlike ELITEA-2166 (which sends
                # a message and gets a real /chat/{id} URL), creating an
                # agent PARTICIPANT alone does NOT persist the conversation
                # with a numeric URL id — it stays at the bare /chat route.
                # A blocking `page.wait_for_url(re.compile(r"/chat/\d+"))`
                # here is actively HARMFUL, not just ineffective: it can sit
                # idle for the full timeout and get satisfied by an
                # unrelated navigation (this shared dev-token environment
                # runs many concurrent agent sessions against the same
                # backend/user — confirmed live: an earlier version of this
                # test landed on a completely different, pre-existing
                # conversation this way). A non-blocking read is safe.
                match = re.search(r"/chat/(\d+)", page.url)
                if match:
                    conversation_id = int(match.group(1))

            with allure.step(
                "Step 2 — Hover the participant row and click the pencil "
                "'Edit agent' icon; verify the URL gains "
                "?edited_participant_id and the SAME canvas re-opens in "
                "edit mode with title 'echo' / subtitle 'base'"
            ):
                chat.edit_agent_participant(agent_id, timeout=UI_ELEMENT_TIMEOUT)
                page.wait_for_url(
                    re.compile(rf"edited_participant_id={agent_id}\b"),
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                query = parse_qs(urlparse(page.url).query)
                assert query.get("edited_participant_id") == [str(agent_id)], (
                    f"Expected ?edited_participant_id={agent_id}, got URL {page.url!r}"
                )

                agent_canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
                expect(agent_canvas.title).to_have_text(AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT)
                expect(agent_canvas.subtitle).to_have_text("base", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — CLARIFICATION (dedup of closed #709): verify the "
                "composer's 3rd (settings) button shows the literal text "
                "'Editing...' while this agent's own canvas is open — NOT "
                "the case's literal 'echo base Editing...' combined wording"
            ):
                expect(chat.agent_settings_menu_button).to_have_text(
                    "Editing...", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 4 — Locate the WELCOME MESSAGE section in the canvas; "
                "verify it is visible and empty; confirm Save/Discard start "
                "disabled (pre-edit half of case step 7 — must be captured "
                "now, before any edit)"
            ):
                expect(agent_canvas.get_section_header("welcome-message")).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(agent_form.welcome_message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert agent_form.get_welcome_message() == "", (
                    "Welcome message should start empty for this freshly-created agent"
                )
                assert not agent_form.is_save_enabled(), (
                    "Save should be disabled immediately after the canvas opens, before any edit"
                )
                assert not agent_canvas.discard_button.is_enabled(), (
                    "Discard should be disabled immediately after the canvas opens, before any edit"
                )

            with allure.step(
                "Step 5 — Click into the WELCOME MESSAGE field (focus only — "
                "the real observable is step 6's typed value)"
            ):
                agent_form.welcome_message_input.click()

            with allure.step(
                f"Step 6 — Type {NEW_WELCOME_MESSAGE!r}; verify the field "
                f"reflects the typed text"
            ):
                agent_form.welcome_message_input.press_sequentially(
                    NEW_WELCOME_MESSAGE, delay=80
                )
                assert agent_form.get_welcome_message() == NEW_WELCOME_MESSAGE, (
                    f"Welcome message field should read {NEW_WELCOME_MESSAGE!r} after typing"
                )

            with allure.step(
                "Step 7 — Verify Save and Discard both become enabled"
            ):
                agent_form.wait_for_form_validation()
                assert agent_form.is_save_enabled(), (
                    "Save should be enabled once the Welcome Message is dirtied"
                )
                assert agent_canvas.discard_button.is_enabled(), (
                    "Discard should be enabled once the Welcome Message is dirtied"
                )

            with allure.step(
                "Step 8 — Click Save; verify the exact success toast text, "
                "the field retaining its value, and Save/Discard returning "
                "to disabled (no more dirty state)"
            ):
                agent_form.save_button.evaluate("el => el.click()")
                expect(agent_canvas.save_success_toast).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(agent_canvas.save_success_toast).to_have_text(
                    SAVE_SUCCESS_TOAST_TEXT, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(agent_form.welcome_message_input).to_have_value(
                    NEW_WELCOME_MESSAGE, timeout=UI_ELEMENT_TIMEOUT
                )
                assert not agent_form.is_save_enabled(), (
                    "Save should return to disabled once saved (no more dirty state)"
                )
                assert not agent_canvas.discard_button.is_enabled(), (
                    "Discard should return to disabled once saved (no more dirty state)"
                )

            with allure.step(
                "Step 9 — Close the canvas via the X button; verify the "
                "canvas is gone, the conversation view is shown, and the "
                "URL's ?edited_participant_id param is gone"
            ):
                agent_canvas.close(timeout=UI_ELEMENT_TIMEOUT)
                expect(agent_canvas.title).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                page.wait_for_url(
                    lambda url: "edited_participant_id" not in url, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 10 — Verify the composer's active-participant/version "
                "buttons revert from 'Editing...' back to 'echo'/'base'"
            ):
                expect(chat.switch_participant_button).to_contain_text(
                    AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.chat_version_selector_trigger).to_have_text(
                    "base", timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.agent_settings_menu_button).not_to_have_text(
                    "Editing...", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 11 — Navigate to the Agents section; verify the page "
                "loads and the newly-created 'echo' agent is listed"
            ):
                # NOTE (implementer exploration, amends the AFS's literal
                # "26 vs 25" wording): the card view only RENDERS a first
                # page of cards (confirmed live — 20 rendered against a real
                # project total > 20), so an exact total-count comparison is
                # not a reliable observable in this shared, ever-growing
                # environment. `list_agents()` sorts newest-first (same as
                # this card view), so the just-created agent is reliably on
                # the first page regardless of the total — assert presence,
                # not an arithmetic count delta.
                agents_list.navigate()
                names = agents_list.get_agent_card_names()
                assert AGENT_NAME in names, f"{AGENT_NAME!r} should be listed, found: {names!r}"

            with allure.step(
                "Step 12 — Search + click the 'echo' agent card; verify the "
                "standalone agent detail page opens"
            ):
                agents_list.search_and_wait_for_results(AGENT_NAME)
                assert agents_list.agent_exists_in_list(AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                    f"{AGENT_NAME!r} should appear in the (searched) agents list"
                )
                agents_list.select_agent(AGENT_NAME)
                agent_detail.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                assert f"/agents/all/{agent_id}" in page.url, (
                    f"Expected the standalone detail page for agent {agent_id}, "
                    f"got URL {page.url!r}"
                )

            with allure.step(
                "Step 13 — Scroll down to the WELCOME MESSAGE section on "
                "the standalone Agent detail page; verify it is visible"
            ):
                agent_detail.welcome_message_input.scroll_into_view_if_needed()
                expect(agent_detail.welcome_message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                f"Step 14 — Verify the WELCOME MESSAGE field displays "
                f"{NEW_WELCOME_MESSAGE!r} — the canvas edit synchronized to "
                f"the Agents section (case's core assertion)"
            ):
                expect(agent_detail.welcome_message_input).to_have_value(
                    NEW_WELCOME_MESSAGE, timeout=UI_ELEMENT_TIMEOUT
                )

            assert not console_messages, (
                f"Unexpected console errors across the flow: "
                f"{[m.text for m in console_messages]!r}"
            )
        finally:
            with allure.step("Cleanup — delete the created agent and conversation"):
                # Agent first — it's an independent entity that does NOT
                # cascade-delete from conversation deletion (AFS § Cleanup).
                if agent_id:
                    try:
                        agent_api.delete_agent(agent_id)
                        logger.info("Deleted agent %s", agent_id)
                    except Exception as exc:
                        logger.warning("Cleanup failed for agent %s: %s", agent_id, exc)
                if conversation_id:
                    try:
                        conversation_api.delete_conversation(conversation_id)
                        logger.info("Deleted conversation %s", conversation_id)
                    except Exception as exc:
                        logger.warning(
                            "Cleanup failed for conversation %s: %s",
                            conversation_id, exc,
                        )
