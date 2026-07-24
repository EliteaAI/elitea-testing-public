---
name: get_yaml_content()'s pipeline-yaml-lines testid can lag CodeMirror's own render (race)
description: PipelineDetailPage.get_yaml_content()'s app-added per-line testid tagging can transiently show 0 lines right after a Flow-view state change, even though CodeMirror's native .cm-line divs already hold the real text — falls through to a single-blob text_content() that concatenates gutter digits + fold glyphs into unparseable YAML. Fixed with an additive #579-sanctioned CodeMirror .cm-line fallback tier, scoped inside the yaml_editor testid parent.
type: feedback
---

ELITEA-2018 (PR #1028): calling `PipelineDetailPage.get_yaml_content()`
immediately after `switch_to_yaml_view()` — in a session that had already
done canvas interactions (node select, delete-confirm) beforehand — hit
`self.yaml_lines.count() == 0` even after an explicit
`wait_for(state="attached", timeout=3000)` on the first line. The method's
existing fallback (`self.yaml_editor.text_content()`) then returns a
single-line string with the CodeMirror gutter's line-number digits and
fold-toggle glyphs (`›⌄⌄⌄⌄⌄⌄`) mashed into the front, no newlines at all —
`yaml.safe_load()` on that raises `ScannerError: mapping values are not
allowed here`. Waiting longer (`wait_for(state="attached")`, up to 3s) did
NOT resolve it — the app's own `data-testid="pipeline-yaml-lines"` tagging
effect on each `.cm-line` appears to lag CodeMirror's render pass
specifically after this kind of Flow-view state change, not just on first
mount.

**Fix (additive, in `pipeline_detail_page.py`):** when the testid-tagged
`yaml_lines.count()` is 0, try `self.yaml_editor.locator(".cm-line")`
(CodeMirror's own per-line class, scoped inside the already-testid'd
`yaml_editor` parent) before falling through to the single-blob
`text_content()` branch. This is a NEW instance of the #579 sanctioned
scoped-raw-handle exception (same shape as the existing
`mcp_form_page.py:121` `fill_raw_json_line()` precedent) — declare it
explicitly in the docstring + PR description, don't just add it silently.
Zero behavior change for the pre-existing `line_count > 0` path (both
existing callers already always hit that path).

If you hit `yaml.scanner.ScannerError: mapping values are not allowed
here` from `get_yaml_content()`'s output, this is almost certainly the
same race — check for the `›⌄` glyph signature before assuming a genuine
product YAML-formatting bug.
