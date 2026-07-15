"""Save As Version creates a named version visible in the version dropdown
(ELITEA-1888).

Edits an existing agent's Instructions, saves the change as a new named
version via "Save As Version", and verifies the new version is visible
(and active) in the VERSION dropdown alongside "base".

Test-data strategy (per AFS — see below): agent creation via the default
UI/API create flow is currently broken by an open, unrelated defect
(EliteaAI/elitea-testing-public#524 — `temperature`/`reasoning_effort`
conflict), so this test does NOT use the `agent_id` fixture (which calls
`AgentAPI.create_agent()`). Instead it reuses an existing disposable
"debris" agent already present in the project (one of several duplicate
agents left over from ELITEA-1735 runs, named `elitea-1735-skills-agent`)
and deletes the WHOLE agent at teardown via `delete_agent_via_menu()`. A
long-lived shared fixture agent (e.g. id 3 "Test Agent") is deliberately
NOT reused — this case's Step 3 permanently adds a new version to whatever
agent it targets, and there is no "delete version" UI/API, so a shared
fixture would accumulate versions across every automated run.

Spec: test-specs/agents/lcritical_save-as-version-creates-named-version-visible-in-dropdown_ELITEA-1888.md
"""

import pytest
import allure

from pages.agent_detail_page import AgentDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000

# Name pattern for the disposable debris agents left over from ELITEA-1735
# runs — reused here to avoid the broken create-agent flow (see module
# docstring / AFS Test Data).
DEBRIS_AGENT_NAME = "elitea-1735-skills-agent"

VERSION_NAME = "v2-test"
INSTRUCTION_APPEND = " Additionally."


class TestAgentSaveAsVersion:
    """Save As Version creates a named version visible in version dropdown (ELITEA-1888, lcritical/p0)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1888_save-as-version-creates-named-version-visible-in-dropdown.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p0
    @pytest.mark.regression
    def test_save_as_version_creates_named_version_visible_in_dropdown(self, page, agent_api):
        """Editing Instructions and clicking Save As Version creates a named
        version that appears (and is active) in the VERSION dropdown."""
        with allure.step("Precondition — reuse an existing disposable agent in its 'base' version"):
            agents = agent_api.list_agents().get("rows", [])
            debris_agents = [a for a in agents if a.get("name") == DEBRIS_AGENT_NAME]
            assert debris_agents, (
                f"Expected at least one existing disposable agent named "
                f"{DEBRIS_AGENT_NAME!r} to reuse (agent creation is blocked by "
                f"issue #524 — see module docstring); none found in the project"
            )
            agent_id = debris_agents[0]["id"]

        detail_page = None
        try:
            with allure.step("Step 1 — Navigate to agent detail page in 'base' version"):
                detail_page = AgentDetailPage(page)
                detail_page.navigate(agent_id)
                assert detail_page.get_version_selector_value() == "base", (
                    "Reused agent should be showing its 'base' version on arrival"
                )
                original_instructions = detail_page.get_instructions()
                assert not detail_page.is_save_enabled(), (
                    "Save should be disabled before any edit is made"
                )
                # NOTE: AgentFormPage.discard_button's `discard-button` testid is not
                # actually wired up on the Agent detail page live (confirmed absent
                # from document.querySelectorAll('[data-testid]') during ELITEA-1888
                # implementation — pre-existing gap, out of this case's scope to fix;
                # unlike PipelineFormPage/CredentialDetailPage, whose own
                # discard-button testids ARE live). Discard-state is therefore not
                # asserted here — only Save / Save As Version, whose testids are
                # confirmed live.

            with allure.step("Step 2 — Append a word to the Instructions field"):
                detail_page.instructions_input.click()
                detail_page.instructions_input.press(
                    "ControlOrMeta+End"
                )
                detail_page.instructions_input.press_sequentially(
                    INSTRUCTION_APPEND, delay=50
                )
                expected_instructions = original_instructions + INSTRUCTION_APPEND
                assert detail_page.get_instructions() == expected_instructions, (
                    "Instructions field should reflect the appended text"
                )
                assert detail_page.is_save_enabled(), (
                    "Save should become enabled once the form is dirty"
                )
                assert detail_page.save_as_version_button.is_enabled(), (
                    "Save As Version should be enabled once the form is dirty"
                )

            with allure.step(
                'Step 3/4 — Click "Save As Version" and verify the "Create version" '
                "dialog appears asking for a version name"
            ):
                previous_version_id = detail_page.get_version_id()
                detail_page.open_save_as_version_dialog(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.create_version_name_input.is_visible(), (
                    'The "Create version" dialog should show a Name input'
                )
                assert not detail_page.create_version_save_button.is_enabled(), (
                    "Dialog Save button should be disabled while Name is empty"
                )

            with allure.step('Step 5 — Enter "v2-test" and confirm'):
                detail_page.confirm_new_version(VERSION_NAME, timeout=NAVIGATION_TIMEOUT)

                assert detail_page.get_version_selector_value() == VERSION_NAME, (
                    f"VERSION selector should show {VERSION_NAME!r} after Save As Version"
                )
                new_version_id = detail_page.get_version_id()
                assert new_version_id != previous_version_id, (
                    "Version ID should change after creating a new named version"
                )
                assert not detail_page.is_save_enabled(), (
                    "Save should return to disabled — the new version is persisted, "
                    "not a local unsaved edit"
                )
                assert detail_page.get_instructions() == expected_instructions, (
                    "The edited Instructions text should be preserved in the new "
                    "version, not reset to the base version's content"
                )

            with allure.step(
                'Step 6 — Open the VERSION dropdown and verify it lists both '
                '"base" and "v2-test"'
            ):
                detail_page.open_version_selector()
                assert detail_page.is_version_option_visible("base", timeout=UI_ELEMENT_TIMEOUT), (
                    "VERSION dropdown should list the 'base' version"
                )
                assert detail_page.is_version_option_visible(VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                    f"VERSION dropdown should list the new {VERSION_NAME!r} version"
                )

            with allure.step('Step 7 — Verify "v2-test" is the currently active version'):
                assert detail_page.is_version_option_active(VERSION_NAME), (
                    f"{VERSION_NAME!r} should be the active/selected option in the "
                    f"open VERSION dropdown"
                )
                assert not detail_page.is_version_option_active("base"), (
                    "'base' should NOT be the active/selected option anymore"
                )
                detail_page.close_versions_menu()
        finally:
            with allure.step("Cleanup — delete the reused agent (including the new version)"):
                try:
                    if detail_page is not None and "/agents/all/" in detail_page.page.url:
                        detail_page.delete_agent_via_menu(timeout=NAVIGATION_TIMEOUT)
                    else:
                        agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")
