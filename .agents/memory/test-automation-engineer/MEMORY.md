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
- [Proving a negative w/o sleep](proving_a_negative_without_wait_for_timeout.md) — `Locator.wait_for()` + `pytest.raises(TimeoutError)`, never wait_for_timeout
- [post_data_json is None](playwright_post_data_json_none_use_route_interception.md) — use page.route() to read a request body, not response.request
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
- [press_sequentially can drop the first char](search_input_press_sequentially_drops_leading_keystroke.md) — plain native-input search box: prefer .fill() if a sibling page object already does
- [AFS "pre-existing testid" can be uncommitted](afs_pre_existing_testid_claim_can_be_uncommitted_worktree_only.md) — check `git status`/`git log` in EliteaUI, not just the live DOM
- [MUI Menu trigger click can silently no-op](secrets_row_actions_menu_click_needs_react_props_invoke.md) — .click()/force/el.click() all fail; invoke React onClick prop directly
- [Testid provenance: check timestamps](testid_provenance_claim_verify_commit_timestamp_vs_afs.md) — diff testid commit vs AFS commit before claiming "predates session"/"drift"
- [PROVENANCE "on-main" needs both refs](afs_on_main_provenance_claim_needs_two_ref_grep.md) — grep origin/main AND origin/automation/testids; same-day claim isn't exempt
- [a11y `[active]` = focus, not selection](playwright_active_marker_is_focus_not_selection.md) — never assert it as "selected"; add data-selected instead
- [Shared-state cleanup must soft-assert](cleanup_verification_on_shared_state_must_soft_assert.md) — logger.error-only lets a failed cleanup pollute the shared baseline silently
- [MUI icon auto-testid is dev-build-only](mui_icon_auto_testid_is_dev_build_only_never_locate_on_it.md) — never locate on it; add a real data-testid prop on the icon call site instead
- [is_visible(timeout=) does not poll](locator_is_visible_timeout_kwarg_does_not_poll.md) — one-shot read, kwarg ignored; use .wait_for(state="visible") to actually wait
- [Catalog Start Chat needs extra wait (#1043)](catalog_start_chat_1043_needs_extra_wait.md) — open_agent_by_name()'s wait alone isn't enough; add wait_for_timeout(1000) before click_start_chat()
- [reasoning_effort:"none" agent silently no-ops chat send](reasoning_effort_none_agent_silently_no_ops_chat_send.md) — use plain create_agent() for any test that actually sends a message
- [Nested agent attach/accordion quirks](nested_agent_attach_and_accordion_quirks.md) — attach_agent_by_testid() over attach_agent(); expect_response() over capture_requests_matching(); two tool-chips share one testid
- [wait_for_chat_response header text false-stable](wait_for_chat_response_header_text_false_stable.md) — low-effort agents: header/thought-accordion text can lock in as "stable" before the answer renders
- [Search highlighting breaks exact text= locators](search_highlight_breaks_exact_text_locator.md) — read entity-card-name testid + .text_content() instead, on any entity-card list page
- [Name field 32-char silent truncation](pipeline_agent_name_field_32char_silent_truncation.md) — agent-name-input caps at 32, no error; keep generated names ≤32 chars
- [Build-with-AI review Name 32-char BLOCKS approve](build_with_ai_review_form_name_32char_validation_blocks_approve.md) — unlike above, disables Create Agent button, not silent
- [Save As Version is never dirty-gated](pipeline_save_as_version_quirks.md) — don't assert it disabled at baseline; ReactFlow always renders a synthetic END node too
- [Signal-parity claims need an assertion diff](afs_signal_parity_claim_needs_assertion_diff.md) — "same N-signal pattern" prose ≠ same assert list; diff them
- [Page-object API delete needs Bearer fallback on localhost](page_object_api_delete_needs_bearer_fallback_on_localhost.md) — self.page.request has no cookies there; 400s silently without it
- [Pipeline node types can share a component tree](pipeline_custom_node_shares_toolkit_node_component_tree.md) — check BaseToolNode/DefaultNode family before assuming from-scratch testid work
- [MUI SingleSelect auto-id ≠ #579](mui_simple_select_auto_id_is_not_a_579_exception.md) — `#simple-select-<Label>` is app-owned (accepts data-testid), not library-internal
- [CustomHandle testId ≠ #579](custom_handle_testid_prop_not_579_exception.md) — `.react-flow__handle` accepts a `testId` prop; not library-internal DOM
- [Pipeline YAML tab truncates](pipeline_yaml_tab_truncates_use_api_not_dom.md) — long docs cut off silently; use `pipeline_api.get_pipeline()` not the DOM (#1025)
- [Fork/Import "Got it" stale copy-id race](fork_import_got_it_stale_copy_id_race.md) — poll copy-id text to settle before reading id right after Got it
- [Delete-menu redirect needs real history](delete_menu_redirect_navigate_minus_one_needs_history.md) — navigate(-1) no-ops after page.goto(); soft-assert + #1332
- [Mechanical grep misses JS-string selectors](mechanical_grep_misses_js_string_embedded_selectors.md) — grep querySelector too on any wait_for_function/evaluate diff
- [Fixed-value YAML field types by content](chat_history_value_field_serializes_as_yaml_list_not_string.md) — typed "[]" parses as list not str; assert live type, not case wording
- [Dynamic Tooltip title + child's own aria-label = no clone](mui_tooltip_dynamic_title_needs_slotprops_testid_when_child_has_own_arialabel.md) — read via slotProps.tooltip testid, not aria-label
- [Wave dispatch case-snapshot dir has no wave suffix](wave_dispatch_case_snapshot_dir_has_no_wave_suffix.md) — check `<campaign>/cases/` before `needs-analyst` on a missing `-w<N>` path
