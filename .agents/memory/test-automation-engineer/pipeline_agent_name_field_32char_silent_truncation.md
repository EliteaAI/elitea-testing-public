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

**Variant — appending to an already-at-cap fixture name (ELITEA-2048,
2026-08-09):** `pipeline_id`'s own `[:32]` name generation means the field is
frequently already AT the 32-char cap before your test even edits it. A
"modify the name" test step that does `f"{original_name} modified"` (the
common AFS phrasing) silently drops the whole suffix, and the field reads
back **unchanged** — indistinguishable from "the edit never happened" rather
than a length error. Don't append to a fixture-generated name; use a fixed
short literal instead (`"autotest_name_modified"`), same as
`test_discard_reverts_name_change`'s pre-existing pattern.

**Same trap with a MANUALLY-chosen (not fixture-generated) base name
(ELITEA-2614, 2026-08-12):** `f"immutable-test-agent-2614-{uuid.hex[:6]}"`
landed at exactly 32 chars by coincidence of the prefix+suffix lengths — no
`[:32]` slicing involved, so nothing about the base name LOOKED
truncation-prone. Appending `-EDITED` for a "attempt to edit the Name" case
step typed 0 extra characters (already at cap), so the field's value never
actually changed — and the symptom here was `Save` staying **disabled**
(`is_save_enabled()` → False) rather than a wrong post-save value, an even
more misleading signal since it looks like "the click/type interaction
itself failed" rather than a length problem. Any test that constructs its
own base name AND plans to edit/append to it later in the same test must
budget headroom for the longest planned suffix up front — don't just check
the base name's own length in isolation.

**Variant — `pipeline_api.create_pipeline()` HARD-REJECTS >32 chars, does NOT
silently truncate (ELITEA-2062, 2026-08-09):** unlike the UI's `agent-name-input`
(above, silent truncation), the server-side `POST
/elitea_core/applications/prompt_lib/{project}` payload validator 400s with
`[{'type': 'string_too_long', 'loc': ['name'], 'msg': 'String should have at
most 32 characters'}]` when `name` exceeds 32 chars. A descriptive prefix like
`f"autotest_multitab_pipe_1_{ts}"` (26-char prefix + 10-digit unix timestamp =
36 chars) 400s immediately at `pipeline_api.create_pipeline()` — before any
browser interaction, so this is the FIRST thing to check when a pipeline-API
test setup step 400s with a `string_too_long` body. Budget the full generated
name (prefix + suffix) at ≤32 chars up front, same as the UI-field discipline
above but for the API path — e.g. `f"autotest_mtab1_{ts}"` (15-char prefix +
10-digit ts = 25 chars).
