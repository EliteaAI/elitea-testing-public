# TMS Test Case Updates - Summary

**Date:** 2026-08-21  
**Status:** ✅ Updates Applied (Not Committed)  
**Repository:** `onetest-ai-tm-Elitea`  
**Files Modified:** 14  

---

## What Was Done

Updated 14 TMS test case files to fix orphaned `automation_test_id` references after tests were reorganized from `agents/` suite to `agent_hub/` suite.

### Changes Applied

| # | Case ID | Old Suite | New Suite | Change Type |
|---|---------|-----------|-----------|-------------|
| 1 | ELITEA-2366 | agent-hub | agent_hub | Hyphen → Underscore |
| 2 | ELITEA-2350 | agents | agent_hub | Suite reorganization |
| 3 | ELITEA-2351 | agents | agent_hub | Suite reorganization |
| 4 | ELITEA-2352 | agents | agent_hub | Suite reorganization |
| 5 | ELITEA-2353 | agents | agent_hub | Suite reorganization |
| 6 | ELITEA-2354 | agents | agent_hub | Suite reorganization |
| 7 | ELITEA-2355 | agents | agent_hub | Suite reorganization |
| 8 | ELITEA-2356 | agents | agent_hub | Suite reorganization |
| 9 | ELITEA-2357 | agents | agent_hub | Suite reorganization |
| 10 | ELITEA-2358 | agents | agent_hub | Suite reorganization |
| 11 | ELITEA-2359 | agents | agent_hub | Suite reorganization |
| 12 | ELITEA-2363 | agents | agent_hub | Suite reorganization |
| 13 | ELITEA-2364 | agents | agent_hub | Suite reorganization |
| 14 | ELITEA-2365 | agents | agent_hub | Suite reorganization |

### Typical Change

**Before:**
```yaml
automation_test_id:
  - tests.ui.agents.test_agent_hub_close_agent_detail_modal.TestAgentHubCloseAgentDetailModal.test_agent_hub_close_agent_detail_modal
```

**After:**
```yaml
automation_test_id:
  - tests.ui.agent_hub.test_agent_hub_close_agent_detail_modal.TestAgentHubCloseAgentDetailModal.test_agent_hub_close_agent_detail_modal
```

**Change:** `tests.ui.agents` → `tests.ui.agent_hub`

---

## Current Status

### In Repository: `onetest-ai-tm-Elitea`

```bash
$ cd onetest-ai-tm-Elitea
$ git status --short

 M tests/automated-full-regression-ui/agent_hub/ELITEA-2350_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2351_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2352_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2353_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2354_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2355_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2356_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2357_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2358_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2359_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2363_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2364_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2365_*.md
 M tests/automated-full-regression-ui/agent_hub/ELITEA-2366_*.md

14 files changed, 14 insertions(+), 14 deletions(-)
```

**Changes are staged for your review but NOT committed.**

---

## Review Instructions

### 1. Review Changes

```bash
cd /path/to/onetest-ai-tm-Elitea

# See all changes
git diff tests/automated-full-regression-ui/agent_hub/

# Review specific file
git diff tests/automated-full-regression-ui/agent_hub/ELITEA-2357_agent-hub-close-agent-detail-modal-with-x-button.md

# See just the automation_test_id changes
git diff | grep -E "^[-+].*test_agent_hub"
```

### 2. Verify Correctness

Each change should follow this pattern:
- `tests.ui.agents.test_agent_hub_*` → `tests.ui.agent_hub.test_agent_hub_*`
- OR `tests.ui.agent-hub.test_agent_hub_*` → `tests.ui.agent_hub.test_agent_hub_*`

All changes are in the `automation_test_id` field only.

### 3. Commit When Ready

```bash
# If changes look correct
git add tests/automated-full-regression-ui/agent_hub/ELITEA-*.md

git commit -m "fix(tms): update 14 orphan automation_test_id refs for agent_hub suite

Tests were moved from agents/ to agent_hub/ suite, causing TMS case
automation_test_id fields to become orphaned and fail correlation.

Updated high-confidence matches:
- ELITEA-2366: agent-hub → agent_hub (hyphen to underscore)
- ELITEA-2350-2365: agents → agent_hub (13 cases)

All matches verified - exact class and method names exist in new location.

Correlation impact: 14 fewer orphan references in coverage reports."

# Push to remote
git push origin main
```

### 4. Discard If Needed

```bash
# If you want to undo all changes
git restore tests/automated-full-regression-ui/agent_hub/ELITEA-*.md
```

---

## Expected Impact

### Before Update
- **Orphan TMS References:** 141
- **Failed Correlations:** 14 agent_hub tests

### After Update + Index Rebuild
- **Orphan TMS References:** 127 (reduced by 14)
- **Failed Correlations:** 0 for these 14 tests
- **Coverage Improvement:** ~10% for agent_hub suite

### To Rebuild Index

After committing these changes:

```bash
cd onetest-ai-tm-Elitea
npx @onetest/tms build-index
npx @onetest/tms automation-coverage
```

This will regenerate `index.json` and `reports/coverage.md` with the corrected references.

---

## Analysis Tool

These updates were identified using:

```bash
cd elitea-testing-public/automation
python3 scripts/analyze_orphan_tms_refs.py
```

This tool is reusable for future test reorganizations.

---

## Documentation

Full details available in:
- **`TMS_ORPHAN_UPDATES.md`** - Complete manual with all 14 cases detailed
- **`automation/scripts/analyze_orphan_tms_refs.py`** - Analysis tool
