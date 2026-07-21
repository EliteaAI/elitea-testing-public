---
name: Empty test data can defeat content-based assertions
description: When two test fixtures are both created empty/minimal for speed, an assertion checking "content differs between state A and state B" can become vacuous — it passes whether the transition happened correctly or not at all. Reviewer catch, PR #696/ELITEA-2114 round-2.
type: feedback
---

## The pattern

Creating test data via a fast API call with no message/content payload (rather
than a slow real UI action) is good practice — matches Rule 10 (read-only/
minimal-seed-by-default) and avoids unnecessary LLM round-trips. But it has a
side effect reviewers must check for: if a test step's assertion is meant to
prove "the UI now shows entity B's content, not entity A's", and both A and B
were created empty, the assertion degenerates to "the UI shows *something*
empty" — which is true in the correct case AND in the broken case (stale
view of now-deleted A, which was also empty).

## Concrete instance

PR #696 (ELITEA-2114, chat conversation deletion). `conv_target` and
`conv_sibling` both created via `conversation_api.create_conversation(name)`
— zero messages by design (`automation/api/client.py:266-276`, no message
payload). Case step 12 ("main chat panel does not show the deleted
conversation") was implemented as:

```python
assert chat.get_message_count() == 0, (
    "Main chat panel should show an empty message list for the newly-active "
    "(also empty) conversation, not any lingering conv_target content"
)
```

This passes identically whether the panel correctly switched to
`conv_sibling` or is stuck showing a stale/unrefreshed `conv_target` view
(also 0 messages). The regression this step exists to catch would slip
through undetected.

## The fix pattern

Don't reach for a content-based check when both fixtures are contentless.
Reuse an identity-based signal instead — in this case, the codebase already
had the exact idiom needed: `page.expect_response()` capturing a specific
network call (see `confirm_delete_conversation()`,
`automation/pages/chat_page.py:1968-1984`, used one step earlier in the same
test to prove the DELETE actually fired). The AFS's own § Network Behavior
had already documented the panel's `GET .../conversation/.../{next_id}?...`
fetch — asserting THAT resolves for `next_id` specifically is a real
discriminator, at zero cost of a new testid.

## Reviewer checklist addition

When a step's stated purpose is "prove content A is gone / content B is
shown" and the two fixtures were deliberately created empty/minimal: ask
whether the assertion can actually fail in the broken case. If both branches
of the failure mode produce the same observable, the assertion is vacuous —
flag it as an Important finding even though a real `expect()`/`assert` is
technically present at that step (the "per-step assertion" gate is satisfied
literally, but "assertion strength" is not).
