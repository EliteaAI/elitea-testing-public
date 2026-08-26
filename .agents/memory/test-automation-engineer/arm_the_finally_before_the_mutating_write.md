---
name: A fixture's try must open before the mutating write, not after it
description: Teardown never runs for a fixture that raises during SETUP — so any statement between the write and the try can strand shared state permanently
type: feedback
aliases: [fixture teardown, try finally, org-wide config, setup-phase failure, readback assert]
tags: [type/gotcha, area/fixtures]
created: 2026-08-27
updated: 2026-08-27
---

## The rule

In a `yield` fixture that mutates state outside the test process (an org-wide config, a
feature flag, a shared account), the `try:` opens **immediately before the mutating call** —
not before the `yield`. Everything that can raise while the state is dirty (the readback GET,
its assertion, logging) must sit inside the protected region.

Why it is not cosmetic: **pytest does not run the teardown half of a fixture that raised
during SETUP.** So a readback assert placed after the write — which is exactly where it feels
natural — guarantees the corruption it exists to detect. The sharper way to see it: that
assert exists *because it can fail*.

```python
original = api.get_config()          # read: safe, outside
try:                                 # ARM FIRST
    api.set_config(mutated)          # now dirty
    assert readback_is_correct()     # may raise — covered
    yield
finally:
    api.set_config(original)         # captured original, never a hardcoded {}
    assert (readback.get(k) or {}) == (original.get(k) or {})   # `or {}`: None == {} is a false alarm
```

Two companions:
- `restored.get(k) == original.get(k)` fails loudly on a **successful** restore when the key
  is absent (`None == {}`). Normalise both sides.
- Additive mutate + wholesale restore is **asymmetric on purpose** (a read-modify-write restore
  reopens the race it closes). Document which half wins under concurrency rather than
  "fixing" it — and keep the window short.

Caught by review on ELITEA-2211/PR #1832; proved by forcing the readback assert to fail and
confirming the config still came back. Reviewer's own note:
`.agents/memory/qa-engineer/fixture_try_finally_must_open_before_the_mutating_write.md`.
