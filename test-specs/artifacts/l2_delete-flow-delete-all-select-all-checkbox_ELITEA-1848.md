# Test Case: Delete Flow – Delete All Files and Folders Using Select All Checkbox via Delete All Files Icon

## Metadata
- **TMS ID**: ELITEA-1848
- **Linked Story**: [EliteaAI/elitea-testing-public#1392](https://github.com/EliteaAI/elitea-testing-public/issues/1392)
- **Priority**: l2 (high — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` → DEV backend, project 399)
- **User set**: `${TEST_USER}` (localhost `auth_state`, `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer, combined analyst+implementer slot (2026-08-22)
- **Status**: **ready-for-automation** — every case step executed and observed live in one clean
  session (seed 4 items → select all → confirm delete → post-state), 0 console errors, no blocking
  defect. Two case-text drifts found (confirmation message + success toast) — handled by the
  reverse-masking guard (assert the live contract) and routed to the tracker: the toast drift is an
  exact duplicate of [#660](https://github.com/EliteaAI/elitea-testing-public/issues/660)
  (commented, not re-filed); the confirmation-message drift is filed as [#1640](https://github.com/EliteaAI/elitea-testing-public/issues/1640), a sibling of
  [#659](https://github.com/EliteaAI/elitea-testing-public/issues/659) because the all-selected
  variant additionally renders the **ungrammatical** string `"Are you sure to delete the all files?"`.

## Relationship to ELITEA-1849 / ELITEA-1850 (why NOT a family AFS)
Same entry point (select rows → toolbar delete icon → shared `DeleteEntityModal`), but the terminal
actions differ in KIND, not parameter value: 1848 asserts deletion (toast, empty table, empty state
in BOTH panels, bucket survives), 1849/1850 assert *non*-deletion (no toast, zero DELETE requests,
items + selection intact). The same reasoning ELITEA-1844/1845 recorded: a parameter table would put
every assertion behind an `if variant == …` branch. ⇒ three AFS files, three sibling test methods in
ONE spec file — the shape `test_artifacts_delete_subfolder_checkbox.py` (1847+1846) already uses.

## Overlap check vs existing automation
`test_artifacts_delete_subfolder_checkbox.py` covers the bulk toolbar delete with a **partial**
selection (1 folder row — ELITEA-1847; 2 file rows — ELITEA-1846). Neither ever clicks the header
**Select all** checkbox to drive a full selection, so neither ever sees:
- the toolbar tooltip flip to `"Delete all files"` (both existing tests assert the `"Delete selected
  files"` branch and 1846 explicitly asserts the header checkbox is *indeterminate*),
- the modal's entity-name span reading `"all files"`,
- a bucket emptied to zero items — i.e. the empty state in the **right panel** (`artifacts-empty-state`),
  the empty label in the **left tree** (`artifacts-bucket-tree-empty-label-{bucket}`), or the bucket
  itself surviving its own emptying.
No existing artifacts test clicks `artifacts-select-all-checkbox` at all
(`grep -rn "click_select_all_checkbox" automation/tests/` → no hits before this case).

## Preconditions
Freshly seeded bucket (`artifact_bucket` fixture) with exactly 4 top-level items — two folders
(`a1`, `folder-a`, each holding one file) and two root files (`sample.md`, `sample - Copy.md`).
The case's `bucket-1` is a name in the case text only; this suite seeds its own bucket per test
because the case is destructive.

## Test Data
| Field | Value (live-verified 2026-08-22) |
|---|---|
| Items in bucket | `a1`, `folder-a`, `sample - Copy.md`, `sample.md` (4 top-level rows) |
| Underlying storage keys | `a1/file1.txt`, `folder-a/placeholder.txt`, `sample.md`, `sample - Copy.md` |
| Pagination before | `1 - 4 of 4` |
| Toolbar tooltip, all selected | `Delete all files` (matches the case) |
| Modal title | `Delete confirmation` |
| Modal message | **`Are you sure to delete the all files?`** (case says `Are you sure to delete all files?` — CLARIFICATION #1640, sibling of #659) |
| Emphasised entity name ("highlighted in blue") | `all files` |
| Success toast | **`The selected files have been successfully deleted.`** (case Test Data says `The artifacts have been deleted successfully` — exact duplicate of #660) |
| Empty-state text (both panels) | `No files in this bucket` |

## Test Steps
| # | Action | Expected (live-verified 2026-08-22) |
|---|---|---|
| 1-2 | Navigate to the seeded bucket | Artifacts page loads with the bucket selected |
| 3 | Read the file table | 4 rows: `a1`, `folder-a`, `sample - Copy.md`, `sample.md`; pagination `1 - 4 of 4` |
| 4 | Click the header `Select all` checkbox | — |
| 5 | Read every row's checkbox state | all 4 `True` (both folders and both files) |
| 6 | Read the header checkbox state | fully checked (`Mui-checked`), **not** indeterminate |
| 7 | Read the toolbar delete icon's tooltip | `Delete all files` |
| 8 | Click the toolbar delete icon | `delete-confirm-dialog` visible |
| 9 | Read the modal's parts | title `Delete confirmation`; warning icon present (`delete-confirm-title-icon`, count 1); message `Are you sure to delete the all files?`; entity-name span `all files`; X, `Cancel` and `Delete` all present (count 1 each) |
| 10 | Click `Delete` | one `DELETE …/artifacts/artifacts/default/399/{bucket}?fname[]=…` → **200**, `fname[]` = the 4 fully-expanded storage keys (folders expanded to their underlying files — no bare `a1/` key) |
| 11 | Observe the modal | hidden |
| 12 | Read the toast | `The selected files have been successfully deleted.` |
| 13 | Read the file table | 0 rows (`wait_for_file_count(0)`, then `get_file_names() == []`) |
| 14 | Observe the main panel | `artifacts-empty-state` visible, text `No files in this bucket` |
| 15 | Observe the left tree under the bucket | `artifacts-bucket-tree-empty-label-{bucket}` visible, text `No files in this bucket` |
| 16 | Observe the bucket list | the bucket row is still listed (`wait_for_bucket_in_list`) |
| + | Independent ground truth (Axis 2) | `ArtifactAPI.list_bucket_files` returns `[]` — every key really gone from storage, not just from the DOM |

## Expected Results
All 4 items (both folders with their contents and both root files) are deleted. The bucket itself
survives and stays in the bucket list, showing the empty state in both the main panel and the
left-panel tree.

## Coverage Map
### Axis 1 — Case element → Coverage
| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: bucket-1 holds exactly 4 items (2 folders, 2 files) | setup | seeded via `artifact_api.upload_file` ×4, asserted in Step 1 |
| Step 1 (navigate to Artifacts) | asserted | Step 1 — folded into `navigate_to_bucket`, proven by the table rendering |
| Step 2 (select bucket-1) | asserted | Step 1 — same |
| Step 3 (table shows the 4 items) | asserted | Step 1 — name set + row count + pagination |
| Step 4 (click Select all) | asserted | Step 2 |
| Step 5 (all 4 rows checked, folders + files) | asserted | Step 2 — `get_checkbox_states()` == all True |
| Step 6 (header checkbox fully checked) | asserted | Step 3 — checked True **and** indeterminate False |
| Step 7 (tooltip `Delete all files`) | asserted | Step 4 |
| Step 8 (click Delete all files icon → modal) | asserted | Step 5 |
| Step 9 (modal: warning icon, title, message, "all files" highlighted, X, Cancel, Delete) | asserted | Step 6 — each element individually; the message is the LIVE string (CLARIFICATION) |
| Step 10 (click Delete) | asserted | Step 7 — plus the DELETE response status + `fname[]` contents |
| Step 11 (modal closes) | asserted | Step 8 |
| Step 12 (green success notification, exact text) | asserted | Step 9 — LIVE text (#660); "green" is a `toastSuccess` severity not exposed as a testid-assertable attribute, so the exact text is the observable |
| Step 13 (file table empty) | asserted | Step 10 |
| Step 14 (main panel empty state) | asserted | Step 11 |
| Step 15 (left tree shows "No files in this bucket") | asserted | Step 12 |
| Step 16 (bucket still in the bucket list) | asserted | Step 13 |

### Axis 2 — Observables asserted beyond the case
| Addition | Why grounded |
|---|---|
| DELETE response 200 + `fname[]` == the 4 expanded storage keys | the case says "all files and folders deleted"; only the request payload proves the folders were expanded to their real S3 keys (this storage has no folder objects) rather than sent as bare prefixes |
| `ArtifactAPI.list_bucket_files(bucket) == []` | an empty table can also mean "the table failed to refetch"; storage is the independent producer of the case's own claim |
| header checkbox **not** indeterminate (Step 3) | discriminates "fully checked" from "partially checked", which the case's step 6 wording ("fully filled") is exactly about |
| no console errors | project-wide side-channel check |

## Cleanup
None beyond the `artifact_bucket` fixture teardown — the case's own action empties the bucket.
(Known issue #636: the fixture's bucket delete 404s silently; unchanged by this case.)

## Concrete Handles (discovered during exploration)
Provenance verified 2026-08-22 with a fresh `git fetch origin` in `../EliteaUI` and the two-stage
`-i`/`[:=]` grep over `origin/main` and `origin/automation/testids`.

| Element | Handle | Provenance |
|---|---|---|
| Header select-all checkbox | `artifacts-select-all-checkbox` | on-main ✓ |
| Toolbar delete icon (wrapper carries the dynamic tooltip as `aria-label`) | `artifacts-delete-files-button` | on-main ✓ |
| Modal root | `delete-confirm-dialog` | on-main ✓ |
| Modal title | `delete-confirm-title` | on-main ✓ |
| Modal warning icon | `delete-confirm-title-icon` | **on `automation/testids` only** — EliteaAI/EliteaUI@7b359d32, awaiting human cherry-pick |
| Modal message | `delete-confirm-message` | on-main ✓ |
| Emphasised entity name | `delete-confirm-entity-name` | **on `automation/testids` only** — EliteaAI/EliteaUI@e59d0c97 |
| Modal X (close) | `delete-confirm-close-button` | **on `automation/testids` only** — EliteaAI/EliteaUI@08d9bb4f (presence-only here; 1850 drives it) |
| Modal `Cancel` | `delete-confirm-cancel-button` | on-main ✓ (presence-only here; 1849 drives it) |
| Modal `Delete` | `delete-confirm-button` | on-main ✓ |
| Success toast | `toast-message` | on-main ✓ |
| Right-panel empty state | `artifacts-empty-state` | on-main ✓ |
| Left-tree empty label | `artifacts-bucket-tree-empty-label-{bucket}` (`ArtifactsPage.BUCKET_TREE_EMPTY_LABEL`) | **on `automation/testids` only** — runtime-composed at `BucketContent.jsx:87`; a bare-substring grep of `origin/main` finds nothing |

**Promotability:** FOUR testids this spec references are not yet on `main`
(`delete-confirm-title-icon`, `delete-confirm-entity-name`, `delete-confirm-close-button`,
`artifacts-bucket-tree-empty-label-*`). Green on localhost, red on any deployed env until a human
cherry-picks them. No new testid was needed for this cluster.

## Network Behavior
One `DELETE /api/v2/artifacts/artifacts/default/{project}/{bucket}?fname[]=…` (the PLURAL bulk
endpoint — `ArtifactsPage.confirm_delete()`'s `"artifacts/artifacts"` matcher is the right one; the
singular `…/artifact/…` sibling used by the row dropdown is NOT involved). It invalidates
`TAG_ARTIFACTS` + `TAG_BUCKETS`, so table, empty state and left tree all refetch asynchronously —
settle with `wait_for_file_count(0)` before reading.

## Known Defects Found During Exploration
None blocking. Two case-text drifts (§ Metadata) — the confirmation message additionally reads
`"Are you sure to delete the all files?"`, which is ungrammatical product copy worth a human look;
routed as CLARIFICATION #1640 (sibling of #659), not as a blocker.

## Blocked Steps
None.

## Automation Hints
- `ArtifactsPage` already has everything needed except a `click_delete_close_button()` (added by
  ELITEA-1850 in the same PR) — `click_select_all_checkbox`, `get_checkbox_states`,
  `is_select_all_checkbox_checked/_indeterminate`, `get_delete_button_tooltip_text`,
  `click_delete_files_button`, `confirm_delete`, `is_bucket_empty`, `bucket_tree_empty_label`,
  `wait_for_bucket_in_list` all exist.
- Read the tooltip via the wrapper's `aria-label` (`get_delete_button_tooltip_text`) — no hover
  needed; MUI clones the dynamic Tooltip title onto the wrapping `<Box component="span">`.
- Give the post-delete reads a settle (`wait_for_file_count(0)`); the empty state and the tree label
  arrive on separate refetches.
