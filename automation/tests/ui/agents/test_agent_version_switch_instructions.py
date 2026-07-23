"""Switching between agent versions updates the Instructions field correctly,
in both directions (ELITEA-1890).

Creates a dedicated, disposable agent with two versions carrying distinct
Instructions content (a "base" version + a named "v2-distinct" version,
created via the same "edit Instructions -> Save As Version" setup flow
ELITEA-1888/1889/1892 already established), then verifies that switching from
"base" to "v2-distinct" via the VERSION dropdown updates the Instructions
field to the newly-selected version's own content, and that switching back to
"base" restores the original content byte-for-byte.

No product defects were found live during this case's analysis — all 6 case
steps executed cleanly with no console errors observed at any point (AFS
Expected Results). Zero new testids needed: every handle this case uses
(``agent-version-selector-trigger``, ``version-option-{name}``,
``copy-version-id``, ``agent-instructions-input``) was added by prior cases
and is confirmed on `main` (AFS Concrete Handles).

Spec: test-specs/agents/lcritical_switching-versions-updates-instructions-field_ELITEA-1890.md
"""

import uuid

import allure
import pytest
from config import settings
from pages.agent_detail_page import AgentDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

SECOND_VERSION_NAME = "v2-distinct"
BASE_INSTRUCTIONS = "BASE VERSION INSTRUCTIONS - ELITEA-1890."
INSTRUCTION_APPEND = " V2 DISTINCT INSTRUCTIONS - ELITEA-1890 SWITCHED."
SECOND_VERSION_INSTRUCTIONS = BASE_INSTRUCTIONS + INSTRUCTION_APPEND


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the open #524 defect (`temperature` is not
    allowed together with a `reasoning_effort` other than 'none' on the
    project's reasoning-capable default model) — same workaround as
    ELITEA-1888/1889/1892's payloads.
    """
    return {
        "name": name,
        "description": "Disposable agent for ELITEA-1890 version-switch test",
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


class TestAgentVersionSwitchInstructions:
    """Switching between agent versions updates the Instructions field
    correctly, in both directions (ELITEA-1890, lcritical/p0)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1890_switching-versions-updates-instructions-field.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p0
    @pytest.mark.regression
    def test_switching_versions_updates_instructions_field(self, page, agent_api):
        """Switching versions via the VERSION dropdown updates the
        Instructions field to match each version's own content, and
        switching back restores the original content byte-for-byte."""
        with allure.step(
            "Setup — create a dedicated disposable agent in its 'base' version"
        ):
            agent_name = f"elitea-1890-ver-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        detail_page = AgentDetailPage(page)
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
        )

        try:
            with allure.step(
                "Setup — edit Instructions and Save As Version to create a "
                f"second, distinct version ({SECOND_VERSION_NAME!r})"
            ):
                detail_page.navigate(agent_id)
                assert detail_page.get_version_selector_value() == "base", (
                    "New disposable agent should be showing its 'base' version"
                )
                base_version_id = detail_page.get_version_id()

                detail_page.instructions_input.click()
                detail_page.instructions_input.press("ControlOrMeta+End")
                detail_page.instructions_input.press_sequentially(
                    INSTRUCTION_APPEND, delay=50
                )
                assert detail_page.get_instructions() == SECOND_VERSION_INSTRUCTIONS, (
                    "Instructions field should reflect the appended text "
                    "before Save As Version"
                )

                detail_page.open_save_as_version_dialog(timeout=UI_ELEMENT_TIMEOUT)
                detail_page.confirm_new_version(
                    SECOND_VERSION_NAME, timeout=NAVIGATION_TIMEOUT
                )
                assert detail_page.get_version_selector_value() == SECOND_VERSION_NAME, (
                    f"VERSION selector should show {SECOND_VERSION_NAME!r} after "
                    "Save As Version"
                )
                second_version_id = detail_page.get_version_id()
                assert second_version_id != base_version_id, (
                    "The new named version should have a distinct version id "
                    "from 'base'"
                )

            with allure.step(
                "Step 1 — Navigate to the agent's detail page fresh (bare "
                "?viewMode=owner, no version segment) and record the active "
                "version + its Instructions content"
            ):
                detail_page.navigate(agent_id)
                assert detail_page.get_version_selector_value() == "base", (
                    "A fresh, bare navigate should always land on 'base', "
                    "regardless of which version was last active"
                )
                assert detail_page.get_version_id() == base_version_id, (
                    "The version id shown should match the original 'base' "
                    "version's id"
                )
                assert detail_page.get_instructions() == BASE_INSTRUCTIONS, (
                    "Instructions field should show the 'base' version's "
                    "original content"
                )

            with allure.step(
                "Step 2 — Open the VERSION dropdown, verify it lists both "
                f"versions, select {SECOND_VERSION_NAME!r}, and verify the "
                "Instructions field updates to that version's content"
            ):
                detail_page.open_version_selector()
                assert detail_page.is_version_option_visible(
                    "base", timeout=UI_ELEMENT_TIMEOUT
                ), "VERSION dropdown should list the 'base' version"
                assert detail_page.is_version_option_visible(
                    SECOND_VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT
                ), f"VERSION dropdown should list the {SECOND_VERSION_NAME!r} version"
                assert detail_page.is_version_option_active("base"), (
                    "'base' should be the active/selected option before switching"
                )
                assert not detail_page.is_version_option_active(SECOND_VERSION_NAME), (
                    f"{SECOND_VERSION_NAME!r} should NOT be active before switching"
                )
                detail_page.close_versions_menu()

                switched_version_id = detail_page.select_version_by_name(
                    SECOND_VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                assert switched_version_id == second_version_id, (
                    "select_version_by_name should land on the previously "
                    "created second version's id"
                )
                assert detail_page.get_version_selector_value() == SECOND_VERSION_NAME, (
                    f"VERSION selector should show {SECOND_VERSION_NAME!r} after "
                    "switching"
                )
                assert (
                    f"/agents/all/{agent_id}/{second_version_id}" in detail_page.page.url
                ), "URL should carry the second version's id segment after switching"
                assert detail_page.get_instructions() == SECOND_VERSION_INSTRUCTIONS, (
                    f"Instructions field should show the {SECOND_VERSION_NAME!r} "
                    "version's own content immediately after switching"
                )

            with allure.step(
                "Step 3 — Switch back to 'base' and verify the Instructions "
                "field returns to the original content"
            ):
                detail_page.open_version_selector()
                assert detail_page.is_version_option_active(SECOND_VERSION_NAME), (
                    f"{SECOND_VERSION_NAME!r} should be the active/selected "
                    "option before switching back"
                )
                assert not detail_page.is_version_option_active("base"), (
                    "'base' should NOT be active before switching back"
                )
                detail_page.close_versions_menu()

                restored_version_id = detail_page.select_version_by_name(
                    "base", timeout=UI_ELEMENT_TIMEOUT
                )
                assert restored_version_id == base_version_id, (
                    "select_version_by_name should land back on the original "
                    "'base' version's id"
                )
                assert detail_page.get_version_selector_value() == "base", (
                    "VERSION selector should show 'base' after switching back"
                )
                assert (
                    f"/agents/all/{agent_id}/{base_version_id}" in detail_page.page.url
                ), "URL should carry the base version's id segment after switching back"
                assert detail_page.get_instructions() == BASE_INSTRUCTIONS, (
                    "Instructions field should return to the exact original "
                    "'base' content, byte-for-byte"
                )

            with allure.step("Verify no console errors occurred across the whole flow"):
                assert not console_errors, (
                    f"Expected no console errors during version switching, "
                    f"got: {console_errors!r}"
                )
        finally:
            with allure.step(
                "Cleanup — delete the dedicated agent (including both versions)"
            ):
                try:
                    agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")
