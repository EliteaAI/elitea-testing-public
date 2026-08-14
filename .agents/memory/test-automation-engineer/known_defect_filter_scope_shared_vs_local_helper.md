---
name: Known-defect filter scope — shared vs local helper
description: When applying a known-defect console filter (e.g. #554), never edit a shared base_page.py helper with out-of-batch callers — filter the returned list at the assertion site instead.
type: feedback
---

## The situation

A console-error assertion needs a narrowly-scoped known-defect filter (e.g.
elitea-testing-public#554 — the RTK-Query `toolkitTypes` empty-projectId 404
race). Most tests build their own `console_messages = []` +
`page.on("console", lambda msg: ...)` inline, so adding
`and not _is_known_554_toolkits_404(msg)` to the lambda is a pure, local,
additive edit.

But some tests instead call a **shared page-object helper** —
`AgentDetailPage`/`BasePage.capture_console_errors()` — which attaches the
listener internally and returns a `CapturedConsoleMessages` (a `list`
subclass). That helper had 30+ callers across the whole suite (grep
`capture_console_errors` before assuming it's local), most of them merged
long before and outside the current batch.

## The rule

**Never edit the shared helper to add a batch-specific filter.** Editing it
changes behavior for every one of those 30+ callers — exactly the
additive-only-on-shared-caller-files violation the project's Hard Rule 3
exists to prevent, even though the *filter itself* only narrows what's
already an `error`-type message.

Instead, filter the **returned list** at the assertion site, in the one test
file that needs it:

```python
console_errors = detail_page.capture_console_errors()
...
unexpected = [m for m in console_errors if not _is_known_554_toolkits_404(m)]
assert not unexpected, f"Unexpected console errors: {[m.text for m in unexpected]}"
```

This works because `CapturedConsoleMessages` is a plain `list` subclass —
no special construction needed to filter it after the fact. The helper
itself, and every other caller, stays byte-identical.

## Where this applied

`test_agent_embedded_chat_conversation_starter_chips.py` (batch
agents-batch1-1277, fix-only dispatch for issue #1277) — every *other*
sibling file in the same batch used an inline `page.on("console", ...)`
lambda and got the filter added directly to the lambda; this one file used
`capture_console_errors()` and got the call-site-filter treatment instead.
