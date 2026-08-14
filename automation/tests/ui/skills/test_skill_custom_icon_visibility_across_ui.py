"""Skill custom icon visibility across UI (ELITEA-2605).

Creates a dedicated, uniquely-named disposable skill with a distinctive
custom icon AND a dedicated disposable agent (icon visibility across
multiple surfaces needs an agent with the skill attached — per this
project's Hard Rule 10 test-data guidance, mutating a shared fixture
skill/agent risks polluting other tests' assertions), and confirms the
SAME uploaded-icon ``src`` renders correctly and identically across all
five UI locations the case names:

  1. Skills list card (``entity-card-icon-img``, ELITEA-2428 testid — page
     object plumbing added this case).
  2. Skill detail/edit page (``skill-form-icon-img``, pre-existing since
     ELITEA-2602/2604).
  3. SkillMenu attach-dropdown (``skill-menu-item-icon-img`` — NEW testid,
     EliteaAI/EliteaUI@ccc8c001).
  4. Agent SKILLS-section SkillCard (``skill-card-icon-img`` — NEW testid,
     same commit).
  5. Chat ``~mention`` autocomplete (``skill-mention-item-icon-img`` — NEW
     testid, same commit).

No product/visual defect — the icon is byte-identical and correctly
displayed everywhere (asserted via ``src`` equality, a stronger check than
the case's own "is displayed" wording — catches a future regression where
one surface silently falls back to a stale/default/wrong icon URL while
the others stay correct).

Case-text CLARIFICATION (reverse-masking guard, not a defect — see AFS
Coverage Map): step 14 ("Save the agent") needs no separate Save click —
skill attachment is an immediate auto-save (step 12's PATCH already
persisted it server-side); the agent-level Save button stays disabled.
Automation asserts the attachment survives a full agent reload instead.

Three new testids added for this case (none existed before, all on the
SAME ``EliteAImage``/``SkillIcon`` conditional-pair shape, custom-icon
branch only — the default ``SkillIcon`` glyph branch stays untagged, per
``.agents/testing.md`` § Locator policy "only the used branch is named"):
``skill-menu-item-icon-img`` (``SkillMenu.jsx``), ``skill-card-icon-img``
(``features/skill/ui/SkillCard.jsx``), ``skill-mention-item-icon-img``
(``MentionSkillList.jsx``). All three land in EliteaAI/EliteaUI@ccc8c001.

Spec: test-specs/skills/l2_skill-custom-icon-visibility-across-ui_ELITEA-2605.md
"""

import logging
import time
from pathlib import Path

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.skills")

# Reuses the existing repo test-icon asset (already added for ELITEA-2602/2604) —
# distinctive, well under the 500KB limit. No new test data file needed.
ICON_FILE = str(
    Path(__file__).resolve().parents[4] / "test-data" / "images" / "skill-fork-test-icon.png"
)


class TestSkillCustomIconVisibilityAcrossUI:
    """Skill custom icon visibility across UI (ELITEA-2605, l2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2605_skill-custom-icon-visibility-across-ui.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_skill_custom_icon_visible_across_ui(self, page, skill_api, agent_api):
        """Create a Skill with a custom icon + an Agent, attach the skill, and
        verify the SAME uploaded-icon src renders in all 5 named locations.

        Steps (AFS
        test-specs/skills/l2_skill-custom-icon-visibility-across-ui_ELITEA-2605.md):
        1. Create a skill with a distinctive custom icon and save it.
        2. Navigate to the Skills list page (CardList view).
        3. Locate the skill in the list.
        4. Verify the custom icon on the skill card (src match).
        5. Click the skill to open the detail/edit page.
        6. Verify the custom icon on the detail page (src match).
        7. Navigate to Agents section and create an agent.
        8. Go to the SKILLS section of the agent.
        9-11. Open the "+ Skill" dropdown, locate the skill, verify its
           custom icon in the SkillMenu (src match) — WITHOUT selecting it.
        12. Attach the skill to the agent.
        13. Verify the custom icon on the attached-skill SkillCard (src match).
        14. "Save" the agent — CLARIFICATION: auto-saved at attach time;
            verify persistence across a full reload instead.
        15. Open a chat conversation with the agent (embedded chat composer).
        16. Type "~" to trigger skill autocomplete.
        17. Verify the custom icon in the ~mention autocomplete (src match).
        """
        unique_suffix = int(time.time())
        skill_name = f"el-2605-icon-visibility-{unique_suffix}"[:32]
        agent_name = f"el-2605-icon-agent-{unique_suffix}"[:32]

        skill_id = None
        agent_id = None
        console_errors = None  # CapturedConsoleMessages, needs stop() in finally

        try:
            with allure.step(
                "Step 1 — Create a skill with a distinctive custom icon and save it"
            ):
                list_page = SkillsListPage(page)
                list_page.navigate_to_create()

                form_page = SkillFormPage(page)
                form_page.wait_for_form_load()
                console_errors = form_page.capture_console_errors()

                form_page.upload_skill_icon(ICON_FILE, timeout=UI_ELEMENT_TIMEOUT)
                uploaded_icon_src = form_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT)
                assert uploaded_icon_src, (
                    "Skill form icon avatar should show the uploaded image "
                    "(non-empty img src) after upload"
                )

                form_page.fill_form(
                    name=skill_name,
                    instructions=(
                        "You are a helper skill created for ELITEA-2605 icon "
                        "visibility verification. Respond with ICONSKILL."
                    ),
                    description="ELITEA-2605 icon visibility verification skill.",
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required fields"
                )
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = SkillDetailPage(page)
                detail_page.verify_on_detail_page()
                skill_id = int(detail_page.get_skill_id())
                logger.info("Created skill %r id=%d", skill_name, skill_id)

            with allure.step("Step 2 — Navigate to the Skills list page (CardList view)"):
                list_page.navigate()
                assert list_page.is_card_view_active(), (
                    "Skills list should default to Card view"
                )

            with allure.step("Step 3 — Locate the skill in the list"):
                assert list_page.skill_exists_in_list(skill_name), (
                    f"Skill {skill_name!r} should be visible in the Skills list"
                )

            with allure.step(
                "Step 4 — Verify the custom icon is displayed on the skill card"
            ):
                card_icon_img = list_page.card_icon_img_locator(skill_name)
                expect(card_icon_img).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                card_icon_src = card_icon_img.get_attribute("src")
                assert card_icon_src == uploaded_icon_src, (
                    "Skills list card icon src should match the uploaded "
                    f"icon's src; expected {uploaded_icon_src!r}, got {card_icon_src!r}"
                )

            with allure.step("Step 5 — Click on the skill to open the detail/edit page"):
                list_page.click_skill_card(skill_name, timeout=UI_ELEMENT_TIMEOUT)
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                detail_page.verify_on_detail_page()

            with allure.step(
                "Step 6 — Verify the custom icon is displayed on the detail page"
            ):
                detail_icon_src = detail_page.get_form_icon_src(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_icon_src == uploaded_icon_src, (
                    "Skill detail page icon src should match the uploaded "
                    f"icon's src; expected {uploaded_icon_src!r}, got {detail_icon_src!r}"
                )

            with allure.step("Step 7 — Navigate to Agents section and create an agent"):
                agents_list_page = AgentsListPage(page)
                agents_list_page.navigate_to_create()

                agent_form_page = AgentFormPage(page)
                agent_form_page.wait_for_form_load()
                agent_form_page.fill_form(
                    name=agent_name,
                    description="Agent for ELITEA-2605 icon visibility verification.",
                    instructions="You are a helpful assistant.",
                )
                agent_form_page.wait_for_form_validation()
                assert agent_form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required agent fields"
                )
                agent_form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                agent_detail_page = AgentDetailPage(page)
                # Root-cause fix (ELITEA-2605 flakiness): verify_on_detail_page()
                # reads page.url synchronously with no wait of its own, racing the
                # SPA's client-side route push after save. The working sibling
                # test_create_agent_via_ui (test_agent_management.py) always calls
                # wait_for_page_load() first, which waits for the INFORMATION
                # section + populated Name field — by which point the URL has
                # settled too. This test skipped that call; add it to match.
                agent_detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                agent_detail_page.verify_on_detail_page()
                agent_id = int(agent_detail_page.get_agent_id())
                logger.info("Created agent %r id=%d", agent_name, agent_id)

            with allure.step("Step 8 — Go to the SKILLS section of the agent"):
                agent_detail_page.ensure_skills_section_visible(timeout=UI_ELEMENT_TIMEOUT)
                counter_before = agent_detail_page.get_skills_counter_text(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert counter_before.startswith("0/5"), (
                    f"Expected '0/5 skills added.' on a fresh agent, got {counter_before!r}"
                )

            with allure.step(
                "Steps 9-11 — Open the '+ Skill' dropdown, locate the skill in "
                "the SkillMenu, and verify its custom icon (read-only — not "
                "yet selected)"
            ):
                popper = agent_detail_page.open_skill_menu(timeout=UI_ELEMENT_TIMEOUT)
                menu_row = agent_detail_page.get_skill_menu_item(
                    popper, skill_name, timeout=UI_ELEMENT_TIMEOUT
                )
                menu_icon_img = menu_row.locator(
                    AgentDetailPage.SKILL_MENU_ITEM_ICON_IMG_SELECTOR
                )
                expect(menu_icon_img).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                menu_icon_src = menu_icon_img.get_attribute("src")
                assert menu_icon_src == uploaded_icon_src, (
                    "SkillMenu dropdown row icon src should match the "
                    f"uploaded icon's src; expected {uploaded_icon_src!r}, got {menu_icon_src!r}"
                )
                # Close the popper without selecting — attachment happens
                # explicitly in step 12 via attach_skill() (fresh re-open).
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)

            with allure.step("Step 12 — Attach the skill to the agent"):
                agent_detail_page.attach_skill(skill_name, timeout=UI_ELEMENT_TIMEOUT)
                assert agent_detail_page.is_skill_attached(
                    skill_name, timeout=UI_ELEMENT_TIMEOUT
                ), f"Skill {skill_name!r} should be attached to the agent"
                counter_after = agent_detail_page.get_skills_counter_text(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert counter_after.startswith("1/5"), (
                    f"Expected '1/5 skills added.' after attaching, got {counter_after!r}"
                )

            with allure.step(
                "Step 13 — Verify the custom icon is displayed on the attached "
                "skill's SkillCard in the Agent's SKILLS section"
            ):
                skill_card_icon_src = agent_detail_page.get_skill_card_icon_src(
                    skill_name, timeout=UI_ELEMENT_TIMEOUT
                )
                assert skill_card_icon_src == uploaded_icon_src, (
                    "Agent SKILLS-section SkillCard icon src should match the "
                    f"uploaded icon's src; expected {uploaded_icon_src!r}, got {skill_card_icon_src!r}"
                )

            with allure.step(
                "Step 14 — 'Save' the agent — CLARIFICATION: the attach "
                "already auto-saved server-side (Save stays disabled); verify "
                "persistence across a full page reload instead"
            ):
                assert not agent_detail_page.is_save_enabled(), (
                    "Save should remain disabled — the attach already "
                    "persisted server-side, nothing new to save"
                )
                page.reload()
                agent_detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                assert agent_detail_page.is_skill_attached(
                    skill_name, timeout=UI_ELEMENT_TIMEOUT
                ), "Skill attachment should persist across a full page reload"

            with allure.step(
                "Step 15 — Open a chat conversation with the agent (embedded "
                "chat composer, active by default on the agent detail page)"
            ):
                agent_detail_page.chat_message_input.wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 16 — Type ~ to trigger skill autocomplete"):
                agent_detail_page.type_tilde_in_chat(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 17 — Verify the custom icon is displayed in the "
                "~mention autocomplete"
            ):
                mention_row = agent_detail_page.get_chat_mention_item(
                    skill_name, timeout=UI_ELEMENT_TIMEOUT
                )
                mention_icon_img = mention_row.locator(
                    AgentDetailPage.SKILL_MENTION_ITEM_ICON_IMG_SELECTOR
                )
                expect(mention_icon_img).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                mention_icon_src = mention_icon_img.get_attribute("src")
                assert mention_icon_src == uploaded_icon_src, (
                    "~mention autocomplete row icon src should match the "
                    f"uploaded icon's src; expected {uploaded_icon_src!r}, got {mention_icon_src!r}"
                )

            with allure.step(
                "Verify zero console errors across the full 17-step flow"
            ):
                assert not console_errors, (
                    f"Unexpected console errors during the flow: "
                    f"{[m.text for m in console_errors]}"
                )

        finally:
            if console_errors is not None:
                console_errors.stop()
            if agent_id is not None:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleanup: deleted agent id=%d", agent_id)
                except Exception as exc:
                    logger.warning("Cleanup: failed to delete agent id=%s: %s", agent_id, exc)
            if skill_id is not None:
                try:
                    skill_api.delete_skill(skill_id)
                    logger.info("Cleanup: deleted skill id=%d", skill_id)
                except Exception as exc:
                    logger.warning("Cleanup: failed to delete skill id=%s: %s", skill_id, exc)
