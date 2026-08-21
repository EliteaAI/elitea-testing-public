# Test Case: File Tree Behavior – Breadcrumb Path Updates on Navigation

## Metadata
- **TMS ID**: ELITEA-1837
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/399)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, artifacts-w02, 2026-08-21)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (auth_state, localhost).
- A bucket exists with subfolder `a1/`. Seeded per test: `artifact_bucket`
  fixture + `ArtifactAPI.upload_file` for `a1/f1.txt` and a root-level
  `root.txt` (transit — § Fidelity Declaration). `root.txt` exists so that
  Step 8's "root level contents are shown" is a *positive* observable (a root
  listing of `[a1, root.txt]`), not merely the absence of the subfolder view.
- The seeded bucket must not be the one `/artifacts` auto-selects on a
  param-less load (`#651` toggle trap) — asserted as a precondition.

## Test Data
### seeded (per test, cleaned up by the fixture)
- Bucket: `autotest-<test-name>-<ts>`
- `a1/f1.txt`, `root.txt`

## Concrete Handles

| Element | Handle | Provenance |
|---|---|---|
| Bucket row | `artifacts-bucket-row-{name}` (`BUCKET_ROW`, `click_bucket_row`, `is_bucket_selected`) | pre-existing, `on-main ✓` |
| Tree node | `artifacts-tree-item-{key}` (`ARTIFACTS_TREE_ITEM`; `a1/` for the folder) | pre-existing |
| Breadcrumb — bucket crumb (**also the click target of Step 7**) | `artifacts-breadcrumb-bucket-label` — `ArtifactTableToolbar.jsx:65`; `onClick` is wired **only while `currentPrefix` is truthy** (at bucket root the crumb is inert) | pre-existing testid; **new page-object method** `click_breadcrumb_bucket_label()` (additive) |
| Breadcrumb — folder crumb(s) | `artifacts-breadcrumb-folder-label` (`get_breadcrumb_folder_names()`) — conditionally rendered; count 0 at bucket root | pre-existing |
| Main-panel rows | `artifacts-file-row` / `artifacts-folder-row` (`get_file_names()`) | pre-existing |
| URL | `page.url` — `?bucket=<name>` at root, `?bucket=<name>&folder=a1` inside the subfolder (`Artifacts.jsx`'s `setSearchParams`) | product-owned, asserted with `expect(page).to_have_url(...)` |

**No new testid is needed and none was added.** The only framework addition is
the page-object method `ArtifactsPage.click_breadcrumb_bucket_label()`, wrapping
the pre-existing `breadcrumb_bucket_label` descriptor — specs may not build
locators (`.agents/testing.md` § Locator policy).

## Test Steps

1. **Navigate to Artifacts**, viewport 1600x900.
   *Assert*: heading visible; the seeded bucket row rendered and not selected.
2. **Click the bucket row.**
   *Assert*: row `data-selected="true"`.
3. *Assert (breadcrumb at bucket root)*: bucket crumb == bucket name **and**
   folder crumbs == `[]` (the header shows the bucket alone). Also assert the URL
   is `?bucket=<name>` with **no** `folder` param — the root-state baseline that
   makes Step 10's return meaningful.
4. **Click the tree node `a1/`.**
   *Assert*: `a1/` is the selected tree node.
5. *Assert (breadcrumb inside the subfolder)*: bucket crumb == bucket name **and**
   folder crumbs == `["a1"]` → `bucket > a1`.
6. *Assert (URL)*: matches `\?bucket=<name>&folder=a1$` — **both** params, the
   folder one without a trailing slash (product-normalised).
7. **Click the bucket crumb in the main-panel breadcrumb**
   (`click_breadcrumb_bucket_label()`).
8. *Assert (root contents)*: the main panel lists the bucket's root items —
   exactly `{a1, root.txt}`.
9. *Assert (breadcrumb)*: bucket crumb == bucket name **and** folder crumbs ==
   `[]` — the subfolder crumb is gone.
10. *Assert (URL)*: back to `?bucket=<name>` with no `folder` param.

Each step is wrapped in `with allure.step("Step N — …")`; every assertion is
web-first (`expect(...)`), no sleeps.

## Expected Results
- At the bucket root the header shows only the bucket name and the URL carries
  only `?bucket=`.
- Selecting `a1` updates the header to `bucket > a1` and the URL to
  `?bucket=…&folder=a1`.
- Clicking the bucket crumb navigates back to the root: root contents listed,
  the folder crumb removed, and the `folder` param dropped from the URL.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | § Preconditions | `auth_state` | covered |
| Precondition: bucket with subfolder `a1` | — | § Preconditions | seeded; existence asserted in steps 2/4 | asserted |
| 1 Navigate to Artifacts | Artifacts page loads | step 1 | heading visible + row rendered | asserted |
| 2 Click "bucket-1" | bucket is selected | step 2 | row `data-selected="true"` | asserted |
| 3 Header/breadcrumb displays "bucket-1" | breadcrumb shows bucket | step 3 | bucket crumb text + folder crumbs `[]` | asserted |
| 4 Click subfolder "a1" | `a1` is selected | step 4 | `is_tree_item_selected("a1/")` | asserted |
| 5 Breadcrumb updates to "bucket-1 > a1" | breadcrumb shows both | step 5 | bucket crumb + folder crumbs `["a1"]` | asserted |
| 6 URL updates to reflect the subfolder path | URL has bucket **and** folder params | step 6 | `to_have_url(re…bucket=<name>&folder=a1)` | asserted |
| 7 Click "bucket-1" in the breadcrumb | navigation back to root occurs | steps 7-8 | the click, then the root listing | asserted |
| 8 Main panel navigates back to the root | root contents shown | step 8 | `get_file_names() == {a1, root.txt}` | asserted |
| 9 Breadcrumb displays only "bucket-1" | folder crumb gone | step 9 | folder crumbs `[]` + bucket crumb text | asserted |
| 10 URL updates back to the root bucket path | only the bucket param | step 10 | `to_have_url(re…bucket=<name>$)` | asserted |
| Expected Final State: breadcrumb + URL reflect navigation; crumb click returns to root and clears the subfolder | — | steps 3-10 | the assertions above | asserted |

### Axis 2 — Analyst additions
- **The URL is asserted as an anchored full-query match**, not a substring.
  `"bucket=<name>" in url` would still pass with a stale `&folder=a1` appended —
  precisely the regression Step 10 exists to catch.
- **The root listing is asserted as a SET equality** (`{a1, root.txt}`), not "a1
  is present": the case's "root level contents are shown" is only meaningful if
  the panel is no longer showing the subfolder's contents.
- **The bucket-root baseline (step 3) asserts folder crumbs are `[]`**, so
  Step 9's "displays only bucket-1" is a return to a *verified* baseline rather
  than to an assumed one.
- **NOT asserted: that the tree collapses on breadcrumb-root navigation.** Live
  it does not (the `a1/` subtree stays expanded; only `data-selected` clears) —
  the case makes no claim, and ELITEA-1836 owns tree expand/collapse.
- **NOT asserted: console errors** (recurring environmental flake class,
  `.agents/testing.md` § Unconfirmed).

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| Bucket creation (`artifact_bucket` fixture) + the two seed files (`ArtifactAPI.upload_file`) | **Transit** | The case's precondition only requires the bucket and subfolder to exist. Every asserted observable — breadcrumb text, folder-crumb count, main-panel rows, and the browser URL — is produced by the running product. |

## Blocked Steps
None.

## Findings
- **Case-text detail confirmed, worth knowing:** the case's example URL
  `"...?bucket=bucket-1&folder=a1"` is exactly what the product produces — the
  `folder` param carries **no** trailing slash even though the internal prefix
  and the tree key do (`Artifacts.jsx` does
  `normalizedPrefix.replace(/\/$/, '')`). No drift, no filing.
- **The bucket crumb is only clickable inside a subfolder** — at bucket root
  `ArtifactTableToolbar` passes `onClick={undefined}`. Clicking it there is a
  no-op, not a bug; the case never does it.

## Live-execution evidence (2026-08-21, localhost:5173, project Private/399)
- After selecting the bucket: URL `…/artifacts?bucket=<name>`, breadcrumb
  `<bucket>` + folder crumbs `[]`, main panel `['a1', 'root.txt']` (Steps 2-3 ✓).
- After clicking `a1/`: breadcrumb `<bucket>` + `['a1']`, URL
  `…?bucket=<name>&folder=a1`, main panel `['f2.txt', 'f1.txt']` (Steps 4-6 ✓).
- After clicking the breadcrumb bucket crumb: URL back to `…?bucket=<name>`,
  folder crumbs `[]`, main panel `['a1', 'root.txt']`, `a1/` tree node
  `data-selected="false"` while the bucket row is selected again (Steps 7-10 ✓).
- Console errors during the full flow: none.
