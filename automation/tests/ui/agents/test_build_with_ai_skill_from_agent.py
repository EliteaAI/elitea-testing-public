"""UI Test for ELITEA-1999 — Build with AI from Agent: created Skill is
auto-attached and the user is redirected back to the Agent editor.

Verifies the create-new-from-a-picker round-trip for Skills, created via
"Build with AI" from inside an existing Agent's SKILLS section: the user is
redirected back to the ORIGINATING Agent editor (never the Skill's own
details page), the new Skill is automatically attached to the Agent's
SKILLS section once the async attach chain completes, and the attachment
persists after an explicit Save + reload.

Spec: test-specs/agents/l2_build-with-ai-skill-from-agent-auto-attaches-and-redirects_ELITEA-1999.md

No existing spec exercises this round-trip (AFS § Coverage decision): a
repo-wide search for the ``newSkillId``/``ReturnUrl``/``SourceApplicationId``
query-param handshake (the pattern the source code's own comments call
"mirrors the toolkit newToolkitId round-trip") returned zero hits. The
nearest sibling AFS, ELITEA-1911, covers a DIFFERENT Skill-attachment
mechanism entirely — selecting an already-*suggested* Skill while generating
a brand-new Agent. This case instead edits an EXISTING Agent, opens its
SKILLS section's own "+ Skill -> Create new" picker, and creates a
brand-new Skill via Build with AI from there, with a completion contract
(redirect back to the Agent editor) that only exists because of the
``sourceApplicationId``/``returnUrl`` query params ``SkillMenu.jsx``'s
"Create new" handler attaches to the navigation.

Testid gap filled this implementation (``add-data-testid``, committed +
pushed to ``automation/testids``): ``agent-add-skill-create-new-button`` —
the "Create new" ``MenuItem`` inside the shared ``UnifiedDropdown.jsx`` (used
by ``SkillMenu.jsx`` for the Skills "+ Skill" picker) carried no testid at
all. Added an optional ``createNewTestId`` prop through
``UnifiedDropdown.jsx``'s existing ``createNewLabel``/``onCreateNew`` prop
trio (undefined by default, so ``ToolMenu.jsx``'s other ``UnifiedDropdown``
call sites are unaffected); ``SkillMenu.jsx`` (the caller for THIS section)
supplies ``"agent-add-skill-create-new-button"``. Same pattern as
ELITEA-2166's ``agents-create-new-button`` thread-through.
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from pages.agent_detail_page import AgentDetailPage
from pages.generate_skill_modal_page import GenerateSkillModalPage

logger = logging.getLogger("elitea.tests.agents.build_with_ai_skill")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
# The generate-draft call is a real (non-mocked) LLM call — a longer,
# more generous timeout avoids flaking on ordinary LLM-latency variance
# (same rationale as LIVE_GENERATE_RESPONSE_TIMEOUT in
# test_agent_build_with_ai.py).
LIVE_GENERATE_RESPONSE_TIMEOUT = 30_000
# The post-redirect auto-attach chain (GET skill details -> PATCH attach ->
# GET refetch skills list) is asynchronous and takes several seconds — the
# AFS's own timing re-run measured ~4s total. Poll with a generous timeout
# rather than a short/fixed wait (AFS step 6's explicit warning: an
# implementer who checks immediately after the redirect sees a false
# negative, not a product defect).
SKILL_ATTACH_TIMEOUT = 15_000

# Arbitrary, per the case's own Test Data table ("A valid description for
# the new Skill") — not verbatim from the case, which gives no exact wording.
PROMPT_TEXT = (
    "A skill that reviews GitHub pull request diffs and flags missing unit tests."
)


class TestBuildWithAISkillFromAgent:
    """ELITEA-1999: Build with AI from Agent — created Skill is auto-attached
    and the user is redirected back to the Agent editor (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agents/ELITEA-1999_build-with-ai-skill-from-agent-auto-attaches-and-redirects.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_build_with_ai_skill_auto_attaches_and_redirects_to_agent(
        self, page, agent_id, skill_api
    ):
        """Creating a Skill via Build with AI from an Agent's SKILLS section
        redirects back to the Agent editor (never the Skill details page),
        auto-attaches the new Skill once the async attach chain completes,
        and the attachment persists after Save + reload.

        Steps (AFS
        test-specs/agents/l2_build-with-ai-skill-from-agent-auto-attaches-and-redirects_ELITEA-1999.md):
        1. Open the fixture Agent for editing; in the SKILLS section click
           "+ Skill" -> "Create new"; verify navigation to
           /skills/create?source_application_id=...&return_url=....
        2. Click "Build with AI"; fill the prompt; click Generate; verify
           the generate-draft POST resolves 200 and the review form shows
           the generated Name/Description/Instructions.
        3. Click "Create Skill"; verify the creation POST resolves 201 and
           the URL transitions to /agents/all/{agent_id}?..., NOT to a
           Skill-details URL.
        4. Verify the user lands on the Agent editor, not the Skill details
           page.
        5. Verify the new Skill is automatically attached (async — poll,
           do not assert immediately, see SKILL_ATTACH_TIMEOUT).
        6. Save the Agent and reload it; verify the attached Skill is still
           present and correctly linked.
        """
        detail_page = AgentDetailPage(page)
        modal = GenerateSkillModalPage(page)

        skill_id = None
        try:
            with allure.step("Setup — open the fixture Agent for editing"):
                detail_page.navigate(agent_id)

            with allure.step(
                'Step 1 — In the SKILLS section, click "+ Skill" -> '
                '"Create new"; verify navigation to the Skill-create page '
                "with the source_application_id/return_url round-trip params"
            ):
                detail_page.open_create_new_skill(timeout=NAVIGATION_TIMEOUT)
                page.wait_for_url(
                    lambda url: "/skills/create" in url
                    and f"source_application_id={agent_id}" in url
                    and "return_url=" in url,
                    timeout=NAVIGATION_TIMEOUT,
                )

            with allure.step(
                'Step 2 — Click "Build with AI"; enter the prompt and click '
                "Generate; verify the generate-draft request resolves 200 "
                "and the review form shows the generated Name/Description/"
                "Instructions"
            ):
                modal.open_modal(timeout=UI_ELEMENT_TIMEOUT)
                modal.fill_prompt(PROMPT_TEXT)
                assert modal.get_prompt_value() == PROMPT_TEXT, (
                    "Prompt textarea should contain exactly the entered text"
                )

                generate_response = modal.click_generate_and_wait_for_response(
                    timeout=LIVE_GENERATE_RESPONSE_TIMEOUT
                )
                assert generate_response.status == 200, (
                    f"Expected the generate-draft request to succeed, got "
                    f"{generate_response.status}"
                )
                modal.wait_for_review_form(timeout=LIVE_GENERATE_RESPONSE_TIMEOUT)

                generated_name = modal.get_review_name()
                assert generated_name, (
                    "Review form's Name field should be pre-populated after generation"
                )
                assert modal.get_review_description(), (
                    "Review form's Description field should be pre-populated after generation"
                )
                assert modal.get_review_instructions(), (
                    "Review form's Instructions field should be pre-populated after generation"
                )

            with allure.step(
                'Step 3 — Click "Create Skill"; verify the creation POST '
                "resolves 201 and the URL redirects to the Agent editor, "
                "NOT a Skill-details page"
            ):
                with page.expect_response(
                    lambda r: r.request.method == "POST"
                    and "/elitea_core/skills/prompt_lib/" in r.url
                ) as resp_info:
                    modal.approve_button.click()
                create_response = resp_info.value
                assert create_response.status == 201, (
                    f"Skill-creation POST should resolve 201, got "
                    f"{create_response.status} for {create_response.url}"
                )
                created_skill = create_response.json()
                skill_id = created_skill.get("id")
                assert skill_id, (
                    f"Expected a numeric skill id in the creation response, "
                    f"got: {created_skill!r}"
                )

                page.wait_for_url(
                    lambda url: f"/agents/all/{agent_id}" in url,
                    timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(
                "Step 4 — Verify the user lands on the Agent editor, not "
                "the Skill details page"
            ):
                assert f"/agents/all/{agent_id}" in page.url, (
                    f"Expected to be redirected to the originating Agent "
                    f"editor, got {page.url}"
                )
                assert "/skills/all/" not in page.url, (
                    f"Should NOT redirect to the Skill's own details page, "
                    f"got {page.url}"
                )
                detail_page.wait_for_page_load()

            with allure.step(
                "Step 5 — Verify the newly created Skill is automatically "
                "attached in the SKILLS section (async — poll with a real "
                "timeout, never assert immediately after the redirect; "
                "AFS's own timing re-run measured ~4s total for the "
                "GET-skill-details -> PATCH-attach -> GET-refetch chain)"
            ):
                detail_page.ensure_skills_section_visible(timeout=SKILL_ATTACH_TIMEOUT)
                counter_text = detail_page.wait_for_skills_counter(
                    "1/", timeout=SKILL_ATTACH_TIMEOUT
                )
                assert counter_text.startswith("1/"), (
                    f'Expected the Skills counter to read "1/N skills '
                    f'added." once the async attach chain completes, got '
                    f"{counter_text!r}"
                )
                skill_card = detail_page.get_skill_card_by_id(skill_id)
                expect(skill_card).to_be_visible(timeout=SKILL_ATTACH_TIMEOUT)

            with allure.step(
                "Step 6 — Save the Agent and reload it; verify the attached "
                "Skill is still present and correctly linked (AFS note: "
                "the attachment is already server-persisted the moment the "
                "PATCH resolves — Save is not the causal persistence "
                "mechanism, but the case's own step is followed literally)"
            ):
                detail_page.click_save()
                page.reload()
                detail_page.wait_for_page_load()
                detail_page.ensure_skills_section_visible(timeout=UI_ELEMENT_TIMEOUT)

                counter_after_reload = detail_page.wait_for_skills_counter(
                    "1/", timeout=UI_ELEMENT_TIMEOUT
                )
                assert counter_after_reload.startswith("1/"), (
                    f'Expected the Skills counter to still read "1/N '
                    f'skills added." after Save + reload, got '
                    f"{counter_after_reload!r}"
                )
                skill_card_after_reload = detail_page.get_skill_card_by_id(skill_id)
                expect(skill_card_after_reload).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        finally:
            with allure.step("Cleanup — delete the created Skill"):
                # Skill first, then the fixture Agent (via the agent_id
                # fixture's own teardown) — deleting the Agent does NOT
                # cascade-delete the Skill (independent entities, AFS §
                # Cleanup), so it must be removed separately here.
                if skill_id:
                    try:
                        skill_api.delete_skill(skill_id)
                        logger.info("Deleted skill %s", skill_id)
                    except Exception as exc:
                        logger.warning(
                            "Cleanup failed for skill %s: %s", skill_id, exc
                        )
