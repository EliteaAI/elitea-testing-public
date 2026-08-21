# Test Case: Scroll Through Bucket List with 20 or More Buckets

## Metadata
- **TMS ID**: ELITEA-1822
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/399)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, artifacts-w01, 2026-08-21)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (auth_state, localhost).
- **At least 20 buckets exist in the project** — satisfied by the project's
  **existing** buckets: 768 rendered live in `Private`/399 on 2026-08-21
  (the `#636` leak keeps this number growing). The case's fallback ("if fewer
  than 20 exist, create bucket-1…bucket-20") is therefore **not exercised** —
  seeding 20 buckets would add 20 permanent rows to a project already leaking
  them, for zero extra signal. The test asserts the ≥20 precondition (the
  case's own Step 3 expected result) instead of creating it, and is fully
  read-only (workflow skill Hard Rule 10).

## Test Data
### existing-stable (read-only)
- The bucket rows already present in `Private`/399. Only their *rendered
  geometry* is read (is a given row inside the panel's visible band?), never
  their contents. Row identity comes from
  `ArtifactsPage.get_rendered_bucket_names()`, snapshotted once at Step 3, so
  the test names no literal bucket.

## Concrete Handles

| Element | Handle | Provenance |
|---|---|---|
| Buckets list scroll container (the "bucket list panel" the case scrolls) | `artifacts-buckets-scroll-container` | **added this run**, `BucketsPanel.jsx`'s `bucketListOuterContainer` Box, EliteaAI/EliteaUI@3c96bc4b — on `automation/testids` only (awaiting human promotion to main) |
| A named bucket row | `artifacts-bucket-row-{name}` (dynamic — `ArtifactsPage.BUCKET_ROW`) | pre-existing |
| Any bucket row | `[data-testid^="artifacts-bucket-row-"]` (`ArtifactsPage.BUCKET_ROW_ANY_SELECTOR`) | pre-existing |
| Buckets page heading | `artifacts-buckets-heading` | pre-existing (`wait_for_page_load()`) |
| Sidebar Artifacts entry | `sidebar-menu-item-artifacts` — or `ArtifactsPage.navigate_to_artifacts()` (direct URL transit) | pre-existing |

**No new non-testid handle is introduced.** "Is this row currently visible in
the panel?" is answered by comparing the row's own `bounding_box()` against the
scroll container's — both located by testid — because a row scrolled out of an
`overflow: auto` container is still `is_visible() == True` in Playwright
(it has a box and is not `visibility: hidden`; it is merely clipped).

## Test Steps

1. **Navigate to Artifacts** (`ArtifactsPage.navigate_to_artifacts()` +
   `wait_for_page_load()`), viewport 1600x900.
   *Assert*: buckets heading visible; at least one bucket row rendered.
2. **Read the rendered bucket list** (`get_rendered_bucket_names()`).
   *Assert*: ≥ 20 distinct bucket rows (the case's Step 2/3 expected result).
   Snapshot `first = names[0]`, `last = names[-1]`.
3. *(implementation note — the shipped spec folds steps 3 and 4 into one
   `allure.step`, because both need the cursor already over the panel.)*
4. **Place the cursor over the bucket list panel** — `page.mouse.move()` to the
   centre of `artifacts-buckets-scroll-container`. Then, as **setup** (not an
   assertion): wheel UP (`0, -5000`, ≤ 40 steps) until the first bucket is in
   view, because `/artifacts` auto-selects a bucket and
   `SimpleBucketList.jsx` scrolls it into view, so the list does not reliably
   start at its top and the case's Steps 4-6 presume it does. This uses the
   product's own scrolling — nothing is injected. Then **find the fold**: scan
   `names[15:80]` for the first row NOT fully inside the container's visible band
   → `below_fold`.
   *Assert*: the first bucket is in the visible band, and `below_fold` exists —
   i.e. the list really is longer than the panel (there is something to scroll to).
5. **Scroll down one wheel notch** (`page.mouse.wheel(0, 500)`).
   *Assert*: `below_fold` is now inside the visible band **and** `first` has
   left it — the list scrolled down and buckets further in the list became visible.
6. **Keep wheeling down** (`0, 5000` per step, ≤ 40 steps) until `last` is
   inside the band.
   *Assert*: `last` (the final bucket of 768) is inside the visible band — the
   whole list is reachable by wheel.
7. **Scroll back up one wheel notch** (`0, -500`).
   *Assert*: `last` has left the band — the list scrolled up.
8. **Keep wheeling up** (`0, -5000`, ≤ 40 steps) until `first` is inside the band.
   *Assert*: `first` is inside the band and its top edge sits within 56 px
   (the container's 16 px padding + one 40 px row) of the container's top — the
   first bucket is back at the top.
9. **Click into the bucket list panel** at the container's left padding gutter
   (x + 6 px), which contains no row — verified live: the URL does not change
   and no bucket is selected (the spec asserts the URL is unchanged). Then
   **press `ArrowDown`** until `below_fold` enters the band (≤ 80 presses,
   ~38.7 px per press measured live).
   *Assert*: `below_fold` is in band and `first` has left it — the list scrolls
   down under keyboard control.
10. **Press `ArrowUp`** until `first` is back in the band (≤ 80 presses).
    *Assert*: `first` is in band with its top edge within 56 px of the
    container's top — the list scrolled back up to the first listed bucket.

Every scroll assertion settles through
`ArtifactsPage.wait_until_bucket_row_within_panel()` — a polled condition wait on
the product's rendered geometry, because `mouse.wheel()` returns before the
scroll is applied. No fixed sleep stands in for a wait.

Each step is wrapped in `with allure.step("Step N — …")`.

## Expected Results
- The bucket list (768 buckets, no virtualisation — every row is in the DOM)
  scrolls under the mouse wheel in both directions, reaching the last bucket
  and returning to the first.
- The same list scrolls under `ArrowDown` / `ArrowUp` after the user clicks
  into the panel, in both directions.
- No bucket is selected and no navigation occurs as a side effect of the
  scrolling interactions.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | § Preconditions | `auth_state` | covered |
| Precondition: ≥20 buckets exist (else create bucket-1…20) | ≥20 present | step 2 | `len(get_rendered_bucket_names()) >= 20` | asserted *(satisfied read-only by 768 existing buckets; the create-fallback is deliberately not exercised — see § Preconditions)* |
| 1 Navigate to Artifacts | Artifacts page loads | step 1 | heading visible + ≥1 bucket row | asserted |
| 2 Bucket list displayed / create if <20 | ≥20 buckets present | step 2 | same count assertion | asserted |
| 3 At least 20 buckets present | 20+ listed | step 2 | `>= 20` distinct rows | asserted |
| 4 Cursor over the bucket list panel | cursor over the list | step 4 (also carries the top-of-list setup scroll) | `mouse.move()` onto the container's own testid box (precondition for the wheel events that follow — a wheel with the cursor elsewhere would scroll something else) | covered |
| 5 Scroll down with the wheel | list scrolls, further buckets visible | step 5 | `below_fold` enters band, `first` leaves it | asserted |
| 6 Continue until the last bucket is visible | all buckets reachable | step 6 | `last` (bucket #768) inside the band | asserted |
| 7 Scroll back up with the wheel | list scrolls up | step 7 | `last` leaves the band | asserted |
| 8 Continue until the first bucket is visible | first bucket at the top | step 8 | `first` in band **and** its top within one row height of the container top | asserted |
| 9 Click into the panel, press Down repeatedly | list scrolls down, further buckets visible | step 9 | `below_fold` in band, `first` out of band | asserted |
| 10 Press Up repeatedly | scrolls back to the first bucket | step 10 | `first` in band, top-aligned | asserted |
| Expected Final State: fully scrollable by wheel and keyboard in both directions | — | steps 5-10 | the assertions above | asserted |

### Axis 2 — Analyst additions
- **"First bucket is at the top" asserted as top-alignment, not merely
  visibility** (steps 8/10). With a 755 px band and 40 px rows, "the first
  bucket is somewhere in the panel" is true for any scroll position under
  ~715 px, so a visibility-only check would pass while the list is still
  scrolled. The extra clause (top edge within one row height of the container's
  content top) is what makes "back at the top" mean it.
- **`first` asserted to LEAVE the band on every downward scroll** (steps 5/9).
  The case says "buckets further in the list become visible"; asserting only
  that a later bucket appeared would also pass if the panel had merely grown.
  The pair (later bucket in, first bucket out) is what proves a scroll.
- **The click target for step 9 is the panel's padding gutter, and the absence
  of a side effect is asserted** (URL unchanged, no row selected). Clicking a
  bucket row would select and expand a bucket — a different interaction than
  the case describes, and one that would make the later assertions read a
  different DOM.
- **The list is wheeled to its top before Step 4's assertions** (declared setup, not a substitution — it scrolls via the product's own wheel handling). Without it the case's "scroll down from the top" premise is at the mercy of which bucket `/artifacts` auto-selected.
- **`below_fold` is discovered live, never hardcoded to an index.** Row height
  and panel height are theme/viewport dependent; the test scans for the first
  out-of-band row so it stays correct if either changes.
- **NOT asserted: scroll offsets (`scrollTop`) or wheel-delta arithmetic.**
  Those are implementation values, not the case's observable, and reading them
  needs `evaluate()`. Every assertion here reads the geometry the product
  actually rendered.
- **NOT asserted: console errors.** `.agents/testing.md` § Unconfirmed records a
  confirmed recurring environmental console-500/404 flake class on this project;
  importing it into a pure scrolling test buys noise, not signal.
- **NOT asserted: smooth-scroll animation or scrollbar styling** — the case
  never mentions them.

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| *(none)* | — | The test performs **no** substitution: no seeding, no `page.route`, no injected state, no `evaluate()` writing anything. Every observable is the geometry the product rendered in response to real `mouse.wheel` / `keyboard.press` events dispatched by the browser. The ≥20-bucket precondition is met by buckets that already exist. |

## Blocked Steps
None.

## Live-execution evidence (2026-08-21, localhost:5173, project Private/399)
- 768 bucket rows rendered; container `scrollHeight` 30792, `clientHeight` 755
  (no virtualisation — every row is in the DOM).
- Wheel: one `wheel(0, 500)` moved `scrollTop` 16 → 516; six `wheel(0, 5000)`
  reached the bottom (30037 = 30792 − 755) with the last bucket
  (`zzz-test-unpin-bucket-from-top-584583`) rendered inside the panel; seven
  `wheel(0, -5000)` returned to `scrollTop` 0 with the first bucket (`aa`) at
  the top.
- Keyboard: after clicking the panel's padding gutter (`document.activeElement`
  stayed `BODY`, URL unchanged), 10 × `ArrowDown` moved `scrollTop` 0 → 387
  (~38.7 px/press) and `ArrowUp` moved it back — Chromium scrolls the clicked
  scroll container even though the container itself is not focusable. **No
  product defect found in any of the 10 steps.**
