---
name: Native maxlength probe without context blowup
description: Verify a native HTML maxlength truncation live via execCommand('insertText') inside browser_evaluate, never a literal huge string in browser_type
type: feedback
---

## Situation

Testing whether a plain `<input>`/`<textarea maxlength="N">` (MUI
`slotProps.htmlInput.maxLength`, e.g. `GenerateSkillReviewForm.jsx`'s
Description/Instructions fields, `MAX_DESCRIPTION_LENGTH`/
`MAX_INSTRUCTIONS_LENGTH`) actually truncates over-limit input at N chars —
the same class of finding ELITEA-1993 established for the Name field
(`maxlength=64`) and ELITEA-1994/1995 confirmed for Description (2304) and
Instructions (5000, not the case-stated 2500).

Passing a 2000+ char literal string as `browser_type`'s `text` param (or
`Read`-ing a file containing one) echoes the ENTIRE string back into the
tool response/generated-code block — one accidental 2400-char paste blew
through the per-turn output token limit and forced a resume.

## What works

Inside `browser_evaluate` (function body constructs the string via
`.repeat()`, so the literal never appears in the call payload), target the
element ref, then:

```js
(el) => {
  el.focus();
  el.select();
  const s = 'y'.repeat(2400);           // built in-page, not passed in
  const ok = document.execCommand('insertText', false, s);
  return { execOk: ok, resultLen: el.value.length };  // small, safe to return
}
```

`execCommand('insertText', ...)` on a focused editable element fires the
SAME native `input` event pipeline as a real paste/keystroke — confirmed
live to reproduce the identical `maxlength` truncation that `.fill()` and
`press_sequentially()` already do (per the Name-field precedent), and it
counts as a real user-input-equivalent action, not a synthesized value-set
(`el.value = ...` bypasses `maxlength` entirely and would NOT prove
anything). Only the small `resultLen`/state summary crosses back into the
transcript — never the 2000+ char string itself.

## When to use which

- Need to prove a plain HTML `maxlength` attribute truncates — use this
  (`execCommand('insertText', ...)` inside `browser_evaluate`).
- Need to fill a CodeMirror/ProseMirror/Monaco editor with a large value —
  use the sibling entry `codemirror_large_fill_clipboard_paste.md`
  (clipboard-write + Ctrl/Cmd+V) instead; `execCommand('insertText')` does
  not reliably drive those editors' own transaction pipelines.
- Either way: never pass a 500+ char literal through `browser_type`'s
  `text` param or `Read` a file containing one — both echo the full string
  back into context for no benefit once only the resulting length/state
  matters.
