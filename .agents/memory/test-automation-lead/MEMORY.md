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
- [build_index MCP verb can silently no-op](build_index_mcp_verb_can_silently_no_op.md) — check index.json mtime, don't trust the success message
