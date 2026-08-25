# Pipeline Test Run Monitoring - Run #32761394529

**CI Run:** [#32761394529](https://github.com/EliteaAI/elitea-testing-public/actions/runs/32761394529)  
**Start Time:** 2026-08-24 18:15:39 UTC  
**Status:** 🔄 IN PROGRESS  
**Branch:** main  
**Trigger:** workflow_dispatch (manual)

---

## Monitoring Objective

Compare this run with previous run #32732414588 to determine:
1. Do the **3 deterministic failures** reproduce?
   - `test_decision_node_routes_execution_to_correct_branch`
   - `test_entry_point_trigger_types_persist`
   - `test_schedule_trigger_settings_modal`

2. Do the **12 new failures** still occur or were they transient?

3. Do the **4-5 testid-workaround tests** still pass?

4. Overall pass rate improvement?

---

## Previous Run (#32732414588) Baseline

| Metric | Value |
|--------|-------|
| Total Tests | 106 |
| Passed | 80 (75%) |
| Failed | 16 |
| Errors | 1 |
| Job Status | CANCELLED at 92% |
| Deterministic Failures | 3 (failed all retries) |
| Flaky (passed on retry) | 2 |

### Previous Failures Breakdown:

**Deterministic (3):**
1. `test_decision_node_routes_execution_to_correct_branch` - 3/3 failed
2. `test_entry_point_trigger_types_persist` - 3/3 failed
3. `test_schedule_trigger_settings_modal` - 3/3 failed

**Single-attempt failures (14):**
- `test_attach_pipeline_as_tool`
- `test_custom_node_configuration`
- `test_pipeline_fork_to_different_project`
- `test_hitl_node_runtime_behavior`
- `test_interrupt_after_toggle_pauses_and_attempts_resume`
- `test_create_pipeline_minimal_via_sidebar_button`
- `test_delete_pipeline_via_ui_menu`
- `test_mcp_node_fresh_attach`
- `test_router_node_configuration_and_edge_wiring`
- `test_subgraph_state_sharing_non_common_state_isolation`
- `test_subgraph_state_sharing_common_vars`
- `test_subgraph_state_sharing_node_c_state_propagation` (known issue)
- `test_toolkit_node_config_and_input_mapping`
- `test_tools_section_mcp_add_view_remove`

**ERROR (1):**
- `test_mcp_node_change_toolkit_and_tool`

---

## Live Monitoring

**Job ID:** 97540849331  
**Job URL:** https://github.com/EliteaAI/elitea-testing-public/actions/runs/32761394529/job/97540849331

### Progress Updates

| Time (UTC) | Status | Notes |
|------------|--------|-------|
| 18:15:39 | Started | Workflow dispatched manually |
| 18:15:48 | Running | Pipelines job started |
| TBD | TBD | Waiting for test execution |

---

## What to Look For

### 🔴 CRITICAL - Must Check:
1. **Do the 3 deterministic failures reproduce?**
   - If YES → Real bugs, need immediate investigation
   - If NO → Previous run had environment-specific issues

2. **Job completion status**
   - Does it complete or get cancelled again?
   - If cancelled → investigate timeout/resource issues

### ⚠️ IMPORTANT - Pattern Analysis:
3. **New failures vs transient**
   - Which of the 12 new failures reappear?
   - If most disappear → confirms transient/environment issue
   - If most reappear → systematic problem

4. **Testid workarounds**
   - Do the 4-5 previously fixed tests still pass?
   - If they fail → workarounds broke

### 📊 METRICS - Success Criteria:
5. **Pass rate**
   - Target: >95% (100+ of 106 tests)
   - Previous: 75% (80 of 106 tests)
   - Improvement threshold: >85%

6. **Total failures**
   - Target: <5 failures
   - Previous: 17 failures
   - Acceptable: <10 failures

---

## Data Collection Commands

Once run completes, execute these to collect data:

```bash
# Get final status
env -u GITHUB_TOKEN gh run view 32761394529 --repo EliteaAI/elitea-testing-public

# Download full logs
env -u GITHUB_TOKEN gh run view 32761394529 --repo EliteaAI/elitea-testing-public --job 97540849331 --log > automation/ci-logs/pipelines-job-97540849331.log

# Extract failures
grep -E "(FAILED|ERROR|test_)" automation/ci-logs/pipelines-job-97540849331.log | grep -E "FAILED|ERROR" > automation/ci-logs/run-32761394529-failures.txt

# Get test summary
grep -E "(passed.*failed|warnings summary)" automation/ci-logs/pipelines-job-97540849331.log
```

---

## Comparison Template

After run completes, fill this out:

### Deterministic Failures Reproduction

| Test | Previous Run | This Run | Reproduced? |
|------|--------------|----------|-------------|
| `test_decision_node_routes_execution_to_correct_branch` | 3/3 FAILED | TBD | TBD |
| `test_entry_point_trigger_types_persist` | 3/3 FAILED | TBD | TBD |
| `test_schedule_trigger_settings_modal` | 3/3 FAILED | TBD | TBD |

### New Failures Stability Check

| Test | Previous Run | This Run | Status |
|------|--------------|----------|--------|
| `test_attach_pipeline_as_tool` | FAILED | TBD | TBD |
| `test_custom_node_configuration` | FAILED | TBD | TBD |
| `test_pipeline_fork_to_different_project` | FAILED | TBD | TBD |
| _(etc - all 14 tests)_ | ... | ... | ... |

### Overall Metrics Comparison

| Metric | Previous (#32732414588) | This Run (#32761394529) | Change |
|--------|------------------------|------------------------|--------|
| Total Tests | 106 | TBD | TBD |
| Passed | 80 (75%) | TBD | TBD |
| Failed | 16 | TBD | TBD |
| Errors | 1 | TBD | TBD |
| Job Completed | ❌ Cancelled | TBD | TBD |

---

## Next Steps After Completion

1. **If failures improved (< 10 failures):**
   - Focus on fixing remaining failures
   - Previous run had environment issues
   - Continue with testid PR merge

2. **If failures same/worse (≥ 10 failures):**
   - Systematic issues confirmed
   - Prioritize the deterministic 3 failures
   - Check dev.elitea.ai backend status
   - May need to pause new test development

3. **If job cancelled again:**
   - Investigate timeout configuration
   - Check for resource exhaustion
   - May need to split pipeline suite

---

**Document Status:** Monitoring in progress  
**Last Updated:** 2026-08-24 18:15:39 UTC  
**Will Update:** After run completion
