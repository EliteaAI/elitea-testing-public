# Batch Report — approved-top10

**Batch:** approved-top10 · **Base:** origin/automation/base · **Integration branch:** tests/batch-approved-top10
**Source:** board #9, Approved column, first 10 cards in board order

## Outcome: 10/10 automated

| Case | Issue | Unit | Outcome | Notes |
|---|---|---|---|---|
| ELITEA-1934 | #84 | mcp cluster | automated | Green. Findings #1086, #1087, #1088 filed. |
| ELITEA-1937 | #149 | mcp cluster | automated | Green. Same PR/findings as ELITEA-1934. |
| ELITEA-1976 | #106 | credentials cluster | automated | Green. |
| ELITEA-1978 | #112 | credentials cluster | **automated (sanctioned RED)** | Known defect #1004, deterministic 4/4, expect.soft(). |
| ELITEA-1979 | #176 | credentials cluster | automated | Green after stabilize round (timing flake fix, commit 71089500). |
| ELITEA-1890 | #172 | agent-version cluster | automated | Green. Finding #1091 filed. |
| ELITEA-1891 | #173 | agent-version cluster | automated | Green. Same PR/findings as ELITEA-1890. |
| ELITEA-1877 | #107 | single | automated | Green. Finding #1093 filed. |
| ELITEA-1880 | #161 | single | automated | Green. |
| ELITEA-1993 | #170 | single | automated | Green. |

## Gate: GREEN

- **N=3 consecutive green**, 9 UI specs together (run by the lead directly, per testing.md — the workflow's
  internal gate agent stalled on a slow `git fetch` over the OneDrive-hosted repo and returned not-run):
  - run 1: 14 passed (375.9s)
  - run 2: 14 passed (385.1s) — first attempt infra-killed mid-run at 10/14 clean, no failures, retried
  - run 3: 14 passed (391.9s)
- **Sanctioned-RED spec** (ELITEA-1978, known defect #1004): re-confirmed independently by the lead, 1/1,
  identical signature to the 3/3 already established during stabilize diagnosis.
- **New unit-test regression coverage** (from the stabilize fix): 4/4 passed.
- **Blast-radius regression sweep**: one full run across 42 files reachable from the batch's 6 modified page
  objects (agent_detail_page.py, credential_create_page.py, generate_skill_modal_page.py, mcp_form_page.py,
  toolkit_detail_page.py, toolkit_test_settings_page.py). 10 failures encountered; **all 10 independently
  reproduced identically on unmodified origin/automation/base** — zero regressions introduced by this batch:
  - test_guardrails_live_reload.py (×3 tests) — pre-existing red on base
  - test_agent_publish_unpublish_version.py — pre-existing sanctioned-red (its own known defect)
  - test_fork_agent_to_different_project.py — pre-existing sanctioned-red (its own known defect)
  - test_ghost_skill_after_agent_removed.py — pre-existing timeout/flake on base
  - test_skill_conversation_interaction.py — pre-existing timeout/flake on base
  - test_credential_search_by_name.py — pre-existing soft-assert failures on base
  - test_toolkit_creation_create_bucket_verify_list_files.py — pre-existing #1866 (already AFS-flagged by this batch)
  - test_toolkit_parameterized.py[bitbucket], [confluence] — pre-existing on base
  - test_agent_management.py::TestAgentExecution::test_agent_executes_with_name_description_instructions_only —
    one-off transient (failed once mid-sweep, passed clean in isolation on both base and trunk)

## Findings routed

- **New defects/clarifications filed during the batch** (already on the tracker, no re-filing needed):
  #1086, #1087 (clarifications, ELITEA-1937 case-text drift), #1088 (defect, LLMModelSelector testid gap —
  **fixed in this batch** via EliteaAI/EliteaUI@a467c0ac), #1091 (clarification, ELITEA-1891 version-ordering
  case-text drift), #1093 (minor defect, Run History has no close control).
- **Housekeeping**: `origin/automation/base-merged` is an orphaned local branch (last commit 2026-07-24) holding
  a prior, never-merged implementation of ELITEA-1976/1978. Superseded by this batch's fresh implementation on
  `tests/1976-1978-1979-credential-dropdown-flows`. Recommend a human deletes the stale branch.
- **Minor doc-completeness gaps** (non-blocking, logged to memory, not tracker items): a few AFS Coverage Map
  cells cite superseded code samples instead of the final compliant implementation; one dead LocatorDescriptor
  field (`RUN_HISTORY_LIST_ITEM_SELECTED_SELECTOR`); a `bare except Exception` in `is_reasoning_slider_visible`.

## Testid provenance (verified fresh, `git fetch origin` + `git grep` against both refs)

All new testids this batch's diff references, on `origin/automation/testids` — **none yet on `origin/main`**
except `pipeline-history-tab` and `toast-message`, which are pre-existing/reused:

| Testid | main | testids |
|---|---|---|
| agent-set-default-version-confirm-button | no | ✅ |
| credential-form-api-error-message | no | ✅ |
| credential-select-mismatch-footer | no | ✅ |
| credential-select-refresh-button | no | ✅ |
| generate-skill-review-name-helper-text | no | ✅ |
| model-settings-button | no | ✅ |
| model-settings-cancel-button | no | ✅ |
| model-settings-dialog | no | ✅ |
| model-settings-max-tokens-section | no | ✅ |
| model-settings-reasoning-slider | no | ✅ |
| pipeline-history-tab | ✅ (pre-existing) | ✅ |
| run-history-list-item | no | ✅ |
| select-group-header-{} | no | ✅ |
| set-as-a-default-menuitem | n/a (dynamic, `testId: item.key` in DotMenu.jsx — pre-existing mechanism, not a new addition) | ✅ (inherent) |
| toast-message | ✅ (pre-existing) | ✅ |
| toolkit-connection-status | no | ✅ |
| toolkit-credential-select-{}-combobox | no | ✅ |
| toolkit-test-param-{}-input | no | ✅ |
| version-option-pin-icon | no | ✅ |

**Status:** all pushed to `automation/testids` (dev server serves them) — ⚠️ NOT yet on `main` (awaiting human
cherry-pick) → not deployable-env-promotable yet, per-case Testids row in each closure record has exact SHAs.

## Next

Lead: open + merge the trunk PR, back-write TMS, post closure records, move board cards to Ready, post backlink
comments on the already-filed issues, flag the orphaned branch, run cleanup.mjs.
