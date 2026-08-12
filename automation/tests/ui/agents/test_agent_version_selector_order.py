"""Version selector lists all versions in correct order with expected
metadata (ELITEA-1891).

Builds a dedicated, disposable agent with a deliberately ordered version
sequence — ``base`` (Draft, initially pinned) -> ``v1-early-draft`` (Draft)
-> ``v2-published`` (Published, via Publish) -> ``v3-latest-draft`` (Draft,
newest) -> re-pin ``v1-early-draft`` as the default — then opens the VERSION
dropdown and verifies every ordering rule and metadata field in one pass.

Case-text drift (CLARIFICATION, filed as
https://github.com/EliteaAI/elitea-testing-public/issues/1091): the TMS case
describes a three-tier ordering (Pinned -> Published -> Draft -> base). The
live sort algorithm (``VersionSelect.jsx``'s ``versionSelectOptions``
comparator) has no Published/Draft status tier at all — the real rule is
``[pinned] -> [everything else by created_at descending, Published/Draft
interleaved] -> [base, unless base is itself pinned]``. This test asserts the
real rule (Step 7), not the case's literal wording — reverse-masking guard,
live product behavior is correct.

Two new testids were added for this case (EliteaUI automation/testids commit
4e5b819d):
- ``version-option-pin-icon`` — scoped inside the already-testid'd
  ``version-option-{name}`` parent (``version.helpers.jsx``'s
  ``buildVersionOption()``).
- ``agent-set-default-version-confirm-button`` — wired via a
  ``confirmButtonTestId`` prop at THIS page's own call site
  (``useSetDefaultVersion.hooks.jsx``), since ``SetDefaultVersionDialog.jsx``
  is a component shared with the Skill "Set as default" flow.

Spec: test-specs/agents/l2_version-selector-lists-all-versions-order-metadata_ELITEA-1891.md
"""

import re
import uuid

import allure
import pytest
from config import settings
from pages.agent_detail_page import AgentDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
VALIDATE_TIMEOUT = 30_000  # publish_validate is AI-backed — variable latency
PUBLISH_TIMEOUT = 15_000

CATEGORY_NAME = "Quality Assurance"
V1_NAME = "v1-early-draft"
V2_NAME = "v2-published"
V3_NAME = "v3-latest-draft"

OPTION_TEXT_PATTERN = re.compile(r"^(?P<name>.+) - (?P<date>\d{2}\.\d{2}\.\d{4})$")


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the open #524 defect — same workaround as
    ELITEA-1888/1892's payloads. Seeds substantive Instructions text and a
    non-empty Tag directly in the creation payload (AFS § Automation Hints)
    so the Publish wizard's AI ``publish_validate`` content-quality gate
    passes on the FIRST ``Continue`` click, avoiding flakiness risk.
    """
    return {
        "name": name,
        "description": "Disposable agent for ELITEA-1891 version-order test",
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [{"name": "regression"}],
                "instructions": (
                    "You are a helpful QA validation assistant for the "
                    "ELITEA platform version-ordering test (ELITEA-1891). "
                    "You answer general questions about testing status."
                ),
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


class TestAgentVersionSelectorOrder:
    """Version selector lists all versions in correct order with expected
    metadata (ELITEA-1891, l2/p1)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1891_version-selector-lists-all-versions-in-correct-order.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1091",
        "CLARIFICATION #1091 — ordering rule case-text drift",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_version_selector_lists_versions_in_correct_order(self, page, agent_api):
        """The VERSION dropdown lists all versions with name+date metadata,
        Draft versions above an unpinned base, base last when unpinned, and
        the pinned/default version at the top with a pin icon — with no
        independent Published-before-Draft tier (CLARIFICATION #1091)."""
        with allure.step("Precondition — create a dedicated disposable agent ('base' version)"):
            agent_name = f"elitea-1891-ord-{uuid.uuid4().hex[:8]}"[:32]
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        detail_page = AgentDetailPage(page)
        try:
            with allure.step(
                "Precondition — navigate; confirm 'base' is the active version "
                "and (per Test Data purpose) already the pinned/default one"
            ):
                detail_page.navigate(agent_id)
                assert detail_page.get_version_selector_value() == "base", (
                    "New disposable agent should be showing its 'base' version"
                )

            with allure.step(
                'Precondition — edit Instructions, click "Save As Version" '
                f'to create Draft version {V1_NAME!r}'
            ):
                detail_page.instructions_input.click()
                detail_page.instructions_input.press("ControlOrMeta+End")
                detail_page.instructions_input.press_sequentially(
                    " Early draft marker.", delay=50
                )
                detail_page.save_as_version(V1_NAME, timeout=NAVIGATION_TIMEOUT)
                assert detail_page.get_version_selector_value() == V1_NAME, (
                    f"VERSION selector should show {V1_NAME!r} after Save As Version"
                )

            with allure.step(
                f"Precondition — Publish the active version ({V1_NAME!r}) as "
                f"{V2_NAME!r}, creating a Published version"
            ):
                detail_page.open_publish_wizard(timeout=UI_ELEMENT_TIMEOUT)
                detail_page.fill_publish_preparation_step(
                    V2_NAME, CATEGORY_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                validate_status = detail_page.click_publish_continue(timeout=VALIDATE_TIMEOUT)
                assert validate_status == 200, (
                    "publish_validate should return 200 (no Critical issues) — "
                    "the disposable agent was seeded with Instructions + a Tag "
                    f"precisely to satisfy the AI content-quality gate, got "
                    f"{validate_status}"
                )
                publish_status = detail_page.confirm_publish(timeout=PUBLISH_TIMEOUT)
                assert publish_status == 200, (
                    f"publish POST should return 200, got {publish_status}"
                )

            with allure.step(
                f"Precondition — explicitly re-select {V1_NAME!r} (Known defect "
                "#614: Publish's own post-publish auto-navigation is "
                "unreliable — re-selecting by name is the reliable path)"
            ):
                detail_page.select_version_by_name(V1_NAME, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                f'Precondition — "Save As Version" again from {V1_NAME!r} to '
                f"create the newest Draft version {V3_NAME!r} (no further "
                "Instructions edit needed — only creation order matters here)"
            ):
                detail_page.save_as_version(V3_NAME, timeout=NAVIGATION_TIMEOUT)
                assert detail_page.get_version_selector_value() == V3_NAME, (
                    f"VERSION selector should show {V3_NAME!r} after Save As Version"
                )

            with allure.step(
                "Precondition — confirm 'base' is STILL the pinned/default "
                "version at this point (sorts first, with a pin icon) — the "
                "state the re-pin below is about to change"
            ):
                detail_page.open_version_selector()
                order_before_repin = detail_page.get_version_option_order(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert order_before_repin[0] == "base", (
                    "'base' should still sort first (pinned/default) before "
                    f"the re-pin below, got order {order_before_repin!r}"
                )
                assert detail_page.is_version_option_pinned("base"), (
                    "'base' should still show the pin icon before the re-pin"
                )
                detail_page.close_versions_menu()

            with allure.step(
                f"Precondition — re-pin {V1_NAME!r} as the agent's default "
                "version via the actions menu's 'Set as a default'"
            ):
                detail_page.select_version_by_name(V1_NAME, timeout=UI_ELEMENT_TIMEOUT)
                set_default_status = detail_page.set_current_version_as_default(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert set_default_status == 200, (
                    "default_version PATCH should return 200, got "
                    f"{set_default_status}"
                )

            with allure.step(
                "Step 1 — Navigate to the agent with base + Draft + Published "
                "versions (built above)"
            ):
                detail_page.navigate(agent_id)
                active_version = detail_page.get_version_selector_value()
                assert active_version, (
                    "Agent detail page should load with an active version shown"
                )

            with allure.step("Step 2 — Click the version dropdown in the toolbar"):
                detail_page.open_version_selector()
                order = detail_page.get_version_option_order(timeout=UI_ELEMENT_TIMEOUT)
                assert len(order) == 4, (
                    f"VERSION dropdown should open with all 4 versions present "
                    f"as a sanity check before indexing into the order, got "
                    f"{order!r}"
                )

            with allure.step("Step 3 — Verify all versions are listed"):
                for name in ("base", V1_NAME, V2_NAME, V3_NAME):
                    assert detail_page.is_version_option_visible(
                        name, timeout=UI_ELEMENT_TIMEOUT
                    ), f"VERSION dropdown should list {name!r}"
                assert set(order) == {"base", V1_NAME, V2_NAME, V3_NAME}, (
                    f"VERSION dropdown option set should be exactly the 4 "
                    f"built versions, got {order!r}"
                )

            with allure.step(
                "Step 4 — Verify each entry shows version name and creation "
                "date (baked into the SAME text node — not a separate 'time' "
                "component despite the case text saying 'date/time')"
            ):
                option_text = detail_page.get_version_option_text(V2_NAME)
                match = OPTION_TEXT_PATTERN.match(option_text)
                assert match is not None, (
                    f"Version option text should match '{{name}} - "
                    f"{{DD.MM.YYYY}}', got {option_text!r}"
                )
                assert match.group("name") == V2_NAME, (
                    f"Version option text's name part should be {V2_NAME!r}, "
                    f"got {match.group('name')!r}"
                )

            with allure.step("Step 5 — Verify 'base' version appears last"):
                assert order[-1] == "base", (
                    "'base' should be last now that it is no longer the "
                    f"pinned/default version, got order {order!r}"
                )

            with allure.step("Step 6 — Verify Draft named versions appear above base"):
                base_index = order.index("base")
                assert order.index(V1_NAME) < base_index, (
                    f"{V1_NAME!r} (Draft) should render above 'base', got order {order!r}"
                )
                assert order.index(V3_NAME) < base_index, (
                    f"{V3_NAME!r} (Draft) should render above 'base', got order {order!r}"
                )

            with allure.step(
                "Step 7 — Verify the REAL ordering rule (CLARIFICATION #1091): "
                "no independent Published-before-Draft tier — non-pinned, "
                "non-base versions sort purely by created_at descending. "
                f"{V3_NAME!r} (Draft, created AFTER {V2_NAME!r}) legitimately "
                f"outranks {V2_NAME!r} (Published, older)"
            ):
                assert order.index(V3_NAME) < order.index(V2_NAME), (
                    f"{V3_NAME!r} (newer, Draft) should sort above {V2_NAME!r} "
                    f"(older, Published) — created_at descending, no status "
                    f"tier — got order {order!r}"
                )

            with allure.step(
                f"Step 8 — Verify the pinned/default version ({V1_NAME!r}) "
                "appears at the top with a pin icon, and (same dropdown-open, "
                "same read) that 'base' simultaneously moved to last — "
                "proving steps 5 and 8 are the SAME rule, not two independent "
                "ones"
            ):
                assert order[0] == V1_NAME, (
                    f"{V1_NAME!r} should be first (pinned/default), got order {order!r}"
                )
                assert detail_page.is_version_option_pinned(V1_NAME), (
                    f"{V1_NAME!r} should show the pin icon now that it is "
                    "the default version"
                )
                assert not detail_page.is_version_option_pinned("base"), (
                    "'base' should NOT show the pin icon anymore — the pin "
                    f"moved to {V1_NAME!r}"
                )
                detail_page.close_versions_menu()
        finally:
            with allure.step(
                "Cleanup — delete the dedicated agent (unpublish the "
                f"{V2_NAME!r} clone first — no per-version delete API)"
            ):
                try:
                    agent_api.delete_agent(agent_id)
                except Exception:
                    try:
                        agent = agent_api.get_agent(agent_id)
                        for version in agent.get("versions", []):
                            if version.get("status") == "published":
                                agent_api.unpublish_version(version["id"])
                        agent_api.delete_agent(agent_id)
                    except Exception as cleanup_exc:
                        print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")
