---
name: AFS wizard Current/Suggested column claimed asserted but has no real check
description: In an Edit-with-AI-style wizard AFS, "Current read-only vs Suggested editable column" case elements can end up covered ONLY by a data-level diff proxy — verify a real locator+assertion exists per row, not just the diff-differs check
type: feedback
---

## What happened (ELITEA-2611 review, PR #1477)

The AFS's Coverage Map marked case elements 10 ("Current" value read-only)
and 11 ("Suggested" value editable) — plus the "both shown" half of element
15 (Instructions Current vs Suggested) — as `asserted` at AFS step 6/7,
citing "CURRENT column" / "SUGGESTED column (contentEditable)" as the
assertion site.

The implementation (`ai_edit_skill_modal_page.py` + the test) only asserts:
default-checked state of the Apply-changes checkboxes, and a **data-level
diff** (`draft.get("description") != SEED_DESCRIPTION`) as the AFS's own
"diff-highlighting" proxy (justified in AFS Automation Hints, and that part
is fine). But nothing reads or asserts the CURRENT column's displayed value
or the SUGGESTED column's editability — no locator exists for either in the
page object (`TextDiffHighlight.jsx`, the component both columns render
through, has no testid, same as the diff-highlighting case, but no
Automation Hints entry addresses the read-only/editable distinction
specifically — only the diff-color mechanism).

**Root cause of the miss:** the AFS's own Automation Hints paragraph about
"assert the observable outcome, not the CSS mechanism" for diff-highlighting
reads, at a glance, like it also covers the read-only/editable claim — it
doesn't; those are two distinct original-case elements (10/11 vs 12) with
one shared justification paragraph that only actually argues for one of
them. Skimming Automation Hints as blanket cover for an entire step's
Coverage Map rows is the trap.

## Lesson for review

When an AFS step's "Verify" bullets list MULTIPLE distinct case elements
(e.g. "shows a CURRENT column" + "SUGGESTED column" + "diff highlighting"
+ "checkbox checked" — four different things), check the Coverage Map
disposition of EACH one independently against the code, even when they
share one step number and one Automation Hints paragraph. A single
justification note for the hardest one (diff-highlighting) can read as
covering the whole step's row cluster when it only covers one row.

## Lesson for implementers of this feature family

If a future Agent/Project-Context Edit-with-AI case needs to actually prove
"Current is read-only, Suggested is editable" as a real assertion (not just
inferred from `TextDiffHighlight.jsx`'s `mode="original"` vs
`mode="modified" editable` props), that component has no testid — same gap
as the diff-color case in `edit_with_ai_wizard_zero_testid_coverage.md`.
Options: add a scoped testid on `TextDiffHighlight`'s wrapper `Box`
distinguishing current/suggested (generic, shared-component name per
`.agents/testing.md`), or accept the data-level diff as the case's actual
proof and get the AFS Coverage Map to say so explicitly instead of claiming
column-level UI assertion it doesn't have.
