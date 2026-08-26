---
name: "@action decorator seam when inserting page-object methods"
description: Inserting a method above an existing def steals its @action; a unit guard now catches it
type: feedback
aliases: [action decorator seam, stolen decorator, stacked @action, page object insertion point]
tags: [area/page-objects, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## The failure

Appending new methods to `automation/pages/*.py` by "insert before line N" can land
the new block **between a pre-existing `@action("…")` and its `def`**. Both halves
fail silently — nothing raises, no test goes red:

- the first inserted method becomes double-decorated and logs/reports under the
  PREVIOUS method's step name;
- the pre-existing method LOSES its `@action`, so its merged callers stop emitting a
  step and stop getting `@action`'s screenshot-on-failure.

Shipped once in `artifacts_page.py` (ELITEA-1853/1854/1855, review round 1): the seam
stole `@action("Edit file preview content")` from `edit_file_preview_content`, whose
caller is `tests/ui/artifacts/test_artifacts_file_preview_edit_save.py`.

## The guard (use it, don't re-derive it)

`automation/tests/unit/test_page_object_action_decorator_seams.py` — AST scan over
`automation/pages/*.py`: no method may carry more than one `@action`, plus named
anchors for the two methods the original seam damaged. Runs in 0.2s, no browser.
`@action` records nothing on the wrapper (`utils/actions.py` closes over
`step_description`), so a source-level check is the only possible one.

## Habit

After inserting anything into a page object, look at the line ABOVE the insertion
point, and run that unit file. `git diff <base> -- automation/pages/ | grep -E '^-[^-]'`
stays empty either way — a stolen decorator is pure addition, so the additive-only
check does NOT catch it.

Related: [[project_briefing]]
