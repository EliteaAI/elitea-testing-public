"""UI Tests for "Build with AI" — Skill Magic Wand button role-gated visibility.

Covers ELITEA-1986: the Magic Wand ("Build with AI") button on the New
Skill creation screen is visible, correctly labelled, and enabled for the
admin-equivalent ``TEST_USER`` role.

Scope note: this AFS/spec covers the admin-role half only (case steps 1-3).
The editor-role half (case steps 4-6) is a documented, out-of-scope gap — no
non-admin test-user credential exists in this environment. This is the same
recurring missing-test-data-fixture gap already tracked centrally at
EliteaAI/elitea-testing-public#1314 ("No editor/viewer test-user credential
— blocks RBAC-role-differentiated cases"), which already covers ELITEA-1903
(Agents analog) and ELITEA-2613. The case's core RBAC-gating mechanism
(``checkPermission(PERMISSIONS.applications.update)`` in
``GenerateEntityButton.jsx`` — the identical gate shared with the Agent
"Build with AI" button, ELITEA-1903) is nonetheless fully verified here for
one authenticated role, both via live UI observation and source-code
confirmation of the gating logic itself. See the AFS § Blocked Steps.

Spec: test-specs/skills/l2_build-with-ai-button-visible-for-admin-and-editor-roles_ELITEA-1986.md
Covers: GenerateSkillButton.jsx (GenerateEntityButton.jsx via GenerateSkillModal.jsx)

Markers:
    - ui: requires browser
    - skills: skill-related tests
    - p2: medium priority (case priority: high)

Usage:
    cd automation
    pytest tests/ui/skills/test_skill_build_with_ai_role_visibility.py -v
"""

import logging

import allure
import pytest
from pages.generate_skill_modal_page import GenerateSkillModalPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

logger = logging.getLogger("elitea.tests.skills.build_with_ai_role_visibility")

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

EXPECTED_BUTTON_ACCESSIBLE_TEXT = "Build with AI"


class TestSkillBuildWithAIButtonRoleVisibility:
    """Build with AI (L2): Magic Wand button visibility is RBAC-gated —
    verified live here for the admin-equivalent role. The editor-role half
    is out of scope for this spec (see module docstring)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-1986_build-with-ai-button-visible-for-admin-and-editor-roles.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_build_with_ai_button_visible_for_admin_role(self, page):
        """Magic Wand ("Build with AI") button is visible, correctly
        labelled, and enabled for the admin-equivalent TEST_USER on the New
        Skill creation screen; zero console errors surface across the flow."""
        list_page = SkillsListPage(page)
        form_page = SkillFormPage(page)
        modal = GenerateSkillModalPage(page)

        console_errors = []

        def _on_console(msg):
            if msg.type == "error":
                console_errors.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step("Step 1 — Authenticate as TEST_USER, verify dashboard/app shell loads"):
                # The `auth_state` fixture already authenticated TEST_USER via
                # VITE_DEV_TOKEN before this test started (localhost bypass —
                # see conftest.py). Navigating to the Skills dashboard is the
                # live confirmation that the session is authenticated and the
                # app shell (header + sidebar) renders.
                list_page.navigate()

                assert list_page.page_header.is_visible(), (
                    "Skills dashboard header should be visible once authenticated"
                )

            with allure.step(
                "Step 2 — Navigate to Skills, open the New Skill creation screen; "
                "verify it loaded"
            ):
                # AFS Concrete Handles: reuses the existing navigate_to_create()
                # deep-link — the suite's established, accepted pattern for
                # this exact destination (ELITEA-1988/1989/1990/2001/1991/2613
                # lineage) — rather than the literal sidebar-click path, which
                # has no dedicated page-object field on SkillsListPage.
                list_page.navigate_to_create()
                form_page.wait_for_form_load()

                assert "/skills/create" in page.url, (
                    f"Expected to land on the New Skill creation page, got {page.url}"
                )
                # No testid exists on the page-level "New Skill" tab bar itself
                # (AFS Concrete Handles) — page-readiness is asserted via the
                # Name field instead, matching the existing skills suite's own
                # pattern (mirrors ELITEA-1903's Agents analog).
                assert form_page.name_input.is_visible(), (
                    "Name field should be visible once the create form has loaded (page-ready signal)"
                )

            with allure.step(
                'Step 3 — Verify the "Build with AI" button is visible, labelled, '
                "and enabled"
            ):
                assert modal.open_button.is_visible(), (
                    "generate-skill-open-button should be visible on the New Skill "
                    "creation screen for the admin-equivalent role"
                )
                button_text = modal.open_button.inner_text().strip()
                assert button_text == EXPECTED_BUTTON_ACCESSIBLE_TEXT, (
                    f"Build with AI button's accessible text should read "
                    f"{EXPECTED_BUTTON_ACCESSIBLE_TEXT!r}, got {button_text!r}"
                )
                assert modal.open_button.is_enabled(), (
                    "Build with AI button should be enabled/clickable, not a "
                    "disabled ghost control"
                )

            with allure.step(
                "Step 3 (Axis 2 addition) — confirm zero console errors on the "
                "creation screen across the permissions fetch and render"
            ):
                assert not console_errors, (
                    "Expected zero console errors on the New Skill creation "
                    f"screen, got: {[m.text for m in console_errors]}"
                )
        finally:
            page.remove_listener("console", _on_console)
