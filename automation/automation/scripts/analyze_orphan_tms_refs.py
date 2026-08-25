#!/usr/bin/env python3
"""
Analyze orphan TMS refs from dashboard.md and map them to actual test files.
Checks if the last part (test name) exists in the codebase and builds success/failure mappings.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Orphan refs from dashboard.md
ORPHAN_REFS = [
    ("tests.ui.artifacts.test_artifacts_bucket_name_validation_invalid_formats.TestArtifactBucketNameValidationInvalidFormats.test_bucket_name_validation_rejects_invalid_format", "ELITEA-1814"),
    ("tests.ui.chat.test_agent_hub_create_conversation_via_starter.TestAgentHubCreateConversationViaStarter.test_agent_hub_create_conversation_via_starter", "ELITEA-2093"),
    ("tests.ui.chat.test_attach_files_10_left_counter.TestAttachFiles10LeftCounter.test_attach_files_menuitem_shows_10_left_counter", "ELITEA-2195"),
    ("tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_attach_files_of_different_types_shows_identical_icon_and_long_filename_truncates", "ELITEA-2199"),
    ("tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_attach_files_then_remove_two_individually_sequentially", "ELITEA-2198"),
    ("tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_attach_multiple_files_displays_chips_above_composer", "ELITEA-2196"),
    ("tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_long_filename_truncates_and_overflow_indicator_click_expands", "ELITEA-2467"),
    ("tests.ui.chat.test_build_with_ai_cancel_then_generate_echo_agent.TestBuildWithAICancelThenGenerateEchoAgent.test_cancel_then_generate_creates_echo_agent_in_canvas", "ELITEA-2073"),
    ("tests.ui.chat.test_chat_agent_starters_add_remove.TestChatAddAgentWithStartersAndSendViaStarter.test_add_agent_with_starters_and_send_via_starter", "ELITEA-2465"),
    ("tests.ui.chat.test_chat_agent_starters_add_remove.TestChatAddAgentWithStartersToConversation.test_add_agent_with_starters_to_conversation", "ELITEA-2177"),
    ("tests.ui.chat.test_chat_agent_starters_add_remove.TestChatRemoveAgentClearsConversationStarters.test_remove_agent_clears_conversation_starters", "ELITEA-2178"),
    ("tests.ui.chat.test_chat_canvas_edit_agent.TestChatCanvasEditAgent.test_edit_agent_welcome_message_syncs_to_agents_section", "ELITEA-2089"),
    ("tests.ui.chat.test_chat_folder_creation_custom_name_and_cancel.TestChatFolderCreationCustomNameAndCancel.test_cancel_folder_creation_discards_folder", "ELITEA-2134"),
    ("tests.ui.chat.test_chat_folder_creation_custom_name_and_cancel.TestChatFolderCreationCustomNameAndCancel.test_create_folder_with_custom_name", "ELITEA-2457"),
    ("tests.ui.chat.test_chat_folder_rename_checkmark_validation.TestChatFolderRenameCheckmarkValidation.test_folder_rename_cancel_via_x_icon_discards_changes", "ELITEA-2122"),
    ("tests.ui.chat.test_chat_folder_rename_checkmark_validation.TestChatFolderRenameCheckmarkValidation.test_folder_rename_no_changes_close_via_x_icon", "ELITEA-2131"),
    ("tests.ui.chat.test_chat_folder_rename_checkmark_validation.TestChatFolderRenameCheckmarkValidation.test_folder_rename_via_context_menu_edit_option", "ELITEA-2121"),
    ("tests.ui.chat.test_chat_folder_rename_checkmark_validation.TestChatFolderRenameCheckmarkValidation.test_pinned_folder_rename_retains_pin_state", "ELITEA-2130"),
    ("tests.ui.chat.test_chat_folder_rename_length_boundaries.TestChatFolderRenameLengthBoundaries.test_rename_folder_length_boundary_50_chars_accepted", "ELITEA-2128"),
    ("tests.ui.chat.test_chat_folder_rename_length_boundaries.TestChatFolderRenameLengthBoundaries.test_rename_folder_type_and_paste_beyond_max_length_truncates", "ELITEA-2129"),
    ("tests.ui.chat.test_chat_interface.TestHashSearch.test_add_agent_via_hash_search_joins_participants_and_responds", "ELITEA-2469"),
    ("tests.ui.chat.test_chat_interface.TestHashSearch.test_add_pipeline_via_hash_search_joins_participants_and_responds", "ELITEA-2470"),
    ("tests.ui.chat.test_chat_interface.TestHashSearch.test_hash_search_shows_agents_and_pipelines_from_all_sources", "ELITEA-2206"),
    ("tests.ui.chat.test_chat_search_and_modules_panel.TestChatSearchAndModulesPanel.test_search_cleared_by_x_icon_restores_default_view", "ELITEA-2164"),
    ("tests.ui.chat.test_chat_search_and_modules_panel.TestChatSearchAndModulesPanel.test_search_input_cleared_by_deleting_text_updates_dynamically", "ELITEA-2165"),
    ("tests.ui.chat.test_chat_search_and_modules_panel.TestChatSearchAndModulesPanel.test_search_no_results_state", "ELITEA-2163"),
    ("tests.ui.chat.test_close_toolkit_canvas_without_saving.TestCloseToolkitCanvasWithoutSaving.test_close_toolkit_canvas_without_saving_creates_no_toolkit", "ELITEA-2081"),
    ("tests.ui.chat.test_context_auto_summarization_disabled.TestContextAutoSummarizationDisabled.test_no_summarization_when_auto_summarization_disabled", "ELITEA-2217"),
    ("tests.ui.chat.test_context_management_disabled.TestContextManagementDisabledWidgetStaysZero.test_context_management_disabled_widget_stays_at_zero", "ELITEA-2216"),
    ("tests.ui.chat.test_conversation_deletion_inside_folder.TestConversationDeletionInsideFolder.test_delete_conversation_inside_folder_preserves_folder", "ELITEA-2115"),
    ("tests.ui.chat.test_conversation_rename_basic_via_edit_option.TestConversationRenameBasicViaEditOption.test_rename_conversation_basic_via_edit_option", "ELITEA-2099"),
    ("tests.ui.chat.test_conversation_rename_cancel_discards_changes.TestConversationRenameCancelDiscardsChanges.test_rename_conversation_cancel_discards_changes", "ELITEA-2100"),
    ("tests.ui.chat.test_conversation_rename_checkmark_active_state.TestConversationRenameCheckmarkActiveState.test_rename_checkmark_activates_at_three_characters", "ELITEA-2109"),
    ("tests.ui.chat.test_conversation_rename_checkmark_active_state.TestConversationRenameCheckmarkActiveState.test_rename_checkmark_inactive_click_has_no_effect[ELITEA-2105-no-changes]", "ELITEA-2105"),
    ("tests.ui.chat.test_conversation_rename_checkmark_active_state.TestConversationRenameCheckmarkActiveState.test_rename_checkmark_inactive_click_has_no_effect[ELITEA-2106-empty-field]", "ELITEA-2106"),
    ("tests.ui.chat.test_conversation_rename_checkmark_active_state.TestConversationRenameCheckmarkActiveState.test_rename_checkmark_inactive_click_has_no_effect[ELITEA-2107-1-char]", "ELITEA-2107"),
    ("tests.ui.chat.test_conversation_rename_checkmark_active_state.TestConversationRenameCheckmarkActiveState.test_rename_checkmark_inactive_click_has_no_effect[ELITEA-2108-2-char]", "ELITEA-2108"),
    ("tests.ui.chat.test_conversation_rename_invalid_chars_and_recovery.TestConversationRenameInvalidCharsAndRecovery.test_rename_checkmark_inactive_for_invalid_input_shows_tooltip[ELITEA-2110-special-characters]", "ELITEA-2110"),
    ("tests.ui.chat.test_conversation_rename_invalid_chars_and_recovery.TestConversationRenameInvalidCharsAndRecovery.test_rename_checkmark_inactive_for_invalid_input_shows_tooltip[ELITEA-2111-dollar-percent-at-characters]", "ELITEA-2111"),
    ("tests.ui.chat.test_conversation_rename_invalid_chars_and_recovery.TestConversationRenameInvalidCharsAndRecovery.test_rename_checkmark_inactive_for_invalid_input_shows_tooltip[ELITEA-2112-leading-space]", "ELITEA-2112"),
    ("tests.ui.chat.test_conversation_rename_invalid_chars_and_recovery.TestConversationRenameInvalidCharsAndRecovery.test_rename_recovers_and_saves_after_invalid_value_replaced", "ELITEA-2113"),
    ("tests.ui.chat.test_conversation_rename_length_boundaries.TestConversationRenameLengthBoundaries.test_rename_conversation_length_boundary[ELITEA-2101-49-chars]", "ELITEA-2101"),
    ("tests.ui.chat.test_conversation_rename_length_boundaries.TestConversationRenameLengthBoundaries.test_rename_conversation_length_boundary[ELITEA-2102-50-chars]", "ELITEA-2102"),
    ("tests.ui.chat.test_conversation_rename_length_boundaries.TestConversationRenameLengthBoundaries.test_rename_conversation_paste_beyond_max_length_truncates", "ELITEA-2104"),
    ("tests.ui.chat.test_conversation_rename_length_boundaries.TestConversationRenameLengthBoundaries.test_rename_conversation_type_beyond_max_length_truncates", "ELITEA-2103"),
    ("tests.ui.chat.test_create_mcp_from_conversation_discard_changes.TestCreateMcpFromConversationDiscardChanges.test_create_mcp_from_conversation_discard_changes_creates_no_mcp", "ELITEA-2084"),
    ("tests.ui.chat.test_create_new_conversation_team_project_attachments_and_llm.TestCreateNewConversationTeamProjectAttachmentsAndLLM.test_create_conversation_team_project_attachments_and_llm", "ELITEA-2091"),
    ("tests.ui.chat.test_create_toolkit_from_conversation.TestCreateToolkitFromConversation.test_create_toolkit_from_conversation_close_canvas_and_verify_participant", "ELITEA-2083"),
    ("tests.ui.chat.test_delete_confirmation_modal_ui_validation.TestDeleteConfirmationModalUIValidation.test_delete_confirmation_modal_dismisses_via_escape_and_outside_click", "ELITEA-2116"),
    ("tests.ui.chat.test_delete_confirmation_modal_ui_validation.TestDeleteConfirmationModalUIValidation.test_delete_confirmation_modal_title_body_and_button_styling", "ELITEA-2116"),
    ("tests.ui.chat.test_drag_drop_conversation_folder.TestDragDropConversationBackToGeneralList.test_drag_drop_conversation_back_to_general_list", "ELITEA-2145"),
    ("tests.ui.chat.test_drag_drop_conversation_folder.TestDragDropConversationToFolder.test_drag_drop_conversation_to_folder", "ELITEA-2142"),
    ("tests.ui.chat.test_drag_drop_conversation_folder.TestDragDropHighlightsTargetFolderOnHover.test_drag_drop_highlights_target_folder_on_hover", "ELITEA-2143"),
    ("tests.ui.chat.test_folder_creation.TestChatFolderCreation.test_create_folder_default_name_checkmark_active", "ELITEA-2118"),
    ("tests.ui.chat.test_folder_list_scrollability_and_expand_states.TestFolderDisplaysConversationsOrEmptyState.test_folder_displays_conversations_or_empty_state", "ELITEA-2460"),
    ("tests.ui.chat.test_folder_list_scrollability_and_expand_states.TestFolderListScrollableWhenManyFoldersExist.test_folder_list_scrollable_when_many_folders_exist", "ELITEA-2146"),
    ("tests.ui.chat.test_folder_list_scrollability_and_expand_states.TestMoveToSubmenuFolderListScrollable.test_move_to_submenu_folder_list_scrollable", "ELITEA-2147"),
    ("tests.ui.chat.test_generated_echo_agent_save_close_and_starters.TestGeneratedEchoAgentSaveCloseAndStarters.test_save_close_and_use_generated_starters", "ELITEA-2074"),
    ("tests.ui.chat.test_invite_users_add_cancel_close.TestCancelAddUsersModalAfterPreselectingUsers.test_cancel_after_preselecting_two_users_adds_no_one", "ELITEA-2176"),
    ("tests.ui.chat.test_invite_users_add_cancel_close.TestRemovePreselectedUserViaChipX.test_remove_preselected_user_via_chip_x", "ELITEA-2175"),
    ("tests.ui.chat.test_last_remaining_conversation_deletion.TestLastRemainingConversationDeletion.test_delete_last_remaining_conversation_shows_welcome_state", "ELITEA-2117"),
    ("tests.ui.chat.test_move_conversation_to_folder.TestMoveConversationBackToList.test_move_conversation_back_to_list", "ELITEA-2140"),
    ("tests.ui.chat.test_move_conversation_to_folder.TestMoveConversationBetweenTwoFolders.test_move_conversation_between_two_folders", "ELITEA-2141"),
    ("tests.ui.chat.test_move_conversation_to_folder.TestMoveConversationToExistingFolder.test_move_conversation_to_new_folder", "ELITEA-2137"),
    ("tests.ui.chat.test_move_conversation_to_folder.TestMoveConversationToNewFolder.test_move_conversation_to_new_folder_with_custom_name", "ELITEA-2138"),
    ("tests.ui.chat.test_open_conversation_from_folder.TestOpenExistingConversationFromFolder.test_open_existing_conversation_from_folder", "ELITEA-2098"),
    ("tests.ui.chat.test_owner_has_no_remove_control_in_users_dropdown.TestOwnerHasNoRemoveControlInUsersDropdown.test_owner_has_no_remove_control_in_users_dropdown", "ELITEA-2192"),
    ("tests.ui.chat.test_participants_dropdown_click_name_inserts_mention.TestParticipantsDropdownClickNameInsertsMention.test_click_participant_name_inserts_mention[ELITEA-2173-single-mention]", "ELITEA-2173"),
    ("tests.ui.chat.test_participants_dropdown_click_name_inserts_mention.TestParticipantsDropdownClickNameInsertsMention.test_click_participant_name_inserts_mention[ELITEA-2174-two-mentions]", "ELITEA-2174"),
    ("tests.ui.chat.test_pin_conversation.TestChatPanelOrderingPinnedFoldersAndConversations.test_pinned_folder_and_conversation_render_above_unpinned_panel_order", "ELITEA-2461"),
    ("tests.ui.chat.test_pin_conversation.TestMultipleConversationsPinnedIndependently.test_pin_two_conversations_independently", "ELITEA-2160"),
    ("tests.ui.chat.test_pin_conversation.TestPinDisabledInFolderThenMovedAndPinned.test_pin_disabled_in_folder_then_moved_and_pinned", "ELITEA-2158"),
    ("tests.ui.chat.test_pin_conversation.TestUnpinConversationViaContextMenu.test_unpin_conversation_via_context_menu", "ELITEA-2150"),
    ("tests.ui.chat.test_pin_folder.TestMultipleFoldersPinnedIndependently.test_pin_two_folders_independently", "ELITEA-2161"),
    ("tests.ui.chat.test_pin_folder.TestPinFolderViaPinOnTop.test_pin_empty_folder_retains_empty_state", "ELITEA-2155"),
    ("tests.ui.chat.test_pin_folder.TestPinFolderViaPinOnTop.test_pin_folder_via_pin_on_top", "ELITEA-2462"),
    ("tests.ui.chat.test_pin_folder.TestPinFolderViaPinOnTop.test_pin_folder_with_multiple_conversations_retains_all", "ELITEA-2154"),
    ("tests.ui.chat.test_pin_folder.TestUnpinFolderViaContextMenu.test_unpin_empty_folder_retains_empty_state", "ELITEA-2156"),
    ("tests.ui.chat.test_pin_folder.TestUnpinFolderViaContextMenu.test_unpin_folder_via_context_menu", "ELITEA-2153"),
    ("tests.ui.chat.test_pipeline_create_save_basic_configuration.TestPipelineCreateSaveBasicConfiguration.test_create_pipeline_save_basic_configuration", "ELITEA-2077"),
    ("tests.ui.chat.test_pipeline_discard_changes_clears_canvas.TestPipelineDiscardChangesClearsCanvas.test_discard_clears_canvas_and_creates_no_pipeline", "ELITEA-2076"),
    ("tests.ui.chat.test_pipeline_flow_editor_discard_llm_node.TestPipelineFlowEditorDiscardLlmNode.test_add_llm_node_discard_changes_removes_node", "ELITEA-2078"),
    ("tests.ui.chat.test_public_conversation_green_icon.TestPublicConversationGreenIcon.test_public_conversation_shows_green_icon_in_chat_list", "ELITEA-2188"),
    ("tests.ui.chat.test_regenerate_response.TestRegenerateResponse.test_regenerate_only_on_last_and_click_triggers_new_generation", "ELITEA-2187"),
    ("tests.ui.chat.test_regenerate_response.TestRegenerateResponse.test_regenerate_replaces_response_with_new_generation", "ELITEA-2185"),
    ("tests.ui.chat.test_regenerate_response.TestRegenerateResponse.test_regenerate_visible_only_on_last_response", "ELITEA-2184"),
    ("tests.ui.chat.test_send_message_with_attachments_verify_included.TestSendMessageWithAttachmentsVerifyIncluded.test_send_message_with_attachments_verify_included", "ELITEA-2201"),
    ("tests.ui.chat.test_slash_mention_mcp_selection_and_available_tools.TestSlashMentionMcpSelectionAndAvailableTools.test_select_mcp_from_slash_mention_no_tools_shows_empty_panel", "ELITEA-2468"),
    ("tests.ui.chat.test_slash_mention_mcp_selection_and_available_tools.TestSlashMentionMcpSelectionAndAvailableTools.test_select_mcp_from_slash_mention_shows_its_tools", "ELITEA-2468"),
    ("tests.ui.chat.test_streaming_response.TestStreamingResponse.test_composer_send_button_toggles_with_empty_input_and_waveform_reappears", "ELITEA-2466"),
    ("tests.ui.help_center.test_help_center_resource_links.TestHelpCenterResourceLinks.test_resource_card_link_redirects_to_external_page[ELITEA-2220-documentation-getting-started]", "ELITEA-2220"),
    ("tests.ui.help_center.test_help_center_resource_links.TestHelpCenterResourceLinks.test_resource_card_link_redirects_to_external_page[ELITEA-2221-release-notes-latest]", "ELITEA-2221"),
    ("tests.ui.help_center.test_help_center_resource_links.TestHelpCenterResourceLinks.test_resource_card_link_redirects_to_external_page[ELITEA-2222-tutorials-how-to-create-an-agent]", "ELITEA-2222"),
    ("tests.ui.help_center.test_help_center_resource_links.TestHelpCenterResourceLinks.test_resource_card_link_redirects_to_external_page[ELITEA-2224-tutorials-more]", "ELITEA-2224"),
    ("tests.ui.help_center.test_help_center_resource_links.TestHelpCenterResourceLinks.test_video_library_more_redirects_to_external_portal", "ELITEA-2223"),
    ("tests.ui.help_center.test_help_center_sidebar_tour.TestHelpCenterSidebarTourExtras.test_sidebar_interactive_tour_back_returns_to_step_one", "ELITEA-2230"),
    ("tests.ui.help_center.test_help_center_sidebar_tour.TestHelpCenterSidebarTourExtras.test_sidebar_interactive_tour_restarts_after_completion", "ELITEA-2228"),
    ("tests.ui.help_center.test_help_center_sidebar_tour.TestHelpCenterSidebarTourExtras.test_sidebar_interactive_tour_skip_terminates", "ELITEA-2229"),
    ("tests.ui.help_center.test_help_center_sidebar_tour.TestHelpCenterSidebarTourExtras.test_sidebar_interactive_tour_starts_on_link_click", "ELITEA-2226"),
    ("tests.ui.help_center.test_help_center_version_info.TestHelpCenterVersionInfo.test_version_info_tooltip_displays_and_copies", "ELITEA-2225"),
    ("tests.ui.onboarding.test_onboarding_welcome.TestOnboardingWelcomePage.test_welcome_page_displayed_on_first_login", "ELITEA-2231"),
    ("tests.ui.settings.test_ai_providers_page_sections_load_without_error.TestAIProvidersPageSections.test_ai_providers_page_sections_load_without_error_test", "ELITEA-2392"),
    ("tests.ui.skills.test_agent_skills_validation_attribution_and_token_invalidation.TestAgentSkillsValidationAttributionAndTokenInvalidation.test_agent_skills_validation_attribution_and_token_invalidation", "ELITEA-2601"),
    ("tests.ui.skills.test_agent_with_skills_publishing_flow.TestAgentWithSkillsPublishingFlow.test_agent_with_skills_publishing_flow", "ELITEA-2600"),
    ("tests.ui.skills.test_published_agent_version_cannot_be_modified.TestPublishedAgentVersionCannotBeModified.test_published_agent_version_cannot_be_modified", "ELITEA-2614"),
    ("tests.ui.skills.test_skill_agent_interaction.TestInteractWithSkillsFromAgent.test_skill_autonomous_invocation_thought_process_and_security", "ELITEA-2607"),
    ("tests.ui.skills.test_skill_agent_interaction.TestInteractWithSkillsFromAgent.test_skill_explicit_and_autonomous_invocation_coexistence", "ELITEA-2609"),
    ("tests.ui.skills.test_skill_agent_version_selection_behavior.TestSkillAgentVersionSelectionBehavior.test_skill_version_selection_drives_agent_chat_behavior", "ELITEA-2610"),
    ("tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAIBackToPromptFromReviewStep.test_back_to_prompt_returns_to_input_step_and_preserves_prompt_text", "ELITEA-1996"),
    ("tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAICancelFromPromptStep.test_cancel_from_prompt_step_closes_modal_without_creating_skill", "ELITEA-1997"),
    ("tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAICancelFromReviewStep.test_cancel_from_review_step_does_not_create_skill", "ELITEA-1998"),
    ("tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAICreationFailureRecovery.test_creation_failure_stays_on_review_step_and_retry_succeeds", "ELITEA-2000"),
    ("tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAIGeneratedNameNamingRules.test_generated_skill_name_adheres_to_naming_rules", "ELITEA-1992"),
    ("tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAIReviewFormCharacterLimits.test_review_form_field_character_limit_is_enforced[ELITEA-1994-description", "ELITEA-1994"),
    ("tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAIReviewFormCharacterLimits.test_review_form_field_character_limit_is_enforced[ELITEA-1995-instructions", "ELITEA-1995"),
    ("tests.ui.skills.test_skill_build_with_ai_role_visibility.TestSkillBuildWithAIButtonRoleVisibility.test_build_with_ai_button_visible_for_admin_role", "ELITEA-1986"),
    ("tests.ui.skills.test_skill_edit_with_ai_happy_path.TestSkillEditWithAIHappyPath.test_edit_with_ai_happy_path", "ELITEA-2611"),
    ("tests.ui.skills.test_skill_edit_with_ai_navigation_error_handling.TestSkillEditWithAINavigationErrorHandling.test_edit_with_ai_navigation_and_error_handling", "ELITEA-2612"),
    ("tests.ui.skills.test_skill_edit_with_ai_role_visibility.TestSkillEditWithAICharacterLimit.test_edit_with_ai_summary_instructions_truncates_at_character_limit", "ELITEA-2613"),
    ("tests.ui.skills.test_skill_edit_with_ai_role_visibility.TestSkillEditWithAIRoleVisibility.test_edit_with_ai_button_visible_for_admin_role", "ELITEA-2613"),
    ("tests.ui.skills.test_skill_publish_ai_validation_blockers.TestSkillPublishAiValidationBlockers.test_short_content_placeholder_and_secrets_block_publish", "ELITEA-2596"),
    ("tests.ui.skills.test_skill_publish_token_invalidation_and_ttl.TestSkillPublishTokenInvalidationAndTTL.test_publish_token_expires_after_ttl", "ELITEA-2597"),
    ("tests.ui.skills.test_skill_publish_token_invalidation_and_ttl.TestSkillPublishTokenInvalidationAndTTL.test_publish_token_invalidated_by_modification", "ELITEA-2597"),
    ("tests.ui.skills.test_skill_publish_warn_status_allows_publishing.TestSkillPublishWarnStatusAllowsPublishing.test_warn_status_does_not_block_publish", "ELITEA-2598"),
    ("tests.ui.skills.test_skill_publish_wizard_happy_path.TestSkillPublishWizardHappyPath.test_publish_skill_happy_path", "ELITEA-2595"),
    ("tests.ui.skills.test_skill_unpublish_republish_lifecycle.TestSkillUnpublishRepublishLifecycle.test_unpublish_republish_lifecycle", "ELITEA-2599"),
    ("tests.ui.skills.test_subagent_skills_isolation.TestSubagentSkillsIsolation.test_subagent_uses_only_its_own_attached_skill", "ELITEA-2608"),
]


def search_test_in_codebase(test_name: str) -> List[str]:
    """Search for test name in codebase using grep."""
    try:
        result = subprocess.run(
            ["grep", "-r", "--include=*.py", f"def {test_name}", "tests/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        if result.returncode == 0:
            return [line.strip() for line in result.stdout.strip().split('\n') if line]
        return []
    except Exception as e:
        print(f"Error searching for {test_name}: {e}")
        return []


def extract_test_name(full_ref: str) -> str:
    """Extract just the test method name from the full dotted ref."""
    # Handle parametrized tests - extract base name before [
    if '[' in full_ref:
        full_ref = full_ref.split('[')[0]

    # Get the last part after the last dot
    return full_ref.split('.')[-1]


def main():
    print("Analyzing orphan TMS refs...\n")

    found = []
    not_found = []

    for full_ref, case_id in ORPHAN_REFS:
        test_name = extract_test_name(full_ref)
        matches = search_test_in_codebase(test_name)

        if matches:
            # Convert grep output to proper automation test path
            for match in matches:
                # Extract file path from grep output
                file_path = match.split(':')[0]

                # Convert to dotted automation test path
                # Remove tests/ prefix and .py extension, replace / with .
                if file_path.startswith('tests/'):
                    auto_path = file_path[:-3].replace('/', '.')

                    # Extract class name if present
                    class_match = None
                    if '::' in match or 'class ' in match:
                        # Try to extract class name from the file
                        try:
                            with open(Path(__file__).parent.parent / file_path, 'r') as f:
                                content = f.read()
                                # Look for class definition before this test
                                import re
                                # Find class that contains this test
                                class_pattern = r'class\s+(\w+).*?def\s+' + test_name
                                class_search = re.search(class_pattern, content, re.DOTALL)
                                if class_search:
                                    class_match = class_search.group(1)
                        except:
                            pass

                    # Build full path
                    if class_match:
                        full_auto_path = f"{auto_path}.{class_match}.{test_name}"
                    else:
                        full_auto_path = f"{auto_path}.{test_name}"

                    found.append({
                        "tms_ref": full_ref,
                        "case_id": case_id,
                        "test_name": test_name,
                        "file_path": file_path,
                        "automation_test_id": full_auto_path,
                        "matches": matches
                    })
        else:
            not_found.append({
                "tms_ref": full_ref,
                "case_id": case_id,
                "test_name": test_name
            })

    # Save results
    results = {
        "summary": {
            "total_orphans": len(ORPHAN_REFS),
            "found": len(found),
            "not_found": len(not_found)
        },
        "found_mappings": found,
        "not_found": not_found
    }

    output_file = Path(__file__).parent / "orphan_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✅ Analysis complete!")
    print(f"   Total orphans: {len(ORPHAN_REFS)}")
    print(f"   Found in code: {len(found)}")
    print(f"   Not found: {len(not_found)}")
    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
