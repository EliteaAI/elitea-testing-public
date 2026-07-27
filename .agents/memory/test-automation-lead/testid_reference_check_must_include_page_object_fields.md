---
name: testid reference check must include page-object fields
description: control-audit item 2 ("every added testid referenced by the case's diff") requires grepping new LocatorDescriptor FIELD NAMES against the test file and all page-object methods, not just confirming the draft testid PR exists and the testid string is present live
type: feedback
---

## What happened (issue #75, ELITEA-1888, PR #533)

A delivery shipped 6 new testids via a compliant-looking flow: draft PR
opened on EliteaAI/EliteaUI (#567), commits landed on `automation/testids`,
promotability table verified true. Everything about the *delivery pipeline*
for the testids was correct. But 2 of the 6
(`agent-version-dialog-cancel-button`, `agent-version-dialog-close-button`)
were defined as `LocatorDescriptor` class fields in `agent_detail_page.py`
and then **never called anywhere** — not by any page-object method, not by
the test. They existed purely because the AFS's element/handle inventory
mentioned the Cancel/Close buttons (as part of describing the dialog), even
though the AFS's own covered-steps table never asked the test to exercise
them.

This slipped past the implementer's self-check AND a fresh reviewer round,
despite the exact rule being in canon since 2026-07-14
(`.agents/testing.md` line 90-93, `.agents/role-overrides.md` line 28-32):
"testids go ONLY on elements tests actually touch."

## The gap in how I'd been auditing item 2

Prior audits of item 2 ("testids delivered the canonical way") checked:
draft PR exists, built on fresh main, commits present on
`automation/testids`, diff is additive-only. That's necessary but NOT
sufficient — it verifies the testid was delivered correctly, not that it
was *needed*.

## The fix — always run this extra grep

For every new `LocatorDescriptor` field (or UPPER_CASE selector constant)
added in the case's own diff, grep its **Python identifier** (not the
testid string) against:
1. the case's own test file(s), and
2. every method body in the same page-object class (and any subclass that
   might call it).

If a field's identifier appears ONLY at its own definition line, it is
dead — flag it as a scope violation regardless of whether the underlying
testid is correctly wired up and promotable. A testid appearing in the
AFS's element/handle inventory is not the same as it being exercised by a
test step — the AFS's own Coverage/steps table is the ground truth for
"touched," not the handle inventory (which often documents the full dialog
surface for completeness, not just what gets clicked).

## Distinguish from the legitimate declared-improvisation carve-out

Compare to issue #30/#277: a same-hunk conditional-pair testid
(`entity-card-tag-overflow`, sibling of the used `entity-card-tag-chip`,
same ternary) that's reasoned-about in-code (docstring + AFS PROVENANCE) is
a textbook declared improvisation — not a solo-FAIL. The #75 case is
different: no declaration anywhere, and the fields aren't a disambiguation
pair for a used element, they're independent unused UI affordances the AFS
happened to mention while describing the dialog.
