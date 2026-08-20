# Investigate and Fix Tests

A systematic workflow for investigating test failures, fixing what's possible, and properly marking blockers.

## When to Use

- Test failures from CI runs
- Investigating deterministic failures
- Fixing or documenting test blockers
- Updating test markers after fixes

## Prerequisites

- Test failure details (run URL or test names)
- Access to test logs
- Understanding of test framework (Playwright + pytest)

## Investigation Workflow

### Phase 1: Gather Information

1. **Extract failure details from CI run**
   ```bash
   env -u GITHUB_TOKEN gh run view <RUN_ID> --log | grep -A20 "FAILED"
   ```

2. **Categorize failures by type:**
   - Timeout errors
   - Element not found
   - Assertion failures
   - Environment issues
   - Product bugs

3. **Check for existing issues:**
   ```bash
   env -u GITHUB_TOKEN gh issue list --repo EliteaAI/elitea-testing-public \
     --label bug --state all --limit 300 --json number,title,state
   ```

### Phase 2: Investigation Strategy

For each failing test:

1. **Read the test file**
   ```bash
   # Find and read the test
   find automation/tests -name "test_*.py" | grep <test_name>
   ```

2. **Understand what it's testing:**
   - Read test docstring
   - Check AFS if referenced
   - Understand expected behavior

3. **Analyze the failure:**
   - Read error message and stack trace
   - Check if it's a known issue (grep for issue numbers in comments)
   - Look for patterns across multiple failures

4. **Categorize root cause:**
   - **Fixable in test code:** Timeout, wait, locator, assertion issues
   - **Product bug:** UI/API behavior wrong
   - **Environment issue:** Backend instability, auth problems
   - **Test data issue:** Missing credentials, wrong test data

### Phase 3: Fix or Document

#### For Fixable Issues

1. **Make the fix:**
   - Increase timeouts if needed
   - Fix locators
   - Improve waits
   - Fix assertions

2. **Test locally:**
   ```bash
   cd automation
   HEADLESS=true ../venv/bin/pytest tests/ui/<path>/test_file.py::test_name -v
   ```

3. **Update markers if needed:**
   - If test had `pytest.mark.new` and is now fixed → change to `pytest.mark.new_verified`
   - Remove `@pytest.mark.blocked` if unblocking
   - Remove `@pytest.mark.bug` if product bug was fixed

#### For Product Bugs

1. **Check if bug already filed:**
   - Search issues with component name
   - Check test file for existing bug references

2. **If bug exists:**
   - Add `@pytest.mark.blocked` to test
   - Add `@pytest.mark.bug` to test
   - Add comment with issue number:
     ```python
     @pytest.mark.blocked
     @pytest.mark.bug
     # Known product bug: #<issue_number> - <brief description>
     def test_something(page):
     ```

3. **If bug doesn't exist:**
   - File new bug:
     ```bash
     env -u GITHUB_TOKEN gh issue create \
       --repo EliteaAI/elitea-testing-public \
       --title "bug: <component> - <brief issue>" \
       --label bug \
       --body "<detailed description with repro steps>"
     ```
   - Mark test as blocked (as above)

#### For Environment Issues

1. **Document in test or skip:**
   ```python
   @pytest.mark.skip(reason="DEV environment issue: <description>")
   def test_something(page):
   ```

2. **Or add conditional skip:**
   ```python
   @pytest.mark.skipif(
       settings.environment == "dev",
       reason="Known instability on DEV: <issue>"
   )
   ```

### Phase 4: Commit and Verify

1. **Stage changes:**
   ```bash
   git add automation/tests/<modified_files>
   ```

2. **Commit with clear message:**
   ```bash
   git commit -m "fix(test): <what was fixed>
   
   - Issue: <describe problem>
   - Fix: <describe solution>
   - Affected tests: <list>
   
   <Additional context if needed>"
   ```

3. **Run affected tests locally to verify:**
   ```bash
   cd automation
   HEADLESS=true ../venv/bin/pytest -k "<test_pattern>" -v
   ```

4. **Push and trigger CI:**
   ```bash
   git push origin <branch>
   env -u GITHUB_TOKEN gh workflow run test-ui-dev-all.yml \
     --ref <branch> -f markers="<marker_to_test>"
   ```

## Decision Tree

```
Test fails
  │
  ├─ Is it a timeout?
  │   ├─ Yes → Increase timeout + verify element actually loads
  │   └─ No → Continue
  │
  ├─ Is element not found?
  │   ├─ Testid missing? → Run add-data-testid skill
  │   ├─ Wrong locator? → Fix locator
  │   └─ Element doesn't exist? → Check if product bug
  │
  ├─ Is it an assertion failure?
  │   ├─ Expected behavior wrong? → Fix assertion
  │   └─ Actual behavior wrong? → Product bug
  │
  ├─ Is it environment instability?
  │   ├─ Random failures? → Add retries or better waits
  │   └─ Consistent on CI only? → Mark skip or environment-specific
  │
  └─ Is it a product bug?
      ├─ Already filed? → Mark test as blocked+bug
      └─ Not filed? → File bug → Mark test
```

## Marker Update Rules

After fixing:

1. **Test was `new` and is now fixed:**
   ```python
   # Before
   pytestmark = [..., pytest.mark.new]
   
   # After
   pytestmark = [..., pytest.mark.new_verified]
   ```

2. **Test was `blocked` and is now unblocked:**
   ```python
   # Before
   @pytest.mark.blocked
   @pytest.mark.bug
   def test_something(page):
   
   # After (remove both markers)
   def test_something(page):
   ```

3. **Test needs to be blocked:**
   ```python
   # Add both markers
   @pytest.mark.blocked
   @pytest.mark.bug
   # Known product bug: #<N> - <description>
   def test_something(page):
   ```

## Bulk Processing

For multiple failing tests:

1. **Group by failure type:**
   - Same error message → likely same root cause
   - Same test file → related functionality
   - Same component → related area

2. **Fix in order:**
   - Quick wins first (timeouts, simple fixes)
   - Product bugs (file and mark)
   - Complex issues last

3. **Commit in logical groups:**
   - One commit per fix type
   - Or one commit per test file
   - Not one giant commit

## Anti-Patterns

❌ **Don't:**
- Fix tests without understanding the failure
- Mark as blocked without filing a bug
- Increase timeouts blindly without verification
- Skip tests without clear reason
- Commit unrelated fixes together

✅ **Do:**
- Understand root cause before fixing
- Test fixes locally before committing
- Document known issues in code
- Update markers consistently
- File bugs for product issues

## Output Format

After investigation, provide:

1. **Summary table:**
   ```
   | Test | Root Cause | Action | Status |
   |------|------------|--------|--------|
   | test_x | Timeout | Increased to 20s | Fixed ✅ |
   | test_y | Product bug #123 | Marked blocked | Blocked 🚫 |
   ```

2. **Commits made:**
   - List commit SHAs and messages

3. **Issues filed:**
   - List issue numbers and titles

4. **Next steps:**
   - What needs verification
   - What needs human decision
   - What's ready to merge
