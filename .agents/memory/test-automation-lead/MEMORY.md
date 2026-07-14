# Memory index — test-automation-lead

- [Project briefing](project_briefing.md) — Stack overlay (test-automation) — orchestration starting context for Tal
- [Live-run gate is pre-merge, not post](live_run_gate_is_pre_merge_not_post.md) — the orchestrator's independent N=3 live-run gate must run before `gh pr merge`, never after; reviewer APPROVED (even with its own independent run) is not a substitute
- [Isolated defect: red is expected](isolated_defect_red_is_expected.md)
- [Merge gate: gh pr diff staleness check](merge_gate_gh_pr_diff_staleness.md)
- [Resuming subagents for narrow fixups](resuming_subagents_for_narrow_fixups.md)
- [Shared-caller enumeration gap](shared_caller_enumeration_gap.md)
- [Interrupted dispatch recovery](interrupted_dispatch_recovery.md) — after an interrupted turn, check git/PR/branch state before re-dispatching — the subagent may have already completed and landed real work
- [Mechanical grep gate coverage](mechanical_grep_gate_coverage.md) — a self-check grep alternation must cover every clause of the policy being enforced (lexical AND structural), not just the clause the task started from
- [Bulk TMS intake technique](bulk_tms_intake_technique.md) — recursive git-trees pull, dedup-by-title-substring, contradiction clustering, python env-unset gotcha, and board Done read-back verification for large backlog-intake runs
- [Control dispatch premise can be stale](control_dispatch_premise_can_be_stale.md) — verify board status/PR/closure-record directly before scoring a control-audit checklist; if nothing was delivered, use a distinct not-ready verdict, not FAIL
- [Promotability grep false negative](promotability_grep_false_negative.md) — grep the bare testid value first, not a `data-testid="..."` attribute-string pattern — object-literal props and conditional JSX expressions won't match the literal form
- [Implementer stalls on background wait](implementer_stalls_on_background_wait.md) — after 2 stalls on the same run-and-wait step, stop re-dispatching full scope; verify + run the test yourself, hand back a minimal commit/PR-only task
