---
name: Analytics TMS case links live under settings/analytics, not settings-analytics
description: This repo's AFS directory name (test-specs/settings-analytics/) is NOT the TMS folder path — copying it into @allure.issue URLs 404s silently
type: reference
aliases: [allure.issue 404, settings-analytics, onetest case path, dead TMS link]
tags: [area/tms, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## The mismatch

| Where | Path |
|---|---|
| AFS directory, THIS repo | `test-specs/settings-analytics/` |
| TMS case files, `EliteaAI/onetest-ai-tm-Elitea` | `tests/automated-full-regression-ui/settings/analytics/` |

The hyphenated AFS folder name leaked into three `@allure.issue` URLs on PR
#1956; `settings-analytics/` does not exist in the TMS repo at all, so every
link 404'd. Verified with `git ls-files` in the sibling clone.

Two habits that cost nothing:

1. **Copy the path from a merged sibling spec**, never from the AFS slug
   (`test_analytics_tools_tab.py` et al. already carry the right shape).
2. **A parameterized spec owes one `@allure.issue` per case it automates** —
   the bar-chart spec had a single folder-only URL for two cases, so
   ELITEA-2328 was untraceable even before the path was wrong.

A dead Allure link never fails a run. The static guard shape this repo already
uses (`tests/unit/test_*_allure_issue_links.py`, ~6 of them) resolves each link
against the sibling clone on the local filesystem — no network.

Related: [[negative_text_wait_needs_use_inner_text]]
