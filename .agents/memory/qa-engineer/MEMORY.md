# Memory index — qa-engineer

> Only *preventive* facts are indexed — things that change your FIRST move.
> Per-surface notes (testid maps, per-feature quirks, one-off case findings) are
> NOT listed but ARE on disk — always grep before concluding something is unknown:
> `grep -rl '<keyword>' .agents/memory/qa-engineer/`
> Compacted by scout 2026-08-10 (41 → 26 lines): merged near-duplicates, demoted
> surface lookups to disk-only, promoted 5 preventive entries. Nothing was deleted.

- [Project briefing](project_briefing.md) — analyst + reviewer slots; testid-only HARD OVERRIDE; localhost = automation/testids
- [AFS claims need a full sweep](afs_claims_need_full_sweep_and_grep.md) — no row/clause/PROVENANCE cell is true till you grep it
- [Reviewer verifies, never trusts](reviewer_verifies_never_trusts.md) — re-run live; re-run their pasted greps; triage reds
- [A passing assertion may prove nothing](passing_assertion_may_prove_nothing.md) — would it differ in the broken case? 12 shapes
- [Locator review beyond the grep](locator_review_beyond_the_grep.md) — identity, construction site, LocatorDescriptor, JS payloads
- [extend-existing: classify + shape](extend_existing_classification_and_shape.md) — already-covered is board-first; 3 shapes
- [Analyst commit authority](analyst_slot_has_no_git_commit_authority.md) — batch trunk: commit the AFS; standalone: leave untracked
- [Can't self-approve a PR via gh](gh_identity_blocks_self_approval.md) — post the verdict via gh pr comment instead
- [EliteaUI commits need [EL-NNNN]](eliteaui_testid_commit_message_format.md) — commitlint rejects [ELITEA-NNNN]
- [Priority marker drift](priority_marker_drift_afs_vs_pytest_mark.md) — grep AFS Priority vs @pytest.mark.p*; seen 7×, incl. module-level
- [Open cross-cutting defects](open_cross_cutting_defects.md) — #694, bucket-fixture 404, #551/#585, #607 (re-verify before acting)
- [Provenance grep lies](provenance_grep_needs_case_insensitive.md) — needs -i; object-literal testId: still fails; live ≠ on-main
- [Closed/unlabelled ≠ absent](mui_menu_unmounted_when_closed_false_negative.md) — open overflows before counting; snapshot isn't evidence
- [MUI icon auto-testid is dev-only](mui_icons_material_auto_testid_on_icon_svg.md) — stripped in prod builds; NOT a locator, ever
- [No non-admin test user exists](no_non_admin_test_user_credential_exists.md) — RBAC cases need a flagged gap, not a role hunt
- [Pipeline says Completed but nothing ran](code_node_needs_dict_literal_return_not_assignment.md) — 5 silent no-op triggers
- [Known-defect soft-assert polarity](known_defect_soft_assert_polarity_must_encode_correct_behavior.md) — must fire on the BUG
- [Clipboard read hangs w/o permission](clipboard_read_hangs_without_permission_grant.md) — 1800s MCP hang, not a product bug
- [InputBase autoBlur breaks Control+a](input_autoblur_breaks_control_a_select_all.md) — clear via Home+Shift+End instead
- [Stale case families](settings_analytics_case_family_stale_six_count.md) — analytics + Agent Hub text predates the product; cite, don't re-file
- [#579 claims need a source check](579_claim_check_component_already_forwards_testid_prop.md) — does the component already forward testId?
- [TMS gate: draft is normal](markdown_tms_case_gate_status_draft_vs_ready.md) — draft = automate it; ready+automated+id = already-covered
- [Sanctioned-RED needs ONE signature](sanctioned_red_requires_single_failure_signature.md) — two failure paths = flaky, blocks even if both filed
- [Missing control = defect, not clarification](case_describes_nonexistent_control_is_defect_not_clarification.md) — don't stretch reverse-masking
- [browser_click target = CSS selector, not ref/text](playwright_mcp_snapshot_refs_go_stale_fast_on_pipeline_canvas.md) — any page, use `[data-testid=...]`
- [Corrective testid commits leave orphans](corrective_testid_commit_can_leave_wrong_call_site_wired.md) — grep automation/testids, not the narrative
- [MUI Tooltip title is app-owned](mui_tooltip_title_content_is_app_owned_testid_able.md) — not #579; testid the JSX directly
- [Dead-code guard's "class scoping" still false-passes](dead_code_guard_class_name_substring_scoping_still_false_passes.md) — verify via a live collision, don't trust the scoping code
- [Recovered-branch PRs can wipe daily logs](pr_branch_recovery_can_silently_wipe_other_units_daily_log.md) — diff line counts vs base, not just content
- [UI/flow assumption gate](ui_flow_assumption_gate.md) — test fails, assume UI changed? Verify vs case text first, wait if unconfirmed
- [Tests own their preconditions](test_owns_its_own_preconditions.md) — borrowed pre-existing data = green when dirty, red when clean
- [CI login failure becomes SKIP](ci_login_failure_becomes_skip.md) — a green dev-stable job can mean the test never ran; grep the log
