"""UI Test for ELITEA-2355 — Agent Hub: unlike an agent from the list view.

Verifies that unliking a currently-liked agent card on the Agent Hub
(Catalog) page (`/elitea-catalog`) decrements its like count, unfills the
heart icon to its inactive state, and both persist across a full page
refresh.

Spec: test-specs/agent-hub/l3_agent-hub-unlike-agent-from-list-view_ELITEA-2355.md

Reuses `AgentHubPage` as-is for navigation/heading/agent-card lookup
(ELITEA-2075) and the like-button helpers added by ELITEA-2354
(`find_unliked_application`, `click_like_button`, `wait_for_like_count`,
`is_agent_liked`). Adds `find_first_liked_application_id()` (dynamic "locate
a currently-liked agent" discovery, this case's Step 2) and an opt-in
``first=True`` scoping param on the existing like-button methods, both
additive to `AgentHubPage`.

**Declared improvisation (AFS § Preconditions, per
`.agents/role-overrides.md` § Declared-improvisation protocol):** "an agent
is already liked by the current user" is NOT reliable ambient state in this
environment — ELITEA-2354's own test mandatorily unlikes its target in
cleanup, so a fresh run reliably has zero agents liked by `${TEST_USER}`
(re-verified live this dispatch: 0 of 23 rendered like buttons showed
`data-liked="true"`, and the "My Liked" filter rendered 0 cards). This test
therefore performs a small setup step (not one of the case's own 6 numbered
steps) that dynamically likes an unliked agent to produce the precondition,
then proceeds through the case's own steps exactly as specced — Step 2's
dynamic discovery finds the agent the setup step just liked. Net effect on
shared product data across the whole test (setup like + case's own Step 3
unlike) is zero — no separate cleanup block is needed for the common path; a
defensive `finally` cleanup unlike still guards the case where the setup
like succeeded but the case's own unlike never ran.

Known defect (filed, non-blocking — AFS § Known Defects Found,
EliteaAI/elitea-testing-public#1215): clicking the like/unlike heart icon
fires a Redux "non-serializable value" console.error every time. Same
handling as ELITEA-2354/ELITEA-2358 (soft assertions via the
`soft_failures`/`pytest.fail()` mechanism — a raw console-message list isn't
`expect.soft()`-bindable — so this stays a tracked, visible RED until the
product fix ships, without masking a genuinely new console error).

Usage:
    cd automation
    pytest tests/ui/agents/test_agent_hub_unlike_agent_list_view.py -v
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p3]

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


def _setup_cleanup_soft_failures(
    *,
    unlike_status: int,
    like_count_restored: bool,
    final_like_count: int,
    unexpected_unlike_errors: list[str],
) -> list[str]:
    """Pure helper: turn the defensive setup-cleanup observations into
    soft-failure messages instead of a logger-only record — mirrors
    ELITEA-2354's `_cleanup_soft_failures` (this test's setup step mutates
    the same kind of shared, cross-session product data, so a failed
    defensive cleanup must never be able to pass this test silently while
    leaving that baseline polluted).
    """
    failures: list[str] = []
    if unlike_status != 204:
        failures.append(
            f"Defensive setup-cleanup unlike expected 204, got {unlike_status} — like-count "
            "baseline may not be restored for sibling cases"
        )
    if not like_count_restored:
        failures.append(
            f"Defensive setup-cleanup did not restore like count, got {final_like_count} "
            "— shared like-count baseline left polluted for sibling cases"
        )
    if unexpected_unlike_errors:
        failures.append(
            f"Unexpected console errors on defensive setup-cleanup unlike click: {unexpected_unlike_errors}"
        )
    return failures


class TestAgentHubUnlikeAgentListView:
    """ELITEA-2355: Agent Hub — unlike an agent from the list view (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2355_agent-hub-unlike-an-agent-from-the-list-view.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1215",
        "Known defect — non-serializable console error on like/unlike click",
    )
    @pytest.mark.p3
    def test_agent_hub_unlike_agent_from_list_view(self, page: Page):
        """Unliking a liked agent card decrements its count, unfills the
        heart icon, and persists across a full page refresh."""
        agent_hub = AgentHubPage(page)
        soft_failures: list[str] = []
        setup_liked = False
        unliked_via_case = False
        setup_application_id: int | None = None
        setup_agent_name: str | None = None

        try:
            with allure.step(
                "Setup — dynamically like an unliked agent to establish this case's precondition "
                "(declared improvisation — see this file's module docstring / AFS § Preconditions)"
            ):
                applications = agent_hub.navigate_and_capture_applications(timeout=NAVIGATION_TIMEOUT)
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"
                setup_target = agent_hub.find_unliked_application(applications)
                assert setup_target is not None, (
                    "Expected at least one agent the current user hasn't liked yet, to use for this "
                    "case's dynamic 'like' precondition setup"
                )
                setup_application_id = setup_target["id"]
                setup_agent_name = setup_target["name"]
                setup_baseline_count = setup_target.get("likes", 0)
                assert agent_hub.get_agent_card(setup_agent_name).first.is_visible(), (
                    f"Agent card {setup_agent_name!r} (id={setup_application_id}) should be visible "
                    "to set up this case's precondition"
                )
                setup_response = agent_hub.click_like_button(
                    setup_application_id, timeout=UI_ELEMENT_TIMEOUT, first=True
                )
                setup_liked = True
                assert setup_response.status == 201, (
                    f"Setup-like for {setup_agent_name!r} (id={setup_application_id}) expected 201, "
                    f"got {setup_response.status}"
                )
                agent_hub.wait_for_like_count(
                    setup_application_id, setup_baseline_count + 1, timeout=UI_ELEMENT_TIMEOUT, first=True
                )

            with allure.step("Step 1 — Navigate to Agent Hub"):
                agent_hub.navigate()
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

            with allure.step("Step 2 — Locate an agent card currently liked by the user"):
                application_id = agent_hub.find_first_liked_application_id(timeout=UI_ELEMENT_TIMEOUT)
                assert application_id is not None, (
                    "Expected at least one agent card with data-liked='true' after the setup 'like' step"
                )
                assert agent_hub.is_agent_liked(application_id, timeout=UI_ELEMENT_TIMEOUT, first=True), (
                    f"Agent (id={application_id}) discovered via data-liked='true' should read liked"
                )
                initial_like_count = agent_hub.get_like_count(application_id, first=True)
                assert initial_like_count >= 1, (
                    f"Agent (id={application_id}) discovered as liked should show a like count >= 1, "
                    f"got {initial_like_count}"
                )

            with allure.step(f"Step 3 — Click the heart icon on agent (id={application_id}) to unlike it"):
                console_errors = agent_hub.capture_console_errors()
                response = agent_hub.click_like_button(application_id, timeout=UI_ELEMENT_TIMEOUT, first=True)
                unliked_via_case = True
                assert response.status == 204, (
                    f"Expected DELETE .../social/like/... to return 204, got {response.status}"
                )

            with allure.step("Step 4 — Verify the heart icon changes to an unfilled/inactive state"):
                # wait_for_liked_state (auto-retrying), not is_agent_liked — the
                # like/unlike DOM update is optimistic-async relative to the
                # click's own network response resolving (confirmed live during
                # implementation), so a state TRANSITION right after a click
                # needs a retry-until-flips wait, not a one-shot/appear-only
                # check. See AgentHubPage.wait_for_liked_state's docstring.
                agent_hub.wait_for_liked_state(application_id, liked=False, timeout=UI_ELEMENT_TIMEOUT, first=True)

            with allure.step("Step 5 — Verify the like count decrements by 1"):
                agent_hub.wait_for_like_count(
                    application_id, initial_like_count - 1, timeout=UI_ELEMENT_TIMEOUT, first=True
                )

            with allure.step(
                "Side-channel check — known defect #1215 console error on the unlike click "
                "(checked here, after steps 4-5's own waits, so the async dispatch that "
                "triggers it has definitely already landed — same ordering as ELITEA-2354/2358)"
            ):
                unexpected_errors = [m.text for m in console_errors if not _is_known_defect_1215(m.text)]
                assert not unexpected_errors, f"Unexpected console errors on unlike click: {unexpected_errors}"
                # Known defect: EliteaAI/elitea-testing-public#1215 — recorded in
                # soft_failures (a raw console-message list isn't expect.soft()
                # -bindable) so it stays a tracked, visible RED until the product
                # fix ships. Sanctioned-RED per .agents/testing.md § Merge gate.
                known_defect_errors = [m.text for m in console_errors if _is_known_defect_1215(m.text)]
                if known_defect_errors:
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1215: "
                        f"non-serializable Redux console error(s) on unlike click: {len(known_defect_errors)} "
                        "occurrence(s)"
                    )
                console_errors.stop()

            with allure.step(
                "Step 6 — Refresh the page and verify the updated like count and unliked state persist"
            ):
                page.reload()
                agent_hub.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                # Same rationale as ELITEA-2354's Step 6: the default post-refresh
                # view only renders the top-N "Trending" cards by like-count
                # descending, so a just-unliked (now lower-count) agent is not
                # guaranteed to still be among them — re-locate via search using
                # the setup step's own captured name (the same agent this case
                # discovered dynamically in Step 2, since nothing else in this
                # environment currently carries data-liked="true" — AFS §
                # Preconditions' declared-improvisation note).
                agent_hub.search(setup_agent_name, timeout=UI_ELEMENT_TIMEOUT)
                assert agent_hub.get_agent_card(setup_agent_name).first.is_visible(), (
                    f"Agent card {setup_agent_name!r} should be visible via search after refresh"
                )
                agent_hub.wait_for_like_count(
                    application_id, initial_like_count - 1, timeout=UI_ELEMENT_TIMEOUT, first=True
                )
                agent_hub.wait_for_liked_state(application_id, liked=False, timeout=UI_ELEMENT_TIMEOUT, first=True)
        finally:
            # Defensive cleanup (not an AFS case step): this test's own Step 3
            # already unlikes the setup-liked agent (see this file's module
            # docstring — net zero shared-data mutation). This finally block
            # only fires the RESTORE path when the setup-like succeeded but the
            # case's own unlike never ran (e.g. an earlier assertion failed) —
            # same defensive-cleanup discipline as ELITEA-2354's test.
            if setup_liked and not unliked_via_case and setup_application_id is not None:
                with allure.step("Defensive cleanup — unlike the setup agent (case's own unlike never ran)"):
                    try:
                        cleanup_console_errors = agent_hub.capture_console_errors()
                        cleanup_response = agent_hub.click_like_button(
                            setup_application_id, timeout=UI_ELEMENT_TIMEOUT, first=True
                        )
                        if cleanup_response.status != 204:
                            logger.error(
                                "Defensive setup-cleanup unlike for %r (id=%s) expected 204, got %s",
                                setup_agent_name,
                                setup_application_id,
                                cleanup_response.status,
                            )
                        like_count_restored = True
                        final_like_count = -1
                        try:
                            agent_hub.wait_for_like_count(
                                setup_application_id, setup_baseline_count, timeout=UI_ELEMENT_TIMEOUT, first=True
                            )
                        except AssertionError:
                            like_count_restored = False
                            final_like_count = agent_hub.get_like_count(setup_application_id, first=True)
                            logger.error(
                                "Defensive setup-cleanup did not restore like count for %r (id=%s), got %s",
                                setup_agent_name,
                                setup_application_id,
                                final_like_count,
                            )
                        unexpected_cleanup_errors = [
                            m.text for m in cleanup_console_errors if not _is_known_defect_1215(m.text)
                        ]
                        if unexpected_cleanup_errors:
                            logger.error(
                                "Unexpected console errors on defensive setup-cleanup unlike for %r (id=%s): %s",
                                setup_agent_name,
                                setup_application_id,
                                unexpected_cleanup_errors,
                            )
                        cleanup_console_errors.stop()

                        soft_failures.extend(
                            _setup_cleanup_soft_failures(
                                unlike_status=cleanup_response.status,
                                like_count_restored=like_count_restored,
                                final_like_count=final_like_count,
                                unexpected_unlike_errors=unexpected_cleanup_errors,
                            )
                        )
                    except Exception as exc:  # noqa: BLE001 — cleanup must never mask the real failure
                        logger.error(
                            "Defensive setup-cleanup unlike raised for %r (id=%s): %s",
                            setup_agent_name,
                            setup_application_id,
                            exc,
                        )
                        soft_failures.append(
                            f"Defensive setup-cleanup unlike raised an exception for {setup_agent_name!r} "
                            f"(id={setup_application_id}): {exc}"
                        )

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
