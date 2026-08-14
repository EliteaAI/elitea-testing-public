---
name: Truncate-after-concat defeats agent/skill name uniqueness suffix
description: f-string name + timestamp sliced [:32] AFTER concat can erase the whole suffix — verify entropy survives the cap
type: feedback
---

Found reviewing ELITEA-2610 (PR #1476, `test_skill_agent_version_selection_behavior.py`):

```python
TS = int(time.time())
SKILL_NAME = f"elitea-2610-response-style-{TS}"[:32]
AGENT_NAME = f"elitea-2610-version-behavior-agent-{TS}"[:32]
```

`[:32]` slices the **finished string**, not the base name — so if the base
prefix alone is already close to/over 32 chars, the timestamp suffix gets
chopped off from the right, silently. Computed on a real epoch (`1786559349`,
10 digits):

- `SKILL_NAME[:32]` → `elitea-2610-response-style-17865` — keeps only the
  **leading 5 digits** of the epoch. Since the leading digits of Unix time
  change slowest, this buys ~28 hours of uniqueness resolution, not real
  per-run uniqueness.
- `AGENT_NAME[:32]` → `elitea-2610-version-behavior-age` — the entire
  timestamp is gone. **Every run of this test creates an agent with the
  IDENTICAL name, forever.** If a prior run's `finally`-block cleanup ever
  fails (already observed in this same PR's own implementation history —
  2 manual reruns during dev), the next run collides with a residual entity
  instead of getting a clean one, producing a flaky failure disconnected
  from the actual test logic.

**The established, correct pattern already exists 3x in the same directory**
(`test_published_agent_version_cannot_be_modified.py`,
`test_agent_with_skills_publishing_flow.py`,
`test_agent_skills_validation_attribution_and_token_invalidation.py`):
keep the base name SHORT ENOUGH to leave room for a real suffix, don't rely on
truncation to make room.

```python
_SUFFIX = uuid.uuid4().hex[:6]          # 6 hex chars, real entropy
AGENT_NAME = f"immut-agt-2614-{_SUFFIX}"  # 15-char base + 6 = 21, well under 32
```

**Reviewer check going forward:** any name built as `f"<base>-{something}"[:N]`
— compute `len(base)` mentally (or actually run it) and confirm the variable
part survives the cap. A truncation that only bites AFTER the suffix is
appended is invisible by reading the code casually; it only shows up by doing
the arithmetic.
