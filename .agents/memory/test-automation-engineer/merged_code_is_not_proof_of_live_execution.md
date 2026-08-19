---
name: Merged code is not proof of live execution
description: A CI-only/guardrails-gated merged test can't stand in for live-execution proof either
type: feedback
---

## What happened (ELITEA-2210, fix round, 2026-08-19)

Reviewer flagged that an AFS's Coverage Map rows 4-5 (a `delete_file`-specific
chip observable) were dispositioned `asserted (reused)` on a source-code
tool-agnosticism argument alone — the covering spec only ever ran
`create_file`, never `delete_file`.

First instinct: cite a DIFFERENT already-merged test
(`test_hitl_sensitive_action_authorization.py::TestSensitiveActionAuthorize::
test_authorize_executes_toolkit_tool_directly`, ELITEA-2212) that DOES assert
`"{toolkit}: delete_file"` against a real backend deletion — merged to
`origin/automation/base` via a reviewed PR. Looked like a clean fix requiring
zero new code.

**Caught before shipping it:** that test's own AFS states "Network Behavior
... not captured live this pass" — the whole HITL cluster is
`pytest.mark.guardrails`, CI-only (Admin Guardrails route 404s on localhost),
and nobody has ever actually observed that assertion pass. It went through
review and merged as CODE, but "merged + reviewed" is not the same claim as
"executed and observed". Citing it would have satisfied the letter of the
finding (a different test asserts the right thing) while repeating the exact
defect the finding flagged, one hop removed.

## The rule

**"Asserted (reused)" must point at a citation that was ITSELF actually
executed and observed** — not just written, reviewed, and merged. Before
citing ANY existing test as coverage proof for a gap, check whether it is
gated out of the environment you can actually run it in (guardrails/CI-only
markers, `pytest.mark.skip`, an unreachable precondition). If it is, its
existence proves intent, not fact — go execute the observable yourself
(a new, additive test if the existing abstraction supports it) rather than
borrowing an unverified citation.

## Bonus finding

The new live test (delete_file, no sensitivity/guardrails needed) hit the
SAME known defect (#1127 — model narrates tool success without invoking the
tool) 3/3 consecutive runs, notably higher than `create_file`'s recorded 2/5.
Worth a quick sanity pass next time you write a new direct-toolkit-call test:
budget for the possibility that YOUR tool triggers this defect harder than
whatever tool the precedent test used, and that 3/3-deterministic can
legitimately convert a plain-RED test into sanctioned-RED (`.agents/testing.md`
§ Merge gate) rather than something to keep re-running for green.
