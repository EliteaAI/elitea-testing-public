"""UI Test for ELITEA-4629 — Chat: "~" mention of a skill participant in a chat with no agent.

AFS: test-specs/chat-interface/l1_tilde-mention-skill-in-chat-without-agent_ELITEA-4629.md

Case-text drift (live product is the contract): the "~" list in a chat WITHOUT an agent lists only
the conversation's skill participants and excludes the active one, so two skills are added
(mention target first, helper second). "animal-joke" does not exist on DEV: fixture skills are used
and the response is tied to the mentioned skill through a deterministic marker token.
"""

import logging
import time

import allure
import pytest
from playwright.sync_api import expect

from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.chat,
    pytest.mark.skills,
    pytest.mark.p0,
    pytest.mark.regression,
]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
RESPONSE_TIMEOUT = 90_000
MARKER = "ANIMALJOKE:"


@allure.epic("Chat")
@allure.feature("Skill mention")
class TestChatTildeMentionSkillWithoutAgent:
    """ELITEA-4629 — "~skill" autocomplete and invocation in a chat with no agent participant."""

    @pytest.mark.tms("ELITEA-4629")
    @allure.title("Chat: ~ mention of a skill participant works without an agent participant")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-4629_tilde-mention-skill-in-chat-without-agent.md",
        "onetest-ai Test Case link",
    )
    def test_tilde_mention_skill_without_agent(self, page, skill_api, conversation_api):
        chat = ChatPage(page)
        ts = int(time.time())
        name_a = f"animal-joke-{ts}"[:32]
        name_b = f"zebra-fact-{ts}"[:32]
        skill_ids = []
        conv_id = None
        try:
            with allure.step("Setup — create mention-target skill A and helper skill B via API"):
                skill_a = skill_api.create_skill(
                    name=name_a,
                    description="Autotest animal joke skill for ELITEA-4629.",
                    instructions=f"Reply with a one-line animal joke. Begin the reply with the exact token {MARKER}",
                )
                skill_ids.append(skill_a["id"])
                skill_b = skill_api.create_skill(
                    name=name_b,
                    description="Autotest helper skill for ELITEA-4629.",
                    instructions="Begin the reply with the exact token ZEBRAFACT:",
                )
                skill_ids.append(skill_b["id"])

            with allure.step("Step 1 — Open a blank chat; participants panel has no agent and no skills"):
                chat.navigate_to_chat()
                chat.dismiss_platform_banner_dialog()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                chat.dismiss_platform_banner_dialog()
                expect(chat.new_conversation_greeting).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                chat.expand_participants_panel_via_toggle()
                expect(page.locator(chat.PARTICIPANT_ROW_PREFIX)).to_have_count(0)
                expect(chat.switch_participant_button).to_have_count(0)

            with allure.step("Step 2 — Negative control: '~' with no skill participants shows the empty state"):
                popper = chat.open_mention_skill_popper()
                expect(popper).to_be_visible()
                expect(popper.locator(chat.MENTION_LIST_EMPTY)).to_contain_text("No skills in this chat")
                expect(popper.locator(chat.MENTION_SKILL_ITEM_PREFIX)).to_have_count(0)
                chat.message_input.press("Control+a")
                chat.message_input.press("Backspace")
                chat.message_input.press("Escape")

            with allure.step("Step 3 — Add skill A then skill B as participants (no agent)"):
                chat.add_skill_participant(name_a)
                chat.add_skill_participant(name_b)
                for sid in skill_ids:
                    expect(page.locator(chat.PARTICIPANT_ROW.format(sid))).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(page.locator(chat.PARTICIPANT_ROW_PREFIX)).to_have_count(2)
                expect(chat.switch_participant_button).to_have_attribute("aria-label", "Switch Skill")

            with allure.step("Step 4 — '~' lists skill A only (active participant B is excluded)"):
                popper = chat.open_mention_skill_popper()
                expect(popper.locator(chat.MENTION_SKILL_ITEM_PREFIX)).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(popper.locator(chat.MENTION_SKILL_ITEM.format(name_a))).to_be_visible()
                expect(popper.locator(chat.MENTION_SKILL_ITEM.format(name_b))).to_have_count(0)

            with allure.step("Step 5 — Typing 'animal' keeps skill A as the single match"):
                chat.message_input.press_sequentially("animal", delay=60)
                expect(popper.locator(chat.MENTION_SKILL_ITEM_PREFIX)).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(popper.locator(chat.MENTION_SKILL_ITEM.format(name_a))).to_be_visible()

            with allure.step("Step 6 — Select skill A: popper closes, composer holds '~<A> '"):
                popper.locator(chat.MENTION_SKILL_ITEM.format(name_a)).click()
                expect(chat.mention_skill_list).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_have_value(f"~{name_a} ")

            with allure.step("Step 7 — Complete the message with instructions"):
                chat.message_input.press_sequentially("tell me a joke", delay=40)
                expect(chat.message_input).to_have_value(f"~{name_a} tell me a joke")

            with allure.step("Step 8 — Send; the user message shows the full text"):
                initial_count = chat.get_message_count()
                chat.send_button.click()
                chat.wait_for_input_ready()
                conv_id = chat.get_current_conversation_id()
                expect(chat.messages_container.filter(has_text=f"~{name_a} tell me a joke")).to_have_count(
                    1, timeout=UI_ELEMENT_TIMEOUT
                )
                chat.wait_for_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 9 — The mentioned skill is present in the thinking steps (at least once)"):
                # The reply may involve other skills/tools too, so assert only that the mentioned skill's
                # name shows up in the thinking (tool-call) chips of the AI reply — not an exact reply.
                chat.wait_for_generation_complete(timeout=RESPONSE_TIMEOUT)
                ai_reply = chat.messages_container.filter(has=chat.answer_thought_accordion).last
                expect(ai_reply).to_be_visible(timeout=RESPONSE_TIMEOUT)
                expect(ChatPage.answer_tool_chip.resolve(ai_reply).filter(has_text=name_a).first).to_be_visible(
                    timeout=RESPONSE_TIMEOUT
                )
        finally:
            with allure.step("Cleanup — delete conversation and skills"):
                if conv_id:
                    try:
                        conversation_api.delete_conversation(conv_id)
                    except Exception as exc:
                        logger.warning("Conversation cleanup failed: %s", exc)
                for sid in skill_ids:
                    try:
                        skill_api.delete_skill(sid)
                    except Exception as exc:
                        logger.warning("Skill cleanup failed: %s", exc)
