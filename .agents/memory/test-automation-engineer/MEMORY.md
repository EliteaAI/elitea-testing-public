# Memory index — test-automation-engineer

> Only *preventive* facts are indexed — things that change your FIRST move.
> Per-surface notes (component testid maps, per-feature quirks, one-off case
> workarounds) are NOT listed but ARE on disk — always grep before concluding a
> surface is unknown: `grep -rl '<keyword>' .agents/memory/test-automation-engineer/`
> Compacted by scout 2026-08-10 (59 → 31 lines): merged 12 near-duplicate clusters
> into their richest survivor, demoted surface lookups to disk-only, promoted 5
> preventive entries. No entry file was deleted — everything stays greppable.
> `(N×)` = how many separate sessions hit it.
- [Autonomous skill invocation needs a nudge](autonomous_skill_invocation_nudge.md) — attach alone won't do it
- [dnd-kit drag needs a settle-check](dnd_kit_drag_gesture_needs_settle_check.md) — scroll-into-view AND elementFromPoint poll, not just one
- [chat-remaining-w03 case snapshots never existed](chat_remaining_w03_case_snapshots_never_existed.md) — read the TMS file directly, not a novel-ground signal
- [Dynamic testid suffix collides with prefix selector](dynamic_testid_suffix_collides_with_prefix_selector.md) — `${itemId}-suffix` matches item's own `^=` prefix locator; add `:not()`

- [Project briefing](project_briefing.md) — your slot, the six-phase loop, the ≤2-rerun budget, the Run Report
- [Verify feature branch first](verify_feature_branch_before_first_commit.md) — `git branch --show-current` before any commit; dispatch starts you ON the trunk (5×)
- [Never amend after a failed husky commit](never_amend_after_a_failed_husky_commit_on_shared_branch.md) — rejected hook still leaves HEAD on someone else's commit
- [AFS: work order, not gospel](afs_is_a_work_order_not_gospel.md) — verify every claim live; amend the AFS + _surface.md, never re-scope (12×)
- [PROVENANCE needs both refs + git status](afs_on_main_provenance_claim_needs_two_ref_grep.md) — grep origin/main AND origin/automation/testids (6×)
- [AFS Priority vs pytest.mark](afs_priority_vs_pytest_mark_preflight_check.md) — grep Priority vs @pytest.mark.pN before handoff, incl. module-inherited (8×)
- [Verify your own delivery](verify_your_own_delivery_before_handoff.md) — exit code/stdout lie; run all three greps against the batch trunk (12×)
- [Fix round: diff-check each named finding](fix_round_must_diff_check_each_named_finding.md) — grep the round's own commit per finding before calling it done, don't rely on memory
- [chat-send-button force-click race](chat_send_button_force_click_race.md) — plain `.click()`, not `force=True`, right after a starter/programmatic composer populate
- [force=True races a Collapse animation](force_click_races_mui_collapse_animation.md) — 2nd force-click miss (2×): try plain `.click()` after ANY container state change
- [Mechanical greps diff the batch trunk](mechanical_greps_diff_against_batch_trunk_not_origin_base.md) — origin/automation/base lags it; diffing base fakes both results
- [Triple-dot diff hides uncommitted work](triple_dot_diff_hides_uncommitted_changes_when_head_equals_base.md) — `ref...` is empty if HEAD==ref; use `git diff ref` (two-dot) for the self-check grep
- [Console side-channel checks](console_side_channel_checks.md) — dual listener, registered pre-step-1, filter proven to fire (5×)
- [Waits & races](never_assume_a_transition_settled.md) — networkidle/capture-list/Enter-send/cold-nav all lie; name the signal (8×)
- [is_visible(timeout=) does not poll](locator_is_visible_timeout_kwarg_does_not_poll.md) — one-shot read; use .wait_for(state="visible")
- [Proving a negative w/o sleep](proving_a_negative_without_wait_for_timeout.md) — Locator.wait_for() + pytest.raises(TimeoutError)
- [Sanctioned-RED traps](sanctioned_red_soft_assert_traps.md) — soft_failures not expect.soft; never author a new raw locator to fit its API
- [An assertion can prove the wrong fact](assertion_proves_the_wrong_fact.md) — invert-check is necessary, not sufficient; isolate every OR-gate (5×)
- [Shared-state cleanup must soft-assert](cleanup_verification_on_shared_state_must_soft_assert.md) — logger.error-only lets failed cleanup pollute the baseline
- [MUI testid lands on the wrapper](testid_lands_on_mui_wrapper_not_input.md) — relocate via inputProps/slotProps at source; never chain .locator("input") (11×)
- [Declared improvisation needs AFS sweep](declared_improvisation_needs_afs_sweep_not_just_pr_narration.md) — PR-body narration alone leaves the AFS document stale; amend Concrete Handles + Hints too
- [MUI icon auto-testid is dev-build-only](mui_icon_auto_testid_is_dev_build_only_never_locate_on_it.md) — green on localhost, absent in every deployed env
- [New testid must not share a prefix selector](component_level_testid_must_not_share_a_prefix_selector.md) — grep `^=` in the page object before naming
- [#579 exceptions are narrow](custom_handle_testid_prop_not_579_exception.md) — CustomHandle/SingleSelect are app-owned; only ReactFlow/CodeMirror internals qualify
- [No page.locator() in a spec](dynamic_testid_template_constants_need_a_wrapper_method.md) — even a real TESTID_TEMPLATE class field needs a page-object method
- [Dialogs need their own testid](mui_dialog_needs_its_own_testid_not_role_dialog.md) — get_by_role("dialog") is a locator-policy violation
- [a11y `[active]` = focus, not selection](playwright_active_marker_is_focus_not_selection.md) — add data-selected instead of asserting it
- [Control+a no select-all on macOS](control_a_no_select_all_on_macos_chromium.md) — use select_text() + selection-applied wait to clear a field
- [MUI overlays swallow clicks](mui_menu_stays_open_backdrop_intercepts_outside_clicks.md) — escalate to evaluate-click / React onClick; hover the header (5×)
- [Re-selecting a shown value no-ops or toggles off](mui_select_onchange_only_fires_on_value_change.md) — verify pre-set state read-only instead (3×)
- [reasoning_effort on API-created agents](reasoning_effort_none_breaks_embedded_chat.md) — "none" is save/reload-only; any chat-sending test needs another value
- [Page-object API calls need Bearer fallback](page_object_api_delete_needs_bearer_fallback_on_localhost.md) — self.page.request has no cookies on localhost
- [Name fields cap at 32 chars](pipeline_agent_name_field_32char_silent_truncation.md) — silent truncation on agent-name-input, blocks Approve on Build-with-AI (3×)
- [Shared save testid, create vs edit](shared_save_testid_create_vs_edit_navigation_false_pass.md) — create-flow save-and-wait-for-nav helper false-passes on an edit form (no nav)
- [Entity-card list pages](search_highlight_breaks_exact_text_locator.md) — read entity-card-name + .text_content(); scope per-card via .filter(has=…) (3×)
- [Killed runs orphan test data](killed_background_run_orphans_test_data.md) — backgrounded/SIGKILLed pytest skips finally:; filter by name+id, not id alone
- [Resume dispatch: trust disk](resume_dispatch_trust_disk_not_prior_session_notes.md) — a prior session's "completed" note can describe uncommitted code; grep first
- [Positive-existence wait can't assert negative transition](positive_existence_wait_cant_assert_negative_transition.md) — `not is_X()` right after a click races; use `expect().to_have_attribute()` instead
- [Assert at the AFS step, not deferred](assert_at_the_afs_step_not_deferred.md) — verify step N's result inside step N's own allure.step, not step N+1 (rejected 2×)
- [Dead-code guard needs class scoping](dead_code_locator_guard_needs_class_scoping.md) — bare class-name substring still false-passes; require real import/instantiation
- ["Pre-existing" testid, 0-element timeout](icon_picker_close_button_testid_prop_mismatch.md) — suspect a wrapper prop-name mismatch, not timing
- [Dirty trunk from an interrupted prior unit](dirty_trunk_from_interrupted_prior_unit_quarantine_dont_absorb.md) — quarantine onto its OWN branch first; never absorb or clean
- [Icon picker Uploaded gallery can get stuck](skill_icon_uploaded_gallery_order.md) — infinite-scroll loader breaks after mutation+page>0 (#1459); don't build on data-selected there
- [verify_on_detail_page races SPA route](verify_on_detail_page_races_spa_route_push.md) — call wait_for_page_load() first, always, after any save/nav
- [Publish button loses testid on rejection](publish_wizard_step_advances_before_request_resolves_kills_testid.md) — step→PUBLISHING fires before the request resolves
- [Publish AI gate flags "reply X" instructions](skill_publish_ai_gate_rejects_blanket_reply_instructions.md) — 422/FAIL prompt-injection heuristic; use bounded task-specific text
- [Popper select_menuitem substring collision](popper_select_menuitem_substring_collision_attaches_wrong_item.md) — attach-by-name .filter(has_text=).first silently attaches the wrong entity if one seeded name is a substring of another
- [gate-case.mjs timeout/tail trap](gate_case_timeout_and_tail_piping_loses_verdict.md) — size --timeout to real runtime, never `| tail -N`; junit.xml is ground truth if verdict is lost
- [Skill icon-upload-before-tag-save race](skill_publish_wizard_implementer_quirks.md) — icon PUT can revert an unsaved tag; save tag FIRST, then upload icon
- [Edit-with-AI wizard step numbering is positional](edit_with_ai_wizard_step_numbering_is_positional.md) — General/Instructions can be skipped; never hardcode "3. Summary"
- [Nested agent accordion always has wrapper chip](nested_agent_accordion_always_has_wrapper_chip.md) — never assert to_have_count(0) on it; filter to "Skill: " prefix instead
- [Testid-only policy scope = our own app](testid_only_policy_scope_is_our_own_app_source.md) — third-party redirect destinations use ordinary role locators; declare it
- [Build-with-AI suggestion nondeterminism](skill_suggestion_llm_nondeterminism_blocks_live_rewrite.md) — any suggested_* array can go empty across repeats; test 5-6× before trusting a live rewrite
- [Concurrent MCP contaminates dev-token session](concurrent_mcp_session_contaminates_shared_devtoken_conversation.md) — never explore live + run pytest at once; re-run in isolation before blaming a defect
- [Cut your branch FIRST on a batch dispatch](dispatch_tree_starts_on_trunk_cut_your_own_branch_first.md) — "tree is on trunk" = starting state, not commit target
- [Sandbox project 400 for isolated conversation state](sandbox_project_400_for_isolated_conversation_state.md) — genuinely empty; use for exact-count preconditions instead of clearing a shared project
- [Search query cache hit defeats expect_response](search_query_cache_hit_defeats_expect_response_wait.md) — re-querying an already-fetched value (incl. clear-to-initial) can skip the network entirely
- [Folder menuItems array is a repeat regression site](folder_menuitems_array_is_a_repeat_regression_site.md) — re-verify a dot-menu testid live before building, don't trust a prior AFS's claim
- [Chat folder list: shared scroll region, newest-first](chat_folder_list_shared_scroll_container_and_ordering.md) — never assume raw-scroll-max = last-created folder; check live position instead
- [AFS-authorized soft assertion is still masking](afs_authorized_soft_assertion_is_still_masking.md) — AFS text can request a `logger.warning` instead of `assert`; No Defect Masking Rule wins
- [Soft-assert/known-defect ≠ headline subject](soft_assert_known_defect_only_covers_isolated_not_headline_subject.md) — only covers one isolated step; case's own headline observable → blocked
- [New testid can collide with existing `^=` prefix](new_dynamic_testid_can_collide_with_existing_prefix_matcher.md) — grep the prefix string before naming a sibling dynamic testid
