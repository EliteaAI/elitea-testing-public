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
- [MUI Menu unmounted-when-closed](mui_menu_unmounted_when_closed_false_negative.md) — open overflow menus before counting "how many"
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
- [Known-defect soft-assert polarity](known_defect_soft_assert_polarity_must_encode_correct_behavior.md) — condition must fire on the BUG, not on its fix, or it's a hidden green
- [Mechanical grep misses JS-string raw selectors](mechanical_grep_misses_js_string_raw_selectors.md) — grep `wait_for_function`/`evaluate` JS payloads separately for `data-testid=`
- [Empty-title Tooltip breaks a11y snapshot](folder_confirm_button_state_absent_from_ax_snapshot.md) — `title={cond?'':text}` elements vanish/mislabel in browser_snapshot; testid-only is load-bearing, not just policy
- [No non-admin test-user exists](no_non_admin_test_user_credential_exists.md) — TEST_USER is admin everywhere; RBAC cases need a flagged gap, not a role hunt
- [Console-check window gap](console_assertion_window_gap.md) — assert must be LAST or later steps go unchecked
- [#579 claim needs source check](579_claim_check_component_already_forwards_testid_prop.md) — verify component doesn't already forward a testId prop before accepting "library-internal"
- [DotMenu click already closes menu](dot_menu_click_already_closes_menu_before_escape_step.md) — a later "Escape closes it" step asserts on an already-closed menu
- [Confirmed-live ≠ on-main](confirmed_live_is_not_on_main_provenance_check.md) — dev server serves automation/testids; git grep origin/main separately
- [View toggle layout proof](view_toggle_layout_proof_is_entity_card_name_absence_plus_url_param.md) — table headers have no testid; use entity-card-name count + ?view= param
- [Tag filter panel is shared, entity-agnostic](skills_list_tag_filter_quirks.md) — Categories.jsx testids work verbatim on any entity's list page, check before filing testid-needed
- [Pipeline embedded chat = main chat components](pipeline_embedded_chat_shares_main_chat_components.md) — ELITEA-2181's testids already apply, check _surface.md first
- [Pipeline execution needs Save + working model](pipeline_llm_execution_needs_save_and_working_model.md) — Task-fix needs Save; DEV's default Claude 4.5 400s, use gpt-5.2
- [Title project suffix ≠ "Private"](browser_title_project_name_suffix_not_private.md) — capture project name dynamically, don't hardcode "Private" in page-title asserts
- [allure.issue slug can drift](allure_issue_link_slug_can_drift_from_real_tms_filename.md) — verify the TMS URL resolves, don't trust a plausible-looking slug
- [Pipeline clear_embedded_chat() is a no-op](pipeline_clear_embedded_chat_is_broken.md) — stale locator; call chat_clear_button testid directly
- [Run Details Before/After is per-step](pipeline_run_details_before_after_is_per_step_scoped.md) — not run-level; pick the step that touches the var, or read empty
- [Code node needs dict-literal return](code_node_needs_dict_literal_return_not_assignment.md) — assignment silently no-ops; Add-node clicks don't auto-wire edges either
