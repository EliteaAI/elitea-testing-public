# High-Level Flow — Process Test Failure

This document provides the executive summary of the test failure processing workflow. For implementation details, see the main SKILL.md.

---

## The Five-Phase Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT: Test failure (GHA run ID or local logs + node ID)       │
└────────────────┬────────────────────────────────────────────────┘
                 │
         ┌───────▼────────┐
         │  Phase 1:      │  Extract logs, identify test, find TMS case
         │  INTAKE        │  Create tracking issue in board #9 (Approved status)
         └───────┬────────┘  Upload evidence to release
                 │
         ┌───────▼────────┐
         │  Phase 2:      │  Reproduce with enhanced logging
         │  REPRODUCE     │  Verify on appropriate environment (localhost/DEV)
         └───────┬────────┘  Cross-check on other env if needed
                 │
         ┌───────▼────────┐
         │  Phase 3:      │  Load TMS case + AFS
         │  CORRELATE     │  Map test steps ↔ case steps
         └───────┬────────┘  Identify drift type (test/case/none)
                 │
         ┌───────▼────────┐
         │  Phase 4:      │  Categorize failure type
         │  INVESTIGATE   │  Apply decision tree + role-override checks
         └───────┬────────┘  Run comparative tests, identify root cause
                 │
         ┌───────▼────────┐
         │  Phase 5:      │  Fix test | Update to match case |
         │  RESOLVE       │  File clarification | File bug | Document env issue
         └───────┬────────┘  Verify fix (3 green runs), open PR/issues as needed
                 │
         ┌───────▼────────┐
         │  OUTPUT:       │  ✅ Test fixed/documented
         │  CLOSURE       │  📝 Tracking issue updated with resolution
         └────────────────┘  🔗 Artifacts: PR, bug, clarification linked
```

---

## Phase Inputs & Outputs

### Phase 1: Intake
**Input:**
- GHA run ID **OR** local logs/screenshots
- Test node ID (pytest path)

**Output:**
- Tracking issue #N in board #9, status **Approved**
- Original evidence preserved (logs, screenshots uploaded)
- TMS case ID identified
- AFS path located

---

### Phase 2: Reproduce
**Input:**
- Test node ID
- Environment (localhost/DEV)
- Original failure evidence

**Output:**
- Reproduction result: FAIL (confirmed) | PASS (not reproduced) | FLAKY (N/M)
- Enhanced evidence with instrumented logging
- Environment line: localhost-only | DEV-only | both | neither
- Cross-env verification (if needed)

---

### Phase 3: Correlate
**Input:**
- TMS case (markdown from onetest repo)
- AFS (if exists)
- Test code

**Output:**
- Step-by-step mapping table (test ↔ case)
- Drift verdict: YES | NO
- Drift type: test-outdated | case-outdated | mapping-error | none
- Recommended action: update test | file clarification | proceed to RCA

---

### Phase 4: Investigate
**Input:**
- Reproduction result
- Correlation analysis
- Enhanced logs

**Output:**
- Failure category: timeout | element-not-found | assertion-failure | api-error | env-instability | test-code-defect
- Root cause statement (detailed)
- Confidence: HIGH | MEDIUM | LOW
- Recommended resolution path

---

### Phase 5: Resolve
**Input:**
- Root cause + category
- Decision tree selection

**Output:**
- **Path A (Test Code Fix):** PR to automation/base or main, 3/3 green verified
- **Path B (Test Drift):** Updated test + optional AFS update, PR opened
- **Path C (Case Drift):** Clarification issue filed in TMS repo
- **Path D (Product Bug):** Bug issue filed with evidence, test marked if blocking
- **Path E (Env Issue):** Test marked with skip/conditional, documented

**Final artifacts:**
- Tracking issue updated with resolution summary
- All artifacts linked (PR, bugs, clarifications)
- Board card moved to appropriate column (Ready/Blocked)

---

## Key Decision Points

### Decision 1: Test Code vs Product Issue (Phase 3/4 boundary)

```
Does test match TMS case?
├─ NO (drift) → Who is correct?
│   ├─ Case correct → Update test (Path B)
│   └─ Test correct → File case clarification (Path C)
└─ YES (no drift) → Is product behavior correct?
    ├─ NO → File product bug (Path D)
    └─ YES → Test code defect (Path A) or env issue (Path E)
```

### Decision 2: Fix vs File Bug (Phase 4)

```
Root cause is:
├─ Test implementation issue → Fix in test code (Path A)
│   • Missing/wrong testid
│   • Wrong locator
│   • Insufficient wait
│   • Wrong test data
│   • Assertion logic error
│
├─ Test drift → Update to match case (Path B)
│   • Case updated, test not
│   • Expected values changed
│
├─ Case drift → File clarification (Path C)
│   • Test matches product, case doesn't
│   • Case ambiguous/outdated
│
├─ Product defect → File bug (Path D)
│   • Behavior wrong vs case AND vs expected
│   • Verified on DEV (not localhost-only)
│   • Not duplicate
│
└─ Environment instability → Document (Path E)
    • DEV backend intermittent
    • Localhost-only quirk
    • Not fixable in test
```

### Decision 3: Board Movement (Phase 6)

```
Resolution complete →
├─ PR opened, needs review → Leave in "In Progress"
├─ Blocked on product bug → Move to "Blocked"
├─ Fixed and verified → Move to "Ready" (human accepts)
└─ Investigation complete, no action → Move to "Ready", leave OPEN
```

---

## Critical Checkpoints

### ✅ Before moving past Phase 1:
- [ ] Tracking issue created in board #9
- [ ] Issue status set to **Approved** (skips human gate)
- [ ] Original evidence uploaded to evidence release (not bare paths)
- [ ] TMS case ID identified
- [ ] Issue body follows template

### ✅ Before moving past Phase 2:
- [ ] Test reproduced with enhanced logging
- [ ] Fresh evidence captured and uploaded
- [ ] Environment line determined (localhost/DEV/both/neither)
- [ ] If claiming product bug: **DEV verification complete**

### ✅ Before moving past Phase 3:
- [ ] TMS case + AFS loaded and reviewed
- [ ] Step mapping table created
- [ ] Drift type identified (or "none")
- [ ] Recommended action determined

### ✅ Before moving past Phase 4:
- [ ] Failure categorized into one of 6 types
- [ ] Root cause statement written
- [ ] If UI issue: interaction-discovery ladder applied
- [ ] If API issue: OpenAPI contract cross-checked
- [ ] Resolution path selected

### ✅ Before moving past Phase 5:
- [ ] Resolution action taken
- [ ] If code changed: 3/3 green runs verified locally
- [ ] If bug filed: dedup check performed first
- [ ] If evidence referenced: uploaded to release (embedded, not bare paths)
- [ ] Artifacts created (PR, bug issue, clarification issue)

### ✅ Before closing (Phase 6):
- [ ] Final comment posted with resolution summary
- [ ] All artifacts linked in issue
- [ ] Board card moved to appropriate column
- [ ] Self-unassigned (per team convention)

---

## Time Estimates

| Phase | Typical Time | Notes |
|---|---|---|
| Phase 1: Intake | 5-10 min | Faster if logs provided vs extracting from GHA |
| Phase 2: Reproduce | 10-30 min | Depends on reproduction complexity |
| Phase 3: Correlate | 5-15 min | Faster if AFS exists |
| Phase 4: Investigate | 15-60 min | Highly variable; simple locator fix vs complex RCA |
| Phase 5: Resolve | 10-90 min | Code fix: 10-30 min; bug filing: 20-40 min; complex fix: 60-90 min |
| **Total** | **45-205 min** | ~0.75 - 3.5 hours per test failure |

---

## Success Criteria

A processed test failure is **complete** when:

1. ✅ Tracking issue exists in board #9 with full history
2. ✅ Root cause identified with HIGH confidence
3. ✅ Resolution action taken and verified
4. ✅ All evidence uploaded and embedded (no bare paths)
5. ✅ Artifacts linked (PR, bugs, clarifications)
6. ✅ Test status clear: passing | marked-as-blocked | skipped-on-env
7. ✅ Human handoff clear: what's ready for review/merge, what needs decision

---

## Failure Modes & Recovery

### Failure: Cannot reproduce
- **Symptom:** Test passes on all attempts
- **Action:** Mark as "not reproducible", post what was tried, close as "not a defect"
- **Note:** Original evidence preserved; may be transient issue

### Failure: Reproduction is flaky (intermittent)
- **Symptom:** Test passes M/N times (M ≠ 0, M ≠ N)
- **Action:** Run 10 times, record frequency, investigate timing if <30% or >70% fail rate
- **Note:** If 30-70%, deeper investigation needed (race condition)

### Failure: No TMS case found
- **Symptom:** Test has no case ID, or case doesn't exist
- **Action:** File "mapping issue" ticket, escalate to lead (test shouldn't exist without case)
- **Note:** May be orphaned test or wrong ID in docstring

### Failure: Multiple conflicting sources of truth
- **Symptom:** Case says X, AFS says Y, test does Z, product behaves W
- **Action:** Prioritize: product behavior (ground truth) > TMS case > AFS > test
- **Resolution:** File clarifications for mismatches, fix test to match product+case

### Failure: Cannot determine if test or product is wrong
- **Symptom:** Ambiguous expected behavior, no spec
- **Action:** File "question" issue (parked decision), escalate to human/PM
- **Note:** Do not guess or assume; mark confidence LOW

---

## Related Workflows

| Workflow | When to Use | How it Differs |
|---|---|---|
| **investigate-and-fix-tests** | Bulk triage (CI run with N failures) | Processes many tests, lighter investigation per test |
| **adjust-automated-test** | Single test needs adjustment (known fix) | Skips reproduction, goes straight to fix |
| **reproduce-elitea-bug** | Bug card needs reproduction only | Stops at reproduction verdict, never fixes test |
| **batch-promote stabilization loop** | Pre-promotion triage | Fixes all reds before promotion, not deep investigation |

**Use THIS skill (process-test-failure) when:**
- Single test failure needs deep investigation
- Root cause unknown
- Need full pipeline: reproduce → correlate → RCA → fix
- Creating tracking issue required

---

## Metrics

Track these for process improvement:

- **Time per phase** (identify bottlenecks)
- **Resolution path distribution** (A/B/C/D/E — which are most common?)
- **Root cause category distribution** (which failure types dominate?)
- **Reproduction success rate** (how often we confirm vs "not reproduced")
- **Drift rate** (what % have test/case mismatch?)
- **Bug filing rate** (what % result in product bugs?)

---

## Version History

- **1.0.0** (2026-08-26): Initial version — comprehensive 5-phase pipeline
