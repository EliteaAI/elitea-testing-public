"""UI Test for ELITEA-2358 — Agent Hub: like an agent from the expanded detail modal.

Verifies that liking/unliking an agent from the preview modal (opened by
clicking a card on `/elitea-catalog`) toggles the heart icon's active state,
increments/decrements the like count in the modal header, and persists the
change when the modal is closed and reopened, with the updated count also
reflected on the agent's card in the list view.

Spec: test-specs/agent-hub/l2_like-agent-from-expanded-detail-modal_ELITEA-2358.md

Reuses `AgentHubPage` for navigation/modal open/close and like methods
(ELITEA-2354); adds modal-specific like helpers (modal like button click,
count extraction, state assertion) to the same page object (ELITEA-2358).

Known defect (filed, non-blocking — AFS § Known Defects Found,
EliteaAI/elitea-testing-public#1215): clicking the like/unlike heart icon
fires a Redux "non-serializable value" console.error. Functionally harmless —
the like/unlike flow itself (count, icon, persistence, backend call) is
entirely correct. Same handling as ELITEA-2354 (soft assertions via
`pytest.fail()` mechanism — test stays RED until the fix ships, without
masking a genuinely new console error).

Test data: uses a pre-existing published Catalog agent ("Business Analyst",
id 31) with a known pre-existing like count — the test demonstrates the
like-state-toggle mechanism, not a specific count value. No cleanup needed
(read-only modal interaction; like state change is user-initiated preference
data that persists server-side).

Usage:
    cd automation
    pytest tests/ui/agents/test_agent_hub_like_agent_from_modal.py -v
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page, expect

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

_KNOWN_DEFECT_1215_PREFIX = (
    "A non-serializable value was detected in an action, in the path: `payload.updateFn`"
)


def _is_known_defect_1215(text: str) -> bool:
    """True for the known, filed, non-blocking Redux console error
    (EliteaAI/elitea-testing-public#1215) that fires on every like/unlike
    click. Matches on the warning's own stable text prefix.
    """
    return _KNOWN_DEFECT_1215_PREFIX in text


class TestAgentHubLikeAgentFromModal:
    """ELITEA-2358: Agent Hub — like an agent from the expanded detail modal (l2, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2358_agent-hub-like-an-agent-from-the-expanded-detail-modal.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1215",
        "Known defect — non-serializable console error on like/unlike click",
    )
    @pytest.mark.p2
    def test_agent_hub_like_agent_from_modal(self, page: Page):
        """Like an agent from the expanded detail modal: toggle state, increment
        count, and verify persistence across modal close/reopen and in the
        card list."""
        agent_hub = AgentHubPage(page)
        soft_failures: list[str] = []

        # Hardcoded to a known pre-existing agent with a known like count
        # baseline — the case doesn't require dynamic discovery like
        # ELITEA-2354 (which mutates the agent's like count as its primary
        # assertion).  This case just exercises the like-interaction
        # mechanics inside the modal (AFS § Test Data).
        AGENT_NAME = "Business Analyst"
        APPLICATION_ID = 31  # Business Analyst application id (AFS § Test Data)

        with allure.step("Step 1 — Navigate to Agent Hub"):
            agent_hub.navigate()
            assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

        with allure.step(f"Step 2 — Click on the {AGENT_NAME!r} agent card to open the detail modal"):
            assert agent_hub.get_agent_card(AGENT_NAME).first.is_visible(), (
                f"Agent card {AGENT_NAME!r} should be visible on the Catalog page"
            )
            agent_hub.open_agent_by_name(AGENT_NAME, timeout=NAVIGATION_TIMEOUT)

        with allure.step("Step 3 — Locate and verify the like button in the modal header"):
            expect(agent_hub.modal_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            modal_like_button = agent_hub.get_modal_like_button()
            assert modal_like_button.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                "Modal like button should be visible in the modal header"
            )
            initial_like_count = agent_hub.get_modal_like_count()
            initial_liked_state = agent_hub.get_modal_liked_state()
            logger.info(
                "Initial modal like state: count=%s, liked=%s", initial_like_count, initial_liked_state
            )

        with allure.step("Step 4 — Click the like button in the modal"):
            console_errors = agent_hub.capture_console_errors()
            response = agent_hub.click_modal_like_button(timeout=UI_ELEMENT_TIMEOUT)
            # Response is 201 (like) or 204 (unlike) depending on current state
            assert response.status in (201, 204), (
                f"Expected POST/DELETE .../social/like/... to return 201 or 204, got {response.status}"
            )
            logger.info("Modal like click response: %s", response.status)

        with allure.step("Step 5 — Verify the like count and state changed in the modal"):
            # Brief wait for UI to update after the network response
            page.wait_for_timeout(500)
            new_like_count = agent_hub.get_modal_like_count(timeout=UI_ELEMENT_TIMEOUT)
            new_liked_state = agent_hub.get_modal_liked_state()
            logger.info("After click modal like state: count=%s, liked=%s", new_like_count, new_liked_state)

            # Count should have changed by ±1
            count_delta = abs(new_like_count - initial_like_count)
            assert count_delta == 1, (
                f"Expected like count to change by ±1, got {initial_like_count} → {new_like_count}"
            )

            # State should have flipped
            assert new_liked_state != initial_liked_state, (
                f"Expected liked state to flip, got {initial_liked_state} → {new_liked_state}"
            )

        with allure.step(
            "Side-channel check — known defect #1215 console error on the like click "
            "(checked here, after step 5's own waits, so the async dispatch has landed)"
        ):
            unexpected_errors = [m.text for m in console_errors if not _is_known_defect_1215(m.text)]
            assert not unexpected_errors, f"Unexpected console errors on like click: {unexpected_errors}"
            # Known defect: EliteaAI/elitea-testing-public#1215 — recorded in
            # soft_failures so it stays RED until the product fix ships.
            known_defect_errors = [m.text for m in console_errors if _is_known_defect_1215(m.text)]
            if known_defect_errors:
                soft_failures.append(
                    "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1215: "
                    f"non-serializable Redux console error(s) on like click: {len(known_defect_errors)} "
                    "occurrence(s)"
                )
            console_errors.stop()

        with allure.step("Step 6 — Close the modal"):
            agent_hub.close_modal(timeout=UI_ELEMENT_TIMEOUT)
            expect(agent_hub.modal_dialog).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
            # Brief wait for page to fully settle after modal closes
            page.wait_for_timeout(500)

        with allure.step("Step 6a — Verify the updated like count is reflected on the agent card in the list"):
            card = agent_hub.get_agent_card(AGENT_NAME).first
            assert card.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                f"Agent card {AGENT_NAME!r} should be visible after modal close"
            )
            # The card's like button should show the same final count as the modal had.
            # Use .first to handle multiple "Business Analyst" cards in different sections.
            card_like_button = agent_hub.get_like_button(APPLICATION_ID)
            card_like_button.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            card_like_count_text = (card_like_button.first.text_content() or "0").strip()
            card_like_count = int(card_like_count_text)
            assert card_like_count == new_like_count, (
                f"Card like count should match modal's final count: "
                f"card={card_like_count}, modal={new_like_count}"
            )

        with allure.step("Step 6b — Reopen the modal and verify like state persists"):
            agent_hub.open_agent_by_name(AGENT_NAME, timeout=NAVIGATION_TIMEOUT)
            expect(agent_hub.modal_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            # State should be the same as when we closed
            reopened_like_count = agent_hub.get_modal_like_count(timeout=UI_ELEMENT_TIMEOUT)
            reopened_liked_state = agent_hub.get_modal_liked_state()
            assert reopened_like_count == new_like_count, (
                f"Like count should persist on modal reopen: "
                f"expected {new_like_count}, got {reopened_like_count}"
            )
            assert reopened_liked_state == new_liked_state, (
                f"Liked state should persist on modal reopen: "
                f"expected {new_liked_state}, got {reopened_liked_state}"
            )

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
