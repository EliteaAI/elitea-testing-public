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

## Recurrence (issue #32, ELITEA-1790 rework, PR #280)

Same failure mode, terser still — the reviewer's comment on #280 didn't
even narrate specifics, just "Mechanical grep (rerun independently): empty
— no non-testid handles added." No file names, no line numbers, no code
block. And this time the **closure record compounded it**: it explicitly
asserted "Reviewed independently by a fresh qa-engineer session (APPROVED,
grep re-run and pasted)" — a claim about the evidence trail that is
verifiably false (nothing was pasted anywhere retrievable via `gh api`).
Two lessons stack here:
- The remedy from the #26 finding (make the paste requirement explicit in
  dispatch prompts) evidently hasn't fully stuck across sessions/dispatches
  yet — keep checking this item every audit, don't assume it's fixed team-wide.
- **A closure record's own narrative can misstate what evidence exists.**
  Don't just check "does the closure record claim the gate passed" — verify
  the specific evidentiary claim (e.g. "pasted") against the actual
  artifact it's describing. A closure record is itself an unverified claim
  until checked, same as any other work-log comment.

## Recurrence (issue #34, ELITEA-1792 rework, PR #283) — zero artifact, not just unpasted

Third occurrence, and a step further than #26/#32: this time there is no
reviewer artifact **anywhere retrievable** — `gh api .../pulls/283/reviews`
→ `[]`, `.../pulls/283/comments` → `[]`, `.../issues/283/comments` → `[]`.
The only record of round-1 CHANGES_REQUESTED and round-2 APPROVED is the
orchestrator's own paraphrase inside the issue-#34 work-log ("Mechanical
grep gate clean (pasted, all hits compliant)") — i.e. the orchestrator
asserts a paste exists that isn't retrievable on the PR at all, not even
as unpasted narration. A subtlety worth flagging for future audits: the PR
body in this case DID contain a pasted mechanical grep, but it was
explicitly labeled by the implementer as their own Phase-3 "reviewer
self-check" — don't let that label cause you to credit it as the fresh
reviewer's independent artifact. The two are different actors under the
slot contract (implementer self-check vs. fresh-session reviewer) even
when one borrows the other's vocabulary.

Three recurrences now (#26, #32, #34) despite the #26 remedy (make the
paste requirement explicit in dispatch prompts). Given the pattern keeps
recurring across different orchestrator sessions/dispatches, the fix
probably needs to move from "say it more clearly in the prompt" to a
structural check: the orchestrator should refuse to treat a review as
complete until it can `gh api` the PR/issue and see the reviewer's own
comment with its own paste, not just accept the reviewer subagent's
self-report back to the dispatching session.

## Recurrence (issue #35, ELITEA-1793 rework, PR #284) — merge-gate evidence bundled into the same gap

Fourth recurrence of the reviewer-gate shape, plus a new wrinkle: the SAME
single pre-merge comment (`.../issues/284/comments`, one entry, posted by
the PR-opening identity 7 seconds before the merge commit) narrates BOTH
"Reviewer: APPROVED (... mechanical grep gate pasted + verified 8/8
compliant ...)" AND "Orchestrator independent live-run gate: 3/3
deterministic (three separate pytest invocations, clean worktree, fresh
env)" — neither claim has a fenced command+output block anywhere on the PR
or issue. The PR body's OWN pasted 8/8-compliant grep (present, real,
correct) sits under a heading literally worded "Mechanical grep (reviewer's
own gate, pasted verbatim)" but was authored at PR-creation time by the PR
opener (the implementer's Phase-3 self-check), not posted independently by
a fresh-session reviewer afterward — the same implementer-self-check-
mislabeled-as-reviewer conflation as the #34 recurrence.

**New lesson**: the merge-gate item (§ checklist 5, the lead's own 3×
pre-merge invocations) is exposed to the exact same evidence-shape failure
as the reviewer-gate item (§ checklist 6) — a single narrated "did the
gate, it passed" comment written by the orchestrator right before merging
satisfies neither. Audit both checklist items independently even when they
show up bundled in one comment; a shared root cause (one actor writing one
summary comment instead of each gate leaving its own artifact) doesn't
make it one finding — it's two checklist items failing the same way.
