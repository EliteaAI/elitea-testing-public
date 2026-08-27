---
name: Removing a false-RED guard can create a silent false-GREEN
description: Before deleting an over-strict assertion, check what still fails when the real defect occurs — often nothing, so the guard needs replacing, not removing
type: feedback
aliases: [false positive assertion, assertion too strict, loosen assertion, over-strict guard, false green, oracle replacement]
tags: [area/test-repair, type/gate]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

A `[Fix]` card that reads *"this assertion is too strict / false-positive — loosen it"*
frames the work as **deletion**. That framing is a trap. The guard is failing wrongly,
but it may be the **only** thing that fails rightly when the real defect occurs.

Ask, before touching it: **if the genuine failure this guard was meant to catch happened
right now, which assertion in this test would go red?** If the answer is "none", the guard
must be *replaced*, not removed — and the replacement is the actual work order.

## Worked case — ELITEA-1140 / #1817 (2026-08-27)

`test_chat_with_toolkit` asserted `"error" not in last_msg.lower()`. The toolkit's payload
was this repo's own branch list, which contains `error`-bearing branch names, so it
false-RED'd on success. Obvious fix: delete it.

Wrong. On a genuine 401 the model still narrates *"…trying to list the **branches**…"*, so
`chat_response_keywords == ["branch","found","repository"]` **passed**, and so did the
message-count assert. Deletion would have converted a visible false-RED into a **silent
false-GREEN**, and the case would have back-written `execution_type: automated` for a
scenario nobody verified.

The same trap fired a second time inside the same card: the `confluence` param had no
captured success pattern, so the new oracle's empty-pattern fallback logged a warning and
asserted nothing — green on a broken toolkit. A reviewer caught it by walking **every**
row of the config table, not just the two the card was about.

## What to do instead

- Make the analyst answer *"what still fails?"* explicitly, before any implementation.
- When an oracle is table-driven, walk **every row**, not the one in the card — a config
  row with no oracle is a disarmed gate.
- Implement "we cannot classify this" as a **`pytest.skip` naming the gap**, never as a
  `logger.warning` + assert-nothing. A warning in a CI log is not a gate. That is not
  masking: it hides no product defect and no red, and `skipped` is the honest outcome
  name for "success and failure are indistinguishable here".
- Add a **static** test that fails if a new table row arrives with neither an oracle nor
  an explicit skip — so the guarantee is inherited at authoring time.

Related: [[capture_the_payload_never_infer_it]]
