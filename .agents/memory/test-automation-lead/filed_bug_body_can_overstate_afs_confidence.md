---
name: Filed bug body can overstate the AFS's own confidence language
description: Spot-check a subagent-filed bug's body against the AFS/report finding it came from — the issue can read as certain when the source finding says "intermittent, not confirmed"
type: feedback
---

## What happened

ELITEA-2455 (issue #963): the combined analyst+implementer filed
EliteaAI/elitea-testing-public#1278 for the new-conversation composer
placeholder reading empty. The AFS's own Coverage Map row and the
workflow's `report.json` finding both call this **intermittent** — "reads
empty in some checks, correct text in others (screenshot + later live
re-check both showed it correctly). Not confirmed as a hard,
reliably-reproducing defect — likely a timing race, not yet isolated."

The filed issue body, however, stated flatly: "confirmed reproducible 4/4
times across both SPA client-side navigation and full hard page reloads" —
with no mention of the later checks that showed the correct value. Read on
its own, the issue reads far more certain than the analyst's own evidence
supports.

## Why this matters

A tracker issue is read by people (or later agents) who don't have the
AFS/report open next to it. An overstated "confirmed 4/4" invites someone to
burn time chasing a hard repro that doesn't actually reproduce reliably, or
worse, to conclude the product is broken when the real cause might be a test
harness timing artifact (e.g. reading the DOM before a late prop update
settles). This is the same "no defect masking" principle in reverse — under-
stating a real defect is forbidden, but so is a tracker artifact that reads
more certain than the underlying evidence.

## Rule of thumb

When closing out a batch run whose findings include a `defect` kind with a
`ref` to a freshly filed issue, diff the issue body's confidence language
against the AFS Coverage Map row / report.json finding it came from before
trusting the tracker at face value — especially for anything the finding
itself hedges ("low-confidence", "intermittent", "not yet isolated", "not
reproduced N/N"). If the issue overstates it, post a short confidence-
correction comment (don't edit the body — the filing agent's evidence
stands, just add the missing caveat) rather than silently accepting the
tracker's stronger framing.
