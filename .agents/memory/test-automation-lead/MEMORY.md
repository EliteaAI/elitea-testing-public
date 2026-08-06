# Memory index — test-automation-lead

> Only *preventive* facts are indexed — things that change your FIRST move.
> Surface- and case-specific entries are NOT listed but ARE on disk:
> `grep -rl '<keyword>' .agents/memory/test-automation-lead/`

- [Project briefing](project_briefing.md) — stack, pipeline, systems map, PR + merge policy
- [Shared-tree git discipline](shared_tree_git_discipline.md) — one tree, many sessions; destructive git eats memory
- [Closure-record discipline](closure_record_discipline.md) — table shape, clickable SHAs, pasted gate + promotability
- [Promotability: which testids](promotability_dependency_set.md) — derive deps from the call chain, not the AFS
- [Testid presence greps](testid_presence_grep_technique.md) — bare-string first; prop/template/dynamic testids lie
- [Evidence, not narration](evidence_must_be_pasted_artifact.md) — verify claims against retrievable artifacts
- [Merge-gate traps](merge_gate_operational_traps.md) — flake resets count, stale gh diff, per-step allure check
- [Unattended run guards](unattended_run_guards.md) — liveness by ps + path overlap beats the 3 literal conditions
- [Dispatch prompt completeness](dispatch_prompt_completeness.md) — what every dispatch carries; stale premises
- [Subagent wait & resume](subagent_wait_and_resume_mechanics.md) — background resumes, orphaned waits, polling
- [TMS back-write discipline](tms_backwrite_discipline.md) — no MCP write verb; hand-edit, recheck all 4 fields
- [TMS intake technique](tms_intake_technique.md) — filename-id dedup, tree API, sequential filing, cap unenforced
- [gh tracker & board gotchas](gh_tracker_and_board_gotchas.md) — pagination, -F vs -f, full+json, Closes #N, --squash
- [Review-round rulings](review_round_rulings.md) — full re-check each round; verdict recorded; R2 cap by class
- [Testid-usage extraction scope](testid_usage_scope.md) — grep all of automation/; trace the test's own call chain
- [AFS gate rulings](afs_gate_rulings.md) — the AFS itself can be wrong: locators, provenance, status header
- [No-edit guardrail is repo-agnostic](no_edit_guardrail_repo_agnostic.md) — 3× violated; conflicts are dispatched
- [#524 blocks ALL agent creation](blocker_524_blocks_all_agent_creation.md) — still OPEN; kills the agent_id fixture
- [Isolated-defect assert can ship GREEN](isolated_defect_can_ship_green.md) — verify its logic by hand, not colour
- [EL-5708 broke indexes_tab](indexes_tab_removed_by_el5708_toolkit_detail_page_stale.md) — count_config_tabs fails
- [Workflow gate stall = false blocked](workflow_gate_stall_gives_false_blocked_lead_runs_gate_directly.md) — check journal.jsonl, run gate yourself
- [Long gate Bash calls get infra-killed](long_running_gate_bash_calls_get_infra_killed.md) — retry on 0 FAILED, don't diagnose red
- [Case→issue mapping isn't in the snapshot](tms_case_to_issue_mapping_not_in_snapshot.md) — capture at intake; strict `[Automate][ELITEA-<id>]` match, not bare-ID
- [Testid provenance: bulk not per-case](testid_provenance_bulk_check_for_multi_case_closure.md) — one dump+diff for the whole wave; `+`-lines only
- [Workflow tool: use scriptPath, not workflow('name',...)](workflow_tool_named_registry_is_empty_use_scriptpath.md) — named registry is empty; wrapper-script call fails silently-fast
- [build_index MCP verb can silently no-op](build_index_mcp_verb_can_silently_no_op.md) — omit `repo:` arg entirely; it misroutes to ~/.onetest-workspaces
- [batch-build never opens trunk→base PR](batch_workflow_never_opens_trunk_to_base_pr.md) — lead always `gh pr create`+merge it by hand, every batch
- [Workflow new-ground blocker needs blocking_detail too](workflow_new_ground_blocker_needs_blocking_detail_too.md) — `blocked` may be a loop-control gap, not unfixable — read the finding first
- [Workflow R2 cap is total, not per-cause](batch_workflow_r2_counter_is_total_not_per_cause.md) — verify per-cause via the implementer's own notes + `gh pr view` before accepting an "R2 cap exceeded" park
- [TMS ids CAN collide across modules](onetest_case_id_can_collide_across_modules.md) — SYSTEMIC (150+ ids); run `grep -h '^id: ELITEA-' -r tests/ | sort | uniq -d` every intake
- [Report outcome "blocked" can still mean LAND IT](batch_report_case_outcome_blocked_can_still_mean_land_it.md) — check `gate.verdict`+`next` before parking a sanctioned-RED case
- [Gate red at runs=1 — confirm before parking](gate_red_at_1_run_lead_confirms_sanctioned_red_before_landing.md) — internal gate honestly stops at 1 red; run your own N=3 before classifying
- [Workflow status:failed ≠ work lost](workflow_hard_failure_can_still_have_landed_real_work.md) — check git+journal.jsonl, then just resume; don't redo
- [gh project rate-limit hits the READ, not the mutation](gh_project_rate_limit_on_verification_read_not_the_mutation.md) — item-edit likely already succeeded; retry the verify read, don't redo the edit
- [Workflow resume needs args too](workflow_resume_requires_args_too.md) — `{scriptPath, resumeFromRunId}` alone throws "args required"; always resend the same `args`
