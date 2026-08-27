---
name: process-test-failure
description: Intake and triage test failures - extract logs/artifacts, classify failure type, find TMS case, upload local evidence, create 'Approved' tracking issue in board #9 as work order for investigation agent. NO reproduction or reruns - analyzes existing evidence only. Use when test fails and needs investigation work order created.
allowed-tools:
  - Bash
  - Read
  - Grep
---

# Process Test Failure — Intake & Triage

**Lightweight intake workflow** that extracts failure evidence, classifies if possible, and creates an **Approved tracking issue** in board #9 as a work order for another agent to investigate and fix.

**This skill does NOT reproduce, rerun, or fix tests.** It only prepares the investigation briefing from existing logs and artifacts.

## When to Use

- Test failed in CI (GHA run ID available)
- Test failed locally (logs/screenshots/video available on disk)
- Need to create investigation work order for another agent
- NOT for bulk triage (use `investigate-and-fix-tests` for N>5 failures)

## Prerequisites

- Test failure details: **either** GHA run ID **or** local logs/artifacts paths
- Test node ID (if known) OR ability to extract from logs

## What This Skill Does

✅ **Extracts** failure evidence from GHA or local filesystem  
✅ **Parses** test identity, failure type, stack trace  
✅ **Finds** TMS case and AFS  
✅ **Uploads** local artifacts to GitHub release (if not already accessible)  
✅ **Classifies** failure type (if clear from logs)  
✅ **Creates** Approved tracking issue in board #9 with complete briefing  

## What This Skill Does NOT Do

❌ Does NOT reproduce or rerun tests  
❌ Does NOT investigate root cause beyond log analysis  
❌ Does NOT fix test code  
❌ Does NOT file bugs  
❌ Does NOT correlate with TMS case (investigation agent does this)  

**The Approved issue is a trigger for investigation agent** (e.g. `qa-engineer`, `test-automation-engineer`) who will actually reproduce, investigate, and fix.

---

## The Four-Step Process

```
1. EXTRACT    → Parse logs, identify test, gather artifacts
2. CLASSIFY   → Determine failure type from logs (if clear)
3. PREPARE    → Find TMS case, upload artifacts, draft briefing
4. FILE       → Create Approved issue in board #9
```

---

## Step 1: Extract Failure Evidence

### From GHA Run

```bash
# 1. Get run logs
env -u GITHUB_TOKEN gh run view <RUN_ID> --repo EliteaAI/elitea-testing-public --log \
  | tee /tmp/gh-run-<RUN_ID>.log

# 2. Extract FAILED tests section
grep -B5 -A30 "FAILED" /tmp/gh-run-<RUN_ID>.log | tee /tmp/failures-<RUN_ID>.txt

# 3. Download artifacts (screenshots, allure-results, video if available)
env -u GITHUB_TOKEN gh run download <RUN_ID> --repo EliteaAI/elitea-testing-public \
  --dir /tmp/gh-artifacts-<RUN_ID>

# 4. List what's available
find /tmp/gh-artifacts-<RUN_ID> -type f | tee /tmp/artifacts-inventory.txt
```

**GHA artifacts are already accessible via run URL** - note their presence, no need to re-upload.

---

### From Local Run

```bash
# 1. User provides paths to:
#    - Log file (pytest output)
#    - Screenshots (automation/screenshots/)
#    - Video (if available)
#    - Allure results (automation/reports/allure-results/)

# 2. Read log
cat <user-provided-log-path> | tee /tmp/local-failure.log

# 3. Inventory local artifacts
ls -lh automation/screenshots/ | tail -10
ls -lh automation/videos/ 2>/dev/null | tail -5
ls -lh automation/reports/allure-results/ | tail -10

# 4. Note: Local artifacts WILL need uploading (see Step 3)
```

---

## Step 2: Parse Test Identity & Failure Type

### Extract from Logs

**1. Test Node ID**
```bash
# From pytest output: FAILED automation/tests/ui/.../test_x.py::TestClass::test_method
grep "^FAILED " /tmp/failures-<RUN_ID>.txt | head -1

# Extract just the path
NODE_ID=$(grep "^FAILED " /tmp/failures-<RUN_ID>.txt | head -1 | awk '{print $2}' | sed 's/ .*//')
echo "Test node ID: $NODE_ID"
```

**2. Failure Type** (classify from error message):

| Pattern in Logs | Classification |
|---|---|
| `TimeoutError`, `timeout.*exceeded` | **timeout** |
| `ElementNotFoundError`, `locator.*not found`, `waiting for.*timed out` | **element-not-found** |
| `AssertionError`, `assert.*failed`, `Expected.*but got` | **assertion-failure** |
| `4xx`, `5xx`, `HTTPError`, `RequestException`, `API.*error` | **api-error** |
| `Exception`, `Error` (other) | **exception** |
| Cannot determine | **unknown** |

```bash
# Simple keyword search
ERROR_LINE=$(grep -A20 "^FAILED " /tmp/failures-<RUN_ID>.txt | tail -1)

if echo "$ERROR_LINE" | grep -qi "timeout"; then
  FAILURE_TYPE="timeout"
elif echo "$ERROR_LINE" | grep -qi "not found"; then
  FAILURE_TYPE="element-not-found"
elif echo "$ERROR_LINE" | grep -qi "assert"; then
  FAILURE_TYPE="assertion-failure"
elif echo "$ERROR_LINE" | grep -qiE "(4[0-9]{2}|5[0-9]{2}|http.*error)"; then
  FAILURE_TYPE="api-error"
else
  FAILURE_TYPE="unknown"
fi

echo "Failure type: $FAILURE_TYPE"
```

**3. Stack Trace** (last 10-15 lines)
```bash
grep -A15 "^FAILED " /tmp/failures-<RUN_ID>.txt | grep "^  " | tail -15 > /tmp/stack-trace.txt
```

**4. Error Message** (last line)
```bash
grep -A20 "^FAILED " /tmp/failures-<RUN_ID>.txt | tail -1 > /tmp/error-message.txt
```

**5. Confidence Level**
- **HIGH**: Pattern clearly matches one type, error message is specific
- **MEDIUM**: Multiple possible types, error message ambiguous
- **LOW**: Cannot determine from logs, needs reproduction

---

## Step 3: Prepare Investigation Briefing

### Find TMS Case

```bash
# 1. Extract test file path from node ID
TEST_FILE=$(echo "$NODE_ID" | sed 's/::.*//')  # strips ::Class::method
echo "Test file: $TEST_FILE"

# 2. Extract case ID from test file docstring
CASE_ID=$(grep -oE "ELITEA-[0-9]+" "$TEST_FILE" | head -1)
echo "TMS case: ${CASE_ID:-not found}"

# 3. Note case file path (don't read - investigation agent will)
if [ -n "$CASE_ID" ]; then
  CASE_FILE="../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/**/${CASE_ID}.md"
  echo "Case file: $CASE_FILE"
fi
```

### Find AFS

```bash
# AFS pattern: test-specs/<feature>/l<pri>_<slug>_<CASE-ID>.md
if [ -n "$CASE_ID" ]; then
  AFS_FILE=$(find test-specs -name "*${CASE_ID}*" -type f 2>/dev/null)
  echo "AFS: ${AFS_FILE:-not found}"
fi
```

### Determine Test Location (Critical for Fix Branch Strategy)

**This determines which branch the investigation agent should work on:**

```bash
# Check if test exists on main (promoted) or only on automation/base

# 1. Fetch latest
git fetch origin main automation/base --no-tags

# 2. Check where test file exists
TEST_ON_MAIN=$(git ls-tree -r origin/main --name-only | grep -F "$TEST_FILE" || echo "")
TEST_ON_BASE=$(git ls-tree -r origin/automation/base --name-only | grep -F "$TEST_FILE" || echo "")

if [ -n "$TEST_ON_MAIN" ]; then
  # Test is promoted to main
  TEST_LOCATION="main"
  FIX_BRANCH_STRATEGY="Cut fix branch from main, PR to main"
  echo "✓ Test found on main (promoted)"
else
  if [ -n "$TEST_ON_BASE" ]; then
    # Test only on automation/base (not promoted yet)
    TEST_LOCATION="automation/base"
    FIX_BRANCH_STRATEGY="Cut fix branch from automation/base, PR to automation/base"
    echo "✓ Test found on automation/base (not promoted)"
  else
    # Test not found on either (may be in work branch or deleted)
    TEST_LOCATION="unknown"
    FIX_BRANCH_STRATEGY="Investigate test location first"
    echo "⚠ Test not found on main or automation/base"
  fi
fi

echo "Test location: $TEST_LOCATION"
echo "Fix strategy: $FIX_BRANCH_STRATEGY"
```

**Why this matters:**

From issue #1776 (correct pattern):
```
**Branch:** main (test already promoted)
**Scope:** ... work on this environment (Keycloak auth, `/app` prefix, live DEV backend/WebSocket timing) 
rather than localhost, and fix anything DEV-specific ... cut a fix branch from main per normal PR flow, 
still targeting main since that's where this test now lives
```

From issue #1800 (incorrect — fixed on automation/base when should be main):
- Test was on main (promoted)
- Fix PR opened to automation/base (wrong target)
- Should have been: fix branch from main → PR to main

**Rule:**
- **Test on main** → Fix on main (tests already delivered to users)
- **Test on automation/base** → Fix on automation/base (tests not promoted yet)

### Upload Local Artifacts (Local Runs Only)

**Skip this for GHA runs** - artifacts are already accessible via run URL.

```bash
# Upload screenshots to evidence release
if [ -d automation/screenshots ]; then
  for img in automation/screenshots/*.png; do
    [ -f "$img" ] || continue
    echo "Uploading $(basename $img)..."
    env -u GITHUB_TOKEN gh release upload evidence "$img" --clobber \
      --repo EliteaAI/elitea-testing-public
  done
fi

# Upload video if exists
if [ -f automation/videos/test_recording.mp4 ]; then
  echo "Uploading test_recording.mp4..."
  env -u GITHUB_TOKEN gh release upload evidence automation/videos/test_recording.mp4 --clobber \
    --repo EliteaAI/elitea-testing-public
fi

# Note: Allure JSON is too large - investigation agent will regenerate if needed
```

---

## Step 4: Create Approved Tracking Issue

### Issue Title Format

`[Fix][CASE-ID] test_name — <brief failure type>`

Examples:
- `[Fix][ELITEA-2037] test_mcp_node_fresh_attach — timeout on save`
- `[Fix][ELITEA-1950] test_agent_creation — assertion on notification text`
- `[Fix][ELITEA-1823] test_pipeline_run — element not found`

**Note:** Title is `[Fix]` not `[Investigate]` - agent's job is to FIX the test, not just investigate.

### Issue Body Template

```markdown
## Summary

**Fix this test failure:** `<test_method_name>` (CASE-ID)

- **Test:** `<full-node-id>`
- **TMS case:** <CASE-ID or "not found">
- **AFS:** `<path>` (or "not found")
- **Failure source:** <GHA run #NNNN | local run YYYY-MM-DD>
- **Environment:** <localhost:5173 | dev.elitea.ai | next.elitea.ai>

**Goal:** Reproduce, investigate, and **DELIVER A FIX** (PR, bug filing, or clarification)

## Failure Classification

**Type:** <timeout | element-not-found | assertion-failure | api-error | exception | unknown>

**Confidence:** <HIGH | MEDIUM | LOW> — <brief reason>

## Failure Evidence

### Error Message
```
<paste last error line>
```

### Stack Trace (last 10-15 lines)
```
<paste stack trace from /tmp/stack-trace.txt>
```

### Full Logs
<GHA: Link to run https://github.com/EliteaAI/elitea-testing-public/actions/runs/<RUN_ID>>
<Local: Paste relevant log section (30-50 lines around failure)>

### Artifacts

**Screenshots:**
<GHA: Available in run artifacts - https://github.com/EliteaAI/elitea-testing-public/actions/runs/<RUN_ID>#artifacts>
<Local: Uploaded to evidence release>
- ![screenshot-1](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/<file1>.png)
- ![screenshot-2](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/<file2>.png)

**Video:** <link if uploaded, or "not available">

**Allure report:** <path or "not available">

## Initial Analysis (from logs only)

<Optional: observations from logs, WITHOUT reproducing>

Examples:
- "Timeout (30s) waiting for `[data-testid="pipeline-save-success-notification"]`"
- "AssertionError: expected 'Success' in notification, actual text not captured in logs"
- "Element `[data-testid="agent-form-save-button"]` not found - possible testid missing or renamed"
- "Cannot determine from logs alone - needs reproduction and enhanced logging"

## Work Scope — FIX THE TEST

**Your job: FIX this test failure, not just investigate.**

**Required workflow:**

1. **Reproduce** — confirm failure on <environment>, add enhanced logging if needed
2. **Correlate** — map test steps vs TMS case <CASE-ID> for drift (identifies what KIND of fix needed)
3. **Root cause** — determine: test code issue | test drift | case drift | product bug | env issue
4. **FIX & DELIVER:**
   - **Test code issue** → Fix test code, open PR (see Fix Branch Strategy below)
   - **Test drift** → Update test to match case, open PR
   - **Case drift** → File case clarification in TMS repo
   - **Product bug** → File bug in elitea-testing-public, mark test with `expect.soft()` + bug link
   - **Env issue** → Add conditional skip, document reason

**Test location:** `<test-file-path>`

**CRITICAL:** Do NOT stop after investigation. Issue is complete ONLY when:
- ✅ PR opened (for test fixes), OR
- ✅ Bug filed + test marked (for product defects), OR  
- ✅ Case clarification filed (for case drift), OR
- ✅ Skip added + documented (for env issues)

### Fix Branch Strategy

**Test is on:** <main | automation/base | unknown>

**Fix instructions:**

<If test is on MAIN:>
- **Branch from:** `main`
- **PR target:** `main`
- **Why:** Test already promoted to main (delivered). Fixes to already-promoted tests MUST go to main, not automation/base.
- **Example:** See issue #1776 (correct pattern)

<If test is on automation/base:>
- **Branch from:** `automation/base`
- **PR target:** `automation/base`
- **Why:** Test not promoted yet. Fixes go to automation/base until batch promotion.

<If test location unknown:>
- **First step:** Investigate where test actually lives before starting fix
- Check: work branches, recent deletions, renamed files

**Expected deliverables (MANDATORY):**

Choose ONE based on root cause:

1. **Test code fix → PR opened** to correct branch (main or automation/base)
   - Includes: fix commit, 3/3 green verification, PR description
   
2. **Product bug → Bug filed + test marked**
   - Bug issue in elitea-testing-public (with evidence)
   - Test marked with `@pytest.mark.blocked` + `@pytest.mark.bug` OR `expect.soft()` + bug link
   - PR opened with test marking
   
3. **Case drift → Case clarification filed**
   - Clarification issue in onetest-ai-tm-Elitea repo
   - Test stays as-is (test is correct, case needs update)
   
4. **Env issue → Skip added + documented**
   - Test marked with `@pytest.mark.skipif(env=="dev")` + reason
   - PR opened with skip + documentation

**NOT acceptable:** "Investigated, root cause is X" with no PR/bug/clarification. MUST deliver fix.
```

### File Issue with Approved Status

```bash
# 1. Prepare body (fill template with extracted data)
cat > /tmp/issue-body.md <<'EOF'
<Fill template above with all extracted data>
EOF

# 2. Review before filing
cat /tmp/issue-body.md

# 3. File issue
ISSUE_NUM=$(env -u GITHUB_TOKEN gh issue create \
  --repo EliteaAI/elitea-testing-public \
  --title "[Fix][${CASE_ID}] <test_method_name> — ${FAILURE_TYPE}" \
  --body-file /tmp/issue-body.md \
  --json number --jq '.number')

echo "Created issue #${ISSUE_NUM}"
```

### Add to Board #9 and Set to Approved

```bash
# 1. Cache project field IDs (run once per session)
if [ ! -f /tmp/project-9-fields.json ]; then
  env -u GITHUB_TOKEN gh project field-list 9 --owner EliteaAI --format json \
    > /tmp/project-9-fields.json
fi

# 2. Extract IDs
STATUS_FIELD_ID=$(jq -r '.fields[] | select(.name == "Status") | .id' /tmp/project-9-fields.json)
APPROVED_OPTION_ID=$(jq -r '.fields[] | select(.name == "Status") | .options[] | select(.name == "Approved") | .id' /tmp/project-9-fields.json)
PROJECT_ID=$(env -u GITHUB_TOKEN gh project view 9 --owner EliteaAI --format json | jq -r '.id')

echo "Status field ID: $STATUS_FIELD_ID"
echo "Approved option ID: $APPROVED_OPTION_ID"
echo "Project ID: $PROJECT_ID"

# 3. Add issue to board
ITEM_ID=$(env -u GITHUB_TOKEN gh project item-add 9 --owner EliteaAI \
  --url "https://github.com/EliteaAI/elitea-testing-public/issues/${ISSUE_NUM}" \
  --format json | jq -r '.id')

echo "Added to board #9 as item ${ITEM_ID}"

# 4. Set status to Approved
env -u GITHUB_TOKEN gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "$STATUS_FIELD_ID" \
  --single-select-option-id "$APPROVED_OPTION_ID"

echo "Status set to Approved"

# 5. Verify
env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --format json --limit 200 \
  | jq ".items[] | select(.content.number == ${ISSUE_NUM}) | {number: .content.number, status: .status}"
```

---

## Output

Report to human:

```
✅ Intake Complete

**Tracking issue:** #<NUM>
**Test:** `<node-id>`
**TMS case:** <CASE-ID>
**Failure type:** <type> (confidence: <HIGH|MEDIUM|LOW>)

**Board:** Added to #9, status: Approved
**Artifacts:** <GHA run link | N screenshots uploaded to evidence release>

**Next:** Investigation agent will:
- Reproduce failure
- Correlate with TMS case
- Determine root cause
- Fix or file bugs as appropriate

**View issue:** https://github.com/EliteaAI/elitea-testing-public/issues/<NUM>
```

---

## Complete Script (Copy-Paste Ready)

```bash
#!/bin/bash
set -euo pipefail

# Usage: ./process-test-failure.sh <GHA-RUN-ID | local>

SOURCE="$1"  # "12345" for GHA run ID, or "local" for local run

# ============================================================================
# Step 1: Extract Evidence
# ============================================================================

if [ "$SOURCE" != "local" ]; then
  # GHA run
  RUN_ID="$SOURCE"
  echo "Extracting from GHA run #$RUN_ID..."
  
  env -u GITHUB_TOKEN gh run view "$RUN_ID" --repo EliteaAI/elitea-testing-public --log \
    | tee /tmp/gh-run-$RUN_ID.log
  
  grep -B5 -A30 "FAILED" /tmp/gh-run-$RUN_ID.log | tee /tmp/failures-$RUN_ID.txt
  
  env -u GITHUB_TOKEN gh run download "$RUN_ID" --repo EliteaAI/elitea-testing-public \
    --dir /tmp/gh-artifacts-$RUN_ID || true
  
  LOG_FILE="/tmp/failures-$RUN_ID.txt"
  SOURCE_DESC="GHA run #$RUN_ID"
  ARTIFACTS_URL="https://github.com/EliteaAI/elitea-testing-public/actions/runs/$RUN_ID#artifacts"
else
  # Local run
  echo "Processing local run..."
  echo "Provide log file path:"
  read LOG_PATH
  cat "$LOG_PATH" | tee /tmp/local-failure.log
  LOG_FILE="/tmp/local-failure.log"
  SOURCE_DESC="local run $(date +%Y-%m-%d)"
  
  # Upload local artifacts
  echo "Uploading local artifacts..."
  for img in automation/screenshots/*.png 2>/dev/null; do
    [ -f "$img" ] || continue
    env -u GITHUB_TOKEN gh release upload evidence "$img" --clobber \
      --repo EliteaAI/elitea-testing-public
  done
  ARTIFACTS_URL="https://github.com/EliteaAI/elitea-testing-public/releases/tag/evidence"
fi

# ============================================================================
# Step 2: Parse Test Identity & Failure Type
# ============================================================================

NODE_ID=$(grep "^FAILED " "$LOG_FILE" | head -1 | awk '{print $2}' | sed 's/ .*//')
TEST_FILE=$(echo "$NODE_ID" | sed 's/::.*//')
TEST_METHOD=$(echo "$NODE_ID" | grep -oE '::[^:]+$' | sed 's/:://')

echo "Test: $NODE_ID"

# Classify failure type
ERROR_LINE=$(grep -A20 "^FAILED " "$LOG_FILE" | tail -1)

if echo "$ERROR_LINE" | grep -qi "timeout"; then
  FAILURE_TYPE="timeout"
  CONFIDENCE="HIGH"
elif echo "$ERROR_LINE" | grep -qi "not found"; then
  FAILURE_TYPE="element-not-found"
  CONFIDENCE="HIGH"
elif echo "$ERROR_LINE" | grep -qi "assert"; then
  FAILURE_TYPE="assertion-failure"
  CONFIDENCE="HIGH"
elif echo "$ERROR_LINE" | grep -qiE "(4[0-9]{2}|5[0-9]{2}|http.*error)"; then
  FAILURE_TYPE="api-error"
  CONFIDENCE="MEDIUM"
else
  FAILURE_TYPE="unknown"
  CONFIDENCE="LOW"
fi

echo "Failure type: $FAILURE_TYPE (confidence: $CONFIDENCE)"

# Extract stack trace
grep -A15 "^FAILED " "$LOG_FILE" | grep "^  " | tail -15 > /tmp/stack-trace.txt

# ============================================================================
# Step 3: Find TMS Case & AFS & Determine Test Location
# ============================================================================

CASE_ID=$(grep -oE "ELITEA-[0-9]+" "$TEST_FILE" 2>/dev/null | head -1 || echo "not-found")
echo "TMS case: $CASE_ID"

if [ "$CASE_ID" != "not-found" ]; then
  AFS_FILE=$(find test-specs -name "*${CASE_ID}*" -type f 2>/dev/null || echo "not found")
else
  AFS_FILE="not found"
fi
echo "AFS: $AFS_FILE"

# Determine test location (critical for fix branch strategy)
echo "Checking test location..."
git fetch origin main automation/base --no-tags

TEST_ON_MAIN=$(git ls-tree -r origin/main --name-only | grep -F "$TEST_FILE" || echo "")
TEST_ON_BASE=$(git ls-tree -r origin/automation/base --name-only | grep -F "$TEST_FILE" || echo "")

if [ -n "$TEST_ON_MAIN" ]; then
  TEST_LOCATION="main"
  FIX_INSTRUCTIONS="Branch from: main → PR target: main (test already promoted)"
  echo "✓ Test found on main (promoted)"
else
  if [ -n "$TEST_ON_BASE" ]; then
    TEST_LOCATION="automation/base"
    FIX_INSTRUCTIONS="Branch from: automation/base → PR target: automation/base (not promoted)"
    echo "✓ Test found on automation/base"
  else
    TEST_LOCATION="unknown"
    FIX_INSTRUCTIONS="Investigate test location first (not found on main or automation/base)"
    echo "⚠ Test not found on main or automation/base"
  fi
fi

# ============================================================================
# Step 4: Create Approved Issue
# ============================================================================

cat > /tmp/issue-body.md <<EOF
## Summary

Test failure triage for \`$TEST_METHOD\` ($CASE_ID).

- **Test:** \`$NODE_ID\`
- **TMS case:** $CASE_ID
- **AFS:** \`$AFS_FILE\`
- **Failure source:** $SOURCE_DESC
- **Environment:** <fill from context>

## Failure Classification

**Type:** $FAILURE_TYPE

**Confidence:** $CONFIDENCE

## Failure Evidence

### Error Message
\`\`\`
$(tail -1 "$LOG_FILE")
\`\`\`

### Stack Trace
\`\`\`
$(cat /tmp/stack-trace.txt)
\`\`\`

### Full Logs
$ARTIFACTS_URL

### Artifacts
$ARTIFACTS_URL

## Initial Analysis

<From logs: $(echo "$ERROR_LINE" | head -c 200)...>

## Investigation Scope

1. Reproduce on <environment>
2. Correlate with TMS case $CASE_ID
3. Root cause analysis
4. Resolve: fix | clarification | bug

**Test file:** \`$TEST_FILE\`

### Fix Branch Strategy

**Test is on:** $TEST_LOCATION

**Fix instructions:** $FIX_INSTRUCTIONS

**Why this matters:** Tests already on \`main\` are delivered/promoted. Fixes to promoted tests MUST target \`main\`, not \`automation/base\`. See issue #1776 (correct) vs #1800 (incorrect - fixed on automation/base when should be main).
EOF

# File issue
ISSUE_NUM=$(env -u GITHUB_TOKEN gh issue create \
  --repo EliteaAI/elitea-testing-public \
  --title "[Fix][$CASE_ID] $TEST_METHOD — $FAILURE_TYPE" \
  --body-file /tmp/issue-body.md \
  --json number --jq '.number')

echo "Created issue #${ISSUE_NUM}"

# Add to board #9 with Approved status
if [ ! -f /tmp/project-9-fields.json ]; then
  env -u GITHUB_TOKEN gh project field-list 9 --owner EliteaAI --format json \
    > /tmp/project-9-fields.json
fi

STATUS_FIELD_ID=$(jq -r '.fields[] | select(.name == "Status") | .id' /tmp/project-9-fields.json)
APPROVED_OPTION_ID=$(jq -r '.fields[] | select(.name == "Status") | .options[] | select(.name == "Approved") | .id' /tmp/project-9-fields.json)
PROJECT_ID=$(env -u GITHUB_TOKEN gh project view 9 --owner EliteaAI --format json | jq -r '.id')

ITEM_ID=$(env -u GITHUB_TOKEN gh project item-add 9 --owner EliteaAI \
  --url "https://github.com/EliteaAI/elitea-testing-public/issues/${ISSUE_NUM}" \
  --format json | jq -r '.id')

env -u GITHUB_TOKEN gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "$STATUS_FIELD_ID" \
  --option-id "$APPROVED_OPTION_ID"

echo "✅ Intake complete: issue #${ISSUE_NUM} filed and approved"
```

---

## Anti-Patterns

❌ **Don't:**
- Reproduce the test yourself (that's investigation agent's job)
- Make assumptions about root cause without evidence from logs
- File bugs (that's investigation agent's job after confirmation)
- Correlate with TMS case in detail (that's investigation agent's job)
- Fix test code (that's investigation agent's job)
- **❌ CRITICAL: Skip test location check** — investigation agent MUST know which branch to target

✅ **Do:**
- Extract all available evidence from logs/artifacts
- Upload local artifacts so they're accessible
- Classify what you CAN determine from logs
- Be honest about confidence level
- Create complete briefing for investigation agent
- Set issue to Approved status
- **✅ CRITICAL: Always check if test is on main vs automation/base** — this determines fix branch strategy

---

## Common Mistake: Wrong PR Target (Issue #1800)

**Problem:** Test was on `main` (promoted), but fix PR opened to `automation/base`

**Why it's wrong:** Tests on `main` are delivered. Fixes MUST go to `main`, not `automation/base`.

**How this skill prevents it:** 
1. Checks `git ls-tree origin/main` for test file
2. If found on main → explicitly states "Branch from: main → PR target: main"
3. Issue body explains WHY this matters

**Investigation agent's responsibility:** Follow the fix instructions in the issue exactly

---

## Related Documentation

- `.agents/profile.md` § Issue tracker — board #9 mechanics, identity rule
- `references/approved-issue-creation.md` — detailed board manipulation procedure

---

## Version History

- **2.0.0** (2026-08-26): **Breaking change** — now intake-only, no reproduction/investigation
- **1.0.0** (2026-08-26): Original full 5-phase investigation (deprecated)
