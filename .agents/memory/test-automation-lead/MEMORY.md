# Memory index — test-automation-lead

- [Project briefing](project_briefing.md) — Stack overlay (test-automation) — orchestration starting context for Tal
- [Live-run gate is pre-merge, not post](live_run_gate_is_pre_merge_not_post.md) — the orchestrator's independent N=3 live-run gate must run before `gh pr merge`, never after; reviewer APPROVED (even with its own independent run) is not a substitute
- [Isolated defect: red is expected](isolated_defect_red_is_expected.md)
- [Merge gate: gh pr diff staleness check](merge_gate_gh_pr_diff_staleness.md)
- [Resuming subagents for narrow fixups](resuming_subagents_for_narrow_fixups.md)
- [Shared-caller enumeration gap](shared_caller_enumeration_gap.md)
- [Interrupted dispatch recovery](interrupted_dispatch_recovery.md) — after an interrupted turn, check git/PR/branch state before re-dispatching — the subagent may have already completed and landed real work
- [Mechanical grep gate coverage](mechanical_grep_gate_coverage.md) — a self-check grep alternation must cover every clause of the policy being enforced (lexical AND structural), not just the clause the task started from
