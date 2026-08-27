# Creating Approved Issues in Board #9

How to file tracking issues that land in the Test Automation Factory project (board #9) with **Approved** status, skipping the human approval gate.

---

## Why "Approved" Status Matters

The board status machine (`.agents/profile.md` § Issue tracker):

```
Todo → Approved (HUMAN-ONLY) → In Progress → Ready → Done (HUMAN-ONLY)
         ^^^^^^                                          ^^^^^^
```

- **Approved** is normally human-only: a human drags cards from `Todo` to `Approved` after vetting them
- For **investigation tasks** (not new feature work), we want to skip that gate and go straight to work
- Setting status to `Approved` at creation = pre-approved work order

---

## Prerequisites

### 1. GitHub CLI Auth Setup (One-Time)

**Identity rule** (`.agents/profile.md` § Issue tracker): NEVER use `GITHUB_TOKEN` for writes.

```bash
# Check current auth status
env -u GITHUB_TOKEN gh auth status

# If not logged in with correct account:
gh auth login
# Choose: GitHub.com, HTTPS, authenticate via browser
# Scopes needed: repo, project, read:org

# Verify correct identity
env -u GITHUB_TOKEN gh auth status
# Should show: YOUR username (from keyring), not a shared token
```

### 2. Get Project Field IDs (Cache Per Session)

Board #9 has a `Status` field with options like `Todo`, `Approved`, `In Progress`, etc. We need their internal IDs.

```bash
# Fetch field metadata (run once per session, cache to file)
env -u GITHUB_TOKEN gh project field-list 9 --owner EliteaAI --format json \
  > /tmp/project-9-fields.json

# Inspect structure
cat /tmp/project-9-fields.json | jq .
```

**Expected structure:**
```json
{
  "fields": [
    {
      "id": "PVTF_lADO...",
      "name": "Status",
      "dataType": "SINGLE_SELECT",
      "options": [
        {"id": "f75ad846", "name": "Todo"},
        {"id": "47fc9ee4", "name": "Approved"},
        {"id": "...", "name": "In Progress"},
        ...
      ]
    },
    ...
  ]
}
```

### 3. Extract Status Field ID and Approved Option ID

```bash
# Status field ID (the column itself)
STATUS_FIELD_ID=$(jq -r '.fields[] | select(.name == "Status") | .id' /tmp/project-9-fields.json)
echo "Status field ID: $STATUS_FIELD_ID"

# Approved option ID (the "Approved" value)
APPROVED_OPTION_ID=$(jq -r '.fields[] | select(.name == "Status") | .options[] | select(.name == "Approved") | .id' /tmp/project-9-fields.json)
echo "Approved option ID: $APPROVED_OPTION_ID"

# Also get project ID (needed for item-edit)
PROJECT_ID=$(env -u GITHUB_TOKEN gh project view 9 --owner EliteaAI --format json | jq -r '.id')
echo "Project ID: $PROJECT_ID"
```

**Save these to session variables:**
```bash
export STATUS_FIELD_ID="PVTF_lADO..."
export APPROVED_OPTION_ID="47fc9ee4"
export PROJECT_ID="PVT_kwDO..."
```

---

## Step-by-Step Issue Creation

### Step 1: Prepare Issue Body

Write body to file first (easier to review):

```bash
cat > /tmp/issue-body.md <<'EOF'
## Summary

Investigate failure of `test_mcp_node_fresh_attach` (ELITEA-2037) — timeout on toolkit attachment.

- **Test:** `automation/tests/ui/pipelines/test_pipeline_mcp_node_fresh_attach.py::test_mcp_node_fresh_attach`
- **TMS case:** ELITEA-2037
- **AFS:** `test-specs/pipelines/l2_pipeline-mcp-node-integration-fresh-attach_ELITEA-2037.md`
- **Failure source:** GHA run #32931571484
- **Failure type:** timeout
- **Environment:** dev.elitea.ai

## Failure Evidence

### Error Message
```
TimeoutError: Timeout 30000ms exceeded.
waiting for locator('[data-testid="pipeline-save-success-notification"]')
```

### Stack Trace
```
automation/pages/pipeline_editor_page.py:156: in save_pipeline
    self.page.wait_for_selector('[data-testid="pipeline-save-success-notification"]', timeout=30000)
```

## Investigation Plan

1. **Reproduce** — confirm timeout with enhanced logging of save response timing
2. **Correlate** — compare test steps vs TMS case for drift
3. **Root cause** — categorize: test timing issue | DEV backend slow | product bug
4. **Resolution** — fix wait strategy | increase timeout | file defect

## Scope

- Branch: main (test already promoted)
- Target environment: dev.elitea.ai

## Out of Scope

- Bulk triage (single-test deep investigation)
EOF

# Review before filing
cat /tmp/issue-body.md
```

### Step 2: Create Issue

```bash
# File issue (captures number)
ISSUE_NUM=$(env -u GITHUB_TOKEN gh issue create \
  --repo EliteaAI/elitea-testing-public \
  --title "[Investigate][ELITEA-2037] test_mcp_node_fresh_attach — timeout on save" \
  --body-file /tmp/issue-body.md \
  --json number --jq '.number')

echo "Created issue #${ISSUE_NUM}"
```

**Important notes:**
- `env -u GITHUB_TOKEN` prefix is **mandatory** (identity rule)
- Title format: `[Investigate][CASE-ID] test_name — brief`
- Body from file (not inline string — easier to review)
- `--json number --jq '.number'` extracts just the issue number for next step

### Step 3: Add Issue to Project Board

```bash
# Add to board #9 (returns item ID)
ITEM_ID=$(env -u GITHUB_TOKEN gh project item-add 9 --owner EliteaAI \
  --url "https://github.com/EliteaAI/elitea-testing-public/issues/${ISSUE_NUM}" \
  --format json | jq -r '.id')

echo "Added to board #9 as item ${ITEM_ID}"
```

**At this point:**
- Issue exists: `https://github.com/EliteaAI/elitea-testing-public/issues/${ISSUE_NUM}`
- Card exists on board #9
- Status: **`Todo`** (default for new items)

### Step 4: Set Status to Approved

```bash
# Update item status
env -u GITHUB_TOKEN gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "$STATUS_FIELD_ID" \
  --single-select-option-id "$APPROVED_OPTION_ID"

echo "Status set to Approved"
```

**Verification:**
```bash
# Check item status
env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --format json --limit 200 \
  | jq ".items[] | select(.content.number == ${ISSUE_NUM}) | {number: .content.number, title: .content.title, status: .status}"
```

Expected output:
```json
{
  "number": 1776,
  "title": "[Investigate][ELITEA-2037] test_mcp_node_fresh_attach — timeout on save",
  "status": "Approved"
}
```

---

## Complete Script (Copy-Paste Ready)

```bash
#!/bin/bash
set -euo pipefail

# Prerequisites: gh auth login already done with correct account

# 1. Cache field IDs (run once per session)
if [ ! -f /tmp/project-9-fields.json ]; then
  env -u GITHUB_TOKEN gh project field-list 9 --owner EliteaAI --format json \
    > /tmp/project-9-fields.json
fi

# 2. Extract IDs
STATUS_FIELD_ID=$(jq -r '.fields[] | select(.name == "Status") | .id' /tmp/project-9-fields.json)
APPROVED_OPTION_ID=$(jq -r '.fields[] | select(.name == "Status") | .options[] | select(.name == "Approved") | .id' /tmp/project-9-fields.json)
PROJECT_ID=$(env -u GITHUB_TOKEN gh project view 9 --owner EliteaAI --format json | jq -r '.id')

echo "Status field: $STATUS_FIELD_ID"
echo "Approved option: $APPROVED_OPTION_ID"
echo "Project ID: $PROJECT_ID"

# 3. Prepare body
cat > /tmp/issue-body.md <<'EOF'
## Summary

<Fill in summary>

- **Test:** `<node-id>`
- **TMS case:** ELITEA-XXXX
- **AFS:** `<path>`
- **Failure source:** <GHA run | local>
- **Failure type:** <category>
- **Environment:** <localhost | dev.elitea.ai>

## Failure Evidence

<paste evidence>

## Investigation Plan

1. Reproduce
2. Correlate
3. Root cause
4. Resolve

## Scope

- Branch: <automation/base | main>
- Target environment: <env>
EOF

echo "Edit /tmp/issue-body.md now, then press Enter to continue..."
read

# 4. Create issue
ISSUE_NUM=$(env -u GITHUB_TOKEN gh issue create \
  --repo EliteaAI/elitea-testing-public \
  --title "[Investigate][ELITEA-XXXX] test_name — brief" \
  --body-file /tmp/issue-body.md \
  --json number --jq '.number')

echo "Created issue #${ISSUE_NUM}"

# 5. Add to board
ITEM_ID=$(env -u GITHUB_TOKEN gh project item-add 9 --owner EliteaAI \
  --url "https://github.com/EliteaAI/elitea-testing-public/issues/${ISSUE_NUM}" \
  --format json | jq -r '.id')

echo "Added to board #9 as item ${ITEM_ID}"

# 6. Set status to Approved
env -u GITHUB_TOKEN gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "$STATUS_FIELD_ID" \
  --single-select-option-id "$APPROVED_OPTION_ID"

echo "Status set to Approved"

# 7. Verify
env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --format json --limit 200 \
  | jq ".items[] | select(.content.number == ${ISSUE_NUM}) | {number: .content.number, status: .status}"

echo "✅ Issue #${ISSUE_NUM} created and approved"
echo "   View: https://github.com/EliteaAI/elitea-testing-public/issues/${ISSUE_NUM}"
```

---

## Troubleshooting

### Error: "your authentication token is missing required scopes [project]"

**Problem:** Using `GITHUB_TOKEN` (shared token, no project scope)

**Solution:** Prefix with `env -u GITHUB_TOKEN`
```bash
env -u GITHUB_TOKEN gh project item-edit ...
```

### Error: "field-id not found"

**Problem:** `STATUS_FIELD_ID` extraction failed or wrong project

**Solution:** Re-fetch fields:
```bash
rm /tmp/project-9-fields.json
env -u GITHUB_TOKEN gh project field-list 9 --owner EliteaAI --format json \
  > /tmp/project-9-fields.json
cat /tmp/project-9-fields.json | jq '.fields[] | select(.name == "Status")'
```

### Error: "option-id not found"

**Problem:** "Approved" option doesn't exist or was renamed

**Solution:** List all status options:
```bash
jq -r '.fields[] | select(.name == "Status") | .options[] | "\(.name): \(.id)"' \
  /tmp/project-9-fields.json
```

### Issue Created But Not on Board

**Problem:** `gh project item-add` failed silently

**Solution:** Add manually:
```bash
env -u GITHUB_TOKEN gh project item-add 9 --owner EliteaAI \
  --url "https://github.com/EliteaAI/elitea-testing-public/issues/${ISSUE_NUM}"
```

### Issue on Board But Status Still "Todo"

**Problem:** `gh project item-edit` failed or wrong IDs

**Solution:** Get current item state:
```bash
env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --format json \
  | jq ".items[] | select(.content.number == ${ISSUE_NUM})"
```

Then retry status update with correct IDs.

---

## Assignment Convention

Per team convention (`.agents/profile.md` § Issue tracker):

- **File unassigned** — issue starts with no assignee
- **Self-assign when starting work** — agent adds `--add-assignee "@me"` when beginning Phase 2
- **Self-unassign when done** — agent removes `--remove-assignee "@me"` at Phase 6 (handoff to human)

```bash
# At Phase 2 start
env -u GITHUB_TOKEN gh issue edit ${ISSUE_NUM} --add-assignee "@me"

# At Phase 6 end
env -u GITHUB_TOKEN gh issue edit ${ISSUE_NUM} --remove-assignee "@me"
```

---

## Board Movement Through Phases

| Phase | Status | Who Moves |
|---|---|---|
| Created | `Approved` | Agent (this doc) |
| Phase 2 starts | `In Progress` | Agent (manual or auto when self-assigning) |
| Phase 5 complete, PR opened | `In Progress` | Leave as-is (human reviews PR) |
| Phase 5 complete, blocked on bug | `Blocked` | Agent moves |
| Phase 6 complete, ready for human acceptance | `Ready` | Agent moves |
| Human accepts work | `Done` | **Human only** (agent never closes) |

**Move to Blocked:**
```bash
BLOCKED_OPTION_ID=$(jq -r '.fields[] | select(.name == "Status") | .options[] | select(.name == "Blocked") | .id' /tmp/project-9-fields.json)

env -u GITHUB_TOKEN gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "$STATUS_FIELD_ID" \
  --single-select-option-id "$BLOCKED_OPTION_ID"
```

**Move to Ready:**
```bash
READY_OPTION_ID=$(jq -r '.fields[] | select(.name == "Status") | .options[] | select(.name == "Ready") | .id' /tmp/project-9-fields.json)

env -u GITHUB_TOKEN gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "$STATUS_FIELD_ID" \
  --single-select-option-id "$READY_OPTION_ID"
```

---

## Related Documentation

- `.agents/profile.md` § Issue tracker — board status machine, identity rule
- `.agents/profile.md` § Board #9 rules — only elitea-testing-public issues, cross-repo links via comments
- `issue-tracking` skill — general GitHub issue operations
- `batch-promote` skill § Stage 0 — similar board manipulation pattern

---

## Version History

- **1.0.0** (2026-08-26): Initial version — complete Approved-issue creation procedure
