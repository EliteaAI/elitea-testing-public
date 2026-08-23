---
name: CodeMirror text reading and line editing in Elitea
description: .cm-content text_content() drops newlines (splitlines is a trap); Shift+Home is how you REPLACE a line rather than append
type: reference
aliases: [cm-content newlines, codemirror line replace, get_file_preview_content_text, shift+home line edit, cm-line]
tags: [area/artifacts, area/editor, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## Reading: `.cm-content` `text_content()` has NO line separators

`ArtifactsPage.get_file_preview_content_text()` (and any `text_content()` on a
CodeMirror `.cm-content` node) returns every line concatenated with **nothing
between them**. Live sample, artifacts file-preview editor, 2026-08-23:

```
'# Project OverviewThis is a **bold** statement about the project.## ScopeCovers…'
```

So **`.splitlines()[0]` returns the whole document, not line 1.** Any assertion
phrased "line N shows X" needs a different shape:

- unique-substring pair — `to_contain_text(new)` + `not_to_contain_text(old)`
- whole-content **byte-equality** against a captured baseline (the right shape
  for "content reverted" / "content intact" claims)

Cost when missed: a probe read that looks like the edit landed everywhere.

## Writing: append vs REPLACE a line

`ArtifactsPage.edit_file_preview_line_containing(match, text)` **appends** —
it clicks the `.cm-line` filtered by text, presses `End`, and types. Cases that
need to *replace* a line need one extra keystroke:

```python
line.click()
page.keyboard.press("End")
page.keyboard.press("Shift+Home")   # select back to line start
page.keyboard.type(new_text)        # replaces the selection
```

Verified 2/2 on ELITEA-1859/1860 (swapping `# Project Overview` →
`# Modified Heading`). `Control+Home` still does NOT reliably reach document
start in this CodeMirror instance — filter `.cm-line` by text instead.
`.cm-line` is a `#579` sanctioned raw handle, scoped under the testid'd
content parent, and belongs in a page-object method, never inlined in a spec.

Related: [[no_playwright_mcp_use_sync_playwright_script]]

## Caveat: `Shift+Home` selects the VISUAL line, not the logical one

CodeMirror 6's `standardKeymap` binds `Shift+Home` to
`selectLineBoundaryBackward` — the start of the **visual** (wrapped) line. On a
short, unwrapped line (headings, the ELITEA-1859/1860 case) that is the logical
line start and the replace recipe above is exact. On a **long line that soft-wraps**
in the editor's width, it selects only back to the wrap point, so `type()` replaces
a *fragment* and the assertion pair (`to_contain_text(new)` +
`not_to_contain_text(old)`) can still pass while the line is mangled. If
`replace_file_preview_line_containing()` is ever pointed at a long line, press
`Shift+Home` twice (second press extends to the logical start) or verify the
whole-content byte-equality shape instead. Raised during static review of
PR #1691 (2026-08-23); not a defect in that PR — its target line cannot wrap.
