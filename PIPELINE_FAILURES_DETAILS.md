# Pipeline Test Failures - Detailed Error Analysis
**CI Run:** [#32732414588](https://github.com/EliteaAI/elitea-testing-public/actions/runs/32732414588)  
**Date:** 2026-08-24  
**Log File:** `automation/ci-logs/pipelines-job-97447456915.log`

---

## Extraction Method

Errors extracted from full CI job log using pattern matching for:
- Test failure markers (FAILED, ERROR)
- Exception traces (TimeoutError, AssertionError)
- Screenshot captures
- Rerun markers

---

## Failed Tests with Error Details

test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:28:00.3267554Z tests/ui/pipelines/test_pipeline_agent_node_integration.py::test_agent_node_fresh_attach PASSED [ 11%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:28:28.4772714Z tests/ui/pipelines/test_pipeline_attach_files_in_chat.py::test_attach_files_in_chat PASSED [ 12%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:29:11.0370598Z tests/ui/pipelines/test_pipeline_attach_files_in_chat.py::test_attachments_toggle_persists_across_save_and_reload PASSED [ 13%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:29:31.3518143Z tests/ui/pipelines/test_pipeline_attach_pipeline_as_tool.py::test_attach_pipeline_as_tool 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:29:31.3531238Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_attach_pipeline_as_tool_FAIL_20260824_132930.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:29:57.3999419Z tests/ui/pipelines/test_pipeline_canvas_delete_node.py::test_delete_middle_node_removes_its_edges_and_persists PASSED [ 15%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:30:30.1742473Z tests/ui/pipelines/test_pipeline_canvas_zoom_and_pan.py::test_canvas_zoom_pan_and_fit_view PASSED [ 16%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:31:07.6427830Z tests/ui/pipelines/test_pipeline_canvas_zoom_and_pan.py::test_canvas_control_panel_zoom_out_interactivity_cards_size_and_auto_arrange PASSED [ 16%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:32:12.3662307Z tests/ui/pipelines/test_pipeline_chat_starters_visible_and_clickable.py::test_pipeline_chat_starters_visible_and_clickable PASSED [ 17%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:32:46.5911191Z tests/ui/pipelines/test_pipeline_code_node_configuration.py::test_code_node_configuration_and_persistence PASSED [ 18%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:34:00.6442002Z tests/ui/pipelines/test_pipeline_code_node_elitea_client_user_info.py::test_code_node_elitea_client_user_info PASSED [ 19%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:35:20.8044134Z tests/ui/pipelines/test_pipeline_code_node_input_filtering.py::test_code_node_input_filtering_selective_state_access PASSED [ 20%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:36:18.5249232Z tests/ui/pipelines/test_pipeline_code_node_multi_var_dict_return.py::test_code_node_return_dict_multiple_state_vars PASSED [ 21%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:37:19.0393940Z tests/ui/pipelines/test_pipeline_code_node_reads_state_variable.py::test_code_node_reads_elitea_state_variable PASSED [ 22%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:37:31.6060540Z tests/ui/pipelines/test_pipeline_collapse_left_panel.py::test_collapse_and_expand_left_configuration_panel PASSED [ 23%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:38:31.9997985Z tests/ui/pipelines/test_pipeline_create_full_details_persist.py::test_create_pipeline_full_details_persist_after_reload PASSED [ 24%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:39:19.7893367Z tests/ui/pipelines/test_pipeline_create_version.py::test_create_pipeline_version_save_list_switch_preserves_canvas_state PASSED [ 25%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:39:35.9490773Z tests/ui/pipelines/test_pipeline_custom_node_configuration.py::test_custom_node_configuration 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:39:35.9492549Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_custom_node_configuration_FAIL_20260824_133934.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:40:02.5025019Z tests/ui/pipelines/test_pipeline_dashboard_pin_to_top.py::test_pipeline_dashboard_pin_to_top PASSED [ 27%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:40:42.0863331Z tests/ui/pipelines/test_pipeline_decision_node_configuration.py::test_decision_node_configuration_and_edge_wiring PASSED [ 28%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:41:41.7445816Z tests/ui/pipelines/test_pipeline_decision_node_execution.py::test_decision_node_routes_execution_to_correct_branch 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:41:41.7446846Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_decision_node_routes_execution_to_correct_branch_FAIL_20260824_134135.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:41:41.7450844Z RERUN [ 29%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:42:43.1604723Z tests/ui/pipelines/test_pipeline_decision_node_execution.py::test_decision_node_routes_execution_to_correct_branch 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:42:43.1606516Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_decision_node_routes_execution_to_correct_branch_FAIL_20260824_134236.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:42:43.1610600Z RERUN [ 29%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:43:37.4757792Z tests/ui/pipelines/test_pipeline_decision_node_execution.py::test_decision_node_routes_execution_to_correct_branch 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:43:37.4759428Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_decision_node_routes_execution_to_correct_branch_FAIL_20260824_134336.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:44:01.4534739Z tests/ui/pipelines/test_pipeline_delete_version.py::test_delete_pipeline_version_falls_back_to_base PASSED [ 30%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:44:17.7989481Z tests/ui/pipelines/test_pipeline_edge_creation.py::test_drag_connect_creates_edge_replacing_prior_transition PASSED [ 31%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:44:30.9489468Z tests/ui/pipelines/test_pipeline_edge_deletion.py::test_delete_edge_resets_source_transition_and_persists PASSED [ 32%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:45:04.0834391Z tests/ui/pipelines/test_pipeline_entry_point_trigger_restricted_interactive_nodes.py::test_entry_point_trigger_restricted_interactive_nodes 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:45:04.0836404Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_entry_point_trigger_restricted_interactive_nodes_FAIL_20260824_134457.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:45:04.0840640Z RERUN [ 33%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:45:30.5425517Z tests/ui/pipelines/test_pipeline_entry_point_trigger_restricted_interactive_nodes.py::test_entry_point_trigger_restricted_interactive_nodes PASSED [ 33%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:46:00.4402135Z tests/ui/pipelines/test_pipeline_entry_point_trigger_types_persist.py::test_entry_point_trigger_types_persist 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:46:00.4403129Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_entry_point_trigger_types_persist_FAIL_20260824_134554.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:46:00.4406005Z RERUN [ 33%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:46:33.9487582Z tests/ui/pipelines/test_pipeline_entry_point_trigger_types_persist.py::test_entry_point_trigger_types_persist 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:46:33.9488747Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_entry_point_trigger_types_persist_FAIL_20260824_134627.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:46:33.9492418Z RERUN [ 33%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:46:58.1222280Z tests/ui/pipelines/test_pipeline_entry_point_trigger_types_persist.py::test_entry_point_trigger_types_persist 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:46:58.1231059Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_entry_point_trigger_types_persist_FAIL_20260824_134656.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:47:14.9742589Z tests/ui/pipelines/test_pipeline_entry_point_trigger_types_persist.py::test_entry_point_trigger_shown_only_on_entry_point_node PASSED [ 34%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:47:35.1649364Z tests/ui/pipelines/test_pipeline_execution.py::TestExecutePipeline::test_pipeline_response_is_meaningful PASSED [ 35%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:48:08.2171810Z tests/ui/pipelines/test_pipeline_execution.py::TestExecutePipeline::test_message_count_starts_at_zero_and_grows PASSED [ 36%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:48:24.7386393Z tests/ui/pipelines/test_pipeline_execution.py::TestPipelineExecutionEdgeCases::test_empty_pipeline_execution PASSED [ 37%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:49:02.9409725Z tests/ui/pipelines/test_pipeline_execution.py::TestPipelineExecutionEdgeCases::test_navigate_away_and_reexecute PASSED [ 38%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:49:20.1758031Z tests/ui/pipelines/test_pipeline_execution.py::TestPipelineChatMessages::test_user_message_visible PASSED [ 39%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:49:55.5259251Z tests/ui/pipelines/test_pipeline_execution.py::TestPipelineChatMessages::test_multiple_executions_accumulate PASSED [ 40%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:50:46.7301307Z tests/ui/pipelines/test_pipeline_execution.py::TestExecutePipelineStreaming::test_long_response_streams_progressively PASSED [ 41%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:50:56.9733467Z tests/ui/pipelines/test_pipeline_flow_to_yaml_sync.py::test_add_node_in_flow_view_syncs_to_yaml PASSED [ 42%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:50:57.6593659Z tests/ui/pipelines/test_pipeline_fork_to_different_project.py::TestPipelineForkToDifferentProject::test_pipeline_fork_to_different_project 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:50:57.6594749Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_pipeline_fork_to_different_project_FAIL_20260824_135057.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:52:08.7111989Z tests/ui/pipelines/test_pipeline_hitl_node_configuration.py::test_hitl_node_configuration_and_router_mapping 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:52:08.7112963Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_hitl_node_configuration_and_router_mapping_FAIL_20260824_135129.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:52:08.7116049Z RERUN [ 44%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:52:28.2531554Z tests/ui/pipelines/test_pipeline_hitl_node_configuration.py::test_hitl_node_configuration_and_router_mapping PASSED [ 44%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:53:40.2003037Z tests/ui/pipelines/test_pipeline_hitl_node_runtime_behavior.py::test_hitl_node_runtime_behavior 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:53:40.2004075Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_hitl_node_runtime_behavior_FAIL_20260824_135334.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:53:40.2006284Z RERUN [ 45%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:54:16.6398797Z tests/ui/pipelines/test_pipeline_hitl_node_runtime_behavior.py::test_hitl_node_runtime_behavior 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:54:16.6401231Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_hitl_node_runtime_behavior_FAIL_20260824_135415.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:54:56.5432585Z tests/ui/pipelines/test_pipeline_import_via_file.py::test_pipeline_import_via_file PASSED [ 46%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:55:03.5398347Z tests/ui/pipelines/test_pipeline_information_section.py::test_pipeline_information_section PASSED [ 47%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:56:17.4127444Z tests/ui/pipelines/test_pipeline_interrupt_before_after_toggles.py::test_interrupt_after_toggle_pauses_and_attempts_resume 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:56:17.4129181Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_interrupt_after_toggle_pauses_and_attempts_resume_FAIL_20260824_135617.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:56:31.5774431Z tests/ui/pipelines/test_pipeline_llm_node_system_task_chat_history_config.py::test_llm_node_system_task_chat_history_config PASSED [ 49%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:56:46.5052615Z tests/ui/pipelines/test_pipeline_llm_node_system_task_chat_history_config.py::test_llm_node_system_type_walks_fixed_fstring_variable PASSED [ 50%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:57:02.7060606Z tests/ui/pipelines/test_pipeline_llm_node_system_task_chat_history_config.py::test_llm_node_config_verified_via_yaml PASSED [ 50%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:57:34.6604338Z tests/ui/pipelines/test_pipeline_llm_structured_output_state_variables.py::test_llm_structured_output_parses_into_state_variables PASSED [ 51%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:57:39.6400535Z tests/ui/pipelines/test_pipeline_management.py::TestPipelineDashboard::test_pipeline_dashboard_loads PASSED [ 52%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:57:46.0675911Z tests/ui/pipelines/test_pipeline_management.py::TestPipelineDashboard::test_pipeline_created_via_api_visible_in_dashboard PASSED [ 53%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:57:52.6211488Z tests/ui/pipelines/test_pipeline_management.py::TestPipelineDashboard::test_view_toggle_table_and_card PASSED [ 54%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:58:02.2829414Z tests/ui/pipelines/test_pipeline_management.py::TestCreatePipeline::test_create_pipeline_via_ui PASSED [ 55%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:58:09.2354725Z tests/ui/pipelines/test_pipeline_management.py::TestCreatePipeline::test_create_pipeline_required_fields_validation PASSED [ 56%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:58:14.6020174Z tests/ui/pipelines/test_pipeline_management.py::TestCreatePipeline::test_create_pipeline_minimal_via_sidebar_button 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:58:14.6022713Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_create_pipeline_minimal_via_sidebar_button_FAIL_20260824_13***4.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:58:26.2690778Z tests/ui/pipelines/test_pipeline_management.py::TestEditPipeline::test_edit_pipeline_name PASSED [ 58%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:58:38.2645240Z tests/ui/pipelines/test_pipeline_management.py::TestEditPipeline::test_edit_pipeline_description PASSED [ 59%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:58:46.2106750Z tests/ui/pipelines/test_pipeline_management.py::TestEditPipeline::test_pipeline_detail_page_loads PASSED [ 60%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:58:53.0925755Z tests/ui/pipelines/test_pipeline_management.py::TestEditPipeline::test_pipeline_has_configuration_and_history_tabs PASSED [ 61%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:59:05.7297174Z tests/ui/pipelines/test_pipeline_management.py::TestDeletePipeline::test_delete_pipeline_via_api PASSED [ 62%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:59:30.8117758Z tests/ui/pipelines/test_pipeline_management.py::TestDeletePipeline::test_delete_pipeline_via_ui_menu 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:59:30.8118738Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_delete_pipeline_via_ui_menu_FAIL_20260824_135929.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:59:39.9423882Z tests/ui/pipelines/test_pipeline_management.py::TestSearchPipeline::test_search_pipeline_by_name PASSED [ 64%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:59:51.0268878Z tests/ui/pipelines/test_pipeline_management.py::TestSearchPipeline::test_search_pipeline_no_results PASSED [ 65%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T13:59:58.9833146Z tests/ui/pipelines/test_pipeline_management.py::TestSearchPipeline::test_search_placeholder_and_dashboard_grid_filters_and_clears PASSED [ 66%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:00:04.8931662Z tests/ui/pipelines/test_pipeline_management.py::TestPipelineIsolation::test_fixture_creates_fresh_pipeline PASSED [ 66%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:00:05.3901134Z tests/ui/pipelines/test_pipeline_management.py::TestPipelineIsolation::test_fixture_cleanup_cycle PASSED [ 67%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:00:07.6749707Z tests/ui/pipelines/test_pipeline_mcp_node_change_toolkit_and_tool.py::test_mcp_node_change_toolkit_and_tool ERROR [ 68%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:00:27.2767746Z tests/ui/pipelines/test_pipeline_mcp_node_empty_toolkit_before_attach.py::test_mcp_node_empty_toolkit_before_attach PASSED [ 69%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:00:36.1518905Z tests/ui/pipelines/test_pipeline_mcp_node_fresh_attach.py::test_mcp_node_fresh_attach 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:00:36.1521245Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_mcp_node_fresh_attach_FAIL_20260824_140035.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:00:52.3164800Z tests/ui/pipelines/test_pipeline_multiple_browser_tabs.py::test_pipeline_multiple_browser_tabs PASSED [ 71%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:01:03.6550363Z tests/ui/pipelines/test_pipeline_node_auto_increment_naming.py::test_node_auto_increment_naming_by_type PASSED [ 72%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:01:13.8148748Z tests/ui/pipelines/test_pipeline_nodes.py::TestAddNode::test_add_human_in_the_loop_node_and_connect_to_end PASSED [ 73%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:01:28.0134009Z tests/ui/pipelines/test_pipeline_printer_node_configuration.py::test_printer_node_configuration_and_persistence PASSED [ 74%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:01:59.4902074Z tests/ui/pipelines/test_pipeline_router_node_configuration.py::test_router_node_configuration_and_edge_wiring 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:01:59.4903409Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_router_node_configuration_and_edge_wiring_FAIL_20260824_140158.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:02:36.6133277Z tests/ui/pipelines/test_pipeline_run_details_delete_run_from_history.py::test_run_details_delete_run_from_history PASSED [ 76%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:02:56.5731187Z tests/ui/pipelines/test_pipeline_run_details_multiple_state_variables.py::test_run_details_multiple_state_variables_different_types PASSED [ 77%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:03:13.6937502Z tests/ui/pipelines/test_pipeline_run_details_panel.py::test_run_details_panel_opens_after_execution PASSED [ 78%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:03:32.0210861Z tests/ui/pipelines/test_pipeline_run_details_state_before_after.py::test_run_details_state_before_after_per_node PASSED [ 79%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:03:50.9444384Z tests/ui/pipelines/test_pipeline_run_details_timeline_steps.py::test_run_details_timeline_steps_display PASSED [ 80%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:04:18.1185479Z tests/ui/pipelines/test_pipeline_run_history_view_executions.py::TestPipelineRunHistoryViewExecutions::test_run_history_panel_lists_and_shows_execution_details PASSED [ 81%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:04:37.7511912Z tests/ui/pipelines/test_pipeline_run_history_view_executions.py::TestPipelineRunHistoryPanelClose::test_run_history_panel_closes_and_restores_chat PASSED [ 82%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:05:04.8045967Z tests/ui/pipelines/test_pipeline_schedule_trigger_settings_modal.py::test_schedule_trigger_settings_modal 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:05:04.8047046Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_schedule_trigger_settings_modal_FAIL_20260824_140458.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:05:04.8050193Z RERUN [ 83%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:05:29.9269656Z tests/ui/pipelines/test_pipeline_schedule_trigger_settings_modal.py::test_schedule_trigger_settings_modal 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:05:29.9271303Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_schedule_trigger_settings_modal_FAIL_20260824_140523.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:05:29.9272947Z RERUN [ 83%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:05:51.1358920Z tests/ui/pipelines/test_pipeline_schedule_trigger_settings_modal.py::test_schedule_trigger_settings_modal 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:05:51.1360059Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_schedule_trigger_settings_modal_FAIL_20260824_140549.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:06:06.6243581Z tests/ui/pipelines/test_pipeline_state_modifier_node_configuration.py::test_state_modifier_node_configuration_and_persistence PASSED [ 83%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:06:17.9292220Z tests/ui/pipelines/test_pipeline_state_panel_attachments_module.py::test_state_panel_attachments_module PASSED [ 84%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:06:34.1991764Z tests/ui/pipelines/test_pipeline_state_panel_default_and_custom_variables.py::test_state_panel_default_and_custom_variables PASSED [ 85%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:06:47.9492690Z tests/ui/pipelines/test_pipeline_state_panel_default_and_custom_variables.py::test_state_panel_delete_custom_variable PASSED [ 86%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:07:04.4582376Z tests/ui/pipelines/test_pipeline_structured_output_toggle_persistence.py::test_pipeline_structured_output_toggle_persistence PASSED [ 87%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:07:11.9756990Z tests/ui/pipelines/test_pipeline_subgraph_state_isolation.py::test_subgraph_state_sharing_non_common_state_isolation 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:07:11.9760307Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_subgraph_state_sharing_non_common_state_isolation_FAIL_20260824_140711.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:07:19.5951536Z tests/ui/pipelines/test_pipeline_subgraph_state_sharing.py::test_subgraph_state_sharing_common_vars 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:07:19.5952450Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_subgraph_state_sharing_common_vars_FAIL_20260824_140719.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:07:27.6413724Z tests/ui/pipelines/test_pipeline_subgraph_state_sharing.py::test_subgraph_state_sharing_node_c_state_propagation 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:07:27.6414745Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_subgraph_state_sharing_node_c_state_propagation_FAIL_20260824_140727.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:07:55.5158254Z tests/ui/pipelines/test_pipeline_tags_add_and_filter.py::test_pipeline_tags_add_and_filter PASSED [ 91%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:08:03.8150326Z tests/ui/pipelines/test_pipeline_three_dot_menu_actions.py::test_pipeline_three_dot_menu_actions PASSED [ 92%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:08:12.0662775Z tests/ui/pipelines/test_pipeline_toolkit_node_config_and_input_mapping.py::test_toolkit_node_config_and_input_mapping 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:08:12.0664602Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_toolkit_node_config_and_input_mapping_FAIL_20260824_140811.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:08:20.8817844Z tests/ui/pipelines/test_pipeline_tools_section_mcp_add_view_remove.py::test_tools_section_mcp_add_view_remove 
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:08:20.8818998Z   [FAIL] Screenshot: /home/runner/work/elitea-testing-public/elitea-testing-public/automation/screenshots/test_tools_section_mcp_add_view_remove_FAIL_20260824_140820.png
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:08:33.6166387Z tests/ui/pipelines/test_pipeline_webhook_trigger_settings_modal.py::test_webhook_trigger_settings_modal PASSED [ 95%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:08:52.3137611Z tests/ui/pipelines/test_pipeline_welcome_message_shown_before_first_input.py::test_pipeline_welcome_message_shown_before_first_input PASSED [ 96%]
test / dev-stable - pipelines	UNKNOWN STEP	2026-08-24T14:09:02.2427131Z tests/ui/pipelines/test_pipeline_yaml_editor_invalid_syntax.py::test_yaml_editor_invalid_syntax_blocks_save PASSED [ 97%]


---

## Pattern Analysis


Since the log file is large and the CI job was cancelled, detailed error messages may be incomplete. 

### Common Error Patterns Observed:
1. **TimeoutError** - Elements not appearing within expected timeframe
2. **Screenshot captures** - Failures captured with screenshots for debugging
3. **RERUN markers** - Tests that were automatically retried

### Next Steps:
1. Download allure-results artifacts for detailed error traces
2. Review screenshots from failed tests
3. Compare error patterns across reruns

---

**Note:** For detailed stack traces and assertion details, review the allure-results artifacts which contain:
- Full exception traces
- Request/response logs
- Browser console logs
- Network captures
- Step-by-step execution logs

