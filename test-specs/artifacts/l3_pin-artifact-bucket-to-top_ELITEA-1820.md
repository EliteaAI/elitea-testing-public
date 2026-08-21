# Test Case: Pin Artifact Bucket to Top

## Metadata
- **TMS ID**: ELITEA-1820
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/399)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, artifacts-w01, 2026-08-21)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (auth_state, localhost).
- The bucket list contains at least two buckets in alphanumeric order —
  satisfied by the project's **existing** buckets (766 rendered live in
  `Private`/399, live-verified to be exactly ASCII-sorted when nothing is
  pinned, see § Live findings).
- **No bucket is currently pinned.** Live-verified as the normal state of the
  project; the two pin cases are the only things in the suite that pin, and both
  clear the flag in teardown (§ Test Data).
- A bucket that is **not** at the top of the list exists — this case seeds
  exactly one, named with a `z`-prefix so alphanumeric ordering places it near
  the end (the case's "bucket-1" stand-in).

## Test Data
### seeded (created + cleaned up by the test)
- One bucket `zzz-pin-1820-<ts>` created via `ArtifactAPI.create_bucket`
  (fixture-style seeding, the suite's `artifact_bucket` pattern). Fresh state is
  **required**: the case pins a bucket, which is a persisted, project-wide,
  user-visible mutation — it must not be done to a bucket anyone else's test or
  a human depends on.
- **Teardown clears the pin first, then deletes the bucket**
  (`ArtifactAPI.set_bucket_pinned(name, False)` — added this run). Order matters:
  bucket deletion on this project is unreliable (`#636`), and a leaked *pinned*
  bucket would sit at the top of every project member's bucket list forever.

### existing-stable (read-only)
- The project's other 766 buckets — only their rendered *order* and *names* are
  read, never mutated.

## Concrete Handles

| Element | Handle | Provenance |
|---|---|---|
| Bucket row (per bucket) | `artifacts-bucket-row-{name}` (dynamic, `ArtifactsPage.BUCKET_ROW`) | pre-existing |
| Any bucket row | `[data-testid^="artifacts-bucket-row-"]` (`BUCKET_ROW_ANY_SELECTOR`) | pre-existing |
| Bucket-row 3-dot actions trigger | `bucket-menu-{name}-menu-button` (`BUCKET_MENU_BUTTON`) | pre-existing (`DotMenu`'s `${id}-menu-button`) |
| Open dropdown container | `bucket-menu-{name}-menu` (`BUCKET_MENU_CONTAINER`) | pre-existing |
| Dropdown "Pin to top" / "Unpin from top" item | `bucket-menu-pin-menuitem` | **added this run** — `key: 'bucket-menu-pin'` on `BucketItem.jsx`'s menu item, which `DotMenu` turns into `data-testid="{key}-menuitem"`; on `automation/testids` only (awaiting human promotion to main) |
| Pin icon next to a pinned bucket's name | `artifacts-bucket-pin-indicator-{name}` (dynamic) | **added this run** — `BucketItem.jsx`'s `isPinned &&` wrapper `<Box>`; `automation/testids` only |
| Any pin indicator | `[data-testid^="artifacts-bucket-pin-indicator-"]` | same commit |

**Why ONE testid for a menu item whose label flips.** The pin item is a single
live element whose *label* is `isPinned ? 'Unpin from top' : 'Pin to top'`. Per
`.agents/testing.md` § Locator policy (PR #581 ruling) a testid must be stable
identity, never state — so the item keeps one testid (`bucket-menu-pin`) and its
state is asserted through the label text the case itself names. A
`bucket-menu-pin` / `bucket-menu-unpin` pair would be exactly the outlawed shape.

**Why the pin indicator is tagged and the hover pin button is not.**
`BucketItem.jsx` renders two mutually-exclusive pin buttons: the persistent one
under `isPinned &&` (the "pin icon next to the bucket name" this case asserts)
and a hover-only one under `!isPinned && isHovering`. Only the first is on this
test's executed path, so only it gets a testid (`.agents/testing.md` § Locator
policy, canon ruling #511 — no testids on elements the test does not call). This
also keeps the absence assertion in ELITEA-1821 honest: hovering an unpinned row
can never produce a false positive, because the hover button carries no testid.

## Test Steps
1. Navigate to `/artifacts` (viewport 1600x900) and wait for the bucket list
   - **Verify**: the seeded bucket's row is visible.
2. Read the rendered bucket-name order from the left panel
   - **Verify**: no bucket is pinned (`artifacts-bucket-pin-indicator-*`
     count 0) **and** the rendered order equals its own sorted order — i.e. the
     list is displayed in alphanumeric order (the case's step 2).
3. Identify the target bucket (the seeded `zzz-pin-1820-*`)
   - **Verify**: it is **not** the first item in the list.
4. Hover the target bucket's row
   - **Verify**: the 3-dot actions trigger becomes visible (it is
     `display:none` until the row is hovered — `BucketItem.jsx`'s
     `menuContainer` style).
5. Click the 3-dot actions trigger
   - **Verify**: the dropdown container is visible.
6. Read the dropdown's full text
   - **Verify**: it is exactly `Upload filesRenamePin to topDelete` — four
     items, in that order.
   - **CLARIFICATION #666 (already filed, not re-filed)** — the case text names
     the second item **"Edit"**; the product labels it **"Rename"**. Nothing is
     broken, so the live label is asserted (reverse-masking guard) and the
     existing case-text-drift issue is referenced. Same drift as #650
     (ELITEA-1824) and as the merged ELITEA-1817 spec, which already asserts
     this exact string.
7. Click "Pin to top" (`bucket-menu-pin-menuitem`)
   - **Verify**: the pin request completes — `PATCH
     /artifacts/buckets/default/{project}?name={bucket}` returns **200**
     (live-confirmed shape, `EliteaUI/src/api/artifacts.js` `updateBucketPin`).
8. Wait for the bucket list to reflect the new state
   - **Verify**: the pin icon `artifacts-bucket-pin-indicator-{target}` is
     visible next to the bucket's name.
   - **Timing:** the list takes ~8-10 s to re-render after the 200 (§ Live
     findings) — asserted with a condition wait (generous timeout), never a
     sleep.
9. Re-read the rendered bucket-name order
   - **Verify**: the target bucket is now the **first** item, i.e. above every
     unpinned bucket (`BucketsListContent.jsx` renders the pinned list before
     the unpinned list), and the remaining buckets are still in alphanumeric
     order among themselves.

## Expected Results
- The bucket list is alphanumeric while nothing is pinned.
- The bucket-row dropdown offers Upload files / Rename / Pin to top / Delete.
- "Pin to top" persists (PATCH 200), a pin icon appears next to the bucket name,
  and the bucket is repositioned above all unpinned buckets.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | § Preconditions | `auth_state` | covered |
| Precondition: ≥2 buckets in alphanumeric order | list alphanumeric | step 2 | rendered order == sorted(rendered order) | asserted |
| Precondition: "bucket-1" exists, not at the top | target not first | steps 1, 3 | seeded row visible; `rendered[0] != target` | asserted |
| Test Data: bucket to pin | — | § Test Data | seeded `zzz-pin-1820-<ts>` | covered |
| 1 Navigate to Artifacts | page loads | step 1 | seeded bucket row visible | asserted |
| 2 Bucket list in alphanumeric order | order is alphanumeric | step 2 | `names == sorted(names)` + 0 pin indicators | asserted |
| 3 Identify a bucket not at the top | not the first item | step 3 | `rendered[0] != target` | asserted |
| 4 Hover to reveal the actions icon | icon visible on hover | step 4 | trigger visible after `hover()` | asserted |
| 5 Click the actions icon | dropdown appears | step 5 | dropdown container visible | asserted |
| 6 Dropdown shows Upload files / Pin to top / Edit / Delete | all four visible | step 6 | dropdown text == `Upload filesRenamePin to topDelete` | asserted *("Edit" → live "Rename", CLARIFICATION #666)* |
| 7 Click "Pin to top" | pin action completes | step 7 | PATCH … `?name=` returns 200 | asserted |
| 8 Pin icon appears next to the bucket name | pin icon visible | step 8 | `artifacts-bucket-pin-indicator-{target}` visible | asserted |
| 9 Bucket displayed at the top, above all unpinned | first item | step 9 | `rendered[0] == target` | asserted |
| Expected Final State | pinned, icon, above unpinned | steps 8-9 | the assertions above | asserted |

### Axis 2 — Analyst additions
- **"No bucket is pinned" asserted as part of the alphanumeric check** (step 2):
  the case's "alphanumeric order" claim is only true of the unpinned list, so
  the precondition is verified rather than assumed. It also makes step 9's
  `rendered[0] == target` a sound assertion instead of a coincidence.
- **The remaining buckets are re-checked for alphanumeric order after the pin**
  (step 9): pinning must lift exactly one bucket out of the ordered list, not
  reshuffle it.
- **PATCH 200 asserted, not just the DOM** (step 7): the pin is a persisted
  server-side flag; a UI-only assertion would pass on an optimistic render that
  never reached the backend. (Live-relevant: the UI's own re-render lags the 200
  by ~8-10 s, so the two really are separate observables here.)
- **NOT asserted: console errors.** `.agents/testing.md` § Unconfirmed records a
  confirmed recurring environmental console-500/404 flake class on this project;
  importing it here would buy noise, not signal.
- **NOT asserted: the pin's persistence across a page reload.** Live-confirmed
  during analysis, but it is not in the case text and it doubles the runtime of
  an already slow (766-bucket) page load.

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| Bucket creation via `ArtifactAPI.create_bucket` instead of the UI's New Bucket form | **transit** | Reaches the case's starting state (a bucket that is not at the top of the list). The case's own observables — the dropdown, the pin request, the pin icon, the repositioning — are all produced by the product through real UI interaction. Bucket creation via the UI is its own case (ELITEA-1808), already automated. |
| Teardown `set_bucket_pinned(name, False)` | **cleanup, not an observable** | Runs after all assertions; exists so a leaked bucket cannot stay pinned project-wide (`#636`). Nothing is read from it. |

No `page.route`, no `route.fulfill`, no `page.evaluate` that writes, no stubbed
client. The pin state, the pin icon and the list order are all rendered by the
product from its own data.

## Live findings (2026-08-21, this analysis run)
- **The bucket list IS alphanumeric** — with zero pinned buckets, all **766**
  rendered names were exactly `== sorted(names)` (byte order; no case-folding
  ambiguity arose). Mechanism worth knowing: `SimpleBucketList.jsx` runs
  `sortBucketsByRecent`, but the listing payload carries no usable
  `updated_at`/`created_at`, so every comparison is `NaN` and the sort is a
  no-op — the order that survives is the backend's, which is alphanumeric. The
  case text is correct; the *reason* is incidental, so this test asserts the
  observable (alphanumeric order), not the mechanism.
- **Pinned buckets render in a separate list ABOVE the unpinned list**
  (`BucketsListContent.jsx`), and `BucketsPanel.jsx` splits `pinnedBuckets` /
  `unpinnedBuckets` — a pinned bucket is therefore rendered **once**, not twice.
  (`ArtifactsPage.get_rendered_bucket_names()`'s docstring claimed twice; the
  de-duplication is harmless but the claim is stale — corrected in this run.)
- **The list lags the pin by ~8-10 s.** The `PATCH` returns 200 immediately;
  the pin icon and the repositioning appeared at t+10 s (pin) and t+8 s (unpin)
  in live runs, with no intervening `GET .../artifacts/buckets/default/{pid}`
  observed. Not filed as a defect (the state does arrive, and the case sets no
  timing expectation) — recorded here because every assertion after the click
  needs a generous condition wait.
- **`ArtifactAPI.delete_bucket` uses the wrong URL shape** — it deletes via the
  path form `/artifacts/buckets/default/{pid}/{bucket}`, which 404s; the UI (and
  a live check of 10 leaked buckets, all 200) uses the query form
  `?name={bucket}`. This is the likely root cause of the long-standing `#636`
  bucket leak. Out of scope for this case (shared client, many callers) —
  reported to the lead.

## Blocked Steps
None.
