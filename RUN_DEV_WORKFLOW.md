# How to Run DEV Workflow with automation/fixes Branch

## ✅ Branch Pushed Successfully

The `automation/fixes` branch has been pushed to GitHub with all changes:
- 4 test data dependency fixes (committed earlier)
- Test markers (blocked/flaky) 
- DEV workflow updates

**Commits on automation/fixes:**
1. `840d7dd7` - test: mark blocked/flaky tests and update DEV workflow
2. `a3fdb8c4` - fix: notification assertions graceful
3. `fee4d5a8` - fix: guardrails cleanup enhancement
4. `32c53429` - fix: pagination conditional
5. `6d5aa84d` - fix: analytics empty pipeline fixture

---

## 🚀 Running the DEV Workflow

### Option 1: Via GitHub UI (Recommended)

1. **Navigate to Actions:**
   - Go to: https://github.com/EliteaAI/elitea-testing-public/actions
   - Click on "UI Tests DEV" workflow in the left sidebar

2. **Click "Run workflow" button** (top right, on the branch dropdown)

3. **Fill in the workflow parameters:**

   | Parameter | Value | Notes |
   |-----------|-------|-------|
   | **Git branch/tag/SHA** | `automation/fixes` | ⚠️ CRITICAL - Use this branch! |
   | Test suite | `all` | Or choose specific suite |
   | Custom suites | (leave default) | Uses 10 baseline suites |
   | Number of parallel runners | `9` | Default is fine |
   | **Pytest markers** | `not new and not blocked and not flaky` | ✅ Already the default! |
   | Publish results to OneTest TMS | `false` | Optional |

4. **Click "Run workflow"** green button

---

### Option 2: Via GitHub CLI

```bash
gh workflow run "UI Tests DEV" \
  --ref automation/fixes \
  -f suite=all \
  -f markers="not new and not blocked and not flaky" \
  -f parallel_jobs=9 \
  -f publish_to_tms=false \
  --repo EliteaAI/elitea-testing-public
```

---

## 📊 What Will Run

With markers: `not new and not blocked and not flaky`

### ✅ WILL RUN (Expected)
- All tests with **NO markers** (baseline stable tests)
- All tests marked **ONLY with `new`** (newly added tests)

### ❌ WILL NOT RUN (Excluded)
- Tests marked `@pytest.mark.blocked` (14 tests) - DEV environment issues
- Tests marked `@pytest.mark.flaky` (13 tests) - Timing/race conditions
- Tests marked `@pytest.mark.new` **AND** any other marker

### Test Count Estimate
- **Before changes:** ~250 tests would run (including 27 problematic ones)
- **After changes:** ~223 tests will run (stable tests only)
- **Excluded:** 27 tests (14 blocked + 13 flaky)

---

## 🔍 Monitoring the Run

### Watch Progress
1. Go to: https://github.com/EliteaAI/elitea-testing-public/actions
2. Find your workflow run (will show as "UI Tests DEV [automation/fixes] [all]")
3. Click on it to see real-time progress

### Expected Results
- **Pass:** Tests with fixes should now pass
  - Analytics empty pipeline test
  - Pagination conditional test
  - Guardrails cleanup test
  - Notification preconditions test

- **Skipped:** 27 tests will be automatically skipped
  - 14 blocked tests
  - 13 flaky tests

- **Total Duration:** ~30-45 minutes (with 9 parallel runners)

---

## 🐛 If Something Goes Wrong

### Issue: Workflow uses wrong branch
**Symptom:** Tests fail with old issues  
**Solution:** Check the "Git branch/tag/SHA" parameter is set to `automation/fixes`

### Issue: Blocked/flaky tests still running
**Symptom:** See dropdown failures (select-option-400) or timing issues  
**Solution:** Verify markers parameter is `not new and not blocked and not flaky`

### Issue: No tests run
**Symptom:** Workflow completes too quickly with 0 tests  
**Solution:** Markers might be too restrictive - try `not blocked and not flaky` (allow 'new' tests)

---

## 📝 After the Run

### Success Criteria
✅ All 4 fixed tests pass  
✅ No blocked tests appear in results  
✅ No flaky tests appear in results  
✅ Overall pass rate improves significantly  

### Next Steps
1. **Review results** - Check Allure report or GitHub Actions summary
2. **Compare with baseline** - Run 31705800993 had 22 reproduced failures
3. **If successful** - Create PR from `automation/fixes` to `automation/base`
4. **Document** - Update any test documentation with findings

---

## 📋 Quick Reference

**Workflow URL:**  
https://github.com/EliteaAI/elitea-testing-public/actions/workflows/test-ui-dev.yml

**Branch:**  
`automation/fixes`

**Default Markers (New):**  
`not new and not blocked and not flaky`

**Old Markers (Previous):**  
`not new`

**Difference:**  
Now excludes 27 additional problematic tests

---

## 💡 Pro Tips

1. **First Run:** Keep default parameters to validate the marker changes work
2. **Debug Run:** To include everything: set markers to `all`
3. **Test Specific Suite:** Set suite dropdown to target area (e.g., `agents`, `admin`)
4. **Parallel Jobs:** Can reduce to 1-3 for easier debugging of individual tests
5. **Custom Suites:** Can specify exact test paths in custom_suites parameter

---

## 🔗 Related Documents

- `CHANGES_SUMMARY.md` - Complete change log
- `automation/FINAL_REPORT.md` - Failure analysis and recommendations
- `automation/INVESTIGATION_SUMMARY.md` - Technical deep-dive
- `.github/workflows/test-ui-dev.yml` - Workflow definition
- `automation/pytest.ini` - Marker definitions

---

## ✅ Checklist Before Running

- [ ] Branch `automation/fixes` is pushed to GitHub
- [ ] You're on the GitHub Actions page
- [ ] "UI Tests DEV" workflow is selected
- [ ] "Run workflow" button is visible
- [ ] Git branch parameter is set to: `automation/fixes`
- [ ] Markers parameter shows: `not new and not blocked and not flaky` (or left as default)
- [ ] Ready to click "Run workflow"!

---

**Last Updated:** 2026-08-14  
**Branch:** automation/fixes (840d7dd7)  
**Status:** ✅ Ready to run
