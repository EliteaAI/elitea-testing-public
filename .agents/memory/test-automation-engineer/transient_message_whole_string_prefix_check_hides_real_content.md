---
name: Transient-message whole-string prefix check hides real content
description: A "Thought for X seconds" reasoning header + real content in the SAME message body made wait_for_ai_response() time out forever — fixed to check per-line.
type: feedback
---

## What happened (ELITEA-2208/2470 implementation, 2026-08-19)

Sent a message to a dynamically-selected ambient pipeline with no
configured nodes. The product responded correctly and quickly (visible in
the screenshot within ~1s): a collapsed "Thought for less than a second"
reasoning summary, immediately followed by a real error card ("Pipeline
has no nodes to execute. Please add at least one node to the pipeline
before running it.") — both inside the SAME message `<li>`.

`wait_for_ai_response()` timed out at 60s anyway. Root cause:
`_extract_message_body()` joins ALL `<p>`/`<li>` block text with `\n`, so
the extracted string was `"Thought for less than a second\nPipeline has
no nodes to execute..."`. `_is_transient_message()`'s dynamic-pattern
check was `normalized.startswith("thought for ")` — evaluated on the
WHOLE joined string, which of course still starts with that phrase even
though real content follows on the next line. The response never stopped
looking "transient" to the poll loop.

## The fix

Check per-line instead of on the whole joined string — transient only
while EVERY line present so far is itself a thought/packing-status
indicator; ANY other line means real content has landed:

```python
lines = [line for line in normalized.split("\n") if line.strip()]
if not lines:
    return False
return all(
    line.startswith("thought for ") or ("packing" in line and "tool" in line)
    for line in lines
)
```

## Why the agent family's own test never hit this

The merged `test_add_agent_via_hash_search_joins_participants_and_responds`
sends "hello" to a real agent, which (in that session) answered directly
with no visible "Thought for..." reasoning header — single-line body,
`startswith` behaved identically to the per-line check. The bug is latent
for any response shape with ONE line; it only surfaces when a
thought/reasoning summary and the final answer render as separate block
elements in the same message — which pipelines (and any reasoning-capable
agent) can do.

## Generalizes to

Any `_is_transient_message`-style heuristic reused elsewhere (e.g.
`wait_for_message_content_stable`) inherits the same fix automatically —
it's the shared helper. If a FUTURE transient-status pattern is added to
that method, apply it per-line too, not as a whole-string
`startswith`/`in` check, or the same "real content landed but still reads
as transient" trap reproduces.
