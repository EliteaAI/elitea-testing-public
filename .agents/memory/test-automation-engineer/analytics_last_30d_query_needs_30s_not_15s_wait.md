---
name: Analytics "Last 30d" backend query genuinely needs ~30s, not 15s, under campaign load
description: AnalyticsPage's Overview/user-detail waits (select_last_30d, click_first_leaderboard_row, click_user_detail_back) failed 3/3 with Locator.wait_for 15000ms timeouts during a live multi-session campaign — screenshot evidence showed the tab's own loading spinner still active, a real in-flight backend aggregation query, not a stuck/broken UI. Widened to ANALYTICS_QUERY_TIMEOUT = 30_000.
type: feedback
---

## What happened (GAP-073 foundation smoke, cov60 campaign)

`test_analytics_overview_leaderboard_drill_to_user_detail_and_back` passed
clean in isolation (twice, at different points in the same session) but
failed 3/3 (1 attempt + pytest-rerunfailures' 2 auto-reruns, all matching the
`TimeoutError` `--only-rerun` pattern) immediately after merging in unrelated
concurrent `automation/base` work. The failure was always the same:
`Locator.wait_for: Timeout 15000ms exceeded` waiting on
`analytics-overview-kpi-team` or `analytics-user-detail-title`.

Read the actual failure screenshot
(`test_analytics_..._FAIL_20260724_091845.png`) instead of assuming flakiness
— it showed the Analytics Overview tab's own loading spinner still spinning
at the 15s mark, tabs/filters all rendered correctly. This is a genuine
in-flight backend aggregation query for the wider 30-day window, not a hang,
not a JS error, not a locator mismatch. An even earlier session (screenshot
timestamped 2 hours prior) hit the exact same failure/recovery pattern —
consistent with this being latency that scales with **concurrent backend
load** (this campaign runs many simultaneous implementer sessions hitting
the same shared DEV backend), not a one-off fluke.

## The fix

Added `ANALYTICS_QUERY_TIMEOUT = 30_000` in `pages/analytics_page.py` and
used it for the three DATA-dependent waits: `select_last_30d()` (KPI team
card after clicking Last 30d), `click_first_leaderboard_row()` (user-detail
title after drilling in), `click_user_detail_back()` (KPI team card again
after returning to Overview) — plus the smoke test's matching `expect(...)`
calls. Left `navigate_to_analytics()`'s wait for the static
`date_preset_30d_button` at 15s — that one waits on a static UI element, not
a data fetch, and showed zero failures across every run.

30s isn't an arbitrary bump — it matches this codebase's own existing
precedent for backend-bound waits: `BasePage`/`ChatPage`/
`guardrails_admin_page.py`'s `wait_for_load_state("networkidle",
timeout=30000)`.

## Takeaway for whoever automates GAP-073's dedicated case (or touches
AnalyticsPage again)

If you see a timeout on `analytics-overview-kpi-team` or
`analytics-user-detail-title` after selecting a wide date range, **check the
screenshot for a still-spinning loader before assuming a locator/product
bug** — this is a documented, real backend-latency characteristic under
load, not flakiness to paper over with a blind retry, and not (yet, as of
this writing) a filed product-performance defect.
