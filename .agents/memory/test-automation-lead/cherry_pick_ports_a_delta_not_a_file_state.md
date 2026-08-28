---
name: A cherry-pick to main ports a DELTA, not a file state
description: Cherry-picking a repair onto main silently drops every doc section added by OTHER commits — and the wholesale restore that fixes it imports text that is false on main
type: feedback
aliases: [cherry-pick drops AFS sections, port a fix to main, AFS reverted by port, doc drift on port, wholesale restore imports falsehood]
tags: [area/branching, type/lesson]
created: 2026-08-28
updated: 2026-08-28
---

## The trap, in two directions — and the second is CAUSED by fixing the first

Porting a repair from `automation/base` to `main` with `git cherry-pick <sha>`
applies **that one commit's diff** on top of main's older file. It does NOT
reproduce base's file state. Any section added to the same doc by *other*
commits on base never comes across, and there is no conflict to warn you.

**Direction 1 — the port DROPS truth.** On #1895/ELITEA-2008 the cherry-pick
carried 2 of ~17 AFS amendment sections. The dropped ones included the amended
Expected Results, so `main`'s AFS was left stating the **pre-fix contract**
unmarked as superseded — the exact assertion the card was filed against,
presented as current. A later `adjust-automated-test` triangulating the test
against it would "repair" the test *back* and re-create the issue.

**Direction 2 — the wholesale restore IMPORTS falsehood.** Fixing direction 1 by
`git checkout origin/automation/base -- <doc>` then carried across text that is
**true on base** (which still runs that code) and **false on main** (which does
not) — a disproved root cause aimed straight at the next reader.

## Catch both — neither is reachable by the three mandatory greps

The locator/fidelity/masking greps scan `automation/` only, so a doc defect is
invisible to all of them. All three review blockers on PR #1929 were docs; the
code was sound from round 2 onward.

```bash
# direction 1 — dropped sections (every "<" line is content the port lost)
diff <(git show origin/automation/base:<doc> | grep -E '^#{1,4} ') \
     <(git show HEAD:<doc>                   | grep -E '^#{1,4} ')

# direction 2 — imported falsehood: grep the RESTORED file for the old
# mechanism phrases AND the symbol names the repair deleted
git show HEAD:<doc> | grep -nE '<old mechanism phrase>|<deleted symbol>'
```

If base is a verified **strict superset** (heading diff shows main contributes
nothing), restoring wholesale is right — then immediately run direction 2 and
add a dated "**Superseded on `main` by PR #N**" addendum rather than editing the
historical record away. The branches then legitimately diverge by that paragraph
until the repair itself reaches base.

## Also check the dependency chain

The ported spec imported `utils/console_errors`, a base-only module — the port
did not even *import* on main until it came across too. Run the test once before
gating; a `ModuleNotFoundError` is the cheap version of this lesson.

Related: [[main_and_base_can_carry_different_variants_of_one_spec]] · [[promoted_test_fixes_branch_from_main]]
