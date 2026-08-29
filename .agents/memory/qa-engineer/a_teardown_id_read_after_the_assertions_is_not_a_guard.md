---
name: A teardown id captured after the assertions is not a guard
description: Reading a created object's id at the END of the try block leaves the whole assertion block as an un-cleaned window — the guard-ordering rule applies to the READ, not just to a flag
type: feedback
aliases: [teardown guard ordering, conversation leak, orphan conversation, id read-back window]
tags: [area/testing, type/gotcha]
created: 2026-08-30
updated: 2026-08-30
---

## The shape that looks correct and is not

`.agents/testing.md` § Teardown-guard ordering is usually read as "set the boolean flag
before the mutating click". The same rule binds any value teardown NEEDS — most often an
**id read out of the URL or a response**. A spec that mutates at step 6 and reads the id
at step 10 has a four-step window in which every failure leaks the object:

```python
try:
    chat.send_message(...)        # <- the conversation is CREATED here
    ...                           # steps 7, 8, 9 — any of these can raise
    match = URL_PATTERN.search(page.url)   # <- id captured only HERE
    if match: conversation_id = int(match.group(1))
finally:
    if conversation_id: delete(conversation_id)
```

Caught on ELITEA-2416 review (settings-w11, PR #1994): steps 7-8 are a 90 s Socket.IO
frame wait and a 10 s message-count wait, both on the documented flake-prone chat path —
so the leak window is exactly the part of the spec most likely to fail, and each leak
feeds the `#1082` shared-user conversation pollution the same spec's AFS says not to add to.

## Two fixes, both cheap

1. Capture the id **immediately after the mutation** (`page.wait_for_url(PATTERN)` right
   after send, then extract) — the direct application of the rule.
2. Or re-derive it in `finally` when it is still `None` (`page.url` is still readable there).

The reviewer question that finds this every time: **for each statement, if it raised right
here, what is left behind AND does teardown still know how to reach it?** The second half
is the one that gets dropped.

## The mirror-image good pattern from the same PR

ELITEA-2416's configuration teardown does this right: it deletes **by NAME** with the id
only as a fast path, and the names are computed before any mutation — so no ordering
window exists at all. A name-keyed teardown is strictly stronger than a flag, because the
key exists before the object does.

Related: [[creating_a_config_can_silently_become_the_default]]
