---
name: CodeMirror large-content fill via clipboard paste
description: For 500+ char CodeMirror fills, clipboard-write + Ctrl/Cmd+V beats keyboard.type() — same transactionFilter path, much faster
type: feedback
---

## Situation

`SkillFormPage.fill_instructions()` (`automation/pages/skill_form_page.py:222`)
establishes `select_text()` + Backspace + `page.keyboard.type(text)` as the
pattern for filling a CodeMirror editor (CodeMirror ignores `.fill()`). That's
fine for short/medium content, but for a large fill (confirmed at 2500 chars,
ELITEA-2272 Project Context character-limit case) `keyboard.type()` means
2500+ individual synthetic keystrokes — slow, and each one re-runs CodeMirror's
`EditorState.transactionFilter` (maxLength enforcement, syntax highlighting,
etc.) per character.

## What works

```python
page.evaluate(
    "text => navigator.clipboard.writeText(text)", text
)
editor_content.click()  # or select_text() + Backspace to clear first
page.keyboard.press("ControlOrMeta+v")
```

Confirmed live (2026-08-05, ELITEA-2272): a 2500-char paste goes through the
SAME `EditorState.transactionFilter.of(...)` maxLength-clamping logic
(`CodeMirrorEditor.jsx:13-63`) as native typing — truncation, character
counter, and `isDirty`/Save-enabled state all update identically. It is a
real user-input path (paste), not a synthesized `page.evaluate` value-set, so
it doesn't trip the "never synthesize the action" rule.

**Prerequisite already satisfied project-wide:** `conftest.py`'s `context`
fixture grants `clipboard-read`/`clipboard-write` globally
(`permissions=["clipboard-read", "clipboard-write"]`), so no extra
per-test permission setup is needed.

## When to use which

- Short/medium input (a few dozen chars, or a case that cares about
  keystroke-level behavior like autocomplete-as-you-type) → keep
  `keyboard.type()`.
- Large fill (hundreds+ chars) where only the END STATE matters → prefer
  clipboard-paste for speed.
