# Test Case: Delete Flow – Delete Single File via Actions Dropdown – Cancel Keeps File Intact

## Metadata
- **TMS ID**: ELITEA-1845
- **Linked Story**: [EliteaAI/elitea-testing-public#1392](https://github.com/EliteaAI/elitea-testing-public/issues/1392)
- **Priority**: l3 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` → DEV backend, project 399)
- **User set**: `${TEST_USER}` (localhost `auth_state`, `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer, combined analyst+implementer slot (2026-08-22)
- **Status**: **ready-for-automation** — every step executed and observed live in the same clean
  session as ELITEA-1844 (cancel path run FIRST, before the destructive confirm path), 0 console
  errors. Inherits CLARIFICATION [#1638](https://github.com/EliteaAI/elitea-testing-public/issues/1638)
  for its step-5 message wording.

## Relationship to ELITEA-1844 (why NOT a family AFS)
Same entry point and same first four steps, but the terminal action differs in KIND, not in
parameter value: ELITEA-1844 asserts deletion (toast, row removed, tree removed, pagination
decremented), ELITEA-1845 asserts *non-*deletion (no toast, row + metadata + pagination unchanged).
A parameter table would force every assertion behind an `if variant == …` branch, which the
project's parameterised precedent (ELITEA-1842/1843, where both rows share identical observables)
does not support. ⇒ two AFS files, two sibling test methods in ONE spec file — the same shape as
ELITEA-1847 + ELITEA-1846 in `test_artifacts_delete_subfolder_checkbox.py`.

## Overlap check vs existing automation
No existing test clicks `Cancel` on the delete-confirmation modal on ANY path. ELITEA-1847's AFS
explicitly declared its cancel-path probe an "exploratory aside outside this case's asserted
scope", and `artifacts_page.py` carries a standing note that no `cancel_delete()` method exists
(the Cancel button was believed to have no testid). That note is **stale**:
`delete-confirm-cancel-button` exists in `DeleteEntityModal.jsx` and is on `origin/main`
(introduced in EliteaAI/EliteaUI@bf4a13ad). This case is the first to assert the cancel path.

## Preconditions
Identical to ELITEA-1844: a freshly seeded bucket with 4 top-level items, `sample.md` sized to
exactly 331 bytes (Type `Markdown`, Size `331 B`). Seeded per-test; the case's `bucket-1` is a
name in the case text only.

## Test Data
| Field | Value |
|---|---|
| File to attempt deleting | `sample.md` (331 B, Markdown) |
| Pagination before and after | `1 - 4 of 4` |
| Row text before and after | `sample.mdMarkdown331 B<upload timestamp>` — compared **byte-for-byte** against the pre-cancel snapshot (stronger than matching the case's frozen `10-07-2026, 06:45 PM`, which is environment data this suite never reproduces) |

## Test Steps
| # | Action | Expected (live-verified 2026-08-22) |
|---|---|---|
| 1-2 | Navigate to the seeded bucket | file table shows the 4 items, pagination `1 - 4 of 4` |
| — | Snapshot `sample.md`'s row text | `sample.mdMarkdown331 B22-08-2026, 12:10 AM` |
| 3 | Open `sample.md`'s row actions dot-menu | dropdown opens |
| 4 | Click `Delete` | `delete-confirm-dialog` visible |
| 5 | Read the modal message | **`Are you sure to delete the sample.md? It can't be restored.`** (case drops "the" — #1638) |
| 6 | Click `Cancel` (`delete-confirm-cancel-button`) | — |
| 7 | Observe the modal | hidden |
| 8 | Observe the toast area | **zero** `toast-message` elements (no success notification) |
| 9 | Read `sample.md`'s row text again | byte-identical to the pre-cancel snapshot (Type/Size/timestamp unchanged) |
| 10 | Read the pagination label | still `1 - 4 of 4`; `get_file_names()` still the same 4 names |
| +  | Independent ground truth (Axis 2) | `ArtifactAPI.list_bucket_files` still lists all 4 seeded keys — no DELETE reached storage |

## Expected Results
Cancel closes the modal and nothing else changes: no notification, the file row and all its
metadata are untouched, pagination stays `1 - 4 of 4`, and the file still exists in storage.

## Coverage Map
### Axis 1 — Case element → Coverage
| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: bucket with `sample.md` among 4 items | setup | seeded via `artifact_api.upload_file` ×4 |
| Step 1-2 (navigate, select bucket) | asserted | Step 1 — 4 rows render |
| Step 3 (open actions dropdown) | asserted | Step 2 |
| Step 4 (click Delete → modal) | asserted | Step 3 — dialog visible |
| Step 5 (message text) | asserted | Step 3 — LIVE text (#1638) |
| Step 6 (click Cancel) | asserted | Step 4 |
| Step 7 (modal closes) | asserted | Step 4 — `to_be_hidden` |
| Step 8 (no success notification) | asserted | Step 5 — `toast-message` count == 0 |
| Step 9 (file + metadata unchanged) | asserted | Step 5 — row text equals the pre-cancel snapshot |
| Step 10 (pagination unchanged) | asserted | Step 5 |

### Axis 2 — Observables asserted beyond the case
| Addition | Why grounded |
|---|---|
| S3 listing still contains all 4 keys | the case's "not deleted" claim read only off the DOM could pass on a stale table; storage is the independent producer |
| the 4 rendered names still equal the seeded set | discriminates "sample.md survived" from "the table failed to refresh at all" |
| no console errors | project-wide side-channel check |

## Cleanup
None beyond the `artifact_bucket` fixture teardown — this case mutates nothing (the delete is
cancelled), so its final state is its seeded state.

## Concrete Handles (discovered during exploration)
Same table as ELITEA-1844's § Concrete Handles (**amended in fix round 1** — re-verified with the
two-ref grep for every row, plus caller-side diffs for the composed/prop-wired handles). This case
additionally *drives*:

| Element | Handle | Provenance |
|---|---|---|
| Modal `Cancel` | `delete-confirm-cancel-button` | on-main ✓ — EliteaAI/EliteaUI@bf4a13ad |
| File-table row, read twice for the byte-for-byte metadata snapshot (`get_file_row_text()`) | `ArtifactsPage.ARTIFACT_FILE_ROW` → `artifacts-file-row` | on-main ✓ (ternary-wired in `ArtifactTable.jsx:525`, identical on both refs) |

…and never touches `delete-confirm-button`.

**Promotability note:** this case's own handles are all on `main`, but it ships in the SAME spec
file as ELITEA-1844, whose three testids are not (`delete-confirm-entity-name`,
`delete-confirm-close-button`, `delete-confirm-title-icon`). The closure record's promotability
row is therefore file-scoped, not case-scoped: THREE testids pending human cherry-pick.

## Network Behavior
Zero requests fire on the Cancel path — `onClose` only resets local modal state
(`DeleteEntityModal.jsx`'s `resetButtonState`); no RTK mutation is dispatched. The assertion of
record is the post-cancel S3 listing (a real request the *test* makes), not a request-count spy.

## Known Defects Found During Exploration
None.

## Blocked Steps
None.

## Automation Hints
- Run this test's cancel path in its own test method with its own seeded bucket — do NOT chain it
  onto ELITEA-1844's bucket; the confirm path is destructive and ordering would couple them.
- `ArtifactsPage` needs an additive `click_delete_cancel_button()` (the standing "no cancel method"
  note in `artifacts_page.py` is stale — the testid exists on `main`). Update that note in the same
  PR rather than leaving a comment that contradicts the shipped code.
- Assert "no toast" with a count-0 expectation on `toast-message` (auto-retrying, and correct in
  both directions) rather than a sleep-then-check.
