# Test Case: Bucket Highlights on Mouse Hover

## Metadata
- **TMS ID**: ELITEA-1823
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/399)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, artifacts-w01, 2026-08-21)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (auth_state, localhost).
- **At least two buckets are present** — satisfied by the project's **existing**
  buckets: 768 rendered live in `Private`/399 on 2026-08-21. The case needs
  "several buckets" for its Step 8; the test uses three existing rows and seeds
  nothing (fully read-only, workflow skill Hard Rule 10 — and it adds nothing to
  the known `#636` bucket leak).
- **The rows used must not be the SELECTED bucket.** `/artifacts` auto-selects
  (and expands) a bucket when the URL carries no `?bucket=` param, and the
  selected row's background is `conversation.selected`, which *supersedes* the
  hover colour (`BucketItem.jsx`'s `getBackgroundColor()`: `if (isActive) …`
  wins before the `isHovering` branch). Hovering the selected row therefore
  produces **no** background change — correct product behaviour, but it makes
  the case's literal "the first bucket in the list" a trap on a fresh load,
  where the first row IS the auto-selected one. See § Findings.

## Test Data
### existing-stable (read-only)
- Three bucket rows already present in `Private`/399, chosen at run time as the
  first three rendered rows that are (a) `data-selected="false"` and (b) inside
  the panel's visible band. Row identity comes from
  `ArtifactsPage.get_rendered_bucket_names()`; the test names no literal bucket.

## Concrete Handles

| Element | Handle | Provenance |
|---|---|---|
| A named bucket row (hover target **and** the element whose background the case observes) | `artifacts-bucket-row-{name}` (dynamic — `ArtifactsPage.BUCKET_ROW`) | pre-existing, `on-automation/testids` and `main` — the same testid ELITEA-1808/1820/1822 use |
| Row selection state | `data-selected="true|false"` on the same row | pre-existing (`ArtifactsPage.is_bucket_selected()`, ELITEA-1824) |
| Buckets list scroll container (used only to park the cursor away from every row) | `artifacts-buckets-scroll-container` | added by ELITEA-1822, EliteaAI/EliteaUI@3c96bc4b — on `automation/testids` only (awaiting human promotion to main) |
| Buckets page heading | `artifacts-buckets-heading` | pre-existing (`wait_for_page_load()`) |
| Sidebar Artifacts entry | `sidebar-menu-item-artifacts` — or `ArtifactsPage.navigate_to_artifacts()` (direct URL transit) | pre-existing |

**No new testid is needed and none was added.** The case's observable is the
row's own rendered `background-color`, read through Playwright's web-first
`expect(...).to_have_css(...)` / `not_to_have_css(...)` on the **testid-anchored**
row locator — a computed-style assertion on a compliant locator, not a new
handle, and no `evaluate()`.

**Why the hover colour literal is NOT asserted.** The default background is
`conversation.normal: 'transparent'` in **both** palettes
(`darkPalette.js:352`, `lightPalette.js:350`) → computed `rgba(0, 0, 0, 0)`,
so "is this row in its default appearance?" is a theme-independent fact. The
*hover* colour is not: `white6` → `rgba(255, 255, 255, 0.06)` in dark (measured
live), `dark6` in light. The test therefore asserts **default vs not-default**,
which is exactly what the case's expected results say ("background colour
changes to indicate highlight" / "returns to its default appearance"), instead
of pinning a literal that flips with the user's theme.

## Test Steps

1. **Navigate to Artifacts** (`ArtifactsPage.navigate_to_artifacts()` +
   `wait_for_page_load()`), viewport 1600x900.
   *Assert*: buckets heading visible (`wait_for_page_load`) and at least one
   bucket row rendered.
2. **Read the rendered bucket list** (`get_rendered_bucket_names()`) and pick the
   first three non-selected rows inside the panel's visible band → `A`, `B`, `C`.
   *Assert*: ≥ 2 bucket rows rendered (the case's own precondition) and three
   hoverable candidates were found (the case's Step 8 "several buckets").
3. **Move the cursor away from the bucket list** — `page.mouse.move()` to a point
   to the RIGHT of the scroll container's box (the main file panel), i.e. over no
   bucket row.
   *Assert*: `A`, `B`, `C` all have `background-color: rgba(0, 0, 0, 0)` — no
   bucket is highlighted.
4. **Hover `A`** (`hover_bucket_row(A)` → a real `Locator.hover()`, which
   dispatches the `mousemove`/`mouseenter` the product listens for on
   `BucketItem`'s root Box).
5. *Assert*: `A`'s background is **no longer** the default `rgba(0, 0, 0, 0)` —
   the row is highlighted. And `B`, `C` are still default (only the hovered row
   changed).
6. **Move the cursor to `B`** (`hover_bucket_row(B)`).
7. *Assert*: `A` is back to the default `rgba(0, 0, 0, 0)` **and** `B` is
   not-default — the previously hovered bucket reverted, the new one highlighted;
   `C` still default.
8. **Repeat for `C`** (`hover_bucket_row(C)`).
   *Assert*: `C` not-default, `A` and `B` default — the single-highlight
   invariant holds across several buckets.
9. **Move the cursor away again** (same neutral point as step 3).
   *Assert*: `A`, `B`, `C` all default — the Expected Final State's "the
   highlight is removed when the cursor moves away".

Every colour assertion is a web-first `expect(...).to_have_css(...)` /
`not_to_have_css(...)`, which retries until the style settles — no sleep stands
in for a wait. Each step is wrapped in `with allure.step("Step N — …")`.

## Expected Results
- With the cursor off the list, every exercised bucket row renders its default
  (transparent) background.
- The row under the cursor — and only that row — renders a non-default
  background (live-measured `rgba(255, 255, 255, 0.06)` in the dark theme).
- Moving to the next bucket reverts the previous one to default and highlights
  the new one; the invariant holds for three consecutive buckets.
- Moving the cursor off the list clears the highlight entirely.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | § Preconditions | `auth_state` | covered |
| Precondition: ≥2 buckets present | — | step 2 | `len(get_rendered_bucket_names()) >= 2` | asserted *(satisfied read-only by 768 existing buckets)* |
| 1 Navigate to Artifacts | Artifacts page loads | step 1 | heading visible + ≥1 bucket row | asserted |
| 2 Bucket list displayed, ≥1 bucket | Bucket list visible | step 2 | rendered-rows count | asserted |
| 3 Move cursor away from the bucket list | No bucket highlighted | step 3 | all three targets `to_have_css("background-color", "rgba(0, 0, 0, 0)")` | asserted |
| 4 Move the cursor over the first bucket | Row background changes to indicate highlight | steps 4-5 | `not_to_have_css(..., default)` on `A` | asserted |
| 5 Verify the row is visually highlighted (background colour changes) | First bucket highlighted | step 5 | same, plus `B`/`C` still default | asserted |
| 6 Move the cursor to the next bucket | Cursor moves to the next bucket | step 6 | `hover_bucket_row(B)` (the action; its effect is asserted in step 7) | covered |
| 7 Previous bucket returns to default, new one highlighted | Only the current bucket is highlighted | step 7 | `A` default **and** `B` not-default **and** `C` default | asserted |
| 8 Repeat for several buckets — only the hovered one is highlighted | Single-highlight consistent across the list | step 8 | `C` not-default, `A` + `B` default (third row) | asserted |
| Expected Final State: only one highlighted at a time, highlight removed when the cursor moves away | — | steps 5, 7, 8, 9 | the assertions above + step 9's all-default | asserted |

### Axis 2 — Analyst additions
- **"Highlighted" is asserted as *not the default background*, and "default" as
  the exact `rgba(0, 0, 0, 0)`.** Bi-directional: the positive check alone would
  pass on any non-transparent colour a future regression introduced permanently,
  and the negative check alone would pass on a row that never highlights. The
  pair is what makes "changes on hover, reverts off hover" mean it.
- **The unhovered SIBLINGS are asserted on every hover, not just the hovered
  row.** The case's Step 7/8 claim is a *single-highlight invariant*; checking
  only the row under the cursor cannot see a second row stuck highlighted.
- **Target rows are chosen live as the first three non-selected, in-band rows**,
  never a literal name or index. The selected row's background supersedes hover
  (see § Preconditions), and a row scrolled out of the `overflow:auto` container
  cannot be hovered at all.
- **NOT asserted: the exact hover colour literal** — theme-dependent, see
  § Concrete Handles.
- **NOT asserted: the other hover-driven changes** the same style function makes
  (border-radius, border-bottom removal, the hover-only pin button, the dot-menu
  becoming `display:flex`). The case names the background colour; the dot-menu
  reveal is already ELITEA-1820's assertion.
- **NOT asserted: console errors.** `.agents/testing.md` § Unconfirmed records a
  confirmed recurring environmental console-500/404 flake class on this project;
  importing it into a pure hover test buys noise, not signal.

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| *(none)* | — | The test performs **no** substitution: no seeding, no `page.route`, no injected state, no `evaluate()`. Every asserted value is the `background-color` the product computed in response to real `mousemove`/`mouseenter`/`mouseleave` events dispatched by the browser. The ≥2-bucket precondition is met by buckets that already exist. |

## Blocked Steps
None.

## Findings
- **Case-text nuance (not a defect): "the first bucket in the list" is a trap on
  a fresh `/artifacts` load.** The page auto-selects a bucket, and the selected
  row's `conversation.selected` background wins over the hover branch — so a
  tester (or a test) hovering the literal first row sees *no* background change
  and could file a false "hover highlight broken" bug. Live-measured: selected
  row `aa` stayed `rgba(41, 184, 245, 0.15)` while hovered. Filed as a
  clarification (see the run's findings) so the TMS case says "the first bucket
  that is not the currently selected one".

## Live-execution evidence (2026-08-21, localhost:5173, project Private/399)
Every step below was executed live, in order, and observed:
- 768 bucket rows rendered; row 1 (`aa`) `data-selected="true"`,
  `background-color: rgba(41, 184, 245, 0.15)` (`conversation.selected`, blue15);
  rows 2+ `data-selected="false"`, `rgba(0, 0, 0, 0)`.
- Cursor parked right of the panel (`x = panel.x + panel.width + 400`): targets
  `attach`, `attachments`, `autotest-1857-1858-1862-1785718023` all
  `rgba(0, 0, 0, 0)` — no highlight (case Step 3 ✓).
- Hover `attach` → `rgba(255, 255, 255, 0.06)`; the other two `rgba(0, 0, 0, 0)`
  (Steps 4-5 ✓).
- Hover `attachments` → it becomes `rgba(255, 255, 255, 0.06)`, `attach` reverts
  to `rgba(0, 0, 0, 0)`, third row untouched (Steps 6-7 ✓).
- Hover the third row → same pattern, first two both back to `rgba(0, 0, 0, 0)`
  (Step 8 ✓).
- Cursor away again → all three `rgba(0, 0, 0, 0)` (Expected Final State ✓).
- **No product defect found in any of the 8 steps.** Hover is React state
  (`BucketItem.jsx`'s `isHovering`, `onMouseEnter`/`onMouseLeave`), not a CSS
  `:hover` rule, which is why a real pointer move is required — and why the
  single-highlight invariant is structural (one `isHovering` flag per row,
  cleared by `onMouseLeave`).
