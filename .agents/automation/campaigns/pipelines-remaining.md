# Campaign: pipelines-remaining

## State
- Stage: waves (wave-01 launching)
- Conductor: none — plain sequential `batch-build` waves (foundation is null and already evidenced;
  per `campaign-planning.md` § When NOT to run a campaign, the full conductor apparatus is skipped)
- Operator checkpoint: **substituted** — factory/unattended mode has no interactive `AskUserQuestion`.
  Human already saw the full 55-case candidate list (posted as a comment on
  EliteaAI/elitea-testing-public#1297) and replied "Ok, automate this batch" — treated as blanket plan
  approval. The lead (this agent) self-reviewed the dispatched planner's wave/cluster proposal in its
  place (see Plan below) before launching wave-01. Documented here for a human to override at any point
  by commenting on #1297.
- Foundation merged: n/a — foundation is null (pipelines surface already foundation-rich: `automation/pages/`
  has pipeline page objects, `automation/tests/ui/pipelines/` has ~30 existing test files, 27 sibling
  pipeline cases already automated per prior campaigns incl. `approved-next50`)
- Foundation surfaces CLAIMED: none (no foundation stage)
- Heads analyzed: none (skipped — no foundation stage)
- Waves: wave-01-node-type-configs (8 cases) — launching
  wave-02 through wave-07 — PLANNED, not yet launched (see Plan)

## Source

Tracking issue: EliteaAI/elitea-testing-public#1297 ("[Automate] Ramaining pipeline test cases").
55 pipeline TMS cases with no board task and no TMS automation record, identified by a scoping pass
posted to #1297 on 2026-08-07. Per #1297's explicit instruction, **no per-case board tasks are created**
— all progress is tracked in #1297 itself via work-log comments + closure-record-style updates, and in
this campaign card for durable cross-session state.

Case snapshots: `.agents/automation/pipelines-remaining/cases/*.md` (committed on automation/base,
intake commit on 2026-08-08).

Pre-check: `ls automation/pages/` + `ls automation/tests/ui/pipelines/` both confirm existing pipeline
coverage — foundation-rich, no greenfield bootstrap needed.

## Goal

No numeric coverage goal set — plain backlog automation of the 55 identified cases.

## Plan (planner-proposed, lead-self-reviewed in place of an operator checkpoint)

```json
{
  "campaign": "pipelines-remaining", "batch": "pipelines-remaining", "base": "origin/automation/base",
  "foundation": null, "goal": null,
  "waves": [
    { "slug": "wave-01-node-type-configs",
      "caseIds": ["ELITEA-2009","ELITEA-2035","ELITEA-2036","ELITEA-2038","ELITEA-2039","ELITEA-2045","ELITEA-2046","ELITEA-2047"],
      "clusters": [] },
    { "slug": "wave-02-lifecycle-dashboard-version",
      "caseIds": ["ELITEA-2003","ELITEA-2063","ELITEA-2022","ELITEA-2012","ELITEA-2050","ELITEA-2049","ELITEA-2051","ELITEA-2024","ELITEA-2025","ELITEA-2013"],
      "clusters": [] },
    { "slug": "wave-03-yaml-decision-trigger",
      "caseIds": ["ELITEA-2027","ELITEA-2029","ELITEA-2067","ELITEA-2016","ELITEA-2041"],
      "clusters": [] },
    { "slug": "wave-04-canvas-editor-controls",
      "caseIds": ["ELITEA-2019","ELITEA-2057","ELITEA-2060","ELITEA-2061","ELITEA-2072","ELITEA-2048"],
      "clusters": [] },
    { "slug": "wave-05-chat-panel",
      "caseIds": ["ELITEA-2017","ELITEA-2052","ELITEA-2053","ELITEA-2058","ELITEA-2059","ELITEA-2062","ELITEA-2071"],
      "clusters": [] },
    { "slug": "wave-06-state-settings-tools",
      "caseIds": ["ELITEA-2043","ELITEA-2044","ELITEA-2066","ELITEA-2054","ELITEA-2055","ELITEA-2056","ELITEA-2064","ELITEA-2065"],
      "clusters": [["ELITEA-2054","ELITEA-2055"]] },
    { "slug": "wave-07-run-details-execution-introspection",
      "caseIds": ["ELITEA-2011","ELITEA-2070","ELITEA-2451","ELITEA-2454","ELITEA-2443","ELITEA-2444","ELITEA-2445","ELITEA-2446","ELITEA-2447","ELITEA-2448","ELITEA-2449"],
      "clusters": [] }
  ],
  "extendCandidates": ["ELITEA-2003","ELITEA-2011","ELITEA-2016","ELITEA-2022","ELITEA-2024","ELITEA-2027","ELITEA-2029","ELITEA-2041","ELITEA-2048","ELITEA-2049","ELITEA-2050","ELITEA-2063","ELITEA-2067","ELITEA-2070"],
  "policy": {}
}
```

Rationale (planner, verbatim): "Pipelines surface confirmed foundation-rich (foundation: null, no
scaffolding stage needed). Clustering stayed conservative per the differs-in-DATA-not-STEPS test: the
five node-type config cases (Code/StateModifier/Custom/Agent/Printer) share an identical 6-8 step
template but each configures structurally different fields, so they were kept solo rather than
force-merged into a false family; the only case surviving the test was ELITEA-2054/2055 (Step limit vs
Editor notes — same expand/edit/save/reload/verify flow, differing only in field name and value). Wave 1
was picked first because it has zero suspected extend-candidates and every case is a clear standalone
add-node/configure/persist flow, ideal for validating the batch mechanism on clean ground before wave 2's
dense cluster of dashboard/lifecycle extend-candidates and wave 7's large Run-Details/subgraph/code-state
wave."

Verified 55/55 covered across the 7 waves, no duplicates, no omissions (checked programmatically by the
lead before launching wave-01).

## Log

- 2026-08-08 Intake: 55 case snapshots written + committed to `automation/base` (`.agents/automation/pipelines-remaining/cases/`).
- 2026-08-08 sync-base-branches run (all 3 branches already current — automation/base 0 behind main;
  EliteaUI automation/testids 0 behind main; elitea_assistant automation/testids 0 behind main). Smoke
  suite green (2/2) post-sync.
- 2026-08-08 Planner dispatched (qa-engineer) over the 55 snapshots — returned the 7-wave plan above.
  Lead verified 55/55 coverage programmatically, no dupes/gaps. Self-approved (operator checkpoint
  substitution documented above under State).
