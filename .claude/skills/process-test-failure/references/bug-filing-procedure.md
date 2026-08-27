# Bug Filing Procedure — Product Bugs vs Automation Issues

How to determine whether to file a product bug, an automation issue, or both — and the correct procedure for each.

---

## The Two Trackers

| Tracker | Purpose | When to File |
|---|---|---|
| **`elitea-testing-public`** (this repo) | Test automation work, lightweight localhost-found defects | During analysis/investigation, ANY potential defect |
| **`elitea_issues`** (app tracker) | Application bugs visible to dev team | **Only after DEV verification + explicit human request** |

**Key distinction:**
- **`elitea-testing-public` bugs** = filed during investigation, may or may not be real product bugs
- **`elitea_issues` bugs** = confirmed product defects escalated for dev team action

**DO NOT conflate them.** Every product bug starts in `elitea-testing-public`; escalation to `elitea_issues` is a separate, human-gated step.

---

## Decision Tree: What to File

```
Test failure root cause:
│
├─ Test code issue (wrong locator, missing wait, assertion logic)
│   └─ NO BUG FILED — fix test directly
│
├─ Test drift (case updated, test not)
│   └─ NO BUG FILED — update test to match case
│
├─ Case drift (test matches product, case doesn't)
│   └─ FILE: Case clarification in onetest-ai-tm-Elitea
│
├─ Product defect (behavior wrong vs case AND test)
│   ├─ Verified on localhost ONLY
│   │   └─ FILE: Lightweight bug in elitea-testing-public, label "bug"
│   │       Note: "localhost-only, not DEV-verified"
│   │       DO NOT escalate to elitea_issues
│   │
│   └─ Verified on DEV (dev.elitea.ai)
│       └─ FILE: Confirmed bug in elitea-testing-public, label "bug"
│           Note: "DEV-verified, ready for escalation"
│           SURFACE escalation option to human
│           DO NOT auto-escalate to elitea_issues
│
└─ Environment issue (DEV backend instability, timing)
    └─ FILE: Investigation finding in elitea-testing-public
        Label: "env-issue" (not "bug")
        Document in test with skip/conditional
```

---

## Filing in `elitea-testing-public` (Lightweight Bugs)

### When to File Here

**Always file here first for:**
- Potential product defects found during test investigation
- Behavior mismatches discovered during analysis
- Regressions suspected from test failures

**DO NOT wait for DEV verification** to file in this tracker — it's lightweight and expected.

### Dedup Check (MANDATORY Before Filing)

```bash
# Check for existing bugs matching this defect
env -u GITHUB_TOKEN gh issue list --repo EliteaAI/elitea-testing-public \
  --label bug --state all --limit 300 --json number,title,state \
  | tee /tmp/existing-bugs.json

# Keyword search locally
grep -i "<component>" /tmp/existing-bugs.json
grep -i "<symptom>" /tmp/existing-bugs.json
```

**Apply duplicate/sibling/regression tests** (`.agents/profile.md` § Bug filing):

| If Match Is... | Action |
|---|---|
| **Duplicate** (same object + trigger + expected/actual) | Add `duplicate` label to **higher-numbered issue**, comment "Duplicate of #M", leave OPEN. Do NOT file new. |
| **Sibling** (same pattern, different object/case/surface) | File as separate bug, cross-link both ways (`sibling of #N — same pattern, different <object>`) |
| **Regression** (closed issue that reproduces again) | File as new bug, note "regression of #M" in body. Do NOT mark old issue as duplicate. |
| **Unsure** | File with "possible duplicate of #N" in body. Better to file than silently drop. |

### Bug Template

```markdown
## Summary

<One-line what's wrong>

## Severity

<HIGH | MEDIUM | LOW>

## Environment

- **URL:** <https://dev.elitea.ai | http://localhost:5173>
- **Branch:** <automation/testids | main>
- **Browser:** Chromium (Playwright <version>)
- **Auth:** <Keycloak TEST_USER | VITE_DEV_TOKEN dev bypass>

## Steps to Reproduce

1. <step 1>
2. <step 2>
3. <step 3>
...

## Expected Behavior

<What should happen, per TMS case ELITEA-XXXX Step N>

## Actual Behavior

<What actually happens>

## Evidence

![screenshot description](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/<file>.png)

**Network response** (if API error):
```json
<paste response body>
```

**Error message:**
```
<paste error from console/logs>
```

## Frequency

<deterministic (100% repro) | intermittent (M/N runs)>

## Workaround

<if any>

## Related

- **TMS case:** ELITEA-XXXX
- **Investigation:** #<investigation-issue-num>
- **Found while working:** #<investigation-issue-num>

## Verification Status

- [x] Reproduced on localhost
- [ ] Reproduced on DEV (dev.elitea.ai)

<If DEV-verified, add:>
**DEV verification:** <date> — <brief result>
**Ready for escalation:** YES
```

### Filing Command

```bash
# Prepare body
cat > /tmp/bug-body.md <<'EOF'
<paste filled template>
EOF

# File bug
BUG_NUM=$(env -u GITHUB_TOKEN gh issue create \
  --repo EliteaAI/elitea-testing-public \
  --title "bug: <component> - <brief issue>" \
  --label bug \
  --body-file /tmp/bug-body.md \
  --json number --jq '.number')

echo "Filed bug #${BUG_NUM}"

# Link to investigation issue
env -u GITHUB_TOKEN gh issue comment ${INVESTIGATION_ISSUE} --body "🐛 Filed bug: #${BUG_NUM}"
```

**Labels:**
- `bug` (required)
- `high-priority` (if severity HIGH)
- `localhost-only` (if not DEV-verified)
- `repro:confirmed` (if DEV-verified)

---

## Test Code Changes for Blocking Defects

When a product bug **blocks test execution** (cannot proceed past failing step):

### Option A: Soft Assertion (Non-Blocking Defect)

For **isolated defects** where test can continue:

```python
# Known defect: #<BUG-NUM> - <brief>
expect.soft(notification).to_contain_text("Expected text")
# Test continues to verify other steps
```

**Use when:**
- Defect is single assertion failure
- Remaining steps are independent
- Want to verify rest of functionality

### Option B: Mark Test as Blocked (Blocking Defect)

For **blocking defects** where test cannot proceed:

```python
@pytest.mark.blocked
@pytest.mark.bug
# Known product bug: #<BUG-NUM> - <brief description>
def test_something(page):
    """ELITEA-XXXX: Test case description.
    
    Currently blocked by product bug #<BUG-NUM>.
    """
    ...
```

**Use when:**
- Defect prevents test from completing
- No workaround exists
- Test would fail on every run

**DO NOT use `pytest.skip` or `@pytest.mark.skip`** — that hides the defect. `@pytest.mark.blocked` is the team convention for known blockers.

### Option C: Environment-Conditional Skip (Environment Issue, Not Product Bug)

For **environment instability** (not product defects):

```python
@pytest.mark.skipif(
    settings.environment == "dev",
    reason="DEV backend instability: EliteaAI/elitea-testing-public#<NUM>"
)
def test_something(page):
    ...
```

**Use when:**
- Intermittent env-specific failure
- Not a product defect (backend timing, service instability)
- Test works on other environments

---

## Escalation to `elitea_issues` (HUMAN-GATED)

### The Escalation Gate

From `.agents/profile.md` § Bug filing:

> **Escalation path (know it exists; act only on an explicit ask).** A confirmed bug (DEV-verified via the `reproduce-elitea-bug` skill, verdict `repro:confirmed`) is escalated to `elitea_issues` via the `file-app-bug` skill — **ONLY on an explicit user request.** Agents NEVER file to `elitea_issues` on their own initiative: surface the confirmed bug and the escalation option, and wait.

### When to Surface the Option

**After DEV verification + RCA, post to investigation issue:**

```markdown
🐛 **Product Bug Confirmed**

**Bug filed:** #<BUG-NUM>
**DEV verification:** <date> — reproduced on https://dev.elitea.ai/
**Root cause:** <detailed RCA>

**Evidence:**
- Screenshot: <embedded>
- Network response: <pasted>

**Frequency:** Deterministic (3/3 repro)

**Next Steps:**

This bug is DEV-verified and ready for escalation to `EliteaAI/elitea_issues` (application bug tracker).

**Human decision needed:** Should this be escalated now?

To escalate, ask: "escalate bug #<BUG-NUM> to elitea_issues"
(Uses `file-app-bug` skill — posts to dev team tracker)
```

**Then wait.** Do NOT invoke `file-app-bug` on your own.

### If Human Requests Escalation

**Only then:**

```bash
# Human says: "escalate bug #1234 to elitea_issues"

# Use the skill
claude-code skill file-app-bug --bug-num 1234
```

The `file-app-bug` skill:
1. Reads bug #1234 from `elitea-testing-public`
2. Reformats for `elitea_issues` (dev-team audience)
3. Creates issue in `elitea_issues`
4. Links back to original bug via comment

**DO NOT hand-roll this.** The skill exists to enforce the format and cross-linking discipline.

---

## Automation Issue (Test Code Problem)

When investigation reveals a **test code defect** (not product bug):

### What to File

**Either:**

1. **Comment on existing investigation issue** (if issue already exists)
   ```markdown
   🔬 **Root Cause: Test Code Defect**
   
   **Issue:** <describe test bug>
   **Fix:** <describe solution>
   **PR:** #<NUM> (opened)
   ```

2. **Create new issue** (if test issue discovered independently)
   ```bash
   env -u GITHUB_TOKEN gh issue create \
     --repo EliteaAI/elitea-testing-public \
     --title "fix(test): <component> - <brief issue>" \
     --label "test-automation" \
     --body "## Problem
   <describe test defect>
   
   ## Root Cause
   <RCA>
   
   ## Solution
   <fix description>
   
   ## Related
   - TMS case: ELITEA-XXXX
   - Test: \`<node-id>\`
   "
   ```

**Labels:**
- `test-automation` (not `bug` — this is a test issue, not product)
- `fix` or `refactor`

---

## Special Cases

### Case 1: Both Test AND Product Are Wrong

**Symptoms:**
- Test has wrong assertion
- Product also has wrong behavior
- Case describes correct behavior

**Action:**
1. File product bug for product issue
2. Fix test to match case (even though product is also wrong)
3. Mark test with soft assertion + bug link
4. Test will fail until product fix ships (that's correct)

**Rationale:** Test should reflect requirements (case), not broken product.

### Case 2: Localhost-Only Bug

**Action:**
1. File bug in `elitea-testing-public`, label `localhost-only`
2. Note: "Not DEV-verified, may be local env quirk"
3. Do NOT escalate to `elitea_issues`
4. Investigate: HMR state? `.env` difference? `automation/testids` vs `main` JSX?

**Most localhost-only "bugs" are:**
- Local env config issues
- HMR stale state
- Branch-specific testid JSX not yet on `main`

### Case 3: Intermittent Bug (Flaky)

**Action:**
1. File bug with frequency: "intermittent (M/N runs)"
2. Capture evidence from BOTH pass and fail runs
3. Investigate: race condition? Timing? External service?
4. If <30% fail rate: may be env noise, not product bug
5. If >70% fail rate: treat as deterministic

**DO NOT file as product bug if it's test timing issue** (missing wait, sleep instead of proper wait).

### Case 4: Regression (Was Working, Now Broken)

**Action:**
1. Check git history: when did it break?
2. Find likely culprit commit (bisect if needed)
3. File bug noting: "regression, introduced around <commit-sha>"
4. If old bug re-occurs: file as NEW bug, note "regression of #M"

**DO NOT mark old CLOSED bug as duplicate** — regressions are new bugs.

---

## Anti-Patterns

❌ **Don't:**
- File product bug without DEV verification (localhost ≠ real)
- Auto-escalate to `elitea_issues` (human-gated)
- Skip dedup check (creates duplicate bugs)
- File duplicate without marking it (wastes dev time)
- Mask bugs with `pytest.skip` (hides defect)
- File test code issue as "bug" (label it correctly)
- Include bare screenshot paths (upload + embed)

✅ **Do:**
- File in `elitea-testing-public` first, always
- Verify on DEV before claiming product bug
- Dedup check before filing
- Mark duplicates explicitly (leave OPEN, label `duplicate`)
- Use `expect.soft()` for non-blocking defects
- Use `@pytest.mark.blocked` for blocking defects
- Upload evidence to release (embed, not path)
- Surface escalation option, don't auto-escalate

---

## Evidence Requirements

### For Product Bugs

**MANDATORY:**
- Screenshot showing actual vs expected (uploaded + embedded)
- Steps to reproduce (numbered, specific)
- Expected behavior (quote TMS case)
- Actual behavior (what happened)
- Environment (localhost vs DEV, clear)

**RECOMMENDED:**
- Network response (if API error)
- Console errors (if applicable)
- Component source pointer (if code read during investigation)

### For Test Issues

**MANDATORY:**
- Description of test defect
- Root cause
- Proposed fix

**RECOMMENDED:**
- Link to test file + line number
- Link to TMS case
- Before/after code comparison

---

## Work-Log Comments

Post progress comments on filed bugs:

```bash
# When starting investigation
env -u GITHUB_TOKEN gh issue comment ${BUG_NUM} --body "🔧 **Investigating** — reproducing on DEV"

# After DEV verification
env -u GITHUB_TOKEN gh issue comment ${BUG_NUM} --body "✅ **Verified on DEV** — deterministic (3/3 repro)

Evidence: <embedded screenshots>
Ready for escalation (awaiting human decision)"

# If escalated
env -u GITHUB_TOKEN gh issue comment ${BUG_NUM} --body "📬 **Escalated** — filed as EliteaAI/elitea_issues#<NUM>

Application bug tracker notified."

# If test marked
env -u GITHUB_TOKEN gh issue comment ${BUG_NUM} --body "🚫 **Test marked as blocked** — @pytest.mark.blocked added

Test: \`<node-id>\`
PR: #<NUM>"
```

---

## Related Documentation

- `.agents/profile.md` § Bug filing — dedup rule, duplicate/sibling/regression definitions
- `.agents/role-overrides.md` § screenshot evidence — upload + embed procedure
- `reproduce-elitea-bug` skill — DEV verification procedure
- `file-app-bug` skill — escalation to elitea_issues (human-gated)
- `embed-evidence` skill — mechanical evidence upload + embedding

---

## Version History

- **1.0.0** (2026-08-26): Initial version — dual-tracker bug filing + escalation discipline
