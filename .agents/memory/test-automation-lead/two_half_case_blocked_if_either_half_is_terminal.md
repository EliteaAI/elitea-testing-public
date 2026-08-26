---
name: A case with two halves is blocked if EITHER half is terminal and is the case's subject
description: One reproducible half never licenses ready-for-automation; check every step the case names before overturning a blocked verdict
type: feedback
aliases: [reopen blocked case, half reproducible, partial coverage, sanctioned-RED misapplied]
tags: [area/afs-gate, type/classification]
created: 2026-08-27
updated: 2026-08-27
---

## The mistake, in my own words

I re-opened ELITEA-1984 (#1394 wave-03) believing its `blocked` verdict had
misapplied `.agents/testing.md` § Merge gate → *Analysis-time entry*. My evidence
was real: the linked bug (#1713) showed the cancel path reproducing **live with no
provider identity**, and the defect plainly did not block further exploration —
which is the exact criterion that rule turns on.

A fresh analyst re-executed it live and **re-blocked it**. I was half right, and
half right is blocked.

The case named two failure paths:

| Half | Reproducible? |
|---|---|
| the user **cancels** (closes the OAuth popup) | yes — that was #1713, my half |
| the **provider denies** authorization | no — needs a registered OAuth client |

The second half was steps 5–6 — *the case's subject*. Its observable was reachable
only through a real provider redirect, so simulating it would be terminal
substitution. Coverage of the first half does not buy the case.

## The rule

Before overturning a `blocked` verdict, **enumerate every step the case names and
find which one carries the subject.** "This part reproduces" is an argument for a
*rescope*, never for `ready-for-automation` — and a rescope drops steps, which
changes *what is verified*, which is a human decision (`role-overrides.md`
§ declared-improvisation protocol, ceiling). Route it; don't declare it.

## What made the re-check worth doing anyway

The re-examination was not wasted, and this is the part worth repeating:

- The blocker sharpened from *"needs a Microsoft account"* to an exact
  provisioning order (registered Entra app + redirect URI + a consenting account).
- It **corrected a false claim** in the already-merged AFS — "the provider answers
  a bare 404 and never redirects back" was true only of the *placeholder* tenant.
- The AFS now fully specifies the descoped ~40 s spec, so approving the rescope
  costs no further exploration.

So: re-check a blocked verdict when you have new evidence — but dispatch a fresh
analyst to re-execute it, never overturn it from your own desk reading.

Related: [[credentials_area_backlog_1394]] · [[afs_gate_rulings]] · [[afs_defect_found_can_be_extend_existing_shaped]]
