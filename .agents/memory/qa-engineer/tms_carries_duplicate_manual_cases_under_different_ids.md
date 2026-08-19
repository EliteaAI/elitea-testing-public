---
name: TMS carries duplicate manual cases under different IDs
description: Same feature, different TMS ID, near-verbatim steps — check merged specs before treating as new
type: reference
---

Confirmed 2026-08-19: ELITEA-2471/2472/2473 ("Chat – HITL Authorize/Block/Block
with Comment button …") turned out to be near-verbatim restatements of
ELITEA-2212/2213/2214 (the same HITL sensitive-action-authorization flow,
analysed and automated 2026-08-03, cluster commit `ddaf8b31b`). Different TMS
case IDs and slightly different title wording, but identical trigger
precondition, identical buttons, identical expected results. Classified
`already-covered` against the merged
`automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py`
without re-execution — see
`test-specs/chat-interface/lcovered_hitl-*-duplicate-manual-case_ELITEA-247{1,2,3}.md`.

**Why this happens:** the onetest TMS's case-authoring process appears to
occasionally generate a second manual case for a feature that was already
covered in an earlier authoring pass (possibly a re-run of an
LLM-assisted-case-generation step, or the same acceptance criterion carded
twice under different section headers). It is not limited to chat-interface —
treat it as a standing possibility on any surface.

**What this changes:** Phase 2b's "read the neighbours by BEHAVIOUR, not by
case ID" instruction is exactly the defense — grep `test-specs/` and
`automation/tests/` by the observable/UI label (e.g. "Sensitive Action
Authorization", "Block with Comment") before assuming a case's TMS ID means
it's unseen work. When the title AND the step table both match an existing
merged spec almost word-for-word (not just "similar area" — literally the
same buttons, same expected results, sometimes the same example strings),
that is strong enough for `already-covered` even without live re-execution,
provided the covering test is read in full and cited at file:line (see the
worked traceability AFS files above for the citation shape).

**When live re-execution isn't even possible for the duplicate:** if the
original case's precondition requires a deployed env (e.g. this cluster's
`pytest.mark.guardrails` — Admin Guardrails route 404s on localhost), the
duplicate inherits that same constraint regardless of its own TMS ID — don't
try to force a localhost repro just because it's a "different" case.
