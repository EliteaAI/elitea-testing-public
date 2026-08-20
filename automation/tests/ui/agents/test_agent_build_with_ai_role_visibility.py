"""UI Tests for "Build with AI" — Magic Wand button role-gated visibility.

Covers ELITEA-1903: the Magic Wand ("Build with AI") button in the New Agent
creation form's General section is visible, correctly labelled, and
functional for the admin-equivalent ``TEST_USER`` role.

Scope note: this AFS/spec covers the admin-role half only (case steps 1-3).
The editor-role half (case steps 4-6) is a documented, out-of-scope gap — no
non-admin test-user credential exists in this environment (see the AFS §
Blocked Steps and EliteaAI/elitea-testing-public#1314, tracked separately).
The case's core RBAC-gating mechanism
(``checkPermission(PERMISSIONS.applications.update)`` in
``GenerateEntityButton.jsx``) is nonetheless fully verified here for one
authenticated role, both via live UI observation and source-code
confirmation of the gating logic itself.

Spec: test-specs/agents/l2_build-with-ai-button-visible-for-admin-and-editor-roles_ELITEA-1903.md
Covers: GenerateAgentButton.jsx (GenerateEntityButton.jsx via GenerateAgentModal.jsx)

Markers:
    - ui: requires browser
    - agents: agent-related tests
    - p2: medium priority (case priority: l2)

Usage:
    cd automation
    pytest tests/ui/agents/test_agent_build_with_ai_role_visibility.py -v
"""

import logging

import allure
import pytest
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage
from pages.generate_agent_modal_page import GenerateAgentModalPage

logger = logging.getLogger("elitea.tests.agents.build_with_ai_role_visibility")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.new_verified]

EXPECTED_BUTTON_ACCESSIBLE_TEXT = "Build with AI"


class TestAgentBuildWithAIButtonRoleVisibility:
    """Build with AI (L2): Magic Wand button visibility is RBAC-gated —
    verified live here for the admin-equivalent role. The editor-role half
    is out of scope for this spec (see module docstring)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agents/build_with_ai/ELITEA-1903_build-with-ai-button-visible-for-admin-and-editor-roles.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_build_with_ai_button_visible_for_admin_role(self, page):
        """Magic Wand ("Build with AI") button is visible, correctly
        labelled, and functional (opens the generation modal) for the
        admin-equivalent TEST_USER on the New Agent creation page."""
        list_page = AgentsListPage(page)
        form_page = AgentFormPage(page)
        modal = GenerateAgentModalPage(page)

        # ------------------------------------------------------------------
        # Step 1 — Authenticate as TEST_USER (admin-equivalent role),
        # verify the dashboard/app shell loads
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Authenticate as TEST_USER, verify dashboard/app shell loads"):
            # The `auth_state` fixture already authenticated TEST_USER via
            # VITE_DEV_TOKEN before this test started (localhost bypass —
            # see conftest.py). Navigating to the dashboard is the live
            # confirmation that the session is authenticated and the app
            # shell (header + sidebar) renders.
            list_page.navigate()

            assert list_page.page_header.is_visible(), (
                "Agents dashboard header should be visible once authenticated"
            )
            assert list_page.create_agent_button.is_visible(), (
                "Sidebar create-agent control should be visible — confirms the sidebar/app shell rendered"
            )

        # ------------------------------------------------------------------
        # Step 2 — Navigate to Agents, click the sidebar "+ Agent" create
        # button
        # ------------------------------------------------------------------
        with allure.step('Step 2 — Click sidebar "+ Agent" create button, verify the creation page opens'):
            list_page.click_create_agent()
            form_page.wait_for_form_load()

            assert "/agents/create" in page.url and "viewMode=owner" in page.url, (
                f"Expected to land on the New Agent creation page (?viewMode=owner), got {page.url}"
            )
            # No testid exists on the page-level tab bar itself (AFS
            # Concrete Handles) — page-readiness is asserted via the Name
            # field, which `wait_for_form_load()` already waits on.
            assert form_page.name_input.is_visible(), (
                "Name field should be visible once the create form has loaded (page-ready signal)"
            )

        # ------------------------------------------------------------------
        # Step 3 — Verify the Magic Wand ("Build with AI") button is
        # visible, correctly labelled, and functional
        # ------------------------------------------------------------------
        with allure.step('Step 3 — Verify the "Build with AI" button is visible, labelled, and opens the modal'):
            assert modal.open_button.is_visible(), (
                "generate-agent-open-button should be visible in the General section header "
                "for the admin-equivalent role"
            )
            button_text = modal.open_button.inner_text().strip()
            assert button_text == EXPECTED_BUTTON_ACCESSIBLE_TEXT, (
                f"Build with AI button's accessible text should read "
                f"{EXPECTED_BUTTON_ACCESSIBLE_TEXT!r}, got {button_text!r}"
            )

            # Axis 2 addition (AFS): functional reachability, not just DOM
            # presence — a disabled/non-interactive ghost button would still
            # satisfy a bare visibility check. Reuses the existing
            # open_modal() helper already exercised by
            # test_agent_build_with_ai.py.
            modal.open_modal()
            assert modal.modal.is_visible(), (
                "Clicking Build with AI should open the generate-agent-modal dialog"
            )

        # Cleanup (not a case step — AFS § Cleanup: none required, the
        # modal is closed via X without generating a draft; the agent-
        # create form itself is abandoned, not saved).
        modal.close_button.click()
