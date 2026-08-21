# Test Case: Delete Flow – Delete Single File via Actions Dropdown

## Metadata
- **TMS ID**: ELITEA-1844
- **Linked Story**: [EliteaAI/elitea-testing-public#1392](https://github.com/EliteaAI/elitea-testing-public/issues/1392) (artifacts automation intake — "Found while working #1392" for the CLARIFICATION filed from this case)
- **Priority**: l2 (high — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` → DEV backend, project `Private` / 399)
- **User set**: `${TEST_USER}` (on localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer, combined analyst+implementer slot (2026-08-22)
- **Status**: **ready-for-automation** — every case step executed and observed live in one clean
  session (seed 4 items → dropdown → confirm delete → post-state), 0 console errors, no blocking
  defect. Two case-text drifts found (confirmation message + success toast) — handled by the
  reverse-masking guard (assert the live contract) and filed as CLARIFICATION
  [#1638](https://github.com/EliteaAI/elitea-testing-public/issues/1638), sibling of #659/#660.
  Two additive testids were needed and added (see § Concrete Handles).

## Overlap check vs existing automation
- `test_artifacts_delete_subfolder_checkbox.py` (ELITEA-1847 + ELITEA-1846) deletes via the **row
  checkbox + toolbar bulk-delete icon** → `deleteArtifacts` (plural endpoint,
  `/artifacts/artifacts/default/{project}/{bucket}?fname[]=…`). This case deletes via the **per-row
  actions dropdown** → `deleteArtifact` (SINGULAR endpoint,
  `/artifacts/artifact/default/{project}/{bucket}?filename=…`), a different code path
  (`ArtifactRowActions.jsx`'s `onConfirm` → `ArtifactTable.jsx:347 onDeleteArtifact`), a different
  confirmation message and a different success toast. Zero behavioural overlap.
- `test_artifacts_download_single_file_dropdown.py` (ELITEA-1839) opens the SAME dropdown but only
  asserts the Delete item is *visible* and never clicks it ("visibility-only, never clicked" —
  its own page-object docstring). This case is the first to exercise it.
- `test_artifacts_file_preview_actions_dropdown.py` (ELITEA-1856) deletes from the **file-preview
  editor** menu (`FilePreviewCanvas`, toast `File deleted successfully`) — a third, distinct path.
⇒ New spec file, `ready-for-automation`.

## Preconditions
- Authenticated `${TEST_USER}` session (fixture `auth_state`, localhost dev token).
- A bucket containing exactly 4 top-level items: subfolders `a1`, `folder-a` and files
  `sample - Copy.md`, `sample.md`.
- The case names the bucket `bucket-1`; **no such shared fixture exists in this suite** and this
  case is destructive, so the test seeds its own fresh bucket via the `artifact_bucket` fixture
  (`autotest-…`) and the API — established pattern for every artifacts delete case (ELITEA-1847).

## Test Data
### generate-per-test (in test setup; bucket removed by the `artifact_bucket` fixture teardown)
| Key | Content | Renders as |
|---|---|---|
| `a1/file1.txt` | `b"a1 file\n"` | top-level folder row `a1` |
| `folder-a/placeholder.txt` | `b"folder-a file\n"` | top-level folder row `folder-a` |
| `sample - Copy.md` | short markdown | file row `sample - Copy.md` |
| `sample.md` | markdown sized to **exactly 331 bytes** | file row `sample.md`, Type `Markdown`, Size `331 B` (matches the case's own Test Data row) |

Live-observed row text for `sample.md`: `sample.mdMarkdown331 B22-08-2026, 12:10 AM`
(the timestamp is upload time — assert Type/Size, not the case's frozen `10-07-2026, 06:45 PM`).

## Test Steps
| # | Action | Expected (live-verified 2026-08-22) |
|---|---|---|
| 1-2 | Navigate to the seeded bucket (`navigate_to_bucket`) — folds the case's "open Artifacts" + "click bucket-1" | Bucket panel + file table load |
| 3 | Read the file table's rendered names | exactly `{a1, folder-a, sample - Copy.md, sample.md}` (4 rows) |
| 4 | Read the pagination label | `1 - 4 of 4` |
| 5 | Open `sample.md`'s row actions dot-menu (`open_file_actions_menu`) | Dropdown opens |
| 6 | Read the dropdown's items | exactly `["Download", "Delete"]`, both visible |
| 7 | Click `Delete` | `delete-confirm-dialog` becomes visible |
| 8 | Inspect the modal | title `Delete confirmation`; warning icon (`delete-confirm-title-icon`) present; message **`Are you sure to delete the sample.md? It can't be restored.`** (case drops "the" — #1638); the file name is rendered in its own emphasis element (`delete-confirm-entity-name` = `sample.md`, the "highlighted in blue" span); X icon (`delete-confirm-close-button`), `Cancel` and `Delete` buttons all present |
| 9 | Click the modal's `Delete` | exactly one `DELETE /api/v2/artifacts/artifact/default/399/{bucket}?filename=sample.md` → **200** |
| 10 | Observe the modal | hidden |
| 11 | Observe the toast | **`The sample.md file has been successfully deleted.`** (case text differs — #1638) |
| 12 | Read the file table | `sample.md` absent |
| 13 | Read the left-panel tree | `sample.md` no longer present (`is_tree_item_visible` → False); `sample - Copy.md` still True |
| 14 | Read the pagination label | `1 - 3 of 3` |
| 15 | Read the remaining rows | exactly `{a1, folder-a, sample - Copy.md}` |
| +  | Independent ground truth (Axis 2) | `ArtifactAPI.list_bucket_files` no longer lists `sample.md`; still lists the other 3 keys |

## Expected Results
`sample.md` is deleted through the row dropdown; the modal closes, the success toast names the
file, the row and the tree entry disappear, pagination drops to `1 - 3 of 3`, and the other three
items are untouched in both the UI and S3 storage.

## Coverage Map
### Axis 1 — Case element → Coverage
| Case element | Disposition | Where asserted |
|---|---|---|
| Precondition: bucket with a1/folder-a/2 files | setup | seeded via `artifact_api.upload_file` ×4 |
| Step 1-2 (navigate, select bucket) | asserted | Step 1 — bucket panel loads, table renders 4 rows |
| Step 3 (4 items listed) | asserted | Step 1 — `get_file_names()` == the 4 expected names |
| Step 4 (pagination `1 - 4 of 4`) | asserted | Step 2 — `get_pagination_info_text()` |
| Step 5 (open actions dropdown) | asserted | Step 3 — dropdown opens, items readable |
| Step 6 (Download + Delete visible) | asserted | Step 3 — exact `["Download","Delete"]` label list + both locators visible |
| Step 7 (click Delete → modal) | asserted | Step 4 — dialog visible |
| Step 8 (modal elements + message) | asserted | Step 4 — title, warning icon, message (LIVE text), entity-name span, X, Cancel, Delete. **Not asserted:** the *blue colour* of the name — a computed-style read has no testid-compliant handle; the dedicated `delete-confirm-entity-name` element (which carries the colour) is asserted instead. Declared in § Automation Hints. |
| Step 9 (click Delete) | asserted | Step 5 — DELETE 200 with `filename=sample.md` |
| Step 10 (modal closes) | asserted | Step 6 |
| Step 11 (success toast) | asserted | Step 6 — LIVE toast text (#1638) |
| Step 12 (`sample.md` absent from table) | asserted | Step 7 |
| Step 13 (absent from left tree) | asserted | Step 8 |
| Step 14 (pagination `1 - 3 of 3`) | asserted | Step 7 |
| Step 15 (remaining 3 unchanged) | asserted | Step 7 (names) + Step 9 (storage keys) |

### Axis 2 — Observables asserted beyond the case
| Addition | Why grounded |
|---|---|
| DELETE request URL/params + 200 status | the case's "deletion completes" needs a producer-side fact, not only a DOM re-read; also pins the SINGULAR endpoint that distinguishes this path from ELITEA-1847's |
| S3 listing after delete (`list_bucket_files`) | independent ground truth beyond the DOM, same discipline as ELITEA-1847 step 10 |
| `sample - Copy.md` still visible in the tree | step 13 asserts a removal; the sibling's survival makes it a real discrimination, not a tree that simply failed to render |
| no console errors | project-wide side-channel check |

## Cleanup
`artifact_bucket` fixture teardown removes the bucket (known to 404 silently, issue #636 — buckets
accumulate; not this case's to fix). The case's own delete is the only mutation the test drives.

## Concrete Handles (discovered during exploration)
Provenance verified 2026-08-22 after `cd ../EliteaUI && git fetch origin`.

| Element | Handle | Provenance |
|---|---|---|
| Row actions dot-menu trigger | `ArtifactsPage.ARTIFACT_ACTIONS_MENU_BUTTON` → `artifact-actions-{name}-menu-button` | on-main ✓ |
| Dropdown `Download` item | `artifacts-file-download-menuitem` | on-main ✓ |
| Dropdown `Delete` item | `artifacts-file-delete-menuitem` | on-main ✓ |
| Confirmation dialog root | `delete-confirm-dialog` | on-main ✓ |
| Dialog title | `delete-confirm-title` | on-main ✓ |
| Dialog warning icon | `delete-confirm-title-icon` | on-main ✓ |
| Dialog message | `delete-confirm-message` | on-main ✓ |
| Dialog emphasised entity name | `delete-confirm-entity-name` | **added this run** — EliteaAI/EliteaUI@e59d0c97 on `automation/testids` (attribute-only add on the existing `<Typography component="span">`) |
| Dialog X (close) | `delete-confirm-close-button` | **added this run** — EliteaAI/EliteaUI@08d9bb4f on `automation/testids` (prop-only: `DeleteEntityModal` now forwards `closeButtonTestId` to `Modal.BaseModal`, which already accepted it) |
| Dialog `Cancel` | `delete-confirm-cancel-button` | on-main ✓ |
| Dialog `Delete` | `delete-confirm-button` | on-main ✓ |
| Success toast | `toast-message` | on-main ✓ |
| Pagination label | `ArtifactsPage.get_pagination_info_text()` | existing |
| Left-panel tree item | `ArtifactsPage.is_tree_item_visible(name)` | existing |

## Network Behavior
- Single-file row delete → `DELETE /api/v2/artifacts/artifact/default/{projectId}/{bucket}?filename={name}`
  (`src/api/artifacts.js:125`, `deleteArtifact`), **200**, exactly one request per confirm.
  Distinct from the bulk path's `/artifacts/artifacts/…?fname[]=…` (`deleteArtifacts`).
- `invalidatesTags: [TAG_ARTIFACTS, TAG_BUCKETS]` drives an automatic listing refetch — the table
  and tree settle asynchronously, so post-delete reads use a condition wait
  (`wait_for_file_count(3)`), never a bare read.

## Known Defects Found During Exploration
None. Two **case-text drifts** (not defects) → CLARIFICATION
[#1638](https://github.com/EliteaAI/elitea-testing-public/issues/1638).

## Blocked Steps
None.

## Automation Hints
- Reuse `ArtifactsPage.open_file_actions_menu()` / `download_menu_item` / `delete_menu_item`
  (ELITEA-1839) as-is.
- `ArtifactsPage.confirm_delete()` is **not** reusable: its `expect_response` matcher is
  `"artifacts/artifacts" in r.url`, which never matches the singular endpoint. Add a sibling
  `confirm_delete_single_artifact()` (same idiom, `"artifacts/artifact/"` substring) — additive,
  the existing method stays byte-identical.
- The "highlighted in blue" styling of the file name is **not** asserted (no testid-compliant way
  to read a computed colour); the dedicated `delete-confirm-entity-name` element that carries that
  styling is asserted by text instead. Declared improvisation per `role-overrides.md`
  § declared-improvisation protocol (canon has no shape for asserting colour under a testid-only
  policy) — a *how*, not a change to *what* is verified.
- Seed `sample.md` with content of exactly 331 bytes so the row's Size cell reads `331 B`, matching
  the case's own Test Data without depending on any pre-existing environment data.
