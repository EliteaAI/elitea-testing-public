---
name: Blast radius of an in-place page-object repair is settled by class hierarchy, not method-name grep
description: Identically-named methods live on unrelated page-object classes; grep the class bases before trusting or rejecting a caller count.
type: feedback
aliases: [blast radius, close_versions_menu, same-named methods, in-place page object fix]
tags: [area/page-objects, type/review-check]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

`close_versions_menu()` exists on **three** page objects —
`AgentDetailPage`, `PipelineDetailPage`, `SkillDetailPage` — and
`open_version_selector()` on the same three. A flat
`grep -rn "close_versions_menu" automation/` returns ~20 hits across agents,
pipelines and skills specs and makes an in-place fix look reckless.

It is not, if the classes are unrelated:

```
AgentDetailPage(AgentFormPage)          # pages/agent_detail_page.py:30
PipelineDetailPage(PipelineFormPage)    # pages/pipeline_detail_page.py:35
```

No inheritance edge, so a change to one reaches only its own callers.

## The check, in order

1. `grep -n "^class " pages/<a>.py pages/<b>.py` — settle the hierarchy first.
2. Then scope the caller grep to `--include='*.py' pages/ tests/` (an unscoped
   `grep -rn` over the repo pulls in `reports/allure-results/` and returns
   megabytes).
3. Only then judge whether "fix in place" vs "add a new method" is right.

The *semantic* question is separate and also matters: `AgentDetailPage`'s
`close_versions_menu` drives the **skill card's** plain MUI `Menu` (no search
field), which is why PR #2058 had to add a new method there; all three
`PipelineDetailPage` call sites drive the one searchable VERSION dropdown, so
that class could be fixed in place. Same name, different component.

Related: [[diagnostic_readback_needs_its_own_timeout]]
