# Test Case: Delete Flow – Close X on Delete Confirmation Modal Keeps Items Intact

## Metadata
- **TMS ID**: ELITEA-1850
- **Linked Story**: [EliteaAI/elitea-testing-public#1392](https://github.com/EliteaAI/elitea-testing-public/issues/1392)
- **Priority**: l3 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` → DEV backend, project 399)
- **User set**: `${TEST_USER}` (localhost `auth_state`, `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer, combined analyst+implementer slot (2026-08-22)
- **Status**: **ready-for-automation** — every step executed and observed live in the same clean
  session as ELITEA-1848/1849, 0 console errors, no drift from the case text on this case's own
  strings (the message here is the `selected files` branch, already covered by #659).

## Relationship to ELITEA-1848 / ELITEA-1849
See ELITEA-1848 § Relationship. This case is the **partial-selection** branch: its step 4 names the
`Delete selected files` icon, so the tooltip and the modal's entity name read `selected files`, not
`all files`. Its step 9 additionally asserts something no other case in the cluster does —
the previously selected checkboxes are still **checked** after the dismissal.

## Overlap check vs existing automation
No existing test clicks the delete modal's X on ANY path. `delete-confirm-close-button` was added
during ELITEA-1844's implementation but only ever asserted for *presence*; this case is the first to
drive it. ELITEA-1846 (same file family, partial selection) *confirms* the delete instead of
dismissing it, and asserts nothing about selection retention.

## Preconditions
Fresh `artifact_bucket` seeded exactly as ELITEA-1848/1849 (4 top-level items). Own bucket instance.

## Test Data
| Field | Value (live-verified 2026-08-22) |
|---|---|
| Items selected (case: "one or more") | `sample.md`, `sample - Copy.md` — 2 of 4 rows, a genuine partial selection so the `selected files` branch is exercised |
| Items left unselected | `a1`, `folder-a` |
| Header checkbox with a partial selection | indeterminate |
| Toolbar tooltip | `Delete selected files` |
| Modal message | `Are you sure to delete the selected files?` (already tracked as #659) |
| Emphasised entity name | `selected files` |
| Toast after X | **none** — zero over a 3 s observation window |
| Selection after X | `sample.md` + `sample - Copy.md` still checked; `a1` + `folder-a` still unchecked; header still indeterminate |

## Test Steps
| # | Action | Expected (live-verified 2026-08-22) |
|---|---|---|
| 1-2 | Navigate to the seeded bucket | 4 rows, pagination `1 - 4 of 4` |
| 3 | Check `sample.md` and `sample - Copy.md` | both `True`; `a1`/`folder-a` `False`; header indeterminate |
| 4 | Read the toolbar tooltip, then click the delete icon | tooltip `Delete selected files`; `delete-confirm-dialog` visible |
| 5 | Read the modal | title `Delete confirmation`; message `Are you sure to delete the selected files?`; entity name `selected files`; X present |
| 6 | Click the X (`delete-confirm-close-button`) | — |
| 7 | Observe the modal | hidden |
| 8 | Wait out a full toast window (3 s) on `toast-message` | never becomes visible (detector proven by the sibling ELITEA-1848 test in the same file) |
| 9 | Read the table and every checkbox | same 4 names, each row's text byte-identical to the pre-X snapshot; `sample.md`/`sample - Copy.md` still checked, `a1`/`folder-a` still unchecked; header still indeterminate; pagination still `1 - 4 of 4` |
| + | Independent ground truth (Axis 2) | zero DELETE requests captured; `ArtifactAPI.list_bucket_files` still returns all 4 seeded keys |

## Expected Results
The X closes the modal with no deletion, no notification and no request; every item remains, and the
prior selection survives the dismissal exactly as it was.

## Coverage Map
### Axis 1 — Case element → Coverage
| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: bucket with selectable files | setup | seeded ×4, asserted in Step 1 |
| Step 1 (navigate to Artifacts) | asserted | Step 1 — folded into `navigate_to_bucket` |
| Step 2 (select bucket-1) | asserted | Step 1 |
| Step 3 (select one or more items) | asserted | Step 2 — 2 of 4 rows checked, the other 2 verified unchecked |
| Step 4 (click Delete selected files icon) | asserted | Step 3 — including the tooltip text that names the icon |
| Step 5 (modal opens) | asserted | Step 3 — dialog visible + title/message/entity name |
| Step 6 (click the X) | asserted | Step 4 |
| Step 7 (modal closes immediately) | asserted | Step 4 — `to_be_hidden`; "immediately" is bounded by the assertion's own timeout, not measured as a duration |
| Step 8 (no success notification) | asserted | Step 5 — 3 s wait-for-visible that must time out |
| Step 9 (items unchanged AND still checked) | asserted | Step 6 — name set, per-row byte-for-byte text, and the full checkbox-state map |

### Axis 2 — Observables asserted beyond the case
| Addition | Why grounded |
|---|---|
| header checkbox still indeterminate after the X | the case's "items remain checked" claim is about selection state; the header is the same selection model rendered a second way, so it catches a partial reset the row map alone would miss |
| zero DELETE requests captured | as ELITEA-1849 — "no items deleted" off the DOM alone can pass against a stale table |
| storage listing still holds all 4 keys | independent producer, beyond the DOM |
| pagination unchanged | cheap corroboration that the table did refetch-or-not consistently |
| no console errors | project-wide side-channel check |

## Cleanup
None — this case mutates nothing.

## Concrete Handles (discovered during exploration)
Same table as ELITEA-1848 § Concrete Handles. This case *drives* `delete-confirm-close-button`
(**on `automation/testids` only** — EliteaAI/EliteaUI@08d9bb4f, awaiting human cherry-pick) and
never touches `delete-confirm-button` or `delete-confirm-cancel-button`.

## Network Behavior
**Zero requests.** `DeleteEntityModal` passes ONE handler to both `BaseModal`'s `onClose` (X /
backdrop / Escape) and the Cancel button's `onClick` — the same shape `ZipDownloadProgressDialog`
and `DuplicateResolutionDialog` use. Selection lives in `ArtifactTable`'s `rowSelectionModel`, which
the modal never touches, which is why the checkboxes survive.

## Known Defects Found During Exploration
None. (Adjacent, not asserted here: #677 — the toolbar delete/tooltip stays enabled with a stale
selection after a multi-file delete. That is the post-*delete* path, not this dismissal path.)

## Blocked Steps
None.

## Automation Hints
- `ArtifactsPage` needs one additive method, `click_delete_close_button()`, mirroring
  `click_delete_cancel_button()` — the `delete_confirm_close_button` descriptor already exists.
- Same absence-assertion discipline as ELITEA-1849 (wait-for-visible that must time out, never
  `to_have_count(0)`).
- Select 2 of 4 rows deliberately: "one or more" satisfied by a full selection would silently move
  this case onto ELITEA-1848's `all files` branch and lose the `selected files` coverage.
