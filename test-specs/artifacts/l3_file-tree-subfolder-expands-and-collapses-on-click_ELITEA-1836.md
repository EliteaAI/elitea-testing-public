# Test Case: File Tree Behavior – Subfolder Expands and Collapses on Click

## Metadata
- **TMS ID**: ELITEA-1836
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/399)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, artifacts-w02, 2026-08-21)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (auth_state, localhost).
- A bucket exists containing subfolder `a1/` with files under it. The case names
  "bucket-1"/"a1"; **no such fixture bucket exists in this project** (digest
  § ELITEA-1851 cluster), so the test seeds its own fresh bucket via the
  `artifact_bucket` fixture and creates `a1/f1.txt` + `a1/f2.txt` with
  `ArtifactAPI.upload_file` (transit — see § Fidelity Declaration). Seeding ONLY
  files under `a1/` makes the bucket's tree top level exactly `[a1]`, which is
  what the case's Step 6 describes.
- The seeded bucket must **not** be the bucket `/artifacts` auto-selects on a
  param-less load (that would make Step 2's click a collapse toggle — open
  CLARIFICATION `EliteaAI/elitea-testing-public#651`). Asserted as a precondition:
  `is_bucket_selected(bucket) is False` right after navigation. Live: the
  auto-selected row is the alphabetically-first bucket (`aa`), never an
  `autotest-…` one.

## Test Data
### seeded (per test, cleaned up by the fixture)
- Bucket: `autotest-<test-name>-<ts>` (`artifact_bucket` fixture)
- `a1/f1.txt`, `a1/f2.txt` — 2 small text files, uploaded through
  `ArtifactAPI.upload_file`; `a1/` is an S3 key prefix (there is no "create
  folder" UI).

## Concrete Handles

| Element | Handle | Provenance |
|---|---|---|
| Bucket row in the left panel | `artifacts-bucket-row-{name}` (`ArtifactsPage.BUCKET_ROW`) | pre-existing, `on-main ✓` |
| Bucket row selection state | `data-selected="true|false"` on the same row (`is_bucket_selected()`) | pre-existing |
| Tree node (folder or file), keyed by its full relative key | `artifacts-tree-item-{key}` (`ArtifactsPage.ARTIFACTS_TREE_ITEM`) — folder key carries a trailing slash (`a1/`), a nested file's key is the full path (`a1/f1.txt`) | pre-existing, `FileTreeItem.jsx:107` |
| Tree node selection state | `data-selected` on the tree node (`is_tree_item_selected()`) | pre-existing |
| Main-panel breadcrumb — bucket crumb | `artifacts-breadcrumb-bucket-label` (`get_breadcrumb_bucket_text()`) | pre-existing (ELITEA-1824) |
| Main-panel breadcrumb — folder crumb(s) | `artifacts-breadcrumb-folder-label` (`get_breadcrumb_folder_names()`) — conditionally rendered, absent at bucket root | pre-existing (ELITEA-1824) |
| Main-panel file rows | `artifacts-file-row` / `artifacts-folder-row` (`get_file_names()`) | pre-existing |
| Buckets page heading | `artifacts-buckets-heading` (`wait_for_page_load()`) | pre-existing |

**No new testid is needed and none was added.** Every element this case touches
already carries one.

**Page-object gap:** none for this case — `click_tree_item` / `is_tree_item_visible`
/ `is_tree_item_selected` / `tree_item` (locator accessor for `expect(...)`) all
exist.

## Test Steps

1. **Navigate to Artifacts** (`navigate_to_artifacts()` + `wait_for_page_load()`),
   viewport 1600x900.
   *Assert*: buckets heading visible; the seeded bucket's row is rendered and
   `data-selected="false"` (guards the `#651` toggle trap).
2. **Click the bucket row** (`click_bucket_row(bucket)`).
   *Assert*: the row is selected (`data-selected="true"`), the tree node `a1/`
   becomes visible beneath it, and the bucket's own children `a1/f1.txt` /
   `a1/f2.txt` are **not** rendered (`to_have_count(0)`) — the subfolder starts
   collapsed, which is what makes Step 3's expansion observable.
3. **Click the tree node `a1/`** (`click_tree_item("a1/")`).
   *Assert*: `a1/f1.txt` **and** `a1/f2.txt` tree nodes are visible (the
   subfolder expanded and lists its files), `a1/` itself is still visible and is
   now the selected tree node.
4. **Verify the main-panel header** (no click).
   *Assert*: breadcrumb bucket crumb == bucket name **and** folder crumbs ==
   `["a1"]` — i.e. the header reads `bucket > a1`. Also assert the main panel now
   lists the subfolder's files (`{f1.txt, f2.txt}`), which is the observable
   behind "the main panel header updates on expansion".
5. **Click the tree node `a1/` again** (`click_tree_item("a1/")`).
   *Assert*: `a1/f1.txt` and `a1/f2.txt` are gone from the tree
   (`to_have_count(0)` — MUI `Collapse unmountOnExit` removes them ~300 ms after
   the click; a web-first assertion covers the animation, no sleep).
6. *Assert (final tree state)*: the tree shows the bucket row plus `a1/`, still
   visible and still collapsed — `a1/` visible, its two children count 0.

**Ordering discipline (load-bearing, see § Findings / `#1631`):** Step 4's
assertions must run **between** the two `a1/` clicks. A collapse click fired
immediately after the expand click is discarded 2 times in 5 (measured); with
Step 4's assertions in between it collapsed 5/5 (and 7/7 in two earlier probes).
The case's own step order is what makes the test deterministic — do not "optimise"
Step 4 to after Step 5.

Each step is wrapped in `with allure.step("Step N — …")`.

## Expected Results
- Clicking the bucket expands it and lists `a1` beneath it, with `a1` itself
  collapsed.
- Clicking `a1` expands it: `f1.txt` and `f2.txt` appear as tree nodes under it,
  `a1` becomes the selected tree node.
- The main-panel header reads `bucket > a1` and the panel lists `f1.txt` /
  `f2.txt`.
- Clicking `a1` again collapses it: both file nodes are removed from the tree,
  `a1` stays listed under the bucket.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | § Preconditions | `auth_state` | covered |
| Precondition: bucket with subfolder `a1` containing files | — | § Preconditions | seeded via fixture + `upload_file`; existence asserted in steps 2-3 | asserted |
| 1 Navigate to Artifacts | Artifacts page loads | step 1 | heading visible + bucket row rendered | asserted |
| 2 Click "bucket-1" — it expands and shows subfolder "a1" | bucket expands, `a1` shown | step 2 | row `data-selected="true"`, `a1/` tree node visible | asserted |
| 3 Click subfolder "a1" — it expands, files listed beneath it in the tree | `a1` expands, files shown | step 3 | `a1/f1.txt` + `a1/f2.txt` visible | asserted |
| 4 Main panel header displays "bucket-1 > a1" | breadcrumb shows `bucket-1 > a1` | step 4 | bucket crumb == bucket, folder crumbs == `["a1"]` | asserted |
| 5 Click "a1" again — it collapses, files no longer shown in the tree | `a1` collapses, files hidden | step 5 | both child nodes `to_have_count(0)` | asserted |
| 6 Left panel returns to the bucket entry with "a1" listed but collapsed | bucket + collapsed `a1` | step 6 | `a1/` visible **and** children count 0 | asserted |
| Expected Final State: `a1` toggles between expanded and collapsed; header updates on expansion | — | steps 3-6 | the assertions above | asserted |

### Axis 2 — Analyst additions
- **The pre-state is asserted, not assumed** (step 2 asserts the children are
  absent *before* the expand click). Without it, "files are visible after the
  click" would pass on a tree that was already expanded, proving nothing about
  the click.
- **Both child files are asserted, not just one** — "shows its files" is a set
  claim; a single-file check would pass on a partially-rendered subtree.
- **The main panel's file list is asserted alongside the breadcrumb** (step 4).
  The case names only the header, but the header and the table are driven by the
  same `currentPrefix`; asserting both makes "the main panel updated" mean the
  content, not just the label.
- **NOT asserted: that the breadcrumb/URL reset on collapse.** Live, they do
  **not** — collapsing keeps `currentPrefix = a1/`, so the header stays
  `bucket > a1` and the URL keeps `&folder=a1` (`FileTreeItem.handleSelect` calls
  `onSelectFolder` on *both* clicks; only the local `isExpanded` toggles). The
  case makes no claim either way, and asserting a reset would be inventing a
  requirement. Recorded in the digest so the next reader is not surprised.
- **NOT asserted: console errors** — `.agents/testing.md` § Unconfirmed records a
  confirmed recurring environmental console-500/404 flake class on this project.
- **NOT asserted: breadcrumb/URL detail** — that is ELITEA-1837's subject, kept
  there to avoid two specs owning the same claim.

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| Bucket creation (`artifact_bucket` fixture → artifacts API) and the two seed files (`ArtifactAPI.upload_file`) | **Transit** | The case's precondition merely requires the bucket + subfolder to *exist*; it does not ask that they be created through the UI. Every asserted observable (tree nodes, selection state, breadcrumb, main-panel rows) is rendered by the running product from its own data. |

## Blocked Steps
None.

## Findings
- **Product defect (MINOR, does not block automation):** a rapid second click on
  a subfolder fails to collapse it — 2 of 5 live attempts with no wait between
  the expand and collapse clicks; 5/5 collapse when the case's own Step-4
  assertions run in between. Likely mechanism: `BucketContent.jsx`'s
  `isFetching` early-return unmounts the `FileTreeItem` subtree, which then
  re-initialises `isExpanded` from `expandedPaths` (still containing the folder).
  Filed `EliteaAI/elitea-testing-public#1631`.
- **Case-text nuance (no filing):** Step 4 says "the main panel header updates on
  expansion". It updates on *selection* — the same click that expands also sets
  `currentPrefix`, and a collapse click keeps the header where it is. Nothing in
  the case contradicts the live product, so this is a digest note, not a defect.

## Live-execution evidence (2026-08-21, localhost:5173, project Private/399)
Executed live against a seeded bucket with `a1/f1.txt`, `a1/f2.txt`, `root.txt`:
- After `click_bucket_row`: `data-selected="true"`, URL `?bucket=<name>`, tree
  shows `a1/` + `root.txt`, `a1/f1.txt` count **0** (Step 2 ✓).
- After clicking `a1/`: `a1/f1.txt` + `a1/f2.txt` visible, `a1/` selected
  (`is_tree_item_selected("a1/") == True`), bucket row `data-selected` → `false`
  (tree selection is exclusive), breadcrumb `<bucket>` + `['a1']`, URL
  `?bucket=<name>&folder=a1`, main panel `['f2.txt', 'f1.txt']` (Steps 3-4 ✓).
- After clicking `a1/` again: child count 1 → **0** at t≈300 ms, `a1/` still
  visible and selected, `root.txt` still visible; breadcrumb and URL unchanged
  (Steps 5-6 ✓). Reproduced 3/3 in probe 2 and 4/4 in probe 3 with a settle.
- Console errors during the full flow: none.
