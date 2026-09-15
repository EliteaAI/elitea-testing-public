# Pipeline Test Suite Comparison

## GitHub Actions Run #32931571484 (2026-08-26 ~05:00 UTC)

### Suite: pipelines (NOT pipelines_2)
**Total Tests**: ~60 tests
**Duration**: ~27m38s
**Failed**: 3
**Passed**: ~57

### Failures in GHA pipelines suite:
1. `test_pipeline_decision_node_execution.py::test_decision_node_routes_execution_to_correct_branch`
2. `test_pipeline_entry_point_trigger_restricted_interactive_nodes.py::test_entry_point_trigger_restricted_interactive_nodes`
3. `test_pipeline_fork_to_different_project.py::TestPipelineForkToDifferentProject::test_pipeline_fork_to_different_project`

### Schedule-Related Tests Status (in pipelines suite):
✅ `test_entry_point_trigger_types_persist` - PASSED
✅ `test_entry_point_trigger_shown_only_on_entry_point_node` - PASSED

Note: `test_schedule_trigger_settings_modal` is NOT in the pipelines suite - it's in pipelines_2

---

## Local Run #1 - pipelines_2 Suite (Completed 2026-08-26 12:32 PM local)

### Suite: pipelines_2 
**Total Tests**: 55 tests
**Duration**: 1048.47s (~17.5 minutes)
**Passed**: 48 (87%)
**Failed**: 6 (11%)
**Error**: 1 (2%)

### ✅ KEY SUCCESS:
**test_schedule_trigger_settings_modal - PASSED** (our fix worked!)

### ❌ Failures in Local pipelines_2:

1. **test_create_pipeline_minimal_via_sidebar_button** (Management)
   - **Issue**: URL path mismatch - expected `/pipelines/create`, got `/app/pipelines/create`
   - **Root Cause**: APP_PREFIX difference between localhost and DEV environment
   - **Type**: Environment-specific issue

2. **test_delete_pipeline_via_ui_menu** (Management) 
   - **Issue**: Known defect #1332 - no auto-redirect to dashboard after delete
   - **Status**: Sanctioned RED (soft assertion, linked issue)
   - **Type**: Known product bug

3. **test_mcp_node_fresh_attach** (MCP)
   - **Issue**: MCP popper search input not found - expected count > 0, got 0
   - **Root Cause**: UI element not rendering or locator issue
   - **Type**: Requires investigation

4. **test_router_node_configuration_and_edge_wiring** (Router)
   - **Issue**: Known defect #1036 - default-output edge doesn't render immediately
   - **Status**: Sanctioned RED (soft assertion, linked issue)
   - **Type**: Known product bug

5. **test_subgraph_state_sharing_node_c_state_propagation** (Subgraph)
   - **Issue**: Known defect #1381 - timeline stuck at 4 steps, CODE2 node never executes
   - **Status**: Sanctioned RED (soft assertion, linked issue)
   - **Type**: Known product bug

6. **test_tools_section_mcp_add_view_remove** (MCP)
   - **Issue**: MCP popper menu items not found - expected count > 0, got 0
   - **Root Cause**: Similar to #3, MCP popper not showing toolkits
   - **Type**: Requires investigation

### ⚠️ Error:

1. **test_mcp_node_change_toolkit_and_tool**
   - **Issue**: HTTP 400 - "No such tool with id 3"
   - **Root Cause**: API call with non-existent tool ID
   - **Type**: Test data / fixture issue

---

## Analysis

### Failures by Category:

**Known Product Bugs (3)** - Sanctioned RED with linked issues:
- #1332: Delete redirect issue
- #1036: Router edge rendering
- #1381: Subgraph state propagation

**Environment Issues (1)**:
- APP_PREFIX path mismatch (localhost vs DEV)

**Requires Investigation (3)**:
- 2 MCP popper issues (search input & menu items not rendering)
- 1 API error (tool ID 3 not found)

### Success Rate:
- **pipelines_2**: 48/55 = 87% pass rate
- **Legitimate new failures**: 3 (MCP popper × 2, API error)
- **Known issues**: 3 (documented, expected)
- **Environment difference**: 1 (APP_PREFIX)

---

## Actions Completed This Session:

1. ✅ Fixed `set_schedule_hour_minute()` method for MUI Autocomplete
2. ✅ Updated test assertions to expect quoted summary text
3. ✅ Committed and pushed fix (commit 2241fb7bc)
4. ✅ Verified schedule modal test passes locally
5. ✅ Ran full pipelines_2 suite (17.5 min, 87% pass)

---

## Next Steps (In Progress):

1. ⏳ Run pipelines suite locally for comparison
2. ⏳ Run pipelines_2 suite again
3. ⏳ Compare all results with GHA run #32931571484
4. 📋 Document differences between suites and environments
5. 🔍 Investigate the 3 legitimate failures (MCP popper × 2, API error)
