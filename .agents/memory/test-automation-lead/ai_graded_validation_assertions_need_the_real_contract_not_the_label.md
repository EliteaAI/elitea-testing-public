---
name: AI-graded validation status labels are non-deterministic — assert the real gate, not the label
description: Elitea's publish_skill_validate (and likely other LLM-judged endpoints) can return different status labels (WARN vs PASS) for the byte-identical fixture across separate runs, moving the same finding between warnings[] and recommendations[]. Never assert the exact label; assert the deterministic field (critical_issues empty/non-empty) plus the real downstream behavior (Publish succeeds/is blocked).
type: feedback
---

## What happened (2026-08-12, #1399/wave-03, ELITEA-2598)

A test asserted `validate_body.get("status") == "WARN"` for a skill with a generic
name ("skill") but otherwise-valid content (icon + tag present). The lead's own gate
run caught the SAME fixture returning `status: "PASS"` instead, with the identical
generic-name finding moved from `warnings[]` to `recommendations[]` — `critical_issues`
stayed `[]` in both cases. Confirmed via captured `junit.xml` response bodies across
multiple runs, not guessed. A later re-verification pass (5 runs) caught a THIRD live
phrasing variant on the AI's free-text suggestion field too.

## The fix pattern

1. Never assert the LLM grader's status label exactly (`WARN`, `PASS`, etc.) when the
   case's real behavioral contract is about a DIFFERENT, deterministic gate (here:
   "non-critical issues don't block Publish"). Assert:
   - `status in (<the set of non-blocking labels>)` — a set, not a single value, if the
     grader can legitimately move a finding between them.
   - The actual deterministic blocking condition (`critical_issues == []`).
   - The real downstream behavior (Publish button enabled, Publish POST succeeds, entity
     appears where expected) — this is the thing that would ACTUALLY turn red if the
     product regressed.
2. Never keyword-match the AI's free-text prose (`"generic" in suggestion`) — it has
   multiple live-observed phrasings for the same finding. Assert structure instead
   (the right `field` name is present, non-empty text) if you must assert anything
   about the free-text at all.
3. This is NOT a case-text-drift clarification and NOT a product defect — it's inherent
   non-determinism in an LLM-graded response. Document it as a Known-Defects-style note
   in the AFS with the captured evidence (not a `bug`/`question` tracker filing) so
   nobody re-litigates it as either.

## Verifying the fix isn't masking

Before approving a loosened assertion like this, confirm the diff still asserts
something that WOULD fail on a real regression: is the deterministic blocking field
still checked unchanged, and is the downstream behavior (the thing that actually
matters to the user) still independently confirmed, not just "validation returned a
benign-looking status"?

See also: `.claude/skills/test-automation-workflow/references/orchestration-playbook.md`
§ No Defect Masking (the general decision tree this is an instance of).
