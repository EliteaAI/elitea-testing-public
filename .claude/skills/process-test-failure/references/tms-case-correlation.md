# TMS Case Correlation — Phase 3 Deep Dive

How to systematically compare a test implementation against its source TMS case to identify drift and determine the correct resolution path.

---

## Why Correlation Matters

A test failure might be:
1. **Test bug** — implementation wrong
2. **Test drift** — case updated, test not
3. **Case drift** — test matches product, case doesn't
4. **Product bug** — behavior wrong vs both test AND case

**You cannot know which until you correlate.** Skipping this phase leads to:
- Fixing test when case is wrong (wasted work)
- Filing bug when test is outdated (false defect)
- Updating case when product is broken (hiding real bug)

---

## Step 1: Load All Sources of Truth

### 1.1: TMS Case (primary source)

```bash
# Case lives in onetest repo
CASE_ID="ELITEA-XXXX"
CASE_FILE="../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/<feature>/${CASE_ID}.md"

# Read full case
cat "$CASE_FILE"

# Or via MCP
npx -y @onetest/tms get_test_case --id "$CASE_ID" --repo EliteaAI/onetest-ai-tm-Elitea
```

**Extract from case:**
- Test steps (numbered, in case body)
- Expected results (per step or at end)
- Preconditions
- Test data requirements
- Last updated date (from frontmatter `updated:`)

### 1.2: AFS (analyst's interpretation)

```bash
# AFS pattern: test-specs/<feature>/l<pri>_<slug>_<CASE-ID>.md
find test-specs -name "*${CASE_ID}*" -type f

# Read AFS
cat test-specs/<feature>/l<pri>_<slug>_${CASE_ID}.md
```

**Extract from AFS:**
- Implementation guidance
- Handle references (testids, expected)
- Edge cases analyst identified
- Known issues flagged during analysis

**Note:** AFS is NOT source of truth for steps — it's an interpretation. If AFS conflicts with TMS case, **TMS case wins** (unless case is proven wrong).

### 1.3: Test Code (actual implementation)

```bash
# Test file from node ID
TEST_FILE="automation/tests/ui/<feature>/test_<name>.py"
cat "$TEST_FILE"
```

**Extract from test:**
- Test method body (actual steps)
- Assertions
- Test data used
- Comments (especially "Known defect" markers)

### 1.4: Product Behavior (ground truth)

This comes from Phase 2 reproduction. Note:
- What actually happens when you run test steps manually
- Any deviations from test expectations
- Any deviations from case expectations

---

## Step 2: Create Step Mapping Table

Map each test implementation step to its corresponding TMS case step.

### Template

| # | Test Step (code) | TMS Case Step | Match? | Notes |
|---|---|---|---|---|
| 1 | `page.navigate("/agents/all")` | "1. Open Agents page" | ✅ | Exact match |
| 2 | `page.click(new_agent_button)` | "2. Click + New Agent" | ✅ | Exact match |
| 3 | `page.fill(name_input, "TestAgent")` | "3. Enter agent name" | ⚠️ | Case says "My Agent", test uses "TestAgent" |
| 4 | `page.click(save_button)` | "4. Click Save" | ✅ | Exact match |
| 5 | `assert "Agent created" in notification.text` | "5. Verify success message 'Agent saved successfully'" | ❌ | **MISMATCH**: case says "Agent saved successfully", test expects "Agent created" |
| 6 | (missing in test) | "6. Verify agent appears in list" | ❌ | **MISSING**: test doesn't verify Step 6 |

### Match Symbols

- ✅ **Exact match** — test step directly implements case step with same inputs/assertions
- ⚠️ **Minor variance** — same action, different data (may be acceptable)
- ❌ **Mismatch** — different action, wrong assertion, or missing step
- ➕ **Extra in test** — test has step not in case
- ➖ **Missing in test** — case has step not in test

---

## Step 3: Identify Drift Patterns

### Pattern A: Test Outdated (Test Drift)

**Symptoms:**
- Case has steps test doesn't (➖)
- Case expected results differ from test assertions (❌)
- Case was recently updated (`updated:` field newer than test commit)

**Example:**
- Case Step 5 updated from "Success" to "Saved successfully" on 2026-08-15
- Test still asserts "Success"
- Test last modified 2026-07-20

**Resolution:** Update test to match current case (Path B)

---

### Pattern B: Case Outdated (Case Drift)

**Symptoms:**
- Test matches product behavior (verified in Phase 2)
- Case doesn't match product
- Product behavior is intentional (not a bug)

**Example:**
- Case says "Click Save button"
- Product now has "Save & Close" and "Save & New" buttons
- Test clicks "Save & Close" (matches product)
- Case hasn't been updated

**Resolution:** File case clarification (Path C)

---

### Pattern C: Both Wrong (Product Bug)

**Symptoms:**
- Test AND case agree on expected behavior
- Product does something different
- Product behavior is verified wrong (not intentional change)

**Example:**
- Case Step 5: "Verify success notification 'Agent saved'"
- Test asserts: "Agent saved" in notification
- Product actually shows: "Error: Failed to save"
- This is reproducible and DEV-verified

**Resolution:** File product bug (Path D)

---

### Pattern D: Test Logic Error (Test Code Defect)

**Symptoms:**
- Test implements case step with wrong logic
- Not a drift (case didn't change)
- Test always had this bug

**Example:**
- Case: "Verify at least 3 tags are displayed"
- Test asserts: `assert len(tags) == 3` (exact match, not "at least")
- This fails when 4 tags exist (correct product behavior)

**Resolution:** Fix test implementation (Path A)

---

### Pattern E: Mapping Error

**Symptoms:**
- Test references wrong case ID in docstring
- `automation_test_id` in TMS case points to wrong test
- Test actually implements a different case

**Example:**
- Test docstring says "ELITEA-1234"
- Test actually implements ELITEA-5678 steps
- ELITEA-1234 is a different feature

**Resolution:** Fix mapping (update docstring AND TMS case `automation_test_id`)

---

## Step 4: Determine Confidence Level

### HIGH Confidence

**All true:**
- Clear pattern (A, B, C, D, or E above)
- One obvious explanation
- Evidence supports it (dates, repro results, code history)
- No conflicting signals

**Example:**
- Case updated 2026-08-15
- Test last modified 2026-07-20
- Test fails because expected value changed in case
- **HIGH confidence: Pattern A (Test Outdated)**

---

### MEDIUM Confidence

**Some true:**
- Multiple possible explanations
- Some evidence for each
- Need to verify one hypothesis

**Example:**
- Test fails on assertion
- Case updated recently BUT expected value was always that way
- Product behavior unclear (need to verify on DEV)
- **MEDIUM confidence: Could be Pattern A or C**

---

### LOW Confidence

**True:**
- Contradictory evidence
- Multiple sources of truth disagree
- No clear pattern
- Reproduction flaky/unreliable

**Example:**
- Case says X, AFS says Y, test does Z, product does W
- All recently updated
- **LOW confidence: Escalate to human**

---

## Step 5: Map Confidence to Action

| Confidence | Action |
|---|---|
| **HIGH** | Proceed directly to resolution (Phase 5) |
| **MEDIUM** | Verify hypothesis first (reproduce on DEV, check git history, ask human if needed), then proceed |
| **LOW** | File "question" issue, escalate to human, do NOT guess |

---

## Common Drift Scenarios

### Scenario 1: Case Added New Step

**Mapping:**
```
Test: Steps 1-5 implemented
Case: Steps 1-6 (Step 6 added recently)
```

**Verdict:** Test outdated (Pattern A)

**Resolution:** Add Step 6 to test

---

### Scenario 2: Case Changed Expected Result

**Mapping:**
```
Test: assert "Success" in notification
Case (old): "Verify 'Success' message"
Case (new): "Verify 'Saved successfully' message"
```

**Verdict:** Test outdated (Pattern A)

**Resolution:** Update assertion to "Saved successfully"

---

### Scenario 3: Product Changed, Case Not Updated

**Mapping:**
```
Test: clicks "Save & Close" button
Case: "Click Save button"
Product: Has "Save & Close" and "Save & New" (changed 2026-08-10)
Case: Last updated 2026-07-01
```

**Verdict:** Case outdated (Pattern B)

**Resolution:** Test is correct. File case clarification asking to update to "Save & Close"

---

### Scenario 4: Product Regression

**Mapping:**
```
Test: assert notification.is_visible()
Case: "Verify success notification appears"
Product: No notification shown (verified on DEV)
Git history: Notification worked until 2026-08-20 commit
```

**Verdict:** Product bug (Pattern C)

**Resolution:** File bug. Test and case are both correct; product regressed.

---

### Scenario 5: Test Never Matched Case

**Mapping:**
```
Test: asserts len(tags) == 3
Case: "Verify at least 3 tags"
Test commit: Original implementation (2026-06-15)
Case: Never changed
```

**Verdict:** Test logic error (Pattern D)

**Resolution:** Fix test to `assert len(tags) >= 3`

---

## Special Cases

### Case Has No Steps (Old Format)

**Symptom:** Case body is narrative, not numbered steps

**Action:**
- Extract implied steps from narrative
- Map best-effort
- Note in correlation comment: "Case uses narrative format, mapping inferred"
- Consider filing case clarification asking for numbered steps

---

### Test Covers Multiple Cases

**Symptom:** Test docstring lists multiple case IDs

**Action:**
- Correlate against ALL listed cases
- Verify test actually covers union of all case steps
- If test misses steps from one case, that's drift

---

### Case Covers Multiple Tests

**Symptom:** Case `automation_test_id` lists multiple test paths

**Action:**
- Correlate only the failing test
- Note: other tests may cover other aspects of this case
- Fixing this test may not fully cover the case

---

### Parameterized Test

**Symptom:** Test runs multiple times with different data

**Action:**
- Identify which parameter set failed
- Correlate that specific execution against case
- Check if case describes all parameter sets or just one

---

## Output Format

Post correlation findings as issue comment:

```markdown
🔍 **Correlation Analysis**

## Sources

- **TMS Case:** ELITEA-XXXX (updated: YYYY-MM-DD)
- **AFS:** test-specs/feature/lN_slug_ELITEA-XXXX.md
- **Test:** automation/tests/ui/feature/test_name.py::test_method (last modified: YYYY-MM-DD)

## Step Mapping

| # | Test Step | Case Step | Match | Notes |
|---|---|---|---|---|
| 1 | ... | ... | ✅ | ... |
| 2 | ... | ... | ❌ | **MISMATCH: ...** |
| 3 | ... | ... | ➖ | **MISSING in test** |

## Analysis

**Drift detected:** YES

**Drift type:** Test Outdated (Pattern A)

**Evidence:**
- Case updated 2026-08-15 (added Step 6)
- Test last modified 2026-07-20
- Test missing Step 6

**Confidence:** HIGH

## Recommended Action

**Update test to match case** (Resolution Path B)
- Add implementation of Step 6: "Verify agent appears in list"
- Update test to match case Step 5 expected result: "Saved successfully"

**Next:** Proceeding to implement fix...
```

---

## Anti-Patterns

❌ **Don't:**
- Skip correlation and guess which is wrong
- Update test without checking case
- Assume case is always correct
- Assume test is always correct
- File bug without checking for drift first
- Copy-paste AFS without reading original case

✅ **Do:**
- Load ALL sources of truth
- Create explicit mapping table
- Identify pattern before acting
- Use confidence level to guide action
- Escalate on LOW confidence
- Cite evidence (dates, commits, repro results)

---

## Related Documentation

- `.agents/test-automation.yaml` § `automation_test_id` — how TMS case links to test
- `test-case-analysis` skill § Spec format — how AFS is structured
- `.agents/workflow.md` § Closure record — verifying testid provenance (similar correlation)
- `.agents/profile.md` § Test case storage — where TMS cases live

---

## Version History

- **1.0.0** (2026-08-26): Initial version — systematic correlation procedure
