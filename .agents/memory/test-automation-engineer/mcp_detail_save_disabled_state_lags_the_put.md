---
name: MCP detail Save button's disabled state lags the PUT response
description: save_and_wait_for_updated() returns at the PUT; the Save button is still enabled for a tick or two — assert it with expect(), never is_disabled()
type: reference
aliases: [save button disabled race, detail_save_button, is_disabled snapshot read, formik dirty reset]
tags: [area/toolkits, type/flake]
created: 2026-08-24
updated: 2026-08-24
---

## The race

`McpFormPage.save_and_wait_for_updated()` returns the moment the
`PUT /tool/prompt_lib/{project}/{id}` 200 arrives. The detail page's Save button
is disabled off **Formik dirty-state**, which only resets after React processes
that response *and* the follow-up GET refetch lands — one or more ticks later.

So this is a coin flip, not an assertion:

```python
save_response = form.save_and_wait_for_updated(project_id, toolkit_id)
assert form.detail_save_button.is_disabled()      # ← snapshot read at the worst tick
```

Correct shape (retries until the state settles):

```python
expect(form.detail_save_button).to_be_disabled(timeout=UI_STATE_TIMEOUT)
```

## The general rule this instantiates

Every UI-state check that FOLLOWS a click or a navigation must retry.
`is_visible()`, `is_disabled()`, `is_enabled()`, `get_attribute()` and
`text_content()` are single-shot reads — they pass or fail on whichever tick
they happen to land. Playwright's `expect()` polls. Caught by review on
ELITEA-1935 (PR #1724, fix round 1); the same file had three more instances of
the class (detail heading, `aria-pressed` on the view toggle, editor visibility
after `switch_to_raw_json_view()`), all converted in the same round.

Related: [[codemirror_selectionmatch_breaks_line_locators]]
