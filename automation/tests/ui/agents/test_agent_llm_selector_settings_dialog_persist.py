"""LLM selector — change model, verify settings dialog, save and persist
(ELITEA-1880).

Verifies that:
1. The embedded chat panel's LLM model selector allows switching to a
   different (reasoning-capable) model, with the new selection reflected
   immediately in the selector (``model-selector-name``).
2. The Settings (gear) dialog opens and shows fields appropriate to the
   selected model's declared capabilities — a Reasoning slider
   (Low/Medium/High) + Max Completion Tokens (Default/Custom) for a
   reasoning-capable model.
3. Closing the dialog (without applying any dialog-internal change) and
   clicking the top-toolbar Save persists the model selection — asserted at
   the network level (``PUT .../application/prompt_lib/...`` -> 201
   Created), not just via the Save button's disabled state.
4. After a full page reload, the model selector still shows the saved model
   — genuine server-side persistence, not just client-side/cached state.

Test-data strategy (per AFS): mirrors the ELITEA-1881 pattern — this test
creates a **dedicated, uniquely-named agent** via
``AgentAPI.create_agent_full()`` rather than mutating the shared "Test
Agent" fixture, to avoid xdist races on persisted LLM state across parallel
test runs (pytest-xdist is in the stack). The agent is deleted at teardown.

Clarification (AFS Coverage Map, reverse-masking guard): the case's own Test
Data table names the Max Completion Tokens options "Auto/Custom"; the live
UI's label is "Default", not "Auto" (``MaxTokensSection.jsx``) — cosmetic
case-text drift, not a defect. This test asserts the live "Default" label
(surfaced via the ``model-settings-max-tokens-mode-auto`` testid).

Spec: test-specs/agents/l2_llm-selector-change-model-verify-settings-dialog-save-persist_ELITEA-1880.md
"""

import uuid

import allure
import pytest
from playwright.sync_api import Page, Response

from config import settings
from pages.agent_detail_page import AgentDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
SAVE_RESPONSE_TIMEOUT = 15_000

# A "Supports reasoning" model, distinct from the agent's creation-time
# default — its display name as rendered in the model-selector dropdown
# (confirmed live during AFS analysis). The case's own Test Data table names
# GPT-5.4 as its example but lists GPT-5.2 as an equally valid substitute for
# the "Supports reasoning" requirement; GPT-5.2 also doubles as
# settings.default_model_name, kept cheap for cost efficiency in tests.
TARGET_MODEL_DISPLAY_NAME = "GPT-5.2"


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the open #524-class defect (`temperature`
    not allowed together with a `reasoning_effort` other than 'none' on the
    project's reasoning-capable default model) — mirrors the same payload
    shape used by ``test_agent_llm_selector_anthropic_models.py``. The
    initial model is irrelevant to this case — the test re-selects the
    target model via the UI (step 3) before saving.
    """
    return {
        "name": name,
        "description": "Auto-created for ELITEA-1880 LLM selector settings dialog test",
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [],
                "instructions": "You are a helpful assistant.",
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


def _is_save_response(response: Response) -> bool:
    """Match the agent Save PUT: `.../application/prompt_lib/{project}/{id}`."""
    return (
        "application/prompt_lib" in response.url
        and response.request.method == "PUT"
    )


class TestAgentLlmSelectorSettingsDialogPersist:
    """LLM selector — change model, verify settings dialog, save and persist (ELITEA-1880, p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1880_llm-selector-change-model-verify-settings-dialog-save-persist.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_llm_selector_change_model_verify_settings_dialog_save_persist(
        self, page: Page, agent_api
    ):
        """Change the LLM model, verify the Settings dialog's fields match
        the selected model's capabilities, save (201 on the Save PUT), and
        confirm the selection survives a full page reload."""
        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1880-llm-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        detail_page = None
        # Captures both "error" and "warning" console messages — the case's
        # Expected Results call for "no console errors or warnings at any
        # point in the flow" (per AFS Axis-2 console-message check).
        console_issues = []
        page.on(
            "console",
            lambda msg: console_issues.append(msg)
            if msg.type in ("error", "warning")
            else None,
        )

        try:
            with allure.step("Step 1 — Navigate to agent detail page"):
                detail_page = AgentDetailPage(page)
                detail_page.navigate(agent_id)
                assert detail_page.information_section.is_visible(), (
                    "Agent detail page's Information section should be visible"
                )
                assert detail_page.chat_message_input.is_visible(), (
                    "Embedded chat panel's message input should be visible"
                )

            with allure.step("Step 2 — Note the currently selected model"):
                initial_model_name = detail_page.get_selected_model_name()
                assert initial_model_name, (
                    "A model name should be selected on the closed model selector"
                )

            with allure.step(
                f"Step 3-4 — Select {TARGET_MODEL_DISPLAY_NAME!r} and verify it's shown"
            ):
                detail_page.open_model_selector(timeout=UI_ELEMENT_TIMEOUT)
                detail_page.select_llm_model(
                    TARGET_MODEL_DISPLAY_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                # Exact match (not a substring/has_text check) — TARGET_MODEL_DISPLAY_NAME
                # and a "-mini" sibling variant are both valid model names, and a loose
                # match would produce a false positive (AFS Axis 2 addition).
                assert detail_page.get_selected_model_name() == TARGET_MODEL_DISPLAY_NAME, (
                    f"Model selector should now show {TARGET_MODEL_DISPLAY_NAME!r} as selected"
                )
                assert detail_page.is_save_enabled(), (
                    "Save should be enabled once the model selection is dirty"
                )

            with allure.step("Step 5 — Click the Settings (gear) icon"):
                detail_page.open_model_settings(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.is_settings_dialog_open(), (
                    "Model settings dialog should be open"
                )

            with allure.step(
                "Step 6 — Verify the dialog shows fields appropriate to the model type: "
                "Reasoning slider + Max Completion Tokens (reasoning-capable model)"
            ):
                assert detail_page.is_reasoning_slider_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    f"Reasoning slider (Low/Medium/High) should be visible for "
                    f"reasoning-capable model {TARGET_MODEL_DISPLAY_NAME!r}"
                )
                # Clarification (AFS Coverage Map): the case text names this option
                # "Auto"; the live UI label is "Default" — asserting the live label per
                # the reverse-masking guard, not the stale case text.
                assert detail_page.is_max_tokens_mode_visible(
                    "auto", timeout=UI_ELEMENT_TIMEOUT
                ), 'Max Completion Tokens "Default" option should be visible'
                assert detail_page.is_max_tokens_mode_visible(
                    "custom", timeout=UI_ELEMENT_TIMEOUT
                ), 'Max Completion Tokens "Custom" option should be visible'

            with allure.step("Step 7 — Close the settings dialog and click Save"):
                detail_page.close_settings_dialog(timeout=UI_ELEMENT_TIMEOUT)
                assert not detail_page.is_settings_dialog_open(), (
                    "Model settings dialog should be closed"
                )

                # Network-level assertion (not just the Save button's disabled state) —
                # the stronger, non-flaky proof of persistence (AFS Axis 2 addition,
                # mirroring the pattern established in ELITEA-1881's merged test).
                with page.expect_response(
                    _is_save_response, timeout=SAVE_RESPONSE_TIMEOUT
                ) as response_info:
                    detail_page.click_save(timeout=UI_ELEMENT_TIMEOUT)
                save_response = response_info.value
                assert save_response.status == 201, (
                    "PUT application/prompt_lib/... should return 201 on Save, "
                    f"got {save_response.status}"
                )
                assert not detail_page.is_save_enabled(), (
                    "Save should return to disabled once the model selection has persisted"
                )

            with allure.step("Step 8 — Reload the page"):
                page.reload()
                # Reload wait strategy (AFS Automation Hints): the embedded chat panel
                # (and its model selector) mounts slightly after the form sections, so
                # wait_for_page_load()'s Information-section + non-empty-Name-input
                # condition must settle before reading model-selector-name below.
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)

            with allure.step(
                f"Step 9 — Verify the model selector still shows {TARGET_MODEL_DISPLAY_NAME!r} "
                "after reload"
            ):
                # A fresh DOM query post-reload (full page navigation, not a client-side
                # cache read) — genuine server-round-trip confirmation of persistence.
                assert detail_page.get_selected_model_name() == TARGET_MODEL_DISPLAY_NAME, (
                    f"Model selector should still show {TARGET_MODEL_DISPLAY_NAME!r} after "
                    "a full page reload (server-side persistence)"
                )

            with allure.step("Verify no console errors or warnings across the full flow"):
                assert not console_issues, (
                    "Expected no console errors/warnings across the model-change/"
                    f"settings-dialog/save/reload flow, got: "
                    f"{[(m.type, m.text) for m in console_issues]}"
                )
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                try:
                    if detail_page is not None and "/agents/all/" in detail_page.page.url:
                        detail_page.delete_agent_via_menu(timeout=NAVIGATION_TIMEOUT)
                    else:
                        agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(
                        f"Warning: UI-menu delete failed for agent {agent_id}: "
                        f"{cleanup_exc}. Falling back to API delete."
                    )
                    # UI-teardown hiccup is a documented flake class (see
                    # mui-patterns.md) — fall back to the API so the
                    # disposable test agent doesn't leak either way.
                    try:
                        agent_api.delete_agent(agent_id)
                    except Exception as api_cleanup_exc:
                        print(
                            f"Warning: API fallback delete also failed for agent "
                            f"{agent_id}: {api_cleanup_exc}"
                        )
