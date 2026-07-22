"""UI Test for ELITEA-2166 — Chat: Private Project – Create New Conversation
and Add Agent via Create New Agent Canvas.

Verifies the full "+ Create New Agent" in-chat canvas flow on a fresh,
Private-project conversation: no "Invite Users" item in the composer's +
menu (Private-project guard), the canvas panel's 5 accordion sections, the
Save button's disabled/enabled gating, the underlying agent-creation POST,
the canvas's post-save title/subtitle transition, the PARTICIPANTS panel
listing, the composer's post-close participant/version display, and
sending the first message to the freshly-created agent.

Spec: test-specs/chat-interface/l2_create-agent-via-chat-canvas_ELITEA-2166.md

New page-object surface (AFS § Automation Hints): no existing ``ChatPage``
method drove the in-chat "+ Create New Agent" canvas before this case.
``ChatPage`` gained the entry-point locators/method
(``open_create_new_agent_canvas()``); ``AgentCanvasPage`` (new) owns the
canvas-specific chrome (close button, title/subtitle, accordion section
headers). The Name/Description/Instructions fields and the Save button are
NOT redeclared here — the canvas renders the exact same ``CreateAgentForm``
component as the standalone ``/agents/create`` page, so ``AgentFormPage`` is
reused directly on the same ``page`` (same composition pattern already used
by ``test_agent_with_toolkit_chat.py``, which combines ``AgentPage`` +
``ChatPage``).

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``):
- ``agents-create-new-button`` — the "+ Create New Agent" item in the
  Agents submenu (``PlusChatSubmenu.jsx``'s ``showCreateNew`` item,
  templated ``${sectionKey}-create-new-button``).
- ``agent-canvas-section-{general,instructions,welcome-message,
  chat-starters,advanced}`` — the 5 accordion section headers
  (``BasicAccordion.jsx``'s existing per-item ``testId`` prop, wired at each
  of the 5 call sites).
- ``agent-save-button`` on ``CreateApplicationSaveButton.jsx`` — added ONLY
  at the ``AgentEditor.jsx`` call site (component-sharing guard:
  ``CreateApplicationSaveButton.jsx`` is also used by ``PipelineEditor.jsx``,
  which must not get this agent-specific testid).
- ``agent-canvas-close-button`` / ``agent-canvas-title`` /
  ``agent-canvas-subtitle`` — threaded as optional
  ``closeButtonTestId``/``titleTestId``/``subtitleTestId`` props through
  ``BaseEditor.jsx`` -> ``EditorHeader.jsx`` (both shared across Agent/
  Pipeline/Toolkit editors); only ``AgentEditor.jsx``'s call site supplies
  values.

Declared improvisations (canon gaps found during Phase 2 exploration, not
in the lead's original testid list — `.agents/role-overrides.md` §
Declared-improvisation protocol):
- ``invite-users-menuitem`` — the AFS's step-1 assertion ("no 'Invite
  Users' item for a Private project") needs a testid-only way to prove
  ABSENCE, but the item carried no testid at all (unlike its
  ``*-menuitem`` siblings in ``EXPANDABLE_ITEMS``). Added directly to
  ``PlusChatButton.jsx``'s conditional ``MenuItem`` (the whole element is
  conditionally rendered, not a state-conditional testid VALUE, so this is
  compliant with the testid=identity/state=data-* ruling). Verified live:
  a Private project renders exactly 5 ``*-menuitem`` elements page-wide
  and zero ``invite-users-menuitem``.
- ``chat-version-selector-trigger`` — the AFS named
  ``agent-version-selector-trigger`` for "the composer's version-selector
  button", but that testid actually belongs to a DIFFERENT component
  (``ApplicationVersionSelect.jsx``, rendered on the agent detail page's
  own tab bar — confirmed via ``grep`` that it has zero importers outside
  that surface). The composer's actual version button is rendered by
  ``VersionSelector.jsx`` (``chat/ui/chat-input``, used ONLY by the
  composer's ``AgentEditorPanel.jsx`` — not a shared component), which
  carried no testid at all. Added ``chat-version-selector-trigger``
  there instead of reusing the wrong name.

Known defect handling (step 10, issue #708): the FIRST message sent to a
freshly-created in-chat agent can get no response (reply row created, body
stays empty indefinitely — confirmed intermittent: reproduced 0/2 times
during this implementation's own manual Phase-2 verification runs, but
already CONFIRMED and filed during analyst Phase 0/3 execution). Automated
via the pytest-native ``soft_failures``/``pytest.fail()`` idiom (mirrors
``test_agent_publish_unpublish_version.py``'s #611/#614 handling) rather
than ``expect.soft()`` directly, since the observable
(``wait_for_message_content_stable()`` raising ``TimeoutError``) isn't a
bare Locator/Page/APIResponse assertion. The user-message-appears and
no-new-console-errors-on-send assertions stay HARD.
"""

import logging
import re

import allure
import pytest
from playwright.sync_api import expect

from config import settings
from pages.agent_canvas_page import AgentCanvasPage
from pages.agent_form_page import AgentFormPage
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.agents, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds, except AI_RESPONSE_TIMEOUT which is also
# passed in ms to wait_for_message_content_stable)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000

AGENT_NAME = "echo"
AGENT_DESCRIPTION = "test agent"
AGENT_INSTRUCTIONS = "echo every user input"
TEST_MESSAGE = "hi"

# Live-verified for a Private project's plus menu (AFS step 1): exactly 5
# top-level items, all carrying a "*-menuitem" testid, none of them
# "Invite Users" (PlusChatButton.jsx's !isPrivateProject guard hides that
# item entirely for Private projects).
EXPECTED_PLUS_MENU_ITEM_COUNT = 5


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_conversation_deletion_flow.py`` /
    ``test_open_conversation_today_section.py`` — an unrelated
    toolkit/secrets panel probe that fires on every page load in this
    local environment, not caused by this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestCreateAgentViaChatCanvas:
    """ELITEA-2166: Chat – Create New Conversation and Add Agent via Create New Agent Canvas (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2166_chat-private-project-create-new-conversation-and-add-agent-via-create-new-agent-canvas.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_create_new_conversation_and_add_agent_via_canvas(
        self, page, conversation_api, agent_api,
    ):
        """Create a new conversation in the Private project, create a new
        agent via the in-chat canvas, verify the canvas/composer/
        participants surfaces, then send the agent its first message.

        Steps (AFS
        test-specs/chat-interface/l2_create-agent-via-chat-canvas_ELITEA-2166.md):
        1. Switch to Private project; click + Chat. Verify a blank
           conversation opens with zero history, and the + menu has no
           "Invite Users" item.
        2. + menu -> Agents -> + Create New Agent. Verify the canvas opens
           with heading "Create New Agent".
        3. Verify all 5 accordion sections are visible.
        4. Verify Save is disabled pre-fill.
        5. Fill Name/Description/Instructions.
        6. Verify Save becomes enabled.
        7. Click Save; verify the creation POST resolves 201; canvas
           transitions to the saved-agent view (title=agent name,
           subtitle="base").
        8. Verify the PARTICIPANTS panel's AGENTS section lists the new
           agent (composer text NOT asserted here — see CLARIFICATION #709
           in the module/AFS notes).
        9. Close the canvas; verify the composer now shows the agent name
           and version.
        10. Send "hi"; verify it appears and no NEW console errors on the
            send action itself; soft-assert the reply stabilizes to
            non-empty content within 30s (Known defect: #708).
        """
        chat = ChatPage(page)
        agent_canvas = AgentCanvasPage(page)
        agent_form = AgentFormPage(page)

        agent_id = None
        conversation_id = None
        soft_failures: list[str] = []

        # Registered before Setup so console errors from every step are
        # captured (side-channel discipline). The pre-existing secrets 403
        # noise is filtered so it can't mask a genuinely new error.
        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step("Setup — navigate to chat and switch to the Private project"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(str(settings.elitea_project_id), timeout=NAVIGATION_TIMEOUT)

            with allure.step(
                "Step 1 — Click + Chat; verify a new blank conversation "
                "opens (zero message history) and the composer's + menu "
                "has NO 'Invite Users' item for this Private project"
            ):
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_message_count() == 0, (
                    "A freshly-opened conversation should start with zero messages"
                )

                chat.plus_menu_button.click()
                expect(chat.agents_menuitem).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                item_count = chat.get_open_plus_menu_item_count()
                assert item_count == EXPECTED_PLUS_MENU_ITEM_COUNT, (
                    f"Expected exactly {EXPECTED_PLUS_MENU_ITEM_COUNT} plus-menu "
                    f"items for a Private project, found {item_count}"
                )
                assert chat.invite_users_menuitem.count() == 0, (
                    "'Invite Users' should be entirely absent for a Private "
                    "project (PlusChatButton.jsx's !isPrivateProject guard), "
                    f"found {chat.invite_users_menuitem.count()}"
                )
                # Close the menu by toggling it again (its Popper has no
                # Escape-key handling — confirmed live; ClickAwayListener
                # only reacts to clicks outside it) — required before Step
                # 2 re-opens it via the same button.
                chat.plus_menu_button.click()

            with allure.step(
                "Step 2 — + menu -> Agents -> + Create New Agent; verify "
                "the canvas panel opens with heading 'Create New Agent'"
            ):
                chat.open_create_new_agent_canvas(timeout=NAVIGATION_TIMEOUT)
                agent_canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
                expect(agent_canvas.title).to_have_text(
                    "Create New Agent", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 3 — Verify all 5 accordion sections are visible: "
                "General, Instructions, Welcome message, Chat starters, Advanced"
            ):
                for key in agent_canvas.SECTION_KEYS:
                    expect(agent_canvas.get_section_header(key)).to_be_visible(
                        timeout=UI_ELEMENT_TIMEOUT
                    )

            with allure.step(
                "Step 4 — Verify the Save button is disabled while Name/"
                "Description are empty"
            ):
                assert not agent_form.is_save_enabled(), (
                    "Save should be disabled before any mandatory field is filled"
                )

            with allure.step(
                f"Step 5 — Fill Name={AGENT_NAME!r}, "
                f"Description={AGENT_DESCRIPTION!r}, "
                f"Instructions={AGENT_INSTRUCTIONS!r}"
            ):
                agent_form.fill_form(
                    name=AGENT_NAME,
                    description=AGENT_DESCRIPTION,
                    instructions=AGENT_INSTRUCTIONS,
                )
                assert agent_form.get_name() == AGENT_NAME
                assert agent_form.get_description() == AGENT_DESCRIPTION
                assert agent_form.get_instructions() == AGENT_INSTRUCTIONS

            with allure.step("Step 6 — Verify the Save button becomes enabled"):
                assert agent_form.is_save_enabled(), (
                    "Save should be enabled once Name and Description are filled"
                )

            with allure.step(
                "Step 7 — Click Save; verify the creation POST resolves "
                "201; the canvas transitions to the saved-agent view "
                "(heading = agent name, subtitle = 'base')"
            ):
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

                expect(agent_canvas.title).to_have_text(
                    AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(agent_canvas.subtitle).to_have_text(
                    "base", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 8 — Open the PARTICIPANTS panel; verify the AGENTS "
                "section lists the new agent. The composer's own text is "
                "NOT asserted here — while this agent's own canvas is "
                "still open it correctly shows an 'Editing…' status label "
                "instead of the agent name (CLARIFICATION #709 — the "
                "case's literal step 8 wording implies the composer shows "
                "'echo | base' at this point; live, that only renders "
                "after Step 9 closes the canvas)"
            ):
                popper = chat.open_participants_popover(
                    timeout=UI_ELEMENT_TIMEOUT, section="agents"
                )
                expect(popper).to_contain_text(AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 9 — Click the canvas's X (close) button (this click "
                "also dismisses the still-open participants popper via its "
                "ClickAwayListener); verify the canvas is gone and the "
                "composer now shows the agent name and 'base' version"
            ):
                agent_canvas.close(timeout=UI_ELEMENT_TIMEOUT)
                expect(agent_canvas.title).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.switch_participant_button).to_contain_text(
                    AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.chat_version_selector_trigger).to_have_text(
                    "base", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 10 — Send 'hi'; verify the user message appears and "
                "no NEW console errors on the send action itself (HARD); "
                "soft-assert the agent's reply stabilizes to non-empty "
                "content within 30s — Known defect: #708 (first message "
                "to a freshly-created agent can get no response; the "
                "Socket.IO 502/503/CORS noise that appears WHILE waiting "
                "for the (currently broken) reply is part of the known-"
                "defect signature, not a separate assertion target — not "
                "checked against the pre-send baseline below)"
            ):
                baseline_error_count = len(console_messages)
                initial_count = chat.get_message_count()
                chat.send_message(TEST_MESSAGE)

                expect(chat.messages_container.nth(initial_count)).to_contain_text(
                    TEST_MESSAGE, timeout=UI_ELEMENT_TIMEOUT
                )

                # Capture the conversation id (assigned server-side only
                # once this first message is sent — AFS § Test Data) for
                # cleanup. Best-effort: a missed capture means cleanup
                # can't delete the conversation, not a test failure.
                try:
                    page.wait_for_url(re.compile(r"/chat/\d+"), timeout=UI_ELEMENT_TIMEOUT)
                except Exception:
                    logger.warning(
                        "Conversation URL never resolved to /chat/{id} — "
                        "cleanup may not find it: %s", page.url,
                    )
                match = re.search(r"/chat/(\d+)", page.url)
                if match:
                    conversation_id = int(match.group(1))

                send_time_new_errors = [
                    m.text for m in console_messages[baseline_error_count:]
                ]
                assert not send_time_new_errors, (
                    "Unexpected console errors on the send action itself: "
                    f"{send_time_new_errors!r}"
                )

                try:
                    chat.wait_for_message_content_stable(
                        stable_duration_ms=2000, timeout=AI_RESPONSE_TIMEOUT
                    )
                except TimeoutError as exc:
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/708: "
                        "agent reply never stabilized to non-empty content "
                        f"within {AI_RESPONSE_TIMEOUT / 1000:.0f}s: {exc}"
                    )

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed (known isolated product "
                    "defect, not test/infrastructure — the create-agent-"
                    "via-canvas flow above passed cleanly):\n"
                    + "\n".join(soft_failures)
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
