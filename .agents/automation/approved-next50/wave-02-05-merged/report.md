# Wave Report — wave-02-05-merged (campaign approved-next50)

**Base:** origin/automation/base · **Integration branch:** tests/batch-wave-02-05-merged

This wave merges the operator-requested consolidation of the original waves 2–5 (10 clusters,
39 cases) into one wave, run after wave-01 landed. Several units required multi-round recovery
after a mid-session interruption (see `.agents/memory/test-automation-lead/` — session memory —
for the full recovery narrative); all reached a terminal outcome before this report.

## Outcome: 33/39 automated (3 sanctioned RED), 6 blocked

| Case | Issue | Unit | Outcome |
|---|---|---|---|
| ELITEA-1851 | #259 | File Preview/Edit — open/verify editor UI cluster | automated, green |
| ELITEA-1852 | #218 | Same cluster — edit+save | automated, green |
| ELITEA-1856 | #263 | Same cluster — actions dropdown | automated, green |
| ELITEA-1857 | #234 | File Preview/Edit — markdown/image cluster | automated, green |
| ELITEA-1858 | #248 | Same cluster — markdown raw-tab edit | automated, green |
| ELITEA-1862 | #258 | Same cluster — image restricted controls | automated, green |
| ELITEA-2028 | #465 | Pipeline YAML-to-Flow sync (solo) | automated, green |
| ELITEA-2135 | #338 | Chat Move-to/Pin cluster — move to existing folder | automated, green |
| ELITEA-2137 | #340 | Same cluster — move to new folder | automated, green |
| ELITEA-2149 | #352 | Same cluster — pin conversation | automated, green |
| ELITEA-2162 | #365 | Chat search + modules panel (solo) | automated, green |
| ELITEA-2168 | #371 | Chat team-project mention/remove (solo) | **automated (sanctioned RED)** — known defect [#1119](https://github.com/EliteaAI/elitea-testing-public/issues/1119) |
| ELITEA-2197 | #400 | Chat attachments cluster — 10-file limit | automated, green |
| ELITEA-2200 | #403 | Same cluster — unsupported format error | **automated (sanctioned RED)** — known defect [#1121](https://github.com/EliteaAI/elitea-testing-public/issues/1121) |
| ELITEA-2202 | #405 | Chat slash-command cluster — empty state | automated, green |
| ELITEA-2203 | #406 | Same cluster — toolkit/MCP filtering | automated, green |
| ELITEA-2204 | #407 | Same cluster — tool selection | automated, green |
| ELITEA-2211 | #414 | Chat HITL sensitive-action cluster — card displays | **blocked** — [#1140](https://github.com/EliteaAI/elitea-testing-public/issues/1140) (missing `/admin` route) |
| ELITEA-2212 | #415 | Same cluster — authorize executes | **blocked** — #1140 |
| ELITEA-2213 | #416 | Same cluster — block prevents | **blocked** — #1140 |
| ELITEA-2214 | #417 | Same cluster — block with comment | **blocked** — #1140 |
| ELITEA-2215 | #418 | Same cluster — direct toolkit-call complete flow | **blocked** — #1140 (also non-deterministic per [#1127](https://github.com/EliteaAI/elitea-testing-public/issues/1127), excluded from gate) |
| ELITEA-2218 | #421 | Context auto-summarization (solo) | automated, green |
| ELITEA-2075 | #424 | Agent Hub participant read-only canvas (solo) | automated, green |
| ELITEA-2079 | #428 | Pipeline flow editor add-LLM-node cluster | **automated (sanctioned RED)** — known defect [#1039](https://github.com/EliteaAI/elitea-testing-public/issues/1039) |
| ELITEA-2085 | #434 | Same cluster — create MCP from conversation | automated, green |
| ELITEA-2086 | #435 | Chat canvas editing cluster — table display | automated, green |
| ELITEA-2087 | #436 | Same cluster — table cell edit+save | automated, green |
| ELITEA-2088 | #437 | Same cluster — Mermaid generate+edit | **blocked** — [#1142](https://github.com/EliteaAI/elitea-testing-public/issues/1142) (real instability: 3 distinct failure signatures across runs) |
| ELITEA-2004 | #441 | Pipeline node-config cluster — LLM node | automated, green |
| ELITEA-2010 | #447 | Same cluster — Toolkit node | automated, green |
| ELITEA-2005 | #442 | Pipeline entry-point trigger cluster — trigger types persist | automated, green |
| ELITEA-2006 | #443 | Same cluster — webhook modal | automated, green |
| ELITEA-2007 | #444 | Same cluster — schedule modal | automated, green (required a mid-gate flake fix — see Notable) |
| ELITEA-2008 | #445 | Same cluster — trigger restricted w/ HITL/Printer/Interrupt | automated, green |
| ELITEA-2018 | #455 | Pipeline canvas node/edge CRUD cluster — delete node | automated, green |
| ELITEA-2030 | #467 | Same cluster — add-node menu | automated, green |
| ELITEA-2031 | #468 | Same cluster — edge creation | automated, green |
| ELITEA-2032 | #469 | Same cluster — edge deletion | automated, green |

## Gate: GREEN

- **Green-required set, 29 UI spec files** (30 minus `test_generate_mermaid_diagram_and_edit_in_canvas.py`,
  excluded per ELITEA-2088's blocked disposition), run in 4 chunks of ~7-8 files:
  - Chunks 1–3: N=3 consecutive clean on first attempt.
  - Chunk 4: run 3 of its first N=3 attempt failed —
    `test_pipeline_schedule_trigger_settings_modal.py` (ELITEA-2007), an intermittent flake in the
    virtualized hour/minute cron-picker (JS-evaluate clicks with no post-toggle verification could
    silently miss, leaving the grid in a multi-value state that surfaced several steps later as
    `"Frequency cannot be less than every hour"`). A dispatched implementer root-caused it (no
    reproduction needed — found by code inspection) and added explicit post-toggle
    locator-count/attribute verification with one retry (commit `60b3d49b`). Re-gated **fresh N=3**
    on chunk 4 after the fix: clean 3/3.
- **Sanctioned-RED specs (3), each independently confirmed deterministic 3/3** by the lead, run
  together each time:
  - `test_attach_unsupported_file_format_error.py` (ELITEA-2200, defect #1121 — toast severity is
    `info` not `error`)
  - `test_team_users_mention_and_remove_participants.py` (ELITEA-2168, defect #1119)
  - `test_pipeline_flow_editor_add_llm_node_from_chat_canvas.py` (ELITEA-2079, defect #1039)
  - All three carry `expect.soft()` + a linked open-defect comment; identical failure signature
    all 3 runs, no other assertion affected.
- **Blast-radius regression sweep**: 85 files reachable from this wave's modified page objects
  (`agent_detail_page.py`, `artifacts_page.py`, `chat_page.py`, `mcp_form_page.py`,
  `pipeline_detail_page.py`, plus `conftest.py`/`data_fixtures.py`/`client.py`) not already covered
  by the gate above. Result: 175 passed, 19 failed, 7 errored, 7 skipped (github/jira-credential
  gated). **Every failure/error independently triaged as pre-existing/unrelated — zero regressions
  introduced by this wave:**
  - 7 errors: 3 guardrails (`Credential with ID 'guardrails_test_credential' already exists` —
    stale test-data collision, same pattern already confirmed pre-existing during
    `approved-top10`'s sweep), 4 HITL-authorization (ELITEA-2211–2214, already `blocked` on #1140).
  - 14 of 19 failures matched already-confirmed-pre-existing patterns from the wave-01 sweep, or
    are inline-cited known defects (#649 upload-defaults-to-subfolder,
    #655 cancel-doesn't-navigate-back, #1088 incomplete-fix-follow-up-already-posted,
    #1103 wave-01's own sanctioned-RED, #1142 this wave's own filed defect, #1127 already-excluded
    non-determinism).
  - 5 untriaged, freshly checked against unmodified `origin/automation/base`:
    - `test_agent_build_with_ai.py` (suggested-resources precondition) — reproduced identically
      on base.
    - `test_agent_management.py::TestAgentExecution` — reproduced identically on base (same
      garbled "CONFIRMED"-substring-vs-streaming-UI-text signature).
    - `test_agent_llm_selector_anthropic_models.py` — reproduced the identical signature on a
      2nd base run (1/2) — same flake family.
    - `test_agent_run_history_select_past_run.py` — didn't reproduce in 2 base runs, but carries
      the byte-identical garbled signature as the two confirmed cases above — same root cause
      (AI-response text read racing the streaming "Thought for..." UI), classified pre-existing
      by pattern match.
    - `test_import_agent_zip_nested_agent_dependencies.py` — a distinct failure class (name
      mismatch), no code-path overlap with this wave's one `agent_detail_page.py` change
      (`get_visible_model_option_names`, unrelated to import/zip). Passed clean 2/2 on base and
      1/1 re-run on the wave branch itself — one-off transient, cleared on recheck.

## Notable — recovery narrative

Six of sixteen units required a multi-round recovery after the original implementer/analyst
sessions were force-ended mid-task (StructuredOutput cutoffs / tooling timeouts) partway through
this large consolidated wave: ELITEA-2004+2010, ELITEA-2162, ELITEA-2211–2215, ELITEA-2086-2088,
ELITEA-2005-2008, ELITEA-2018/2030/2031/2032. Each was recovered from its committed-but-unmerged
branch state, taken through the missing review/fix rounds (1–4 rounds each), and merged. Two PR
review passes had been silently skipped by the interrupted workflow (ELITEA-2162 PR #1116,
ELITEA-2086-2088 PR #1133) — both caught and given a proper fresh-session review before merge.
PR #1138 (ELITEA-2018/2030/2031/2032) showed a false `CONFLICTING` mergeable state from GitHub;
a real `git merge` (not `merge-tree`) found the actual — and purely additive — conflict in
`pipeline_detail_page.py` and resolved it as a union of both branches' new class constants.

## Findings

- Defect [#1142](https://github.com/EliteaAI/elitea-testing-public/issues/1142) filed this wave —
  `test_generate_mermaid_diagram_and_edit_in_canvas.py` (ELITEA-2088) showed 3 distinct failure
  signatures across ~5 runs (dagre NaN transform, a re-render race, "Maximum update depth
  exceeded") — real product instability, not a chain of independent test bugs. Case classified
  `blocked`, spec excluded from the gate.
- Defects #1119, #1121, #1039 — already open, consumed as this wave's 3 sanctioned-REDs.
- Defect #1140 (missing `/admin` route) — blocks ELITEA-2211 through 2215; code for all 5 is
  merged and correct, just can't execute past the missing route.
- Defect #1127 — ELITEA-2215's own case additionally carries non-deterministic behavior in the
  direct-toolkit-call flow; excluded from the gate independent of the #1140 block.
- Governance note (ELITEA-2005-2008 recovery): one commit on the recovery branch was made with
  `--no-verify` under a forced session cutoff. Investigated: this repo has no git hooks
  configured, so it was a no-op, not an actual bypass — but 6 pre-existing ruff violations found
  during that check were fixed anyway.

## Next

Land this wave (PR to `automation/base`), back-write TMS for the 33 automated cases, closure
records for all 39 issues (33 → Ready, 6 → Blocked with "Waiting on #N"), rebuild
`onetest-ai-tm-Elitea`'s `index.json`, clean up 16 unit branches + the trunk. This closes out the
`approved-next50` campaign (11 + 39 = 50/50 cases reaching a terminal outcome).
