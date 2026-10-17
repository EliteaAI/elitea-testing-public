# Maintenance Report: ui-tests-dev-main-all

## Legend

| Icon | Resolution |
|------|------------|
| 🔴 | to_fix |
| 🟡 | to_rerun |
| 🟠 | already_in_progress |
| 🟣 | id_mapping_error |
| ⚪ | pending_analysis |
| 🟢 | passed (no failure) |

## Test Results Matrix

| Test Case | #253 | #254 | #255 | #264 | #265 | #266 | #293 | Tracking Issue |
|-----------|--------|--------|--------|--------|--------|--------|--------|----------------|
| ELITEA-0143 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2471](https://github.com/EliteaAI/elitea-testing-public/issues/2471) |
| ELITEA-0679 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟡 | [#2472](https://github.com/EliteaAI/elitea-testing-public/issues/2472) |
| ELITEA-1866 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟠 | [#2401](https://github.com/EliteaAI/elitea-testing-public/issues/2401) |
| ELITEA-2036 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2474](https://github.com/EliteaAI/elitea-testing-public/issues/2474) |
| ELITEA-2051 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2476](https://github.com/EliteaAI/elitea-testing-public/issues/2476) |
| ELITEA-2058 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2475](https://github.com/EliteaAI/elitea-testing-public/issues/2475) |
| ELITEA-2350 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2467](https://github.com/EliteaAI/elitea-testing-public/issues/2467) |
| ELITEA-2352 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2466](https://github.com/EliteaAI/elitea-testing-public/issues/2466) |
| ELITEA-2353 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2465](https://github.com/EliteaAI/elitea-testing-public/issues/2465) |
| ELITEA-2356 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2464](https://github.com/EliteaAI/elitea-testing-public/issues/2464) |
| ELITEA-2357 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2464](https://github.com/EliteaAI/elitea-testing-public/issues/2464) |
| ELITEA-2360 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2469](https://github.com/EliteaAI/elitea-testing-public/issues/2469) |
| ELITEA-2363 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2468](https://github.com/EliteaAI/elitea-testing-public/issues/2468) |
| ELITEA-2367 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2470](https://github.com/EliteaAI/elitea-testing-public/issues/2470) |
| ELITEA-2440 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟠 | [#2447](https://github.com/EliteaAI/elitea-testing-public/issues/2447) |
| ELITEA-3750 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2477](https://github.com/EliteaAI/elitea-testing-public/issues/2477) |
| ELITEA-3754 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | [#2473](https://github.com/EliteaAI/elitea-testing-public/issues/2473) |
| tests.ui.agent_hub.test_agent_hub_copy_link_from_modal.TestAgentHubCopyLinkFromModal.test_copy_link_from_modal_navigates_to_agent[chromium] | 🟢 | 🟢 | 🟢 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.agent_hub.test_agent_hub_filter_multiple_categories.TestAgentHubFilterMultipleCategories.test_agent_hub_filter_by_multiple_categories[chromium] | 🟢 | 🟢 | 🟣 | 🟢 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.agent_hub.test_agent_hub_filter_single_category.TestAgentHubFilterSingleCategory.test_agent_hub_filter_by_single_category[chromium] | 🟢 | 🟢 | 🟣 | 🟢 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.agent_hub.test_agent_hub_like_agent_list_view.TestAgentHubLikeAgentListView.test_agent_hub_like_agent_from_list_view[chromium] | 🟣 | 🟢 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.agent_hub.test_agent_hub_search_bar_filters_in_real_time.TestAgentHubSearchBarFiltersInRealTime.test_agent_hub_search_bar_filters_in_real_time[chromium] | 🟣 | 🟣 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.artifacts.test_artifacts_bucket_name_validation_invalid_formats.TestArtifactBucketNameValidationInvalidFormats.test_bucket_name_validation_rejects_invalid_format[chromium-ELITEA-1811-leading-digit] | 🟢 | 🟢 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.artifacts.test_artifacts_bucket_name_validation_invalid_formats.TestArtifactBucketNameValidationInvalidFormats.test_bucket_name_validation_rejects_invalid_format[chromium-ELITEA-1814-special-char] | 🟢 | 🟢 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.artifacts.test_artifacts_bucket_name_validation_invalid_formats.TestArtifactBucketNameValidationInvalidFormats.test_bucket_name_validation_rejects_invalid_format[chromium-ELITEA-1814-underscore] | 🟢 | 🟢 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.artifacts.test_artifacts_create_bucket_upload_file.TestArtifactCreateBucketAndUploadFile.test_create_bucket_via_form_and_upload_file_via_bucket_menu[chromium] | 🟣 | 🟢 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.artifacts.test_artifacts_duplicate_bucket_name.TestArtifactDuplicateBucketName.test_duplicate_bucket_name_is_not_allowed[chromium] | 🟢 | 🟣 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.artifacts.test_bucket_permissions_api.TestBucketPermissionsAPI.test_no_access_permission_blocks_all_api_operations[chromium] | 🟣 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.artifacts.test_bucket_permissions_api.TestBucketPermissionsAPI.test_read_only_permission_allows_get_blocks_write_operations[chromium] | 🟣 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.chat.test_agent_with_toolkit_chat.TestAgentWithToolkitInChat.test_agent_with_toolkit_executes_in_chat[chromium] | 🟣 | 🟣 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.chat.test_chat_interface.TestConversationUIElements.test_attach_files_button_sends_file_with_message[chromium] | 🟢 | 🟢 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.chat.test_image_creation.TestImageCreation.test_create_image[chromium-minimal_prompt] | 🟢 | 🟢 | 🟣 | 🟢 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.pipelines.test_pipeline_custom_node_configuration.test_custom_node_configuration[chromium] | 🟣 | 🟣 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.pipelines.test_pipeline_fork_to_different_project.TestPipelineForkToDifferentProject.test_pipeline_fork_to_different_project[chromium] | 🟣 | 🟣 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.pipelines.test_pipeline_information_section.test_pipeline_information_section[chromium] | 🟢 | 🟢 | 🟢 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.pipelines_2.test_pipeline_webhook_trigger_settings_modal.test_webhook_trigger_settings_modal[chromium] | 🟣 | 🟣 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.skills.test_skill_export_import.TestSkillExportImportNonBaseVersion.test_import_skill_non_base_version[chromium] | 🟣 | 🟣 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.skills.test_skill_test_panel_no_new_conversation.TestSkillTestPanelNoNewConversation.test_test_panel_does_not_create_new_chat_conversation[chromium] | 🟣 | 🟣 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.skills.test_skill_test_panel_version_instructions.TestSkillTestPanelVersionInstructions.test_test_panel_uses_selected_skill_version_instructions[chromium] | 🟣 | 🟣 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.support_assistant.test_support_assistant_smoke.TestSupportAssistantHistory.test_history_restore_and_continue[chromium] | 🟢 | 🟢 | 🟢 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.toolkits.test_toolkit_indicators_for_credentials.TestAgentCredentialIndicators.test_agent_credential_indicators_e2e[chromium] | 🟢 | 🟢 | 🟣 | 🟢 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.toolkits.test_toolkit_parameterized.TestChatWithToolkit.test_chat_with_toolkit[chromium-github] | 🟢 | 🟢 | 🟢 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.toolkits.test_toolkit_parameterized.TestCreateToolkit.test_create_toolkit[chromium-confluence] | 🟢 | 🟢 | 🟢 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.toolkits.test_toolkit_parameterized.TestCreateToolkit.test_create_toolkit[chromium-github] | 🟢 | 🟣 | 🟣 | 🟣 | 🟢 | 🟢 | 🟢 | - |
| tests.ui.toolkits.test_toolkit_parameterized.TestCreateToolkit.test_create_toolkit[chromium-jira] | 🟢 | 🟢 | 🟣 | 🟢 | 🟢 | 🟢 | 🟢 | - |
| **Total executed** | 260 | 260 | 260 | 260 | 260 | 260 | 251 | - |

## Summary

- **Runs Shown:** 7 (max 10)
- **Total Test Cases:** 45
- **With Tracking Issues:** 17

*Generated automatically from maintenance files*