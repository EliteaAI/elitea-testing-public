# TMS Orphan References - Update Summary

**Generated:** 2026-08-21 16:41 UTC  
**Issue:** 127 orphan `automation_test_id` refs in TMS inflating coverage metrics

## Quick Summary

| Metric | Before | After Cleanup | Change |
|--------|--------|---------------|--------|
| Total tests in automation | 432 | 432 | - |
| Tests "linked to TMS" (dashboard) | 286 | 159 | **-127** ❌ |
| Orphan refs | 127 | 0 | -127 ✅ |
| **True TMS Coverage** | 66.2% | **36.8%** | -29.4% |

## What Happened

The TMS dashboard showed **286 tests linked to TMS cases**, but **127 of those refs** (44%) point to tests that **don't exist** in the automation codebase.

These "orphan refs" were created when:
- Tests were planned but never built
- Tests were renamed/refactored without updating TMS
- Test files were deleted
- Test structure changed (class names, file paths)

## All 127 Orphan Refs Found

**Zero matches** - All 127 refs searched in codebase, none exist as actual tests.

### Breakdown by Category

| Category | Count | Example Case IDs |
|----------|-------|------------------|
| **Chat - Folder Management** | 18 | ELITEA-2118, 2134, 2121, 2128, 2146, 2137 |
| **Chat - Conversation Renaming** | 18 | ELITEA-2099, 2100, 2105-2113, 2101-2104 |
| **Skills - Build/Edit with AI** | 17 | ELITEA-1986, 1992, 1994-2000, 2611-2613 |
| **Chat - Pinning** | 11 | ELITEA-2150, 2153-2156, 2158, 2160-2162 |
| **Help Center** | 10 | ELITEA-2220-2230 |
| **Chat - Attachments** | 6 | ELITEA-2195, 2196, 2198, 2199, 2467, 2201 |
| **Skills - Publishing** | 6 | ELITEA-2595-2599, 2614 |
| **Skills - Agent Interaction** | 6 | ELITEA-2600, 2601, 2607-2610 |
| **Chat - Starters** | 5 | ELITEA-2073, 2074, 2177, 2178, 2465 |
| **Chat - Hash Search** | 7 | ELITEA-2206, 2469, 2470, 2173-2176, 2192 |
| **Other Chat Features** | 23 | Build AI, Canvas, Context, Search, Regenerate, etc. |
| **Artifacts** | 1 | ELITEA-1814 |
| **Settings** | 1 | ELITEA-2392 |
| **Onboarding** | 1 | ELITEA-2231 |

## Detected Patterns

### 1. Large Incomplete Batch Efforts

Three major feature areas appear to have been **planned as batches** but never completed:

- **Folder Management** (18 refs) - Creation, renaming, moving, scrollability
- **Conversation Renaming** (18 refs) - Validation, boundaries, special chars
- **Skills Build/Edit AI** (17 refs) - Wizards, character limits, role visibility

### 2. Duplicate Case IDs

Some case IDs have **multiple orphan refs** (data issue):

- ELITEA-2116 (2 refs) - Delete confirmation modal
- ELITEA-2468 (2 refs) - Slash mention MCP selection
- ELITEA-2597 (2 refs) - Publish token invalidation
- ELITEA-2613 (2 refs) - Edit with AI role visibility

### 3. Possible Renames

- **ELITEA-2392** - Ref ends with `_test` but actual test doesn't have that suffix
- **ELITEA-1814** - Parameterized test - base name exists, specific param doesn't

## Impact on Metrics

### Coverage Inflation

```
Claimed:  286 / 432 = 66.2% TMS coverage
Reality:  159 / 432 = 36.8% TMS coverage

Ghost coverage: 127 / 286 = 44% of "automated" cases don't exist
```

### CI Correlation Failures

`correlate_results` command can't match these 127 JUnit `code_ref` values because the tests don't exist:

```bash
cd onetest-ai-tm-Elitea
npx @onetest/tms correlate-results --automated reports/automated/junit-RUN-*.json

# Result: 127 TMS cases marked "automated" show NO correlation ❌
```

## What to Do

### Step 1: Review with Team

For each major cluster, decide:

**Folder Management (18)** - Build these tests? Deprioritize? Mark manual?  
**Conversation Renaming (18)** - Same question  
**Skills Build/Edit AI (17)** - Future sprint? Cancel?  
**Help Center (10)** - Low priority area?

### Step 2: Clean TMS Case Files

For **each of 127 orphan refs**, update the TMS case file:

**If test was never built:**
```yaml
execution_type: manual  # or leave as draft
status: draft
# Delete the automation_test_id line
```

**If test exists with different name:**
```yaml
automation_test_id:
  - tests.ui.chat.CORRECT_NEW_NAME  # Update to actual path
```

**If feature removed:**
```yaml
status: deprecated
execution_type: manual
```

### Step 3: Rebuild TMS Index

After editing case files:

```bash
cd onetest-ai-tm-Elitea
npx @onetest/tms build-index
```

This rebuilds `index.json` and `index_automated.json`.

### Step 4: Regenerate Dashboard

```bash
cd onetest-ai-tm-Elitea
npx @onetest/tms coverage --output reports/dashboard.md
```

New dashboard will show **corrected** metrics (~37% coverage, not 66%).

---

## Files Generated

All analysis files created in project root:

1. **ORPHAN_REFS_SUMMARY.md** - Executive summary, impact, recommendations
2. **LATEST_ORPHAN_ANALYSIS.md** - Full categorized list (all 127 with details)
3. **ALL_ORPHAN_REFS_COMPLETE.md** - Success/not-success mapping, actionable steps
4. **TMS_ORPHAN_UPDATES.md** - This file - consolidated update summary
5. **automation/scripts/analyze_orphan_tms_refs.py** - Python analysis script
6. **automation/scripts/orphan_analysis.json** - Machine-readable results
7. **automation/scripts/update_tms_orphans.sh** - Bash cleanup helper (sample)

---

## Sample TMS Updates

### Example 1: Test Never Built

**File:** `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/chat/ELITEA-2093.md`

```diff
  ---
  title: Agent Hub - Create Conversation via Starter
- execution_type: automated
+ execution_type: manual
- status: ready
+ status: draft
- automation_test_id:
-   - tests.ui.chat.test_agent_hub_create_conversation_via_starter...
  ---
```

### Example 2: Test Renamed

**File:** `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/settings/ELITEA-2392.md`

```diff
  ---
  title: AI Providers Page Sections Load
  execution_type: automated
  status: ready
  automation_test_id:
-   - tests.ui.settings...test_ai_providers_page_sections_load_without_error_test
+   - tests.ui.settings.test_ai_providers_page_sections_load_without_error.TestAIProvidersPageSections.test_ai_providers_page_sections_load_without_error
  ---
```

---

## Next Steps

1. ✅ **Review** - Team reviews all 127 cases, decides per-cluster
2. 🔧 **Clean** - Update TMS case files (remove orphan refs)
3. 🔨 **Rebuild** - Run `build-index` to regenerate TMS index
4. 📊 **Dashboard** - Regenerate to show corrected coverage (~37%)
5. 📝 **Document** - Update workflow to prevent future orphan refs

---

**End of Report**

