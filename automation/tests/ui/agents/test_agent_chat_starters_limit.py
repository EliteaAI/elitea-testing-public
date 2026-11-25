"""UI test for the admin chat-starters limit on the agent create form (ELITEA-4863).

Reads the admin limit M (never changes it), then adds starters on the create
form and verifies the ``n/M starters added.`` counter, the disabled add button
at M, the at-limit tooltip, and that Discard creates nothing.

Spec: test-specs/agents/l1_chat-starters-limit-counter-and-disabled-add_ELITEA-4863.md
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

AGENT_NAME = "Regression Chat Starters Limit"
AGENT_DESCRIPTION = "Regression agent for the chat starter limit"
AT_LIMIT_TOOLTIP = "You have reached the limit of chat starters"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
    "agents/configurable-chat-starters-limit/"
    "ELITEA-4863_add-chat-starters-up-to-the-admin-limit-and-verify-the-counter.md",
    "onetest-ai Test Case link",
)
@pytest.mark.tms("ELITEA-4863")
@pytest.mark.p1
@pytest.mark.regression
def test_chat_starters_limit_counter_and_disabled_add(page):
    """Counter tracks n/M up to the admin limit, add is disabled at M, Discard creates nothing."""
    list_page = AgentsListPage(page)
    form = AgentFormPage(page)

    with allure.step("Step 1 — Read the admin limit M (1..10) from the guardrails API"):
        list_page.navigate()
        limit = form.get_admin_conversation_starters_limit()
        assert 1 <= limit <= 10, f"Admin limit must be a whole number 1..10, got {limit}"

    with allure.step("Step 2 — Platform settings deliver the same limit to the editor"):
        assert form.get_editor_conversation_starters_limit() == limit

    with allure.step("Step 3 — Open the new agent form from the Agents list"):
        list_page.open_new_agent_form_via_add_menu()
        form.wait_for_form_load(timeout=15000)
        assert "/agents/create" in page.url

    with allure.step("Step 4 — Fill Name/Description; counter reads 0/M and add is enabled"):
        form.name_input.fill(AGENT_NAME)
        form.description_input.fill(AGENT_DESCRIPTION)
        expect(form.conversation_starters_limit_counter).to_have_text(f"0/{limit} starters added.")
        expect(form.conversation_starter_add_button).to_be_enabled()

    with allure.step("Steps 5-7 — Add starters 1..M; counter n/M after each, add disabled only at M"):
        for n in range(1, limit + 1):
            form.add_conversation_starter_and_wait_count(f"Regression starter {n}", expected_count=n)
            expect(form.conversation_starters_limit_counter).to_have_text(f"{n}/{limit} starters added.")
            if n < limit:
                expect(form.conversation_starter_add_button).to_be_enabled()
        expect(form.conversation_starter_add_button).to_be_disabled()

    with allure.step("Step 8 — Hovering the disabled add button shows the at-limit tooltip"):
        form.hover_add_button_at_limit()
        expect(form.at_limit_tooltip).to_have_text(AT_LIMIT_TOOLTIP)

    with allure.step("Step 9 — The disabled add button adds no field; counter stays M/M"):
        expect(form.conversation_starter_add_button).to_be_disabled()
        expect(form.conversation_starter_inputs).to_have_count(limit)
        expect(form.conversation_starters_limit_counter).to_have_text(f"{limit}/{limit} starters added.")

    with allure.step("Step 10 — Cancel + Discard leaves the form and creates no agent"):
        form.cancel_create_and_confirm_discard()
        expect(page).to_have_url(re.compile(r"/agents/all"), timeout=15000)
        list_page.wait_for_page_load()
        list_page.search_and_wait_for_results(AGENT_NAME)
        assert AGENT_NAME not in list_page.get_agent_card_names(timeout=5000), (
            f"Agent '{AGENT_NAME}' must not exist after Discard"
        )
