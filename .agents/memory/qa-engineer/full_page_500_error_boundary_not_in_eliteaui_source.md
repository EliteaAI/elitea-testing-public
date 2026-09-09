---
name: Full-page branded 500 error page is NOT rendered by EliteaUI's own React source
description: A CI screenshot of Elitea's branded "500 Internal Server Error / Something went wrong on our end" page has zero matches anywhere in EliteaUI/src — it's an infra/gateway-level page, not an app ErrorBoundary. Useful signal when triaging a full-page (not console-only) 500 on a deployed env.
type: feedback
aliases: [500 error page, Internal Server Error page, Go to Elitea button, infra outage signature]
tags: [area/skills, area/ci-triage, status/transient-infra]
created: 2026-09-09
updated: 2026-09-09
---

## What happened

ELITEA-1740 (`test_skill_tag_filter.py`) failed on CI run 34331579791 (#114,
2026-09-09, DEV) — `assert list_page.skill_exists_in_list(skill_a_name)` failed
with a misleading message ("should be visible in the grid after creation").
The actual allure failure screenshot showed Elitea's own branded full-page
`500 Internal Server Error / Something went wrong on our end` screen (logo,
gradient "500", "Go to Elitea"/"Go Back" buttons) instead of the Skills grid
— i.e. `SkillsListPage.navigate()` landed on an error page, and the
point-in-time `skill_exists_in_list()` check correctly (if confusingly)
reported "not found."

## The tell

`git grep -n "Something went wrong on our end\|Go to Elitea" origin/main -- src/`
returns **zero hits** in `EliteaAI/EliteaUI`. This page is not part of the
React bundle at all — no `ErrorBoundary`, no `errorElement`, no static
`500.html` in `public/`. It is served by a layer in front of the app
(gateway/reverse-proxy/CDN) when the backend itself is unreachable/erroring,
not by app code reacting to a failed XHR.

**Diagnostic value:** if a failure screenshot shows this exact branded page,
you are looking at a **platform/infra-level outage window**, not a
Skills-specific (or any specific-feature) code defect — don't go hunting in
the feature's own source for a root cause; there won't be one there.

## Corroborating signal, same run

CI run 34331579791 failed 8 of 10 suite jobs (chat, toolkits, pipelines,
agents, artifacts, pipelines_2, agent_hub, skills) — sibling `[FIX]` cards
#2076–#2084 were all filed from this one run. A single run failing broadly
across unrelated feature areas is the same "session-wide backend strain"
signature already documented in `.agents/testing.md` § Unconfirmed (the
#1082 shared-test-user pollution class, the onboarding-w2 multi-symptom
entry, issue #2023's 10/10-job banner-race outage) — always check for
sibling `[FIX]` cards from the same run window before assuming a
feature-specific cause.

## What this does NOT excuse

`SkillsListPage.wait_for_page_load()` (called from `.navigate()`, used by
~16 skills test files) waits only for URL regex + `wait_for_network`
(networkidle) + best-effort banner dismissal — it never checks that the
navigation actually succeeded. `BasePage.navigate()` calls
`self.page.goto(url, wait_until="domcontentloaded")` and **discards the
returned `Response`** — capturing `resp.status` there and failing fast on
`>= 500` (a `Response.status` check, not a locator — no testid-policy
conflict) would turn a confusing 64s "element not visible" failure into an
instant, accurate "navigation to X returned HTTP 500" diagnostic. This is
honest hardening (Class D — hygiene/robustness), not masking: it never
touches what the test asserts about skill visibility/tags/filtering.

Related: [[skill_form_and_export_import_quirks]] · [[skills_list_search_quirks]]
