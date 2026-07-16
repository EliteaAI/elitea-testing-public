"""Agent icon can be changed and persists on the agents list card (ELITEA-1899).

Creates a dedicated, uniquely-named disposable agent (icon state is a
visible, shared-list-affecting mutation — per this project's Hard Rule 10
test-data guidance, a fresh instance per run is load-bearing, not
incidental, same reasoning as the ELITEA-1884/ELITEA-1888 AFS's). Opens the
icon picker from the agent detail page, selects a different default icon,
verifies the header icon updates immediately (no reload), then navigates to
the Agents dashboard and verifies the matching card shows the identical
icon URL.

Case's step 5 ("Click Save") is NOT performed literally — the icon change
persists immediately and independently via its own `PUT
.../upload_icon/.../{versionId}` call, decoupled from the agent form's
Save/Discard state (the main Save button stays disabled after an icon-only
change, since the icon field isn't formik-tracked). Asserting a literal
Save click would either no-op harmlessly or, if Save happened to be enabled
from an unrelated pending edit, trigger an unrelated save outside this
case's intent. Filed as a case-text CLARIFICATION (reverse-masking guard),
not a defect: https://github.com/EliteaAI/elitea-testing-public/issues/566

Spec: test-specs/agents/l3_agent-icon-change-persists-on-list-card_ELITEA-1899.md
"""

import uuid

import allure
import pytest

from config import settings
from pages.agent_detail_page import AgentDetailPage
from pages.agents_list_page import AgentsListPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000

# A fixed known index (not the picker's implicit default) so the test
# deterministically exercises a *change* rather than re-selecting whatever
# icon a fresh agent happens to start with.
ICON_OPTION_INDEX = 3


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Mirrors the ELITEA-1884/ELITEA-1888 pattern: uses
    ``reasoning_effort: "none"`` and omits ``temperature`` entirely so agent
    creation does not hit the open #524 defect (`temperature` is not allowed
    together with a `reasoning_effort` other than 'none' on the project's
    reasoning-capable default model, which ``AgentAPI.create_agent()``'s
    convenience payload always sends). This does not "fix" #524 — it simply
    avoids the known-bad combination in this test's own fixture payload.
    """
    return {
        "name": name,
        "description": "Agent for ELITEA-1899 icon change persistence check",
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
                "meta": {"step_limit": 25},
            }
        ],
    }


class TestAgentIconManagement:
    """Agent icon can be changed and persists on the agents list card (ELITEA-1899, p3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1899_agent-icon-change-persists-on-list-card.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    @pytest.mark.regression
    def test_agent_icon_change_persists_on_list_card(self, page, agent_api):
        """Selecting a new icon in the picker updates the header immediately
        and the identical icon persists on the agent's dashboard card."""
        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1899-icon-{uuid.uuid4().hex[:8]}"[:32]
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        detail_page = AgentDetailPage(page)
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )
        icon_requests = detail_page.capture_requests_matching("upload_icon", method="PUT")

        try:
            with allure.step("Step 1 — Navigate to the agent detail page"):
                detail_page.navigate(agent_id)
                assert detail_page.get_name() == agent_name, (
                    "Agent detail page should show the newly created agent"
                )

            with allure.step(
                "Step 2 — Click the agent icon (hover first) — icon picker opens"
            ):
                # AUTOMATION QUIRK (ELITEA-1899 AFS, not a product defect): the
                # icon's clickable state only mounts once its hover-triggered
                # edit-pencil overlay is rendered — a bare single .click() with
                # no prior .hover() only triggers the hover state and does not
                # open the dialog. open_icon_picker() hovers before clicking.
                detail_page.open_icon_picker(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.icon_picker_dialog.is_visible(), (
                    "Icon picker dialog should be open after hover + click"
                )

            with allure.step("Step 3 — Select a different icon from the picker"):
                previous_src = detail_page.get_header_icon_src(timeout=2000)
                new_src = detail_page.select_icon_option(
                    ICON_OPTION_INDEX, timeout=UI_ELEMENT_TIMEOUT
                )
                assert new_src != previous_src, (
                    "Selecting a different icon option should change the header icon src"
                )
                resolved = [r for r in icon_requests if r["status"] is not None]
                assert resolved and resolved[-1]["status"] == 200, (
                    "PUT .../upload_icon/... should return 200 for the icon "
                    f"selection, captured: {icon_requests!r}"
                )

            with allure.step(
                "Step 4 — New icon is shown in the agent header immediately (no reload)"
            ):
                assert detail_page.get_header_icon_src(timeout=2000) == new_src, (
                    "Header icon src should match the just-selected icon with no reload"
                )

            with allure.step(
                "Step 5 — CLARIFICATION (issue #566, not a defect): the icon "
                "change already persisted via its own PUT call in Step 3 — "
                "there is no separate 'click Save' action for this field. "
                "The main Save button stays disabled after an icon-only change "
                "since the icon field is not formik-tracked"
            ):
                assert not detail_page.is_save_enabled(), (
                    "Save button should remain disabled after an icon-only "
                    "change — the icon persists independently via its own "
                    "PUT call, not through the form's Save/Discard state"
                )

            with allure.step("Step 6 — Navigate to the Agents dashboard"):
                list_page = AgentsListPage(page)
                list_page.navigate()
                assert list_page.agent_exists_in_list(agent_name), (
                    "Newly-edited agent should appear on the Agents dashboard"
                )

            with allure.step(
                "Step 7 — Agent card shows the newly selected icon (exact src match)"
            ):
                card_src = list_page.get_card_icon_src(agent_name, timeout=UI_ELEMENT_TIMEOUT)
                assert card_src == new_src, (
                    "Agent card icon src should exactly match the header icon "
                    f"src set in Step 3/4 — expected {new_src!r}, got {card_src!r}"
                )

            assert not console_errors, (
                "Expected no console errors across the icon-change flow, got: "
                f"{[m.text for m in console_errors]}"
            )
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                try:
                    agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")
