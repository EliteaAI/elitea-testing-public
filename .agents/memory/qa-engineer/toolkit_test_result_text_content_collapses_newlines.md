---
name: Toolkit test-run result — text_content() collapses the JSON block's newlines
description: The Test-Toolkit result renders as a highlighted <pre>; text_content() has no newlines, innerText does. Parse, never string-match.
type: feedback
aliases: [toolkit test result, wait_for_tool_result, list_files result, prettifyToolkitMessage, chat-message-list pre block]
tags: [area/toolkits, type/gotcha]
created: 2026-09-09
updated: 2026-09-09
---

## The fact

On the Test Toolkit surface (`/toolkits/{tab}/{id}/test`), a tool result whose payload is
*exactly* a JSON object is pretty-printed by `prettifyToolkitMessage`
(`EliteaUI/src/[fsd]/features/toolkits/lib/helpers/toolkits.helpers.js:247,266`) into a
fenced ```json block — `JSON.stringify(parsed, null, 2)`.

That block is syntax-highlighted **one element per line with no newline text nodes**, so:

| Read | Value |
|---|---|
| `text_content()` (what `ToolkitTestSettingsPage.wait_for_tool_result()` returns) | `... ✅ list_files (0.192s) {   "total": 0,   "rows": [] }` — **no `\n` at all** |
| `inner_text()` | `... {\n   "total": 0,\n   "rows": []\n }` |

Each line's 2-space indent survives in `text_content()` as the run of spaces. Verified live
2026-09-09 (localhost:5173, EliteaUI@automation/testids 6d285a00).

## Why it matters

Any assertion that string-matches a serialized payload here is pinned to a presentation
detail that has already moved once: ELITEA-1866's Step 31 pinned the **Python-repr** form
`{'total': 0, 'rows': []}` and went red when the same, still-correct empty result started
rendering as pretty JSON (issue #2066). A repair that assumes `\n` in `result_text` is
equally wrong.

## What to do instead

Split on the `✅`/`❌` marker, take the tail, extract `(\{.*\})\s*$`, then
`json.loads` with an `ast.literal_eval` fallback, and compare the **parsed structure**.
Bidirectional (handles both serializations), strictly stronger than a substring match, and
correctly fails on a non-empty result.

The `<pre>` block itself carries **no testid** and lives in the shared markdown renderer —
it is not testid-addressable, and it disappears entirely if serialization reverts (the
helper's `catch` path). Do not build the assertion on it.

Related: [[artifacts_landing_networkidle_wait_too_short]]
