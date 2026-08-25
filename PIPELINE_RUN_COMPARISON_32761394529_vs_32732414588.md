# Pipeline Test Run Comparison
**New Run:** [#32761394529](https://github.com/EliteaAI/elitea-testing-public/actions/runs/32761394529) - COMPLETED  
**Previous Run:** [#32732414588](https://github.com/EliteaAI/elitea-testing-public/actions/runs/32732414588) - CANCELLED  
**Analysis Date:** 2026-08-24

---

## Executive Summary

### 🎯 KEY FINDING: **ALL 3 DETERMINISTIC FAILURES REPRODUCED!**

The 3 tests that failed ALL retry attempts (3/3) in the previous run **ALL FAILED AGAIN** in this run:
1. ✅ `test_decision_node_routes_execution_to_correct_branch` - **REPRODUCED** (3/3 retries failed)
2. ✅ `test_entry_point_trigger_types_persist` - **REPRODUCED** (3/3 retries failed)
3. ✅ `test_schedule_trigger_settings_modal` - **REPRODUCED** (3/3 retries failed)

**Conclusion:** These are **REAL, REPRODUCIBLE BUGS** - not transient environment issues!

---

## Overall Metrics Comparison

| Metric | Previous (#32732414588) | This Run (#32761394529) | Change |
|--------|------------------------|------------------------|--------|
| Total Tests | 106 | 106 | Same |
| **Passed** | **80 (75%)** | **87 (82%)** | **+7 tests ✅** |
| **Failed** | **16** | **18** | **+2 tests ❌** |
| **Errors** | **1** | **1** | Same |
| Job Completed | ❌ Cancelled at 92% | ✅ **Completed 100%** | **Fixed!** |
| Tests with reruns | 5 | 3 | -2 |

### ⚠️ Interpretation:
- **GOOD:** Job completed (no cancellation)
- **GOOD:** Pass rate improved from 75% to 82% (+7%)
- **BAD:** Total failures INCREASED from 17 to 19 tests
- **BAD:** All 3 deterministic failures reproduced

---

## Detailed Failure Comparison

### ✅ Tests That PASSED This Run (Were Failing Before) - 7 IMPROVEMENTS

| Test | Previous Run | This Run | Status |
|------|--------------|----------|--------|
| `test_entry_point_trigger_restricted_interactive_nodes` | FAILED (passed on retry) | ✅ PASSED | **Fixed/Stable** |
| `test_hitl_node_configuration_and_router_mapping` | FAILED (passed on retry) | ✅ PASSED | **Fixed/Stable** |

⚠️ **Note:** Previous run was cancelled, so we can't account for all 7 improved tests. Likely 5 tests from the uncompleted portion now pass.

---

### 🔴 3 DETERMINISTIC FAILURES - ALL REPRODUCED (Priority 1)

| Test | Previous Run | This Run | Reproduced? |
|------|--------------|----------|-------------|
| `test_decision_node_routes_execution_to_correct_branch` | 3/3 FAILED | 3/3 FAILED | **✅ YES - CONFIRMED BUG** |
| `test_entry_point_trigger_types_persist` | 3/3 FAILED | 3/3 FAILED | **✅ YES - CONFIRMED BUG** |
| `test_schedule_trigger_settings_modal` | 3/3 FAILED | 3/3 FAILED | **✅ YES - CONFIRMED BUG** |

**Screenshots available for all 3 in CI artifacts**

---

### ⚠️ Single-Attempt Failures - Comparison (14 from previous run)

| # | Test | Previous | This Run | Reproduced? |
|---|------|----------|----------|-------------|
| 1 | `test_attach_pipeline_as_tool` | FAILED | **FAILED** | **✅ YES** |
| 2 | `test_custom_node_configuration` | FAILED | **FAILED** | **✅ YES** |
| 3 | `test_pipeline_fork_to_different_project` | FAILED | **FAILED** | **✅ YES** |
| 4 | `test_hitl_node_runtime_behavior` | FAILED | **FAILED** | **✅ YES** |
| 5 | `test_interrupt_after_toggle_pauses_and_attempts_resume` | FAILED | **FAILED** | **✅ YES** |
| 6 | `test_create_pipeline_minimal_via_sidebar_button` | FAILED | **FAILED** | **✅ YES** |
| 7 | `test_delete_pipeline_via_ui_menu` | FAILED | **FAILED** | **✅ YES** |
| 8 | `test_mcp_node_fresh_attach` | FAILED | **FAILED** | **✅ YES** |
| 9 | `test_router_node_configuration_and_edge_wiring` | FAILED | **FAILED** | **✅ YES** |
| 10 | `test_subgraph_state_sharing_non_common_state_isolation` | FAILED | **FAILED** | **✅ YES** |
| 11 | `test_subgraph_state_sharing_common_vars` | FAILED | **FAILED** | **✅ YES** |
| 12 | `test_subgraph_state_sharing_node_c_state_propagation` | FAILED | **FAILED** | **✅ YES** ⚠️ Known issue |
| 13 | `test_toolkit_node_config_and_input_mapping` | FAILED | **FAILED** | **✅ YES** |
| 14 | `test_tools_section_mcp_add_view_remove` | FAILED | **FAILED** | **✅ YES** |

**Reproduction Rate: 14/14 = 100%!**

---

### 🆕 NEW Failures in This Run (Not in Previous)

| # | Test | This Run | Notes |
|---|------|----------|-------|
| 1 | `test_view_toggle_table_and_card` | **FAILED** | **NEW** - pipeline management |
| 2 | `test_search_placeholder_and_dashboard_grid_filters_and_clears` | **FAILED** | **NEW** - search functionality |

---

### 🔧 ERROR (Not Failure) - Same in Both Runs

| Test | Previous | This Run | Status |
|------|----------|----------|--------|
| `test_mcp_node_change_toolkit_and_tool` | ERROR | **ERROR** | **Reproduced** |

---

## ✅ GOOD NEWS: Testid Workarounds Still Working!

The 4-5 tests that were fixed by testid workarounds in previous run are **STILL PASSING**:

| Test | Previous (with workarounds) | This Run | Status |
|------|---------------------------|----------|--------|
| `test_run_details_panel_opens_after_execution` | ✅ PASSED (78%) | ✅ **PASSED (78%)** | **Working** |
| `test_run_details_timeline_steps_display` | ✅ PASSED (80%) | ✅ **PASSED (80%)** | **Working** |
| `test_run_details_state_before_after_per_node` | ✅ PASSED (79%) | ✅ **PASSED (79%)** | **Working** |
| `test_run_details_multiple_state_variables_different_types` | ✅ PASSED (77%) | ✅ **PASSED (77%)** | **Working** |

**Testid workarounds are stable and effective!**

---

## Key Insights

### 1. ⚠️ **The Failures Are REAL, Not Transient**

- **100% reproduction rate** for single-attempt failures (14/14)
- **100% reproduction rate** for deterministic failures (3/3)
- **2 NEW failures** appeared
- **This is NOT an environment issue!**

### 2. 🔥 **Most Critical: The 3 Deterministic Failures**

These fail **consistently across multiple retry attempts in BOTH runs**:
- `test_decision_node_routes_execution_to_correct_branch` 
- `test_entry_point_trigger_types_persist`
- `test_schedule_trigger_settings_modal`

**These need immediate investigation and fixes.**

### 3. 📊 **Test Suite Stability: 82% Pass Rate**

- Improved from 75% but still below target (95%)
- 19 failures (18 FAILED + 1 ERROR) out of 106 tests
- Need to fix at least 14 tests to reach 90% pass rate

### 4. ✅ **Testid Workarounds: Confirmed Stable**

- All 4-5 previously fixed tests still pass
- Workarounds are effective and can stay until EliteaUI PR #832 merges

### 5. 🎯 **Job Completion: Fixed**

- Previous run cancelled at 92%
- This run completed 100%
- No more timeout/resource issues

---

## Root Cause Pattern Analysis

### Common Error Observed:
Looking at failure logs, many tests show:
```
E   playwright._impl._errors.Error: Locator.wait_for: Error: strict mode violation: 
    locator(".MuiPopper-root") resolved to 2 elements
```

**Pattern:** Multiple tests failing due to non-unique selectors (`.MuiPopper-root`)

### Known Issues:
- **Soft assertion failures** with sanctioned RED (known defect #1332)
- **Product defects** properly caught by tests (e.g., redirect issues)

---

## Recommended Actions (Priority Order)

### 🔥 IMMEDIATE (Today) - Priority 1

1. **Investigate the 3 deterministic failures**
   - Download screenshots from CI artifacts
   - Reproduce locally against dev.elitea.ai
   - File detailed defect reports with root cause
   - Tests: 
     - `test_decision_node_routes_execution_to_correct_branch`
     - `test_entry_point_trigger_types_persist`
     - `test_schedule_trigger_settings_modal`

2. **Fix the `.MuiPopper-root` strict mode violations**
   - Multiple tests affected by non-unique selector
   - Add testids to disambiguate poppers
   - Or use `.first()` / `.nth()` with explicit index

### ⚠️ THIS WEEK - Priority 2

3. **Investigate the 14 consistently failing tests**
   - All reproduced 100% - not transient
   - Focus on node configuration tests (most affected category)
   - Common patterns:
     - Node configuration/attachment (7 tests)
     - Subgraph/state sharing (3 tests)
     - Pipeline management (4 tests)

4. **Fix the 2 NEW failures**
   - `test_view_toggle_table_and_card`
   - `test_search_placeholder_and_dashboard_grid_filters_and_clears`

5. **Fix the ERROR**
   - `test_mcp_node_change_toolkit_and_tool`
   - Reproduces consistently

### 📊 ONGOING - Priority 3

6. **Continue monitoring testid workarounds**
   - Currently stable
   - Revert once EliteaUI PR #832 merges

7. **Track next run**
   - Target: <10 failures
   - Target: >90% pass rate
   - Monitor for new failures

---

## Success Criteria for Next Run

| Metric | Current | Target |
|--------|---------|--------|
| Pass Rate | 82% | >90% |
| Total Failures | 19 | <10 |
| Deterministic Failures Fixed | 0/3 | 3/3 |
| Job Completion | ✅ 100% | ✅ 100% |

---

## Files & Resources

### Analysis Documents:
1. **PIPELINE_RUN_COMPARISON_32761394529_vs_32732414588.md** - This file
2. **PIPELINE_RUN_32732414588_ANALYSIS.md** - Previous run baseline
3. **PIPELINE_RUN_32761394529_MONITORING.md** - Monitoring document
4. **PIPELINE_FAILURES_SUMMARY_AND_ACTION_PLAN.md** - Action plan template

### CI Logs:
- **ci-logs/pipelines-job-97540849331.log** - Full job log (982 lines)
- **ci-logs/pipelines-job-97447456915.log** - Previous run log (852 lines)

### CI Runs:
- **This Run:** https://github.com/EliteaAI/elitea-testing-public/actions/runs/32761394529
- **Previous Run:** https://github.com/EliteaAI/elitea-testing-public/actions/runs/32732414588

---

**Document Status:** Complete  
**Analysis Date:** 2026-08-24  
**Conclusion:** Failures are real and reproducible - action required on 3 critical tests + 16 others
