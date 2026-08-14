---
name: An assertion can prove the wrong fact — invert-checking is necessary, not sufficient
description: A positional/relational assertion can be non-tautological (inverting it really fails) and still prove something other than the claim, because its comparison target is structurally decoupled from the thing under test. The fix is a same-category comparison target — seed a real sibling instance — not a stronger version of the same comparison.
type: feedback
---

## Rule

Two independent questions about any new assertion:

- **Can it fail?** → temporarily invert it, rerun once, confirm a real
  `AssertionError` with the expected values in the message, revert. Cheap;
  do it on every "add a missing assertion" fix.
- **Does failing mean the claim is false?** → name the comparison target and
  ask what structural invariant already forces the result. If the target sits
  in a *different DOM section*, a different entity category, or is otherwise
  ordered by layout rather than by the behavior under test, the assertion
  passes the invert check and still proves nothing about the claim.

**"New X prepends to the top of the X list" can only be tested against
another member of that list.** Comparing the sole folder's bounding box
against a conversation date-group heading only proves the Folders and
Conversations containers are separate siblings — Folders is always first, so
the check is immune to a real prepend-vs-append regression. Fix: **seed a
real sibling instance of the same thing** and compare against its own row.
Do not "strengthen" the decoupled comparison.

## Judgment calls when fixing this in a fix-only round

- Seed via the case's own UI flow (click the same button twice) rather than
  building new API infra the round doesn't need — even when the AFS's
  Automation Hints recommend an API client.
- **Drop the superseded check.** When the new comparison strictly supersedes
  the old, remove the old check's *usage* (and its now-pointless fixture);
  leave the harmless additive page-object method in place. Belt-and-suspenders
  doubles the seeded state for zero marginal strength.
- **Verify the mechanism live before writing code** whenever the fix rests on
  product behavior you haven't personally watched (here: "can two folders
  share the default name?", "does a second create-folder click open a NEW
  editor above the first?") — a few minutes of `playwright-cli` turns "I
  assume" into "I watched."
- **Scale the leak check to what you added.** Doubling the seeded entities
  means the out-of-band leftover check must independently verify BOTH ids
  every run, including the asymmetric early-failure path where only one
  exists — show both `if <id>:` guards working, not one.

## Seen 2×

- ELITEA-2132 / PR #698 R2→R3 — R2's folder-vs-"Today"-heading box comparison passed the invert check and was reviewed as solid; R3 showed it proved layout separation, not prepend order. Fixed by seeding a baseline folder through the case's own UI flow.
- ELITEA-2132 / PR #698 R2 (same PR, earlier) — the invert-sanity-check habit itself, established while adding the assertion that later proved to be the wrong fact — which is precisely why it is necessary-not-sufficient.

See also: positional_check_needs_same_category_comparison_target.md ·
console_filter_idiom_and_seed_vs_document_ambient_data.md (§ invert-check) ·
../qa-engineer/positional_assertion_wrong_comparison_target_survives_invert_sanity_check.md
