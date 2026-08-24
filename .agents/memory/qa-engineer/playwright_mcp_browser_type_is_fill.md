---
name: Playwright MCP browser_type maps to fill() — destroys CodeMirror documents
description: browser_type on a contenteditable replaces the WHOLE document; use a pytest scratch spec with keyboard.type() instead
type: feedback
aliases: [browser_type fill, codemirror fill destroys, mcp type contenteditable, raw json editor wiped]
tags: [area/playwright-mcp, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## What happened

Analysing ELITEA-1935 I needed to replace ONE line inside the Remote MCP Raw
Json CodeMirror editor. I selected the line (`Home` / `Shift+End`) and called
`mcp__playwright__browser_type` on the editor element.

`browser_type` compiles to **`locator.fill(...)`**, not `keyboard.type(...)`.
On a contenteditable root, `fill()` replaces the **entire document**: 29 lines
of JSON collapsed to the single line I passed. The selection I had carefully
made was irrelevant.

## The rule

**`browser_type` is only safe on a real `<input>`/`<textarea>`.** For any
contenteditable / rich editor (CodeMirror, ProseMirror, Monaco), it is a
document-nuke.

There is no MCP tool that maps to `keyboard.type()` — `browser_press_key` is
one key per call, which is unusable for a 37-character string.

## What to do instead

Drive it through the project's own page object in a throwaway pytest spec:

```python
# automation/tests/ui/<area>/test_scratch_<case>.py  — delete after
form.fill_raw_json_line('"read_wiki_contents",', '"ask_question", "read_wiki_contents",')
```

`McpFormPage.fill_raw_json_line()` uses `page.keyboard.type()`, which respects
the selection. This is also strictly better analysis: it validates the exact
helper the implementer will call, so the AFS's automation hints are proven
rather than guessed. Run with
`HEADLESS=true ../.venv/bin/pytest <file> -q -p no:cacheprovider -o addopts="" --log-cli-level=WARNING`
and read the values off `logger.warning` lines.

Nothing was lost in the incident — the wiped editor left Save disabled (no PUT
fired) and a reload restored it. But it cost two probes.

Related: [[browser_console_messages_all_true_is_expensive]]
