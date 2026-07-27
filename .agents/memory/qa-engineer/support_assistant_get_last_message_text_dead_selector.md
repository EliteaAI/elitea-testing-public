---
name: Support Assistant get_last_message_text() dead selector
description: SupportAssistantPage.get_last_message_text() queries .elitea-assistant-widget p, which matches zero live elements (correct container class is .elitea-assistant-window); method always returns ""; makes ELITEA-1799's GH#607 text-comparison soft-assert permanently inert (both sides always "")
type: feedback
---

Discovered live during ELITEA-1800 analyst pass (2026-07-18), while
independently verifying restored-session content integrity via
`browser_evaluate`.

**The bug:** `SupportAssistantPage.get_last_message_text()`
(`automation/pages/support_assistant_page.py` L305-317) does:

```python
paragraphs = self.page.locator('.elitea-assistant-widget p')
```

`.elitea-assistant-widget` matches **zero** elements in the live DOM.
Verified directly:

```js
document.querySelectorAll('.elitea-assistant-widget p').length   // 0
document.querySelector('.elitea-assistant-window').querySelectorAll('p').length  // 25, correct content
```

The real container class is `.elitea-assistant-window` (same class
`is_fullview_mode()` already correctly uses for its `--expanded` modifier
check, a few methods away in the same file). `get_last_message_text()` was
never updated when the class was chosen elsewhere, or was written against a
different DOM version.

**Blast radius:** `get_last_message_text()` always returns `""`.
`test_history_restore_and_continue` (ELITEA-1800's covering test) never
calls this method — unaffected. `test_new_chat_creates_fresh_session`
(ELITEA-1799's covering test) DOES call it twice, inside the GH#607
regression-net `soft_failures` check:

```python
response_before_new_chat = support_page.get_last_message_text()   # always ""
...
restored_last_message = support_page.get_last_message_text()      # always ""
if restored_last_message != response_before_new_chat:             # "" != "" -> always False
    soft_failures.append(...)
```

The text-comparison half of that check can never fire — it's dead code that
always passes. The count-based half of the same check
(`restored_message_count < total_count_before`) is unaffected and still
carries real signal (verified working via live wrapper-count checks this
same pass), so ELITEA-1799's current pass/fail outcome doesn't change — but
its defect-detection power for GH#607 is weaker than the test believes it
is: a truncation scenario that dropped/reordered messages but happened to
keep the same *count* would slip through undetected.

**Fix (not applied — out of scope for the ELITEA-1800 analyst pass, flagged
to orchestrator/lead instead):** change L312 to
`self.page.locator('.elitea-assistant-window').locator('p')` (or scope
similarly to how `is_fullview_mode()` reaches `.elitea-assistant-window`).

**How to independently verify a getter like this before trusting it in an
assertion:** don't just read the method's Python source and assume the
selector is right — run it live via `browser_evaluate` / `page.evaluate`
against the actual DOM and compare count/content to a manual read of the
snapshot. This is the same "verify live, don't trust prior-pass code"
discipline already established for the Support Assistant module (see
`support_assistant_launcher_click_quirk.md`), applied one level deeper —
past passes trusted this getter's *name* implied correctness without
checking its *selector* against the live DOM.
