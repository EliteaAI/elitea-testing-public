---
name: CodeMirror editor content testid prop is generic
description: Field.CodeMirrorEditor already accepts contentTestId — no shared-component change needed for a new CodeMirror surface's content testid
type: project
---

`EliteaUI/src/[fsd]/shared/ui/field/CodeMirrorEditor.jsx` already accepts a
`contentTestId` prop and wires it onto CodeMirror's internal `.cm-content`
DOM node via `EditorView.contentAttributes.of({ 'data-testid': contentTestId })`
(CodeMirror renders its own internal DOM, so a plain JSX `data-testid` on the
wrapper component would only land on the outer wrapper, never the actual
editable text node).

This means **any new CodeMirror-backed editor surface only needs a call-site
change** — pass `contentTestId="<section>-editor-content"` to the existing
`Field.CodeMirrorEditor` — never a change to `CodeMirrorEditor.jsx` itself.
Confirmed live examples using this exact mechanism: `skill-instructions-editor-content`
(`SkillFormPage`/`CreateSkillForm.jsx`), `toolkit-raw-json-editor-content`
(`ToolCustom.jsx`), and `project-context-editor-content`
(`ProjectContextEditor.jsx`, ELITEA-2272).

Also: `maxLength` on the same component enforces a hard character cap via a
`transactionFilter` extension (`createMaxLengthExtension` in
`CodeMirrorEditor.jsx`) that clips inserts once the doc hits the limit — a
silent no-op transaction, not a thrown error, not a truncated-then-appended
value. If a case says "characters beyond N are rejected", this is the
mechanism; assert on content length staying flat + the counter text, not on
an exception or console error (there won't be one on a correct build).
