---
name: Pipeline/Agent name field 32-char silent truncation
description: MAX_NAME_LENGTH=32 on agent-name-input; typing beyond it silently truncates, no error
type: feedback
---

`ApplicationEditForm.jsx` caps the Name field (`agent-name-input`, shared by
Agents AND Pipelines) at `MAX_NAME_LENGTH = 32` (`src/common/constants.js`).
Typing/`press_sequentially()`/`type()`-ing a longer string does **not** error
or block — it silently truncates to the first 32 chars, and `input_value()`
returns the truncated string.

**Confirmed live (ELITEA-2020):** a manually generated name
`f"autotest_create_pipeline_minimal_{uuid.uuid4().hex[:8]}"` (41 chars)
truncated to exactly `autotest_create_pipeline_minimal` (32 chars) — the
`_a1b3da2e` suffix vanished entirely, so a naive
`assert get_name() == pipeline_name` failed with a confusing diff.

**Same root cause as the `pipeline_id` fixture's own `[:32]` truncation**
already noted in the ELITEA-2023 AFS (`f"autotest_{request.node.name}"[:32]`)
— but this one bites ANY manually-typed name in a test body, not just that
one fixture.

**Fix:** keep generated Name-field values ≤32 chars total. A short fixed
prefix + an 8-hex uuid suffix works: `f"autotest_pipe_min_{uuid.uuid4().hex[:8]}"`
= 27 chars. Don't assume a descriptive multi-word prefix is safe — count it.

This also applies to Agents (`test_agent_name_character_limit.py` already
covers the truncation behavior itself as a case, ELITEA-1900) — any NEW test
that generates its own name for either entity should budget for this cap
before picking a prefix.
