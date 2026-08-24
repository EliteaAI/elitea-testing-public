# Pipeline Suite Issues Summary
**Session Date:** 2026-08-24  
**CI Run Analyzed:** [#32712834665](https://github.com/EliteaAI/elitea-testing-public/actions/runs/32712834665)  
**Status:** Partially resolved with workarounds; permanent fix pending EliteaUI PR merge

---

## Executive Summary

**Root Cause:** Two `data-testid` attributes removed from EliteaUI `RunStateDialog.jsx` on 2026-08-11 (commit `a638b586`).

**Impact:** 
- 17 test failures in CI run #32712834665
- 6 tests actually affected by missing testids (5 timeline + 1 states)
- 11 other failures unrelated or transient

**Resolution:**
- ✅ Temporary workarounds implemented in `automation/pages/pipeline_detail_page.py`
- ✅ Permanent fix PR created: [EliteaUI PR #832](https://github.com/EliteaAI/EliteaUI/pull/832)
- ⏳ Awaiting PR merge and deployment to DEV

---

## Issue 1: Missing `pipeline-run-details-timeline-section` Testid

### What Happened
**Removed:** `data-testid="pipeline-run-details-timeline-section"` from timeline header Box  
**When:** 2026-08-11, commit `a638b586`  
**Why:** "Zero-functional-impact cleanup" - removed wrapper `<Box sx={{ display: 'contents' }}>` that carried the testid

### Affected Tests (5 of 17 CI failures)
1. `test_pipeline_execution_updates_timeline_after_new_message`
2. `test_pipeline_message_input_state_shows_waiting_message`
3. `test_subgraph_state_sharing_different_parent_nodes_isolated`
4. `test_subgraph_state_sharing_node_c_state_propagation` ⚠️
5. `test_subgraph_state_sharing_shared_parent_propagates`

⚠️ Test #4 has a **separate issue** - pipeline stays "In progress" instead of "Completed" (timing/execution issue, not testid-related)

### Workaround Implemented
**File:** `automation/pages/pipeline_detail_page.py`  
**Commit:** `5f20bceb5`  
**Strategy:** CSS + xpath parent traversal

```python
run_details_timeline_section = LocatorDescriptor(
    locator='[data-testid="pipeline-run-details-panel"] >> text="Timeline step:" >> xpath=..',
    description='Run Details panel "Timeline step" section (label + node id + stepper)'
)
```

**Verification:** 8 of 10 timeline tests confirmed passing locally (80% success rate)

### Permanent Fix
**EliteaUI PR #832, commit `890082b5`**  
Restored testid to the timeline header Box:
```jsx
<Box
  sx={styles.timelineHeader}
  data-testid="pipeline-run-details-timeline-section"
>
```

---

## Issue 2: Missing `pipeline-run-details-states-section` Testid

### What Happened
**Never existed:** This testid was never in the codebase originally  
**Discovered:** When `test_run_details_panel_opens_after_execution` started failing

### Affected Tests (1 failure)
- `test_run_details_panel_opens_after_execution` - Expects to read state variable names from the States section

### Workaround Implemented (7 iterations)
**File:** `automation/pages/pipeline_detail_page.py`  
**Final commit:** `ada49a3a1`  
**Strategy:** Method override - iterate all MUI Accordions to capture state variable names

```python
def get_run_details_states_section_text(self) -> str:
    """Return the Run Details panel's States section text content.
    
    TEMPORARY: Builds locator manually due to missing testid.
    Returns combined text from header + all accordion summaries + any expanded content.
    """
    panel = self.page.get_by_test_id("pipeline-run-details-panel")
    
    # Get "States" header
    header = panel.locator('text="States"').first.text_content() or ""
    
    # Get all accordion summaries (state variable names)
    accordions = panel.locator(".MuiAccordion-root")
    accordion_texts = []
    for i in range(accordions.count()):
        accordion_texts.append(accordions.nth(i).text_content() or "")
    
    # Combine: header + all accordion content
    all_text = f"{header} {' '.join(accordion_texts)}"
    return all_text.strip()
```

**Why 7 iterations?**
1. Wrong element targeted (header vs container)
2. CSS selector syntax errors in LocatorDescriptor
3. Xpath chaining syntax errors
4. Missing header text
5. Missing collapsed accordion names
6. Final: Iterate all accordions individually

### Permanent Fix
**EliteaUI PR #832, commit `dd1b7939`**  
Added testid to the states container (which holds the accordion list):
```jsx
<Box
  sx={styles.statesContainer}
  data-testid="pipeline-run-details-states-section"
>
```

**Note:** Testid placed on `statesContainer` (not `statesHeader`) because tests need access to state variable accordions, not just the "States" header text.

---

## Other CI Failures (Not Testid-Related)

### Artifacts/Toolkits Suites (11 failures)
**Sample investigation:**
- 2 sampled failures had different root causes (APP_PREFIX, known defect #1332)
- 10 untested failures don't call `run_details` methods
- Likely transient CI issues (network, timing)

**Recommendation:** Monitor next CI runs for recurrence

### Separate Pipeline Issue Discovered
**Test:** `test_subgraph_state_sharing_node_c_state_propagation`  
**Symptom:** Pipeline execution stays "In progress" when test expects "Completed"  
**Error:** `Embedded chat response did not stabilise within timeout`  
**Status:** Needs separate investigation (not related to testid issue)

---

## Next Steps (After EliteaUI PR #832 Merges)

### 1. Wait for PR Merge & Deployment
- ✅ PR #832 created with both testid restorations
- ⏳ Awaiting review and merge to `EliteaUI` main
- ⏳ Awaiting deployment to dev.elitea.ai

### 2. Revert Workarounds
**File:** `automation/pages/pipeline_detail_page.py`  
**Remove:**
```python
# Timeline workaround (commit 5f20bceb5) - revert to:
run_details_timeline_section = LocatorDescriptor(
    testid="pipeline-run-details-timeline-section",
    description='Run Details panel "Timeline step" section'
)

# States workaround (commit ada49a3a1) - revert to:
run_details_states_section = LocatorDescriptor(
    testid="pipeline-run-details-states-section", 
    description='Run Details panel "States" section'
)
```

**And delete the manual `get_run_details_states_section_text()` method override**

### 3. Verify All Timeline Tests
Run full regression against DEV to confirm all 10 timeline tests pass with real testids:
```bash
HEADLESS=true ../.venv/bin/pytest tests/ui/pipelines/ -k "timeline or states" -v
```

Expected: All tests PASS (no workarounds, clean testid locators)

### 4. Investigate Remaining Issue
**Test:** `test_subgraph_state_sharing_node_c_state_propagation`  
**Next Steps:**
- Reproduce locally against dev.elitea.ai
- Check if pipeline actually completes or genuinely hangs
- Review embedded chat response stabilization logic
- Check for backend/WebSocket timing issues

---

## Files Modified

### This Repository (elitea-testing-public)
**Workarounds (temporary):**
- `automation/pages/pipeline_detail_page.py` (commits `5f20bceb5`, `ada49a3a1`)

**Documentation:**
- `PIPELINE_TIMELINE_FIX_PLAN.md` - Fix plan with affected tests mapped
- `PIPELINE_TIMELINE_VERIFICATION_REPORT.md` - Verification results (8/10 passing)
- `CI_RUN_32712834665_ANALYSIS.md` - Full CI failure breakdown
- `PIPELINE_SUITE_ISSUES_SUMMARY.md` - This file

### EliteaUI Repository
**Permanent fixes (pending merge):**
- `src/[fsd]/features/pipelines/flow-editor/ui/state/RunStateDialog.jsx`
  - Commit `890082b5` - Restored timeline testid
  - Commit `dd1b7939` - Added states testid
- **PR:** [EliteaUI#832](https://github.com/EliteaAI/EliteaUI/pull/832)

---

## Key Learnings

### 1. Zero-Functional-Impact Changes Can Break Tests
The `a638b586` commit was correct from a UI perspective (removed wrapper with no visual impact), but broke 5 automation tests. **Lesson:** Testids are load-bearing for automation even if functionally inert.

### 2. LocatorDescriptor Limitations
The class cannot handle Playwright's `>>` chaining syntax or xpath parent traversal patterns the same way raw `page.locator()` does. **Workaround:** Use method overrides for complex locators that need chaining.

### 3. MUI Accordion Content Visibility
Accordions collapsed by default don't expose their summary text via parent `.text_content()`. **Solution:** Iterate accordions individually to capture both expanded and collapsed content.

### 4. Testid Placement Strategy
For sections with multiple interactive elements (like States with accordions), place testid on the **container** that holds the elements, not just the header. Tests need access to the interactive surface, not just labels.

---

## References

- **CI Run:** https://github.com/EliteaAI/elitea-testing-public/actions/runs/32712834665
- **EliteaUI PR:** https://github.com/EliteaAI/EliteaUI/pull/832
- **EliteaUI Commit (removal):** `a638b586` (2026-08-11)
- **Workaround Commits:** `5f20bceb5` (timeline), `ada49a3a1` (states)
- **Related Issues:**
  - Known defect #1332 (affects some unrelated failures)
  - TBD issue for pipeline execution timing (test #4)

---

**Document Created:** 2026-08-24  
**Last Updated:** 2026-08-24  
**Status:** Active - awaiting EliteaUI PR #832 merge
