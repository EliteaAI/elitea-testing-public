---
name: CodeMirror body — contentTestId exists, and read it with inner_text()
description: Field.CodeMirrorEditor already accepts contentTestId, so an editor body needs NO #579 raw-handle exception; read it with inner_text(), never text_content().
type: feedback
aliases: [codemirror, cm-content, contentTestId, editor body, code editor testid]
tags: [area/locators, area/eliteaui, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## Two facts, both confirmed by source + live run (ELITEA-2291, 2026-08-27)

### 1. A CodeMirror body is testid-able — the #579 exception does NOT apply

`src/[fsd]/shared/ui/field/CodeMirrorEditor.jsx` already accepts a
**`contentTestId`** prop and applies it **directly onto the `.cm-content`
DOM node** that CodeMirror renders, via
`EditorView.contentAttributes.of({'data-testid': contentTestId})`
(lines 83, 276-283, 331). Merged precedent: `contentTestId="toolkit-raw-json-editor-content"`
at `ToolCustom.jsx:218`.

So "CodeMirror's DOM is library-internal" is **not** a valid #579
stop-and-flag claim for the editor's content node. It is a one-line
call-site prop, exactly like `SingleSelect`'s `data-testid`.

⚠️ The `.agents/testing.md` § Locator policy #579 text names
"CodeMirror's per-line `<div>` nodes" as a sanctioned example
(`mcp_form_page.py:121`'s `fill_raw_json_line()`). That example is about
selecting **which line to edit** — a genuinely per-line concern with no
prop. It is NOT licence to reach for a raw handle to read the editor's
**content**, which `contentTestId` covers. Don't let the section's headline
stand in for the specific case it describes.

This is the same shape as [[579_claim_check_component_already_forwards_testid_prop]]:
read the rendering component's source before accepting any #579 claim.

### 2. Reading it: `inner_text()`, never `text_content()`

CodeMirror renders each line as its own `<div>`. `text_content()`
concatenates them with **no separator**, so the result will not parse as
JSON/XML and every structural assertion built on it fails for the wrong
reason. `inner_text()` preserves the newlines — verified live on the
Personal Tokens IDE-settings preview (13-line JSON, well under CodeMirror's
virtualization threshold, so the whole document is in the DOM).

For a long document, expect virtualization to truncate what is in the DOM —
assert on a bounded region or drive the editor's own API, don't assume the
full text is readable.

Related: [[579_claim_check_component_already_forwards_testid_prop]]
