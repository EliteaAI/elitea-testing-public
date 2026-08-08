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

Covers ELITEA-1911: extends ELITEA-1909's coverage to the Skill suggested-
resource type — a selected suggested Skill is attached to the created
agent's SKILLS section (a distinct accordion/network contract from the
Toolkit/Agent flow), and a non-selected suggested Skill is absent.

Covers ELITEA-1905: extends ELITEA-1915's Step 1 (open modal, enter
description) with standalone, message-carrying visibility assertions for
the prompt input, Generate button, and Cancel button — closing the one
genuine gap left by the covering tests (`cancel_button` was previously
never referenced by any test's executed code path).

Covers ELITEA-1906: the review form's Name, Description, Instructions,
Welcome Message, and Conversation-starter fields are all pre-populated with
the generated draft's values AND remain editable before agent creation — the
first test in this file to read the Welcome Message / Chat-starter fields at
all (their `data-testid`s were added for this case; see the AFS Concrete
Handles).

Covers ELITEA-1914: extends ELITEA-1909/1911's create+navigate coverage to
the ungated, no-resource-selection path — approving a plain draft (no
suggested resources rendered at all) creates the agent via the base-create
POST only (no toolkit/agent/skill relation calls), auto-navigates to the
created agent's detail page with the draft's content carried over and the
Skills counter reading zero, and the new agent is visible back on the
Agents list — the one step (post-creation Agents-list verification) not
exercised by any prior Build-with-AI test in this file.

Covers ELITEA-1908: extends ELITEA-1909/1911's create+navigate coverage to
a full, combined-across-categories zero-selection path — a draft with
suggested Toolkit/MCP/Pipeline/Agent resources ALL rendered simultaneously
(cards visible, checkboxes present) is approved with literally zero boxes
checked, proving (a) no toolkit/agent-relation/skill relation call fires at
all — not even for one item, across any category — and (b) the created
agent's Tools section and Skills counter both confirm zero attachments
across every category. Distinct from ELITEA-1909/1911 (which always select
at least one item per category) and from ELITEA-1914 (whose plain draft
never renders any suggestion at all) — the first test in this file to
assert a combined, all-category zero with resources genuinely on offer.

Spec: test-specs/agents/l2_build-with-ai-generation-failure-retry_ELITEA-1915.md
Spec: test-specs/agents/l2_build-with-ai-generated-draft-suggested-resources_ELITEA-1907.md
Spec: test-specs/agents/l2_build-with-ai-selected-suggested-resources-attached-to-created-agent_ELITEA-1909.md
Spec: test-specs/agents/lextend_build-with-ai-selected-suggested-skills-attached-to-created-agent_ELITEA-1911.md
Spec: test-specs/agents/lextend_build-with-ai-modal-contains-prompt-generate-cancel-controls_ELITEA-1905.md
Spec: test-specs/agents/l2_build-with-ai-draft-generated-from-natural-language-description_ELITEA-1906.md
Spec: test-specs/agents/lextend_build-with-ai-approve-creates-agent-and-navigates-to-agent-menu_ELITEA-1914.md
Spec: test-specs/agents/lextend_build-with-ai-suggested-resources-require-explicit-selection_ELITEA-1908.md
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

# ELITEA-1914 — a deliberately generic/non-resource-implying prompt (per the
# AFS's Test Data) so no "Suggested {Category}:" section renders at all —
# the negative control that distinguishes the plain-approve path from
# ELITEA-1909/1911's positive-attachment scenarios.
NO_RESOURCES_PROMPT_TEXT = (
    "Create a simple agent that summarizes long text documents into concise bullet-point summaries."
)

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

# ELITEA-1906 — verbatim prompt per the case's Test Data table.
FIELD_POPULATION_PROMPT_TEXT = "An agent that helps write concise JIRA ticket descriptions"

# Mocked generate_application_draft response for ELITEA-1906 — matches the
# AFS's Test Data payload exactly. Content is plausibly aligned with the
# prompt's intent (a live, unmocked reference call during analysis returned a
# semantically-matching draft — see the AFS's Test Data section) so the
# assertions genuinely exercise "the UI renders the generated draft content",
# not just "the UI renders some non-empty string". Suggested-resource arrays
# are deliberately empty — ResourceSuggestions.jsx renders null for an empty
# category (already asserted by ELITEA-1907) — keeping the DOM surface
# focused on the 5 core fields this case cares about.
FIELD_POPULATION_DRAFT_PAYLOAD = {
    "name": "JIRA Ticket Description Writer",
    "description": "Helps users turn rough notes into concise, well-structured JIRA ticket descriptions.",
    "instructions": (
        "You are a helpful assistant that writes concise, well-structured JIRA ticket descriptions "
        "from rough notes, bug reports, or feature ideas. Keep descriptions compact, use bullet "
        "points where helpful, and include acceptance criteria when relevant."
    ),
    "welcome_message": (
        "Hi! I can help you write clear, concise JIRA ticket descriptions. Paste your notes to get started."
    ),
    "conversation_starters": [
        "Turn these notes into a concise JIRA ticket description",
        "Write a bug ticket description from this issue report",
    ],
    "suggested_toolkits": [],
    "suggested_mcp": [],
    "suggested_pipelines": [],
    "suggested_agents": [],
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

            # --- ELITEA-1905 gap fill: modal-contents assertions -------------
            # (modal-open itself is already covered by ELITEA-1903's dedicated
            # test — see test_agent_build_with_ai_role_visibility.py)
            assert modal.prompt_input.is_visible(), (
                "Natural-language prompt input should be visible in the Build with AI modal"
            )
            assert modal.generate_button.is_visible(), (
                "Generate button should be visible in the Build with AI modal"
            )
            assert modal.cancel_button.is_visible(), (
                "Cancel button should be visible in the Build with AI modal"
            )
            # -------------------------------------------------------------------

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
    (Toolkit, nested Agent, Skill — ELITEA-1909 @ELITEA-1909, extended for
    Skill by ELITEA-1911 @ELITEA-1911) are attached to the created agent;
    non-selected suggested resources are absent."""

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

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agents/build_with_ai/ELITEA-1911_build-with-ai-selected-suggested-skills-attached-to-created-agent.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_selected_suggested_skill_attached_and_non_selected_absent(
        self, page, agent_api, github_relevant_skills
    ):
        """Selecting one suggested Skill (leaving a second suggested Skill
        unchecked) and clicking "Create Agent" attaches exactly the selected
        Skill to the created agent's SKILLS section; the deliberately-
        unselected Skill is absent. Extends this class's Toolkit/nested-Agent
        coverage (ELITEA-1909) to the Skill suggested-resource type
        (ELITEA-1911) — a genuinely distinct network contract
        (GET+PATCH .../skill/prompt_lib/...) and a distinct accordion
        (agent-skills-section, not agent-toolkits-section)."""
        list_page = AgentsListPage(page)
        modal = GenerateAgentModalPage(page)
        selected_skill = github_relevant_skills["selected"]
        not_selected_skill = github_relevant_skills["not_selected"]

        # Names both fixture skills explicitly so the suggestion engine's
        # relevance match surfaces both as `suggested_skills` candidates —
        # see ELITEA-1911 AFS Test Data (prompt text and fixture
        # descriptions are coupled by design, same pattern as
        # github_relevant_agents/prompt_text above).
        prompt_text = (
            "An agent that manages a GitHub repository by delegating changelog "
            f"writing to the {selected_skill['name']} skill or issue labeling to "
            f"the {not_selected_skill['name']} skill."
        )

        created_agent_id = None
        try:
            # ------------------------------------------------------------------
            # Step 1 — Generate a draft mentioning both fixture Skills; the
            # Suggested Skills section renders both as unchecked cards
            # ------------------------------------------------------------------
            with allure.step("Step 1 — Generate an agent draft mentioning both fixture Skills"):
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

                assert modal.is_resource_section_visible("skill"), (
                    'The "Suggested Skills:" section should be present with both fixture Skills'
                )
                assert modal.get_resource_name_text("skill", selected_skill["id"]) == selected_skill["name"], (
                    "Suggested skill card should be the fixture skill intended for selection"
                )
                assert modal.get_resource_description_text("skill", selected_skill["id"]) == selected_skill["description"], (
                    "Suggested skill card should show the fixture skill's description"
                )
                assert modal.get_resource_name_text("skill", not_selected_skill["id"]) == not_selected_skill["name"], (
                    "Suggested skill card should also include the fixture skill intended to stay unselected"
                )
                assert modal.get_resource_description_text("skill", not_selected_skill["id"]) == not_selected_skill["description"], (
                    "Suggested skill card should show the sibling fixture skill's description too"
                )
                assert not modal.is_resource_checked("skill", selected_skill["id"]), (
                    "Skill suggestion should not be pre-selected"
                )
                assert not modal.is_resource_checked("skill", not_selected_skill["id"]), (
                    "Skill suggestion should not be pre-selected"
                )

            # ------------------------------------------------------------------
            # Step 2 — Select the suggested Skill; deliberately leave the
            # sibling suggested Skill unchecked
            # ------------------------------------------------------------------
            with allure.step("Step 2 — Select the suggested Skill; leave the sibling Skill unchecked"):
                # Start capturing skill-relation traffic before the selection
                # so the post-approve absence check (step 6) below covers the
                # entire flow, not just the click itself.
                skill_requests = modal.capture_requests_matching("/elitea_core/skill/prompt_lib/")

                modal.select_resource("skill", selected_skill["id"])

                assert modal.is_resource_checked("skill", selected_skill["id"]), (
                    f"{selected_skill['name']!r} card should be checked/selected after clicking its checkbox"
                )
                assert not modal.is_resource_checked("skill", not_selected_skill["id"]), (
                    f"{not_selected_skill['name']!r} card should remain unchecked — this test's negative fixture"
                )

            # ------------------------------------------------------------------
            # Step 3 — Click "Create Agent"; verify the base-agent create call
            # plus the selected Skill's GET+PATCH relation pair
            # ------------------------------------------------------------------
            with allure.step('Step 3 — Click "Create Agent"'):
                create_response, skill_get_response, skill_patch_response = (
                    modal.click_approve_and_wait_for_skill_creation()
                )

                assert create_response.status == 201, (
                    f"Expected the base-agent create call to resolve 201, got {create_response.status}"
                )
                created_agent_id = create_response.json()["id"]

                assert str(selected_skill["id"]) in skill_get_response.url, (
                    f"The skill-details GET should target the selected Skill's id, got {skill_get_response.url}"
                )
                assert skill_get_response.status == 200, (
                    f"Expected fetchSkillDetails GET to resolve 200, got {skill_get_response.status}"
                )

                assert str(selected_skill["id"]) in skill_patch_response.url, (
                    f"The skill relation PATCH should target the selected Skill's id, got {skill_patch_response.url}"
                )
                assert skill_patch_response.status == 201, (
                    f"Expected the selected-Skill association PATCH to resolve 201, "
                    f"got {skill_patch_response.status}"
                )
                skill_patch_body = skill_patch_response.json()
                # Live-observed contract (see the ELITEA-1911 AFS amendment
                # committed alongside this change): the response is
                # {"skill_id", "skill_version_id", "skill_name",
                # "version_name"} — NOT {"has_relation": true, ...} as the
                # AFS's Network Behavior section guessed (that field was
                # explicitly flagged there as "not independently
                # re-verified field-by-field"). Asserting the live contract
                # per the reverse-masking guard, not the unverified case text.
                assert skill_patch_body.get("skill_id") == selected_skill["id"], (
                    f"Skill association response should confirm skill_id={selected_skill['id']}, "
                    f"got {skill_patch_body.get('skill_id')!r}"
                )

                page.wait_for_url(f"**/agents/all/{created_agent_id}**")

            # ------------------------------------------------------------------
            # Step 4 (case) — created Agent detail page is displayed
            # ------------------------------------------------------------------
            detail_page = AgentDetailPage(page)
            with allure.step("Step 4 — Verify the created Agent detail page is displayed"):
                detail_page.wait_for_page_load()
                assert f"/agents/all/{created_agent_id}" in page.url, (
                    f"Expected to land on the created agent's detail page, got {page.url}"
                )

            # ------------------------------------------------------------------
            # Step 5 (case) — selected Skill present in the SKILLS section
            # ------------------------------------------------------------------
            with allure.step("Step 5 — Verify the selected Skill is present in the SKILLS section"):
                assert detail_page.is_skill_attached(selected_skill["name"]), (
                    f"Selected skill {selected_skill['name']!r} should appear in the Skills section"
                )
                counter_text = detail_page.get_skills_counter_text()
                assert counter_text.startswith("1/"), (
                    f'Expected the Skills counter to read "1/N skills added.", got {counter_text!r}'
                )

            # ------------------------------------------------------------------
            # Step 6 (case) — non-selected suggested Skill is absent, both by
            # card and by network log (no relation call ever fired for it)
            # ------------------------------------------------------------------
            with allure.step("Step 6 — Verify the non-selected suggested Skill is absent"):
                assert not detail_page.is_skill_attached(not_selected_skill["name"]), (
                    f"Non-selected skill {not_selected_skill['name']!r} should NOT appear in the Skills section"
                )
                not_selected_calls = [
                    r for r in skill_requests if str(not_selected_skill["id"]) in r["url"]
                ]
                assert not not_selected_calls, (
                    f"No GET/PATCH .../skill/prompt_lib/.../{not_selected_skill['id']} call should ever fire "
                    f"for the deliberately-unselected Skill, got: {not_selected_calls}"
                )
        finally:
            if created_agent_id is not None:
                try:
                    agent_api.delete_agent(created_agent_id)
                    logger.info("Deleted created agent %s", created_agent_id)
                except Exception as exc:
                    logger.warning("Failed to delete created agent %s during teardown: %s", created_agent_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agents/build_with_ai/ELITEA-1914_build-with-ai-approve-creates-agent-and-navigates-to-agent-menu.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_approve_with_no_resources_creates_agent_and_appears_in_list(self, page, agent_api):
        """Approving a plain draft — no suggested resources rendered at all —
        creates the agent via the base-create POST only (no toolkit/agent/
        skill relation calls), auto-navigates to the created agent's detail
        page with the draft's content carried over and the Skills counter
        reading zero, and the new agent is visible back on the Agents list.
        Extends this class's create+navigate coverage (ELITEA-1909/1911) to
        the ungated, no-resource-selection path (ELITEA-1914) — a distinct
        network contract that click_approve_and_wait_for_creation()/
        click_approve_and_wait_for_skill_creation() would hang on, since
        neither association call ever fires for a plain draft (see
        GenerateAgentModalPage.click_approve_and_wait_for_agent_created())."""
        list_page = AgentsListPage(page)
        modal = GenerateAgentModalPage(page)

        created_agent_id = None
        try:
            # ------------------------------------------------------------------
            # Step 1 (case) — Generate a draft from a plain, non-resource-
            # implying prompt; review form populates with no "Suggested
            # {Category}:" sections rendered at all
            # ------------------------------------------------------------------
            with allure.step("Step 1 — Generate a plain draft implying no resources"):
                list_page.navigate_to_create()
                modal.open_modal()
                modal.fill_prompt(NO_RESOURCES_PROMPT_TEXT)

                assert modal.get_prompt_value() == NO_RESOURCES_PROMPT_TEXT, (
                    "Prompt textarea should contain exactly the entered text"
                )

                response = modal.click_generate_and_wait_for_response(
                    timeout=LIVE_GENERATE_RESPONSE_TIMEOUT
                )
                assert response.status == 200, (
                    f"Expected the generate-draft request to succeed, got {response.status}"
                )
                modal.wait_for_review_form()

                for entity_type in ("toolkit", "mcp", "pipeline", "agent", "skill"):
                    assert not modal.is_resource_section_visible(entity_type), (
                        f'No "Suggested {entity_type.capitalize()}:" section should render for a '
                        "plain, non-resource-implying prompt"
                    )

                draft_name = modal.get_review_name()

            # ------------------------------------------------------------------
            # Step 2 (case) — Click "Create Agent"; only the base-create POST
            # fires (no toolkit/agent/skill relation calls)
            # ------------------------------------------------------------------
            with allure.step('Step 2 — Click "Create Agent"'):
                create_response = modal.click_approve_and_wait_for_agent_created()

                assert create_response.status == 201, (
                    f"Expected the base-agent create call to resolve 201, got {create_response.status}"
                )
                created_agent_id = create_response.json()["id"]

            # ------------------------------------------------------------------
            # Steps 3-4 (case) — agent is created without errors, and the
            # user is auto-navigated to the created Agent's detail page with
            # the draft's content carried over and zero resources attached
            # ------------------------------------------------------------------
            detail_page = AgentDetailPage(page)
            with allure.step("Step 3-4 — Verify agent creation and navigation to the Agent detail page"):
                page.wait_for_url(f"**/agents/all/{created_agent_id}**")
                detail_page.wait_for_page_load()

                assert f"/agents/all/{created_agent_id}" in page.url, (
                    f"Expected to land on the created agent's detail page, got {page.url}"
                )
                assert detail_page.get_name() == draft_name, (
                    "Detail page Name field should carry over the generated draft's name verbatim, "
                    f"expected {draft_name!r}, got {detail_page.get_name()!r}"
                )
                counter_text = detail_page.get_skills_counter_text()
                assert counter_text.startswith("0/"), (
                    "Skills counter should read '0/N skills added.' for a plain draft with no "
                    f"resources attached, got {counter_text!r}"
                )

            # ------------------------------------------------------------------
            # Step 5 (case) — Navigate to the Agents list; the new Agent
            # appears there
            # ------------------------------------------------------------------
            with allure.step("Step 5 — Verify the new Agent appears in the Agents list"):
                list_page.navigate()
                assert list_page.agent_exists_in_list(draft_name), (
                    f"Newly created agent {draft_name!r} should be visible in the Agents list"
                )
        finally:
            if created_agent_id is not None:
                try:
                    agent_api.delete_agent(created_agent_id)
                    logger.info("Deleted created agent %s", created_agent_id)
                except Exception as exc:
                    logger.warning("Failed to delete created agent %s during teardown: %s", created_agent_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agents/build_with_ai/ELITEA-1908_build-with-ai-suggested-resources-require-explicit-selection.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_zero_selection_across_categories_attaches_nothing(self, page, agent_api):
        """Generating a draft with suggested resources rendered across
        multiple categories simultaneously (Toolkit, MCP, Pipeline, Agent)
        and clicking "Create Agent" with literally zero boxes checked
        creates the agent via the base-create POST alone — no toolkit/
        agent-relation/pipeline-relation/mcp-relation call ever fires, for
        any category — and the created agent's Tools section and Skills
        counter both confirm zero attachments across every category
        (ELITEA-1908). Distinct from this class's per-item selective
        coverage (ELITEA-1909/1911, which always select at least one item)
        and from ELITEA-1914's ungated no-resources-rendered-at-all path —
        this is the first test to assert a COMBINED all-category zero with
        resources genuinely on offer."""
        list_page = AgentsListPage(page)
        modal = GenerateAgentModalPage(page)

        created_agent_id = None
        try:
            # ------------------------------------------------------------------
            # Step 1 (case) — Generate a draft with Toolkit/MCP/Pipeline/Agent
            # suggestions all rendered (mocked — see AFS Preconditions:
            # project 400 cannot reliably reproduce multi-category live
            # suggestions, same gap ELITEA-1906/1907/1915 already resolve
            # this way)
            # ------------------------------------------------------------------
            with allure.step("Step 1 — Generate a draft with suggested Toolkits/MCP/Pipelines/Agents rendered"):
                list_page.navigate_to_create()
                modal.open_modal()
                modal.fill_prompt(SUGGESTED_RESOURCES_PROMPT_TEXT)

                assert modal.get_prompt_value() == SUGGESTED_RESOURCES_PROMPT_TEXT, (
                    "Prompt textarea should contain exactly the entered text"
                )

                modal.mock_generate_success(SUGGESTED_RESOURCES_DRAFT_PAYLOAD)
                response = modal.click_generate_and_wait_for_response(timeout=GENERATE_RESPONSE_TIMEOUT)
                assert response.status == 200, (
                    f"Expected the mocked generate-draft request to succeed, got {response.status}"
                )
                modal.wait_for_review_form(timeout=REVIEW_FORM_TIMEOUT)

                assert modal.is_resource_section_visible("toolkit"), (
                    'The "Suggested Toolkits:" section should be present (mocked payload)'
                )
                assert modal.is_resource_section_visible("mcp"), (
                    'The "Suggested MCP:" section should be present (mocked payload)'
                )
                assert modal.is_resource_section_visible("pipeline"), (
                    'The "Suggested Pipelines:" section should be present (mocked payload)'
                )
                assert modal.is_resource_section_visible("agent"), (
                    'The "Suggested Agents:" section should be present (mocked payload)'
                )

            # ------------------------------------------------------------------
            # Step 2 (case) — do NOT select any suggested resource; explicit
            # re-check immediately before approve, across all four rendered
            # categories (the gap ELITEA-1907 only checks at generation time)
            # ------------------------------------------------------------------
            with allure.step("Step 2 — Verify no suggested resource is selected, across every rendered category"):
                assert not modal.is_resource_checked("toolkit", 101), (
                    "Toolkit suggestion should remain unchecked — this test never selects it"
                )
                assert not modal.is_resource_checked("mcp", 3), (
                    "MCP suggestion should remain unchecked — this test never selects it"
                )
                assert not modal.is_resource_checked("pipeline", 202), (
                    "Pipeline suggestion should remain unchecked — this test never selects it"
                )
                assert not modal.is_resource_checked("agent", 303), (
                    "Agent suggestion should remain unchecked — this test never selects it"
                )

            # ------------------------------------------------------------------
            # Step 3 (case) — Click "Approve"/"Create Agent" with zero
            # selections; verify no relation call fires for ANY category —
            # GenerateAgentModal.jsx's associateToolkits/associateApplications/
            # associateSkills each guard on `if (!versionId || !items.length)
            # return;` (lines ~121/140/179), so an empty selection Set means
            # none of these callbacks ever call the underlying association
            # API, regardless of how many resources were rendered
            # ------------------------------------------------------------------
            with allure.step('Step 3 — Click "Create Agent"; verify no relation call fires for any category'):
                toolkit_requests = modal.capture_requests_matching("/elitea_core/tool/prompt_lib/")
                relation_requests = modal.capture_requests_matching("/elitea_core/application_relation/prompt_lib/")
                skill_requests = modal.capture_requests_matching("/elitea_core/skill/prompt_lib/")

                create_response = modal.click_approve_and_wait_for_agent_created()

                assert create_response.status == 201, (
                    f"Expected the base-agent create call to resolve 201, got {create_response.status}"
                )
                created_agent_id = create_response.json()["id"]

                assert not toolkit_requests, (
                    "No .../tool/prompt_lib/... call should fire for a zero-selection approve, "
                    f"got: {list(toolkit_requests)}"
                )
                assert not relation_requests, (
                    "No .../application_relation/prompt_lib/... call should fire for a zero-selection "
                    f"approve (covers both nested Agent and Pipeline suggestions), got: {list(relation_requests)}"
                )
                assert not skill_requests, (
                    "No .../skill/prompt_lib/... call should fire for a zero-selection approve, "
                    f"got: {list(skill_requests)}"
                )

            # ------------------------------------------------------------------
            # Step 4 (case) — Open the created Agent
            # ------------------------------------------------------------------
            detail_page = AgentDetailPage(page)
            with allure.step("Step 4 — Verify the created Agent detail page is displayed"):
                page.wait_for_url(f"**/agents/all/{created_agent_id}**")
                detail_page.wait_for_page_load()
                assert f"/agents/all/{created_agent_id}" in page.url, (
                    f"Expected to land on the created agent's detail page, got {page.url}"
                )

            # ------------------------------------------------------------------
            # Step 5 (case) — Verify no Toolkits/Agents/Pipelines/MCPs
            # attached, across every category (Toolkit/MCP/Agent share the
            # same ToolCard.jsx/agent-toolkit-card component; Pipeline
            # attaches via the same application_relation mechanism as nested
            # Agent — see AFS Concrete Handles / Axis 2 flag)
            # ------------------------------------------------------------------
            with allure.step("Step 5 — Verify no Toolkits, Agents, Pipelines, or MCPs were attached"):
                assert not detail_page.is_toolkit_attached("GitHub Toolkit"), (
                    "Suggested Toolkit should NOT appear in the Tools section — it was never selected"
                )
                assert not detail_page.is_toolkit_attached("Remote Github"), (
                    "Suggested MCP should NOT appear in the Tools section — it was never selected"
                )
                assert not detail_page.is_toolkit_attached("Jira Triage Agent"), (
                    "Suggested nested Agent should NOT appear in the Tools section — it was never selected"
                )
                assert not detail_page.is_toolkit_attached("Jira Update Pipeline"), (
                    "Suggested Pipeline should NOT appear in the Tools section — it was never selected"
                )
                counter_text = detail_page.get_skills_counter_text()
                assert counter_text.startswith("0/"), (
                    "Skills counter should read '0/N skills added.' — the mock payload's "
                    f"suggested_skills is empty and none was selected, got {counter_text!r}"
                )
        finally:
            if created_agent_id is not None:
                try:
                    agent_api.delete_agent(created_agent_id)
                    logger.info("Deleted created agent %s", created_agent_id)
                except Exception as exc:
                    logger.warning("Failed to delete created agent %s during teardown: %s", created_agent_id, exc)


class TestAgentBuildWithAIDraftFieldPopulation:
    """Build with AI (P2): the generated draft's Name, Description,
    Instructions, Welcome Message, and Conversation-starter fields are all
    pre-populated with the generated values and remain editable before agent
    creation (ELITEA-1906)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agents/build_with_ai/ELITEA-1906_build-with-ai-agent-draft-generated-from-natural-language-description.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_draft_fields_prepopulated_and_editable(self, page):
        """Submitting a natural-language description populates all 5 review-
        form fields (Name, Description, Instructions, Welcome Message, and
        the Chat-starter inputs) with the generated draft's values, and every
        one of those fields remains editable before "Create Agent" is
        clicked."""
        list_page = AgentsListPage(page)
        modal = GenerateAgentModalPage(page)
        draft = FIELD_POPULATION_DRAFT_PAYLOAD

        # ------------------------------------------------------------------
        # Step 1 — Open the GenerateAgentModal
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Open the GenerateAgentModal"):
            list_page.navigate_to_create()
            modal.open_modal()

            assert modal.modal.is_visible(), "Build with AI modal should be visible"
            assert modal.prompt_input.is_visible(), "Prompt input should be visible once the modal opens"

        # ------------------------------------------------------------------
        # Step 2 — Enter the natural-language description
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Enter the natural-language description"):
            modal.fill_prompt(FIELD_POPULATION_PROMPT_TEXT)

            assert modal.get_prompt_value() == FIELD_POPULATION_PROMPT_TEXT, (
                "Prompt textarea should contain exactly the entered text"
            )
            assert modal.is_generate_enabled(), (
                "Generate button should become enabled once the prompt is non-empty"
            )

        # ------------------------------------------------------------------
        # Step 3 — Click "Generate Draft"; loading state shown while the
        # (artificially delayed) mocked request is in flight
        # ------------------------------------------------------------------
        with allure.step('Step 3 — Click "Generate Draft"; verify the loading state is shown'):
            modal.mock_generate_success(draft)

            with modal.expect_generate_response(timeout=GENERATE_RESPONSE_TIMEOUT) as response_info:
                modal.generate_button.click()
                modal.wait_for_loading_visible(timeout=LOADING_STATE_TIMEOUT)

            response = response_info.value
            assert response.status == 200, (
                f"Expected the mocked generate-draft request to succeed, got {response.status}"
            )

        # ------------------------------------------------------------------
        # Step 4 — Wait for generation to complete; modal transitions to the
        # review/edit form
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Wait for generation to complete and the review form to render"):
            modal.wait_for_review_form(timeout=REVIEW_FORM_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 5 — Review form pre-populated with Name
        # ------------------------------------------------------------------
        with allure.step("Step 5 — Verify the review-form Name field is pre-populated"):
            assert modal.get_review_name() == draft["name"], (
                "Review-form Name field should be pre-populated with the generated draft's name"
            )

        # ------------------------------------------------------------------
        # Step 6 — Review form pre-populated with Description
        # ------------------------------------------------------------------
        with allure.step("Step 6 — Verify the review-form Description field is pre-populated"):
            assert modal.get_review_description() == draft["description"], (
                "Review-form Description field should be pre-populated with the generated draft's description"
            )

        # ------------------------------------------------------------------
        # Step 7 — Review form pre-populated with Instructions
        # ------------------------------------------------------------------
        with allure.step("Step 7 — Verify the review-form Instructions field is pre-populated"):
            assert modal.get_review_instructions() == draft["instructions"], (
                "Review-form Instructions field should be pre-populated with the generated draft's instructions"
            )

        # ------------------------------------------------------------------
        # Step 8 — Review form pre-populated with Welcome Message
        # ------------------------------------------------------------------
        with allure.step("Step 8 — Verify the review-form Welcome Message field is pre-populated"):
            assert modal.get_review_welcome_message() == draft["welcome_message"], (
                "Review-form Welcome Message field should be pre-populated with the generated draft's welcome message"
            )

        # ------------------------------------------------------------------
        # Step 9 — Review form pre-populated with Conversation starters
        # ------------------------------------------------------------------
        with allure.step("Step 9 — Verify the review-form Chat starters are pre-populated"):
            assert modal.review_starters_header.is_visible(), (
                'The "Chat starters:" section header should be visible when conversation_starters is non-empty'
            )
            for i, starter_text in enumerate(draft["conversation_starters"]):
                assert modal.get_review_starter_value(i) == starter_text, (
                    f"Chat-starter input #{i} should be pre-populated with the generated draft's "
                    f"conversation_starters[{i}]"
                )

        # ------------------------------------------------------------------
        # Step 10 — All fields editable before approval
        # ------------------------------------------------------------------
        with allure.step("Step 10 — Verify all 5 fields are editable"):
            # Native-element testid wiring (inputProps={'data-testid': ...}) makes
            # a plain click()+fill() React-correct here — the same pattern
            # fill_prompt() already relies on for the prompt textarea; no
            # press_sequentially() workaround needed (see AFS Automation Hints).
            edited_name = f"{draft['name']} [edited]"
            modal.review_name_input.click()
            modal.review_name_input.fill(edited_name)
            assert modal.get_review_name() == edited_name, (
                "Name field should reflect the newly typed text — proves it is genuinely editable"
            )

            edited_description = f"{draft['description']} [edited]"
            modal.review_description_input.click()
            modal.review_description_input.fill(edited_description)
            assert modal.get_review_description() == edited_description, (
                "Description field should reflect the newly typed text — proves it is genuinely editable"
            )

            edited_instructions = f"{draft['instructions']} [edited]"
            modal.review_instructions_input.click()
            modal.review_instructions_input.fill(edited_instructions)
            assert modal.get_review_instructions() == edited_instructions, (
                "Instructions field should reflect the newly typed text — proves it is genuinely editable"
            )

            edited_welcome_message = f"{draft['welcome_message']} [edited]"
            modal.review_welcome_message_input.click()
            modal.review_welcome_message_input.fill(edited_welcome_message)
            assert modal.get_review_welcome_message() == edited_welcome_message, (
                "Welcome Message field should reflect the newly typed text — proves it is genuinely editable"
            )

            edited_starter = f"{draft['conversation_starters'][0]} [edited]"
            first_starter = modal.get_review_starter(0)
            first_starter.click()
            first_starter.fill(edited_starter)
            assert modal.get_review_starter_value(0) == edited_starter, (
                "First Chat-starter input should reflect the newly typed text — proves it is genuinely editable"
            )
