---
name: One-shot input_value() after navigation races form hydration
description: A bare `get_x() == expected` right after a URL/networkidle wait reads the empty MUI shell on DEV — review for it, demand `expect().to_have_value`
type: feedback
aliases: [name hydration race, get_name empty string, input_value race, to_have_value]
tags: [type/feedback, area/review, area/agents]
created: 2026-09-11
updated: 2026-09-11
---

## The pattern (ELITEA-1902 / #2261 / PR #2268)

`confirm_import_complete()` (URL regex + `networkidle`) and `verify_on_detail_page()` (URL only) both
return before the agent GET populates the MUI form, so `AgentFormPage.get_name()` = one-shot
`name_input.input_value()` read `''` 3/3 on DEV nightlies #126/#127 while the screenshot showed the
name populated. `pytest.ini --only-rerun` excludes `AssertionError`, so CI gave it zero reruns.

## What to demand at review

- After ANY navigation/redirect, a value read from a form field must be an auto-retrying assertion
  (`expect(locator, message=…).to_have_value(expected, timeout=…)`), not `assert get_x() == y`.
  Same strength (equality, fails loudly with expected + actual), bounded wait instead of a racing read.
- Verified on Playwright 1.61.0: `Expect.__call__(actual, message=None)` in `sync_api/__init__.py:100`;
  custom message is prefixed, driver `errorMessage` still carries the actual value.
- Page-object `expect_*` helpers are an established shape (`secrets_page.py:921`,
  `generate_entity_modal_page_base.py:156`) — not an improvisation.
- `AgentDetailPage.navigate()` is protected by `wait_for_page_load()` (raw `input#name`
  `wait_for_function`, legacy #25/#42); sites reached via `confirm_import_complete()` or a
  saved-form redirect are NOT. PR #2268's body lists ~50 sibling one-shot sites across agents /
  pipelines / skills / chat — a migration card, not per-PR nits.

Related: [[project_briefing]]
