# Test Case: Delete Flow – Cancel Delete All Keeps All Items Intact

## Metadata
- **TMS ID**: ELITEA-1849
- **Linked Story**: [EliteaAI/elitea-testing-public#1392](https://github.com/EliteaAI/elitea-testing-public/issues/1392)
- **Priority**: l3 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` → DEV backend, project 399)
- **User set**: `${TEST_USER}` (localhost `auth_state`, `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer, combined analyst+implementer slot (2026-08-22)
- **Status**: **ready-for-automation** — every step executed and observed live in the same clean
  session as ELITEA-1848/1850, 0 console errors. Inherits ELITEA-1848's step-6 message
  CLARIFICATION (live text is `Are you sure to delete the all files?` — [#1640](https://github.com/EliteaAI/elitea-testing-public/issues/1640)).

## Relationship to ELITEA-1848 / ELITEA-1850
See ELITEA-1848 § Relationship — three sibling test methods in one spec file, not a family AFS.
Distinct from ELITEA-1850 in BOTH the selection scope (all rows vs a partial selection, i.e. the
`all files` vs `selected files` modal branch) and the dismissal control (`Cancel` button vs the
header X). Distinct from ELITEA-1845, which cancels the **single-file row-dropdown** modal
(different trigger, different message, no multi-row selection to preserve).

## Overlap check vs existing automation
No existing test clicks `Cancel` on the **bulk toolbar** delete modal. ELITEA-1845
(`test_artifacts_delete_single_file_dropdown.py`) cancels the row-dropdown modal; ELITEA-1847's AFS
declared its own cancel probe an exploratory aside outside its asserted scope. Selection retention
after a dismissed bulk-delete modal is asserted nowhere.

## Preconditions
Identical seed to ELITEA-1848: a fresh `artifact_bucket` with `a1/file1.txt`,
`folder-a/placeholder.txt`, `sample.md`, `sample - Copy.md` → 4 top-level rows. Own bucket instance;
NOT chained onto ELITEA-1848's bucket, whose test empties it.

## Test Data
| Field | Value (live-verified 2026-08-22) |
|---|---|
| Items | `a1`, `folder-a`, `sample - Copy.md`, `sample.md` |
| Pagination before and after | `1 - 4 of 4` |
| Modal message | `Are you sure to delete the all files?` (case drops "the" — CLARIFICATION #1640) |
| Toast after Cancel | **none** — zero `toast-message` elements over a 3 s observation window |
| Selection after Cancel | all 4 row checkboxes still checked; header checkbox still fully checked |

## Test Steps
| # | Action | Expected (live-verified 2026-08-22) |
|---|---|---|
| 1-2 | Navigate to the seeded bucket | 4 rows, pagination `1 - 4 of 4` |
| — | Snapshot each row's text | used for the byte-for-byte post-cancel comparison |
| 3 | Click the header `Select all` checkbox | — |
| 4 | Read the checkbox states | all 4 `True`, header fully checked |
| 5 | Click the toolbar delete icon | `delete-confirm-dialog` visible |
| 6 | Read the modal message | `Are you sure to delete the all files?` |
| 7 | Click `Cancel` (`delete-confirm-cancel-button`) | — |
| 8 | Observe the modal | hidden |
| 9 | Wait out a full toast window (3 s) on `toast-message` | never becomes visible (detector proven by the sibling ELITEA-1848 test in the same file, which sees the same locator carry text after a real delete) |
| 10 | Read the file table | same 4 names; every row's text byte-identical to the pre-cancel snapshot |
| 11 | Read the pagination label | still `1 - 4 of 4` |
| 12 | Read the left-panel tree | `a1/`, `folder-a/`, `sample.md`, `sample - Copy.md` all still present |
| + | Independent ground truth (Axis 2) | zero DELETE requests captured on the page; `ArtifactAPI.list_bucket_files` still returns all 4 seeded keys |
| + | Axis 2 | selection is **retained** — all 4 checkboxes still checked after the dismissal |

## Expected Results
Cancel closes the modal and changes nothing: no notification, no request, all 4 items (and their
storage keys) intact, pagination unchanged, left tree unchanged, and the selection still in place.

## Coverage Map
### Axis 1 — Case element → Coverage
| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: bucket with the 4 items | setup | seeded ×4, asserted in Step 1 |
| Step 1 (navigate to Artifacts) | asserted | Step 1 — folded into `navigate_to_bucket` |
| Step 2 (select bucket-1) | asserted | Step 1 |
| Step 3 (click Select all) | asserted | Step 2 |
| Step 4 (all 4 selected) | asserted | Step 2 — `get_checkbox_states()` all True |
| Step 5 (click Delete all files icon → modal) | asserted | Step 3 |
| Step 6 (modal message) | asserted | Step 3 — LIVE text |
| Step 7 (click Cancel) | asserted | Step 4 |
| Step 8 (modal closes) | asserted | Step 4 — `to_be_hidden` |
| Step 9 (no success notification) | asserted | Step 5 — 3 s wait-for-visible that must time out |
| Step 10 (all 4 items remain unchanged) | asserted | Step 6 — name set + per-row byte-for-byte text |
| Step 11 (pagination still `1 - 4 of 4`) | asserted | Step 6 |
| Step 12 (left tree unchanged) | asserted | Step 7 — all 4 tree items still visible |

### Axis 2 — Observables asserted beyond the case
| Addition | Why grounded |
|---|---|
| zero DELETE requests captured | "no deletion occurred" read only off the DOM can pass while a request fired and the table went stale; the request log is the direct producer |
| storage listing still holds all 4 keys | independent ground truth beyond the DOM, same discipline as ELITEA-1847 Step 10 |
| selection retained after Cancel | the case is silent, but ELITEA-1850 asserts exactly this for the X path; the two dismissal controls share one `onClose`, so asserting it on both turns a shared-handler assumption into a test-enforced invariant |
| no console errors | project-wide side-channel check |

## Cleanup
None — this case mutates nothing; final state == seeded state.

## Concrete Handles (discovered during exploration)
Same table as ELITEA-1848 § Concrete Handles. This case *drives* `delete-confirm-cancel-button`
(on-main ✓, EliteaAI/EliteaUI@bf4a13ad) and never touches `delete-confirm-button`. Promotability is
file-scoped: it ships in the same spec file as ELITEA-1848/1850, so the four pending testids apply.

## Network Behavior
**Zero requests.** `DeleteEntityModal`'s `onClose` (`resetButtonState`) only resets local modal
state — no RTK mutation is dispatched. The assertions of record are the captured request log and the
post-cancel S3 listing (a request the *test* makes), not a spy on internal state.

## Known Defects Found During Exploration
None.

## Blocked Steps
None.

## Automation Hints
- Assert "no toast" by **waiting for it to appear and requiring a timeout**
  (`pytest.raises(PlaywrightTimeoutError)` around `success_toast_message.wait_for(state="visible",
  timeout=3000)`), not with `to_have_count(0)` — the latter is true at the first poll and cannot see
  a toast that renders 300 ms later (reviewer finding on ELITEA-1845,
  `.agents/memory/qa-engineer/absence_assertion_needs_a_proven_detector.md`).
- Capture DELETE requests with a `page.on("request", …)` listener registered before the flow starts.
- `click_delete_cancel_button()` already exists (added by ELITEA-1845).
