# Test Case: Unpin Artifact Bucket from Top

## Metadata
- **TMS ID**: ELITEA-1821
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/399)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, artifacts-w01, 2026-08-21)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (auth_state, localhost).
- **"bucket-1" is pinned and displayed at the top of the bucket list with a pin
  icon next to its name.** Established **through the UI**, inside the test: the
  seeded bucket is pinned via its own dot-menu "Pin to top" item, exactly as a
  user would, and the pinned state is verified before the case's own steps
  begin. No API shortcut, so this case performs **no** precondition
  substitution at all.
- No other bucket is pinned (verified at the start — it is what makes "at the
  top" and "no longer at the top" unambiguous).

## Test Data
### seeded (created + cleaned up by the test)
- One bucket `zzz-pin-1821-<ts>` created via `ArtifactAPI.create_bucket`. A
  `z`-prefix places it near the end of the alphanumeric list, so "moved to the
  top" and "returned to its alphanumeric position" are far apart and cannot pass
  by accident.
- **Teardown clears the pin first, then deletes the bucket**
  (`ArtifactAPI.set_bucket_pinned(name, False)`) — bucket deletion on this
  project is unreliable (`#636`) and a leaked *pinned* bucket would sit at the
  top of every project member's list forever.

### existing-stable (read-only)
- The project's other buckets — their rendered order is captured before the pin
  and compared again after the unpin; never mutated.

## Concrete Handles

Identical to ELITEA-1820's table (same surface, same run):

| Element | Handle | Provenance |
|---|---|---|
| Bucket row (per bucket) | `artifacts-bucket-row-{name}` | pre-existing |
| Bucket-row 3-dot actions trigger | `bucket-menu-{name}-menu-button` | pre-existing |
| Open dropdown container | `bucket-menu-{name}-menu` | pre-existing |
| Dropdown "Unpin from top" / "Pin to top" item | `bucket-menu-pin-menuitem` | **added this run** (`key: 'bucket-menu-pin'` in `BucketItem.jsx`) — `automation/testids` only, awaiting human promotion to main |
| Pin icon next to a pinned bucket's name | `artifacts-bucket-pin-indicator-{name}` | **added this run** (`BucketItem.jsx`'s `isPinned &&` wrapper `<Box>`) — same commit |
| Any pin indicator | `[data-testid^="artifacts-bucket-pin-indicator-"]` | same commit |

**One testid, label carries the state.** The dropdown item is one live element
whose label is `isPinned ? 'Unpin from top' : 'Pin to top'`; per
`.agents/testing.md` § Locator policy (PR #581) the testid stays stable and the
state is read from the label the case itself names. This case asserts the
**"Unpin from top"** wording on the same testid ELITEA-1820 asserts as
"Pin to top" — the flip IS the observable.

## Test Steps
1. Navigate to `/artifacts` (viewport 1600x900) and wait for the bucket list
   - **Verify**: nothing is pinned yet (`artifacts-bucket-pin-indicator-*`
     count 0), the rendered order equals its own sorted order, and the seeded
     bucket is **not** first. Capture this order as the alphanumeric baseline.
2. **Precondition, through the UI** — hover the seeded bucket's row, open its
   3-dot menu, click "Pin to top", and wait for `PATCH
   /artifacts/buckets/default/{project}?name={bucket}` → 200.
3. Wait for the list to reflect the pin (~8-10 s, condition wait)
   - **Verify (case step 2)**: the bucket is displayed at the **top** of the
     list (first item) **with** its pin icon
     `artifacts-bucket-pin-indicator-{target}` visible next to its name.
4. Click the 3-dot actions icon next to the pinned bucket (case step 3)
   - **Verify**: the dropdown container is visible.
5. Read the dropdown's full text (case step 4)
   - **Verify**: it is exactly `Upload filesRenameUnpin from topDelete` — the
     pin item now reads **"Unpin from top"**.
   - **CLARIFICATION #666 (already filed, not re-filed)** — the case text names
     the second item "Edit"; the product labels it "Rename". Live label
     asserted (reverse-masking guard), existing drift issue referenced.
6. Click "Unpin from top" (`bucket-menu-pin-menuitem`) (case step 5)
   - **Verify**: `PATCH … ?name={bucket}` returns **200**.
7. Wait for the list to reflect the unpin (condition wait)
   - **Verify (case step 6)**: `artifacts-bucket-pin-indicator-{target}` is
     gone — count 0 — and no bucket at all is pinned.
8. Re-read the rendered bucket-name order
   - **Verify (case step 7)**: the target is **not** the first item.
   - **Verify (case step 8)**: the target is back in its alphanumeric position —
     the full rendered order is `== sorted(order)` **and** byte-identical to the
     baseline captured in step 1.

## Expected Results
- A pinned bucket's dropdown offers "Unpin from top" in place of "Pin to top".
- Unpinning persists (PATCH 200), removes the pin icon, and drops the bucket out
  of the top position.
- The bucket lands back in its correct alphanumeric position among the unpinned
  buckets — the list is restored exactly to its pre-pin order.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | § Preconditions | `auth_state` | covered |
| Precondition: "bucket-1" pinned, at top, with pin icon | pinned state established | steps 2-3 | pinned via the real UI menu; PATCH 200; then first-item + pin-icon asserted | asserted |
| Test Data: pinned bucket | — | § Test Data | seeded `zzz-pin-1821-<ts>` | covered |
| 1 Navigate to Artifacts | page loads | step 1 | bucket row visible | asserted |
| 2 "bucket-1" pinned, at top, with pin icon | at top with pin icon | step 3 | `rendered[0] == target` + pin indicator visible | asserted |
| 3 Click the 3-dot actions icon | dropdown appears | step 4 | dropdown container visible | asserted |
| 4 Dropdown shows "Unpin from top" | option visible | step 5 | dropdown text == `Upload filesRenameUnpin from topDelete` | asserted *("Edit" → live "Rename", CLARIFICATION #666)* |
| 5 Click "Unpin from top" | unpin completes | step 6 | PATCH … `?name=` returns 200 | asserted |
| 6 Pin icon no longer displayed | pin icon removed | step 7 | indicator count 0 (target and project-wide) | asserted |
| 7 Bucket no longer at the top | not the first item | step 8 | `rendered[0] != target` | asserted |
| 8 Bucket repositioned in alphanumeric order among unpinned | correct alphabetical position | step 8 | `rendered == sorted(rendered)` **and** `rendered == baseline` | asserted |
| Expected Final State | unpinned, icon gone, alphanumeric | steps 7-8 | the assertions above | asserted |

### Axis 2 — Analyst additions
- **The precondition is built through the UI, not the API.** The cheaper route
  (a `set_bucket_pinned` PATCH) would have been a declared transit substitution;
  driving the real menu instead costs ~10 s and leaves the case with zero
  substitutions of any kind.
- **Baseline order captured before pinning and compared after unpinning**
  (steps 1, 8): "repositioned according to its correct alphanumeric order" is
  asserted as *byte-identical restoration of the whole list*, which is strictly
  stronger than checking the target's own index, and would catch a regression
  that reshuffles other buckets while placing the target correctly.
- **Project-wide "nothing is pinned" checked after the unpin** (step 7), not
  just the target's own indicator — a regression that unpinned the wrong bucket
  (or pinned a second one) would otherwise pass.
- **PATCH 200 asserted for both the pin and the unpin** — the flag is persisted
  server-side and the UI's re-render lags it by ~8-10 s, so DOM-only assertions
  would not prove the state reached the backend.
- **NOT asserted: console errors** — same reasoning as ELITEA-1820 (known
  recurring environmental console-500/404 class, `.agents/testing.md`
  § Unconfirmed).
- **NOT asserted: persistence across reload** — live-confirmed during analysis,
  not in the case text, and a 766-bucket reload is expensive.

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| Bucket creation via `ArtifactAPI.create_bucket` instead of the UI's New Bucket form | **transit** | Reaches the case's starting data (a bucket to pin). Every observable this case reads — the "Unpin from top" label, the PATCH result, the pin icon's removal, the restored alphanumeric order — is produced by the product through real UI interaction. UI bucket creation is its own automated case (ELITEA-1808). |
| Teardown `set_bucket_pinned(name, False)` | **cleanup, not an observable** | Runs after all assertions; guards against a leaked bucket staying pinned project-wide (`#636`). |

The case's **precondition** (a pinned bucket) is NOT substituted — it is created
by clicking the product's own "Pin to top" item. No `page.route`, no
`route.fulfill`, no state-writing `page.evaluate`, no stubbed client.

## Live findings (2026-08-21, this analysis run)
Shared with ELITEA-1820 — see that AFS's § Live findings for the full set:
alphanumeric ordering confirmed over 766 buckets, pinned list rendered above the
unpinned list (once, not twice), ~8-10 s UI lag behind the PATCH 200, and the
`ArtifactAPI.delete_bucket` wrong-URL-shape finding behind `#636`.

Specific to this case:
- The unpin round-trip was live-confirmed end to end: `Unpin from top` → PATCH
  200 → indicator gone at ~t+8 s → rendered order **byte-identical** to the
  pre-pin baseline (766 names).
- A stale UI matters here: while the list still shows the bucket as unpinned,
  the dot-menu item still reads "Pin to top" and clicking it sends
  `is_pinned: true` **again** rather than unpinning (observed during
  exploration). This is why step 3 waits for the pinned state to actually
  render before opening the menu, rather than proceeding straight from the 200.

## Blocked Steps
None.
