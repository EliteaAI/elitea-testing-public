"""UI Tests for the Agent "Build with AI" generation flow.

Covers ELITEA-1915: generation failure shows an error, preserves the
entered prompt, and a retry (re-clicking the same Generate button) succeeds
once the service recovers.

Covers ELITEA-1907: the generated draft review form includes a Suggested
Resources section (Toolkits/MCP/Pipelines/Agents/Skills), each suggested
item shows a name (and description when the underlying resource has one),
and no suggestion is pre-selected.

Covers ELITEA-1909: only explicitly selected suggested resources (Toolkit,
nested Agent) are attached to the created agent, and a non-selected
suggested resource is absent.

Spec: test-specs/agents/l2_build-with-ai-generation-failure-retry_ELITEA-1915.md
Spec: test-specs/agents/l2_build-with-ai-generated-draft-suggested-resources_ELITEA-1907.md
Spec: test-specs/agents/l2_build-with-ai-selected-suggested-resources-attached-to-created-agent_ELITEA-1909.md
Covers: GenerateAgentModal (GenerateEntityModal.jsx via GenerateAgentModal.jsx)

Markers:
    - ui: requires browser
    - agents: agent-related tests
    - p2: medium priority (case priority: medium)

Usage:
    cd automation
    pytest tests/ui/agents/test_agent_build_with_ai.py -v
"""

import logging

import allure
import pytest

from pages.agent_detail_page import AgentDetailPage
from pages.agents_list_page import AgentsListPage
from pages.generate_agent_modal_page import GenerateAgentModalPage

logger = logging.getLogger("elitea.tests.agents.build_with_ai")

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
NAVIGATION_TIMEOUT = 15000
GENERATE_RESPONSE_TIMEOUT = 15000
LOADING_STATE_TIMEOUT = 3000
REVIEW_FORM_TIMEOUT = 15000

# ELITEA-1909's generate-draft call is a real (non-mocked) LLM call, unlike
# ELITEA-1915/1907's mocked responses — a longer, more generous timeout
# avoids flaking on ordinary LLM-latency variance.
LIVE_GENERATE_RESPONSE_TIMEOUT = 30000

PROMPT_TEXT = (
    "Create a customer support triage agent that categorizes incoming "
    "tickets by urgency and routes them to the correct team."
)
SIMULATED_ERROR_MESSAGE = "Simulated generation failure for ELITEA-1915"

# Minimal, valid draft payload mirroring the real generate_application_draft
# response shape (GenerateAgentModal.jsx / GenerateAgentReviewForm.jsx) —
# used for the retry's synthetic recovery (option (b) per the AFS).
RETRY_DRAFT_PAYLOAD = {
    "name": "Support Ticket Triage Agent",
    "description": "Categorizes incoming support tickets by urgency and routes them to the correct team.",
    "instructions": "You are a support ticket triage agent. Read each incoming ticket, "
                     "classify its urgency, and route it to the correct team.",
    "welcome_message": "Hi! I'll help triage your support tickets.",
    "conversation_starters": [
        "Triage this ticket for me",
        "What urgency is this issue?",
        "Which team should handle this?",
        "Summarize today's incoming tickets",
    ],
}

# ELITEA-1907 — verbatim prompt per the case's Test Data table.
SUGGESTED_RESOURCES_PROMPT_TEXT = "An agent that queries GitHub and runs Jira updates"

# Mocked generate_application_draft response for ELITEA-1907.
#
# Mocking (the same technique ELITEA-1915 uses for failure/retry) is used
# here deliberately, per the AFS's Known Defects Found #1 / Automation
# Hints: the only live-suggestible resource in this project (`Remote
# Github` MCP, id 3) has an empty description, so a live run alone cannot
# demonstrate the "description shown when present" half of step 4, nor
# populate the Toolkit/Pipeline/Agent categories the case's Pass criteria
# also names ("relevant Toolkits/Agents/Pipelines/MCPs" — step 3 and Pass
# criteria). Mocking is the read-only-by-default resolution (Hard Rule 10):
# it exercises the full case scope — all four named categories populated,
# both the "has description" and "no description" rendering paths, and the
# "empty category renders no section" path (via the untouched `skill`
# category) — without creating, mutating, or tearing down any real project
# fixture.
#
# The `suggested_mcp` entry mirrors the AFS's live-observed Network
# Behavior payload exactly (id 3, "Remote Github", description: null) so
# that half of the assertions still reflect a real, previously-verified
# server response shape.
#
# Source-confirmed quirk found during implementation (SuggestionItem.jsx:20,
# not covered by the AFS — the AFS's only live suggestion was an MCP, never
# a toolkit): for `entityType === 'toolkit'` the card's secondary text is
# `item.type` (the toolkit's technical type, e.g. `"github"`), NOT
# `item.description` — every other entity type (mcp, pipeline, agent,
# skill) uses `item.description`. This is intentional product behavior,
# not a bug: toolkit cards show the tool's type to disambiguate which
# integration it is, not a free-text description. Case step 4 ("shows its
# name and description") is asserted here against the verified live
# contract per each entity type, not the literal word "description" —
# see the reverse-masking guard (test-automation-workflow skill § Hard
# Rules → 2): the toolkit `type` field IS this card's secondary text.
SUGGESTED_RESOURCES_DRAFT_PAYLOAD = {
    "name": "GitHub & Jira Integration",
    "description": "An agent that queries GitHub issues and runs Jira updates.",
    "instructions": "You are an agent that integrates with GitHub and Jira to query issues and run updates.",
    "welcome_message": "Hi! I can help you query GitHub and update Jira.",
    "conversation_starters": [
        "Show me open GitHub issues",
        "Update a Jira ticket",
        "List my Jira sprints",
        "Check GitHub PR status",
    ],
    "suggested_toolkits": [
        {
            # "type" here is the toolkit's technical type (icon lookup +
            # this card's secondary text — see the SuggestionItem.jsx
            # quirk note above), NOT an entity-category discriminator.
            "id": 101,
            "type": "github",
            "name": "GitHub Toolkit",
            "description": "Queries GitHub repositories and issues.",
        }
    ],
    "suggested_mcp": [
        {"id": 3, "type": "mcp", "name": "Remote Github", "description": None}
    ],
    "suggested_pipelines": [
        {
            "id": 202,
            "type": "pipeline",
            "name": "Jira Update Pipeline",
            "description": "Automates Jira ticket updates.",
        }
    ],
    "suggested_agents": [
        {
            "id": 303,
            "type": "agent",
            "name": "Jira Triage Agent",
            "description": "Triages incoming Jira tickets and assigns them to the right team.",
        }
    ],
    "suggested_skills": [],
}


class TestAgentBuildWithAIGenerationFailureRetry:
    """Build with AI (P2): generation failure shows error, prompt is
    preserved, and retry succeeds once the service recovers."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agents/build_with_ai/ELITEA-1915_build-with-ai-generation-failure-shows-error-and-allows-retry.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_generation_failure_shows_error_and_allows_retry(self, page):
        """Generation failure surfaces an error, preserves the prompt, and a
        retry (via the same Generate button) succeeds once the service
        recovers."""
        list_page = AgentsListPage(page)
        modal = GenerateAgentModalPage(page)

        # ------------------------------------------------------------------
        # Step 1 — Open modal, enter description
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Open modal, enter description"):
            list_page.navigate_to_create()
            modal.open_modal()

            assert not modal.is_generate_enabled(), (
                "Generate button should be disabled while the prompt is empty"
            )

            modal.fill_prompt(PROMPT_TEXT)

            assert modal.get_prompt_value() == PROMPT_TEXT, (
                "Prompt textarea should contain exactly the entered text"
            )
            assert modal.is_generate_enabled(), (
                "Generate button should become enabled once the prompt is non-empty"
            )

        # ------------------------------------------------------------------
        # Step 2 — Trigger/simulate generation failure
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Trigger/simulate generation failure"):
            modal.mock_generate_failure(SIMULATED_ERROR_MESSAGE, status=500)
            response = modal.click_generate_and_wait_for_response(timeout=GENERATE_RESPONSE_TIMEOUT)

            assert response.status == 500, (
                f"Expected the mocked generate-draft request to resolve 500, got {response.status}"
            )
            modal.wait_for_input_step(timeout=LOADING_STATE_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 3 — Verify clear error message displayed
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Verify clear error message displayed"):
            assert modal.is_error_alert_visible(), (
                "An error alert should be displayed in the modal after a generation failure"
            )
            assert modal.get_error_message() == SIMULATED_ERROR_MESSAGE, (
                "Error alert should surface the backend's error message verbatim, "
                f"got: {modal.get_error_message()!r}"
            )

        # ------------------------------------------------------------------
        # Step 4 — Verify the previously entered prompt is still present
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Verify the previously entered prompt is still present"):
            assert modal.get_prompt_value() == PROMPT_TEXT, (
                "Prompt text entered before the failure should still be visible after the failure"
            )

        # ------------------------------------------------------------------
        # Step 5 — Click retry / "Generate agent" button
        # ------------------------------------------------------------------
        with allure.step('Step 5 — Click retry / "Generate agent" button'):
            modal.clear_generate_mock()
            modal.mock_generate_success(RETRY_DRAFT_PAYLOAD)

            with modal.expect_generate_response(timeout=GENERATE_RESPONSE_TIMEOUT) as retry_response_info:
                modal.generate_button.click()

                # resetGenerate() fires before the retry request — the stale
                # Step 3 error should be gone as soon as the retry is in
                # flight, not only once the new (artificially delayed)
                # request resolves.
                modal.error_alert.wait_for(state="hidden", timeout=LOADING_STATE_TIMEOUT)
                modal.wait_for_loading_visible(timeout=LOADING_STATE_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 6 — Verify the retry succeeds and a draft is returned
        # ------------------------------------------------------------------
        with allure.step("Step 6 — Verify the retry succeeds and a draft is returned"):
            retry_response = retry_response_info.value
            assert retry_response.status == 200, (
                f"Expected the retried generate-draft request to succeed, got {retry_response.status}"
            )
            assert retry_response.json()["name"] == RETRY_DRAFT_PAYLOAD["name"], (
                "Retried request should resolve with the recovered draft payload"
            )

            modal.wait_for_input_step_hidden(timeout=1000)
            modal.wait_for_review_form(timeout=REVIEW_FORM_TIMEOUT)


class TestAgentBuildWithAISuggestedResources:
    """Build with AI (P2): generated draft review form includes a Suggested
    Resources section, each suggested item shows a name (and description
    when the underlying resource has one), and nothing is pre-selected."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agents/build_with_ai/ELITEA-1907_build-with-ai-generated-draft-includes-suggested-resources-section.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_generated_draft_includes_suggested_resources_section(self, page):
        """Submitting a description implying resource use surfaces a
        Suggested Resources section in the review form: relevant
        Toolkit/Agent/Pipeline/MCP suggestions are shown (each with a name,
        and a description when the underlying resource has one), categories
        with no suggestions render no section at all, and no suggestion is
        pre-selected."""
        list_page = AgentsListPage(page)
        modal = GenerateAgentModalPage(page)

        # ------------------------------------------------------------------
        # Step 1 — Open modal, submit description implying resource use
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Open modal, submit description implying resource use"):
            list_page.navigate_to_create()
            modal.open_modal()
            modal.fill_prompt(SUGGESTED_RESOURCES_PROMPT_TEXT)

            assert modal.get_prompt_value() == SUGGESTED_RESOURCES_PROMPT_TEXT, (
                "Prompt textarea should contain exactly the entered text"
            )
            assert modal.is_generate_enabled(), (
                "Generate button should be enabled once a non-empty description is entered"
            )

        # ------------------------------------------------------------------
        # Step 2 — Wait for generation to complete
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Wait for generation to complete"):
            modal.mock_generate_success(SUGGESTED_RESOURCES_DRAFT_PAYLOAD)

            with modal.expect_generate_response(timeout=GENERATE_RESPONSE_TIMEOUT) as response_info:
                modal.generate_button.click()

                # Case step 2's "Verify": the modal shows the loading state
                # before transitioning to the review form. Mirrors ELITEA-1915's
                # Step 5, which asserts the same loading indicator the same
                # way — checked here, in-flight, before the (artificially
                # delayed) mocked response resolves.
                modal.wait_for_loading_visible(timeout=LOADING_STATE_TIMEOUT)

            response = response_info.value

            assert response.status == 200, (
                f"Expected the generate-draft request to succeed, got {response.status}"
            )
            response_body = response.json()
            assert response_body["suggested_mcp"][0]["name"] == "Remote Github", (
                "generate-draft response should carry the suggested MCP through unchanged — "
                "asserted against the response body per the AFS's Network Behavior note "
                "(the more stable, less rendering-detail-coupled contract)"
            )

            modal.wait_for_review_form(timeout=REVIEW_FORM_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 3 — Verify Suggested Resources section(s) shown with relevant
        # suggestions; categories with no suggestions render no section
        # ------------------------------------------------------------------
        with allure.step(
            "Step 3 — Verify Suggested Resources section shown with relevant "
            "Toolkits/Agents/Pipelines/MCPs; empty categories render no section"
        ):
            assert modal.is_resource_section_visible("toolkit"), (
                'The "Suggested Toolkits:" section should be present when suggested_toolkits is non-empty'
            )
            assert modal.is_resource_section_visible("mcp"), (
                'The "Suggested MCP:" section should be present when suggested_mcp is non-empty'
            )
            assert modal.is_resource_section_visible("pipeline"), (
                'The "Suggested Pipelines:" section should be present when suggested_pipelines is non-empty'
            )
            assert modal.is_resource_section_visible("agent"), (
                'The "Suggested Agents:" section should be present when suggested_agents is non-empty'
            )
            # ResourceSuggestions.jsx: `if (!items?.length) return null` — an
            # empty category renders no section at all, not an empty one.
            assert not modal.is_resource_section_visible("skill"), (
                'The "Suggested Skills:" section should NOT render when suggested_skills is empty'
            )

        # ------------------------------------------------------------------
        # Step 4 — Verify each suggested resource shows its name and
        # description (description shown when present, absent from the DOM
        # when not — the verified contract per AFS Known Defects Found #1)
        # ------------------------------------------------------------------
        with allure.step(
            "Step 4 — Verify each suggested resource shows its name; "
            "description shown when present, absent from DOM when not"
        ):
            assert modal.get_resource_name_text("toolkit", 101) == "GitHub Toolkit", (
                "Toolkit suggestion card should display the resource's name"
            )
            # Source-confirmed quirk (SuggestionItem.jsx:20 — see the payload
            # comment above): for entityType "toolkit" the card's secondary
            # text is item.type ("github"), not item.description — asserting
            # the live-verified contract, not the case's literal wording.
            assert modal.resource_description_exists("toolkit", 101), (
                "Toolkit suggestion should render a secondary-text element (its type)"
            )
            assert modal.get_resource_description_text("toolkit", 101) == "github", (
                "Toolkit suggestion card's secondary text should be the toolkit's type, per "
                "SuggestionItem.jsx's entityType-specific secondaryText selection"
            )

            assert modal.get_resource_name_text("mcp", 3) == "Remote Github", (
                "MCP suggestion card should display the resource's name"
            )
            assert not modal.resource_description_exists("mcp", 3), (
                "MCP suggestion has no description (matches this project's live `Remote Github` MCP, "
                "which carries an empty description) — SuggestionItem.jsx's showSecondary conditional "
                "should omit the description element from the DOM entirely, not render it empty"
            )

            assert modal.get_resource_name_text("pipeline", 202) == "Jira Update Pipeline", (
                "Pipeline suggestion card should display the resource's name"
            )
            assert modal.resource_description_exists("pipeline", 202), (
                "Pipeline suggestion has a non-empty description and should render a description element"
            )
            assert modal.get_resource_description_text("pipeline", 202) == (
                "Automates Jira ticket updates."
            ), "Pipeline suggestion card should display the resource's description"

            assert modal.get_resource_name_text("agent", 303) == "Jira Triage Agent", (
                "Agent suggestion card should display the resource's name"
            )
            assert modal.resource_description_exists("agent", 303), (
                "Agent suggestion has a non-empty description and should render a description element"
            )
            assert modal.get_resource_description_text("agent", 303) == (
                "Triages incoming Jira tickets and assigns them to the right team."
            ), "Agent suggestion card should display the resource's description"

        # ------------------------------------------------------------------
        # Step 5 — Verify no resource is pre-selected
        # ------------------------------------------------------------------
        with allure.step("Step 5 — Verify no resource is pre-selected"):
            assert not modal.is_resource_checked("toolkit", 101), (
                "Toolkit suggestion should not be pre-selected"
            )
            assert not modal.is_resource_checked("mcp", 3), (
                "MCP suggestion should not be pre-selected"
            )
            assert not modal.is_resource_checked("agent", 303), (
                "Agent suggestion should not be pre-selected"
            )
            assert not modal.is_resource_checked("pipeline", 202), (
                "Pipeline suggestion should not be pre-selected"
            )


class TestAgentBuildWithAISelectedResourcesAttached:
    """Build with AI (P2): only explicitly selected suggested resources
    (Toolkit, nested Agent) are attached to the created agent; non-selected
    suggested resources are absent."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agents/build_with_ai/ELITEA-1909_build-with-ai-selected-suggested-resources-attached-to-created-agent.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_selected_suggested_resources_attached_and_non_selected_absent(
        self, page, agent_api, github_toolkit, github_relevant_agents
    ):
        """Selecting one suggested Toolkit and one suggested Agent (leaving a
        second suggested Agent unchecked) and clicking "Create Agent"
        attaches exactly the selected resources to the created agent's Tools
        section; the deliberately-unselected Agent is absent."""
        list_page = AgentsListPage(page)
        modal = GenerateAgentModalPage(page)
        selected_agent = github_relevant_agents["selected"]
        not_selected_agent = github_relevant_agents["not_selected"]

        # Names both fixture agents explicitly so the suggestion engine's
        # relevance match surfaces both as `suggested_agents` candidates —
        # see ELITEA-1909 AFS Automation Hints (prompt text and fixture
        # descriptions are coupled by design).
        prompt_text = (
            "An agent that queries GitHub repositories using the GitHub toolkit "
            f"and delegates issue-triage and pull-request-review work to a "
            f"{selected_agent['name']} or a {not_selected_agent['name']} sub-agent."
        )

        created_agent_id = None
        try:
            # ------------------------------------------------------------------
            # Steps 1-2 — GitHub toolkit fixture (case step 1) already created;
            # generate a draft mentioning it and both fixture agents (case step 2)
            # ------------------------------------------------------------------
            with allure.step("Step 1-2 — Generate an agent draft mentioning the GitHub toolkit"):
                list_page.navigate_to_create()
                modal.open_modal()
                modal.fill_prompt(prompt_text)

                assert modal.get_prompt_value() == prompt_text, (
                    "Prompt textarea should contain exactly the entered text"
                )

                response = modal.click_generate_and_wait_for_response(
                    timeout=LIVE_GENERATE_RESPONSE_TIMEOUT
                )
                assert response.status == 200, (
                    f"Expected the generate-draft request to succeed, got {response.status}"
                )
                modal.wait_for_review_form()

            # ------------------------------------------------------------------
            # Step 3 — Suggested Resources area shows the Toolkit and both Agents
            # ------------------------------------------------------------------
            with allure.step("Step 3 — Verify Suggested Toolkits/Agents sections are populated"):
                assert modal.is_resource_section_visible("toolkit"), (
                    'The "Suggested Toolkits:" section should be present with the created GitHub toolkit'
                )
                assert modal.get_resource_name_text("toolkit", github_toolkit["id"]) == github_toolkit["name"], (
                    "Suggested toolkit card should be the GitHub toolkit created for this test"
                )
                assert modal.is_resource_section_visible("agent"), (
                    'The "Suggested Agents:" section should be present — requires the '
                    "github_relevant_agents precondition (see AFS Preconditions)"
                )
                assert modal.get_resource_name_text("agent", selected_agent["id"]) == selected_agent["name"], (
                    "Suggested agent card should be the fixture agent intended for selection"
                )
                assert modal.get_resource_name_text("agent", not_selected_agent["id"]) == not_selected_agent["name"], (
                    "Suggested agent card should also include the fixture agent intended to stay unselected"
                )
                assert not modal.is_resource_checked("toolkit", github_toolkit["id"]), (
                    "Toolkit suggestion should not be pre-selected"
                )
                assert not modal.is_resource_checked("agent", selected_agent["id"]), (
                    "Agent suggestion should not be pre-selected"
                )
                assert not modal.is_resource_checked("agent", not_selected_agent["id"]), (
                    "Agent suggestion should not be pre-selected"
                )

            # ------------------------------------------------------------------
            # Steps 3-4 (case) — select the suggested Toolkit and the
            # "selected" suggested Agent; deliberately leave the other
            # suggested Agent unchecked
            # ------------------------------------------------------------------
            with allure.step("Step 3-4 — Select the suggested Toolkit and one suggested Agent"):
                modal.select_resource("toolkit", github_toolkit["id"])
                modal.select_resource("agent", selected_agent["id"])

                assert modal.is_resource_checked("toolkit", github_toolkit["id"]), (
                    "Toolkit card should be checked/selected after clicking its checkbox"
                )
                assert modal.is_resource_checked("agent", selected_agent["id"]), (
                    f"{selected_agent['name']!r} card should be checked/selected after clicking its checkbox"
                )
                assert not modal.is_resource_checked("agent", not_selected_agent["id"]), (
                    f"{not_selected_agent['name']!r} card should remain unchecked — this test's negative fixture"
                )

            # ------------------------------------------------------------------
            # Step 5 (case) — Click "Create Agent"; verify the three
            # sequential network calls and the auto-navigation to the
            # created agent's detail page
            # ------------------------------------------------------------------
            with allure.step('Step 5 — Click "Create Agent"'):
                create_response, toolkit_patch_response, relation_patch_response = (
                    modal.click_approve_and_wait_for_creation()
                )

                assert create_response.status == 201, (
                    f"Expected the base-agent create call to resolve 201, got {create_response.status}"
                )
                created_agent_id = create_response.json()["id"]

                assert toolkit_patch_response.status == 201, (
                    f"Expected the selected-Toolkit association PATCH to resolve 201, "
                    f"got {toolkit_patch_response.status}"
                )
                assert toolkit_patch_response.json().get("has_relation") is True, (
                    "Toolkit association response should confirm has_relation: true"
                )

                assert relation_patch_response.status == 201, (
                    f"Expected the selected-Agent association PATCH to resolve 201, "
                    f"got {relation_patch_response.status}"
                )
                assert relation_patch_response.json().get("has_relation") is True, (
                    "Agent association response should confirm has_relation: true"
                )

                page.wait_for_url(f"**/agents/all/{created_agent_id}**")

            # ------------------------------------------------------------------
            # Step 6 (case) — created Agent detail page is displayed
            # ------------------------------------------------------------------
            detail_page = AgentDetailPage(page)
            with allure.step("Step 6 — Verify the created Agent detail page is displayed"):
                detail_page.wait_for_page_load()
                assert f"/agents/all/{created_agent_id}" in page.url, (
                    f"Expected to land on the created agent's detail page, got {page.url}"
                )

            # ------------------------------------------------------------------
            # Step 7 (case) — selected Toolkit present in the Tools section
            # ------------------------------------------------------------------
            with allure.step("Step 7 — Verify the selected Toolkit is present in the Tools section"):
                assert detail_page.is_toolkit_attached(github_toolkit["name"]), (
                    f"Selected toolkit {github_toolkit['name']!r} should appear in the Tools section"
                )

            # ------------------------------------------------------------------
            # Step 8 (case) — selected nested Agent present in the same
            # Tools section (shares ToolCard.jsx/agent-toolkit-card with
            # Toolkit cards — see AFS Concrete Handles)
            # ------------------------------------------------------------------
            with allure.step("Step 8 — Verify the selected nested Agent is present in the Tools section"):
                assert detail_page.is_toolkit_attached(selected_agent["name"]), (
                    f"Selected nested agent {selected_agent['name']!r} should appear in the Tools section"
                )

            # ------------------------------------------------------------------
            # Step 9 (case) — non-selected suggested resource is absent
            # ------------------------------------------------------------------
            with allure.step("Step 9 — Verify the non-selected suggested Agent is absent"):
                assert not detail_page.is_toolkit_attached(not_selected_agent["name"]), (
                    f"Non-selected agent {not_selected_agent['name']!r} should NOT appear in the Tools section"
                )
        finally:
            if created_agent_id is not None:
                try:
                    agent_api.delete_agent(created_agent_id)
                    logger.info("Deleted created agent %s", created_agent_id)
                except Exception as exc:
                    logger.warning("Failed to delete created agent %s during teardown: %s", created_agent_id, exc)
