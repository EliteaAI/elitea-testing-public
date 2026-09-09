---
name: agents_list_page.navigate() aborts with net::ERR_ABORTED on dev.elitea.ai
description: Pre-existing DEV-only flake at Step 5 of the import specs — raw error at a precondition, ~50% of invocations, not a spec defect
type: project
aliases: [ERR_ABORTED, net::ERR_ABORTED, agents/all goto abort, import spec DEV flake]
tags: [area/agents, type/flake]
created: 2026-09-09
updated: 2026-09-09
---

## The signature

```
playwright._impl._errors.Error: Page.goto: net::ERR_ABORTED at https://dev.elitea.ai/app/agents/all
  - navigating to "https://dev.elitea.ai/app/agents/all", waiting until "domcontentloaded"
```

Raised from `AgentsListPage.navigate()` → `BasePage.navigate()` →
`page.goto(url, wait_until="domcontentloaded")` (via `conftest.py:443`
`goto_with_banner_dismiss`). Allure status **`broken`**, not `failed`.

## Where it fires

`test_import_agent_valid_md_file.py` Step 5 — the re-open of the Agents
dashboard immediately after the wizard auto-navigates to the imported agent's
detail page. The detail URL carries a project segment
(`/app/399/agents/all/10440?viewMode=owner&...`) while `navigate()` targets the
segment-less `/app/agents/all`; the app's own client-side redirect back to the
project-scoped route is the most likely aborter. **Localhost does not show it.**

## Rate, measured 2026-09-09 (DEV, 11 invocations)

| Code under test | Invocations | Hit ERR_ABORTED |
|---|---|---|
| repaired branch `tests/adjust-ELITEA-1901-…` | 8 | 4 |
| pristine `automation/base` (matched control) | 3 | 3 |

**Pre-existing and repair-independent** — the control settles it. `--reruns=2`
absorbs it about half the time, so it surfaces as either a silent rerun or a
hard red.

## How to respond

It fires at a **precondition**, upstream of every assertion the case makes, so
it can never be a member of a sanctioned-RED set: **re-run, never accept
2-of-3**. Do not raise the timeout — the navigation is cancelled, not slow.
The durable fix is the #1847 family: navigate to the project-scoped route, or
retry the goto on `ERR_ABORTED`.

⚠️ Passing runs hide it: `-q` output shows no log line, and junit records PASS.
Evidence lives in `reports/allure-results/*-result.json` (`"status": "broken"`).

Related: [[dev_model_catalog_turnover_gpt52_removed]] · [[retarget_suite_at_dev_without_editing_env_test]]
