# Memory index — qa-engineer

> Only *preventive* facts are indexed — things that change your FIRST move.
> Per-surface notes (testid maps, per-feature quirks) are NOT listed but ARE on disk:
> `grep -rl '<keyword>' .agents/memory/qa-engineer/`

- [Project briefing](project_briefing.md) — analyst + reviewer slots in Tal's pipeline
- [AFS claims: sweep the whole doc](afs_claims_need_full_sweep_and_grep.md) — no row is true until you grep it
- [Reviewer verifies, never trusts](reviewer_verifies_never_trusts.md) — re-run and re-derive claims; triage reds
- [A passing assertion may prove nothing](passing_assertion_may_prove_nothing.md) — can it fail in the broken case?
- [Locator review beyond the grep](locator_review_beyond_the_grep.md) — testid-clean still breaks POM; check the layer
- [extend-existing: classify + shape](extend_existing_classification_and_shape.md) — insert, sibling, or fresh spec?
- [Analyst has no commit authority](analyst_slot_has_no_git_commit_authority.md) — AFS untracked; testid commits OK
- [Can't self-approve a PR via gh](gh_identity_blocks_self_approval.md) — post the verdict via gh pr comment instead
- [EliteaUI commits need [EL-NNNN]](eliteaui_testid_commit_message_format.md) — commitlint rejects [ELITEA-NNNN]
- [Priority marker drift](priority_marker_drift_afs_vs_pytest_mark.md) — grep AFS Priority vs @pytest.mark.p*
- [Open cross-cutting defects](open_cross_cutting_defects.md) — #524, #694, bucket-fixture 404, #551/#585, #607
- [API seed project mismatch](api_pipeline_seed_project_mismatch.md) — standalone scripts can miss the browser's active project
