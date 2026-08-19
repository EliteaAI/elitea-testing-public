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

**Second confirmed occurrence, same batch (2026-08-19):** ELITEA-2474 ("Chat –
Complete flow from direct toolkit call in thinking steps to output chip
display") is an EXACT duplicate of ELITEA-2215 ("Chat – Tool Action and Output
– Complete Flow from Direct Toolkit Call to Output Display") — same trigger
message, same tool, same chip/response assertions, even a verbatim-matching
chip-description phrase. Classified `already-covered` against the merged
`test_direct_toolkit_call_complete_flow.py` with no new execution. **Contrast
with a near-neighbour that is NOT a duplicate:** the same batch also hit
ELITEA-2209 (genuine small gap — an explicit "no AGENTS section" assertion the
covering test's Setup never checked → `extend-existing`) and ELITEA-2210
(same mechanism but a DIFFERENT tool, `delete_file` vs `create_file` → still
`extend-existing`, needed its own live-executed test per "coverage judgments
stand on your own execution" — a data variant is not the same as a duplicate).
The test that separates the three: does the candidate case differ from the
covering spec in trigger DATA or an asserted STEP at all? Zero difference (not
even data) → `already-covered`. A named data variant needing its own proof, or
an explicit case-text assertion the covering spec's code never runs → at least
`extend-existing`, even with a small gap.
