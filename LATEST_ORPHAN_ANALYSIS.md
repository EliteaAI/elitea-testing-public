# Complete Orphan TMS References Analysis
**Generated:** 2026-08-21 16:40 UTC

## Executive Summary

**127 orphan `automation_test_id` references found** in TMS case files that point to tests that don't exist in the automation codebase.

## All 127 Orphan Refs Categorized

### ARTIFACTS (1 ref)

1. **ELITEA-1814** - `tests.ui.artifacts.test_artifacts_bucket_name_validation_invalid_formats.TestArtifactBucketNameValidationInvalidFormats.test_bucket_name_validation_rejects_invalid_format`
   - **Analysis:** Base test exists; this is likely a parameterized variant that wasn't added

### CHAT - Agent & Starters (5 refs)

2. **ELITEA-2093** - `tests.ui.chat.test_agent_hub_create_conversation_via_starter.TestAgentHubCreateConversationViaStarter.test_agent_hub_create_conversation_via_starter`
3. **ELITEA-2465** - `tests.ui.chat.test_chat_agent_starters_add_remove.TestChatAddAgentWithStartersAndSendViaStarter.test_add_agent_with_starters_and_send_via_starter`
4. **ELITEA-2177** - `tests.ui.chat.test_chat_agent_starters_add_remove.TestChatAddAgentWithStartersToConversation.test_add_agent_with_starters_to_conversation`
5. **ELITEA-2178** - `tests.ui.chat.test_chat_agent_starters_add_remove.TestChatRemoveAgentClearsConversationStarters.test_remove_agent_clears_conversation_starters`
6. **ELITEA-2074** - `tests.ui.chat.test_generated_echo_agent_save_close_and_starters.TestGeneratedEchoAgentSaveCloseAndStarters.test_save_close_and_use_generated_starters`

### CHAT - File Attachments (5 refs)

7. **ELITEA-2195** - `tests.ui.chat.test_attach_files_10_left_counter.TestAttachFiles10LeftCounter.test_attach_files_menuitem_shows_10_left_counter`
8. **ELITEA-2199** - `tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_attach_files_of_different_types_shows_identical_icon_and_long_filename_truncates`
9. **ELITEA-2198** - `tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_attach_files_then_remove_two_individually_sequentially`
10. **ELITEA-2196** - `tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_attach_multiple_files_displays_chips_above_composer`
11. **ELITEA-2467** - `tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_long_filename_truncates_and_overflow_indicator_click_expands`
12. **ELITEA-2201** - `tests.ui.chat.test_send_message_with_attachments_verify_included.TestSendMessageWithAttachmentsVerifyIncluded.test_send_message_with_attachments_verify_included`

### CHAT - Build With AI & Canvas (6 refs)

13. **ELITEA-2073** - `tests.ui.chat.test_build_with_ai_cancel_then_generate_echo_agent.TestBuildWithAICancelThenGenerateEchoAgent.test_cancel_then_generate_creates_echo_agent_in_canvas`
14. **ELITEA-2089** - `tests.ui.chat.test_chat_canvas_edit_agent.TestChatCanvasEditAgent.test_edit_agent_welcome_message_syncs_to_agents_section`
15. **ELITEA-2081** - `tests.ui.chat.test_close_toolkit_canvas_without_saving.TestCloseToolkitCanvasWithoutSaving.test_close_toolkit_canvas_without_saving_creates_no_toolkit`
16. **ELITEA-2083** - `tests.ui.chat.test_create_toolkit_from_conversation.TestCreateToolkitFromConversation.test_create_toolkit_from_conversation_close_canvas_and_verify_participant`
17. **ELITEA-2084** - `tests.ui.chat.test_create_mcp_from_conversation_discard_changes.TestCreateMcpFromConversationDiscardChanges.test_create_mcp_from_conversation_discard_changes_creates_no_mcp`
18. **ELITEA-2091** - `tests.ui.chat.test_create_new_conversation_team_project_attachments_and_llm.TestCreateNewConversationTeamProjectAttachmentsAndLLM.test_create_conversation_team_project_attachments_and_llm`

### CHAT - Folder Management (18 refs)

19. **ELITEA-2134** - `tests.ui.chat.test_chat_folder_creation_custom_name_and_cancel.TestChatFolderCreationCustomNameAndCancel.test_cancel_folder_creation_discards_folder`
20. **ELITEA-2457** - `tests.ui.chat.test_chat_folder_creation_custom_name_and_cancel.TestChatFolderCreationCustomNameAndCancel.test_create_folder_with_custom_name`
21. **ELITEA-2122** - `tests.ui.chat.test_chat_folder_rename_checkmark_validation.TestChatFolderRenameCheckmarkValidation.test_folder_rename_cancel_via_x_icon_discards_changes`
22. **ELITEA-2131** - `tests.ui.chat.test_chat_folder_rename_checkmark_validation.TestChatFolderRenameCheckmarkValidation.test_folder_rename_no_changes_close_via_x_icon`
23. **ELITEA-2121** - `tests.ui.chat.test_chat_folder_rename_checkmark_validation.TestChatFolderRenameCheckmarkValidation.test_folder_rename_via_context_menu_edit_option`
24. **ELITEA-2130** - `tests.ui.chat.test_chat_folder_rename_checkmark_validation.TestChatFolderRenameCheckmarkValidation.test_pinned_folder_rename_retains_pin_state`
25. **ELITEA-2128** - `tests.ui.chat.test_chat_folder_rename_length_boundaries.TestChatFolderRenameLengthBoundaries.test_rename_folder_length_boundary_50_chars_accepted`
26. **ELITEA-2129** - `tests.ui.chat.test_chat_folder_rename_length_boundaries.TestChatFolderRenameLengthBoundaries.test_rename_folder_type_and_paste_beyond_max_length_truncates`
27. **ELITEA-2118** - `tests.ui.chat.test_folder_creation.TestChatFolderCreation.test_create_folder_default_name_checkmark_active`
28. **ELITEA-2460** - `tests.ui.chat.test_folder_list_scrollability_and_expand_states.TestFolderDisplaysConversationsOrEmptyState.test_folder_displays_conversations_or_empty_state`
29. **ELITEA-2146** - `tests.ui.chat.test_folder_list_scrollability_and_expand_states.TestFolderListScrollableWhenManyFoldersExist.test_folder_list_scrollable_when_many_folders_exist`
30. **ELITEA-2147** - `tests.ui.chat.test_folder_list_scrollability_and_expand_states.TestMoveToSubmenuFolderListScrollable.test_move_to_submenu_folder_list_scrollable`
31. **ELITEA-2137** - `tests.ui.chat.test_move_conversation_to_folder.TestMoveConversationToExistingFolder.test_move_conversation_to_new_folder`
32. **ELITEA-2138** - `tests.ui.chat.test_move_conversation_to_folder.TestMoveConversationToNewFolder.test_move_conversation_to_new_folder_with_custom_name`
33. **ELITEA-2140** - `tests.ui.chat.test_move_conversation_to_folder.TestMoveConversationBackToList.test_move_conversation_back_to_list`
34. **ELITEA-2141** - `tests.ui.chat.test_move_conversation_to_folder.TestMoveConversationBetweenTwoFolders.test_move_conversation_between_two_folders`
35. **ELITEA-2098** - `tests.ui.chat.test_open_conversation_from_folder.TestOpenExistingConversationFromFolder.test_open_existing_conversation_from_folder`
36. **ELITEA-2115** - `tests.ui.chat.test_conversation_deletion_inside_folder.TestConversationDeletionInsideFolder.test_delete_conversation_inside_folder_preserves_folder`

### CHAT - Conversation Renaming (18 refs)

37. **ELITEA-2099** - `tests.ui.chat.test_conversation_rename_basic_via_edit_option.TestConversationRenameBasicViaEditOption.test_rename_conversation_basic_via_edit_option`
38. **ELITEA-2100** - `tests.ui.chat.test_conversation_rename_cancel_discards_changes.TestConversationRenameCancelDiscardsChanges.test_rename_conversation_cancel_discards_changes`
39. **ELITEA-2109** - `tests.ui.chat.test_conversation_rename_checkmark_active_state.TestConversationRenameCheckmarkActiveState.test_rename_checkmark_activates_at_three_characters`
40. **ELITEA-2105** - `tests.ui.chat.test_conversation_rename_checkmark_active_state.TestConversationRenameCheckmarkActiveState.test_rename_checkmark_inactive_click_has_no_effect[ELITEA-2105-no-changes]`
41. **ELITEA-2106** - `tests.ui.chat.test_conversation_rename_checkmark_active_state.TestConversationRenameCheckmarkActiveState.test_rename_checkmark_inactive_click_has_no_effect[ELITEA-2106-empty-field]`
42. **ELITEA-2107** - `tests.ui.chat.test_conversation_rename_checkmark_active_state.TestConversationRenameCheckmarkActiveState.test_rename_checkmark_inactive_click_has_no_effect[ELITEA-2107-1-char]`
43. **ELITEA-2108** - `tests.ui.chat.test_conversation_rename_checkmark_active_state.TestConversationRenameCheckmarkActiveState.test_rename_checkmark_inactive_click_has_no_effect[ELITEA-2108-2-char]`
44. **ELITEA-2110** - `tests.ui.chat.test_conversation_rename_invalid_chars_and_recovery.TestConversationRenameInvalidCharsAndRecovery.test_rename_checkmark_inactive_for_invalid_input_shows_tooltip[ELITEA-2110-special-characters]`
45. **ELITEA-2111** - `tests.ui.chat.test_conversation_rename_invalid_chars_and_recovery.TestConversationRenameInvalidCharsAndRecovery.test_rename_checkmark_inactive_for_invalid_input_shows_tooltip[ELITEA-2111-dollar-percent-at-characters]`
46. **ELITEA-2112** - `tests.ui.chat.test_conversation_rename_invalid_chars_and_recovery.TestConversationRenameInvalidCharsAndRecovery.test_rename_checkmark_inactive_for_invalid_input_shows_tooltip[ELITEA-2112-leading-space]`
47. **ELITEA-2113** - `tests.ui.chat.test_conversation_rename_invalid_chars_and_recovery.TestConversationRenameInvalidCharsAndRecovery.test_rename_recovers_and_saves_after_invalid_value_replaced`
48. **ELITEA-2101** - `tests.ui.chat.test_conversation_rename_length_boundaries.TestConversationRenameLengthBoundaries.test_rename_conversation_length_boundary[ELITEA-2101-49-chars]`
49. **ELITEA-2102** - `tests.ui.chat.test_conversation_rename_length_boundaries.TestConversationRenameLengthBoundaries.test_rename_conversation_length_boundary[ELITEA-2102-50-chars]`
50. **ELITEA-2104** - `tests.ui.chat.test_conversation_rename_length_boundaries.TestConversationRenameLengthBoundaries.test_rename_conversation_paste_beyond_max_length_truncates`
51. **ELITEA-2103** - `tests.ui.chat.test_conversation_rename_length_boundaries.TestConversationRenameLengthBoundaries.test_rename_conversation_type_beyond_max_length_truncates`
52. **ELITEA-2116** - `tests.ui.chat.test_delete_confirmation_modal_ui_validation.TestDeleteConfirmationModalUIValidation.test_delete_confirmation_modal_dismisses_via_escape_and_outside_click`
53. **ELITEA-2116** - `tests.ui.chat.test_delete_confirmation_modal_ui_validation.TestDeleteConfirmationModalUIValidation.test_delete_confirmation_modal_title_body_and_button_styling` (duplicate case ID)
54. **ELITEA-2117** - `tests.ui.chat.test_last_remaining_conversation_deletion.TestLastRemainingConversationDeletion.test_delete_last_remaining_conversation_shows_welcome_state`

### CHAT - Drag & Drop (3 refs)

55. **ELITEA-2145** - `tests.ui.chat.test_drag_drop_conversation_folder.TestDragDropConversationBackToGeneralList.test_drag_drop_conversation_back_to_general_list`
56. **ELITEA-2142** - `tests.ui.chat.test_drag_drop_conversation_folder.TestDragDropConversationToFolder.test_drag_drop_conversation_to_folder`
57. **ELITEA-2143** - `tests.ui.chat.test_drag_drop_conversation_folder.TestDragDropHighlightsTargetFolderOnHover.test_drag_drop_highlights_target_folder_on_hover`

### CHAT - Hash Search & Participants (7 refs)

58. **ELITEA-2469** - `tests.ui.chat.test_chat_interface.TestHashSearch.test_add_agent_via_hash_search_joins_participants_and_responds`
59. **ELITEA-2470** - `tests.ui.chat.test_chat_interface.TestHashSearch.test_add_pipeline_via_hash_search_joins_participants_and_responds`
60. **ELITEA-2206** - `tests.ui.chat.test_chat_interface.TestHashSearch.test_hash_search_shows_agents_and_pipelines_from_all_sources`
61. **ELITEA-2176** - `tests.ui.chat.test_invite_users_add_cancel_close.TestCancelAddUsersModalAfterPreselectingUsers.test_cancel_after_preselecting_two_users_adds_no_one`
62. **ELITEA-2175** - `tests.ui.chat.test_invite_users_add_cancel_close.TestRemovePreselectedUserViaChipX.test_remove_preselected_user_via_chip_x`
63. **ELITEA-2192** - `tests.ui.chat.test_owner_has_no_remove_control_in_users_dropdown.TestOwnerHasNoRemoveControlInUsersDropdown.test_owner_has_no_remove_control_in_users_dropdown`
64. **ELITEA-2173** - `tests.ui.chat.test_participants_dropdown_click_name_inserts_mention.TestParticipantsDropdownClickNameInsertsMention.test_click_participant_name_inserts_mention[ELITEA-2173-single-mention]`
65. **ELITEA-2174** - `tests.ui.chat.test_participants_dropdown_click_name_inserts_mention.TestParticipantsDropdownClickNameInsertsMention.test_click_participant_name_inserts_mention[ELITEA-2174-two-mentions]`

### CHAT - Pinning (11 refs)

66. **ELITEA-2461** - `tests.ui.chat.test_pin_conversation.TestChatPanelOrderingPinnedFoldersAndConversations.test_pinned_folder_and_conversation_render_above_unpinned_panel_order`
67. **ELITEA-2160** - `tests.ui.chat.test_pin_conversation.TestMultipleConversationsPinnedIndependently.test_pin_two_conversations_independently`
68. **ELITEA-2158** - `tests.ui.chat.test_pin_conversation.TestPinDisabledInFolderThenMovedAndPinned.test_pin_disabled_in_folder_then_moved_and_pinned`
69. **ELITEA-2150** - `tests.ui.chat.test_pin_conversation.TestUnpinConversationViaContextMenu.test_unpin_conversation_via_context_menu`
70. **ELITEA-2161** - `tests.ui.chat.test_pin_folder.TestMultipleFoldersPinnedIndependently.test_pin_two_folders_independently`
71. **ELITEA-2155** - `tests.ui.chat.test_pin_folder.TestPinFolderViaPinOnTop.test_pin_empty_folder_retains_empty_state`
72. **ELITEA-2462** - `tests.ui.chat.test_pin_folder.TestPinFolderViaPinOnTop.test_pin_folder_via_pin_on_top`
73. **ELITEA-2154** - `tests.ui.chat.test_pin_folder.TestPinFolderViaPinOnTop.test_pin_folder_with_multiple_conversations_retains_all`
74. **ELITEA-2156** - `tests.ui.chat.test_pin_folder.TestUnpinFolderViaContextMenu.test_unpin_empty_folder_retains_empty_state`
75. **ELITEA-2153** - `tests.ui.chat.test_pin_folder.TestUnpinFolderViaContextMenu.test_unpin_folder_via_context_menu`

### CHAT - Pipelines in Chat (3 refs)

76. **ELITEA-2077** - `tests.ui.chat.test_pipeline_create_save_basic_configuration.TestPipelineCreateSaveBasicConfiguration.test_create_pipeline_save_basic_configuration`
77. **ELITEA-2076** - `tests.ui.chat.test_pipeline_discard_changes_clears_canvas.TestPipelineDiscardChangesClearsCanvas.test_discard_clears_canvas_and_creates_no_pipeline`
78. **ELITEA-2078** - `tests.ui.chat.test_pipeline_flow_editor_discard_llm_node.TestPipelineFlowEditorDiscardLlmNode.test_add_llm_node_discard_changes_removes_node`

### CHAT - Search & Context (6 refs)

79. **ELITEA-2164** - `tests.ui.chat.test_chat_search_and_modules_panel.TestChatSearchAndModulesPanel.test_search_cleared_by_x_icon_restores_default_view`
80. **ELITEA-2165** - `tests.ui.chat.test_chat_search_and_modules_panel.TestChatSearchAndModulesPanel.test_search_input_cleared_by_deleting_text_updates_dynamically`
81. **ELITEA-2163** - `tests.ui.chat.test_chat_search_and_modules_panel.TestChatSearchAndModulesPanel.test_search_no_results_state`
82. **ELITEA-2217** - `tests.ui.chat.test_context_auto_summarization_disabled.TestContextAutoSummarizationDisabled.test_no_summarization_when_auto_summarization_disabled`
83. **ELITEA-2216** - `tests.ui.chat.test_context_management_disabled.TestContextManagementDisabledWidgetStaysZero.test_context_management_disabled_widget_stays_at_zero`

### CHAT - Misc UI Features (7 refs)

84. **ELITEA-2188** - `tests.ui.chat.test_public_conversation_green_icon.TestPublicConversationGreenIcon.test_public_conversation_shows_green_icon_in_chat_list`
85. **ELITEA-2187** - `tests.ui.chat.test_regenerate_response.TestRegenerateResponse.test_regenerate_only_on_last_and_click_triggers_new_generation`
86. **ELITEA-2185** - `tests.ui.chat.test_regenerate_response.TestRegenerateResponse.test_regenerate_replaces_response_with_new_generation`
87. **ELITEA-2184** - `tests.ui.chat.test_regenerate_response.TestRegenerateResponse.test_regenerate_visible_only_on_last_response`
88. **ELITEA-2468** - `tests.ui.chat.test_slash_mention_mcp_selection_and_available_tools.TestSlashMentionMcpSelectionAndAvailableTools.test_select_mcp_from_slash_mention_no_tools_shows_empty_panel`
89. **ELITEA-2468** - `tests.ui.chat.test_slash_mention_mcp_selection_and_available_tools.TestSlashMentionMcpSelectionAndAvailableTools.test_select_mcp_from_slash_mention_shows_its_tools` (duplicate case ID)
90. **ELITEA-2466** - `tests.ui.chat.test_streaming_response.TestStreamingResponse.test_composer_send_button_toggles_with_empty_input_and_waveform_reappears`

### HELP CENTER (10 refs)

91. **ELITEA-2220** - `tests.ui.help_center.test_help_center_resource_links.TestHelpCenterResourceLinks.test_resource_card_link_redirects_to_external_page[ELITEA-2220-documentation-getting-started]`
92. **ELITEA-2221** - `tests.ui.help_center.test_help_center_resource_links.TestHelpCenterResourceLinks.test_resource_card_link_redirects_to_external_page[ELITEA-2221-release-notes-latest]`
93. **ELITEA-2222** - `tests.ui.help_center.test_help_center_resource_links.TestHelpCenterResourceLinks.test_resource_card_link_redirects_to_external_page[ELITEA-2222-tutorials-how-to-create-an-agent]`
94. **ELITEA-2224** - `tests.ui.help_center.test_help_center_resource_links.TestHelpCenterResourceLinks.test_resource_card_link_redirects_to_external_page[ELITEA-2224-tutorials-more]`
95. **ELITEA-2223** - `tests.ui.help_center.test_help_center_resource_links.TestHelpCenterResourceLinks.test_video_library_more_redirects_to_external_portal`
96. **ELITEA-2230** - `tests.ui.help_center.test_help_center_sidebar_tour.TestHelpCenterSidebarTourExtras.test_sidebar_interactive_tour_back_returns_to_step_one`
97. **ELITEA-2228** - `tests.ui.help_center.test_help_center_sidebar_tour.TestHelpCenterSidebarTourExtras.test_sidebar_interactive_tour_restarts_after_completion`
98. **ELITEA-2229** - `tests.ui.help_center.test_help_center_sidebar_tour.TestHelpCenterSidebarTourExtras.test_sidebar_interactive_tour_skip_terminates`
99. **ELITEA-2226** - `tests.ui.help_center.test_help_center_sidebar_tour.TestHelpCenterSidebarTourExtras.test_sidebar_interactive_tour_starts_on_link_click`
100. **ELITEA-2225** - `tests.ui.help_center.test_help_center_version_info.TestHelpCenterVersionInfo.test_version_info_tooltip_displays_and_copies`

### ONBOARDING (1 ref)

101. **ELITEA-2231** - `tests.ui.onboarding.test_onboarding_welcome.TestOnboardingWelcomePage.test_welcome_page_displayed_on_first_login`

### SETTINGS (1 ref)

102. **ELITEA-2392** - `tests.ui.settings.test_ai_providers_page_sections_load_without_error.TestAIProvidersPageSections.test_ai_providers_page_sections_load_without_error_test`
   - **Analysis:** Actual test exists as `test_ai_providers_page_sections_load_without_error` (no `_test` suffix)

### SKILLS (23 refs)

#### Agent-Skill Interaction (6 refs)

103. **ELITEA-2601** - `tests.ui.skills.test_agent_skills_validation_attribution_and_token_invalidation.TestAgentSkillsValidationAttributionAndTokenInvalidation.test_agent_skills_validation_attribution_and_token_invalidation`
104. **ELITEA-2600** - `tests.ui.skills.test_agent_with_skills_publishing_flow.TestAgentWithSkillsPublishingFlow.test_agent_with_skills_publishing_flow`
105. **ELITEA-2607** - `tests.ui.skills.test_skill_agent_interaction.TestInteractWithSkillsFromAgent.test_skill_autonomous_invocation_thought_process_and_security`
106. **ELITEA-2609** - `tests.ui.skills.test_skill_agent_interaction.TestInteractWithSkillsFromAgent.test_skill_explicit_and_autonomous_invocation_coexistence`
107. **ELITEA-2610** - `tests.ui.skills.test_skill_agent_version_selection_behavior.TestSkillAgentVersionSelectionBehavior.test_skill_version_selection_drives_agent_chat_behavior`
108. **ELITEA-2608** - `tests.ui.skills.test_subagent_skills_isolation.TestSubagentSkillsIsolation.test_subagent_uses_only_its_own_attached_skill`

#### Build With AI (8 refs)

109. **ELITEA-1996** - `tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAIBackToPromptFromReviewStep.test_back_to_prompt_returns_to_input_step_and_preserves_prompt_text`
110. **ELITEA-1997** - `tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAICancelFromPromptStep.test_cancel_from_prompt_step_closes_modal_without_creating_skill`
111. **ELITEA-1998** - `tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAICancelFromReviewStep.test_cancel_from_review_step_does_not_create_skill`
112. **ELITEA-2000** - `tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAICreationFailureRecovery.test_creation_failure_stays_on_review_step_and_retry_succeeds`
113. **ELITEA-1992** - `tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAIGeneratedNameNamingRules.test_generated_skill_name_adheres_to_naming_rules`
114. **ELITEA-1994** - `tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAIReviewFormCharacterLimits.test_review_form_field_character_limit_is_enforced[ELITEA-1994-description`
115. **ELITEA-1995** - `tests.ui.skills.test_skill_build_with_ai.TestSkillBuildWithAIReviewFormCharacterLimits.test_review_form_field_character_limit_is_enforced[ELITEA-1995-instructions`
116. **ELITEA-1986** - `tests.ui.skills.test_skill_build_with_ai_role_visibility.TestSkillBuildWithAIButtonRoleVisibility.test_build_with_ai_button_visible_for_admin_role`

#### Edit With AI (4 refs)

117. **ELITEA-2611** - `tests.ui.skills.test_skill_edit_with_ai_happy_path.TestSkillEditWithAIHappyPath.test_edit_with_ai_happy_path`
118. **ELITEA-2612** - `tests.ui.skills.test_skill_edit_with_ai_navigation_error_handling.TestSkillEditWithAINavigationErrorHandling.test_edit_with_ai_navigation_and_error_handling`
119. **ELITEA-2613** - `tests.ui.skills.test_skill_edit_with_ai_role_visibility.TestSkillEditWithAICharacterLimit.test_edit_with_ai_summary_instructions_truncates_at_character_limit`
120. **ELITEA-2613** - `tests.ui.skills.test_skill_edit_with_ai_role_visibility.TestSkillEditWithAIRoleVisibility.test_edit_with_ai_button_visible_for_admin_role` (duplicate case ID)

#### Publishing (5 refs)

121. **ELITEA-2614** - `tests.ui.skills.test_published_agent_version_cannot_be_modified.TestPublishedAgentVersionCannotBeModified.test_published_agent_version_cannot_be_modified`
122. **ELITEA-2596** - `tests.ui.skills.test_skill_publish_ai_validation_blockers.TestSkillPublishAiValidationBlockers.test_short_content_placeholder_and_secrets_block_publish`
123. **ELITEA-2597** - `tests.ui.skills.test_skill_publish_token_invalidation_and_ttl.TestSkillPublishTokenInvalidationAndTTL.test_publish_token_expires_after_ttl`
124. **ELITEA-2597** - `tests.ui.skills.test_skill_publish_token_invalidation_and_ttl.TestSkillPublishTokenInvalidationAndTTL.test_publish_token_invalidated_by_modification` (duplicate case ID)
125. **ELITEA-2598** - `tests.ui.skills.test_skill_publish_warn_status_allows_publishing.TestSkillPublishWarnStatusAllowsPublishing.test_warn_status_does_not_block_publish`
126. **ELITEA-2595** - `tests.ui.skills.test_skill_publish_wizard_happy_path.TestSkillPublishWizardHappyPath.test_publish_skill_happy_path`
127. **ELITEA-2599** - `tests.ui.skills.test_skill_unpublish_republish_lifecycle.TestSkillUnpublishRepublishLifecycle.test_unpublish_republish_lifecycle`

---

## Key Patterns

1. **Large batch efforts never completed:**
   - Conversation folder management (18 refs)
   - Conversation renaming (18 refs)
   - Pinning (11 refs)

2. **Duplicate Case IDs:**
   - ELITEA-2116 (2 refs)
   - ELITEA-2468 (2 refs)
   - ELITEA-2597 (2 refs)
   - ELITEA-2613 (2 refs)

3. **Parameterized tests referenced without params:**
   - ELITEA-1814, ELITEA-2392

4. **Entire feature areas missing:**
   - Help Center (all 10 refs)
   - Skills Build/Edit with AI (17 refs)
   - Onboarding (1 ref)

---

## Recommended Next Steps

1. **Review with team:** Were these tests planned but never created, or renamed/deleted?
2. **Clean TMS case files:** Remove invalid `automation_test_id` entries
3. **Update case status:** Set `execution_type: manual` or `status: draft` for non-automated cases
4. **Rebuild TMS index:** Run `build-index` after cleanup
5. **Regenerate dashboard:** Corrected coverage metrics

