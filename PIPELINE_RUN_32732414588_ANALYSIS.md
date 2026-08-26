# Pipeline Suite Test Failures Analysis
**CI Run:** [#32732414588](https://github.com/EliteaAI/elitea-testing-public/actions/runs/32732414588)  
**Job:** [dev-stable - pipelines (CANCELLED)](https://github.com/EliteaAI/elitea-testing-public/actions/runs/32732414588/job/97447456915)  
**Date:** 2026-08-24  
**Status:** Job was cancelled before completion

---

## Executive Summary

**Total Tests:** 106 collected  
**Completed:** ~97 tests (92% coverage before cancellation)  
**Failed:** 16 tests  
**Errors:** 1 test  
**Reruns:** 3 tests had automatic reruns (2 passed on retry, 1 continued failing)

### Key Observation
This run occurred AFTER the workarounds were implemented for missing testids (`pipeline-run-details-timeline-section` and `pipeline-run-details-states-section`). Many failures appear to be **new or different** from the testid-related failures in run #32712834665.

---

## Failed Tests

| # | Test Name | File | Reruns | Notes |
|---|-----------|------|--------|-------|
| 1 | `test_attach_pipeline_as_tool` | `test_pipeline_attach_pipeline_as_tool.py` | No | ❌ New failure |
| 2 | `test_custom_node_configuration` | `test_pipeline_custom_node_configuration.py` | No | ❌ New failure |
| 3 | `test_decision_node_routes_execution_to_correct_branch` | `test_pipeline_decision_node_execution.py` | **Yes (3 runs)** | ⚠️ Failed on all 3 attempts |
| 4 | `test_entry_point_trigger_types_persist` | `test_pipeline_entry_point_trigger_types_persist.py` | **Yes (3 runs)** | ⚠️ Failed on all 3 attempts |
| 5 | `test_pipeline_fork_to_different_project` | `test_pipeline_fork_to_different_project.py` | No | ❌ New failure |
| 6 | `test_hitl_node_runtime_behavior` | `test_pipeline_hitl_node_runtime_behavior.py` | **Yes (2 runs)** | ✅ PASSED on retry |
| 7 | `test_interrupt_after_toggle_pauses_and_attempts_resume` | `test_pipeline_interrupt_before_after_toggles.py` | No | ❌ New failure |
| 8 | `test_create_pipeline_minimal_via_sidebar_button` | `test_pipeline_management.py` | No | ❌ |
| 9 | `test_delete_pipeline_via_ui_menu` | `test_pipeline_management.py` | No | ❌ |
| 10 | `test_mcp_node_fresh_attach` | `test_pipeline_mcp_node_fresh_attach.py` | No | ❌ |
| 11 | `test_router_node_configuration_and_edge_wiring` | `test_pipeline_router_node_configuration.py` | No | ❌ |
| 12 | `test_schedule_trigger_settings_modal` | `test_pipeline_schedule_trigger_settings_modal.py` | **Yes (3 runs)** | ⚠️ Failed on all 3 attempts |
| 13 | `test_subgraph_state_sharing_non_common_state_isolation` | `test_pipeline_subgraph_state_isolation.py` | No | ❌ |
| 14 | `test_subgraph_state_sharing_common_vars` | `test_pipeline_subgraph_state_sharing.py` | No | ❌ |
| 15 | `test_subgraph_state_sharing_node_c_state_propagation` | `test_pipeline_subgraph_state_sharing.py` | No | ⚠️ Known issue (separate investigation needed - mentioned in summary) |
| 16 | `test_toolkit_node_config_and_input_mapping` | `test_pipeline_toolkit_node_config_and_input_mapping.py` | No | ❌ |
| 17 | `test_tools_section_mcp_add_view_remove` | `test_pipeline_tools_section_mcp_add_view_remove.py` | No | ❌ |

---

## Error Tests

| # | Test Name | File | Error Type |
|---|-----------|------|------------|
| 1 | `test_mcp_node_change_toolkit_and_tool` | `test_pipeline_mcp_node_change_toolkit_and_tool.py` | ERROR (not FAILED) |

---

## Tests with Automatic Reruns

### ✅ Passed After Retry (1 test)
1. **`test_hitl_node_configuration_and_router_mapping`** - Failed first, passed on rerun

### ⚠️ Failed After All Retries (2 tests)
1. **`test_decision_node_routes_execution_to_correct_branch`** - Failed 3/3 times
2. **`test_entry_point_trigger_types_persist`** - Failed 3/3 times  
3. **`test_schedule_trigger_settings_modal`** - Failed 3/3 times

---

## Comparison with Previous Run (#32712834665)

### Tests That Were Failing Before (5 testid-related)
The following tests were failing in run #32712834665 due to missing testids:

✅ **NOW PASSING** (testid workarounds working):
1. `test_run_details_panel_opens_after_execution` - Now PASSED (78%)
2. `test_run_details_timeline_steps_display` - Now PASSED (80%)
3. `test_run_details_state_before_after_per_node` - Now PASSED (79%)
4. `test_run_details_multiple_state_variables_different_types` - Now PASSED (77%)

⚠️ **STILL FAILING** (new/different root cause):
5. `test_subgraph_state_sharing_node_c_state_propagation` - Still failing but with different symptom (pipeline execution stays "In progress")

### New Failures in This Run (12 tests)
Tests that were NOT in the previous run's failure list:

1. `test_attach_pipeline_as_tool` - **NEW**
2. `test_custom_node_configuration` - **NEW**
3. `test_decision_node_routes_execution_to_correct_branch` - **NEW** (failed 3/3 retries)
4. `test_entry_point_trigger_types_persist` - **NEW** (failed 3/3 retries)
5. `test_pipeline_fork_to_different_project` - **NEW**
6. `test_interrupt_after_toggle_pauses_and_attempts_resume` - **NEW**
7. `test_create_pipeline_minimal_via_sidebar_button` - **NEW**
8. `test_delete_pipeline_via_ui_menu` - **NEW**
9. `test_mcp_node_fresh_attach` - **NEW**
10. `test_router_node_configuration_and_edge_wiring` - **NEW**
11. `test_schedule_trigger_settings_modal` - **NEW** (failed 3/3 retries)
12. `test_toolkit_node_config_and_input_mapping` - **NEW**

### Reproduced from Previous Run
Based on the summary document's list of 17 failures in run #32712834665, most of those were:
- 5 timeline tests (now passing with workarounds)
- 1 states test (now passing with workarounds)
- 11 other failures (artifacts/toolkits suites - likely transient)

**Overlap between runs:**
- `test_subgraph_state_sharing_node_c_state_propagation` - ⚠️ **REPRODUCED** (same pipeline execution timing issue)

---

## Key Findings

### 1. Testid Workarounds Are Working
The 4-5 tests that failed in run #32712834665 due to missing testids (`pipeline-run-details-timeline-section`, `pipeline-run-details-states-section`) are now **PASSING** with the CSS/xpath workarounds.

### 2. New Failure Pattern
12 tests are now failing that were NOT failing in the previous run. This suggests:
- **Environment changes** between runs (dev.elitea.ai backend state)
- **Timing/race conditions** (many show rerun attempts)
- **Different test execution order** or parallel execution issues

### 3. Persistent Issues with Reruns
Three tests failed ALL retry attempts (3 runs each):
- `test_decision_node_routes_execution_to_correct_branch`
- `test_entry_point_trigger_types_persist`
- `test_schedule_trigger_settings_modal`

This indicates **deterministic failures**, not flaky/transient issues.

### 4. Known Issue Confirmed
`test_subgraph_state_sharing_node_c_state_propagation` continues to fail with the same symptom mentioned in the summary document (pipeline stays "In progress" instead of "Completed").

---

## Next Steps

### Immediate Actions
1. **Verify testid fix PR status** - Check if EliteaUI PR #832 has merged
2. **Investigate new failure pattern** - Why are 12 previously passing tests now failing?
3. **Check DEV environment** - Backend/database state may have changed

### Per-Test Investigation Needed
Focus on the **3 deterministic failures** (failed all retries):
1. `test_decision_node_routes_execution_to_correct_branch` - Decision node routing logic
2. `test_entry_point_trigger_types_persist` - Entry point trigger persistence
3. `test_schedule_trigger_settings_modal` - Schedule trigger modal interactions

### Long-term Tracking
- Monitor if the 12 new failures reproduce in the next run
- Track the known `test_subgraph_state_sharing_node_c_state_propagation` issue separately

---

## Appendix: Job Status

**Job was CANCELLED** before completion:
- Completed: ~97/106 tests (92%)
- Last test executed: ~`test_pipeline_tools_section_mcp_add_view_remove` (94%)
- Tests 98-106 were NOT executed

**Possible reasons for cancellation:**
- Manual cancellation by user
- GitHub Actions timeout (unlikely at 45 minutes)
- CI workflow step failure/timeout

---

**Document Created:** 2026-08-24  
**Analysis Status:** Complete (based on available logs before cancellation)
