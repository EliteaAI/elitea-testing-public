# Orphan TMS References - Final Summary

**Analysis Date:** 2026-08-21  
**Dashboard Source:** https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/reports/dashboard.md

---

## Quick Answer

**Out of 127 orphan refs:**

| Category | Count | % |
|----------|-------|---|
| **High-Confidence Fixable** ✅ | **4-6** | **~4%** |
| **Not Fixable** ❌ | **121** | **~96%** |

**Fix time:** ~12 minutes  
**Coverage gain:** +1.4% (36.8% → 38.2%)

---

## The 4-6 Fixable Orphans

### High Confidence (4 refs) ✅

1. **ELITEA-2392** - Settings AI Providers
   - Issue: Extra `_test` suffix
   - Fix: Remove `_test` from test name
   - Time: 1 min

2. **ELITEA-1814** - Artifacts Bucket Validation
   - Issue: Missing parameter in test name
   - Fix: Add 3 parameterized variants
   - Time: 2 min

3. **ELITEA-2206** - Hash Search
   - Issue: Test renamed
   - Fix: Update to `test_hash_search_participants`
   - Time: 1 min

4. **ELITEA-2469** - Add Agent via Hash Search
   - Issue: Test name more specific than actual
   - Fix: Map to `test_add_participant_via_hash_search`
   - Time: 1 min

5. **ELITEA-2470** - Add Pipeline via Hash Search
   - Issue: Same as above
   - Fix: Map to `test_add_participant_via_hash_search`
   - Time: 1 min

### Medium Confidence (2 refs) ⚠️

6. **ELITEA-2137** - Move Conversation to Existing Folder
   - Issue: Class name mismatch
   - Fix: Verify & map to existing test
   - Time: 3 min

---

## The 121 NOT Fixable

These tests genuinely don't exist:

| Category | Count | Why Not Fixable |
|----------|-------|-----------------|
| Chat - Folder Management | 16 | Planned batch never built |
| Chat - Conversation Renaming | 18 | Planned batch never built |
| Chat - Pinning | 11 | Planned batch never built |
| Skills - Build/Edit AI | 17 | Future feature area |
| Help Center | 10 | Deprioritized area |
| Chat - Other | 49 | Various incomplete features |

**Action:** Remove these orphan refs from TMS case files

---

## Coverage Impact

### Current State (with all orphans)
```
TMS Dashboard shows: 286 / 432 = 66.2% ❌ inflated
```

### After Removing 121 Orphans
```
Valid links: 159 / 432 = 36.8% ✅ accurate
```

### After Fixing 6 Refs
```
Valid links: 165 / 432 = 38.2% ✅ accurate + improved
```

**Net gain from fixes: +1.4%**

---

## Recommended Action Plan

### Phase 1: Quick Wins (12 minutes)

Fix the 4-6 high/medium confidence orphans:

```bash
cd onetest-ai-tm-Elitea

# 1. ELITEA-2392
vim tests/automated-full-regression-ui/settings/ELITEA-2392.md
# Remove _test suffix

# 2. ELITEA-1814
vim tests/automated-full-regression-ui/artifacts/ELITEA-1814.md
# Add 3 parameterized variants

# 3-5. ELITEA-2206, 2469, 2470
# Update hash search test names

# Rebuild
npx @onetest/tms build-index
```

### Phase 2: Clean Remaining 121 (team decision required)

For each orphan category:
1. **Decide:** Build these tests? Mark manual? Cancel?
2. **Update:** Edit TMS case files
3. **Rebuild:** `build-index` + regenerate dashboard

---

## Files Generated

**Analysis Reports:**
1. `README_ORPHAN_ANALYSIS.md` - Navigation index
2. `ORPHAN_REFS_SUMMARY.md` - Executive summary
3. `LATEST_ORPHAN_ANALYSIS.md` - Full list (127 refs)
4. `ALL_ORPHAN_REFS_COMPLETE.md` - Actionable mapping
5. `TMS_ORPHAN_UPDATES.md` - Update instructions
6. `COMMIT_IMPACT_SUMMARY.md` - Visual charts
7. `FIXABLE_ORPHANS_ANALYSIS.md` - Detailed fix guide ⭐
8. `ORPHAN_REFS_FINAL_SUMMARY.md` - This summary

**Scripts & Data:**
- `automation/scripts/analyze_orphan_tms_refs.py`
- `automation/scripts/orphan_analysis.json`
- `automation/scripts/update_tms_orphans.sh`

---

## Bottom Line

✅ **4-6 orphans can be fixed** (~4% of 127)  
❌ **121 orphans should be removed** (~96% of 127)  
📊 **Coverage will drop from 66% to 38%** (accurate)  
⏱️ **12 minutes to fix the fixable ones**

**Next:** Review `FIXABLE_ORPHANS_ANALYSIS.md` for step-by-step fix instructions.

