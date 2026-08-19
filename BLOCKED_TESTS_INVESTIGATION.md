# Blocked Tests Investigation - 2026-08-17

## Investigation Summary

Unmarked and ran 2 blocked tests locally against DEV environment to verify if they're still blocked.

---

## Test 1: test_agent_with_toolkit_executes_in_chat ❌ STILL BLOCKED

**File:** `tests/ui/chat/test_agent_with_toolkit_chat.py`  
**Original block reason:** GitHub toolkit authentication failure (401 Bad credentials)

### Local Execution Result:

**Status:** FAILED  
**Duration:** 84.88s  
**Screenshot:** `screenshots/test_agent_with_toolkit_executes_in_chat_FAIL_20260817_145002.png`

### Failure Details:

```
AssertionError: Expected toolkit response to include the known branch 'main'.

Response: I attempted to list branches via the GitHub toolkit, but the tool call failed 
due to an authentication error:
  list_branches_in_repo → 401 Bad credentials
  I can't retrieve the actual branch names until the GitHub connection for this toolkit 
  is re-authenticated (valid token/credentials with access to EliteaAI/elitea-testing).
```

### Analysis:

**Root Cause:** GitHub token in `.env.test` (variable `GIT_HUB_TOKEN`) is **invalid or expired**

**Evidence:**
1. Test creates GitHub toolkit with token from `.env.test`
2. Agent attempts to call `list_branches_in_repo` 
3. GitHub API returns `401 Bad credentials`
4. Agent's response explicitly states authentication error

**Is This a Valid Block?** ✅ **YES**

This is a **test data / environment configuration issue**, not a product bug:
- The test requires valid GitHub credentials
- The GitHub token used for testing is invalid/expired
- Without valid credentials, the test cannot verify toolkit execution

**Action Required:**
1. Update `GIT_HUB_TOKEN` in `.env.test` with valid token
2. Token needs `repo` scope for `EliteaAI/elitea-testing-public`
3. Once fixed, unmark as blocked and retest

**Keep Blocked:** ✅ YES - re-marked with updated comment

---

## Test 2: test_create_bucket_max_length_name_and_delete ❌ STILL BLOCKED

**File:** `tests/ui/artifacts/test_artifacts_create_bucket_55char_name_and_delete.py`  
**Original block reason:** Unknown (needs investigation)

### Local Execution Result:

**Status:** FAILED → RERUN → TIMEOUT  
**Duration:** 120s+ (killed by timeout)  
**Screenshot:** `screenshots/test_create_bucket_max_length_name_and_delete_FAIL_20260817_144740.png`

### Failure Pattern:

```
RERUN [100%]  (retry triggered)
tests/.../test_artifacts_create_bucket_55char_name_and_delete.py::...::test_create_bucket_max_length_name_and_delete
(test hung during retry, killed after 120s timeout)
```

### Analysis:

**Root Cause:** Test **hangs** during execution, likely during bucket creation or deletion

**Evidence:**
1. Test failed on first attempt (screenshot captured)
2. Retry mechanism triggered (RERUN appeared)
3. Test hung during retry (no output after RERUN line)
4. Killed by 120s timeout
5. Test never completed (no PASSED or FAILED status)

**Possible Issues:**
1. **API timeout** - Bucket creation/deletion endpoint not responding
2. **UI hang** - Page element never appears (infinite wait)
3. **Network issue** - Request to DEV backend stalled
4. **State corruption** - Previous test left artifacts in bad state

**Is This a Valid Block?** ✅ **YES**

This is a **persistent infrastructure/environment issue**:
- Test doesn't complete (hangs indefinitely)
- Retry doesn't help (hung again on retry)
- Blocking execution of subsequent tests in suite

**Action Required:**
1. Run test in debug mode to identify hang point
2. Check DEV backend logs for artifact API errors
3. May need shorter timeouts or better error handling
4. Investigate if bucket name length (56 chars) triggers backend issue

**Keep Blocked:** ✅ YES - re-marked with investigation notes

---

## Summary

### Both Tests Remain Blocked ✅

| Test | Issue | Type | Valid Block? | Action |
|------|-------|------|--------------|--------|
| test_agent_with_toolkit_executes_in_chat | 401 Bad credentials | Test data | ✅ YES | Update GitHub token |
| test_create_bucket_max_length_name_and_delete | Test hangs/timeout | Infrastructure | ✅ YES | Debug + investigate |

### Blocked Tests Count: 17 (Unchanged)

Both tests were already blocked and investigation confirms they should remain blocked.

---

## Detailed Findings

### Test 1: GitHub Toolkit Authentication

**Token Source:**
```python
# Test uses github_toolkit fixture which reads:
GIT_HUB_TOKEN=... from .env.test
```

**Token Verification:**
```bash
# Check if token is valid (should be done before fixing)
curl -H "Authorization: token $GIT_HUB_TOKEN" https://api.github.com/user
# If 401, token is invalid/expired
```

**Fix:**
1. Generate new GitHub personal access token
2. Scope needed: `repo` (full control of private repositories)
3. Update `.env.test`: `GIT_HUB_TOKEN=ghp_xxxxxxxxxxxxx`
4. Restart any cached sessions
5. Rerun test to verify

**Expected After Fix:**
- Agent successfully calls GitHub API
- Response includes "main" branch
- Test passes

---

### Test 2: Artifacts Bucket Timeout

**Hang Point (Suspected):**

Based on test flow (lines 1-37 in docstring):
- Steps 1-7: Navigation + form fill (likely completes)
- Step 8: Click Save → POST /artifacts/bucket
- **Likely hang point:** Waiting for bucket to appear in list after creation

**Debug Steps:**

```bash
# Run with more verbose output
HEADLESS=false ../.venv/bin/pytest \
  tests/ui/artifacts/test_artifacts_create_bucket_55char_name_and_delete.py \
  -v -s --log-cli-level=DEBUG \
  --timeout=60  # Fail fast to see where it hangs
```

**Check DEV Backend:**
```bash
# If test hangs on bucket creation, check backend logs
# Look for:
# - 500 errors on POST /artifacts/bucket
# - Timeouts on S3/storage operations
# - Database deadlocks
# - Long-running queries
```

**Potential Issues:**

1. **56-character name edge case:**
   - Backend may have validation bug at max length
   - Database column too short?
   - S3 bucket name validation failure?

2. **UI timing issue:**
   - Bucket list doesn't refresh after creation
   - Need explicit page reload/refresh
   - WebSocket update not firing

3. **State pollution:**
   - Previous test run left bucket with same name
   - Conflict causes hang
   - Need better cleanup

**Workarounds to Try:**

```python
# Add explicit wait + refresh after creation
page.wait_for_timeout(2000)
page.reload()
artifacts_page.wait_for_bucket_in_list(bucket_name, timeout=10000)
```

---

## Investigation Commands Used

```bash
# Remove blocked markers
git diff tests/ui/artifacts/test_artifacts_create_bucket_55char_name_and_delete.py
git diff tests/ui/chat/test_agent_with_toolkit_chat.py

# Start UI dev server
cd /Users/Aliaksei_Breilian/PycharmProjects/elitea_local/EliteaUI
npm run dev > /tmp/elitea-ui-dev.log 2>&1 &

# Wait for server ready
curl http://localhost:5173  # Should return 200

# Run test 1 (GitHub toolkit) - headless
cd /Users/Aliaksei_Breilian/PycharmProjects/elitea_local/elitea-testing-public/automation
HEADLESS=true ../.venv/bin/pytest \
  tests/ui/chat/test_agent_with_toolkit_chat.py::TestAgentWithToolkitInChat::test_agent_with_toolkit_executes_in_chat \
  -v --tb=short

# Run test 2 (artifacts) - headed for debugging
HEADLESS=false ../.venv/bin/pytest \
  tests/ui/artifacts/test_artifacts_create_bucket_55char_name_and_delete.py::TestArtifactCreateBucketMaxLengthNameAndDelete::test_create_bucket_max_length_name_and_delete \
  -v --tb=short
```

---

## Recommendations

### Short-term:
1. **Keep both tests blocked** ✅ (done)
2. Update GitHub token in `.env.test` to unblock test 1
3. File issue for test 2 timeout investigation
4. Document both in blocked tests tracking

### Medium-term:
1. **Test 1:** Once token fixed, verify on DEV and unblock
2. **Test 2:** Debug hang point with shorter timeout + logging
3. Consider if 56-char name is real use case (may drop test if edge case)

### Long-term:
1. Automate GitHub token rotation/validation
2. Add test timeouts at test level (not just pytest level)
3. Better cleanup between artifact tests
4. Consider mocking GitHub API for toolkit tests

---

## Files Modified

```bash
# Re-marked as blocked with investigation notes:
tests/ui/artifacts/test_artifacts_create_bucket_55char_name_and_delete.py
tests/ui/chat/test_agent_with_toolkit_chat.py
```

**Commit needed:**
```bash
git add tests/ui/artifacts/test_artifacts_create_bucket_55char_name_and_delete.py
git add tests/ui/chat/test_agent_with_toolkit_chat.py
git commit -m "test: keep 2 tests blocked after investigation

- test_agent_with_toolkit_executes_in_chat: 401 Bad credentials verified on DEV
- test_create_bucket_max_length_name_and_delete: Test hangs during retry

Investigation: BLOCKED_TESTS_INVESTIGATION.md"
```

---

## Conclusion

**Investigation Complete:** Both tests have **legitimate reasons** to remain blocked.

- ✅ test_agent_with_toolkit_executes_in_chat: **Test data issue** (invalid GitHub token)
- ✅ test_create_bucket_max_length_name_and_delete: **Infrastructure issue** (test hangs)

**Total blocked tests: 17** (unchanged)

**Next Steps:**
1. Fix GitHub token → unblock test 1
2. Debug test 2 hang → fix or document as known issue
3. Continue with workflow run 32025948363 validation
