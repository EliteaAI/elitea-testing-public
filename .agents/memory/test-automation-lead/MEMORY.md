# Memory index — test-automation-lead

> Only *preventive* facts are indexed — things that change your FIRST move.
> Everything else stays on disk and stays greppable — always grep before
> concluding something is unknown:
> `grep -rl '<keyword>' .agents/memory/test-automation-lead/`
> Compacted by scout 2026-08-10 (51 → 26 lines): merged 8 near-duplicate clusters
> into their richest survivor, demoted surface lookups to disk-only, cut 2 lines
> whose claims are now contradicted by the code. No entry file was deleted.

- [Project briefing](project_briefing.md) — stack, pipeline, systems map, PR + merge policy
- [Shared-tree git discipline](shared_tree_git_discipline.md) — one tree, many sessions; destructive git eats memory; worktrees stay banned
- [Closure-record discipline](closure_record_discipline.md) — table shape, clickable SHAs, pasted gate + promotability
- [Promotability = the call chain](promotability_dependency_set.md) — derive deps from code at check time, never the AFS
- [Testid presence greps](testid_presence_grep_technique.md) — bare string, always -i, [:=] not =; component-scope reused names
- [Evidence, not narration](evidence_must_be_pasted_artifact.md) — verify every claim against a retrievable artifact
- [Merge-gate traps](merge_gate_operational_traps.md) — flake resets count, stale gh diff, per-step allure, sanctioned-RED sets
- [Manual gate file discovery](manual_gate_must_discover_touched_files_via_diff_not_memory.md) — `git diff --name-only` the trunk, never reconstruct touched files from memory of unit summaries
- [Unattended run guards](unattended_run_guards.md) — liveness by ps + path overlap beats the 3 literal conditions
- [Dispatch prompt completeness](dispatch_prompt_completeness.md) — what every dispatch carries; verify the premise first
- [Waiting & resuming](subagent_wait_and_resume_mechanics.md) — poll in-turn; Workflow needs scriptPath AND args, every resume
- [TMS back-write discipline](tms_backwrite_discipline.md) — hand-edit all 4 fields; onetest MCP verbs take NO repo: arg; never pass --dir
- [TMS intake technique](tms_intake_technique.md) — filename-id dedup, uniq -d collision sweep, capture issue# at intake
- [gh tracker & board gotchas](gh_tracker_and_board_gotchas.md) — pagination, -F vs -f, Closes #N, --squash, retry the read
- [Review-round rulings](review_round_rulings.md) — full re-check each round; verdict recorded; R2 cap by signature
- [Testid-usage extraction scope](testid_usage_scope.md) — grep all of automation/; trace the test's own call chain
- [AFS gate rulings](afs_gate_rulings.md) — the AFS itself can be wrong: locators, provenance, status header
- [No-edit guardrail is repo-agnostic](no_edit_guardrail_repo_agnostic.md) — 6× violated; ANY merge's conflicts are dispatched, always
- [Workflow outcomes aren't ground truth](gate_red_at_1_run_lead_confirms_sanctioned_red_before_landing.md) — gh pr view + git log every unit (8×)
- [Gate stalls: 4 shapes, 4 recoveries](workflow_gate_hard_failure_vs_soft_stall_different_recovery.md) — hard-fail resumes; not-run you run (7×)
- [Landing is manual](batch_workflow_never_opens_trunk_to_base_pr.md) — push local refs, open trunk→base PR, verify report.json landed (12×)
- [CORRECT report.json after your own gate](report_writer_agent_can_refuse_disk_write.md) — a lead-run gate must be written back; audits read this file
- [Gate scope = node-ids, not files](large_batch_gate_scope_by_nodeid_not_file.md) — file scope sweeps in pre-existing flaky siblings
- [Blast-radius red doesn't block](blast_radius_red_does_not_block_gate_verdict.md) — trust gate.verdict; file the reds as their own issue
- [Gate red moving between tests](gate_red_recurring_on_different_tests_check_tracker_before_diagnosing.md) — same signature = shared cause, grep tracker
- [Unshallow siblings before every sync](sibling_clones_can_go_shallow_check_before_sync.md) — shallow clones lie about ahead/behind
- [--collect-only prints a tree, not node-ids](pytest_collect_only_renders_tree_not_flat_ids.md) — derive ids from source; zsh won't split $VAR
- [Montserrat font 404 is known-noisy](known_noisy_resource_montserrat_font_404.md) — app-wide CDN flake; caught 4× only by lead's own gate; filter idiom exists
- [Cherry-pick clean units off a broken trunk](cherry_pick_clean_units_off_broken_trunk.md) — one bad unit doesn't sink the whole batch; land the rest alone
- [2 Workflow hard-fails on one batch = switch to direct dispatch](workflow_combined_route_unreliable_switch_to_direct_dispatch.md) — combined-route + retry clusters unreliable
- ["blocked"+StructuredOutput note = near-certain false report](report_case_outcome_can_falsely_say_blocked_for_an_already_merged_case.md) — verify git, expect it actually merged (2×)
- [NEVER call build_index for a routine back-write](build_index_regression_must_be_reverted_not_carried.md) — colliding ids make it destructive; surgical-edit by `path` (2×)
- [Gate/report tail fails 2× = run gate yourself](workflow_internal_gate_two_failures_run_it_yourself.md) — scope by node-id, hand-write report from `result`
