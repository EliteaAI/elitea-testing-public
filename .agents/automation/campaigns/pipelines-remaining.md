# Campaign: pipelines-remaining

## State
- Stage: waves (wave-01 LANDED, wave-02 through wave-07 pending)
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
- Waves: **wave-01-node-type-configs (8 cases) LANDED** — elitea-testing-public#1329, merged `0206a8ef`,
  8/8 automated (1 sanctioned-RED: ELITEA-2047 vs #1327, deterministic 3/3), TMS back-written (8 cases,
  Form C), closure comment posted on #1297, campaign card updated.
  **wave-02-lifecycle-dashboard-version (10 cases) LANDED** — elitea-testing-public#1343, merged
  `6e1b1128`. 8 clean-green + 1 sanctioned-RED (ELITEA-2051 vs #570) + 1 already-covered (ELITEA-2063,
  dedup vs ELITEA-2002's spec, PR #1308). Internal gate this time produced a real verdict (green, 3/3,
  found a SECOND undeclared sanctioned-RED itself — ELITEA-2022 vs #1332 — correctly per the closed-set
  variant); lead still ran an independent from-scratch N=3 + both sanctioned-REDs 3x each per standing
  practice. TMS back-written (9 cases + 1 already-covered pointer), closure comment posted, campaign
  card updated.
  **wave-03-yaml-decision-trigger (5 cases) LANDED** — elitea-testing-public#1350, merged `7d79ad45`,
  5/5 automated (0 sanctioned-RED). Report bug found+fixed (ELITEA-2027 falsely marked blocked by the
  workflow despite being genuinely merged — see Log). TMS back-written, closure comment posted.
  **wave-04-canvas-editor-controls (6 cases) LANDED** — elitea-testing-public#1356, merged `e788bfc2`,
  5/5 automated + 1 already-covered (ELITEA-2060). TMS back-written, closure comment posted.
  **wave-05-chat-panel (7 cases) LANDED** — elitea-testing-public#1364, merged `9df3375c`, 6/7
  automated (0 sanctioned-RED), 1 blocked (ELITEA-2071, confirmed no-fullscreen-mode defect, #1363).
  TMS back-written (6 cases), closure comment posted.
  wave-06 through wave-07 (19 cases) — PLANNED, not yet launched (see Plan)
- Campaign totals so far: 36/55 terminal — 33 automated (2 sanctioned-RED: ELITEA-2047 vs #1327,
  ELITEA-2051 vs #570) + 2 already-covered (ELITEA-2063, ELITEA-2060) + 1 blocked (ELITEA-2071, #1363).
  19/55 remaining across wave-06..07
- **Operator directive 2026-08-08T13:42:41Z: "Proceed with all waves till you complete."** — running
  wave-02..07 sequentially without further per-wave checkpoints; only stopping early for a real blocker
  (question/bug protocol).

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
- 2026-08-08 wave-01-node-type-configs (8 cases) launched via batch-build.workflow.mjs, slug
  `pipelines-remaining-w1`, base `origin/automation/base`. **Run ID: wf_7fe2d036-b85** (task wylsub2n4).
  Polling in-turn for completion.
- 2026-08-08 wave-01 workflow completed (~5.5h wall clock, 43 agents, 7.37M tokens, 2391 tool calls).
  All 8 units built/reviewed/merged onto `tests/batch-pipelines-remaining-w1` cleanly (0 conflicts).
  Internal gate STALLED mid-run (verdict `not-run`, 1/3 green confirmed + run 2/3 left mid-flight per its
  own notes) — all 8 cases returned as `merged-ungated`, the known non-failure "gate never finished"
  outcome. Recovered per protocol: found run 2/3's leftover background log already green
  (`/tmp/gate_run2.log`, 7/7 passed), then ran my OWN fresh independent gate (testing.md § Merge gate —
  N=3 separate lead-run invocations): run 1/3 7 passed (226.06s), 2/3 7 passed (231.43s), 3/3 7 passed
  (229.09s) — all green. Sanctioned-RED spec (ELITEA-2047 vs open defect #1327) run 3× separately by the
  lead — identical deterministic failure all 3 runs, matching the linked ticket exactly (soft-assertion
  aggregation, no masking). Blast radius: 1 pre-existing spec
  (test_pipeline_llm_node_system_task_chat_history_config.py) calls the one non-additive page-object
  change (open_llm_node_output_select click-position fix) — ran once, 2/2 green, no regression.
  PR elitea-testing-public#1329 opened + squash-merged (`0206a8ef`). TMS back-written for all 8 cases
  (Form C, self-checked against real JUnit output from the lead's own gate runs — all 8 MATCH).
  onetest index.json rebuilt (2789 cases). Testid provenance: 7 testid commits on
  EliteaAI/EliteaUI@automation/testids (92fc6ec4 ELITEA-2009, 4195321f ELITEA-2035, d8afe3b0 ELITEA-2036,
  2859a9d0 ELITEA-2038, 955f88b9+b65756af ELITEA-2039, 94d190c9 ELITEA-2047 — no new testid needed for
  2045/2046, reused existing generic structured-output-toggle mechanism) — verified via fresh
  `git fetch origin` + per-file diff (`git diff origin/main origin/automation/testids -- <file>`, more
  reliable than literal-string grep here since several testids are runtime-composed via
  `` `${PREFIX}-suffix` `` template literals, e.g. AgentNode.jsx's `AGENT_NODE_TESTID_PREFIX`,
  DefaultNode.jsx's `TEST_ID_PREFIX_BY_NODE_TYPE`): all 6 touched component files differ from
  `origin/main` — **none of this wave's testids are on `main` yet**, all pushed to `automation/testids`
  only, awaiting human cherry-pick.
  Defects: filed #1327 (Interrupt-after resume path, confirmed 2/2, sanctioned-RED); reconfirmed
  (not newly filed) #1025 and #1274 as not-applicable/already-tracked during analysis. No new duplicate
  filings.
  Closure comment posted on #1297. Card → `Ready`. 8 unit branches deleted (squash-merge auto-delete);
  batch trunk `tests/batch-pipelines-remaining-w1` deleted with the PR merge.
- 2026-08-08T13:42 Operator: "Proceed with all waves till you complete." Card Approved → In Progress.
  sync-base-branches re-run (all 3 branches still current, smoke 2/2 green). wave-02 launched
  (10 cases), Run ID wf_101d0ba3-47f (task wgcf6elq8) written immediately.
- 2026-08-08T20:00 wave-02 workflow completed (~5.7h wall clock, 48 agents, 7.78M tokens, 2157 tool
  calls). This time the INTERNAL GATE completed with a real verdict (green, 3/3, 363/354/374s) —
  no stall/recovery needed. It also self-discovered a SECOND sanctioned-RED not in the dispatch's
  declared list (ELITEA-2022 vs new defect #1332, redirect no-op) while reading the spec diff, applied
  the closed-set variant correctly, and flagged it explicitly for the lead. Lead still ran an
  independent from-scratch gate per standing practice: N=3 on the green-required set (6 new files +
  full test_pipeline_management.py minus the 1 deselected sanctioned-red test) — 21 passed/1 deselected
  all 3 runs (357.9/349.6/352.6s); both sanctioned-RED specs (ELITEA-2051 vs #570, and
  test_delete_pipeline_via_ui_menu vs #1332) run 3x separately each — identical deterministic failure
  every time. Blast radius: reviewed diff of both touched page objects — purely additive (one benign
  import-list expansion only), no separate blast-radius spec needed beyond what's already in the
  green-required set. PR elitea-testing-public#1343 merged (`6e1b1128`). TMS back-written: 9 automated
  cases (Form C, self-checked against the lead's own JUnit output — all MATCH after fixing one mapping
  slip on first pass — ELITEA-2050 was initially miskeyed to the wrong test file, caught before
  committing) + 1 already-covered pointer (ELITEA-2063 → ELITEA-2002's pre-existing test + its original
  PR #1308, not this wave's PR). Testid provenance: 3 new commits on
  EliteaAI/EliteaUI@automation/testids (467fed43 ELITEA-2051, f83557e4 ELITEA-2049, 257cd359 ELITEA-2012)
  — all 4 touched component files differ from `main`, none promoted yet. Closure comment posted on
  #1297. Card stays In Progress (operator directive is running-until-complete — no Ready checkpoint
  between waves this time). Launching wave-03 next.
- 2026-08-08T20:05 wave-03-yaml-decision-trigger (5 cases) launched. **Run ID: wf_308e801c-d83**
  (task w18hrprzc). Polling in-turn for completion.
- 2026-08-09T01:52 wave-03 workflow completed (~5.7h wall clock, 19 agents, 2.91M tokens, 856 tool
  calls). Gate green 3/3 (286/281/282s), no sanctioned-RED this wave. **Report bug found and fixed:**
  the workflow's own final report wrongly marked ELITEA-2027 `blocked` ("subagent completed without
  calling StructuredOutput") despite it having ALREADY built, been reviewed APPROVED, and merged
  (confirmed via `git log` — commit 57fa9244 — AND a genuinely merged PR #1344, AND the extended test
  function present + green in the lead's own gate runs). Root cause not fully diagnosed (likely a
  stale/duplicate re-analysis dispatch whose failure overwrote the real outcome in the report's case
  list) — corrected `report.json` by hand before proceeding, all 5/5 marked `automated`. **Also found:**
  wave-01 and wave-02's report.json/report.md were never committed to git (`.agents/automation/` is
  gitignored by default; case snapshots + campaign card were force-added but the wave reports were
  missed) — fixed retroactively, all 3 waves' reports now committed (matches the `approved-top10`
  precedent of committing report artifacts). Lead ran independent N=3 gate on the 5 green specs (9
  collected tests) — 9 passed every run (279.8/279.5/278.8s). Blast radius: only
  `pipeline_detail_page.py` touched, 0 removed lines, purely additive — no separate spec needed. PR
  elitea-testing-public#1350 merged (`7d79ad45`). TMS back-written (5 cases, Form C, self-checked
  against the lead's own JUnit output incl. re-confirming ELITEA-2027's test really passes). Testid
  provenance: 1 new commit (28dbc5e4, ELITEA-2041) — file differs from main, not promoted yet. Closure
  comment posted on #1297. Card stays In Progress. Launching wave-04 next.
- 2026-08-09T02:05 wave-04-canvas-editor-controls (6 cases) launched. **Run ID: wf_b5ca8d13-d14**
  (task wcukzt24q). Polling in-turn for completion.
- 2026-08-09T04:29 wave-04 workflow completed cleanly (~2.5h wall clock, 23 agents, 3.25M tokens, 857
  tool calls) — gate green 3/3 (227.6/225.0/245.4s) on the first try, no report bugs this time; all 5
  unit PRs (#1351-1355) independently confirmed MERGED via `gh pr view` before trusting the report.
  Lead ran independent N=3 gate on the 4 green specs (14 collected tests) — 14 passed every run
  (227.9/225.2/254.6s). Blast radius: only `pipeline_detail_page.py` touched, 0 removed lines, purely
  additive. PR elitea-testing-public#1356 merged (`e788bfc2`). TMS back-written: 5 automated + 1
  already-covered (ELITEA-2060 → ELITEA-2018's pre-existing test, PR #1143). Testid provenance: 1 new
  commit (74ba8918, ELITEA-2072) — file differs from main, not promoted yet. Closure comment posted on
  #1297. Card stays In Progress. Launching wave-05 next.
- 2026-08-09T04:45 wave-05-chat-panel (7 cases) launched. **Run ID: wf_0e4dae17-105** (task w41f7n4ly).
  Polling in-turn for completion.
- 2026-08-09T04:48 Hard failure at 130s (task w41f7n4ly): triage agent never called StructuredOutput.
  Verified nothing landed (no branches created). Resumed same runId, new task w99k1v4ic. Polling.
- 2026-08-09T08:16 Second hard failure on task w99k1v4ic (same runId), 32 agents done first (6/7
  cases merged per git log: 2017/2052/2053/2058/2059/2062; ELITEA-2071 analyst returned defect-found,
  issue #1363 filed — the crash was in the NEXT dispatch after that, likely gate or an erroneous
  implementer attempt on a defect-found case). Resumed again, same runId, task w6qnx51j1.
- 2026-08-09T08:38 wave-05 workflow completed on the 3rd attempt (task w6qnx51j1). Internal gate
  stalled again (`not-run`, 1 run 360.97s, all 6 cases `merged-ungated`) — same known pattern. All 6
  unit PRs (#1357-1362) independently confirmed MERGED via `gh pr view` before trusting anything.
  Lead ran fresh N=3 gate on the 5 green-required specs (11 collected tests, ELITEA-2058 shares
  ELITEA-2017's test via extend-existing) — 11 passed every run (357.2/345.1/320.9s). Blast radius:
  full diff review showed ZERO net removed lines in pages/fixtures/api despite ELITEA-2052's fix round
  removing 4 dead LocatorDescriptor fields mid-PR (nets to zero vs base — added then removed within
  the same PR). ELITEA-2071 stayed `blocked` — genuinely confirmed: pipeline chat panel has NO
  fullscreen/expand control at all (only a collapse toggle), filed #1363, not part of this merge.
  **Gotcha, caught before it mattered:** a campaign-card commit landed on the batch trunk branch
  instead of `automation/base` (stray checkout left by a crashed workflow run) — caught via
  `git branch --show-current` habit before the NEXT commit, cherry-picked cleanly onto
  `automation/base` before opening the trunk→base PR. PR elitea-testing-public#1364 merged
  (`9df3375c`). TMS back-written: 6 automated (ELITEA-2071 stays `draft`, blocked — not backwritten,
  matches policy for real product blockers). Testid provenance: 3 new commits (a926573d+2a4aab23
  ELITEA-2059, 63c96dd7 ELITEA-2053) — all 3 files differ from main, not promoted yet. Closure comment
  posted on #1297. Card stays In Progress. Launching wave-06 next.
- 2026-08-09T09:05 wave-06-state-settings-tools (8 cases, 1 cluster [ELITEA-2054,ELITEA-2055])
  launched. **Run ID: wf_68c5d244-cb1** (task wso28t4wd). Polling in-turn for completion.
