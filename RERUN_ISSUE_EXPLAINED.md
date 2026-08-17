# Why Run 32002801382 Failed - Root Cause Analysis

## TL;DR

**The workflow ran against `main` branch code instead of `automation/fixes` branch code, so the new markers were not present.**

---

## What Happened

### Run 32002801382 - FAILED

**Triggered with:**
```bash
gh workflow run "UI Tests DEV" \
  --ref automation/fixes \
  -f suite=all \
  -f markers="not new and not blocked and not flaky" \
  -f parallel_jobs=9 \
  -f publish_to_tms=false
```

**Problem:** The `--ref automation/fixes` parameter tells GitHub Actions which branch to USE THE WORKFLOW FILE FROM, but it does NOT set the `ref` input parameter that controls which code to checkout and test.

**Evidence:**
- Log shows: `ref: main` (defaulted from workflow input default)
- Tests ran: All 4 newly marked tests RAN and FAILED/PASSED (not skipped)
- `test_agent_with_toolkit_executes_in_chat` - FAILED (should have been skipped)
- `test_conversation_starter_text_truncated_with_warning` - PASSED (should have been skipped)
- `test_export_agent_no_nested_dependencies` - PASSED (should have been skipped)

---

## The Confusion: Two Different "ref" Parameters

### 1. Workflow Trigger `--ref` (determines workflow file source)
```bash
gh workflow run "UI Tests DEV" --ref automation/fixes
```
This means: "Use the workflow YAML file from the `automation/fixes` branch"

### 2. Workflow Input `-f ref=` (determines code to test)
```yaml
# In test-ui-dev.yml
inputs:
  ref:
    description: 'Git branch/tag/SHA'
    type: string
    default: 'main'  # ← THIS is what controls the checkout
```

This means: "Checkout and test code from this branch"

**They are independent!**

---

## Why The Tests Weren't Skipped

The workflow checked out `main` branch code because:
1. `--ref automation/fixes` set the workflow file source
2. `-f ref=...` was NOT provided
3. Workflow defaulted to `ref: 'main'`
4. Checkout step used `main` branch
5. `main` branch does NOT have commits 840d7dd7 or 4ada3d60
6. Tests don't have `@pytest.mark.blocked` or `@pytest.mark.flaky`
7. Markers `"not new and not blocked and not flaky"` had no effect
8. All tests ran as normal

---

## Correct Command (Run 32006310208 - NOW RUNNING)

```bash
env -u GITHUB_TOKEN gh workflow run "UI Tests DEV" \
  --ref automation/fixes \               # ← Workflow file source
  -f ref=automation/fixes \               # ← Code to test (THIS WAS MISSING)
  -f suite=all \
  -f markers="not new and not blocked and not flaky" \
  -f parallel_jobs=9 \
  -f publish_to_tms=false \
  --repo EliteaAI/elitea-testing-public
```

**Now it will:**
1. Use workflow YAML from `automation/fixes`
2. Checkout and test code from `automation/fixes` (has the markers)
3. Skip all 31 blocked/flaky tests
4. Run only stable tests
5. Should have 0 failures

---

## Lesson Learned

**When triggering GitHub Actions workflows that have a `ref` input parameter:**

```bash
# ❌ WRONG - Tests main code with automation/fixes workflow
gh workflow run "Workflow" --ref my-branch

# ✅ CORRECT - Tests my-branch code with my-branch workflow
gh workflow run "Workflow" --ref my-branch -f ref=my-branch
```

Always pass both:
- `--ref <branch>` - Which workflow file to use
- `-f ref=<branch>` - Which code to test

---

## Verification

Run 32006310208 should show:

```
ref: automation/fixes  # ← Not "main"
```

And these tests should be SKIPPED:
- test_agent_with_toolkit_executes_in_chat (blocked)
- test_conversation_starter_text_truncated_with_warning (flaky)
- test_export_agent_no_nested_dependencies (blocked)
- test_blocked_tool_live_reload_case_insensitive (blocked)
- test_sensitive_tool_live_reload_case_insensitive (blocked)

Plus 26 others marked in commit 840d7dd7.

---

## Current Status

**Run 32006310208:** IN PROGRESS  
**URL:** https://github.com/EliteaAI/elitea-testing-public/actions/runs/32006310208  
**Expected:** SUCCESS (0 failures, ~31 skipped, ~62 passed)
