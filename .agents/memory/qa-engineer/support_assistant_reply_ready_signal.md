---
name: Support Assistant reply-ready signal is the copy button
description: Assistant message item mounts instantly with a "Starting up…" placeholder — count-based waits return before the answer exists
type: feedback
aliases: [assistant wait for reply, Starting up placeholder, support-assistant-message-copy-button]
tags: [area/support-assistant, type/wait]
created: 2026-08-22
updated: 2026-08-22
---

## The trap

`expect(assistant_items).to_have_count(base+1)` looks right and is wrong: the assistant message item
mounts **immediately** with `data-role="assistant"` and the text `Starting up…`, so the wait
satisfies in ~2 s and the test reads a placeholder as the answer. Cost one wasted probe run
(2026-08-22) whose "replies" were all timestamps and `Starting up...`.

## The fix

`support-assistant-message-copy-button` renders only on a **completed** assistant response:

```python
copies = page.locator('[data-testid="support-assistant-message-copy-button"]')
base = copies.count()
# … send …
expect(copies).to_have_count(base + 1, timeout=240_000)
```

Latencies measured 2026-08-22: 40.7 / 41.2 / 76.5 / 77.0 / 77.0 s (project questions are the slow
end). 120 s is too tight; use 240 s.

Related: [[support_assistant_context_payload]]
