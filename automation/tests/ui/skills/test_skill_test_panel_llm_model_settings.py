"""LLM model settings are configurable in the Skill test panel (ELITEA-2436).

Verifies the Skill test panel's model-settings gear control opens a "Model
settings" dialog whose contents adapt to the selected model's capabilities:
a Creativity slider for a non-reasoning model (e.g. ``gpt-5-mini``), and a
Reasoning slider (Low/Medium/High) for a reasoning-capable model (e.g.
``GPT-5.2``). Also verifies a test prompt runs without error while a
non-reasoning model is selected.

This drives the exact same shared ``LLMModelSelector``/``LLMSettingsDialog``
React component as ELITEA-1880 (Agent detail page), but from the Skill test
panel (``SkillDetailPage``/``SkillTestPanel``) — a different screen/page
object, so this is a fresh spec rather than an extension of the ELITEA-1880
test (see the AFS's "Relationship to ELITEA-1880" section for the full
merged-target analysis).

Test-data strategy (per AFS): reuse the pre-existing, shared fixture skill
``elitea-1735-skill-underscore`` (owned by the ELITEA-1735 suite) read-only —
model selection and Settings-dialog edits inside the test panel are pure
client-side state with zero network calls (confirmed live during AFS
analysis), so there is nothing to clean up. Falls back to creating a
disposable skill (with teardown) if that fixture skill is ever absent from
the environment.

Spec: test-specs/skills/l3_llm-model-settings-configurable_ELITEA-2436.md
"""

import logging

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage
from playwright.sync_api import Page, Response

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p3, pytest.mark.regression]

logger = logging.getLogger("elitea.tests.skills")

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
PREDICT_RESPONSE_TIMEOUT = 30_000
AI_RESPONSE_TIMEOUT = 60_000

# Shared, pre-existing fixture skill (owned by the ELITEA-1735 suite) — read
# only, per AFS § Test Data / § Cleanup: model settings interactions never
# mutate the skill entity, so any existing skill is safe to reuse.
SHARED_FIXTURE_SKILL_NAME = "elitea-1735-skill-underscore"

# Disposable-skill fallback payload, used only if the shared fixture skill is
# absent from this environment.
FALLBACK_SKILL_NAME_PREFIX = "elitea-2436-model-settings"
FALLBACK_SKILL_DESCRIPTION = "Auto-created for ELITEA-2436 model-settings test (fallback)"
FALLBACK_SKILL_INSTRUCTIONS = "You are a helpful assistant. Answer concisely."

# A non-reasoning model (case's own suggested example) — renders the
# Creativity slider, not Reasoning (AFS Coverage Map step-2 clarification).
NON_REASONING_MODEL_NAME = "gpt-5-mini"
NON_REASONING_MODEL_DISPLAY_NAME = "GPT-5 mini"

# A reasoning-capable model — renders the Reasoning slider with 3 discrete
# Low/Medium/High positions (the case's own stated Pass/Objective criterion).
REASONING_MODEL_NAME = "gpt-5.2"
REASONING_MODEL_DISPLAY_NAME = "GPT-5.2"
REASONING_LEVEL_LABELS = ("low", "medium", "high")

TEST_MESSAGE = "Say OK"
# AFS step 3 observed this literal — "OK" — as the exact response. Implementer
# re-verification found this is NOT stable: the reused fixture skill's own
# instructions ("replace ALL spaces between words with underscore
# characters") apply unconditionally in the SkillTestPanel (it always runs
# the skill's instructions against the input — unlike agent-level V2
# autonomous invocation, there's no separate trigger-match gate here), so the
# LLM's literal-vs-instruction-following interpretation of "Say OK" is
# genuinely non-deterministic across runs/models: observed "OK" during AFS
# analysis, observed "Say_OK" during implementation re-verification. The
# case's own Pass criterion only requires "action completes without error and
# produces the expected UI state" — asserting a SUBSTRING match instead of an
# exact literal keeps the test honest to that criterion without being
# sensitive to which of the two valid interpretations the LLM produces.
EXPECTED_TEST_RESPONSE = "OK"


def _is_predict_response(response: Response) -> bool:
    """Match the skill test-panel's predict call: `.../predict_llm/prompt_lib/{project}`."""
    return "predict_llm/prompt_lib" in response.url and response.request.method == "POST"


def _is_skill_entity_mutation(request) -> bool:
    """Match a PUT/PATCH to the skill ENTITY endpoint (singular `/skill/`,
    not the plural `/skills/` list endpoint) — used to prove model-selector
    and Settings-dialog edits never persist to the skill (AFS § Network
    Behavior: pure client-side state)."""
    return (
        "/elitea_core/skill/prompt_lib/" in request.url
        and request.method in ("PUT", "PATCH")
    )


def _is_known_disabled_tooltip_warning(msg) -> bool:
    """Pre-existing, unrelated MUI warning traced to the test panel's
    disabled "Clear the chat" button (AFS § Known Defects/Observations) —
    not caused by anything this case's steps touch. Filtered so the
    side-channel check stays honest about what THIS case's flow produces."""
    text = msg.text or ""
    return "disabled" in text and "Tooltip" in text and "button" in text.lower()


def _get_or_create_test_skill(skill_api) -> tuple[int, bool]:
    """Return (skill_id, created_disposable) for the case's test skill.

    Prefers the shared, pre-existing fixture skill (read-only reuse, no
    cleanup needed — AFS § Test Data). Falls back to creating a disposable
    skill (caller must clean up) only if that fixture is absent.
    """
    for skill in skill_api.list_skills().get("rows", []):
        if skill.get("name") == SHARED_FIXTURE_SKILL_NAME:
            skill_id = skill["id"]
            logger.info(
                "Reusing shared fixture skill %r (id=%d)",
                SHARED_FIXTURE_SKILL_NAME, skill_id,
            )
            return skill_id, False

    import uuid

    name = f"{FALLBACK_SKILL_NAME_PREFIX}-{uuid.uuid4().hex[:8]}"
    logger.warning(
        "Shared fixture skill %r not found — creating disposable fallback %r",
        SHARED_FIXTURE_SKILL_NAME, name,
    )
    created = skill_api.create_skill(
        name=name,
        description=FALLBACK_SKILL_DESCRIPTION,
        instructions=FALLBACK_SKILL_INSTRUCTIONS,
    )
    return created["id"], True


class TestSkillTestPanelLlmModelSettings:
    """LLM model settings are configurable — Skill test panel (ELITEA-2436, p3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-2436_llm-model-settings-configurable.md",
        "onetest-ai Test Case link",
    )
    @allure.link(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1447",
        name="Clarification: step 2's 'reasoning slider' wording for a non-reasoning model",
    )
    def test_llm_model_settings_configurable(self, page: Page, skill_api):
        """Model settings dialog adapts to the selected model's capabilities
        (Creativity slider for a non-reasoning model, Reasoning slider for a
        reasoning-capable model), controls respond to interaction, and a
        test prompt runs without error."""
        skill_id, created_disposable = _get_or_create_test_skill(skill_api)

        # Dual listener (console + pageerror), registered BEFORE step 1 —
        # per the project's console side-channel-check idiom.
        console_issues, page_errors = [], []

        def _on_console(msg):
            if msg.type in ("error", "warning") and not _is_known_disabled_tooltip_warning(msg):
                console_issues.append(msg)

        page.on("console", _on_console)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        # Track any PUT/PATCH to the skill entity across the whole flow —
        # model selection / Settings-dialog edits must never fire one.
        skill_mutation_requests = []
        page.on(
            "request",
            lambda req: skill_mutation_requests.append(req)
            if _is_skill_entity_mutation(req)
            else None,
        )

        detail_page = SkillDetailPage(page)

        try:
            with allure.step("Step 1 — Open the Skill and locate model settings in the test panel"):
                detail_page.navigate(skill_id)
                assert detail_page.model_selector_button.is_visible(), (
                    "Model selector button should be visible in the test panel"
                )
                assert detail_page.model_settings_button.is_visible(), (
                    "Model settings (gear) button should be visible next to the model selector"
                )

                detail_page.open_model_settings_dialog(timeout=UI_ELEMENT_TIMEOUT)
                dialog_text = detail_page.model_settings_dialog.text_content() or ""
                assert "Model settings" in dialog_text, (
                    f"Model settings dialog should be titled 'Model settings', got: {dialog_text!r}"
                )
                detail_page.close_model_settings_dialog_via_cancel(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 2 — Select a standard (non-reasoning) model and adjust its "
                "settings control (Creativity slider — see Clarification 1447 "
                "for why 'reasoning slider' does not apply to gpt-5-mini)"
            ):
                detail_page.open_model_selector(timeout=UI_ELEMENT_TIMEOUT)
                detail_page.select_llm_model(NON_REASONING_MODEL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.get_selected_model_name() == NON_REASONING_MODEL_DISPLAY_NAME, (
                    f"Model selector should show {NON_REASONING_MODEL_DISPLAY_NAME!r} "
                    "after selection"
                )

                detail_page.open_model_settings_dialog(timeout=UI_ELEMENT_TIMEOUT)
                assert not detail_page.is_reasoning_slider_visible(timeout=2000), (
                    f"{NON_REASONING_MODEL_DISPLAY_NAME!r} is NOT reasoning-capable — the "
                    "dialog should NOT render the Reasoning slider"
                )
                assert detail_page.is_creativity_slider_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    f"{NON_REASONING_MODEL_DISPLAY_NAME!r} should render the Creativity "
                    "slider instead of the Reasoning slider"
                )

                value_before = detail_page.get_creativity_slider_value()
                assert not detail_page.is_apply_button_enabled(timeout=UI_ELEMENT_TIMEOUT), (
                    "Apply should be disabled before any settings change"
                )

                detail_page.increase_creativity_slider(timeout=UI_ELEMENT_TIMEOUT)

                value_after = detail_page.get_creativity_slider_value()
                assert value_after == value_before + 1, (
                    "Creativity slider value should move by one discrete position "
                    f"after ArrowRight, got {value_before} -> {value_after}"
                )
                assert detail_page.is_apply_button_enabled(timeout=UI_ELEMENT_TIMEOUT), (
                    "Apply should become enabled once the Creativity slider value changes"
                )

                detail_page.click_apply_model_settings(timeout=UI_ELEMENT_TIMEOUT)
                assert not detail_page.model_settings_dialog.is_visible(), (
                    "Model settings dialog should close after Apply"
                )
                assert not skill_mutation_requests, (
                    "Model selection / Settings-dialog edits should never PUT/PATCH "
                    f"the skill entity (pure client-side state), got: "
                    f"{[r.url for r in skill_mutation_requests]}"
                )

            with allure.step("Step 3 — Run a test — verify no error occurs"):
                initial_count = detail_page.get_test_message_count()
                with page.expect_response(
                    _is_predict_response, timeout=PREDICT_RESPONSE_TIMEOUT
                ) as predict_response_info:
                    detail_page.send_test_message(TEST_MESSAGE, timeout=UI_ELEMENT_TIMEOUT)
                predict_response = predict_response_info.value
                assert predict_response.status == 200, (
                    f"predict_llm POST should return 200, got {predict_response.status}"
                )

                detail_page.wait_for_test_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT
                )
                response_text = detail_page.get_last_test_response()
                assert response_text, (
                    "Test panel should produce a non-empty response to the test message"
                )
                assert "error" not in response_text.lower(), (
                    f"Test response should not indicate an error, got: {response_text!r}"
                )
                assert EXPECTED_TEST_RESPONSE.lower() in response_text.lower(), (
                    f"Test response should reflect the sent message ({TEST_MESSAGE!r}) — "
                    f"the reused fixture skill's own instructions (replace spaces with "
                    f"underscores) may transform the literal text (e.g. 'Say_OK' rather "
                    f"than a bare 'OK' — see implementer note below), so this checks a "
                    f"substring rather than an exact match; got: {response_text!r}"
                )

            with allure.step(
                "Step 4 — Switch to a reasoning model and verify reasoning effort "
                "options (Low/Medium/High) appear"
            ):
                detail_page.open_model_selector(timeout=UI_ELEMENT_TIMEOUT)
                detail_page.select_llm_model(REASONING_MODEL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.get_selected_model_name() == REASONING_MODEL_DISPLAY_NAME, (
                    f"Model selector should show {REASONING_MODEL_DISPLAY_NAME!r} after selection"
                )

                detail_page.open_model_settings_dialog(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.is_reasoning_slider_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    f"{REASONING_MODEL_DISPLAY_NAME!r} is reasoning-capable — the dialog "
                    "should render the Reasoning slider"
                )
                # Case-insensitive: the slider's raw DOM text is lowercase
                # ("low"/"medium"/"high"); CSS text-transform renders it
                # capitalized visually (same as ELITEA-1880's Clarification 2).
                reasoning_text = detail_page.get_reasoning_slider_text().lower()
                for label in REASONING_LEVEL_LABELS:
                    assert label in reasoning_text, (
                        f"Reasoning slider should show the {label!r} level, got: {reasoning_text!r}"
                    )

                # Confirm all 3 discrete level marks are individually present too.
                for level in (1, 2, 3):
                    mark = page.locator(
                        detail_page.MODEL_SETTINGS_REASONING_LEVEL.format(level)
                    )
                    assert mark.count() == 1, (
                        f"Reasoning slider level mark {level} should be present"
                    )

            with allure.step("Verify no console errors or warnings across the full flow"):
                assert not console_issues and not page_errors, (
                    "Expected no console errors/warnings or page errors across the "
                    f"model-settings flow, got console={[(m.type, m.text) for m in console_issues]} "
                    f"page_errors={page_errors}"
                )
        finally:
            if created_disposable:
                with allure.step("Cleanup — delete the disposable fallback skill"):
                    try:
                        skill_api.delete_skill(skill_id)
                    except Exception as cleanup_exc:
                        logger.warning(
                            "Cleanup failed for disposable skill id=%s: %s", skill_id, cleanup_exc
                        )
