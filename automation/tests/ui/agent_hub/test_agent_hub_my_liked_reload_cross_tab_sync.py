"""UI Test for ELITEA-2365 — Agent Hub: "My Liked" reload reflects a like
made in another tab.

Verifies that liking an agent in Tab B (a second page in the SAME
authenticated browser context) is NOT immediately visible in Tab A's "My
Liked" section, but appears — with the matching like count — after a full
page reload in Tab A (the only refresh mechanism this surface actually
offers; see the case-text drift note below). Cleanup (mandatory — this case
mutates shared, cross-session product data that sibling cases in this family
depend on as a clean baseline) unlikes the agent again before the test ends.

Spec: test-specs/agent-hub/l3_agent-hub-my-liked-reload-cross-tab-sync_ELITEA-2365.md

Reuses `AgentHubPage` as-is (ELITEA-2075/2350/2352/2354) for navigation,
category filter-rail chip clicks, agent-card lookup, and like/unlike
helpers; adds `find_unliked_application()` and
`reload_and_capture_my_liked()` to the same page object for this case. No
new testids needed — every handle this case touches was already added by
ELITEA-2350/2352/2354's implementers.

Case-text drift (CLARIFICATION, cited — not re-filed,
EliteaAI/elitea-testing-public#1212): case text (step 8) claims a
reload/refresh icon exists next to the "My Liked" section header; no such
icon exists anywhere in the live product for ANY category section (same
shared `AgentCategorySection.jsx` header, same root cause #1212 already
tracks for ELITEA-2352's "Business Analyst" instance). Automation substitutes
the only actual refresh mechanism this surface offers: a full page reload
(same substitution precedent as ELITEA-2354's own step 6).

Known defect (filed, non-blocking — AFS § Known Defects Found,
EliteaAI/elitea-testing-public#1215): clicking the like/unlike heart icon
fires a Redux "non-serializable value" console.error every time. Functionally
harmless — soft-asserted via the pytest-native `soft_failures`/`pytest.fail()`
mechanism (same idiom as `test_agent_hub_like_agent_list_view.py`'s #1215
handling), so this stays a tracked, visible RED until the fix ships without
masking a genuinely new console error (still hard-fails). Sanctioned-RED per
`.agents/testing.md` § Merge gate.

Usage:
    cd automation
    pytest tests/ui/agents/test_agent_hub_my_liked_reload_cross_tab_sync.py -v
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
MY_LIKED_CATEGORY = "My Liked"
MY_LIKED_SLUG = "my-liked"

_KNOWN_DEFECT_1215_PREFIX = (
    "A non-serializable value was detected in an action, in the path: `payload.updateFn`"
)


def _is_known_defect_1215(text: str) -> bool:
    """True for the known, filed, non-blocking Redux console error
    (EliteaAI/elitea-testing-public#1215) that fires on every like/unlike
    click on an Agent Hub agent card. Matches on the warning's own stable
    text prefix (the exact reducer-value suffix varies per click/agent, so
    it is not part of the match). Duplicated from
    `test_agent_hub_like_agent_list_view.py` — a second occurrence, below
    Rule 7's third-repetition extraction threshold.
    """
    return _KNOWN_DEFECT_1215_PREFIX in text


class TestAgentHubMyLikedReloadCrossTabSync:
    """ELITEA-2365: Agent Hub — "My Liked" reload reflects cross-tab likes (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2365_agent-hub-my-liked-reload-button-refreshes-list-with-likes-m.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1215",
        "Known defect — non-serializable console error on like/unlike click",
    )
    @pytest.mark.p2
    def test_agent_hub_my_liked_reload_reflects_cross_tab_like(self, page: Page):
        """A like made in Tab B is absent from Tab A's "My Liked" list until
        Tab A performs a full page reload, after which it appears with the
        matching like count; unliking (cleanup) restores the baseline."""
        agent_hub_a = AgentHubPage(page)
        soft_failures: list[str] = []
        liked = False
        application_id: int | None = None
        agent_name: str | None = None
        pre_like_count: int | None = None
        tab_b: Page | None = None

        try:
            with allure.step('Step 1 — Navigate to Agent Hub in Tab A and click the "My Liked" filter chip'):
                agent_hub_a.navigate()
                assert agent_hub_a.page_heading.is_visible(), "Catalog page heading should be visible"
                agent_hub_a.click_category_filter_chip(MY_LIKED_CATEGORY, timeout=UI_ELEMENT_TIMEOUT)
                assert agent_hub_a.is_category_filter_chip_selected(MY_LIKED_CATEGORY, timeout=UI_ELEMENT_TIMEOUT), (
                    f"{MY_LIKED_CATEGORY!r} chip should be marked selected (data-selected='true') after click"
                )
                visible_headings = agent_hub_a.get_visible_category_heading_texts()
                assert visible_headings == [MY_LIKED_CATEGORY], (
                    "Expected exactly one content-list category section "
                    f"({MY_LIKED_CATEGORY!r}) after filtering, got: {visible_headings!r}"
                )

            with allure.step('Step 2 — Verify the current "My Liked" list is displayed in Tab A'):
                assert agent_hub_a.is_category_section_visible(MY_LIKED_SLUG, timeout=UI_ELEMENT_TIMEOUT), (
                    f"{MY_LIKED_CATEGORY!r} content-list heading should be visible above the results"
                )
                assert agent_hub_a.get_agent_card_count() > 0, (
                    'Expected at least one pre-existing agent card under "My Liked" '
                    "(this environment has pre-existing liked agents — AFS § Test Data)"
                )

            with allure.step("Step 3 — Open Agent Hub in Tab B (new tab, same browser context)"):
                tab_b = page.context.new_page()
                agent_hub_b = AgentHubPage(tab_b)
                applications = agent_hub_b.navigate_and_capture_applications(timeout=NAVIGATION_TIMEOUT)
                assert agent_hub_b.page_heading.is_visible(), "Catalog page heading should be visible in Tab B"

            with allure.step("Step 4 — In Tab B, locate an unliked agent and click its heart icon (like)"):
                target = agent_hub_b.find_unliked_application(applications)
                assert target is not None, (
                    "Expected at least one published agent NOT yet liked by the current "
                    "user at test start (dynamic discovery — like state is mutable, shared, "
                    "cross-session product data, not a stable per-name fixture; see this "
                    "case's AFS § Test Data)"
                )
                application_id = target["id"]
                agent_name = target["name"]
                assert agent_hub_b.get_agent_card(agent_name).first.is_visible(), (
                    f"Agent card {agent_name!r} (id={application_id}) should be visible on Tab B's Catalog page"
                )
                pre_like_count = agent_hub_b.get_like_count(application_id)

                console_errors = agent_hub_b.capture_console_errors()
                response = agent_hub_b.click_like_button(application_id, timeout=UI_ELEMENT_TIMEOUT)
                liked = True
                assert response.status == 201, (
                    f"Expected POST .../social/like/... to return 201, got {response.status}"
                )

            with allure.step("Step 5 — Verify the like count increments on the agent card in Tab B"):
                agent_hub_b.wait_for_like_count(application_id, pre_like_count + 1, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Side-channel check — known defect #1215 console error on the Tab B like click "
                "(checked here, after step 5's own wait, so the async dispatch that triggers it "
                "has definitely already landed)"
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

            with allure.step("Step 6 — Switch back to Browser Tab A"):
                page.bring_to_front()

            with allure.step('Step 7 — Verify the newly liked agent is NOT yet visible in Tab A\'s "My Liked" list'):
                assert agent_hub_a.get_agent_card(agent_name).count() == 0, (
                    f"Agent {agent_name!r} (id={application_id}) should NOT yet appear in Tab A's "
                    '"My Liked" list — Tab A has not refetched since Tab B\'s like'
                )

            with allure.step(
                'Step 8 — Reload Tab A (substituted for the case text\'s non-existent "reload icon" — '
                "CLARIFICATION, cited EliteaAI/elitea-testing-public#1212, not re-filed) and verify "
                'the "My Liked" list refreshes (Step 9)'
            ):
                my_liked_response = agent_hub_a.reload_and_capture_my_liked(timeout=NAVIGATION_TIMEOUT)
                assert "rows" in my_liked_response, (
                    "Expected the re-fetched My-Liked response to contain a 'rows' field"
                )
                # The "My Liked" chip selection is client-only UI state and does NOT
                # survive a full page reload (confirmed live during analysis — AFS
                # § Known Defects/Clarifications implementation note) — re-select it
                # before re-reading the section.
                agent_hub_a.click_category_filter_chip(MY_LIKED_CATEGORY, timeout=UI_ELEMENT_TIMEOUT)
                assert agent_hub_a.is_category_filter_chip_selected(MY_LIKED_CATEGORY, timeout=UI_ELEMENT_TIMEOUT), (
                    f"{MY_LIKED_CATEGORY!r} chip should be re-selectable (data-selected='true') after reload"
                )
                assert agent_hub_a.is_category_section_visible(MY_LIKED_SLUG, timeout=UI_ELEMENT_TIMEOUT), (
                    f"{MY_LIKED_CATEGORY!r} content-list heading should be visible again after re-filtering"
                )

            with allure.step('Step 10 — Verify the agent liked in Tab B now appears in Tab A\'s "My Liked" list'):
                assert agent_hub_a.get_agent_card(agent_name).first.is_visible(), (
                    f"Agent {agent_name!r} (id={application_id}) should now appear in Tab A's "
                    '"My Liked" list after the reload'
                )

            with allure.step("Step 11 — Verify the like count on the newly appeared card matches Tab B's count"):
                agent_hub_a.wait_for_like_count(application_id, pre_like_count + 1, timeout=UI_ELEMENT_TIMEOUT)
        finally:
            # Cleanup (not an AFS case step — mandatory, see this case's AFS
            # § Cleanup): this test mutates shared, cross-session product data
            # (the agent's public like count/state) that sibling cases in this
            # family depend on as a baseline. Best-effort + logged loudly so a
            # cleanup failure never masks a real assertion failure above.
            if liked and application_id is not None and tab_b is not None:
                with allure.step("Cleanup — unlike the agent (in Tab B) to restore the pre-test baseline"):
                    try:
                        unlike_console_errors = agent_hub_b.capture_console_errors()
                        unlike_response = agent_hub_b.click_like_button(application_id, timeout=UI_ELEMENT_TIMEOUT)
                        if unlike_response.status != 204:
                            logger.error(
                                "Cleanup unlike for %r (id=%s) expected 204, got %s",
                                agent_name,
                                application_id,
                                unlike_response.status,
                            )
                        like_count_restored = True
                        final_like_count = pre_like_count
                        try:
                            agent_hub_b.wait_for_like_count(application_id, pre_like_count, timeout=UI_ELEMENT_TIMEOUT)
                        except AssertionError:
                            like_count_restored = False
                            final_like_count = agent_hub_b.get_like_count(application_id)
                            logger.error(
                                "Cleanup did not restore like count to %s for %r (id=%s), got %s",
                                pre_like_count,
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
                        # soft_failures; the step-4/5 occurrence above already
                        # marks this test RED-by-design for the one open ticket).
                        unlike_console_errors.stop()

                        if unlike_response.status != 204:
                            soft_failures.append(
                                f"Cleanup unlike expected 204, got {unlike_response.status} — like-count "
                                "baseline may not be restored for sibling cases"
                            )
                        if not like_count_restored:
                            soft_failures.append(
                                f"Cleanup did not restore like count to {pre_like_count}, got "
                                f"{final_like_count} — shared like-count baseline left polluted for sibling cases"
                            )
                        if unexpected_unlike_errors:
                            soft_failures.append(
                                f"Unexpected console errors on cleanup unlike click: {unexpected_unlike_errors}"
                            )
                    except Exception as exc:  # noqa: BLE001 — cleanup must never mask the real failure
                        logger.error(
                            "Cleanup unlike raised for %r (id=%s): %s", agent_name, application_id, exc
                        )
                        soft_failures.append(
                            f"Cleanup unlike raised an exception for {agent_name!r} "
                            f"(id={application_id}): {exc}"
                        )
            if tab_b is not None:
                tab_b.close()

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
