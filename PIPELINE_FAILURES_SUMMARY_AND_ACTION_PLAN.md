# Pipeline Test Failures - Summary & Action Plan
**CI Run:** [#32732414588](https://github.com/EliteaAI/elitea-testing-public/actions/runs/32732414588)  
**Analysis Date:** 2026-08-24  
**Status:** Job cancelled at 92% completion

---

## Quick Facts

| Metric | Count |
|--------|-------|
| Total Tests | 106 |
| Completed | ~97 (92%) |
| **Failed** | **16** |
| **Errors** | **1** |
| Passed | 80 |
| Tests with reruns | 5 |
| Passed after retry | 2 |
| Failed all retries | 3 |

---

## Executive Summary

### ✅ Good News
**Testid workarounds ARE working!** The 4-5 tests that failed in previous run #32712834665 due to missing `data-testid` attributes (`pipeline-run-details-timeline-section`, `pipeline-run-details-states-section`) are now **PASSING** with the CSS/xpath workarounds implemented in `automation/pages/pipeline_detail_page.py`.

### ⚠️ Concerns
**12 NEW failures** appeared that were NOT failing in the previous run. This suggests:
- Backend/environment changes on dev.elitea.ai
- Timing/race conditions
- Test execution order issues

### 🔥 Critical Issues
**3 tests failed ALL retry attempts** (3 runs each):
1. `test_decision_node_routes_execution_to_correct_branch`
2. `test_entry_point_trigger_types_persist`
3. `test_schedule_trigger_settings_modal`

These are **deterministic failures**, not flaky/transient issues.

---

## Failed Tests Breakdown

### Category 1: Deterministic Failures (Failed All Retries) - **PRIORITY 1**

| Test | File | Retries | Screenshot Pattern |
|------|------|---------|-------------------|
| `test_decision_node_routes_execution_to_correct_branch` | `test_pipeline_decision_node_execution.py` | 3/3 FAILED | `*_FAIL_20260824_1341*.png` (3 screenshots) |
| `test_entry_point_trigger_types_persist` | `test_pipeline_entry_point_trigger_types_persist.py` | 3/3 FAILED | `*_FAIL_20260824_1345*.png`, `*_1346*.png`, `*_1346*.png` |
| `test_schedule_trigger_settings_modal` | `test_pipeline_schedule_trigger_settings_modal.py` | 3/3 FAILED | `*_FAIL_20260824_1404*.png`, `*_1405*.png`, `*_1405*.png` |

**Action Required:**
1. Review screenshots from CI artifacts
2. Reproduce locally against dev.elitea.ai
3. Investigate root cause (likely backend state/config changes)
4. File defect or fix test if expectation is wrong

---

### Category 2: Flaky But Passed on Retry - **PRIORITY 3**

| Test | File | First Attempt | Retry Result |
|------|------|---------------|--------------|
| `test_hitl_node_configuration_and_router_mapping` | `test_pipeline_hitl_node_configuration.py` | FAILED | ✅ PASSED |
| `test_entry_point_trigger_restricted_interactive_nodes` | `test_pipeline_entry_point_trigger_restricted_interactive_nodes.py` | FAILED | ✅ PASSED |

**Action Required:**
1. Monitor for recurrence in next runs
2. Add wait/stabilization if consistently flaky
3. Consider increasing timeouts for these specific tests

---

### Category 3: Single-Attempt Failures (No Retry) - **PRIORITY 2**

| # | Test | File | Screenshot |
|---|------|------|------------|
| 1 | `test_attach_pipeline_as_tool` | `test_pipeline_attach_pipeline_as_tool.py` | `*_FAIL_20260824_132930.png` |
| 2 | `test_custom_node_configuration` | `test_pipeline_custom_node_configuration.py` | `*_FAIL_20260824_133934.png` |
| 3 | `test_pipeline_fork_to_different_project` | `test_pipeline_fork_to_different_project.py` | `*_FAIL_20260824_135057.png` |
| 4 | `test_hitl_node_runtime_behavior` | `test_pipeline_hitl_node_runtime_behavior.py` | 2 screenshots: `*_1353*.png`, `*_1354*.png` |
| 5 | `test_interrupt_after_toggle_pauses_and_attempts_resume` | `test_pipeline_interrupt_before_after_toggles.py` | `*_FAIL_20260824_135617.png` |
| 6 | `test_create_pipeline_minimal_via_sidebar_button` | `test_pipeline_management.py` | `*_FAIL_20260824_135814.png` |
| 7 | `test_delete_pipeline_via_ui_menu` | `test_pipeline_management.py` | `*_FAIL_20260824_135929.png` |
| 8 | `test_mcp_node_fresh_attach` | `test_pipeline_mcp_node_fresh_attach.py` | `*_FAIL_20260824_140035.png` |
| 9 | `test_router_node_configuration_and_edge_wiring` | `test_pipeline_router_node_configuration.py` | `*_FAIL_20260824_140158.png` |
| 10 | `test_subgraph_state_sharing_non_common_state_isolation` | `test_pipeline_subgraph_state_isolation.py` | `*_FAIL_20260824_140711.png` |
| 11 | `test_subgraph_state_sharing_common_vars` | `test_pipeline_subgraph_state_sharing.py` | `*_FAIL_20260824_140719.png` |
| 12 | `test_subgraph_state_sharing_node_c_state_propagation` | `test_pipeline_subgraph_state_sharing.py` | `*_FAIL_20260824_140727.png` ⚠️ **Known issue** |
| 13 | `test_toolkit_node_config_and_input_mapping` | `test_pipeline_toolkit_node_config_and_input_mapping.py` | `*_FAIL_20260824_140811.png` |
| 14 | `test_tools_section_mcp_add_view_remove` | `test_pipeline_tools_section_mcp_add_view_remove.py` | `*_FAIL_20260824_140820.png` |

**Action Required:**
1. Reproduce each test locally
2. Check if failures are environment-specific (dev.elitea.ai vs localhost)
3. Investigate common patterns (many are node configuration/attachment tests)

---

### Category 4: Error (Not Failure) - **PRIORITY 2**

| Test | File | Type |
|------|------|------|
| `test_mcp_node_change_toolkit_and_tool` | `test_pipeline_mcp_node_change_toolkit_and_tool.py` | ERROR (exception during test collection/setup) |

**Action Required:**
1. Check test fixture/setup code
2. May be a pytest configuration issue or missing test data

---

## Comparison with Previous Run (#32712834665)

### ✅ Fixed (Previously Failing, Now Passing)
These tests were failing due to missing testids - **workarounds successful:**
1. ✅ `test_run_details_panel_opens_after_execution` - Now PASSED (78%)
2. ✅ `test_run_details_timeline_steps_display` - Now PASSED (80%)
3. ✅ `test_run_details_state_before_after_per_node` - Now PASSED (79%)
4. ✅ `test_run_details_multiple_state_variables_different_types` - Now PASSED (77%)

### ⚠️ Reproduced from Previous Run
1. `test_subgraph_state_sharing_node_c_state_propagation` - **STILL FAILING**
   - Known issue documented in `PIPELINE_SUITE_ISSUES_SUMMARY.md`
   - Symptom: Pipeline execution stays "In progress" instead of "Completed"
   - Root cause: Timing/execution issue, NOT testid-related

### 🆕 New in This Run (12 tests)
All tests in Category 3 above (single-attempt failures) are NEW - they were NOT failing in run #32712834665.

---

## Root Cause Analysis

### Likely Causes for New Failures

1. **Backend State Changes**
   - dev.elitea.ai may have been restarted or reconfigured
   - Database state may differ from previous run
   - Pipeline execution behavior may have changed

2. **Timing/Race Conditions**
   - Many tests show sensitivity to execution speed
   - Retry patterns suggest intermittent issues
   - May need longer waits for async operations

3. **Test Execution Order**
   - Parallel execution may cause resource contention
   - Test data pollution between tests
   - Shared state issues

### Test Pattern Analysis

**Most affected test categories:**
- **Node configuration tests** (7 failures): custom, decision, router, mcp, toolkit, hitl
- **Subgraph/state tests** (3 failures): state sharing, isolation
- **Pipeline management** (2 failures): create, delete
- **Trigger configuration** (2 failures): schedule, entry point

**Common thread:** Tests involving pipeline execution, node configuration, and state management.

---

## Action Plan

### Phase 1: Immediate Investigation (Priority 1) - **TODAY**

1. **Download Allure artifacts**
   ```bash
   cd /tmp && mkdir -p ci-artifacts
   gh run download 32732414588 --repo EliteaAI/elitea-testing-public --pattern "allure-results-*"
   ```

2. **Review screenshots for the 3 deterministic failures**
   - Look for UI state differences
   - Check error messages in browser console
   - Compare against expected state

3. **Check dev.elitea.ai environment status**
   - When was it last restarted?
   - Any recent backend deployments?
   - Database schema changes?

4. **Reproduce locally**
   ```bash
   cd automation
   ELITEA_URL=https://dev.elitea.ai HEADLESS=true pytest tests/ui/pipelines/test_pipeline_decision_node_execution.py::test_decision_node_routes_execution_to_correct_branch -v
   ```

### Phase 2: Systematic Testing (Priority 2) - **THIS WEEK**

1. **Reproduce all 14 single-attempt failures**
   - Against dev.elitea.ai (deployed env)
   - Against localhost:5173 (local dev server)
   - Document which environment each fails in

2. **Check for common failure patterns**
   - Grep test files for shared page objects/fixtures
   - Look for common waits/assertions
   - Check if all use same backend endpoints

3. **Review test data dependencies**
   - Do tests clean up after themselves?
   - Are there shared test data fixtures?
   - Check for test isolation issues

### Phase 3: Fixes & Prevention (Priority 3) - **NEXT SPRINT**

1. **Fix deterministic failures** (3 tests)
   - Based on root cause from Phase 1
   - Add explicit waits if timing-related
   - Update test expectations if backend changed

2. **Improve test stability** (14 tests)
   - Add retry logic for flaky operations
   - Increase timeouts where needed
   - Better error messages/logging

3. **Monitor testid workarounds**
   - Wait for EliteaUI PR #832 to merge
   - Revert workarounds once real testids deployed
   - Verify all 4-5 tests still pass with real testids

4. **Address known issue**
   - `test_subgraph_state_sharing_node_c_state_propagation`
   - Needs separate investigation per summary doc

---

## Files Created

1. **`PIPELINE_RUN_32732414588_ANALYSIS.md`** - Detailed test-by-test breakdown
2. **`PIPELINE_FAILURES_DETAILS.md`** - Error extraction from logs
3. **`PIPELINE_FAILURES_SUMMARY_AND_ACTION_PLAN.md`** - This file (actionable plan)
4. **`automation/ci-logs/pipelines-job-97447456915.log`** - Full CI job log (852 lines)

---

## Next CI Run Monitoring

### What to Watch For:
1. Do the 3 deterministic failures reproduce?
2. Do the 12 new failures still occur or were they transient?
3. Do the 4-5 testid-workaround tests still pass?
4. Overall pass rate compared to this run (80/106 = 75% vs expected ~95%)

### Success Criteria for Next Run:
- ✅ No more than 3 failures (down from 17)
- ✅ All deterministic failures fixed
- ✅ Testid-workaround tests still passing
- ✅ Overall pass rate > 95%

---

## Resources

- **CI Run:** https://github.com/EliteaAI/elitea-testing-public/actions/runs/32732414588
- **Previous Analysis:** `PIPELINE_SUITE_ISSUES_SUMMARY.md` (run #32712834665)
- **Testid Fix PR:** https://github.com/EliteaAI/EliteaUI/pull/832
- **Workaround Commits:**
  - Timeline: `5f20bceb5`
  - States: `ada49a3a1`

---

**Document Status:** Ready for review  
**Owner:** Test Automation Team  
**Next Update:** After Phase 1 investigation complete
