# Test Case: Cancel During Artifact Toolkit Creation Does Not Create Toolkit or Bucket

## Metadata
- **TMS ID**: ELITEA-1868
- **Linked Story**: [EliteaAI/elitea-testing-public#236](https://github.com/EliteaAI/elitea-testing-public/issues/236) (tracking issue)
- **Priority**: l3 (medium — as authored in the source TMS case frontmatter, `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch →
  DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399, freshly synced against
  `origin/main` this session via `git fetch origin` — see § Concrete Handles for per-testid
  provenance).
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **defect-found** — case executed end-to-end live, TWICE (the second run using
  only native Playwright locator/role clicks — no `page.evaluate()` / JS-dispatched clicks —
  specifically to rule out a synthetic-input artifact per the interaction-hygiene guard; both
  runs reproduced identically). A real, reproducible product defect was found and filed
  ([#655](https://github.com/EliteaAI/elitea-testing-public/issues/655)): confirming "Cancel"
  on the New Artifact Toolkit form does **not** navigate back to the Toolkits list as the
  case's steps 11/12 require — it falls back to the "Choose the toolkit type" screen at the
  SAME URL instead. This is an **isolated** defect, not a blocking one: the case's actual
  namesake objective — "does NOT create a toolkit or a bucket" — holds true and was verified
  two independent ways (UI search returning 0 results AND the full network log showing no
  `POST` to the toolkit-create endpoint ever fires on the Cancel path). Per this project's
  merge-gate "Sanctioned-RED exception" (`.agents/testing.md` § Merge gate), **recommend the
  implementer proceed with automation using `expect.soft()` + `# Known defect: #655`** for the
  one affected assertion (the post-cancel URL/screen) rather than pausing the whole case — see
  § Automation Hints. A second, unrelated MINOR defect
  ([#656](https://github.com/EliteaAI/elitea-testing-public/issues/656) — a React "unique key
  prop" console warning that fires on every load of the type-picker screen, filed separately
  per strict-per-bug policy) was also found; it does not affect this case's own assertions and
  is not gating automation.
  Three genuine testid gaps were found (the Cancel button, its confirmation dialog, and the
  dialog's confirm/"Discard" button — see § Concrete Handles) — all specced as `testid needed:`
  per `.agents/role-overrides.md` § Analyst slot (NOT self-fixed this run — that section
  reserves testid additions for the implementer slot). Not `already-covered` / not
  `extend-existing` — see § Overlap check below.

## Overlap check vs existing automation

`automation/pages/toolkit_detail_page.py` (read in full, 408 lines) was read before this run —
it covers an EXISTING toolkit's detail/config view (credential-status indicators, Save/Discard
on an already-created toolkit) and has no methods for the creation wizard's type-picker or the
"New Artifact Toolkit" form; it is not the right base class for this case (a facade/sibling
`toolkit_creation_page.py` is the correct shape — see § Automation Hints). No
`toolkits_list_page.py` or `toolkit_creation_page.py`/`toolkit_form_page.py` currently exists in
`automation/pages/` at all (`ls automation/pages/` confirmed only `toolkit_detail_page.py` for
the whole toolkits surface).

`automation/tests/ui/toolkits/test_toolkit_parameterized.py` (the only existing test that
touches `/toolkits/create`) was also read: its `toolkit_config` fixture navigates DIRECTLY to
`{base_url}/toolkits/create/{toolkit_id}` (a pre-selected type via URL, bypassing the
type-picker UI entirely) and only asserts `"/toolkits/create" not in page.url` after a
**successful save** of a toolkit that has a working credential (GitHub, Jira, etc. — real
external tokens required, tests auto-skip without them). It never touches the "Choose the
toolkit type" search/click flow, never touches the Artifact toolkit type, and never touches
Cancel at all.

`test_github_toolkit.py`, `test_mcp_*.py`, `test_credential_*.py` were also grepped — none
reference `toolkits/create`, `CreateToolkit`, `toolkit-type-card`, "New Toolkit", or "New
Artifact Toolkit".

Verdict: **zero behavioral overlap** — the type-picker search/filter flow, the Artifact
toolkit's specific form fields (Bucket), and the entire Cancel/confirm-dialog/no-creation path
are all fresh scenarios. `defect-found` (see § Status above for why this is not `blocked`).

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- No pre-existing toolkit named `cancelled-toolkit` or bucket named `cancelled-bucket` (this
  run confirmed both absent at the start: Toolkits list showed 11 toolkits total, Artifacts
  showed 208 buckets total, neither list contained anything matching "cancelled").

## Test Data

### generate-per-test (literal strings, not placeholders)
- **Toolkit name to enter**: `cancelled-toolkit` — confirmed live this IS the case's own
  literal test-data value (its own Test Data table names it explicitly), not a placeholder
  like the `bucket-1`/`autotest-*` convention seen in sibling artifact cases. Safe to reuse
  verbatim since the whole point of the test is that it must NEVER actually get created — no
  collision risk across parallel runs because nothing persists.
- **Bucket name to enter**: `cancelled-bucket` — same reasoning, literal case value.

No `reuse-existing` or `generate-shared-with-cleanup` data applies — this case creates nothing
that outlives the test.

## Test Steps

1. Navigate to the Toolkits section (case step 1). Case says "in the left sidebar" — confirmed
   live the sidebar "Toolkits" nav item has NO testid (`SidebarBody.jsx`/`SidebarMenuItem.jsx`
   shared component, same pre-existing gap already documented and left out-of-scope in
   ELITEA-1809's Implementer Amendments — broad shared-component change, disproportionate to
   one click). Implement via direct URL navigation to `${BASE_URL}/toolkits/all`, the same
   observable the case's own step 1 expects (Toolkits list page displayed).
   - **Verify**: page shows the Toolkits list (existing toolkit cards visible, `entity-card`
     testid present).
2. Click `sidebar-create-button` ("+ Toolkit") (case step 2).
   - **Verify**: URL becomes `${BASE_URL}/toolkits/create?viewMode=owner`.
3. Verify the "New Toolkit" wizard opens with "Choose the toolkit type" heading (case step 3).
   - **Verify**: URL contains `/toolkits/create` (testid-free, URL-based — always compliant)
     AND the tab-panel labelled "New Toolkit" is visible. The literal "Choose the toolkit
     type" heading text has NO testid anywhere in the component tree down to
     `GroupedCategory.jsx`/`Filter.CategoryFilter` — requires
     `testid needed: toolkit-wizard-type-picker-heading` (see § Concrete Handles) if the
     implementer wants a DOM-level assertion beyond the URL check; the URL check alone already
     satisfies this step's observable.
4. Type `"art"` into the "Search toolkits" field (case step 4).
   - **Verify**: input reflects `"art"`. Requires
     `testid needed: toolkit-wizard-type-search-input` (no testid found on this field in
     `ToolkitTypeSelector.jsx`/`Filter.CategoryFilter` — confirmed live via
     `document.querySelectorAll('input[data-testid]')` returning nothing for this field).
5. Verify only the "Artifact" toolkit is displayed under "STORAGE" (case step 5).
   - **Verify**: `[data-testid="toolkit-type-card-artifact"]` visible AND is the only card
     rendered under the "Storage" category section (confirmed live: filtering to "art" leaves
     exactly one category, "Storage", with exactly one card, "Artifact").
6. Click the "Artifact" toolkit card (case step 6).
   - **Verify**: `[data-testid="toolkit-type-card-artifact"]` click navigates URL to
     `${BASE_URL}/toolkits/create/artifact?viewMode=owner`. **Implementation note (both
     exploration runs)**: a text-based Playwright locator
     (`page.locator('div').filter({ hasText: /^Artifact$/ }).first()`) resolved to the WRONG
     ancestor `<div>` (a non-interactive wrapper) and silently no-op'd — always target this
     card via `[data-testid="toolkit-type-card-artifact"]` directly, never by matching on the
     visible "Artifact" text.
7. Verify the "New Artifact Toolkit" configuration form opens (case step 7).
   - **Verify**: tab-panel labelled "New Artifact Toolkit" visible; `toolkit-form-name-input`,
     `toolkit-field-bucket-input`, `toolkit-form-save-button` all visible.
8. Enter `"cancelled-toolkit"` into `toolkit-form-name-input` (case step 8).
   - **Verify**: field value == `"cancelled-toolkit"`. MUI field — use `click()` +
     `press_sequentially()` (confirmed live: `fill()`-equivalent alone does not reliably flip
     `formik.dirty`, which gates the Save button's enabled state — see step 10).
9. Enter `"cancelled-bucket"` into `toolkit-field-bucket-input` (case step 9).
   - **Verify**: field value == `"cancelled-bucket"`. Same MUI click+type pattern as step 8.
10. Verify both Save and Cancel are visible and ACTIVE (case step 10).
    - **Verify**: `toolkit-form-save-button` visible AND enabled (confirmed live: disabled
      before any field is dirtied — `shouldDisableSave = isLoading || !formik.dirty` in
      `CreateToolkitToolTabBar.jsx` — becomes enabled only after step 8/9 dirty the form); the
      Cancel button (see § Concrete Handles for its testid gap) visible AND enabled.
11. Click Cancel (case step 11) — **this is a TWO-CLICK sequence in the live product; the case
    text under-specifies it** (interaction-discovery ladder: the case's literal step 11 text
    ("Click the Cancel button") does not mention a confirmation dialog, but the live product
    always shows one — confirmed via source read of `DiscardButton.jsx`, which unconditionally
    opens a `Modal.BaseModal` on first click, before calling the caller's `onDiscard`).
    1. Click the Cancel button (top-right, next to Save).
       - **Verify**: a "Warning" dialog opens with text "Are you sure you want to cancel
         creation of this toolkit?" and two buttons, "Cancel" (dismiss) and "Discard"
         (confirm).
    2. Click "Discard" in that dialog.
12. Verify the form closes and the user is navigated back to the Toolkits list (case step 12).
    - **Verify — THIS IS WHERE THE DEFECT IS** (see § Known Defects): confirmed live, TWICE,
      that the URL stays at `${BASE_URL}/toolkits/create/artifact?viewMode=owner` and the
      screen falls back to the "Choose the toolkit type" picker instead of navigating to
      `${BASE_URL}/toolkits/all`. **Recommended automation shape**:
      `expect.soft(page.url).to_contain("/toolkits/all")  # Known defect: #655` — assert the
      CORRECT (case-mandated) behavior via soft-assert, not the buggy one, so the test stays
      red until the product fix ships (never assert the bug as if it were the spec).
13. Verify no toolkit named "cancelled-toolkit" appears in the toolkit list (case step 13).
    - **Verify**: navigate to `${BASE_URL}/toolkits/all` directly (works regardless of where
      step 12 actually landed — decouples this assertion from the step-12 defect), click
      `agent-search-input` (shared `SearchBar.jsx` component; this is its DEFAULT `testId` prop
      value and is what the Toolkits list actually renders — confirmed live via DOM inspection,
      NOT a naming mismatch), type `"cancelled-toolkit"`.
    - **Verify (primary, DOM-count, same technique ELITEA-1809 established as more robust than
      eyeballing)**: `page.locator('[data-testid="entity-card"]').count() == 0` after the
      search settles.
    - **Verify (secondary, case-mandated)**: the "No toolkits yet" empty-state message is
      shown (confirmed live: `customEmptyState`/`EmptyStatePage` renders when the filtered list
      is empty).
14. Navigate to the Artifacts section in the left sidebar (case step 14). Same sidebar-testid
    gap as step 1 — implement via direct navigation to `${BASE_URL}/artifacts`.
    - **Verify**: `artifacts-buckets-heading` visible (existing testid, reused from
      ELITEA-1808/1809's `ArtifactsPage.wait_for_page_load()`).
15. Click the search icon in the "BUCKETS" header (case step 15).
    - **Verify**: `artifacts-search-buckets-button` click reveals `artifacts-bucket-search-input`
      (BOTH existing testids — `artifacts-search-buckets-button` is on `main`;
      `artifacts-bucket-search-input` was added by the ELITEA-1809 implementer round and is
      confirmed still present this run, on `automation/testids` — see § Concrete Handles).
16. Type `"cancelled"` into the search field (case step 16).
    - **Verify**: input reflects `"cancelled"`.
17. Verify no bucket named "cancelled-bucket" appears in the filtered results (case step 17).
    - **Verify (primary, DOM-count)**:
      `page.locator('[data-testid="artifacts-bucket-row-cancelled-bucket"]').count() == 0`
      (reuses the existing `BUCKET_ROW` dynamic-testid template already in
      `artifacts_page.py` from ELITEA-1808/1809 — no new handle needed).
    - **Verify (secondary, case-mandated)**: "No buckets found" empty-state message shown
      (confirmed live via `BucketsPanel.jsx`'s search-empty state).
18. Verify the bucket was not created as a result of the cancelled toolkit creation (case step
    18 — same observable as step 17; case's own text splits "verify filtered results" vs.
    "verify not created" into two steps, folded here since both step-17 checks already satisfy
    it).
    - **Verify (additional, network-level — see § Network Behavior)**: across the FULL
      exploration session (both runs, steps 1–13), no `POST` request to the toolkit-create
      endpoint (`/api/v2/elitea_core/tools/...`) or the bucket-create endpoint
      (`/api/v2/artifacts/buckets/default/...`) was ever observed — the strongest possible
      proof that Cancel genuinely aborts before any mutating call, not merely that the UI
      doesn't render the result.

## Expected Results
- The type-picker search/filter narrows correctly to the Artifact card under "Storage".
- The "New Artifact Toolkit" form accepts Toolkit Name and Bucket input, enables Save once
  dirty.
- Cancel → confirm ("Discard") aborts creation with ZERO network mutation (confirmed:
  no `POST` fires) and creates neither a toolkit nor a bucket (confirmed via UI search on both
  the Toolkits list and the Artifacts/Buckets panel).
- **KNOWN DEFECT (#655)**: Cancel → Discard does NOT navigate back to the Toolkits list — it
  falls back to the type-picker screen at the same `/toolkits/create/artifact` URL.
- No application-level console errors during the flow. One unrelated pre-existing MINOR console
  warning was observed and filed separately (#656 — see § Known Defects); it is not part of
  this case's own pass/fail criteria.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Objective: Cancel does not create toolkit or bucket | No mutation occurs | Steps 13, 17, 18 | UI search (0 results) + network log (no POST) | asserted |
| Precondition: user logged in | Session valid | Preconditions | `auth_state` fixture (skips login on localhost) | asserted |
| Test Data: Toolkit name = cancelled-toolkit | Literal value entered | Step 8 | `toolkit-form-name-input` value check | asserted |
| Test Data: Bucket name = cancelled-bucket | Literal value entered | Step 9 | `toolkit-field-bucket-input` value check | asserted |
| Step 1: Navigate to Toolkits (sidebar) | Toolkits list displayed | Step 1 | direct nav to `/toolkits/all`, `entity-card` visible | asserted *(sidebar has no testid — pre-existing, out-of-scope gap; same mechanism-substitution precedent as ELITEA-1809)* |
| Step 2: Click "+ Toolkit" | "New Toolkit" page opens | Step 2 | URL becomes `/toolkits/create` | asserted |
| Step 3: Verify "Choose the toolkit type" heading | Page title correct | Step 3 | URL check (testid-free) | asserted *(DOM-level heading text requires `testid needed: toolkit-wizard-type-picker-heading` for a stronger check — optional, URL already satisfies the observable)* |
| Step 4: Type "art" in search | Filter applied | Step 4 | search input value | asserted *(requires `testid needed: toolkit-wizard-type-search-input`)* |
| Step 5: Verify only Artifact shown under STORAGE | Filter correct | Step 5 | `toolkit-type-card-artifact` sole visible card | asserted |
| Step 6: Click Artifact card | "New Artifact Toolkit" form opens | Step 6 | URL becomes `/toolkits/create/artifact` | asserted |
| Step 7: Verify New Artifact Toolkit form opens | Form visible | Step 7 | 3 testid visibility checks | asserted |
| Step 8: Enter Toolkit Name | Name field shows value | Step 8 | `toolkit-form-name-input` value | asserted |
| Step 9: Enter Bucket name | Bucket field shows value | Step 9 | `toolkit-field-bucket-input` value | asserted |
| Step 10: Verify Save/Cancel visible + active | Both buttons present, enabled | Step 10 | `toolkit-form-save-button` enabled + Cancel button enabled | asserted *(Cancel button requires `testid needed: toolkit-form-cancel-button`)* |
| Step 11: Click Cancel | Form closes, navigates to Toolkits list | Steps 11 (decomposed into 11.1/11.2), 12 | Cancel click → confirm dialog → Discard click | asserted *(decomposed — case's single click is a two-click confirm flow in the live product)* |
| Step 12: Verify navigated to Toolkits list | Toolkits list page shown | Step 12 | `page.url` check | **KNOWN DEFECT — #655, see § Known Defects** |
| Step 13: Verify no "cancelled-toolkit" in toolkit list | Toolkit absent | Step 13 | `entity-card` count == 0 after search (primary) + empty-state text (secondary) | asserted |
| Step 14: Navigate to Artifacts (sidebar) | Artifacts page loads | Step 14 | direct nav to `/artifacts`, `artifacts-buckets-heading` visible | asserted *(same sidebar-testid gap as step 1)* |
| Step 15: Click search icon in BUCKETS header | Search field opens | Step 15 | `artifacts-search-buckets-button` → `artifacts-bucket-search-input` visible | asserted |
| Step 16: Type "cancelled" | Bucket list filters | Step 16 | search input value | asserted |
| Step 17: Verify no "cancelled-bucket" in filtered results | Bucket absent | Step 17 | `artifacts-bucket-row-cancelled-bucket` count == 0 (primary) + empty-state text (secondary) | asserted |
| Step 18: Verify bucket not created | No bucket created | Step 18 | network-level: no POST to bucket-create endpoint across the whole session | asserted |
| Expected Final State: no toolkit, no bucket created; user returned to Toolkits list | Composite pass condition | Steps 12, 13, 17, 18 | combination of the above | **partially asserted — the "returned to Toolkits list" clause is the known defect (#655)** |
| Pass criterion: "All steps complete without errors" | No unexpected errors | All steps | console-error check (0 application-level errors; 1 unrelated pre-existing MINOR warning filed as #656) | asserted |

### Axis 2 — Observables asserted beyond the case
- **Network-level proof of zero mutation** (no `POST` to the toolkit-create or bucket-create
  endpoints across the entire session) as an ADDITIONAL signal beyond the UI-search checks the
  case itself asks for — *added: strongest possible proof that Cancel aborts before any
  server-side effect, not just that the UI doesn't render a result; also directly supports the
  root-cause note in the filed defect (#655) that the Cancel path never calls the create API at
  all.*
- **Two independent full exploration runs, the second using ONLY native Playwright
  locator/role clicks (no `page.evaluate()`)** — *added: the first run's toolkit-type-card
  click used a JS-evaluated click as a workaround for a bad text-based locator; per the
  Synthetic Input Hygiene guard, the defect finding (step 12) was re-verified from a pristine
  page load using exclusively real dedicated-tool clicks before being classified and filed,
  ruling out a synthetic-input artifact.*
- **DOM-count-based negative-result checks** (`entity-card` count == 0,
  `artifacts-bucket-row-{name}` count == 0) as the PRIMARY proof for steps 13/17, with the
  case's own "empty-state message shown" as a secondary/redundant check — *added: same
  technique ELITEA-1809 established as more robust than eyeballing a filtered list.*

## Cleanup
1. Nothing to clean up — the case's entire premise is that Cancel creates neither a toolkit nor
   a bucket, and this was confirmed at both the UI and network level; there is no orphaned
   resource from either exploration run.
2. Local exploration screenshots (repo root, untracked; also uploaded to the evidence release
   and embedded in the filed defects): `ELITEA-1868-step1-toolkits-list.png`,
   `ELITEA-1868-debug-artifact-card.png`,
   `ELITEA-1868-step8-9-10-form-filled-save-cancel-active.png`,
   `ELITEA-1868-step11-cancel-confirmation-dialog.png`,
   `ELITEA-1868-BUG-cancel-does-not-navigate-to-toolkits-list.png` — safe to leave per this
   repo's existing pattern of untracked case-evidence screenshots at repo root.

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator policy
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`) is **testid-only, no
fallback ladder** — `LocatorDescriptor(testid=...)` with no `fallback=`/`locator=`. Per the
currently-authoritative Analyst-slot rule, the genuine gaps below are specced as
`testid needed:` work orders for the **implementer** to add via `add-data-testid` — **not**
self-fixed by this analyst pass.

**Provenance verified freshly this run**: `cd ../EliteaUI && git fetch origin` run immediately
before checking (branch `automation/testids` tracking `origin/automation/testids` cleanly),
then `git grep` run against both `origin/main` and `origin/automation/testids` for every
testid below (both literal-string and template forms, since several of these are computed via
template literals, not hardcoded strings — grepping only the computed value silently
undercounts).

| Element | testid | Status | Provenance | Notes |
|---|---|---|---|---|
| "+ Toolkit" sidebar button | `sidebar-create-button` | existing (shared) | **on-main ✓** | generic create-button, shared across list pages |
| Toolkits list search input | `agent-search-input` | existing (shared, DEFAULT prop) | **on-main ✓** | `SearchBar.jsx`'s default `testId` prop value; confirmed live this IS what renders on the Toolkits list (no override passed at the Toolkits call site) |
| Toolkit list card (generic) | `entity-card` | existing (shared) | **on-main ✓** | `CardList`/`Card.jsx`; used as the DOM-count proof for step 13 |
| Toolkit type card (dynamic) | `[data-testid="toolkit-type-card-{itemKey}"]` template | existing | **on-automation/testids only** (awaiting human promotion to main) | `CategoryItemCard.jsx` — generic template parameterized by item key, NOT hardcoded to "artifact"; compliant with the shared-component testid ruling |
| Toolkit Name input | `toolkit-form-name-input` | existing | **on-automation/testids only** | `NameDescriptionInput.jsx` — generic (shared across ALL toolkit types), not artifact-specific |
| Bucket field (dynamic) | `[data-testid="toolkit-field-{k}-input"]` template | existing | **on-automation/testids only** | `ToolBaseProperty.jsx` — generic template parameterized by the toolkit's schema property key (`k`, here literally `bucket`); this is the SAME mechanism every schema-driven toolkit field uses, fully compliant with the shared-component ruling |
| Save button | `toolkit-form-save-button` | existing | **on-automation/testids only** | `CreateToolkitToolTabBar.jsx` — shared across all toolkit/MCP/application creation |
| **Cancel button (trigger)** | `toolkit-form-cancel-button` | **testid needed** | n/a | `CreateToolkitToolTabBar.jsx`'s `<Button.DiscardButton title="Cancel" onDiscard={onCancel} .../>` call passes NO `dataTestId` prop, though `DiscardButton.jsx` already accepts one — trivial one-line wiring, same component shared across all toolkit/MCP/application types (not artifact-specific) |
| **Cancel confirmation dialog** | `toolkit-form-cancel-confirm-dialog` | **testid needed** | n/a | Same call site — `DiscardButton.jsx` accepts a `modalDataTestId` prop, also unwired |
| **Cancel confirmation "Discard" button** | `toolkit-form-cancel-confirm-button` | **testid needed** | n/a | Same call site — `DiscardButton.jsx` accepts a `confirmButtonDataTestId` prop, also unwired |
| "Choose the toolkit type" heading | `toolkit-wizard-type-picker-heading` | **testid needed** (optional — URL check already satisfies the case's observable) | n/a | `GroupedCategory.jsx` → `Filter.CategoryFilter`; no testid anywhere in this chain |
| Toolkit type search input | `toolkit-wizard-type-search-input` | **testid needed** | n/a | rendered inside `Filter.CategoryFilter`; no testid found |
| Artifacts buckets heading | `artifacts-buckets-heading` | existing (ELITEA-1808) | **on-automation/testids only** | reused from `ArtifactsPage` |
| Search buckets button | `artifacts-search-buckets-button` | existing | **on-main ✓** | reused from `ArtifactsPage` (ELITEA-1809) |
| Bucket search input | `artifacts-bucket-search-input` | existing (ELITEA-1809 implementer round) | **on-automation/testids only** | confirmed still present this run |
| Bucket row (dynamic) | `[data-testid="artifacts-bucket-row-{name}"]` template | existing (ELITEA-1808) | **on-automation/testids only** | already a class constant (`BUCKET_ROW`) in `artifacts_page.py` |

## Network Behavior
- **No mutating request fires on the Cancel path.** Across both full exploration runs (every
  request from initial navigation through the final Discard click), the network log contains
  ONLY: `socket.io` polling, `support_assistant` config/conversation GETs, and read-only GETs
  for toolkit-type schemas / model configurations (`/api/v2/configurations/models/...`,
  `/api/v2/configurations/available/...` — fired when the Artifact card is selected, because
  the Artifact schema has `pgvector_configuration`/embedding-model properties that trigger a
  configuration-loading branch in `ToolkitTypeSelector.jsx`'s `onAddTool`). **No `POST`** to
  `/api/v2/elitea_core/tools/...` (toolkit create) or `/api/v2/artifacts/buckets/default/...`
  (bucket create) is ever observed — confirms the root cause in #655: the Cancel path never
  reaches the save/create call at all, it only resets local component state.

## Known Defects Found During Exploration

- **[MAJOR] Cancel does not navigate back to the Toolkits list** — filed as
  [#655](https://github.com/EliteaAI/elitea-testing-public/issues/655). Root cause (read live,
  `EliteaAI/EliteaUI` `automation/testids`): `src/pages/Toolkits/CreateToolkitToolTabBar.jsx`'s
  `onCancel`/`wantToCancel` effect only calls `onClearEditTool()` (→ `setEditToolDetail(null)`
  in `CreateToolkit.jsx`) + `formik.resetForm()` — neither, nor anything else on the confirm
  path, calls `navigate()`. Clearing `editToolDetail` just makes `CreateToolkit.jsx` fall back
  to rendering `<ToolkitTypeSelector>` again at the SAME URL, instead of routing to
  `RouteDefinitions.ToolkitsWithTab` (the pattern the Save-success path already uses in
  `onSaveEvent`, a few lines below in the same file). Reproduced 2/2, the second run
  pristine-context/native-input-only. Automation: `expect.soft()` +
  `# Known defect: #655` on the post-cancel URL check (step 12) — isolated, does not block the
  rest of the case.
- **[MINOR] React "unique key prop" console warning on the type-picker screen** — filed as
  [#656](https://github.com/EliteaAI/elitea-testing-public/issues/656), unrelated to this
  case's own pass/fail criteria (fires on every load of `/toolkits/create`, independent of
  anything this case's steps do). Not gating automation; do not assert on it either way unless
  a future case specifically targets `CategorySection.jsx`'s list-key hygiene.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- **New page objects needed** — `automation/pages/` currently has no coverage of the Toolkits
  list or the creation wizard at all:
  1. `automation/pages/toolkits_list_page.py` — mirror the shape of
     `automation/pages/agents_list_page.py`/`mcp_list_page.py` (both already exist and use the
     SAME shared `agent-search-input`/`entity-card` testids this case needs — reuse their
     `search()` pattern, don't reinvent). Needs: `sidebar_create_button`
     (`sidebar-create-button`), `search_input` (`agent-search-input`), a
     `count_visible_cards() -> int` thin wrapper around `[data-testid="entity-card"]`.
  2. `automation/pages/toolkit_creation_page.py` (new — do NOT extend
     `ToolkitDetailPage`, which is model for an EXISTING toolkit's detail view and shares no
     real behavior with the creation wizard). Needs:
     - `TOOLKIT_TYPE_CARD` template = `[data-testid="toolkit-type-card-{}"]`.
     - `TOOLKIT_FIELD_INPUT` template = `[data-testid="toolkit-field-{}-input"]` (for `bucket`
       and any future schema-driven field).
     - `name_input` (`toolkit-form-name-input`), `save_button` (`toolkit-form-save-button`),
       `cancel_button` (`toolkit-form-cancel-button`, once added),
       `cancel_confirm_button` (`toolkit-form-cancel-confirm-button`, once added).
     - `select_toolkit_type(type_search_term: str, type_key: str)` — types into the (once
       added) `toolkit-wizard-type-search-input`, clicks `TOOLKIT_TYPE_CARD.format(type_key)`.
     - `cancel_creation()` — clicks Cancel, waits for the confirm dialog
       (`toolkit-form-cancel-confirm-dialog`, once added), clicks
       `toolkit-form-cancel-confirm-button`. Returns nothing — the caller asserts the
       post-cancel URL with `expect.soft()` per the known-defect note above.
- **MUI field caveat** (same as every other toolkit/artifact form in this codebase): use
  `click()` + `press_sequentially()` for `toolkit-form-name-input` /
  `toolkit-field-bucket-input` — plain `fill()` does not reliably flip `formik.dirty`, which
  gates the Save button's enabled state (step 10's assertion would otherwise race).
- **Card-click gotcha** (both exploration runs hit this): do NOT locate the Artifact type card
  via a text-matching locator (`page.locator('div').filter({ hasText: /^Artifact$/ })`) — it
  resolves to a non-interactive wrapper `<div>` in this component tree and silently no-ops.
  Always target `[data-testid="toolkit-type-card-artifact"]` directly.
- Wait strategy: after clicking `toolkit-type-card-artifact`, the Artifact schema's
  vectorstorage/embedding-model config GETs fire in the background (see § Network Behavior) —
  wait for `toolkit-form-name-input`/`toolkit-field-bucket-input` to be visible (they render
  immediately, independent of those background GETs) rather than for network-idle, which may
  lag behind the form's actual readiness.
- Test isolation: this case creates nothing, so no fixture/teardown is needed for the toolkit
  or bucket side — but DO still assert step 13/17's negative-result checks against a
  KNOWN BASELINE count captured at test start (not a hardcoded absolute count), since other
  parallel/serial tests' `autotest-*` toolkits and buckets accumulate in this shared
  environment (same caveat every sibling artifact AFS documents).
