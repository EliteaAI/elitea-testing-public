---
name: Reviewer narration is not pasted evidence
description: A reviewer APPROVED comment that narrates grep results in prose (line numbers, hit counts, specific file names) still fails the "claims require pasted output" rule if it never includes the actual verbatim command + output — specificity of prose is not a substitute for a fenced code block
type: feedback
---

## What happened

Control audit tick on issue #26 (ELITEA-1735 testid-only rework, PR #203,
merged `e516aca`). The fresh reviewer's APPROVED comment read, in relevant
part:

> "Independently re-ran the mechanical grep gate (both lexical + structural
> clauses, including `get_by_test_id`) — zero non-compliant handles; the
> only two real-code hits (`mui.py:97`, `agent_detail_page.py:371`) both
> resolve to literal `[data-testid=` selectors or an UPPER_CASE constant
> one hop away."

This reads as credible, specific evidence — it names exact files, exact
line numbers, and the exact resolution reasoning. It is still a **FAIL**
against `.agents/role-overrides.md` § Reviewer slot: *"Claims require
pasted output. The verdict comment includes the mechanical grep's actual
output verbatim... 'Grep gate clean' without the paste is not a finding,
it is the #19 FAIL-2 anti-pattern; no paste ⇒ no APPROVED."* There is no
fenced code block anywhere in the comment showing the actual
`git diff ... | grep -nE '...'` invocation and its output (empty or
otherwise) — only a narrative description of what that grep supposedly
showed.

I independently re-ran the grep myself as part of the same audit (checklist
item 1) and confirmed the underlying claim was TRUE — the gate genuinely is
clean. That's exactly what makes this a subtle case: the reviewer wasn't
lying or sloppy about the actual state of the code, only about the shape of
the evidence they were required to leave behind.

## Why it matters

The paste requirement isn't there to catch reviewers who are wrong about the
code — it's there so a later reader (the auditor, the human, a future
session) can verify the claim WITHOUT re-running the check themselves. A
narrated result — however specific and however accurate — puts the reader
back in "trust the reviewer's word" territory, which is precisely the
failure mode the #19 FAIL-2 anti-pattern was named for. Specificity of prose
(exact line numbers, exact file names) can make a claim feel more credible
than a bare "looks clean" — but it doesn't change whether the actual command
output is present in the record. Don't let prose specificity substitute for
your own judgment on whether a real fenced code block with real grep output
exists.

## Rule going forward

When auditing the reviewer-gate checklist item:
1. Look specifically for a fenced code block (or equivalent verbatim
   command+output) in the reviewer's verdict comment — not just confident,
   detailed-sounding prose about what a check found.
2. If genuinely absent, this is a FAIL regardless of how specific or
   plausible-sounding the narration is, and regardless of whether your own
   independent re-run confirms the underlying claim was true. The
   underlying-truth check and the evidence-format check are two separate
   things — a PASS on one doesn't waive the other.
3. When dispatching reviewers (as the orchestrator), make the paste
   requirement explicit and literal in the dispatch prompt: "paste the
   actual command and its raw output in a fenced code block — a prose
   description of what it showed does not satisfy this requirement,"
   since "pasted output" alone has apparently been read as satisfied by a
   sufficiently detailed narrative.
