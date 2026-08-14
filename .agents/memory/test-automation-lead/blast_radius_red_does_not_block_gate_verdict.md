---
name: Blast-radius failures don't flip the gate's scripted verdict — route as a separate finding, don't reclassify
description: gate.verdict is authoritative for the NEW spec's N-consecutive-green contract; unrelated blast-radius reds are a distinct signal — file, don't block on them
type: feedback
---

## What happened

ELITEA-2369 (#877, 2026-08-06): the new spec itself went 3/3 consecutive green
(80.9s/74.8s/75.6s). The gate's **one** blast-radius run (over specs sharing files
the implementer touched — `agent_hub_page.py`, `chat_page.py`) surfaced **18**
unrelated failing/erroring specs across toolkits, skills, HITL, chat-canvas and
pipeline-editor — modules this PR never touched. `report.json`'s `gate.verdict`
was still `"green"`.

## Rule going forward

**The gate script's own `verdict` field is authoritative for whether the merge
gate passed** — it already encodes the two-count design (N consecutive greens on
the NEW spec is the hard contract; ONE blast-radius run over the shared-file
blast radius is a *separate*, non-blocking signal). Don't manually second-guess a
`green` verdict into a blocker because the blast-radius list looks alarming, and
don't silently drop the blast-radius list either — route it:

1. Land the case per the scripted verdict — a `green` with red blast-radius
   entries still merges.
2. File the blast-radius failures as their own tracker issue — **don't** fold
   them into the case's own closure record as if they were caused by it, and
   don't diagnose root cause yourself if the dispatch only names the one case
   (rule 6, factory mode: "discoveries become new issues, never started").
3. Neither `bug` (root cause[s] unconfirmed — could be flake, could be a real
   regression, could be environmental/session-state from a long-running suite
   sweep) nor `question` (nothing here blocks on a human decision) fits — a
   plain, unlabelled triage issue is the correct third bucket. Note in the body
   that a `batch-stabilize` pass or manual triage should classify root cause(s)
   before any per-cause `bug` ticket gets filed (strict-per-bug policy applies
   only once causes are actually known).
4. A single shared-fixture-looking cluster inside the noise (e.g. 4 specs in
   the same file, identical `RERUN, RERUN, ERROR` signature) is worth calling
   out explicitly in the issue even before diagnosis — it's a free hint for
   whoever triages next, not a claim of root cause.

Corollary on wall-clock: a single-case `batch-build` run can legitimately run
2+ hours when the implementer touches heavily-shared page objects, because the
blast-radius run sweeps the WHOLE suite once, not just the new spec (1057 tool
calls / ~77 min observed on this run alone). Don't read a long-running blast-radius
phase as a hang — keep polling in-turn (long `TaskOutput` blocking rounds), post
an interim work-log comment every few rounds so the issue thread shows liveness.
