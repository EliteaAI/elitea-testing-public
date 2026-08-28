---
name: A negative to_have_text wait built from inner_text() lines needs use_inner_text=True
description: Playwright text matchers read textContent (no separator between child nodes) by default, so a space-joined expectation can never match and not_to_have_text passes instantly
type: feedback
aliases: [not_to_have_text no-op, use_inner_text, tooltip settle wait, silent wait, textContent vs innerText]
tags: [area/playwright, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

A "wait until this element's text changes" helper written as

```python
previous = [l for l in locator.inner_text().split("\n") if l.strip()]
...
expect(locator).not_to_have_text(" ".join(previous), timeout=T)   # NO-OP
```

**never waits.** Playwright's text matchers read the element the `textContent`
way by default: child nodes are concatenated with **no separator**
(`"Aug 12LLM Calls: 3"`), while the expectation was built from `inner_text()`
(newline-separated) and re-joined with spaces (`"Aug 12 LLM Calls: 3"`). The two
strings can never be equal, so the **negative** assertion is satisfied on its
first poll and the caller reads the stale render.

Fix: `expect(locator).not_to_have_text(" ".join(previous), use_inner_text=True, timeout=T)`
— then both sides come from `innerText`, and Playwright's own whitespace
normalisation collapses the newlines to the same single spaces.

## Why it needs a guard, not just care

Nothing goes red when a wait stops waiting — it degrades into a race, so it
shows up later as an intermittent "assertion saw the previous value". Caught
only by a fresh-session reviewer on PR #1956 (ELITEA-2326/2327/2328/2329).
Pinned by `automation/tests/unit/test_chart_tooltip_change_wait_compares_inner_text.py`,
which drives the real helper against a fake locator exposing both text views —
it fails on the pre-fix code.

**Generalisation:** any assertion that compares a MULTI-LINE element against a
string you assembled yourself must decide, explicitly, which text view it means.
The positive direction (`to_have_text`) fails loudly when you get it wrong; the
negative direction passes silently. Treat every `not_to_*` text assertion as
guilty until its comparison basis is checked.

Related: [[tms_case_links_live_under_settings_analytics]]
