---
name: Static review — import-check every page-object attribute a new spec calls
description: A fix round can add page-object calls without adding the method; hasattr via the venv catches it statically in one turn.
type: feedback
aliases: [missing page object method, AttributeError static review, wait_for_tab_settled]
tags: [area/review, type/technique]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

PR #1945 (settings-w06, ELITEA-2314..2319): the last fix commit (`90c258b04`,
"settle tab renders") added **five** calls to `analytics_page.wait_for_tab_settled(...)`
in `test_analytics_date_filter_content_refresh.py` but never added the method to
`AnalyticsPage` or `BasePage`. Nothing in a diff read flags it — the call site looks
exactly like the sibling `wait_for_overview_settled()` two lines above, which does exist.
The spec cannot even reach its first assertion (`AttributeError`), so the "green" claim
for that fix round was impossible.

## The check (static, ~5 s, no browser, no suite)

```bash
cd automation && ../.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
from pages.analytics_page import AnalyticsPage
for a in ('wait_for_tab_settled','wait_for_overview_settled'):
    print(a, hasattr(AnalyticsPage, a))
"
```

Collect the attribute names the diff's spec files call on the page object
(`grep -oE 'analytics_page\.[a-z_]+' <spec>` | sort -u) and `hasattr` them all.
Importing the page-object module is a pure static import — it starts no browser and
does not violate the static-review contract.

## When to run it

Any review round where a **fix commit** touched a spec but the page object's diff is
small or untouched. That asymmetry (new call sites, no new methods) is the smell.

Related: [[mui_datetimepicker_automation]]
