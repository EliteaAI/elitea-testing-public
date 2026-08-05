# Memory index — test-automation-engineer

> Only *preventive* facts are indexed — things that change your FIRST move.
> Per-surface implementer notes are NOT listed but ARE on disk:
> `grep -rl '<keyword>' .agents/memory/test-automation-engineer/`

- [Project briefing](project_briefing.md) — your slot, the six-phase loop, the ≤2-rerun budget, the Run Report
- [Verify feature branch first](verify_feature_branch_before_first_commit.md) — `git branch --show-current` BEFORE anything else; dispatch starts you ON the trunk
- [Console side-channel checks](console_side_channel_checks.md) — 5 ways a "no console errors" assert proves nothing
- [Waits & races](never_assume_a_transition_settled.md) — networkidle/capture-list/Enter-send/cold-nav all lie
- [Verify your own delivery](verify_your_own_delivery_before_handoff.md) — exit code, stdout and "done" all lie
- [AFS: work order, not gospel](afs_is_a_work_order_not_gospel.md) — verify each claim; amend the file, don't re-scope
- [Sanctioned-RED traps](sanctioned_red_soft_assert_traps.md) — soft_failures not expect.soft; RED isn't guaranteed
- [An assertion can prove the wrong fact](assertion_proves_the_wrong_fact.md) — invert-check passes, claim still false
- [Agent fixtures that will chat](reasoning_effort_none_breaks_embedded_chat.md) — reasoning_effort:"none" 500s chat
- [Testid lands on the MUI wrapper](testid_lands_on_mui_wrapper_not_input.md) — relocate via inputProps/slotProps
- [Entity-card scoping](entity_card_scoping_pattern.md) — shared Card.jsx already has entity-card/-name; check first
- [Shared SearchBar min length](skills_search_bar_quirks.md) — MIN_SEARCH_KEYWORD_LENGTH=3 silently blocks activation
- [AI text substring-vs-exact flake](ai_text_substring_vs_exact_match_flake.md) — before blaming virtualization, check match semantics agree
- [Control+a no select-all on macOS](control_a_no_select_all_on_macos_chromium.md) — use select_text()+wait, not raw Ctrl+A, to clear a field
- [MUI Select onChange skips on same value](mui_select_onchange_only_fires_on_value_change.md) — "re-select shown value" AFS steps can hit a real no-op defect
- [Pipeline STATE panel overlap + wait_for_function](pipeline_state_panel_overlaps_canvas_and_wait_for_function_arg_kwarg.md) — close it before canvas clicks; arg= is keyword-only
- [Interrupt before toggle omission](interrupt_before_toggle_recurring_omission.md) — 3rd pipeline-node AFS to skip it; use is_node_interrupt_before_toggle_visible(node_id)
- [grid-table name column bypasses renderCell](grid_table_name_column_bypasses_rendercell.md) — thread nameCellTestId, not a renderCell 'name' branch
- [AFS Priority vs pytest.mark](afs_priority_vs_pytest_mark_preflight_check.md) — grep AFS Priority vs @pytest.mark.pN BEFORE writing the test, incl. module-inherited
- [Settings->Users hidden for private project](settings_users_hidden_for_private_project_guard.md) — env's ELITEA_PROJECT_ID is the private project; switch project BEFORE navigating to /settings/users
- [New testid must not share an existing prefix selector](component_level_testid_must_not_share_a_prefix_selector.md) — grep `\^="` in the page object before naming
- [StyledInputEnhancer testid needs inputProps](styledinputenhancer_data_testid_needs_inputprops_not_bare_prop.md) — bare data-testid lands on TextField wrapper div, not the input/textarea
- [Disabled-button multi-gate isolation](disabled_button_multi_gate_assertion_isolation.md) — pre-satisfy every OTHER gate in `disabled={A||B||C}` before asserting
