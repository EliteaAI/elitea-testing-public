---
name: Phase-2 amendments leave stale claims outside the AFS steps
description: When an implementer amends an observable mid-build, check 5 other surfaces — docstring, allure description, constants comment, page-object description, _surface.md
type: feedback
aliases: [phase-2 amendment drift, stale allure description, stale surface digest, amendment triangulation]
tags: [area/review, type/gotcha]
created: 2026-08-21
updated: 2026-08-21
---

## The pattern

The combined analyst+implementer slot amends an observable during Phase 2 (a
racy oracle swapped out, a sort order disproven live). The amendment is written
carefully into the **AFS Test Steps** — and nowhere else. Everything that
*restates* the old contract stays behind and now lies.

On PR #1618 (ELITEA-1803/1804/1805) two amendments produced **eight** stale
claims across five files:

| Amendment | Stale in |
|---|---|
| footer oracle: API bucket list → rendered rows | test module docstring · `artifacts_page.py` `buckets_footer_count` description (still says "cross-check against `ArtifactAPI.list_buckets()`") · `_surface.md` handle table row · AFS 1803 + 1805 Coverage-Map row 10 ("regex + API cross-check") |
| page 2 slice → page partition (sort is NOT name-ascending) | test module docstring · `@allure.description` (ships to the report as the test's stated contract) · the `PAGINATION_FILE_COUNT` comment ("the file table sorts by name ascending") · AFS § Expected Results |

## Reviewer checklist when you see "Implementation amendment (Phase 2)" in an AFS

Grep the old claim's keywords across the whole diff, not just the AFS:
`git diff <base>...HEAD | grep -niE '<old oracle|old sort|old literal>'`. Check
in this order — the last three are the ones that keep getting missed:

1. AFS § Expected Results and § Coverage Map "Asserted where" column
2. test module docstring
3. `@allure.description` / `@allure.title` (this one SHIPS to the report)
4. the constants block comment that motivated the old design
5. the page-object `LocatorDescriptor(description=...)` and `_surface.md`
   handle table — these two are *instructions to the next engineer*, so a
   stale one actively sends them back down the path already proven wrong

Related: [[no_playwright_mcp_use_sync_playwright_script]]
