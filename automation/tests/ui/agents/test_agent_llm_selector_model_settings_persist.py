"""LLM selector — change model, verify settings dialog, save and persist
(ELITEA-1880).

Verifies that the LLM model selector accepts a new model selection, that the
Settings (gear) dialog opens showing model-type-appropriate fields (a
Reasoning slider for a reasoning-capable model + the always-present Max
Completion Tokens section), that Save persists the model change at the
network level (PUT .../application/prompt_lib/... -> 201), and that the
change survives a real page reload (UI-level persistence, not just the
network status).

Test-data strategy (per AFS): a dedicated, disposable agent per run via
``AgentAPI.create_agent_full()`` (mirrors the ELITEA-1881/1883/1888 pattern)
rather than mutating a shared fixture agent — this case mutates persisted
``llm_settings`` (model) via Save, so a shared agent would create cross-test
races under ``pytest-xdist``.

Spec: test-specs/agents/l2_llm-selector-change-model-settings-dialog-persist_ELITEA-1880.md
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

# A reasoning-capable model, confirmed live during AFS analysis to render the
# Reasoning-slider branch of the Model settings dialog (Anthropic models on
# this platform are reasoning-capable) — matches ELITEA-1881's dropdown-name
# constant so both specs assert against a confirmed-present option.
TARGET_MODEL_DISPLAY_NAME = "Anthropic Claude 4.5 Sonnet"

# Rendered labels inside the Model settings dialog (per AFS Coverage Map
# Clarification 2: the live UI reads "Default", NOT "Auto" — case-text drift).
REASONING_LEVEL_LABELS = ("Low", "Medium", "High")
MAX_TOKENS_MODE_LABELS = ("Default", "Custom")


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the open #524-class defect (`temperature`
    not allowed together with a `reasoning_effort` other than 'none' on the
    project's reasoning-capable default model) — mirrors
    ``test_agent_llm_selector_anthropic_models.py``'s payload shape. The
    initial model is irrelevant to this case — the case re-selects a
    different model via the UI before saving.
    """
    return {
        "name": name,
        "description": "Auto-created for ELITEA-1880 LLM selector settings-dialog test",
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


class TestAgentLlmSelectorModelSettingsPersist:
    """LLM selector — change model, verify settings dialog, save and persist (ELITEA-1880, p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1880_llm-selector-change-model-settings-dialog-persist.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_llm_selector_change_model_settings_dialog_persist(
        self, page: Page, agent_api
    ):
        """Changing the model via the selector, opening the Settings dialog,
        Save, and a real reload all behave correctly, and the selected model
        persists across the reload."""
        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1880-llm-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        detail_page = None
        # Captures both "error" and "warning" console messages — the case's
        # Expected Results call for "no console errors or warnings at any
        # point in the flow" (AFS Axis-2 console-message check).
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
                    "Model selector should display a non-empty model name "
                    "before any change"
                )

            with allure.step(
                "Step 3 — Click the model selector and choose a different model"
            ):
                detail_page.open_model_selector(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.is_model_option_visible(
                    TARGET_MODEL_DISPLAY_NAME, timeout=UI_ELEMENT_TIMEOUT
                ), f"Model selector dropdown should list {TARGET_MODEL_DISPLAY_NAME!r}"
                assert TARGET_MODEL_DISPLAY_NAME != initial_model_name, (
                    "Target model for this case should differ from the "
                    f"agent's initial model, got both = {initial_model_name!r}"
                )
                detail_page.select_llm_model(
                    TARGET_MODEL_DISPLAY_NAME, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 4 — Verify the new model name is shown in the selector"
            ):
                assert detail_page.get_selected_model_name() == TARGET_MODEL_DISPLAY_NAME, (
                    f"Model selector should show {TARGET_MODEL_DISPLAY_NAME!r} "
                    "immediately after selection (client-side, pre-Save)"
                )
                assert detail_page.is_save_enabled(), (
                    "Save should be enabled once the model selection is dirty"
                )

            with allure.step("Step 5 — Click the Settings (gear) icon"):
                detail_page.open_model_settings_dialog(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.model_settings_dialog.is_visible(), (
                    "Model settings dialog should be open"
                )

            with allure.step(
                "Step 6 — Verify the settings dialog shows fields appropriate "
                "to the selected (reasoning-capable) model type"
            ):
                assert detail_page.is_reasoning_slider_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"{TARGET_MODEL_DISPLAY_NAME!r} is reasoning-capable — the "
                    "dialog should render the Reasoning slider, not the "
                    "Creativity/Temperature slider"
                )
                # Case-insensitive: the slider's raw DOM text is lowercase
                # ("low"/"medium"/"high") — CSS `text-transform: capitalize`
                # renders it as "Low"/"Medium"/"High" visually (confirmed
                # live: REASONING_EFFORT_VALUES in llmSettings.constants.js
                # stores lowercase values). The case cares that all three
                # reasoning levels are present, not the DOM's raw letter
                # case, which is a styling implementation detail.
                reasoning_slider_text = detail_page.get_reasoning_slider_text().lower()
                for label in REASONING_LEVEL_LABELS:
                    assert label.lower() in reasoning_slider_text, (
                        f"Reasoning slider should show the {label!r} level, "
                        f"got: {reasoning_slider_text!r}"
                    )

                max_tokens_text = detail_page.get_max_tokens_section_text()
                for label in MAX_TOKENS_MODE_LABELS:
                    assert label in max_tokens_text, (
                        f"Max Completion Tokens section should show the "
                        f"{label!r} toggle option, got: {max_tokens_text!r}"
                    )

            with allure.step("Step 7 — Close the settings dialog and click Save"):
                detail_page.close_model_settings_dialog_via_cancel(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert detail_page.get_selected_model_name() == TARGET_MODEL_DISPLAY_NAME, (
                    "Model selector should still show the step-3 selection "
                    "after closing the settings dialog without applying "
                    "changes"
                )

                with page.expect_response(
                    _is_save_response, timeout=SAVE_RESPONSE_TIMEOUT
                ) as response_info:
                    detail_page.click_save(timeout=UI_ELEMENT_TIMEOUT)
                save_response = response_info.value
                assert save_response.status == 201, (
                    "PUT application/prompt_lib/... should return 201 on "
                    f"Save, got {save_response.status}"
                )
                assert not detail_page.is_save_enabled(), (
                    "Save should return to disabled once the model "
                    "selection has persisted"
                )

            with allure.step("Step 8 — Reload the page"):
                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)

            with allure.step(
                "Step 9 — Verify the model selector still shows the model "
                "chosen in step 3"
            ):
                assert detail_page.get_selected_model_name() == TARGET_MODEL_DISPLAY_NAME, (
                    "Model selector should display the saved model "
                    f"({TARGET_MODEL_DISPLAY_NAME!r}) after a full page reload"
                )

            with allure.step("Verify no console errors or warnings across the full flow"):
                assert not console_issues, (
                    "Expected no console errors/warnings across the model "
                    "change / settings-dialog / save / reload flow, got: "
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
                            f"Warning: API fallback delete also failed for "
                            f"agent {agent_id}: {api_cleanup_exc}"
                        )
