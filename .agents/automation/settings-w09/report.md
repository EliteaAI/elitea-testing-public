# Batch Report — settings-w09

**Batch:** `settings-w09`  
**Base:** `origin/automation/base`  
**Integration branch:** `tests/batch-settings-w09`

## Summary

| Verdict | Automated | Blocked | Sanctioned-RED | Total |
|---------|-----------|---------|----------------|-------|
| **GREEN** (gate 3/3 pass + 1 expected red) | 10 | 4 | 1 | 15 |

**Gate runs:** 3 consecutive  
**Durations:** 261.6s, 258.3s, 258.4s (baseline ~259s)  
**Gate status:** GREEN (the single failure on ELITEA-2299 is sanctioned-RED on open #1974)

## Key Outcomes

- **10 cases automated** across 5 PRs (#1972, #1976, #1978)
- **4 cases blocked** (3 on build failures #1973, 1 requires human decision #2306)
- **1 case merged as sanctioned-RED** (ELITEA-2299 on #1974 — React re-render loop, expected)

## Gate Details

**Verdict:** GREEN ✓

**Failure on the gate:**
- **Spec:** `automation/tests/ui/admin/test_users_batch_delete.py`
- **Test:** `TestUsersBatchDelete::test_batch_delete_multiple_users` (ELITEA-2299)
- **Error:** `AssertionError: Locator expected to have count '4'`
- **Status:** Sanctioned-RED (expect.soft failure linked to #1974)
- **Reason:** Batch delete puts Users page into React re-render loop (DeleteUserButton.jsx's success effect calls `setSelectedUsers([])` with `users` in its dependency array). Deterministic, single-cause; test correctly asserts expected behaviour with `# Known defect: #1974`.

## Case Summary Table

| Case ID | Status | PR |
|---------|--------|-----|
| ELITEA-2293 | Automated | #1972 |
| ELITEA-2294 | Automated | #1972 |
| ELITEA-2295 | Automated | #1972 |
| ELITEA-2305 | Automated | #1972 |
| ELITEA-2308 | Automated | #1972 |
| ELITEA-2296 | Blocked | #1973 |
| ELITEA-2297 | Blocked | #1973 |
| ELITEA-2309 | Blocked | #1973 |
| ELITEA-2298 | Automated | #1976 |
| ELITEA-2299 | Merged-Sanctioned-RED | #1976 |
| ELITEA-2300 | Automated | #1976 |
| ELITEA-2306 | Blocked | — |
| ELITEA-2301 | Automated | #1978 |
| ELITEA-2302 | Automated | #1978 |
| ELITEA-2303 | Automated | #1978 |

## Key Findings

### Defects Filed

- **#1974** (Bug): Batch delete leaves Users page in React re-render loop
- **#1975** (Minor): Batch delete toast shows singular text for multi-user delete
- **#1971** (Bug): Regression — toolkitTypes RTK-Query fires before project ID resolves
- **#1970** (Clarification): Case text claims Name-header click sorts ascending; product already does
- **#1977** (Clarification): Edit roles dialog includes "user" word in product UI

### Framework Improvements

- **#1847 confirmed:** Removed `wait_for_network()` flake from `ensure_team_project_selected()` — saves ~56s per 8-spec run
- **Testid discovery:** 7 new testids for user management UI; pushed to `automation/testids`

### Blocked Units

- **ELITEA-2296, 2297, 2309**: Build failures (agent StructuredOutput issue)
- **ELITEA-2306**: Product does not prevent self-deletion in UI — requires human decision

---

**Report generated:** 2026-08-29  
**Files:** report.json, report.md
