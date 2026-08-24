---
name: wait_for_tool_result returns on ❌ as well as ✅
description: Toolkit Test-Settings runs need an explicit success-marker assertion — the wait helper resolves on failure too
type: feedback
aliases: [tool run result assertion, toolkit test settings run assertion, run tool green on error]
tags: [area/toolkits, type/review-trap]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

`ToolkitTestSettingsPage.wait_for_tool_result()`
(`automation/pages/toolkit_test_settings_page.py:441`) polls
`expect(result_locator).to_contain_text(re.compile(r"[✅❌]"))` — it resolves as
soon as the run message carries **either** marker, and returns the text either way.

A failed run renders `❌ <tool_key> (0.4s) <error text>`, so the common assertion

```python
result = test_settings.wait_for_tool_result()
assert TOOL_KEY in result          # passes on ❌ too
```

is satisfied by an **errored** run. The merged ELITEA-1937 spec avoids this by
also asserting real remote content (`"AsyncFuncAI/deepwiki-open" in result_text`,
`test_mcp_test_settings_select_and_run_tool.py:132`); ELITEA-1940's first
implementation did not, and would have gone fully green with both tool runs
failing (Run History still lists errored runs with timestamps + durations, and a
detail-pane `to_contain_text(repoName)` is satisfied by the INPUT echo
`Calling '<tool>' with parameters: {...}` alone).

## Rule when reviewing or writing a toolkit/MCP run test

Assert the **success marker** (`"✅" in result`) or real remote output content —
never the tool key alone. And when a case's expected is "input **and** output are
displayed", `to_have_count(2)` on `chat-message-item` proves structure, not that
the second item is an output rather than an error.

Related: [[toolkit_run_history_row_is_a_conversation]]
