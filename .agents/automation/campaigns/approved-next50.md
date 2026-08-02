# Campaign: approved-next50

## State
- Stage: plan-proposed (awaiting operator checkpoint)
- Conductor run: wf_aa16c5c4-f74 — propose call, completed 2026-08-02
- Foundation merged: n/a — foundation is null (all 4 surfaces already foundation-rich, evidenced by directory listing)
- Foundation surfaces CLAIMED: none (no foundation stage)
- Heads analyzed: none yet (foundation:null skips the heads/foundation/mini-gate stages entirely)
- Waves: 11 proposed, none run yet
- Landing: per-batch (policy unset in plan → script default; profile.md doesn't declare a landing granularity, so the default applies) — land each wave before the next cuts its trunk

## Source

50 cases, next in raw board #9 Approved-column API order after `approved-top10`
(unsorted — issue numbers as GitHub returned them, NOT sorted by id/priority):

188, 191, 210, 217, 218, 220, 229, 234, 248, 258, 259, 263, 267, 338, 340, 352,
365, 371, 384, 400, 403, 405, 406, 407, 414, 415, 416, 417, 418, 421, 424, 428,
434, 435, 436, 437, 441, 442, 443, 444, 445, 447, 451, 452, 455, 458, 465, 467,
468, 469

Modules touched (per case titles): agents (2), artifacts (11), chat-interface
(23), pipelines (14).

Pre-check before proposing: all 4 surfaces already have page objects + test
dirs in `automation/` (agents, artifacts, chat, pipelines) — foundation-rich,
no greenfield bootstrap expected. `ls automation/pages/` and `ls
automation/tests/ui/` both confirm existing coverage per surface.

## Pre-batch state

- Board: all 50 issues moved In Progress, assigned, work-log comment posted,
  before dispatch.
- Case snapshots: `.agents/automation/approved-next50/cases/*.md` (committed
  on automation/base, edbe9c6e).
- base: origin/automation/base (up to date — includes the just-merged
  approved-top10 batch, PR #1097).
- No other campaign cards exist yet (`.agents/automation/campaigns/` was
  empty before this file) — no foundation-surface conflicts to check against.

## Goal

No numeric coverage goal set for this campaign — plain backlog automation.

## Plan

```json
{
  "campaign": "approved-next50", "batch": "approved-next50", "base": "origin/automation/base",
  "heads": ["ELITEA-1920", "ELITEA-1811", "ELITEA-2181", "ELITEA-2021"],
  "extendCandidates": ["ELITEA-2028", "ELITEA-2014", "ELITEA-2021", "ELITEA-2218", "ELITEA-1999", "ELITEA-1920"],
  "foundation": null, "goal": null,
  "waves": [
    { "slug": "wave-01-heads", "caseIds": ["ELITEA-1920","ELITEA-1999","ELITEA-1811","ELITEA-1814","ELITEA-2181","ELITEA-2021"],
      "clusters": [["ELITEA-1920","ELITEA-1999"],["ELITEA-1811","ELITEA-1814"]] },
    { "slug": "wave-02-artifacts-upload-dup_pipe-hitl-node", "caseIds": ["ELITEA-1828","ELITEA-1829","ELITEA-1831","ELITEA-2014","ELITEA-2015"],
      "clusters": [["ELITEA-1828","ELITEA-1829","ELITEA-1831"],["ELITEA-2014","ELITEA-2015"]] },
    { "slug": "wave-03-artifacts-file-editor-core_pipe-node-config", "caseIds": ["ELITEA-1851","ELITEA-1852","ELITEA-1856","ELITEA-2004","ELITEA-2010"],
      "clusters": [["ELITEA-1851","ELITEA-1852","ELITEA-1856"],["ELITEA-2004","ELITEA-2010"]] },
    { "slug": "wave-04-artifacts-file-editor-formats_pipe-yaml_chat-search", "caseIds": ["ELITEA-1857","ELITEA-1858","ELITEA-1862","ELITEA-2028","ELITEA-2162"],
      "clusters": [["ELITEA-1857","ELITEA-1858","ELITEA-1862"]] },
    { "slug": "wave-05-chat-conversation-organization", "caseIds": ["ELITEA-2135","ELITEA-2137","ELITEA-2149","ELITEA-2168"],
      "clusters": [["ELITEA-2135","ELITEA-2137","ELITEA-2149"]] },
    { "slug": "wave-06-chat-attachments_slash-commands", "caseIds": ["ELITEA-2197","ELITEA-2200","ELITEA-2202","ELITEA-2203","ELITEA-2204"],
      "clusters": [["ELITEA-2197","ELITEA-2200"],["ELITEA-2202","ELITEA-2203","ELITEA-2204"]] },
    { "slug": "wave-07-chat-hitl-toolkit-direct", "caseIds": ["ELITEA-2211","ELITEA-2212","ELITEA-2213","ELITEA-2214","ELITEA-2215"],
      "clusters": [["ELITEA-2211","ELITEA-2212","ELITEA-2213","ELITEA-2214","ELITEA-2215"]] },
    { "slug": "wave-08-chat-context-agenthub-embedded-builders", "caseIds": ["ELITEA-2218","ELITEA-2075","ELITEA-2079","ELITEA-2085"],
      "clusters": [["ELITEA-2079","ELITEA-2085"]] },
    { "slug": "wave-09-chat-canvas-mode-editing", "caseIds": ["ELITEA-2086","ELITEA-2087","ELITEA-2088"],
      "clusters": [["ELITEA-2086","ELITEA-2087","ELITEA-2088"]] },
    { "slug": "wave-10-pipeline-entry-point-triggers", "caseIds": ["ELITEA-2005","ELITEA-2006","ELITEA-2007","ELITEA-2008"],
      "clusters": [["ELITEA-2005","ELITEA-2006","ELITEA-2007","ELITEA-2008"]] },
    { "slug": "wave-11-pipeline-canvas-graph-ops", "caseIds": ["ELITEA-2018","ELITEA-2030","ELITEA-2031","ELITEA-2032"],
      "clusters": [["ELITEA-2018","ELITEA-2030","ELITEA-2031","ELITEA-2032"]] }
  ],
  "policy": {}
}
```

Rationale (planner, verbatim summary): 4 surfaces (agents ×2, artifacts ×11, chat ×23, pipelines ×14), all
foundation-rich per `ls automation/pages/` + `ls automation/tests/ui/{agents,artifacts,chat,pipelines}/`
(chat_page.py 3818 lines, pipeline_detail_page.py 1778 lines, artifacts_page.py 2133 lines, etc.) → `foundation:
null`. No live campaign card claims these surfaces. 6 `extendCandidates` flagged (not pre-decided) against
existing suites (test_pipeline_advanced.py, test_pipeline_nodes.py, test_pipeline_management.py,
test_context_management.py, test_agent_build_with_ai.py/test_skill_build_with_ai.py) — genuine overlaps to
verify at analysis time, not assumed already-covered. No exact-ID AFS pre-exists for any of the 50. Same-surface
flow-variant clusters capped ≤5; genuinely distinct/complex cases (2162, 2168, 2181, 2218, 2075) left solo.
Heads = one representative per surface, seeded into wave 1 with their own small clusters (avoids fragmenting a
cluster's one analyst session across waves).

Verified count: 50/50 cases covered across the 11 waves, no duplicates, no omissions (checked programmatically).

## Log

- 2026-08-02 propose — conductor wf_aa16c5c4-f74 launched
- 2026-08-02 plan-proposed — 11 waves, foundation null, awaiting operator checkpoint
