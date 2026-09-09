---
name: An assertion on LLM-chosen content is a premise the case never had — but deleting it can still mask
description: Replace content premises with parsed equality against the producer's own captured output; file the fault and keep a hard fail
type: feedback
aliases: [LLM content assertion, non-empty assertion, nondeterministic producer oracle, structured output flake]
tags: [area/assertion-design, type/fidelity]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

`assert value != '""'` / `assert len(parsed) > 0` on a value an LLM chose looks like a
strength check. It is a **premise about the producer's content**, and the TMS case
usually never had it. But deleting it outright is masking when the empty value is
produced by a REAL, silent product fault — `""`/`[]`/`{}` trivially satisfy whatever
shape assertion survives, so an entirely unpopulated run then scores green.

## The shape that does both jobs

1. **Oracle, not content.** Capture what the system actually produced (response body,
   Socket.IO frame, API readback) and assert the UI against it:
   `json.loads(ui_value) == backend_state[key]`. Deterministic, and every value still
   comes from the product (`.agents/testing.md` § Fidelity policy).
2. **Keep the type/shape assertion** — that is usually the case's real observable.
3. **Guard the precondition explicitly**, and make its exhaustion a LOUD failure naming
   the filed defect. A bounded re-ask absorbs producer non-compliance; a systemic
   regression still turns the spec red.
4. **File the fault.** The retry removes the coin flip from CI, not the fault from the
   tracker.

## Compare parsed values, never raw JSON text

`JSON.stringify` emits no separator spaces (`["a","b"]`); Python's default `json.dumps`
does (`["a", "b"]`). Compare `json.loads(ui_text) == value`, or dump with
`separators=(",", ":")`.

Worked case: [[ELITEA-2453]] repair (#2120) — `test-specs/pipelines/l3_run-details-multiple-state-variables-different-types_ELITEA-2453.md` § REPAIR AMENDMENT, defect `#2153`.
