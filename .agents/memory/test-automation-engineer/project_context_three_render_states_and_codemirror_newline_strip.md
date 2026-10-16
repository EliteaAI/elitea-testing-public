---
name: Project Context page has three render states, not two
description: wait_for_page_load() style helpers that only check empty-vs-editor hang on a populated saved view; CodeMirror .text_content() also drops newlines a textarea .input_value() keeps.
type: feedback
---

Settings -> Project Context (`automation/pages/project_context_page.py`,
ELITEA-3252/3253/3254/3255 family, 2026-10-16) renders THREE distinct states,
not two:

1. Empty state — `project-context-create-button` testid.
2. Create/edit editor (route `/settings/project-context/edit`, NOT
   `?view=create` as an older AFS/digest claimed — re-verify route-by-click
   live rather than trusting a stale digest) — `project-context-editor-content`
   testid.
3. Populated saved view — renders NEITHER of the above two testids. Only
   `ai-edit-project-context-open-button` (and `project-context-actions-menu-button`)
   identify it.

`ProjectContextPage.wait_for_page_load()` originally only tried states 1 and
2 (`try: create_button.wait_for(...) except: editor_content.wait_for(...)`)
and would hang the full timeout on state 3 — e.g. navigating to Settings
right after a chat tool call just saved content. Fixed to a 3-way try chain.
If you build a similar "wait for whichever state renders" helper on ANY page
with more than two possible server states, enumerate all of them live first
— don't assume a two-branch try/except covers it just because the first two
states you tested did.

Separately: CodeMirror renders each line as its own DOM node, so
`.text_content()` on the editor strips the `\n` between them, while a plain
`<textarea>`'s `.input_value()` (e.g. the Build-with-AI/Edit-with-AI review
step) keeps them. Comparing the two raw gives a length/equality mismatch
that is NOT a real content difference — normalize both sides with
`.replace("\n", "")` before asserting equality or length-matching across a
CodeMirror editor and a plain textarea holding "the same" content.
