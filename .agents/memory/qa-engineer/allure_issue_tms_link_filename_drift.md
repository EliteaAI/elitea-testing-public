---
name: allure.issue TMS link must be checked against the real case filename
description: Reviewer check — the @allure.issue onetest URL is hand-typed from the slug and silently 404s when the TMS filename differs
type: feedback
aliases: [allure issue link, TMS case link, onetest case url, traceability link]
tags: [area/review, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

Every Elitea UI spec carries an `@allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/<area>/<CASE-ID>_<slug>.md", "onetest-ai Test Case link")`
decorator. The slug is hand-typed from the case TITLE, but the TMS filename is its
own string — they drift. Nothing in the suite validates it: the decorator is inert
metadata, so the test is green and the Allure report ships a 404.

Caught on ELITEA-1942 (PR #1739): spec linked
`ELITEA-1942_mcp-dashboard-filter-by-type-remote.md`, real file is
`ELITEA-1942_mcp-dashboard-filter-by-type-remote-only.md` (`-only` suffix).

## The check (one command, do it on every spec-adding review)

```bash
grep -n "onetest-ai-tm-Elitea/blob" <spec>            # the URL as typed
ls ../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/<area>/ | grep <CASE-ID>
```

Same class as the `automation_test_id` Form-C drift (`.agents/test-automation.yaml`
§ backwrite_on_done): a hand-derived reference that fails silently, never loudly.

Related: [[project_briefing]]
