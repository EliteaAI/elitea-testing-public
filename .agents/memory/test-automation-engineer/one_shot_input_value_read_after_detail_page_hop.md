---
name: One-shot input_value() read after a detail-page hop races form hydration
description: Replace `assert page.get_name() == x` after a navigation with a retrying `expect(...).to_have_value` helper — the MUI shell renders before the entity GET returns on DEV
type: feedback
aliases: [get_name race, empty name after import, expect_name, form hydration race, input_value one-shot]
tags: [type/feedback, area/page-objects, area/dev-env]
created: 2026-09-11
updated: 2026-09-11
---

## The hazard

`AgentFormPage.get_name()` (and the pipeline/skill equivalents) is a one-shot
`self.name_input.input_value()`. After a detail-page hop the MUI form shell renders
BEFORE the entity GET returns, so on DEV the read lands on the empty input:
`assert '' == 'el-1902-main-…'` 3/3 in nightly runs #126/#127 while the screenshot
showed the name populated. `pytest.ini --only-rerun` excludes `AssertionError`, so CI
gives this class zero reruns — it looks deterministic and product-shaped, and it is
neither.

Fully exposed sites are those reached via a redirect the page object does not hydrate
after — `AgentsListPage.confirm_import_complete()` (URL + `networkidle`, #1847 class)
then `verify_on_detail_page()` (URL only). Sites through `AgentDetailPage.navigate()`
are partly covered by `wait_for_page_load()`'s legacy raw `input#name` non-empty wait.

## The shape (ELITEA-1902 / #2261, PR #2268)

Additive `AgentFormPage.expect_name(expected, timeout, message)` =
`expect(self.name_input, message=message).to_have_value(expected, timeout=timeout)` —
same testid, same system-produced value, bounded retry, loud failure with expected +
actual. `get_name()` stays untouched (30 caller files; create-form tests read `""`).
Verified: localhost 1/1, DEV 3/3 with `reruns.json == {}`.

~45 sibling `get_name() ==` sites remain across agents/pipelines/skills/chat specs —
listed in PR #2268's body; pipelines/skills page objects need their own helper.

Related: [[a_settle_can_be_fragile_and_vacuous_at_once]] · [[mui_form_field_quirks]]
