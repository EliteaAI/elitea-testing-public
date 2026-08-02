"""Save As Version creates a named version visible in the version dropdown
(ELITEA-1888), extended to also cover switching versions updates form
fields correctly (ELITEA-1890).

Edits an existing agent's Instructions, saves the change as a new named
version via "Save As Version", and verifies the new version is visible
(and active) in the VERSION dropdown alongside "base". Then (ELITEA-1890's
extension — Step 8) switches back to "base" and verifies the Instructions
field reverts to its original content — the "switch back" round trip that
ELITEA-1888's own steps never exercised.

Test-data strategy (per AFS — see below, amended after the lead's live-run
gate caught pool exhaustion on run 3/3): this test creates a **dedicated,
uniquely-named agent** for each run via `AgentAPI.create_agent_full()` with
an `llm_settings` payload that avoids the open, unrelated
EliteaAI/elitea-testing-public#524 defect (`temperature` + a non-`'none'`
`reasoning_effort` 400 on the project's reasoning-capable default model) by
setting `reasoning_effort: "none"` and omitting `temperature` entirely. The
agent is deleted at teardown via `delete_agent_via_menu()` — this test is
therefore fully self-sufficient (create-and-clean every run) and does not
depend on any shared/finite pool of pre-existing data.

Specs:
- test-specs/agents/lcritical_save-as-version-creates-named-version-visible-in-dropdown_ELITEA-1888.md
- test-specs/agents/lextend_switching-versions-updates-form-fields-correctly_ELITEA-1890.md
"""

import uuid

import pytest
import allure

from config import settings
from pages.agent_detail_page import AgentDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000

VERSION_NAME = "v2-test"
INSTRUCTION_APPEND = " Additionally."
BASE_INSTRUCTIONS = "You are a helpful assistant."


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the open #524 defect (`temperature` is not
    allowed together with a `reasoning_effort` other than 'none' on the
    project's reasoning-capable default model). This does not "fix" #524 —
    it simply avoids the known-bad combination in this test's own fixture
    payload; #524 remains open and unrelated to this test's assertions.
    """
    return {
        "name": name,
        "description": "Auto-created for ELITEA-1888 save-as-version test",
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [],
                "instructions": BASE_INSTRUCTIONS,
                "variables": [],
                "tools": [],
                "llm_settings": {
                    "max_tokens": -1,
                    "reasoning_effort": "none",
                    "model_name": settings.default_model_name,
                    "model_project_id": settings.default_model_project_id,
                },
                "conversation_starters": [],
                "agent_type": "openai",
                "welcome_message": "",
                "meta": {"step_limit": 25},
            }
        ],
    }


class TestAgentSaveAsVersion:
    """Save As Version creates a named version visible in version dropdown
    (ELITEA-1888, lcritical/p0), extended with the switch-back round trip
    (ELITEA-1890, lextend)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1888_save-as-version-creates-named-version-visible-in-dropdown.md",
        "onetest-ai Test Case link (ELITEA-1888)",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1890_switching-between-versions-updates-form-fields-correctly.md",
        "onetest-ai Test Case link (ELITEA-1890)",
    )
    @pytest.mark.p0
    @pytest.mark.regression
    def test_save_as_version_creates_named_version_visible_in_dropdown(self, page, agent_api):
        """Editing Instructions and clicking Save As Version creates a named
        version that appears (and is active) in the VERSION dropdown; switching
        back to 'base' reverts the Instructions field to its original content
        (ELITEA-1890, Step 8)."""
        with allure.step("Precondition — create a dedicated disposable agent in its 'base' version"):
            # API enforces a 32-char max on agent name (confirmed live: creating
            # with the full "elitea-1888-save-as-version-<hex8>" name 400s with
            # "String should have at most 32 characters") — keep the prefix short.
            agent_name = f"elitea-1888-sav-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

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

            with allure.step(
                "Step 8 — Switch back to the original 'base' version and "
                "verify the Instructions field reverts to its original "
                "content (ELITEA-1890's extension — the switch-back round "
                "trip ELITEA-1888's own steps never exercised)"
            ):
                detail_page.open_version_selector()
                detail_page.page.locator(detail_page.VERSION_OPTION.format("base")).click()
                detail_page.page.wait_for_function(
                    """() => {
                        const el = document.querySelector('[data-testid="agent-version-selector-trigger"]');
                        return el && el.innerText.trim() === 'base';
                    }""",
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                assert detail_page.get_version_selector_value() == "base", (
                    "VERSION selector should show 'base' after switching back"
                )
                # The Instructions field's own re-render race (confirmed live,
                # this run): the VERSION trigger's text updates BEFORE the
                # Instructions field's value has actually refetched/reset —
                # a single point-in-time get_instructions() read right after
                # the trigger-text wait can still catch the STALE (v2-test)
                # value. Poll the field's own value, not just the trigger,
                # mirroring confirm_new_version()'s "URL updates before the
                # VERSION selector's text" race documented above.
                detail_page.page.wait_for_function(
                    """expected => {
                        const el = document.querySelector('[data-testid="agent-instructions-input"]');
                        return !!el && el.value === expected;
                    }""",
                    arg=original_instructions,
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                assert detail_page.get_instructions() == original_instructions, (
                    "Instructions field should revert to the original 'base' "
                    "version's content after switching back"
                )
        finally:
            with allure.step("Cleanup — delete the dedicated agent (including the new version)"):
                try:
                    if detail_page is not None and "/agents/all/" in detail_page.page.url:
                        detail_page.delete_agent_via_menu(timeout=NAVIGATION_TIMEOUT)
                    else:
                        agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")
