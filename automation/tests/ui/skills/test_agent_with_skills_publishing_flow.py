"""Agent with Skills Publishing Flow — skills embedded in the published
snapshot, never listed independently, thought process shows invocation
(ELITEA-2600).

Creates 3 skills (each with ≥100-char instructions — AFS Test Data: the
AGENT-level publish AI-validation gate ALSO inspects each attached skill's
own instructions length, so seeding all three correctly up front avoids the
analyst's own discovery-by-failure round-trip), attaches all 3 to a fresh
agent, publishes the agent via the actions-menu wizard (reusing the SAME
``AgentDetailPage`` publish-wizard methods ELITEA-1892 added), confirms the
Publishing Terms disclosure text names the "Skills embedded, never
independently listed" guarantee, confirms the Skills Catalog does NOT list
any of the 3 skills independently after publish, opens the published agent
from the Agents Catalog, starts a chat, and explicitly ``~mentions`` two of
the attached skills in turn — verifying each invocation renders a
``chat-answer-tool-chip`` reading ``"Skill: {skill_name}"`` inside the
"Thought for N secs" accordion, and that the reply content reflects the
mentioned skill's own instructions (not just that a chip rendered).

New testid added this dispatch: ``agent-publish-terms-content``
(``PublishingTerms.jsx``, EliteaAI/EliteaUI@59155a8a on
``automation/testids``) — the Publish wizard's Preparation step had no
handle on the Publishing Terms disclosure text box before this case; see
``AgentDetailPage.publish_terms_content``'s docstring for the naming-
precedent rationale (the component is entityLabel-shared with the skill-
publish wizard, but its call site's sibling fields were already all
hardcoded ``agent-publish-*`` before this change).

Technique substitution vs the AFS's literal step 9 text (Phase 2 — same
observable, more reliable mechanism, not a scope change): the AFS's live
exploration used the Catalog search box + "No skills found" text. This
implementation instead reuses the SAME proven, already-merged idiom
ELITEA-2599 established for "skill absent from Catalog"
(``AgentHubPage.click_skills_tab()`` + ``get_skill_card_count_by_name() == 0``)
— ``AgentHubPage.search()`` is hard-wired to await the AGENTS-tab
``/public_applications/prompt_lib/`` response (confirmed via source: the
Skills tab's own search fires ``/public_skills/{mode}/`` instead), so reusing
it unmodified on the Skills tab would hang on the wrong network wait. Both
mechanisms prove the identical fact the case needs — "not independently
listed in the Skills Catalog" — the card-count check is simply the more
direct one already exercised by a merged sibling test.

Spec: test-specs/skills/l2_agent-with-skills-publishing-flow_ELITEA-2600.md
"""

import logging
import re
import uuid

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agent_hub_page import AgentHubPage
from pages.agents_list_page import AgentsListPage
from pages.chat_page import ChatPage
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.agents, pytest.mark.chat]

logger = logging.getLogger("elitea.tests.skills")

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
VALIDATE_TIMEOUT = 30_000  # publish_validate is AI-backed — variable latency
PUBLISH_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000

_SUFFIX = uuid.uuid4().hex[:6]

SKILL_1_NAME = f"format-uppercase-2600-{_SUFFIX}"
SKILL_1_INSTRUCTIONS = (
    "You are a text formatting skill. Whenever you are invoked, convert the "
    "entire user-provided text to UPPERCASE letters only, with no other "
    "changes, and return just the converted text with no explanation."
)

SKILL_2_NAME = f"word-counter-2600-{_SUFFIX}"
SKILL_2_INSTRUCTIONS = (
    "You are a word-counting skill. Whenever you are invoked, count the "
    "number of words in the user-provided text and respond with exactly "
    "one line in the format 'Word count: N', where N is the total number "
    "of words, and nothing else."
)

SKILL_3_NAME = f"summarizer-2600-{_SUFFIX}"
SKILL_3_INSTRUCTIONS = (
    "You are a summarization skill. Whenever you are invoked, read the "
    "user-provided text and produce a concise one- or two-sentence summary "
    "that captures its main point, omitting minor details."
)

AGENT_NAME = f"multi-skill-agent-2600-{_SUFFIX}"
AGENT_DESCRIPTION = "Disposable agent for ELITEA-2600's skills-publishing flow test"
AGENT_INSTRUCTIONS = (
    "You are a helpful assistant that can format and analyze text using "
    "your attached skills. When a user explicitly mentions a skill, apply "
    "that skill's own instructions to produce the response."
)
AGENT_TAG = "automation"

VERSION_NAME = f"v1-{_SUFFIX}"
CATEGORY_NAME = "Quality Assurance"
CATEGORY_SLUG = "quality-assurance"

PUBLISHING_TERMS_EXCLUSION_SNIPPET = (
    "attached Skills and sub-agents are not stripped"
)
PUBLISHING_TERMS_NEVER_LISTED_SNIPPET = (
    "Retained Skills are never listed as separate entries in the catalog"
)

WORD_COUNTER_PROMPT = "one two three four five six seven eight nine ten"
WORD_COUNTER_EXPECTED_REPLY = "Word count: 10"

UPPERCASE_PROMPT = "elitea test message"
UPPERCASE_EXPECTED_REPLY = "ELITEA TEST MESSAGE"


def _create_skill(page, name: str, instructions: str, description: str) -> int:
    """Create a skill via the UI and return its numeric ID."""
    list_page = SkillsListPage(page)
    list_page.navigate_to_create()

    form_page = SkillFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(name=name, instructions=instructions, description=description)
    form_page.wait_for_form_validation()
    assert form_page.is_save_enabled(), (
        f"Save should be enabled after filling all required fields for skill '{name}'"
    )
    form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

    detail_page = SkillDetailPage(page)
    detail_page.verify_on_detail_page()
    skill_id = int(detail_page.get_skill_id())
    logger.info("Created skill %r with id=%d", name, skill_id)
    return skill_id


class TestAgentWithSkillsPublishingFlow:
    """Agent with Skills Publishing Flow (ELITEA-2600, l2/p1)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-2600_agent-with-skills-publishing-flow.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_agent_with_skills_publishing_flow(self, page, agent_api, skill_api):
        """Skills attached to an agent are embedded in its published
        snapshot — never independently Catalog-listed — and remain
        individually invokable (explicit ``~mention``) with their own
        invocation visible in the published agent's thought process."""
        skill_1_id = None
        skill_2_id = None
        skill_3_id = None
        agent_id = None

        try:
            with allure.step("Step 1 — Create Skill 1 (format-uppercase, ≥100-char instructions)"):
                skill_1_id = _create_skill(
                    page, SKILL_1_NAME, SKILL_1_INSTRUCTIONS,
                    "Convert all text to UPPERCASE format",
                )

            with allure.step("Step 2 — Create Skill 2 (word-counter, ≥100-char instructions)"):
                skill_2_id = _create_skill(
                    page, SKILL_2_NAME, SKILL_2_INSTRUCTIONS,
                    "Count the words in the provided text and return the count",
                )
                assert skill_2_id != skill_1_id, "Skill 2 should have a distinct ID from Skill 1"

            with allure.step("Step 3 — Create Skill 3 (summarizer, ≥100-char instructions)"):
                skill_3_id = _create_skill(
                    page, SKILL_3_NAME, SKILL_3_INSTRUCTIONS,
                    "Provide a brief summary of the given text",
                )
                assert skill_3_id not in (skill_1_id, skill_2_id), (
                    "Skill 3 should have a distinct ID from Skills 1 and 2"
                )

            with allure.step(
                "Step 4 — Create an Agent, add a Tag, and attach all 3 skills to it"
            ):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_NAME,
                    description=AGENT_DESCRIPTION,
                    instructions=AGENT_INSTRUCTIONS,
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required agent fields"
                )
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = AgentDetailPage(page)
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                detail_page.verify_on_detail_page()
                agent_id = int(detail_page.get_agent_id())
                logger.info("Created agent %r with id=%d", AGENT_NAME, agent_id)

                # The Tags field (ApplicationEditForm.jsx's TagEditor) only
                # exists on the DETAIL/edit page, not the create form — same
                # precondition ELITEA-1878/1879's suite already established
                # (confirmed live this dispatch: `agent-tags-input` is absent
                # on /agents/create, 5s timeout waiting for visibility).
                detail_page.add_tag(AGENT_TAG)
                detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)

                for skill_name in (SKILL_1_NAME, SKILL_2_NAME, SKILL_3_NAME):
                    detail_page.attach_skill(skill_name, timeout=UI_ELEMENT_TIMEOUT)
                    assert detail_page.is_skill_attached(skill_name), (
                        f"Skill card for {skill_name!r} should render after attaching"
                    )
                assert "3/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should read '3/5 skills added.' once all 3 are attached"
                )

            with allure.step(
                'Step 5 — Open the agent\'s Publish wizard; verify it opens as a '
                "role=\"dialog\" and the Preparation step's Publishing Terms text "
                "confirms attached Skills are embedded, never independently listed"
            ):
                detail_page.open_publish_wizard(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.publish_version_name_input.is_visible(), (
                    "Publish wizard Preparation step should show a Version-name input"
                )

                terms_text = detail_page.publish_terms_content.text_content() or ""
                assert PUBLISHING_TERMS_EXCLUSION_SNIPPET in terms_text, (
                    "Publishing Terms disclosure should state that attached Skills "
                    f"are not stripped, got: {terms_text!r}"
                )
                assert PUBLISHING_TERMS_NEVER_LISTED_SNIPPET in terms_text, (
                    "Publishing Terms disclosure should state that retained Skills "
                    f"are never listed as separate catalog entries, got: {terms_text!r}"
                )

            with allure.step(
                "Step 6 — Fill Version name + Category, accept Publishing Terms, "
                'click "Continue"; verify the AI publish_validate gate passes '
                "(0 Critical issues) now that every attached skill independently "
                "clears the ≥100-char content gate"
            ):
                detail_page.fill_publish_preparation_step(
                    VERSION_NAME, CATEGORY_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                assert detail_page.is_publish_continue_enabled(), (
                    "Continue should become enabled once Name, Category, and the "
                    "agree-checkbox are all set"
                )

                validate_status = detail_page.click_publish_continue(timeout=VALIDATE_TIMEOUT)
                assert validate_status == 200, (
                    "publish_validate should return 200 (no Critical issues) — every "
                    "attached skill was seeded with ≥100-char instructions precisely "
                    f"to satisfy the AI content-quality gate, got status {validate_status}"
                )
                assert detail_page.publish_confirm_button.is_enabled(), (
                    "Validation step's Publish button should be enabled — "
                    "publish_validate reported no Critical issues"
                )

            with allure.step('Step 7 — Click "Publish"; verify it succeeds and the '
                              "new version becomes the selected one"):
                publish_status = detail_page.confirm_publish(timeout=PUBLISH_TIMEOUT)
                assert publish_status == 200, f"publish POST should return 200, got {publish_status}"

                detail_page.select_version_by_name(VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.get_version_selector_value() == VERSION_NAME, (
                    f"VERSION selector should show {VERSION_NAME!r} once explicitly selected"
                )

            with allure.step(
                "Step 8 — Navigate to the Agents Catalog, search for the agent's "
                "name; verify its card is present, grouped under the selected "
                "Category heading"
            ):
                catalog_page = AgentHubPage(page)
                catalog_page.navigate()
                catalog_page.search(AGENT_NAME, timeout=NAVIGATION_TIMEOUT)
                assert catalog_page.get_agent_card(AGENT_NAME).first.is_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                ), f"Published agent card for {AGENT_NAME!r} should be visible in the Catalog"
                assert catalog_page.is_category_section_visible(
                    CATEGORY_SLUG, timeout=UI_ELEMENT_TIMEOUT
                ), f"Catalog should show the {CATEGORY_NAME!r} category heading"

            with allure.step(
                "Step 9 — Switch to the Skills Catalog tab; verify none of the 3 "
                "attached skills are independently listed as Catalog entities "
                "(embedded in the agent snapshot instead)"
            ):
                # Fresh navigate (not a reuse of Step 8's searched catalog_page)
                # so the shared search-input's leftover AGENT_NAME query — which
                # would otherwise carry over across the tab switch and filter the
                # Skills tab's own results down to zero for the WRONG reason —
                # can't mask this assertion. Same fresh-navigate-then-click-tab
                # idiom already proven in the merged ELITEA-2599 sibling test.
                catalog_page.navigate()
                catalog_page.click_skills_tab(timeout=UI_ELEMENT_TIMEOUT)
                for skill_name in (SKILL_1_NAME, SKILL_2_NAME, SKILL_3_NAME):
                    assert catalog_page.get_skill_card_count_by_name(skill_name) == 0, (
                        f"Skill {skill_name!r} should NOT appear as an independent "
                        "Catalog entity — it should be embedded in the published "
                        "agent's snapshot only"
                    )

            with allure.step(
                'Step 10 — Open the published agent from the Agents Catalog and '
                'click "Start Chat"'
            ):
                catalog_page.navigate()
                catalog_page.search(AGENT_NAME, timeout=NAVIGATION_TIMEOUT)
                catalog_page.open_agent_by_name(AGENT_NAME, timeout=NAVIGATION_TIMEOUT)
                catalog_page.click_start_chat(timeout=UI_ELEMENT_TIMEOUT)

                page.wait_for_url(re.compile(r"/chat"), timeout=NAVIGATION_TIMEOUT)
                chat = ChatPage(page)
                chat.wait_for_page_load()

            with allure.step(
                'Step 11-12 — Mention Skill 2 (word-counter) via "~mention", send, '
                "and verify a chat-answer-tool-chip reading "
                "'Skill: word-counter-...' renders in the Thought accordion, with "
                "the reply reflecting the skill's own word-counting instructions"
            ):
                initial_count = chat.get_message_count()
                chat.send_message_with_skill_mention(
                    SKILL_2_NAME, WORD_COUNTER_PROMPT, timeout=UI_ELEMENT_TIMEOUT
                )
                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=NAVIGATION_TIMEOUT)

                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                assert chat.answer_thought_accordion.is_visible(), (
                    "Thought accordion should be visible after the skill-mention response"
                )
                assert chat.answer_tool_chip.count() >= 1, (
                    "Expected at least 1 skill/tool-call chip in the Thought accordion"
                )
                assert f"Skill: {SKILL_2_NAME}" in (chat.answer_tool_chip.first.text_content() or ""), (
                    f"Expected a tool chip reading 'Skill: {SKILL_2_NAME}'"
                )
                word_counter_reply = chat.get_last_message_text()
                assert WORD_COUNTER_EXPECTED_REPLY in word_counter_reply, (
                    f"Expected reply to contain {WORD_COUNTER_EXPECTED_REPLY!r}, "
                    f"got: {word_counter_reply!r}"
                )

            with allure.step(
                'Step 13 — Mention Skill 1 (format-uppercase) via "~mention" in the '
                "SAME conversation, send, and verify a SECOND chat-answer-tool-chip "
                "reading 'Skill: format-uppercase-...' renders, with the reply text "
                "fully upper-cased (proving the skill's own instructions were "
                "actually applied, not just that a chip rendered)"
            ):
                initial_count = chat.get_message_count()
                chat.send_message_with_skill_mention(
                    SKILL_1_NAME, UPPERCASE_PROMPT, timeout=UI_ELEMENT_TIMEOUT
                )
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

                assert chat.answer_tool_chip.count() >= 1, (
                    "Expected at least 1 skill/tool-call chip in the Thought accordion"
                )
                assert f"Skill: {SKILL_1_NAME}" in (chat.answer_tool_chip.last.text_content() or ""), (
                    f"Expected a tool chip reading 'Skill: {SKILL_1_NAME}'"
                )
                uppercase_reply = chat.get_last_message_text()
                assert UPPERCASE_EXPECTED_REPLY in uppercase_reply, (
                    f"Expected reply to contain {UPPERCASE_EXPECTED_REPLY!r} "
                    f"(the prompt {UPPERCASE_PROMPT!r} fully upper-cased), "
                    f"got: {uppercase_reply!r}"
                )
        finally:
            with allure.step("Cleanup — delete the agent and the 3 skills"):
                if agent_id is not None:
                    try:
                        agent_api.delete_agent(agent_id)
                        logger.info("Cleanup: deleted agent id=%d", agent_id)
                    except Exception as exc:
                        logger.warning("Cleanup: failed to delete agent id=%s: %s", agent_id, exc)
                for skill_id in (skill_1_id, skill_2_id, skill_3_id):
                    if skill_id is not None:
                        try:
                            skill_api.delete_skill(skill_id)
                            logger.info("Cleanup: deleted skill id=%d", skill_id)
                        except Exception as exc:
                            logger.warning("Cleanup: failed to delete skill id=%s: %s", skill_id, exc)
