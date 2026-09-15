# Test Run Status - 2026-08-26

## Runs In Progress

### Local Run - pipelines suite
- **Status**: Running (just started, ~1%)
- **Expected Duration**: ~20-30 minutes
- **Tests**: 51 collected
- **Output**: `/tmp/pipelines_local_run.txt`

### Local Run - pipelines_2 suite (2nd run)
- **Status**: Running (just started, ~1%)  
- **Expected Duration**: ~17 minutes
- **Tests**: 55 collected
- **Output**: `/tmp/pipelines_2_local_run_2.txt`

## Completed Runs

### Local Run - pipelines_2 suite (1st run)
- **Status**: ✅ Completed
- **Duration**: 17.5 minutes
- **Results**: 48 passed, 6 failed, 1 error
- **Pass Rate**: 87%

### GitHub Actions Run #32931571484 - pipelines suite
- **Status**: ✅ Completed (from GHA)
- **Duration**: ~27m38s
- **Results**: ~46 passed, 3 failed
- **Pass Rate**: 94%
- **URL**: https://github.com/EliteaAI/elitea-testing-public/actions/runs/32931571484

## Comparison Plan

Once all runs complete, we will compare:

1. **pipelines suite**: Local vs GHA #32931571484
   - Same 3 failures?
   - Any environment-specific differences?
   - Test execution time comparison

2. **pipelines_2 suite**: Run 1 vs Run 2 (stability check)
   - Same 6 failures?
   - Flaky tests identification
   - Consistent pass rate?

3. **Cross-suite comparison**:
   - Which failures are suite-specific?
   - Common issues across both suites?
   - Known vs unknown failures breakdown

## Key Metrics to Track

- Total test count per suite
- Pass/Fail/Error breakdown
- Known defects (sanctioned RED)
- Environment-specific issues (APP_PREFIX, etc.)
- Flaky tests (different results between runs)
- New failures introduced by recent changes

## Expected Completion Time

Based on previous runs:
- **pipelines**: ~12:50 PM (in ~15 minutes)
- **pipelines_2**: ~12:50 PM (in ~15 minutes)

Will update this document when runs complete.
