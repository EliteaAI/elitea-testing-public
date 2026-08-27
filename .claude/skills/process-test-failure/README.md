# Process Test Failure — Skill Overview

Comprehensive workflow for investigating test failures, reproducing issues, correlating with TMS cases, and resolving through fixes or documentation.

---

## Quick Reference

**When to Use:** Test fails in CI or locally, needs systematic investigation

**What It Does:** 5-phase pipeline from failure intake to resolved + tracked

**Output:** Tracking issue in board #9 (Approved status) + resolution artifacts (PR/bugs/clarifications)

---

## Files in This Skill

| File | Purpose |
|---|---|
| `SKILL.md` | **Main skill** — complete step-by-step procedure for all 5 phases |
| `README.md` | This file — overview and navigation |
| `references/high-level-flow.md` | Executive summary, decision trees, phase I/O |
| `references/tms-case-correlation.md` | Phase 3 deep dive — how to map test ↔ case |
| `references/approved-issue-creation.md` | Phase 1 deep dive — filing tracking issues in board #9 |
| `references/bug-filing-procedure.md` | Phase 5 deep dive — product bugs vs automation issues |

---

## The Five Phases

```
Phase 1: INTAKE        → Extract logs, create tracking issue (#9, Approved)
Phase 2: REPRODUCE     → Confirm with enhanced logging, verify on DEV
Phase 3: CORRELATE     → Map test steps ↔ TMS case, identify drift
Phase 4: INVESTIGATE   → Root cause analysis, categorize failure type
Phase 5: RESOLVE       → Fix test | Update | File clarification | File bug
```

**Time:** ~0.75 - 3.5 hours per test

---

## Entry Points by Reader Type

### For Humans Launching the Skill

**Start here:** `SKILL.md` § Prerequisites

**What you provide:**
- Test failure details (GHA run ID or local logs)
- Test node ID (pytest path)

**What you get:**
- Tracking issue created automatically
- Investigation report with root cause
- Resolution (PR, bug, clarification) as appropriate

---

### For Agents Invoking the Skill

**Read first:** `references/high-level-flow.md` (understand the pipeline)

**Then:** `SKILL.md` (complete implementation)

**Key sections:**
- Phase 1 § Step 1.7 — filing Approved issues (critical: identity rule)
- Phase 2 § Step 2.5 — DEV verification (gate for product bugs)
- Phase 3 — correlation (test vs case, detect drift)
- Phase 5 — decision trees (which resolution path?)

---

### For Reviewers/Auditors

**Check these:**
- `references/approved-issue-creation.md` — verify board manipulation correct
- `references/bug-filing-procedure.md` — verify dedup + escalation discipline
- `references/tms-case-correlation.md` — verify drift analysis methodology

**Anti-patterns section in each doc** lists what NOT to do.

---

### For Process Improvement

**Metrics to track:** `references/high-level-flow.md` § Metrics

**Common failure modes:** `references/high-level-flow.md` § Failure Modes & Recovery

**Time bottlenecks:** Track phase durations to identify optimization opportunities

---

## Key Conventions

### Board #9 Discipline

- Issue filed **unassigned**, status **Approved** (skips human gate)
- Agent self-assigns during work, self-unassigns at handoff
- Move to `Blocked` only for real blockers
- Move to `Ready` when complete, leave OPEN for human acceptance
- Human sets `Done` (agents never close)

### Identity Rule

**Every tracker/board write MUST use keyring account:**
```bash
env -u GITHUB_TOKEN gh issue create ...
env -u GITHUB_TOKEN gh project item-edit ...
```

See `.agents/profile.md` § Issue tracker for setup.

### Evidence Discipline

**Screenshots/logs MUST be uploaded + embedded:**
```bash
env -u GITHUB_TOKEN gh release upload evidence <file>.png --clobber \
  --repo EliteaAI/elitea-testing-public
# Then embed: ![desc](https://github.com/.../evidence/<file>.png)
```

**Never** post bare local paths or filenames — readers can't open them.

### DEV Verification Gate

**Product bugs MUST be DEV-verified before escalation:**
- Localhost-only reproduction ≠ confirmed product bug
- DEV = `https://dev.elitea.ai/` with real Keycloak login
- Post Environment line: `localhost-only | DEV | both`

### Escalation to `elitea_issues`

**HUMAN-GATED ONLY.** After DEV verification:
1. Surface the escalation option to human
2. Wait for explicit "escalate bug #N" request
3. Then invoke `file-app-bug` skill

**Never auto-escalate** — standing rule from `.agents/profile.md` § Bug filing.

---

## Decision Trees (Quick Reference)

### Is This a Product Bug?

```
Failure reproduced?
├─ No → "not reproducible", close as non-defect
└─ Yes → Where?
    ├─ Localhost only → File lightweight bug, label "localhost-only", DO NOT escalate
    └─ DEV or both → Does test match TMS case?
        ├─ No (drift) → Fix test or case, NOT a product bug
        └─ Yes (no drift) → FILE product bug (elitea-testing-public)
            Surface escalation option to human
```

### Which Resolution Path?

```
Root cause:
├─ Test code defect (locator, wait, logic) → Path A: Fix test
├─ Test drift (case updated) → Path B: Update test to match case
├─ Case drift (test matches product) → Path C: File case clarification
├─ Product defect (DEV-verified) → Path D: File bug, surface escalation
└─ Environment issue → Path E: Document + skip on unstable env
```

### Should Test Be Marked?

```
Product bug filed, test affected:
├─ Blocking (cannot proceed) → @pytest.mark.blocked + @pytest.mark.bug
├─ Non-blocking (isolated) → expect.soft() + # Known defect: #N
└─ Environment instability → @pytest.mark.skipif(env=="dev")
```

---

## Common Scenarios

### Scenario: CI Failure on PR

**Input:** GHA run #NNNN failed on test `tests/ui/.../test_x.py::test_y`

**Phases:**
1. Extract logs from GHA run
2. Reproduce locally with enhanced logging
3. Correlate: test vs case
4. RCA: test code issue (missing wait)
5. Fix wait, 3/3 green, open PR

**Output:** PR #M fixing test, tracking issue #N documenting investigation

---

### Scenario: Localhost Pass, DEV Fail

**Input:** Test passes locally, fails on DEV in batch gate

**Phases:**
1. Extract failure from gate logs
2. Reproduce on DEV (Keycloak auth, `/app` prefix)
3. Correlate: no drift
4. RCA: DEV-specific timing (WebSocket response slower)
5. Adjust timeout, verify 3/3 on DEV

**Output:** PR with DEV-appropriate timeout, note in closure record

---

### Scenario: Test AND Case Both Wrong

**Input:** Test fails, investigation reveals product is correct

**Phases:**
1-2. Reproduce, confirm product behavior
3. Correlate: test asserts X, case says X, product does Y
4. RCA: both test and case outdated (product changed intentionally)
5. Fix test to match product + file case clarification

**Output:** PR updating test + clarification issue in TMS repo

---

### Scenario: Intermittent Failure (Flaky)

**Input:** Test passes 7/10 runs

**Phases:**
1-2. Run 10 times, record 70% pass rate
3. Correlate: no drift
4. RCA: race condition (missing wait for WebSocket)
5. Add proper wait (not sleep), verify 10/10

**Output:** PR fixing race condition

---

### Scenario: Product Regression

**Input:** Test was green, now red, no code changes

**Phases:**
1-2. Reproduce on DEV, confirm
3. Correlate: test matches case
4. RCA: product behavior regressed (git bisect → commit ABC123)
5. File bug as regression, note commit

**Output:** Bug #N in elitea-testing-public, surface escalation option

---

## Integration with Other Workflows

| Workflow | Relationship |
|---|---|
| **test-automation-workflow** | This skill is invoked BY the pipeline when single-test failures need deep investigation |
| **investigate-and-fix-tests** | Bulk triage (N failures); this skill is deep investigation (1 failure) |
| **adjust-automated-test** | Known fix → direct to fix; unknown cause → use THIS skill |
| **reproduce-elitea-bug** | This skill uses reproduce-elitea-bug's DEV verification in Phase 2 |
| **file-app-bug** | This skill surfaces escalation option; file-app-bug executes it (human-gated) |
| **batch-promote stabilization** | Batch promo fixes reds before promotion; THIS skill investigates why red |

---

## Success Criteria

A processed failure is **complete** when:

✅ Tracking issue exists with full history
✅ Root cause identified (HIGH confidence)
✅ Resolution action taken and verified
✅ Evidence uploaded + embedded (no bare paths)
✅ Artifacts linked (PR, bugs, clarifications)
✅ Test status clear: passing | blocked | skipped
✅ Human handoff clear: what needs review/merge

---

## Anti-Patterns (Top 10)

1. ❌ Skip reproduction — always confirm yourself
2. ❌ File product bug without DEV verification
3. ❌ Auto-escalate to elitea_issues (human-gated)
4. ❌ Skip dedup check (creates duplicate bugs)
5. ❌ Mask defects with pytest.skip
6. ❌ Fix test without correlating with case first
7. ❌ Post bare screenshot paths (upload + embed)
8. ❌ Close issue before resolution verified
9. ❌ Use `GITHUB_TOKEN` for writes (keyring account required)
10. ❌ Set status to `Done` (human-only)

---

## Getting Started

1. **Human:** Provide test failure details (GHA run or local logs + node ID)
2. **Agent:** Read `SKILL.md` § Phase 1, start intake
3. **Agent:** Follow phases sequentially, post progress to tracking issue
4. **Agent:** At Phase 5 resolution, open artifacts (PR/bugs) as needed
5. **Agent:** Move card to appropriate column, self-unassign, await human acceptance

---

## Questions & Troubleshooting

### "Should I use this skill or `investigate-and-fix-tests`?"

**Use THIS skill when:**
- Single test needs deep investigation
- Root cause unknown
- Need full pipeline with TMS correlation

**Use `investigate-and-fix-tests` when:**
- Bulk triage (N > 5 failures)
- Lighter investigation per test
- Known fix patterns

---

### "Test reproduced on localhost but not DEV — is it a bug?"

**NO.** Localhost-only = potential env quirk. File lightweight bug labeled `localhost-only`, DO NOT escalate to `elitea_issues`.

---

### "Test AND case both seem wrong — what do I fix?"

**Product behavior is ground truth.** If product is correct (intentional):
1. Fix test to match product
2. File case clarification

If product is wrong (regression):
1. Fix test to match case (what product SHOULD do)
2. File product bug
3. Mark test with soft assertion + bug link

---

### "Tracking issue creation failed — wrong IDs?"

Re-fetch field IDs:
```bash
rm /tmp/project-9-fields.json
env -u GITHUB_TOKEN gh project field-list 9 --owner EliteaAI --format json \
  > /tmp/project-9-fields.json
```

See `references/approved-issue-creation.md` § Troubleshooting.

---

### "Human asked to escalate bug — what do I do?"

Invoke `file-app-bug` skill:
```bash
claude-code skill file-app-bug --bug-num <BUG-NUM>
```

See `references/bug-filing-procedure.md` § Escalation.

---

## Version History

- **1.0.0** (2026-08-26): Initial release — comprehensive 5-phase pipeline

---

## Related Documentation

- `.agents/profile.md` § Issue tracker — board #9 mechanics
- `.agents/role-overrides.md` — interaction-discovery ladder, evidence discipline
- `.agents/testing.md` § Merge gate — 3-green verification
- `.agents/workflow.md` § Testid flow — testid provenance checking
- `add-data-testid` skill — adding missing testids
- `reproduce-elitea-bug` skill — DEV verification procedure
- `file-app-bug` skill — escalation to elitea_issues
