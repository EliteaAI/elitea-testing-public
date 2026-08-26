# Test Case: File Tree Behavior – Switching Between Buckets Updates Tree and Main Panel

## Metadata
- **TMS ID**: ELITEA-1838
- **Linked Story**: none
- **Priority**: l2 (TMS `priority: high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/399)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, artifacts-w02, 2026-08-21)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (auth_state, localhost).
- **Two buckets** exist, one with files. Seeded per test: bucket **A** via the
  `artifact_bucket` fixture (files `a1/f1.txt` + `root.txt`), bucket **B**
  created directly with `ArtifactAPI.create_bucket` under the name `{A}-b` and
  seeded with `b-root.txt`, deleted in the test's own teardown. `{A}-b` sorts
  immediately after `A` in the alphanumeric bucket list (digest § Bucket-list
  ordering), so both rows are adjacent and reachable in the same scroll band of
  a 760-bucket list.
- Neither seeded bucket may be the one `/artifacts` auto-selects on a param-less
  load (`#651` toggle trap) — asserted as a precondition.

## Test Data
### seeded (per test, cleaned up)
- Bucket A: `autotest-<test-name>-<ts>` with `a1/f1.txt`, `root.txt`
- Bucket B: `<A>-b` with `b-root.txt` (the case allows "empty or with different
  files"; a distinct file makes B's main-panel contents a positive observable
  and keeps every tree key globally unique, so a tree assertion can never
  accidentally match the other bucket's node)

## Concrete Handles

| Element | Handle | Provenance |
|---|---|---|
| Bucket rows | `artifacts-bucket-row-{name}` (`BUCKET_ROW`, `click_bucket_row`) | pre-existing, `on-main ✓` |
| Bucket highlight/selection state | `data-selected="true|false"` on the row (`is_bucket_selected()`) | pre-existing — `BucketItem.jsx:243`; this is the case's "highlighted" observable |
| Tree nodes (the "expanded" observable) | `artifacts-tree-item-{key}` (`ARTIFACTS_TREE_ITEM`, `tree_item()`, `is_tree_item_visible()`) | pre-existing |
| Main-panel rows | `artifacts-file-row` / `artifacts-folder-row` (`get_file_names()`) | pre-existing |
| Breadcrumb bucket crumb | `artifacts-breadcrumb-bucket-label` (`get_breadcrumb_bucket_text()`) | pre-existing |
| Breadcrumb folder crumbs | `artifacts-breadcrumb-folder-label` (`get_breadcrumb_folder_names()`) | pre-existing |
| URL | `page.url` → `?bucket=<name>` | product-owned |

**No new testid is needed and none was added.** "Expanded" is asserted through
the bucket's own rendered tree nodes — `SimpleBucketList.jsx` renders
`{isExpanded && <BucketContent …>}`, so a collapsed bucket has **zero** tree
nodes in the DOM. There is no `data-expanded` attribute on the bucket row and
none is required: the presence of the bucket's children IS the expansion.

## Test Steps

1. **Navigate to Artifacts**, viewport 1600x900.
   *Assert*: heading visible; both bucket rows rendered and neither selected.
2. *Assert (case Step 2)*: rows for A and B both exist (`to_have_count(1)` each).
3. **Click bucket A.**
   *Assert*: A is `data-selected="true"` (highlighted); A is expanded — its tree
   nodes `a1/` and `root.txt` are visible; the main panel lists A's root
   contents `{a1, root.txt}`; breadcrumb bucket crumb == A, folder crumbs `[]`.
4. **Click bucket B.**
   *Assert (the case's core claim)*: A's tree nodes `a1/` and `root.txt` are
   **still visible** — A did not collapse — while A's row is now
   `data-selected="false"` (lost its highlight).
5. *Assert*: B is `data-selected="true"` and B's contents render — its tree node
   `b-root.txt` is visible and the main panel lists exactly `{b-root.txt}`.
6. *Assert*: breadcrumb bucket crumb == B and folder crumbs == `[]`.
7. *Assert*: URL is `?bucket=<B>` (anchored full-query match).
8. **Click bucket A again.**
   *Assert*: A is `data-selected="true"` again and still/again expanded
   (`a1/`, `root.txt` visible); B is `data-selected="false"`.
9. *Assert*: the main panel lists A's contents `{a1, root.txt}` again;
   breadcrumb bucket crumb == A; URL is `?bucket=<A>`.

Each step is wrapped in `with allure.step("Step N — …")`; every assertion is
web-first, no sleeps.

## Expected Results
- Both buckets are listed; clicking one highlights it, expands it, and shows its
  contents in the main panel.
- Selecting the second bucket moves the highlight without collapsing the first —
  the first bucket's tree nodes remain rendered.
- Breadcrumb and URL follow the selected bucket.
- Returning to the first bucket restores its highlight, its expansion and its
  main-panel contents.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | § Preconditions | `auth_state` | covered |
| Precondition: two buckets, one with files | — | § Preconditions + step 2 | seeded; both rows asserted present | asserted |
| 1 Navigate to Artifacts | Artifacts page loads | step 1 | heading visible | asserted |
| 2 At least two buckets present | both visible | step 2 | row count 1 for each of A and B | asserted |
| 3 Click "bucket-1" — highlighted, expands, files shown in the main panel | highlighted + expanded + files | step 3 | `data-selected="true"`, `a1/`+`root.txt` tree nodes visible, `get_file_names() == {a1, root.txt}` | asserted |
| 4 Click "bucket-2" — "bucket-1" does NOT collapse but loses highlight | bucket-1 expanded + unhighlighted | step 4 | A's tree nodes still visible **and** A `data-selected="false"` | asserted |
| 5 "bucket-2" highlighted, its contents shown | highlighted + contents | step 5 | B `data-selected="true"`, `b-root.txt` node visible, `get_file_names() == {b-root.txt}` | asserted |
| 6 Breadcrumb updates to "bucket-2" | breadcrumb shows bucket-2 | step 6 | bucket crumb == B, folder crumbs `[]` | asserted |
| 7 URL updates to reflect "bucket-2" | URL reflects bucket-2 | step 7 | `to_have_url(re…bucket=<B>$)` | asserted |
| 8 Click back on "bucket-1" — highlighted again and expanded | re-selected + expanded | step 8 | A `data-selected="true"`, A's tree nodes visible, B `data-selected="false"` | asserted |
| 9 Main panel displays "bucket-1" contents again | bucket-1 files shown | step 9 | `get_file_names() == {a1, root.txt}` + breadcrumb + URL | asserted |
| Expected Final State: main panel, breadcrumb and URL update on switch; bucket-1 stays expanded | — | steps 3-9 | the assertions above | asserted |

### Axis 2 — Analyst additions
- **"Loses its highlight" is asserted on the row's own `data-selected`, and
  "does not collapse" on the presence of its children** — two independent
  attributes of two different elements. Collapsing them into one check (e.g.
  only reading the selected row) would let a regression that collapses the
  previous bucket pass unseen, which is the exact behaviour this high-priority
  case exists to protect.
- **Exclusivity is asserted in both directions** (step 8 also asserts B is
  `false`): "A is selected" alone would pass if the product highlighted both.
- **Main-panel contents are asserted as SET equality**, so "the panel updated"
  cannot be satisfied by a panel that merely *added* the new bucket's rows.
- **B is given a distinct filename** so that no tree/panel assertion can match
  the other bucket's node by coincidence.
- **NOT asserted: bucket-list ordering, pinning, scrolling** — other cases'
  subjects (ELITEA-1820/1821/1822).
- **NOT asserted: console errors** (recurring environmental flake class).

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| Both buckets created via the artifacts API (`artifact_bucket` fixture for A, `ArtifactAPI.create_bucket` for B) and their files via `ArtifactAPI.upload_file` | **Transit** | The case's precondition requires only that two buckets exist with content; it prescribes no creation path. Every asserted observable — row selection attributes, rendered tree nodes, main-panel rows, breadcrumb text, URL — is produced by the running product. |

## Blocked Steps
None.

## Findings
- **No defect found.** Every one of the case's 9 steps behaved exactly as
  written, including the load-bearing Step 4 (the previously selected bucket
  stays expanded). Mechanism, for the record: expansion lives in
  `BucketsListContent.jsx`'s `expandedBuckets` map, which is only ever set to
  `true` for a newly selected bucket and toggled solely by clicking an
  **already-active** row (`BucketItem.handleSelectBucket` → `onToggle`, the
  `#651` behaviour) — so selecting a different bucket cannot collapse the
  previous one.
- **Digest note (not a case claim):** returning to bucket A restores A's own
  expansion, but a subfolder that had been expanded *inside* A comes back
  collapsed — `BucketContent` remounts and `FileTreeItem` re-initialises from
  `expandedPaths`, which is empty once `currentPrefix` was reset by the bucket
  click. Out of scope here (ELITEA-1836 owns subfolder expansion), recorded so
  nobody reads it as a regression.

## Live-execution evidence (2026-08-21, localhost:5173, project Private/399)
Executed live with buckets `autotest-test-explore-462441` (A: `a1/f1.txt`,
`a1/f2.txt`, `root.txt`) and `autotest-test-explore-462441-b` (B: `b-root.txt`):
- Click A → `data-selected="true"`, URL `?bucket=<A>`, tree `a1/` + `root.txt`
  visible, main panel `['a1', 'root.txt']`, breadcrumb `<A>` + `[]` (Step 3 ✓).
- Click B → B selected `true`, A selected **false**, A's tree nodes `a1/` and
  `root.txt` **still present and visible** (count 1 each), B's `b-root.txt`
  visible, main panel `['b-root.txt']`, breadcrumb `<B>` + `[]`, URL
  `?bucket=<B>` (Steps 4-7 ✓).
- Click A again → A selected `true`, B `false`, `a1/` visible, main panel
  `['a1', 'root.txt']`, breadcrumb `<A>` + `[]`, URL `?bucket=<A>` (Steps 8-9 ✓).
- Console errors during the full flow: none.
