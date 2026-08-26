---
name: A retired query param silently red-lined a merged spec
description: Check whether the merged spec on your surface still passes before building on its page object — a product route change can have broken it months ago.
type: feedback
aliases: [view=create, project context character limit, stale page object, click_create timeout]
tags: [area/settings, type/suite-health]
created: 2026-08-26
updated: 2026-08-26
---

## What happened

Analysing ELITEA-2266/2267/2276 (2026-08-26) I was about to reuse
`ProjectContextPage.click_create()` as transit. Reading it showed
`wait_for_url("**{PROJECT_CONTEXT_PATH}?view=create")`, but live the Create button lands
on `/settings/project-context/edit`. Ran the merged spec to confirm:

```
TimeoutError: Timeout 10000ms exceeded.
waiting for navigation to "**/settings/project-context?view=create" until 'load'
```

`tests/ui/admin/test_project_context_character_limit.py` (ELITEA-2272) had been red on
`automation/base` since the product retired the query param. Nothing surfaced it —
there is no CI on `automation/base`, so a merged spec only fails when someone runs it.
Filed as **#1794**.

## The habit worth keeping

When § 2b "read the neighbours" turns up a merged spec on your surface, **run it** —
one invocation, a couple of minutes. It is the cheapest possible check and it either
gives you a working transit path or hands the lead a real finding. Reading the page
object is not enough; a stale URL wait looks perfectly reasonable in source.

Related: [[project_context_three_views_no_view_query_param]]
