---
name: Toolkit tool-result text has no newlines — parse, never pin a serialization
description: Chat/tool result payloads collapse in text_content(); assert the parsed structure, not one rendering of it
type: feedback
aliases: [tool result payload, prettifyToolkitMessage, list_files result, pretty-printed JSON drift, ELITEA-1866]
tags: [area/toolkits, type/assertion-design]
created: 2026-09-09
updated: 2026-09-09
---

## The drift (ELITEA-1866 / issue #2066)

A merged spec pinned a tool result as a substring of ONE serialization —
`"{'total': 0, 'rows': []}"`, a Python `repr`. EliteaUI's
`prettifyToolkitMessage` re-emits a tool message that is *exactly* a JSON
object through `JSON.stringify(parsed, null, 2)`; a Python-repr string is not
valid JSON, so that path used to be skipped. Once upstream serialization
started producing real JSON, the pin went red on a **correct** product — the
bucket really was empty.

**Assert the parsed structure, not the rendering.** Split the result text on
the `✅`/`❌` marker, regex the trailing `{...}`, `json.loads` with an
`ast.literal_eval` fallback, compare with `==`. That is strictly stronger than
a substring match (whole-payload equality) and survives drift in **either**
direction, so it needs no expected-result sign-off.

## The trap that breaks naive parsers

`text_content()` on the result message item returns **NO newlines**. The
payload renders in a fenced block whose syntax highlighter emits one element
per line with no newline text nodes, so the block collapses and each line's
two-space indent survives as a run of spaces: `{   "total": 0,   "rows": [] }`.
`innerText` does carry newlines; the page object reads `text_content()`.
Any parser keyed on `\n` is wrong here.

Shipped: `automation/utils/toolkit_result_payload.py`, pinned by
`automation/tests/unit/test_toolkit_result_payload.py`. Pure and browser-free
on purpose — the unit test needs no `page`, so it costs nothing at gate time.

Related: [[networkidle_1847_artifacts_landing_is_the_third_site]]
