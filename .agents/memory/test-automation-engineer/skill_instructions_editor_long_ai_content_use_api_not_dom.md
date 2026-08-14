---
name: Skill instructions editor truncates long AI-generated content — verify via API
description: skill-instructions-editor-content's CodeMirror only renders viewport lines; a multi-paragraph AI-generated instructions block silently truncates under text_content()/inner_text() alike — verify persistence via SkillAPI.get_skill() instead
type: feedback
---

## The gotcha (ELITEA-2611 implementer session)

`SkillFormPage.get_instructions()` / `get_instructions_multiline()` both read
`skill-instructions-editor-content` (the CodeMirror `.cm-content` node) —
fine for short seeded instructions text, but for a long multi-paragraph
AI-generated block (e.g. the "Edit with AI" wizard's Instructions
suggestion, often 1-3 KB of Markdown) the DOM read silently truncates: only
a prefix of the content shows up, no error, `assert ... == expected` just
fails on a shorter string. Same root cause already documented for the MCP
Raw Json editor (`mcp_raw_json_codemirror_full_read_and_load_tools_quirks.md`)
— CodeMirror only keeps a viewport-sized window of `.cm-line` nodes in the
DOM — but a different, much simpler fix applies here.

## Fix: read via `SkillAPI.get_skill(skill_id)["version_details"]["instructions"]`

No need for the Raw Json editor's scroll-and-reconstruct technique. Once
Save has fired (or after a reload), the value is on the server — read it via
the API instead of fighting the editor's DOM. This is also a *stronger*
persistence proof than a DOM read (server ground truth, not "whatever the
client happened to render"), and matches the same "assert AI-generated
content at the data level, not via DOM" reasoning ELITEA-2611's AFS already
applies to the wizard's diff-differs checks (comparing the
`generate_skill_draft` response body directly instead of reading
`TextDiffHighlight.jsx`'s rendered spans, which carry no testid by design).

**When it still matters to distinguish:** short/seeded instructions text
(one line, no wrapping) reads fine via `get_instructions()`/
`get_instructions_multiline()` — this only bites on genuinely long
AI-generated content. Don't reflexively switch every instructions read to
the API; reserve it for cases asserting AI-generated multi-paragraph text.
