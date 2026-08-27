# Memory index — test-automation-engineer

> Only *preventive* facts are indexed — things that change your FIRST move.
> Per-surface notes (component testid maps, per-feature quirks, one-off case
> workarounds) are NOT listed but ARE on disk — always grep before concluding a
> surface is unknown: `grep -rl '<keyword>' .agents/memory/test-automation-engineer/`
> Compacted by scout 2026-08-10 (59 → 31 lines): merged 12 near-duplicate clusters
> into their richest survivor, demoted surface lookups to disk-only, promoted 5
> preventive entries. No entry file was deleted — everything stays greppable.
> `(N×)` = how many separate sessions hit it.

- [Project briefing](project_briefing.md) — your slot, the six-phase loop, the ≤2-rerun budget, the Run Report
- [Verify feature branch first](verify_feature_branch_before_first_commit.md) — `git branch --show-current` before any commit; dispatch starts you ON the trunk (5×)
- [Never amend after a failed husky commit](never_amend_after_a_failed_husky_commit_on_shared_branch.md) — rejected hook still leaves HEAD on someone else's commit
- [AFS: work order, not gospel](afs_is_a_work_order_not_gospel.md) — verify every claim live; amend the AFS + _surface.md, never re-scope (12×)
- [PROVENANCE needs both refs + git status](afs_on_main_provenance_claim_needs_two_ref_grep.md) — grep origin/main AND origin/automation/testids (6×)
- [AFS Priority vs pytest.mark](afs_priority_vs_pytest_mark_preflight_check.md) — grep Priority vs @pytest.mark.pN before handoff, incl. module-inherited (8×)
- [Verify your own delivery](verify_your_own_delivery_before_handoff.md) — exit code/stdout lie; run all three greps against the batch trunk (12×)
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
- [UI/flow assumption gate](ui_flow_assumption_gate.md) — test fails, assume UI changed? Verify vs case text first, wait if unconfirmed
- [Backend API investigation](backend_api_investigation.md) — API fails/wrong data? Isolate, compare CI/local, check retriability
- [A test owns its preconditions](test_owns_its_preconditions.md) — create every entity the case needs; borrowed data passes dirty, fails clean
- [Comment quoting a removed raw locator](comment_quoting_removed_raw_locator_trips_reviewer_grep.md) — trips the reviewer's grep; describe it in prose
- [Early-return null does not mean the observable is gone](early_return_null_does_not_mean_the_observable_is_gone.md) — grep the product for the TEXT before writing "removed"
- [Version sort: no pinned tier](version_dropdown_sort_lost_its_pinned_tier.md) — EliteaUI #857: date desc, base last
- [Rendered timestamps are server UTC](rendered_timestamps_are_server_utc_not_local.md) — assert vs API created_at
- [Chat AI answers: assert the index](chat_ai_answer_assert_the_index_not_the_settle.md) — wait_for_ai_response settles mid-turn; use expect().to_contain_text on nth(n+1)
- [Chat attachments are never inlined](chat_attachments_content_is_never_inlined.md) — upload fires at SEND; the model must call the attachments tool
