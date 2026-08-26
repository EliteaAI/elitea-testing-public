---
name: Find the TMS case file path before writing an allure.issue link
description: settings cases live under settings/project-params/, not settings-project-params/ — a merged spec had a 404 link
type: feedback
aliases: [allure issue link, case link 404, onetest case path, tms case filename]
tags: [area/tms, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

The `@allure.issue` "onetest-ai Test Case link" is easy to get subtly wrong, and nothing
in the run validates it — a broken link ships silently.

Two ways it drifts, both seen on the merged ELITEA-2272 spec (repaired 2026-08-26):

1. **The directory is not the AFS/module slug.** The AFS folder is
   `test-specs/settings-project-params/` and the case frontmatter says
   `module: settings-project-params`, but the case FILE lives under
   `tests/automated-full-regression-ui/**settings/project-params/**`.
2. **The filename slug is truncated**, e.g.
   `ELITEA-2272_project-context-character-limit-is-enforced-at-2500-characte.md`
   (note the clipped final word) — not the tidy slug you would compose.

Always resolve it mechanically instead of composing it:

```bash
find ../onetest-ai-tm-Elitea/tests -name "*<ELITEA-id>*"
```
