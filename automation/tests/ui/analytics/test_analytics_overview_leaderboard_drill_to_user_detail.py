"""Overview leaderboard row drills into user detail; Back returns to Overview (GAP-073).

Clicking a "Top 5 AI Adopters" row on the Analytics Overview tab pre-loads
that user's detail view directly on the Users tab (bypassing the User
Activity list entirely), and the detail view's Back arrow returns to the
Overview tab (not the Users list) — the cross-tab `handleOverviewUserClick` /
`handleBackToOverview` / `cameFromExternal=true` mechanism documented in
``test-specs/analytics/_surface.md``.

Read-only exploration against the live ``Private`` project's shared AI
activity data (``Last 30d`` preset) — nothing is created, edited, or deleted,
so no fixture/cleanup is required. The leaderboard's row count and the first
row's email are read at runtime, never hardcoded, since this is shared-suite
data that will drift between runs.

Distinct from the *native* Users-tab drill-down (clicking a row directly in
the User Activity list) whose Back returns to the list, not Overview — that
is the `cameFromExternal=false` branch of the same `handleBack`, out of scope
for this case (see AFS Axis 2).

Sibling of the standing foundation smoke check in
``automation/tests/ui/smoke/test_foundation_cov60_surfaces_smoke.py``
(``test_analytics_overview_leaderboard_drill_to_user_detail_and_back``) —
that file is NOT a substitute for this dedicated, AFS-traced spec; both stay.

Spec: test-specs/analytics/l3_overview-leaderboard-drill-to-user-detail-and-back_GAP-073.md
GAP-073 is a coverage-gap ledger case (board `cov60`) — no onetest TMS entry;
back-write is a local-file edit, not an `@allure.issue` link.

Markers:
    - ui: requires browser
    - analytics: Analytics dashboard tests
    - p3: frontmatter priority is "medium"/l3 — matches pytest.ini's p3
      marker, the project's l3-to-pN convention (see e.g. ELITEA-1883's
      l3 -> p3 mapping)
"""

import allure
import pytest
from pages.analytics_page import ANALYTICS_QUERY_TIMEOUT, AnalyticsPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.analytics]

USER_DETAIL_KPI_CARDS = (
    "llm_calls",
    "tool_calls",
    "chat_msg",
    "agent_runs",
    "active_days",
    "errors",
)


@pytest.mark.p3
@pytest.mark.regression
def test_overview_leaderboard_row_drills_to_user_detail_and_back(page):
    """Leaderboard row click -> Users tab pre-loaded on that user's detail;
    Back -> Overview (not the Users list) (GAP-073)."""
    analytics_page = AnalyticsPage(page)

    console_messages = []
    page.on(
        "console",
        lambda msg: console_messages.append(msg) if msg.type == "error" else None,
    )

    with allure.step(
        "Step 1 — Navigate to Analytics; select Last 30d; wait for the "
        "Overview KPI cards and the Top 5 AI Adopters leaderboard"
    ):
        analytics_page.navigate_to_analytics()
        analytics_page.select_last_30d()
        expect(analytics_page.overview_kpi_team).to_be_visible(timeout=ANALYTICS_QUERY_TIMEOUT)
        row_count = analytics_page.get_leaderboard_row_count()
        assert row_count >= 1, (
            "'Top 5 AI Adopters' leaderboard should render at least one row "
            "with the Last 30d preset selected"
        )

    with allure.step("Step 2 — Capture the first leaderboard row's email"):
        captured_row_text = analytics_page.first_leaderboard_email()
        assert captured_row_text, (
            "First leaderboard row's text should be non-empty (contains "
            "the user's email)"
        )

    with allure.step(
        "Step 3 — Click the first leaderboard row; the view switches to the "
        "Users tab and renders that user's detail directly"
    ):
        analytics_page.click_first_leaderboard_row()
        assert analytics_page.user_detail_title.first.is_visible(), (
            "User-detail title should be visible immediately after clicking "
            "the leaderboard row — the drill-down renders the detail view "
            "directly, not the User Activity list first"
        )

    with allure.step(
        "Step 4 — Assert the user-detail title equals the captured email, "
        "and all six user KPI cards are visible"
    ):
        detail_title = analytics_page.user_detail_title_text()
        assert detail_title in captured_row_text, (
            "User-detail title should match the leaderboard row that was "
            f"clicked. Title: {detail_title!r}, captured row text: "
            f"{captured_row_text!r}"
        )
        for kpi in USER_DETAIL_KPI_CARDS:
            assert analytics_page.is_user_detail_kpi_visible(kpi), (
                f"User-detail KPI card '{kpi}' should be visible"
            )

    with allure.step(
        "Step 5 — Assert the Users tab did NOT land on the User Activity "
        "list — its title and search box are absent"
    ):
        assert not analytics_page.is_users_list_showing(), (
            "The native Users-list (title + search input) should be absent "
            "while the cross-tab drill-down detail view is showing — the "
            "drill-down bypasses the list entirely (structural mutual "
            "exclusion, not a visibility toggle)"
        )

    with allure.step(
        "Step 6 — Click the user-detail view's Back arrow"
    ):
        analytics_page.click_user_detail_back()

    with allure.step(
        "Step 7 — Assert the Overview tab is active again: KPI cards and "
        "the Top 5 AI Adopters leaderboard are visible (not the Users list)"
    ):
        expect(analytics_page.overview_kpi_team).to_be_visible(timeout=ANALYTICS_QUERY_TIMEOUT)
        assert analytics_page.get_leaderboard_row_count() >= 1, (
            "Leaderboard should re-render with at least one row after "
            "returning to Overview"
        )
        assert not analytics_page.is_users_list_showing(), (
            "Back from the cross-tab detail view should land on Overview, "
            "not the Users list (proves the cameFromExternal=true "
            "onBackToSource branch fired, distinct from the native "
            "Users-tab drill-down's Back -> list branch)"
        )

    with allure.step(
        "Side-channel check — no console errors across the full "
        "navigate -> drill-down -> Back cycle"
    ):
        assert not console_messages, (
            "Unexpected console errors during the leaderboard drill-down "
            f"cycle: {[m.text for m in console_messages]}"
        )
