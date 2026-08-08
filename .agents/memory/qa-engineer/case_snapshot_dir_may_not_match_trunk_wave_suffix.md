---
name: Case snapshot dir may not match trunk wave suffix
description: Dispatch named cases/<ID>.md under a "-w3" wave dir that doesn't exist; the real snapshot sat in the base "pipelines-remaining" dir (no wave suffix) even though the trunk branch was tests/batch-pipelines-remaining-w3
type: feedback
---

## What happened (ELITEA-2016 review, 2026-08-09)

Reviewer dispatch pointed at
`.agents/automation/pipelines-remaining-w3/cases/ELITEA-2016.md` — that path
does not exist. The case snapshots for this whole campaign live under the
un-suffixed `.agents/automation/pipelines-remaining/cases/` dir (30+ case
files, ELITEA-2016 among them), while the batch TRUNK branch is
`tests/batch-pipelines-remaining-w3` (and w1/w2 exist too, sequential waves
of the same larger campaign). The wave suffix is a branch/campaign-tracking
concept, not a snapshot-directory concept — cases aren't re-sharded into
per-wave case dirs.

## Fix / what to do next time

If a named `.agents/automation/<slug>/cases/<ID>.md` snapshot path 404s, before
falling back to a live TMS fetch: `find .agents/automation -iname "*<ID>*"` —
the campaign's base slug (strip any trailing `-wN`) almost certainly holds it.
Saves a TMS round-trip and keeps triangulation on the exact snapshot the
analyst worked from.
