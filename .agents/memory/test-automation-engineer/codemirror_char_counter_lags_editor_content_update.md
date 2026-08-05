---
name: CodeMirror char counter lags editor content update
description: A sibling counter Typography (e.g. project-context-char-counter) re-renders one React tick after the CodeMirror .cm-content DOM updates from the same transaction — waiting only on the editor content misses it.
type: reference
---

## What happened

`ProjectContextPage.set_editor_content_via_paste()` (ELITEA-2272) originally used
blind `page.wait_for_timeout()` sleeps after clearing/pasting into the CodeMirror
editor. Fix round 1 replaced them with condition-based `expect(editor_content)
.to_have_text(...)` waits — and the test immediately went RED on the very next
assertion:

```
AssertionError: Expected char counter text '0 characters left. You have reached
the maximum character limit.', got '2500 characters left.'
```

`content_length == MAX_CHARS` (the assertion right after the editor-content wait)
passed — the CodeMirror DOM was already correct. But the character-counter
Typography (`project-context-char-counter`) is driven by a **separate, slightly
later** state update off the same paste transaction — it hadn't re-rendered yet
when the test read it. The old blind `wait_for_timeout(300)` had enough slack to
paper over this every time; the tighter condition-based wait exposed the real gap.

## Fix

Wait on the counter too, explicitly, after waiting on the editor content:

```python
counter_before_paste = self.get_char_counter_text()
... # clear + paste
expect(self.editor_content).to_have_text(text, timeout=10000)
expect(self.char_counter).not_to_have_text(counter_before_paste, timeout=5000)
```

Don't hardcode the expected counter string inside the page object (that's the
test's assertion to own) — "changed from its pre-action snapshot" is the correct,
non-duplicating condition when a real content change is guaranteed by the caller.

## Generalizes to

Any derived/computed UI element (counters, summaries, validation messages) that
sits in a *different* component from the input it derives from — never assume a
single condition-wait on the input element covers a companion display element's
own re-render. When in doubt, wait on each surfaced observable your test reads,
not just the one you interacted with directly.
