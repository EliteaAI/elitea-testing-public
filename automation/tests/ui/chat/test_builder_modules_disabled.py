"""UI Test for ELITEA-3370 — Skills Builder and Project Context Builder
disabled prevents entity creation.

Verifies that while the ``skill_builder`` and ``project_context_builder``
Modules-panel toggles are OFF, the AI does not create the corresponding
entity no matter how explicit the chat request is — the toggle is a
server-enforced gate (the predict backend reads
``conversation.meta.internal_tools`` to decide which tools the AI may
invoke), not merely a client-side-only control. Enabling a module
mid-conversation only affects NEW requests; it never retroactively
modifies an earlier message/response pair sent while the module was off.

AFS: test-specs/chat-interface/
    l1_skills-and-project-context-builder-disabled-prevents-entity-creation_ELITEA-3370.md

No product defects found — all 9 case steps executed live end-to-end
against the real (unmocked) DEV backend and matched the case's Pass
criteria exactly, for both modules, in both the disabled and enabled
states.

Markers:
    - ui: requires browser
    - chat: chat-related test
    - p0: critical priority (AFS Priority l1 == TMS `priority: critical`)

Usage:
    cd automation
    pytest tests/ui/chat/test_builder_modules_disabled.py -v
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p0, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
AI_RESPONSE_TIMEOUT = 60_000

# Case text's own step-3 wording, live-confirmed to reliably trigger the
# skill_builder tool call when the module is enabled, and to NOT trigger it
# when disabled.
SKILL_CREATION_MESSAGE = "Create a skill that summarizes daily standup notes"

# Case text's step-5 message ("Create project context describing our QA
# process") live-confirmed to reach a clarifying question from the AI
# rather than exercising the disabled-module path meaningfully (the AI
# never reaches the point of attempting the tool call either way, since the
# module is off — but a message that WOULD invoke the tool if enabled is
# the stronger negative test). Reused from the ELITEA-3254 family AFS
# (test_project_context_ai_generation_char_limit.py's
# CHAT_GENERATE_AND_SAVE_MESSAGE) per this AFS's own Test Data section.
PROJECT_CONTEXT_MESSAGE = (
    "Generate and save a project context for this project. It is a "
    "Playwright/pytest test automation suite for the Elitea AI platform, "
    "covering chat, agents, pipelines, skills, toolkits, and settings UI "
    "flows against a deployed DEV environment."
)

# Distinct wording from SKILL_CREATION_MESSAGE so the step-8 skill's name
# cannot collide with anything step 3 might otherwise have produced, making
# the step-9 "earlier message unchanged" check unambiguous.
SKILL_CREATION_MESSAGE_AFTER_ENABLE = (
    "Create a skill named autotest-builder-modules-marker that does nothing useful"
)


@allure.epic("Chat")
@allure.feature("Modules Panel")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/chat/build-skills-project-context/"
    "ELITEA-3370_skills-and-project-context-builder-disabled-prevents-entity-creation.md",
    "onetest-ai Test Case link (ELITEA-3370)",
)
class TestBuilderModulesDisabledPreventsEntityCreation:
    """ELITEA-3370 — Skills Builder / Project Context Builder disabled
    blocks entity creation server-side; enabling mid-conversation only
    affects new requests."""

    @pytest.mark.tms("ELITEA-3370")
    @allure.title(
        "Skills Builder and Project Context Builder disabled prevents entity creation; "
        "enabling mid-conversation does not retroactively affect earlier messages"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_builder_modules_disabled_prevents_entity_creation(
        self, page, conversation_id, skill_api, project_context_api
    ):
        chat = ChatPage(page)
        console_errors = chat.capture_console_errors()
        created_skill_id = None

        try:
            with allure.step(
                "Step 1 — Navigate to the fresh conversation, open the Modules panel, "
                "verify Skills Builder is OFF by default"
            ):
                chat.navigate_to_chat(conversation_id=conversation_id)
                chat.open_internal_tools_menu()
                assert not chat.is_module_toggle_checked("skill_builder"), (
                    "Expected the Skills Builder toggle to be OFF by default "
                    "for a never-touched conversation"
                )

            with allure.step(
                "Step 2 — Verify Project Context Builder is also OFF by default; "
                "close the Modules panel"
            ):
                assert not chat.is_module_toggle_checked("project_context_builder"), (
                    "Expected the Project Context Builder toggle to be OFF by "
                    "default for a never-touched conversation"
                )
                chat.close_modules_panel(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Send a skill-creation request with Skills Builder disabled"
            ):
                initial_count = chat.get_message_count()
                chat.send_message(SKILL_CREATION_MESSAGE, use_enter=True)
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                ai_response_index_step3 = initial_count + 1
                ai_message_step3 = chat.messages_container.nth(ai_response_index_step3)
                step3_response_text = chat._extract_message_body(ai_message_step3)

                assert chat.answer_tool_chip.count() == 0, (
                    "Expected no tool-invocation chip — the AI should never even "
                    "attempt the Skills Builder tool call while the module is disabled"
                )
                assert not chat.message_has_generated_entity_chip(ai_message_step3), (
                    "Expected no generated-entity chip on the step-3 response — "
                    "no Skill should have been created while the module is disabled"
                )

            with allure.step("Step 4 — Verify no Skill was created"):
                skills_after_step3 = skill_api.list_skills().get("rows", [])
                matching = [
                    s for s in skills_after_step3
                    if "standup" in s.get("name", "").lower() or "summar" in s.get("name", "").lower()
                ]
                assert matching == [], (
                    f"Expected no Skill matching the step-3 prompt to exist, found: {matching}"
                )

            with allure.step(
                "Step 5 — Send a project-context request with Project Context Builder disabled"
            ):
                pre_step5_get = project_context_api.get_project_context()
                assert pre_step5_get.status_code == 200, (
                    f"Expected GET project-context to return 200 before step 5, "
                    f"got {pre_step5_get.status_code}"
                )
                pre_step5_body = pre_step5_get.json()

                initial_count_pc = chat.get_message_count()
                chat.send_message(PROJECT_CONTEXT_MESSAGE, use_enter=True)
                chat.wait_for_ai_response(initial_count=initial_count_pc, timeout=AI_RESPONSE_TIMEOUT)
                ai_response_index_step5 = initial_count_pc + 1
                ai_message_step5 = chat.messages_container.nth(ai_response_index_step5)

                assert chat.answer_tool_chip.count() == 0, (
                    "Expected no tool-invocation chip — the AI should never even "
                    "attempt the Project Context Builder tool call while the "
                    "module is disabled"
                )
                assert not chat.message_has_generated_entity_chip(ai_message_step5), (
                    "Expected no generated-entity chip on the step-5 response — "
                    "no Project Context should have been created/updated while "
                    "the module is disabled"
                )

            with allure.step("Step 6 — Verify no Project Context was created/updated"):
                post_step5_get = project_context_api.get_project_context()
                assert post_step5_get.status_code == 200, (
                    f"Expected GET project-context to return 200 after step 5, "
                    f"got {post_step5_get.status_code}"
                )
                post_step5_body = post_step5_get.json()
                assert post_step5_body == pre_step5_body, (
                    f"Expected the Project Context to be unchanged by the "
                    f"step-5 request while the module is disabled: "
                    f"before={pre_step5_body!r}, after={post_step5_body!r}"
                )

            with allure.step(
                "Step 7 — Re-open the Modules panel, enable Skills Builder mid-conversation"
            ):
                chat.open_internal_tools_menu()
                chat.ensure_module_toggle_checked("skill_builder", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_module_toggle_checked("skill_builder"), (
                    "Expected the Skills Builder toggle to be checked immediately "
                    "after enabling it"
                )
                chat.close_modules_panel(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 8 — Re-send a skill-creation request; verify the Skill IS created this time"
            ):
                initial_count_enabled = chat.get_message_count()
                chat.send_message(SKILL_CREATION_MESSAGE_AFTER_ENABLE, use_enter=True)
                chat.wait_for_ai_response(initial_count=initial_count_enabled, timeout=AI_RESPONSE_TIMEOUT)
                ai_response_index_step8 = initial_count_enabled + 1
                ai_message_step8 = chat.messages_container.nth(ai_response_index_step8)

                tool_chips = chat.answer_tool_chip
                chip_texts = [tool_chips.nth(i).text_content() or "" for i in range(tool_chips.count())]
                assert any("Elitea Skills" in t and "post_elitea_core_skills" in t for t in chip_texts), (
                    f"Expected a tool-invocation chip naming the Skills tool's "
                    f"post_elitea_core_skills call, got chip texts: {chip_texts!r}"
                )
                assert chat.message_has_generated_entity_chip(ai_message_step8), (
                    "Expected a generated-entity chip on the step-8 response — "
                    "the Skill should have been created now that the module is enabled"
                )

                skills_after_step8 = skill_api.list_skills().get("rows", [])
                new_matches = [
                    s for s in skills_after_step8
                    if s["id"] not in {sk["id"] for sk in skills_after_step3}
                ]
                assert len(new_matches) == 1, (
                    f"Expected exactly one new Skill created by the step-8 request, "
                    f"got: {new_matches}"
                )
                created_skill_id = new_matches[0]["id"]

            with allure.step(
                "Step 9 — Scroll back to the earlier (step-3) message; verify it is "
                "byte-identical to what was captured before enabling the module"
            ):
                ai_message_step3_now = chat.messages_container.nth(ai_response_index_step3)
                step3_response_text_now = chat._extract_message_body(ai_message_step3_now)
                assert step3_response_text_now == step3_response_text, (
                    "Expected the step-3 response to be unchanged by the later "
                    "toggle-enable action — no retroactive Skill chip should "
                    f"appear. Before: {step3_response_text!r}, after: "
                    f"{step3_response_text_now!r}"
                )
                assert not chat.message_has_generated_entity_chip(ai_message_step3_now), (
                    "Expected the earlier step-3 response to still show no "
                    "generated-entity chip — enabling the module mid-conversation "
                    "must not retroactively create an entity for an earlier message"
                )

            with allure.step("Side-channel check — no console errors at any step"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
            if created_skill_id is not None:
                skill_api.delete_skill(created_skill_id)
