# When I order an addition mid-flight, I have edited the AFS too — say so in the same dispatch

**Date:** 2026-09-09 · **Context:** #2112 / ELITEA-0679, reviewer's sole blocker

## What happened

The analyst's AFS flagged an optional coverage improvement in a section headed
*"Optional coverage improvement — **NOT included in the proposed diff**"*, and marked the
matching Coverage Map row `partial` / *"state not asserted"*.

I ruled: ship it. The implementer shipped it. **Nobody amended the AFS**, so the brief now
asserted, in two places, something false about the code sitting next to it. The fresh reviewer
made that its single blocking finding — correctly. Cost: one extra fix round.

Note what did NOT catch it: **both mechanical greps came back 0 hits, twice** (implementer and
reviewer). Greps see added handles and substitutions. They cannot see a document disagreeing
with the code.

## The rule

**A lead ruling that changes WHAT is verified is an amendment to the AFS, not just an
instruction to the implementer.** Order both in the same dispatch, explicitly:

> "…and amend the AFS accordingly: flip Coverage Map row N to `covered` citing the new line,
> rewrite the deferral section to record the ruling, and add the change to the Adjustment table
> classified as a strengthening."

## Where to look, because it is not only the Coverage Map

An AFS's *deferral* sections rot in the same stroke and are easy to miss — they are phrased in
the negative, so a reader skims past them:

- `§ Optional … — NOT included in the proposed diff`
- `§ Proposed diff` (the snippet stops matching what shipped)
- `§ Adjustment` (the ordered change is the ONE change with no rail classification)
- `§ Handles Reference` (a "not extended" claim goes stale the moment a new call site appears)

**Check the shipped diff against the AFS's deferral sections, not just against its proposed
diff.** That is where this one lived.

## Why it matters beyond bookkeeping

The AFS outlives the conversation that produced it. A later auditor or analyst triangulating
against a stale row records a coverage gap that no longer exists — or "helpfully" adds a second
assertion for it. This is the *"the AFS is the bug"* class the triangulation gate exists to
catch, and row 1 of the triangulation table (all three artifacts agree) cannot see it, because
they no longer do.
