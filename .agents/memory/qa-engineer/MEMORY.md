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
- [Analyst commit authority](analyst_slot_has_no_git_commit_authority.md) — batch dispatch: commit AFS on trunk; standalone: leave untracked
- [Can't self-approve a PR via gh](gh_identity_blocks_self_approval.md) — post the verdict via gh pr comment instead
- [EliteaUI commits need [EL-NNNN]](eliteaui_testid_commit_message_format.md) — commitlint rejects [ELITEA-NNNN]
- [Priority marker drift](priority_marker_drift_afs_vs_pytest_mark.md) — grep AFS Priority vs @pytest.mark.p*
- [Open cross-cutting defects](open_cross_cutting_defects.md) — #524, #694, bucket-fixture 404, #551/#585, #607
- [API seed project mismatch](api_pipeline_seed_project_mismatch.md) — standalone scripts can miss the browser's active project
- [Pipeline STATE panel traps](pipeline_state_panel_ambiguous_add_button_and_name_input_collision.md) — role name "Context" ambiguous; input[name="name"] hits pipeline Name field
- [Clipboard read hangs w/o permission](clipboard_read_hangs_without_permission_grant.md) — grant clipboard-read at context creation or readText() hangs forever
- [InputBase autoBlur breaks Control+a](input_autoblur_breaks_control_a_select_all.md) — clear via Home+Shift+End instead
- [settings-analytics: stale "six" counts](settings_analytics_case_family_stale_six_count.md) — live has 7 tabs/8 KPIs, not 6; clarification not defect
- [MUI v7 TablePagination testids](mui_tablepagination_v7_testid_slotprops.md) — use slotProps.{select,displayedRows,actions.*Button}, not deprecated props
- [Recharts tooltip testid](recharts_hover_tooltip_testid_pattern.md) — thread via content={p=>...}; hover w/ real mouse.move, not page.evaluate
- [Agent Hub family naming drift](agent_hub_family_agent_hub_vs_catalog_naming_drift.md) — "Agent HUB" case text vs live "Catalog"; cite #1208, don't re-file
- [MUI icon auto-testid is dev-only](mui_icons_material_auto_testid_on_icon_svg.md) — `createSvgIcon` strips it in prod builds; NOT a safe locator, ever
- [Provenance grep false negatives](provenance_grep_needs_case_insensitive.md) — needs -i; object-literal `testId:` (colon) still fails filter, eyeball raw grep
- [AI Providers tier selectors](ai_providers_tier_selectors_no_clear_and_no_chat_parity.md) — no unset in UI, only Default feeds chat model
- [structured_output+messages+dict/list crash](structured_output_messages_dict_list_crash.md) — #1274; never combine in one node's output
