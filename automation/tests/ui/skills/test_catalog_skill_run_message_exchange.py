"""UI Test for ELITEA-4633 — run a Catalog skill from the Skills tab and exchange a message.

AFS: test-specs/skills/l1_run-catalog-skill-from-catalog-and-message-exchange_ELITEA-4633.md

Case-text drift (live product is the contract): a skill-run chat shows NO greeting message
(thread is empty until the user sends); Run click persists a conversation named
"Run code-reviewer" immediately; hover shows only a "Run" tooltip.
"""

import logging
import re

import allure
import pytest
from api import ConversationAPI
from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage
from playwright.sync_api import Page, expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.skills,
    pytest.mark.chat,
    pytest.mark.p1,
    pytest.mark.regression,
]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 90_000
CATALOG_SKILL = "code-reviewer"
TEST_MESSAGE = "Review this code: function add(a, b) { return a + b; }"
RELEVANCE_KEYWORDS = ("add", "function", "validation", "type", "return")


@allure.epic("Skills")
@allure.feature("Catalog")
class TestCatalogSkillRunMessageExchange:
    """ELITEA-4633 — Catalog Skills tab -> Run -> chat with skill participant -> message exchange."""

    @pytest.mark.tms("ELITEA-4633")
    @allure.title("Catalog: run a skill from the Skills tab and verify the message exchange")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-4633_run-skill-from-catalog-skills-page.md",
        "onetest-ai Test Case link",
    )
    def test_run_catalog_skill_and_exchange_message(self, page: Page, _browser_cookies):
        hub = AgentHubPage(page)
        chat = ChatPage(page)
        conversation_api = ConversationAPI(browser_cookies=_browser_cookies)
        created_ids: set[int] = set()
        run_name = f"Run {CATALOG_SKILL}"
        try:
            with allure.step("Step 1 — Open the Catalog page"):
                hub.navigate()
                chat.dismiss_platform_banner_dialog()
                expect(hub.page_heading).to_contain_text("Welcome to ELITEA Catalog!", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 2 — Click the Skills tab"):
                hub.click_skills_tab()
                expect(hub.skills_tab).to_have_attribute("aria-selected", "true")

            with allure.step("Step 3 — Search the catalog skill; exactly one card with a Run button"):
                hub.search_skills(CATALOG_SKILL)
                expect(hub.skill_run_button).to_have_count(1, timeout=NAVIGATION_TIMEOUT)
                expect(hub.skill_run_button).to_be_visible()

            with allure.step("Step 4 — Hover the Run button: 'Run' tooltip"):
                hub.skill_run_button.hover()
                expect(hub.skill_run_tooltip).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 5 — Click Run: navigates to a new chat"):
                chat.dismiss_platform_banner_dialog()
                hub.skill_run_button.click()
                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=NAVIGATION_TIMEOUT)
                conv_id = int(re.search(r"/chat/(\d+)", page.url).group(1))
                created_ids.add(conv_id)

            with allure.step("Step 6 — New chat opens with an empty message thread"):
                # Sidebar presence is asserted in Step 11: on DEV the list item does not render
                # until the first message is exchanged (AFS observed it earlier; run-dependent).
                expect(chat.message_input).to_be_visible(timeout=NAVIGATION_TIMEOUT)
                expect(chat.messages_container).to_have_count(0)

            with allure.step("Step 7 — Participants panel: one skill row with Catalog tag and v1.0"):
                chat.expand_participants_panel_via_toggle()
                rows = page.locator(chat.PARTICIPANT_ROW_PREFIX)
                expect(rows).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                row = chat.get_participant_row_by_name(CATALOG_SKILL)
                expect(row).to_contain_text(CATALOG_SKILL)
                expect(row.locator(chat.PARTICIPANT_CATALOG_TAG)).to_have_text("Catalog")
                expect(row).to_contain_text("v1.0")

            with allure.step("Step 8 — Message input is ready with its placeholder"):
                expect(chat.message_input).to_have_attribute("placeholder", "Type your message...")

            with allure.step("Step 9 — Send the review message; it appears in the thread"):
                chat.dismiss_platform_banner_dialog()
                chat.send_message(TEST_MESSAGE)
                expect(chat.messages_container.filter(has_text=TEST_MESSAGE)).to_have_count(
                    1, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 10 — Skill responds with a relevant, non-error review"):
                # Skill replies render no Copy button, so wait_for_ai_response() never completes;
                # condition-wait on the reply item's relevant content instead.
                # Reply item picked by content (the "Thought for" footer only the skill reply renders), not position.
                reply = chat.messages_container.filter(has_text="Thought for")
                expect(reply).to_have_count(1, timeout=AI_RESPONSE_TIMEOUT)
                # Sender label on DEV reads "Elitea to Message" (AFS "Skill: code-r..." drifted) - not asserted.
                expect(reply).to_contain_text(re.compile(r"\b(add|function|validation|type|return)\b", re.I),
                                              timeout=AI_RESPONSE_TIMEOUT)
                expect(reply).to_contain_text("Thought for", timeout=AI_RESPONSE_TIMEOUT)  # generation finished
                text = reply.inner_text().lower()
                assert text.strip(), "Skill response must be non-empty"
                assert "something went wrong" not in text, (
                    f"Skill response looks like an error: {text[:200]!r}"
                )
                assert any(k in text for k in RELEVANCE_KEYWORDS), (
                    f"Skill response not relevant to the sent code: {text[:300]!r}"
                )

            with allure.step("Step 11 — Chat appears in the sidebar list as 'Run code-reviewer'"):
                # Matched by name, not URL id: sending can persist a second "Run code-reviewer" conversation
                # (AFS preconditions); cleanup below deletes every one by name.
                item = chat.get_conversation_item_rows().filter(has_text=run_name)
                expect(item.first).to_be_visible(timeout=NAVIGATION_TIMEOUT)
        finally:
            with allure.step("Cleanup — delete conversation(s) created by the run"):
                # Name sweep only when this run created a conversation; ids below the first one
                # created pre-date the run and are never touched.
                if created_ids:
                    try:
                        for row in conversation_api.list_conversations().get("rows", []):
                            if row.get("name") == run_name and row["id"] >= min(created_ids):
                                created_ids.add(row["id"])
                    except Exception as exc:
                        logger.warning("Conversation listing for cleanup failed: %s", exc)
                for cid in created_ids:
                    try:
                        conversation_api.delete_conversation(cid)
                    except Exception as exc:
                        logger.warning("Conversation %s cleanup failed: %s", cid, exc)
