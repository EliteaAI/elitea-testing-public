"""UI Test for Agent listing "+Create" button navigation (ELITEA-1870).

Verifies that clicking the create-agent control in the Agents dashboard
sidebar navigates to the Create Agent page with an empty form (Name,
Description, Instructions all blank) and the Save button disabled by
default.

Spec: test-specs/agents/l1_agent-listing-create-button-navigation_ELITEA-1870.md

This case is a genuine, previously-unexercised gap: the two existing
create-agent tests (``test_create_agent_via_ui``,
``test_create_agent_required_fields_validation`` in
``test_agent_management.py``) both reach the create form via
``AgentsListPage.navigate_to_create()`` — a direct ``page.goto()`` that
bypasses the button click entirely. This test exercises the actual
button-click navigation path instead.

Read-only / no test data: the case never submits the form, so no agent is
created and nothing needs cleanup.

Markers:
    - ui: requires browser
    - agents: agent-related tests
    - p0: critical priority (frontmatter priority is "critical"/l1 — matches
      pytest.ini's p0 marker, the project's convention for
      must-pass-for-deploy coverage; same mapping used by ELITEA-1869's
      ``test_agent_back_navigation.py``)
"""

import allure
import pytest

from pages.agents_list_page import AgentsListPage
from pages.agent_form_page import AgentFormPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

NAVIGATION_TIMEOUT = 15000


@pytest.mark.p0
@pytest.mark.regression
def test_create_button_navigates_to_create_agent_page(page):
    """Sidebar create-agent button navigates to an empty Create Agent form
    with Save disabled by default (ELITEA-1870).

    Read-only: no agent is created, edited, or deleted.
    """
    list_page = AgentsListPage(page)
    form_page = AgentFormPage(page)

    console_messages = []
    page.on(
        "console",
        lambda msg: console_messages.append(msg) if msg.type == "error" else None,
    )

    with allure.step("Step 1 — Navigate to the Agents dashboard"):
        list_page.navigate()
        list_page.verify_dashboard_header_visible()

    with allure.step(
        "Step 2 — Click the create-agent control in the sidebar and verify "
        "no new POST/PUT request fires on the click itself (pure "
        "client-side route change)"
    ):
        mutating_requests = list_page.capture_requests_matching("/api/v2", method="POST")
        mutating_requests += list_page.capture_requests_matching("/api/v2", method="PUT")
        list_page.click_create_agent(timeout=NAVIGATION_TIMEOUT)
        assert not mutating_requests, (
            "Clicking the create-agent button should be a pure client-side "
            f"route change with no POST/PUT calls, got: {mutating_requests}"
        )

    with allure.step(
        "Step 3 — Verify the browser navigates to /agents/create (or equivalent)"
    ):
        assert "/agents/create" in page.url, (
            f"Expected to land on the create-agent route after clicking the "
            f"create button, got: {page.url}"
        )

    with allure.step(
        "Step 4 — Verify the Create Agent form is shown with empty Name, "
        "Description, and Instructions fields"
    ):
        form_page.wait_for_form_load(timeout=NAVIGATION_TIMEOUT)
        assert form_page.name_input.input_value() == "", (
            "Name field should be empty on a fresh Create Agent form"
        )
        assert form_page.description_input.input_value() == "", (
            "Description field should be empty on a fresh Create Agent form"
        )
        assert form_page.instructions_input.input_value() == "", (
            "Instructions field should be empty on a fresh Create Agent form"
        )

    with allure.step("Step 5 — Verify the Save button is disabled by default"):
        assert not form_page.is_save_enabled(), (
            "Save button should be disabled by default on a fresh Create "
            "Agent form"
        )

    with allure.step(
        "Side-channel check — no console errors across the navigate → "
        "click → form-load flow"
    ):
        assert not console_messages, (
            "Unexpected console errors during create-button navigation: "
            f"{[m.text for m in console_messages]}"
        )
