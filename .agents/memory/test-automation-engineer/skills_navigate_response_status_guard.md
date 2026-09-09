---
name: SkillsListPage.navigate() fails fast on a non-OK navigation response
description: BasePage.navigate() returns the Response; SkillsListPage.navigate() raises AssertionError on a non-None, non-OK status before wait_for_page_load() times out
type: feedback
aliases: [navigate response status guard, non-OK navigation, 500 error page skills, issue 2074]
tags: [area/skills, area/page-objects]
created: 2026-09-09
updated: 2026-09-09
---

## What changed (issue #2074, PR #2088)

`BasePage.navigate(path) -> Response | None` now returns the `Response` from
`self.page.goto(...)` — previously discarded. Not stashed on `self`: returning
it ties the check to the navigation that produced it, so a later UI-click
navigation elsewhere can't read a stale value. `None` is preserved as a
legitimate return (some same-document navigations produce it) — callers must
treat that as "no information," never a failure.

`SkillsListPage.navigate()` captures that response and, only when it is not
`None` and `not response.ok`, raises `AssertionError(f"Navigation to
/skills/all returned HTTP {response.status} — the app served an error page,
not the Skills list.")` **before** calling `wait_for_page_load()`.

## Why

A transient gateway/proxy 500 served in front of the app (confirmed: the
error page's markup does not exist anywhere in EliteaUI's `src/` —
`git grep "Something went wrong on our end" origin/main -- src/` → 0 hits)
used to sail straight through `navigate()`, then `wait_for_page_load()` would
burn its full timeout waiting on a URL regex that never resolved, and finally
whatever downstream assertion ran first (e.g. `skill_exists_in_list()`) would
fail with a message that misleadingly blamed the Skills feature for an
infra-level failure ~64s later.

## Pattern for other page objects

If another list/detail page's `navigate()` override wants the same
diagnosability guard: capture `super().navigate(path)`'s return, check
`response is not None and not response.ok` BEFORE the page's own
`wait_for_page_load()`, and raise `AssertionError` naming the HTTP status.
Zero locator involved — it's a `Response.status` integer check, not a
DOM/text match on the error page (deliberately, since that page carries no
testids and isn't app DOM).

Related: [[skills_search_el2597_data_pollution]]
