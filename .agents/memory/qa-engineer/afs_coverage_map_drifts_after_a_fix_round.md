---
name: AFS Coverage Map drifts after a fix round
description: A fix round that corrects Handles Reference / Test Steps rarely sweeps the Coverage Map — tick that section against the CODE, not against the AFS prose above it.
type: feedback
aliases: [coverage map drift, afs stale row, asserted where cell, fix round docs sweep]
tags: [area/review, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## The gotcha

An AFS has the same fact in four places: § Test Steps, § Handles Reference,
§ Implementer notes, and the Coverage Map's "Asserted where" cell. A fix round
that changes an assertion's *mechanism* updates the first three (they are
prose the author is actively editing) and silently leaves the fourth stale —
the Coverage Map is a table at the bottom nobody re-reads while writing.

Worked example (PR #1911, ELITEA-2349, fix round 3): commit `56c1b7ca9` swapped
a `MuiAlert-colorError` class assertion for a `data-severity` attribute filter
and narrowed a stack-trace check from the page `body` to the `settings-content`
pane. § Test Steps, § Handles Reference and § Implementer notes all say
`data-severity` / `settings-content`. The Coverage Map row still reads
"`toast-alert` visible + `MuiAlert-colorError` … no stack markers in toast text
or page body" — naming two assertions the shipped code does not make.

## Why it matters and how to catch it

The Coverage Map is the section the reviewer ticks and the delivery audit reads.
A stale "Asserted where" cell is not caught by any grep, any linter, or a green
run — all three see prose. It is only caught by ticking the cell against the
DIFF rather than against the paragraphs above it in the same file.

Not automatically blocking: judge the row's **disposition** (is the observable
asserted at all?) separately from its **mechanism** (is the named assertion the
one in the code?). A wrong disposition is `CHANGES_REQUESTED`; a stale mechanism
on a correctly-asserted row is a docs finding — but say it, because the next
fix round is the cheapest moment to sweep it.

Related: [[afs_on_main_provenance_needs_a_file_level_check]]
