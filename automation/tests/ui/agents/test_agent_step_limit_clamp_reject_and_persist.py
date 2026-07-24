"""Agent — Advanced Settings: Step limit accepts value, clamps to 0-999,
blocks non-numeric input, and persists (GAP-003).

GAP-003 is a coverage-gap campaign card (cov60), not an onetest TMS case —
source: ``.agents/automation-board/batches/cov60/cases/GAP-003/source.md``.
Coverage target: ``ApplicationAdvanceSettings.jsx``'s ``isValidStepLimit`` /
``isValidKeyInput`` branches (empty/NaN/>MAX/<MIN/valid, navigation/digit-gate
/reject).

Test-data strategy (per AFS): creates a **dedicated, uniquely-named agent**
via ``AgentAPI.create_agent_full()`` with ``meta: {"step_limit": None}`` —
load-bearing: omitting the key entirely makes the backend default
``step_limit`` to 25, only an explicit ``null`` produces the empty starting
field this case's Step 1 requires. Mirrors the ``reasoning_effort: "none"`` /
omit-``temperature`` pattern already used by
``test_agent_add_variables_persist_after_reload.py`` to avoid the known-bad
``agent_id`` fixture payload (issue #563). The agent is deleted at teardown
via ``delete_agent_via_menu()``.

Spec: test-specs/agents/l3_step-limit-clamp-reject-and-persist_GAP-003.md
"""

import uuid

import allure
import pytest
from config import settings
from pages.agent_detail_page import AgentDetailPage
from playwright.sync_api import Page, Response, expect

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000
SAVE_RESPONSE_TIMEOUT = 15000

# ---------------------------------------------------------------------------
# Test data (per AFS § Test Data)
# ---------------------------------------------------------------------------
MAX_STEP_LIMIT = 999
MIN_STEP_LIMIT = 0
VALID_VALUE = "25"
OVER_MAX_VALUE = "1500"  # pasted -> expected clamp 999
UNDER_MIN_VALUE = "-5"  # pasted -> expected clamp 0

# Pre-existing, unrelated 403 burst that fires on every agent-detail-page
# load in this local environment (project id 471) regardless of feature —
# already documented as not-a-defect in the ELITEA-1880/1893 AFS files.
# Excluded explicitly from the "no console errors" assertions below.
_EXPECTED_NOISE_PATTERNS = ("secrets/secrets/default", "upload_icon/prompt_lib")


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload with ``meta.step_limit`` explicitly ``None``.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the ``agent_id`` fixture's known-bad payload
    (issue #563) — this does not "fix" #563, it simply avoids the known-bad
    combination in this test's own fixture payload.

    ``meta: {"step_limit": None}`` is the load-bearing part: omitting the key
    entirely makes the backend default ``step_limit`` to 25 (confirmed live
    per the AFS), which would fail Step 1's "field is empty" precondition.
    """
    return {
        "name": name,
        "description": "Auto-created for GAP-003 step-limit test",
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [],
                "instructions": "",
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
                "meta": {"step_limit": None},
            }
        ],
    }


def _is_save_response(response: Response) -> bool:
    """Match the agent Save PUT: `.../application/prompt_lib/{project}/{id}`."""
    return (
        "application/prompt_lib" in response.url
        and response.request.method == "PUT"
    )


def _is_expected_noise(message_text: str) -> bool:
    """Match the pre-existing, unrelated 403 burst (project id 471) that
    fires on every agent-detail-page load in this environment, unrelated to
    Step limit — see module docstring."""
    return any(pattern in message_text for pattern in _EXPECTED_NOISE_PATTERNS)


class TestAgentStepLimitClampRejectAndPersist:
    """Step limit: accept + persist, clamp over/under bounds, reject
    non-numeric input, clear-to-empty (GAP-003, p2)."""

    @pytest.mark.p2
    @pytest.mark.regression
    def test_step_limit_accepts_clamps_rejects_and_persists(self, page: Page, agent_api):
        """A valid Step limit is accepted and persists after reload; a
        pasted over-max value clamps to 999; a pasted under-min value clamps
        to 0; typed letters/symbols are rejected at keydown without
        "sticking" the field; clearing the field leaves it empty with no
        validation error."""
        with allure.step("Precondition — create a dedicated disposable agent with meta.step_limit=null"):
            agent_name = f"gap003-step-limit-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        detail_page = AgentDetailPage(page)
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        def assert_no_unexpected_console_errors(step_label: str):
            unexpected = [m for m in console_errors if not _is_expected_noise(m.text)]
            assert not unexpected, (
                f"Expected no console errors attributable to Step-limit interactions "
                f"after {step_label}, got: {[m.text for m in unexpected]}"
            )

        try:
            with allure.step(
                "Step 1 — Navigate to the dedicated agent's detail page in "
                "owner/edit mode; Advanced accordion already expanded, Step "
                "limit input visible and empty"
            ):
                detail_page.navigate(agent_id)
                assert detail_page.is_advanced_section_expanded(), (
                    "Advanced accordion should be expanded by default "
                    "(BasicAccordion defaultExpanded=true) with zero clicks"
                )
                assert detail_page.step_limit_input.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Step limit input should be visible in the Advanced accordion"
                )
                assert detail_page.get_step_limit() == "", (
                    "Step limit should start empty when meta.step_limit was "
                    "created as null"
                )

            with allure.step(f"Step 2 — Type '{VALID_VALUE}' into the Step limit field"):
                detail_page.type_step_limit(VALID_VALUE)
                assert detail_page.get_step_limit() == VALID_VALUE, (
                    f"Step limit field should show '{VALID_VALUE}' after typing"
                )

            with allure.step(
                "Step 3 — Save, reload (full navigation); value persists in "
                "both the Save response body and the DOM"
            ):
                with page.expect_response(
                    _is_save_response, timeout=SAVE_RESPONSE_TIMEOUT
                ) as response_info:
                    detail_page.click_save(timeout=UI_ELEMENT_TIMEOUT)
                save_response = response_info.value
                assert save_response.status == 201, (
                    "PUT application/prompt_lib/... should return 201 on Save, "
                    f"got {save_response.status}"
                )
                saved_step_limit = save_response.json()["version_details"]["meta"]["step_limit"]
                assert saved_step_limit == int(VALID_VALUE), (
                    "Save response body's version_details.meta.step_limit "
                    f"should be {VALID_VALUE}, got {saved_step_limit!r}"
                )

                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                assert detail_page.get_step_limit() == VALID_VALUE, (
                    f"Step limit should still read '{VALID_VALUE}' after a "
                    "full-navigation reload"
                )
                assert_no_unexpected_console_errors("Save + reload")

            with allure.step(
                f"Step 4 — Clear the field, then paste '{OVER_MAX_VALUE}' "
                f"(clamps to {MAX_STEP_LIMIT})"
            ):
                detail_page.clear_step_limit()
                assert detail_page.get_step_limit() == "", (
                    "Step limit should be empty after clear"
                )
                detail_page.paste_step_limit(OVER_MAX_VALUE)
                assert detail_page.get_step_limit() == str(MAX_STEP_LIMIT), (
                    f"Pasting '{OVER_MAX_VALUE}' should clamp to "
                    f"{MAX_STEP_LIMIT}, got {detail_page.get_step_limit()!r}"
                )

            with allure.step(
                f"Step 5 — Clear the field, then paste '{UNDER_MIN_VALUE}' "
                f"(clamps to {MIN_STEP_LIMIT})"
            ):
                detail_page.clear_step_limit()
                assert detail_page.get_step_limit() == "", (
                    "Step limit should be empty after clear"
                )
                detail_page.paste_step_limit(UNDER_MIN_VALUE)
                assert detail_page.get_step_limit() == str(MIN_STEP_LIMIT), (
                    f"Pasting '{UNDER_MIN_VALUE}' should clamp to "
                    f"{MIN_STEP_LIMIT}, got {detail_page.get_step_limit()!r}"
                )

            with allure.step(
                "Step 6 — Clear the field, then type 'a', 'b', '-' one at a "
                "time: each keystroke is rejected and the field stays "
                "unchanged; a valid digit typed immediately afterward still "
                "works (field is not stuck); Backspace/Arrow/Tab remain "
                "functional (isValidKeyInput's navigation-keys allowlist)"
            ):
                detail_page.clear_step_limit()
                assert detail_page.get_step_limit() == "", (
                    "Step limit should be empty before the reject sequence"
                )

                for rejected_char in ("a", "b", "-"):
                    detail_page.type_step_limit(rejected_char)
                    assert detail_page.get_step_limit() == "", (
                        f"Typing '{rejected_char}' should be rejected at "
                        "keydown — the field should remain empty, got "
                        f"{detail_page.get_step_limit()!r}"
                    )

                # Field must not be "stuck" after the rejected sequence —
                # confirmed live with both a single digit and a two-digit
                # value (AFS Redispatch confirmations, Pass 1 + Pass 2).
                detail_page.type_step_limit("7")
                assert detail_page.get_step_limit() == "7", (
                    "Field should still accept a valid digit immediately "
                    "after a rejected keystroke"
                )
                detail_page.clear_step_limit()
                detail_page.type_step_limit("42")
                assert detail_page.get_step_limit() == "42", (
                    "Field should still accept a full valid value "
                    "immediately after the earlier rejected sequence"
                )

                # Navigation keys (Backspace/Arrow/Tab) — isValidKeyInput's
                # navigationKeys allowlist (ApplicationAdvanceSettings.jsx)
                # returns True for these without calling preventDefault,
                # unlike the reject branch above. Distinct requirement from
                # "a digit still works after a rejected keystroke": this
                # proves the specific navigation keys the case names remain
                # functional, not merely that digits do.
                detail_page.clear_step_limit()
                detail_page.type_step_limit("25")
                assert detail_page.get_step_limit() == "25"

                detail_page.press_step_limit_key("Backspace")
                assert detail_page.get_step_limit() == "2", (
                    "Backspace should delete the last character — proves "
                    "the navigation-keys allowlist doesn't block it, got "
                    f"{detail_page.get_step_limit()!r}"
                )

                # ArrowLeft moves the caret before the remaining digit;
                # typing '9' there produces '92' only if the caret actually
                # moved — a direct, functional check that Arrow keys are not
                # blocked (as opposed to merely "nothing visibly broke").
                detail_page.press_step_limit_key("ArrowLeft")
                detail_page.press_step_limit_key("9")
                assert detail_page.get_step_limit() == "92", (
                    "ArrowLeft should move the caret before the remaining "
                    "digit, so typing '9' there should produce '92', got "
                    f"{detail_page.get_step_limit()!r}"
                )

                # Tab's native focus-move behavior only fires if
                # isValidKeyInput did NOT call preventDefault for it — if
                # Tab were incorrectly blocked, focus would stay stuck on
                # the input.
                detail_page.press_step_limit_key("Tab")
                expect(detail_page.step_limit_input).not_to_be_focused(
                    timeout=UI_ELEMENT_TIMEOUT
                )

                assert_no_unexpected_console_errors(
                    "non-numeric reject + navigation-key sequence"
                )

            with allure.step(
                "Step 7 — Select-all + Delete so the field is empty, with "
                "no validation error"
            ):
                detail_page.clear_step_limit()
                assert detail_page.get_step_limit() == "", (
                    "Step limit should be empty after select-all + delete"
                )
                assert not detail_page.is_step_limit_invalid(), (
                    "Step limit should NOT show a validation error when "
                    "empty — empty is a valid state per isValidStepLimit('')"
                )
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                try:
                    if "/agents/all/" in detail_page.page.url:
                        detail_page.delete_agent_via_menu(timeout=NAVIGATION_TIMEOUT)
                    else:
                        agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")
