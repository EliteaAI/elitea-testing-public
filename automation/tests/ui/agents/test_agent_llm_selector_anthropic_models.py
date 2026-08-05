"""LLM selector — Anthropic models are available and functional
(ELITEA-1881).

Verifies that all three specified Anthropic models (Claude 4.5 Sonnet,
Claude 4.6 Sonnet, Claude Haiku 4.5) are present in the agent detail page's
LLM model selector dropdown, can each be selected, persisted via Save
(asserted at the network level — PUT .../application/prompt_lib/... -> 201),
and are functional in the embedded chat panel (each produces a "CONFIRMED"
response correctly attributed to the selected model).

This test drives 3 real, serial LLM round-trips (select -> save -> send ->
await-response, once per model) against live Anthropic-backed models via the
platform's LLM proxy — see AI_RESPONSE_TIMEOUT below for the generous
per-response wait budget this requires (per AFS Automation Hints).

Test-data strategy (per AFS): mirrors the ELITEA-1883/1888 pattern — this
test creates a **dedicated, uniquely-named agent** for each run via
``AgentAPI.create_agent_full()`` rather than mutating the shared "Test Agent"
fixture, to avoid xdist races on that agent's LLM selection across parallel
test runs. The agent is deleted at teardown via ``delete_agent_via_menu()``.

Spec: test-specs/agents/l2_llm-selector-anthropic-models_ELITEA-1881.md
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
# Live LLM inference, not just message delivery — AFS observed 2-15s per
# model round trip; a generous override well above the project default is
# needed to absorb latency variance without flaking (AFS Automation Hints).
AI_RESPONSE_TIMEOUT = 60_000

TEST_MESSAGE = "Reply only with: CONFIRMED"
EXPECTED_RESPONSE_SUBSTRING = "CONFIRMED"

# The 3 case-specified Anthropic models, by their live dropdown DISPLAY name
# (vendor-prefixed — confirmed live during ELITEA-1881 analysis; the case's
# own Test Data table omits the "Anthropic " prefix, which is case-text
# shorthand, not a defect — see AFS Coverage Map clarification).
ANTHROPIC_MODEL_DISPLAY_NAMES = [
    "Anthropic Claude 4.5 Sonnet",
    "Anthropic Claude 4.6 Sonnet",
    "Anthropic Claude Haiku 4.5",
]


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the open #524-class defect (`temperature`
    not allowed together with a `reasoning_effort` other than 'none' on the
    project's reasoning-capable default model) — mirrors the same payload
    shape used by ``test_agent_save_as_version.py`` /
    ``test_agent_add_variables_persist_after_reload.py``. The initial model
    is irrelevant to this case — every case step re-selects the model under
    test via the UI before saving.
    """
    return {
        "name": name,
        "description": "Auto-created for ELITEA-1881 LLM selector test",
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


class TestAgentLlmSelectorAnthropicModels:
    """LLM selector — Anthropic models are available and functional (ELITEA-1881, p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1881_llm-selector-anthropic-models-are-available-and-functional.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    @pytest.mark.slow
    def test_llm_selector_anthropic_models_are_available_and_functional(
        self, page: Page, agent_api
    ):
        """All three Anthropic models are listed in the LLM selector, each
        can be selected + saved (201 on the Save PUT), and each produces a
        "CONFIRMED" response in the embedded chat, correctly attributed to
        the selected model."""
        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1881-llm-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        detail_page = None
        # Captures both "error" and "warning" console messages — the case's
        # Expected Results call for "0 errors/warnings" across the flow, not
        # just errors (per AFS Axis-2 console-message check).
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

            with allure.step("Step 2 — Click the model selector dropdown"):
                detail_page.open_model_selector(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.is_model_option_visible(
                    ANTHROPIC_MODEL_DISPLAY_NAMES[0], timeout=UI_ELEMENT_TIMEOUT
                ), "Model selector dropdown should be open with options visible"

            with allure.step(
                "Step 3 — Verify all three Anthropic models are present in the dropdown"
            ):
                for display_name in ANTHROPIC_MODEL_DISPLAY_NAMES:
                    assert detail_page.is_model_option_visible(
                        display_name, timeout=UI_ELEMENT_TIMEOUT
                    ), f"Model selector dropdown should list {display_name!r}"

            # Close the dropdown before the per-model select/save/chat loop below
            # re-opens it explicitly for each model.
            detail_page.close_model_selector(timeout=UI_ELEMENT_TIMEOUT)

            for i, display_name in enumerate(ANTHROPIC_MODEL_DISPLAY_NAMES, start=1):
                step_label = {1: "Step 4-6", 2: "Step 7", 3: "Step 8"}[i]
                with allure.step(
                    f"{step_label} — Select {display_name!r}, save, and verify the "
                    f'chat response contains "{EXPECTED_RESPONSE_SUBSTRING}"'
                ):
                    detail_page.open_model_selector(timeout=UI_ELEMENT_TIMEOUT)
                    detail_page.select_llm_model(display_name, timeout=UI_ELEMENT_TIMEOUT)
                    assert detail_page.get_selected_model_name() == display_name, (
                        f"Model selector should now show {display_name!r} as selected"
                    )
                    assert detail_page.is_save_enabled(), (
                        "Save should be enabled once the model selection is dirty"
                    )

                    with page.expect_response(
                        _is_save_response, timeout=SAVE_RESPONSE_TIMEOUT
                    ) as response_info:
                        detail_page.click_save(timeout=UI_ELEMENT_TIMEOUT)
                    save_response = response_info.value
                    assert save_response.status == 201, (
                        "PUT application/prompt_lib/... should return 201 on Save, "
                        f"got {save_response.status} for model {display_name!r}"
                    )
                    assert not detail_page.is_save_enabled(), (
                        "Save should return to disabled once the model selection "
                        "has persisted"
                    )

                    initial_count = detail_page.get_chat_message_count()
                    detail_page.send_chat_message(TEST_MESSAGE, timeout=UI_ELEMENT_TIMEOUT)
                    detail_page.wait_for_chat_response(
                        initial_count=initial_count,
                        stable_duration_ms=2000,
                        timeout=AI_RESPONSE_TIMEOUT,
                    )

                    response_text = detail_page.get_last_chat_response_text()
                    assert EXPECTED_RESPONSE_SUBSTRING in response_text, (
                        f"Response for model {display_name!r} should contain "
                        f"{EXPECTED_RESPONSE_SUBSTRING!r}, got: {response_text!r}"
                    )

                    # Axis 2 addition: the response must be attributed to the
                    # correct model in the transcript — a silent misattribution
                    # regression wouldn't fail on response-text alone.
                    full_message_text = detail_page.get_last_chat_message_full_text()
                    assert display_name in full_message_text, (
                        f"Response should be attributed to {display_name!r} in the "
                        f"transcript, got full message text: {full_message_text!r}"
                    )
                    other_models = [
                        m for m in ANTHROPIC_MODEL_DISPLAY_NAMES if m != display_name
                    ]
                    for other in other_models:
                        assert other not in full_message_text, (
                            f"Response for {display_name!r} should NOT be "
                            f"attributed to a different model {other!r}"
                        )

            with allure.step("Verify no console errors or warnings across the full flow"):
                assert not console_issues, (
                    "Expected no console errors/warnings across the 3-model "
                    f"select/save/chat flow, got: {[(m.type, m.text) for m in console_issues]}"
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
