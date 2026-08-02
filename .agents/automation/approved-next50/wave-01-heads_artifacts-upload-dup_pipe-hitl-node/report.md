# Wave Report — wave-01-heads_artifacts-upload-dup_pipe-hitl-node (campaign approved-next50)

**Base:** origin/automation/base · **Integration branch:** tests/batch-wave-01-heads_artifacts-upload-dup_pipe-hitl-node

## Outcome: 11/11 automated

| Case | Issue | Unit | Outcome |
|---|---|---|---|
| ELITEA-1920 | #188 | Build-with-AI (chat canvas + skill) cluster | automated, green |
| ELITEA-1999 | #191 | Build-with-AI cluster | automated, green |
| ELITEA-1811 | #229 | Bucket-name validation cluster | automated, green |
| ELITEA-1814 | #210 | Bucket-name validation cluster | automated, green |
| ELITEA-2021 | #458 | Pipeline full-details persist (head) | automated, green |
| ELITEA-1828 | #217 | Artifacts duplicate-resolution cluster | automated, green |
| ELITEA-1829 | #267 | Artifacts duplicate-resolution cluster | automated, green |
| ELITEA-1831 | #220 | Artifacts duplicate-resolution cluster | automated, green |
| ELITEA-2014 | #451 | Pipeline HITL node cluster | automated, green |
| ELITEA-2015 | #452 | Pipeline HITL node cluster | **automated (sanctioned RED)** — known defect #1103 |
| ELITEA-2181 | #384 | Chat streaming response (head) | automated, green — required a full recovery + 3 review rounds |

## Gate: GREEN

The workflow's internal gate stalled the same way as `approved-top10`'s did (slow `git fetch` over the
OneDrive-hosted repo, returned not-run/0 runs) — the lead ran the real gate directly per `testing.md`.

- **N=3 consecutive green**, 9 UI specs together:
  - run 1: 12/13 passed within scope (the 13th being the sanctioned-red spec, excluded from the green
    requirement) — 491.0s
  - run 2: 12 passed — 430.7s
  - run 3: 12 passed — 452.4s
- **Sanctioned-RED spec** (`test_pipeline_hitl_node_runtime_behavior.py`, ELITEA-2015, known defect
  [#1103](https://github.com/EliteaAI/elitea-testing-public/issues/1103) — HITL node resume does not follow
  configured router mapping): deterministic, 3/3 identical failure signature (once within run 1, twice more
  standalone).
- **Blast-radius regression sweep**: 64 files reachable from the wave's 6 modified page objects
  (agent_detail_page.py, artifacts_page.py, chat_page.py, generate_agent_modal_page.py,
  pipeline_detail_page.py, pipeline_form_page.py), run in full. 9 distinct failures encountered — **every one
  independently confirmed pre-existing and unrelated**: 5 reproduce identically on unmodified
  `origin/automation/base` (test_artifacts_create_bucket_55char_name_and_delete.py,
  test_create_agent_via_chat_canvas.py, test_toolkit_creation_cancel_no_toolkit_no_bucket.py — checked fresh
  this session), 6 match patterns already confirmed pre-existing during the `approved-top10` regression sweep
  (test_agent_publish_unpublish_version.py, test_fork_agent_to_different_project.py,
  test_ghost_skill_after_agent_removed.py, test_skill_conversation_interaction.py,
  test_toolkit_parameterized.py[bitbucket]/[confluence]), and one — `test_toolkit_creation_create_bucket_verify_list_files.py`
  (ELITEA-1866/#1088) — is a known pre-existing red whose presumed fix (EliteaUI@a467c0ac, landed in
  `approved-top10`) turned out NOT to fully resolve it; follow-up comment posted on #1088. Zero regressions
  introduced by this wave.

## Notable — ELITEA-2181 recovery

The original implementer session was force-ended mid-verification by a tooling timeout while a legitimately
slow (34-54s) live test was still running. AFS, testids (pushed to EliteaUI `automation/testids`,
`0e2ca07f`), and the test file survived (recovered from a gate-agent stash); the `chat_page.py` page-object
additions did not survive a tree checkout and were recreated from the AFS's own detailed notes, verified
live against localhost:5173. Went through 3 review rounds: round 1 caught a weakened regression-guard
assertion with a false AFS-amendment claim; round 2's fix (presence-gated containment check) was itself
found to rest on a misread of the EliteaUI source; round 3's fix (plain unconditional containment, matching
the AFS's literal spec) was independently re-verified against source by 3 separate reviewer/implementer
passes and approved. Merged as PR #1106.

## Findings

- Defect [#1103](https://github.com/EliteaAI/elitea-testing-public/issues/1103) (HITL node resume routing) —
  already filed during analysis, consumed as this wave's sanctioned-RED.
- Follow-up posted on [#1088](https://github.com/EliteaAI/elitea-testing-public/issues/1088) — the EliteaUI
  fix from `approved-top10` doesn't fully resolve `test_toolkit_creation_create_bucket_verify_list_files.py`;
  needs a human/implementer look at whether the Artifact-toolkit Test Settings panel takes a different
  `LLMModelSelector` render path than the one the earlier fix targeted.

## Next

Land this wave (PR to `automation/base`), back-write TMS for all 11 cases, closure records, board moves to
Ready, then proceed to the next (consolidated) wave per the operator's request to merge waves 2-5 into one.
