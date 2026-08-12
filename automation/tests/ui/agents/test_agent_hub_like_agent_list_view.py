"""UI Test for ELITEA-2354 — Agent Hub: like an agent from the list view.

Verifies that liking an unliked agent card on the Agent Hub (Catalog) page
(`/elitea-catalog`) increments its like count, fills the heart icon to its
active state, and both persist across a full page refresh. Cleanup
(mandatory — this case mutates shared, cross-session product data that
sibling cases in this family depend on as a baseline) unlikes the agent
again before the test ends.

Spec: test-specs/agent-hub/l3_agent-hub-like-agent-from-list-view_ELITEA-2354.md

Reuses `AgentHubPage` as-is for navigation/heading/agent-card lookup
(ELITEA-2075); adds the like-button/search helpers to the same page object
for this case.

Known defect (filed, non-blocking — AFS § Known Defects Found,
EliteaAI/elitea-testing-public#1215): clicking the like/unlike heart icon
fires a Redux "non-serializable value" console.error every time
(`agentHub/updateApplicationInCategories` dispatched with a raw function
payload). Functionally harmless — the like/unlike flow itself (count, icon,
persistence, backend call) is entirely correct. Soft-asserted via the
pytest-native `soft_failures`/`pytest.fail()` mechanism (same idiom as
`test_secret_create_inline_checkmark_x_cancel.py`'s #1203 handling — a raw
console-message list isn't `expect.soft()`-bindable) so this stays a
tracked, visible RED until the fix ships, without masking a genuinely new
console error (still hard-fails). Sanctioned-RED per `.agents/testing.md`
§ Merge gate.

Testid gaps filled this implementation (`add-data-testid`, pushed to
`automation/testids`, EliteaAI/EliteaUI@e079c0d0): `catalog-agent-like-
button-{application.id}` + `data-liked="true"/"false"` on the shared
`Like.jsx` component's `IconButton`, threaded via a caller-supplied `testId`
prop (`AgentCard.jsx` -> `AgentHubLike.jsx` -> `Like.jsx`) per the
shared-component testid discipline.

Usage:
    cd automation
    pytest tests/ui/agents/test_agent_hub_like_agent_list_view.py -v
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page

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
    click on an Agent Hub agent card. Matches on the warning's own stable
    text prefix (the exact reducer-value suffix varies per click/agent, so
    it is not part of the match).
    """
    return _KNOWN_DEFECT_1215_PREFIX in text


def _cleanup_soft_failures(
    *,
    unlike_status: int,
    like_count_restored: bool,
    final_like_count: int,
    unexpected_unlike_errors: list[str],
) -> list[str]:
    """Pure helper: turn the cleanup-unlike observations into soft-failure
    messages instead of a logger-only record.

    Cleanup here mutates SHARED, cross-session product data (the agent's
    public like count/state) that sibling cases in this family depend on as
    a baseline (see this module's docstring). A failed cleanup that is only
    `logger.error()`-ed is invisible to the test result — the test still
    goes green while the baseline stays polluted for every case that runs
    after it. Each of the three cleanup-unlike observations therefore
    produces its own soft-failure message when it fails, appended to the
    same `soft_failures`/`pytest.fail()` mechanism already used for the
    known #1215 defect above, so a broken cleanup surfaces as a real (if
    soft) test failure rather than a silent log line.
    """
    failures: list[str] = []
    if unlike_status != 204:
        failures.append(
            f"Cleanup unlike expected 204, got {unlike_status} — like-count "
            "baseline may not be restored for sibling cases"
        )
    if not like_count_restored:
        failures.append(
            f"Cleanup did not restore like count to 0, got {final_like_count} "
            "— shared like-count baseline left polluted for sibling cases"
        )
    if unexpected_unlike_errors:
        failures.append(
            f"Unexpected console errors on cleanup unlike click: {unexpected_unlike_errors}"
        )
    return failures


class TestAgentHubLikeAgentListView:
    """ELITEA-2354: Agent Hub — like an agent from the list view (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2354_agent-hub-like-an-agent-from-the-list-view.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1215",
        "Known defect — non-serializable console error on like/unlike click",
    )
    @pytest.mark.p2
    def test_agent_hub_like_agent_from_list_view(self, page: Page):
        """Liking an unliked agent card increments its count, fills the heart
        icon, and persists across a full page refresh; unliking (cleanup)
        restores the original baseline."""
        agent_hub = AgentHubPage(page)
        soft_failures: list[str] = []
        liked = False
        application_id: int | None = None
        agent_name: str | None = None

        try:
            with allure.step("Step 1 — Navigate to Agent Hub"):
                applications = agent_hub.navigate_and_capture_applications(timeout=NAVIGATION_TIMEOUT)
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

            with allure.step("Step 2 — Locate an agent card currently showing 0 likes"):
                target = agent_hub.find_zero_like_application(applications)
                assert target is not None, (
                    "Expected at least one published agent with 0 likes at test start "
                    "(dynamic discovery — live like counts are mutable shared product "
                    "data, not a stable per-name fixture; see this case's AFS § Test Data)"
                )
                application_id = target["id"]
                agent_name = target["name"]
                assert agent_hub.get_agent_card(agent_name).first.is_visible(), (
                    f"Agent card {agent_name!r} (id={application_id}) should be visible on the Catalog page"
                )
                assert agent_hub.get_like_count(application_id) == 0, (
                    f"Agent {agent_name!r} (id={application_id}) should start with 0 likes"
                )

            with allure.step(f"Step 3 — Click the heart icon on {agent_name!r} (like)"):
                console_errors = agent_hub.capture_console_errors()
                response = agent_hub.click_like_button(application_id, timeout=UI_ELEMENT_TIMEOUT)
                liked = True
                assert response.status == 201, (
                    f"Expected POST .../social/like/... to return 201, got {response.status}"
                )

            with allure.step("Step 4 — Verify the heart icon changes to a filled/active state"):
                assert agent_hub.is_agent_liked(application_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Agent {agent_name!r} (id={application_id}) should show data-liked='true' after liking"
                )

            with allure.step("Step 5 — Verify the like count increments by 1"):
                agent_hub.wait_for_like_count(application_id, 1, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Side-channel check — known defect #1215 console error on the like click "
                "(checked here, after steps 4-5's own waits, so the async dispatch that "
                "triggers it has definitely already landed — see this test's module docstring)"
            ):
                unexpected_errors = [m.text for m in console_errors if not _is_known_defect_1215(m.text)]
                assert not unexpected_errors, f"Unexpected console errors on like click: {unexpected_errors}"
                # Known defect: EliteaAI/elitea-testing-public#1215 — recorded in
                # soft_failures (a raw console-message list isn't expect.soft()
                # -bindable) so it stays a tracked, visible RED until the product
                # fix ships. Sanctioned-RED per .agents/testing.md § Merge gate.
                known_defect_errors = [m.text for m in console_errors if _is_known_defect_1215(m.text)]
                if known_defect_errors:
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1215: "
                        f"non-serializable Redux console error(s) on like click: {len(known_defect_errors)} "
                        "occurrence(s)"
                    )
                console_errors.stop()

            with allure.step(
                "Step 6 — Refresh the page and verify the updated like count and liked state persist"
            ):
                page.reload()
                agent_hub.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                # The default post-refresh view only renders the top-6 "Trending"
                # cards by like-count descending — a freshly-liked low-count agent
                # is not guaranteed to be among them, so re-locate via search
                # (confirmed live during analysis — AFS § Test Steps, step 6).
                agent_hub.search(agent_name, timeout=UI_ELEMENT_TIMEOUT)
                assert agent_hub.get_agent_card(agent_name).first.is_visible(), (
                    f"Agent card {agent_name!r} should be visible via search after refresh"
                )
                agent_hub.wait_for_like_count(application_id, 1, timeout=UI_ELEMENT_TIMEOUT)
                assert agent_hub.is_agent_liked(application_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Agent {agent_name!r} (id={application_id}) should still show data-liked='true' after refresh"
                )
        finally:
            # Cleanup (not an AFS case step — mandatory, see this case's AFS
            # § Cleanup): this test mutates shared, cross-session product data
            # (the agent's public like count/state) that sibling cases in this
            # family depend on as a baseline. Best-effort + logged loudly so a
            # cleanup failure never masks a real assertion failure above.
            if liked and application_id is not None:
                with allure.step("Cleanup — unlike the agent to restore the pre-test baseline"):
                    try:
                        unlike_console_errors = agent_hub.capture_console_errors()
                        unlike_response = agent_hub.click_like_button(application_id, timeout=UI_ELEMENT_TIMEOUT)
                        if unlike_response.status != 204:
                            logger.error(
                                "Cleanup unlike for %r (id=%s) expected 204, got %s",
                                agent_name,
                                application_id,
                                unlike_response.status,
                            )
                        # Wait for state FIRST (the retrying wait pumps the
                        # Playwright event loop, so any pending console-message
                        # CDP event has landed by the time we inspect
                        # unlike_console_errors below — same ordering rationale
                        # as steps 4-5 vs. the like-click side-channel check
                        # above). A retrying wait, not a one-shot read, because
                        # the unlike count update is equally optimistic/async
                        # relative to the click's own network response (see
                        # AgentHubPage.get_like_count's docstring).
                        like_count_restored = True
                        final_like_count = 0
                        try:
                            agent_hub.wait_for_like_count(application_id, 0, timeout=UI_ELEMENT_TIMEOUT)
                        except AssertionError:
                            like_count_restored = False
                            final_like_count = agent_hub.get_like_count(application_id)
                            logger.error(
                                "Cleanup did not restore like count to 0 for %r (id=%s), got %s",
                                agent_name,
                                application_id,
                                final_like_count,
                            )
                        unexpected_unlike_errors = [
                            m.text for m in unlike_console_errors if not _is_known_defect_1215(m.text)
                        ]
                        if unexpected_unlike_errors:
                            logger.error(
                                "Unexpected console errors on cleanup unlike click for %r (id=%s): %s",
                                agent_name,
                                application_id,
                                unexpected_unlike_errors,
                            )
                        # Known defect #1215 also fires on unlike (AFS § Known
                        # Defects) — expected, logged only (not re-added to
                        # soft_failures; the step-3 occurrence above already
                        # marks this test RED-by-design for the one open ticket).
                        unlike_console_errors.stop()

                        # Cleanup verification is routed into soft_failures
                        # (same mechanism as the known #1215 defect above),
                        # not logger-only: this test mutates a SHARED,
                        # cross-session like-count baseline that sibling
                        # cases depend on, so a failed cleanup must never be
                        # able to pass this test silently while leaving that
                        # baseline polluted (fix-round 1, review finding).
                        soft_failures.extend(
                            _cleanup_soft_failures(
                                unlike_status=unlike_response.status,
                                like_count_restored=like_count_restored,
                                final_like_count=final_like_count,
                                unexpected_unlike_errors=unexpected_unlike_errors,
                            )
                        )
                    except Exception as exc:  # noqa: BLE001 — cleanup must never mask the real failure
                        logger.error(
                            "Cleanup unlike raised for %r (id=%s): %s", agent_name, application_id, exc
                        )
                        soft_failures.append(
                            f"Cleanup unlike raised an exception for {agent_name!r} "
                            f"(id={application_id}): {exc}"
                        )

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
