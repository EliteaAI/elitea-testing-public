---
name: CodeMirror gutter hidden spacer element is first in DOM order
description: .cm-gutterElement:nth(0) reads a hidden width-measurement spacer, not line 1 — always filter :visible
type: project
---

Discovered during ELITEA-2026 (Pipeline YAML editor view) implementation.

CodeMirror's line-number gutter (`.cm-gutters .cm-lineNumbers .cm-gutterElement`)
renders a **hidden, zero-height spacer element FIRST in DOM order** —
`style="height: 0px; visibility: hidden; pointer-events: none;"` — whose text
content is a width-measurement placeholder (observed `"99"` on a 22-line YAML
doc: CodeMirror sizes the gutter column to fit the largest expected
line-number's digit count). This is NOT line 1's actual number.

`.locator(".cm-gutterElement").nth(0)` therefore reads the spacer, not the
first visible line. Fix: append `:visible` to the selector —
`.cm-gutterElement:visible` — Playwright's own pseudo-class works fine
scoped under a real `LocatorDescriptor` parent
(`self.yaml_editor.locator(".cm-gutters .cm-lineNumbers .cm-gutterElement:visible")`).
After the filter, `.nth(0)` is genuinely line 1, and `.count()` matches the
editor's real line count (join `.cm-line` content and count `\n`-split
lines to cross-check).

This is a sanctioned #579 exception (CodeMirror internal render nodes) — same
shape/precedent as the pre-existing `YAML_LINE_SELECTOR = ".cm-line"` on
`PipelineDetailPage`. New sibling class constant added:
`YAML_GUTTER_LINE_SELECTOR = ".cm-gutters .cm-lineNumbers .cm-gutterElement:visible"`.

Verified live via `page.evaluate()` dumping every `.cm-gutterElement`'s
text/class/style — confirms the pattern is deterministic, not a race.
Applies to any CodeMirror-backed editor in EliteaUI (pipeline YAML editor,
possibly others sharing the same CodeMirror config), not just this case.
