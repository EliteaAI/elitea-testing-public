---
name: Provenance grep misses evaluate_all
description: The canon's `\.evaluate\(` substitution grep does not match `.evaluate_all(` — widen it or judge those call sites by hand
type: feedback
aliases: [evaluate_all, provenance grep blind spot, substitution grep]
tags: [area/review, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## The gap

The canonical provenance/substitution grep (`.agents/role-overrides.md` § Reviewer slot,
`.agents/workflow.md` § Reviewer provenance check) is:

```
grep -nE '^[+].*(\.mock_|page\.route\(|route\.fulfill\(|monkeypatch|\.evaluate\()'
```

`\.evaluate\(` does **not** match `.evaluate_all(` — the `(` is escaped and literal, so a
diff full of `locator.evaluate_all(...)` returns **0 hits** and looks clean.

Seen on PR #1783 (ELITEA-2255/2256/2260): two `evaluate_all` call sites
(`pages/notification_center_page.py` `get_rendered_row_ids`,
`pages/settings_drawer_page.py` `nav_item_visibility_metrics`). Both were legitimate —
pure READS (`getAttribute`, `getBoundingClientRect`, `scrollHeight`/`clientHeight`), no
injection, no fabricated value — but the grep proved nothing about them either way.

## What to do

Run the widened form and judge every hit by hand:

```
grep -nE '^[+].*(\.mock_|page\.route\(|route\.fulfill\(|monkeypatch|\.evaluate(_all)?\()'
```

In-page JS is COMPLIANT when it only *measures* what the product already rendered
(scroll metrics and bounding boxes have no Playwright API equivalent). It is a
substitution when it *writes* state or synthesizes an interaction the user would perform
(`el.click()` to drive the case's own step, store writes, attribute setting).

Related: [[afs_claims_need_full_sweep_and_grep]]
