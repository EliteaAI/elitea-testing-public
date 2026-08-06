"""LLM selector — OpenAI models are available and functional (ELITEA-1882).

Verifies that four of the five case-named OpenAI models (GPT-5 mini, GPT-5.2,
GPT-5.4, GPT-5.4-mini) are present in the agent detail page's LLM model
selector dropdown, can each be selected, persisted via Save (asserted at the
network level — PUT .../application/prompt_lib/... -> 201), and are
functional in the embedded chat panel (each produces a "CONFIRMED" response
correctly attributed to the selected model).

The case's fifth named model, GPT-4.1, does NOT exist in the platform's
current model catalog (confirmed live via both the dropdown DOM and
GET /api/v2/configurations/models/{project}) — this is case-text drift, not
a defect, filed as a CLARIFICATION:
https://github.com/EliteaAI/elitea-testing-public/issues/1285. This test
intentionally asserts only the 4 present models and does not assert
GPT-4.1's absence as a hard invariant (per AFS Automation Hints — a future
re-add of GPT-4.1 to the catalog should not fail this test).

This test drives 4 real, serial LLM round-trips (select -> save -> send ->
await-response, once per model) against live OpenAI-backed models via the
platform's LLM proxy — see AI_RESPONSE_TIMEOUT below for the generous
per-response wait budget this requires (per AFS Automation Hints).

Test-data strategy (per AFS): mirrors the ELITEA-1881 pattern — this test
creates a **dedicated, uniquely-named agent** for each run via
``AgentAPI.create_agent_full()`` rather than mutating the shared "Test Agent"
fixture, to avoid xdist races on that agent's LLM selection across parallel
test runs. The agent is deleted at teardown via ``delete_agent_via_menu()``.

Spec: test-specs/agents/l2_llm-selector-openai-models_ELITEA-1882.md
"""

import uuid

import allure
import pytest
from config import settings
from pages.agent_detail_page import AgentDetailPage
from playwright.sync_api import Page, Response

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
SAVE_RESPONSE_TIMEOUT = 15_000
# Live LLM inference, not just message delivery — AFS observed ~15-25s per
# model round trip; a generous override well above the project default is
# needed to absorb latency variance without flaking (AFS Automation Hints).
AI_RESPONSE_TIMEOUT = 60_000

TEST_MESSAGE = "Reply only with: CONFIRMED"
EXPECTED_RESPONSE_SUBSTRING = "CONFIRMED"

# The 4 case-named OpenAI models actually present in the live model catalog,
# by their dropdown DISPLAY name. OpenAI models carry NO vendor prefix
# (unlike the Anthropic/Azure entries in ELITEA-1881) — confirmed live via
# GET /api/v2/configurations/models/{project}?include_shared=true (AFS
# Network Behavior). GPT-4.1, the case's 5th named model, is absent from the
# catalog entirely — see module docstring / AFS Coverage Map clarification;
# it is deliberately NOT included here.
OPENAI_MODEL_DISPLAY_NAMES = [
    "GPT-5 mini",
    "GPT-5.2",
    "GPT-5.4",
    "GPT-5.4-mini",
]


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the open #524-class defect (`temperature`
    not allowed together with a `reasoning_effort` other than 'none' on the
    project's reasoning-capable default model) — mirrors the same payload
    shape used by ``test_agent_llm_selector_anthropic_models.py`` (ELITEA-1881).
    The initial model is irrelevant to this case — every case step re-selects
    the model under test via the UI before saving.
    """
    return {
        "name": name,
        "description": "Auto-created for ELITEA-1882 LLM selector test",
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


class TestAgentLlmSelectorOpenaiModels:
    """LLM selector — OpenAI models are available and functional (ELITEA-1882, p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1882_llm-selector-openai-models-are-available-and-functional.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    @pytest.mark.slow
    def test_llm_selector_openai_models_are_available_and_functional(
        self, page: Page, agent_api
    ):
        """The 4 present OpenAI models are listed in the LLM selector, each
        can be selected + saved (201 on the Save PUT), and each produces a
        "CONFIRMED" response in the embedded chat, correctly attributed to
        the selected model. GPT-4.1 (case-named, absent from the live
        catalog) is deliberately not exercised — see module docstring."""
        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1882-llm-{uuid.uuid4().hex[:8]}"
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
                    OPENAI_MODEL_DISPLAY_NAMES[0], timeout=UI_ELEMENT_TIMEOUT
                ), "Model selector dropdown should be open with options visible"

            with allure.step(
                "Step 3 — Verify all four present OpenAI models are listed in the dropdown"
            ):
                for display_name in OPENAI_MODEL_DISPLAY_NAMES:
                    assert detail_page.is_model_option_visible(
                        display_name, timeout=UI_ELEMENT_TIMEOUT
                    ), f"Model selector dropdown should list {display_name!r}"

            # Close the dropdown before the per-model select/save/chat loop below
            # re-opens it explicitly for each model.
            detail_page.close_model_selector(timeout=UI_ELEMENT_TIMEOUT)

            step_labels = {1: "Step 4-6", 2: "Step 7", 3: "Step 9", 4: "Step 10"}
            for i, display_name in enumerate(OPENAI_MODEL_DISPLAY_NAMES, start=1):
                step_label = step_labels[i]
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
                    # "GPT-5.4" is a literal substring of "GPT-5.4-mini" (unlike
                    # the Anthropic model names in ELITEA-1881, which don't
                    # overlap) — exclude any other model name that is itself a
                    # substring of the currently-selected model's display name,
                    # since a containment check there would always trivially
                    # fail regardless of actual attribution.
                    other_models = [
                        m
                        for m in OPENAI_MODEL_DISPLAY_NAMES
                        if m != display_name and m not in display_name
                    ]
                    for other in other_models:
                        assert other not in full_message_text, (
                            f"Response for {display_name!r} should NOT be "
                            f"attributed to a different model {other!r}"
                        )

            with allure.step("Verify no console errors or warnings across the full flow"):
                assert not console_issues, (
                    "Expected no console errors/warnings across the 4-model "
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
