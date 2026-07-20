# Test Case: Create Artifact Bucket via Artifact Toolkit Creation and Verify via List Files Tool

## Metadata
- **TMS ID**: ELITEA-1866
- **Linked Story**: [EliteaAI/elitea-testing-public#257](https://github.com/EliteaAI/elitea-testing-public/issues/257) (tracking issue)
- **Priority**: l2 (high — as authored in the source TMS case frontmatter, `priority: high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch →
  DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399, freshly synced against
  `origin/main` and `origin/automation/testids` this session via `git fetch origin` — see
  § Concrete Handles for per-testid provenance).
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live, all 39 steps + the
  Preconditions/Test Data rows verified against the real system (Playwright MCP). The core
  flow (create Artifact toolkit → bucket created as a side effect → List files tool runs →
  bucket visible+empty in Artifacts) works correctly with **zero product defects on the
  primary path**. Two findings were filed, neither blocking:
  - [#669](https://github.com/EliteaAI/elitea-testing-public/issues/669)
    **[CLARIFICATION]** — case step 15 says "Click the info (i) icon" next to the Bucket
    field; the live product's tooltip (`InfoTooltip.jsx`, a plain MUI `Tooltip`) activates
    on **hover**, not click — confirmed via source read (decisive step of the
    interaction-discovery ladder). Content is correct either way. Not a defect — the AFS
    specs `.hover()`.
  - A root-cause **comment** added to the pre-existing, OPEN
    [#636](https://github.com/EliteaAI/elitea-testing-public/issues/636) ("Artifact bucket
    cleanup fails silently — delete returns 404") — discovered while verifying this case's
    own cleanup: the UI's bucket-delete call is query-param shaped
    (`DELETE .../buckets/default/{project_id}?name={bucket}` → confirmed live, 200 OK) while
    `automation/api/client.py`'s `ArtifactAPI.delete_bucket()` sends a path-segment shape
    (`.../buckets/default/{project_id}/{bucket}` → 404s, per #636). This is directly relevant
    to § Cleanup below: **do not use `ArtifactAPI.delete_bucket()` for this test's teardown**
    until #636 is fixed — use the UI dot-menu Delete flow instead (proven working live, see
    § Cleanup). Toolkit deletion has no equivalent defect — `ArtifactAPI`'s sibling
    `_toolkits_url()`/`delete_toolkit()` shape matches the UI's own call exactly (both hit
    `elitea_core/tool/prompt_lib/{project_id}/{toolkit_id}`, confirmed live with a clean
    `204 No Content`) and is safe to use for teardown.
  - One pre-existing, already-filed, non-blocking console warning was observed on every load
    of the type-picker screen — [#656](https://github.com/EliteaAI/elitea-testing-public/issues/656)
    (React "unique key prop" in `CategorySection.jsx`), filed by the ELITEA-1868 analyst pass.
    Not re-filed; not gating. No other console errors were observed across the entire 39-step
    run (multiple explicit console checks — see § Coverage Map Axis 2).
  - See § Known Defects below for full detail on both findings.

## Overlap check vs existing automation

`automation/toolkit_configs.py` (the credential-gated config set `test_toolkit_parameterized.py`
parametrizes over) has **no `artifact` entry** — confirmed by inspection before this run — so no
existing automated test creates an Artifact toolkit via the Save path and runs a tool against it.
This case is genuinely fresh on that half.

The type-picker search/filter flow, the Artifact toolkit's form fields (Name, Bucket), and the
post-save toolkit-detail navigation are ALREADY covered by page objects added for the sibling case
ELITEA-1868 (`test-specs/artifacts/l3_cancel-artifact-toolkit-creation-no-toolkit-no-bucket_ELITEA-1868.md`)
— that case's implementer created `automation/pages/toolkits_list_page.py` and
`automation/pages/toolkit_creation_page.py`, which this AFS extends rather than duplicates (see
§ Automation Hints). ELITEA-1868 itself only exercises the **Cancel** path (asserts nothing is
created); this case exercises the **Save** path and the entirely-new TEST SETTINGS/RUN TOOL
surface, so there is no behavioral overlap between the two cases' own assertions — confirmed by
reading the ELITEA-1868 AFS in full before this run, per the task's sibling-context brief.

`automation/pages/toolkit_detail_page.py` (read in full, 408 lines) covers an EXISTING toolkit's
detail/config view (credential-status indicators, Save/Discard on an already-created toolkit) and
has NO methods for the creation wizard OR the TEST SETTINGS tool-run panel — confirmed by grep
(`Test Settings`, `RUN TOOL`, `toolkit-test-`: zero matches in this file). **Decision: a new page
object, `automation/pages/toolkit_test_settings_page.py`, is warranted** for the TEST SETTINGS
panel (steps 25-31) rather than extending `ToolkitDetailPage` — the TEST SETTINGS panel is a
sibling region of the SAME `/toolkits/all/{id}` page, not a variant of the Configuration form
`ToolkitDetailPage` already models, and its testids (`toolkit-test-*`) form their own distinct,
self-consistent namespace. `toolkit-detail-title` (the header showing the toolkit name, steps
21-23) is a small addition that belongs on `ToolkitDetailPage` itself (it is that page's own
identity, not test-panel-specific) — see § Automation Hints for the exact method list.

Verdict: **zero behavioral overlap with any merged spec** — `ready-for-automation`, fresh
implementation, built on top of (not duplicating) the ELITEA-1868 page objects.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- No pre-existing toolkit named `my-artifact-toolkit` or bucket named `new-bucket`. **Confirmed
  live at the start of this run**: searching the Toolkits list for `my-artifact-toolkit` returned
  0 `entity-card` results; searching the Artifacts bucket panel for the *exact* testid
  `artifacts-bucket-row-new-bucket` returned false (a DIFFERENT, unrelated pre-existing bucket,
  `new-bucketautotest-buck1-800755`, substring-matches "new-bucket" in a bucket-count/search
  context — see § Test Data and § Known Defects/collision note below; it is not the same bucket
  and does not violate this precondition).

## Test Data

### generate-per-test, WITH mandatory pre-test AND post-test cleanup (collision-avoidance design — see rationale below)
- **Toolkit name to enter**: `my-artifact-toolkit` — literal value from the case's own Test Data
  table (not a placeholder). Unlike the sibling ELITEA-1868 case (which never persists anything
  because Cancel aborts before any mutating call), **this case's Save path DOES persist a real
  toolkit + bucket** — confirmed live via network log:
  `POST /api/v2/elitea_core/tools/prompt_lib/399 → 201 Created` (no separate bucket-create POST
  fires — the toolkit-create endpoint creates the bucket server-side as a side effect, matching
  the case's own objective text "creating an Artifact Toolkit... which also creates a bucket").
- **Bucket name to enter**: `new-bucket` — same reasoning, literal case value, created as a
  side effect of the toolkit-create POST above (no independent `create_bucket` call needed or
  observed).

**Collision-avoidance design decision (required by the task brief, not deferred to the
implementer):** the case's own Preconditions section requires these EXACT literal names be
ABSENT before the run — but literal, non-randomized names collide across repeat/CI runs unless
cleanup is both attempted AND made resilient to failure. Given the live-confirmed
`ArtifactAPI.delete_bucket()` defect (#636 — see § Status), pure "delete in teardown and trust
it" is not safe for the bucket half. The recommended pattern:

1. **Idempotent pre-test cleanup (fixture setup, before the test body runs).** Before asserting
   the Preconditions, the fixture best-effort deletes any pre-existing `my-artifact-toolkit`
   toolkit (via `ArtifactAPI.delete_toolkit(id)` — safe, matches the UI's own call shape, no
   known defect) and any pre-existing `new-bucket` bucket. For the bucket, do NOT call
   `ArtifactAPI.delete_bucket()` (broken per #636); instead drive the UI dot-menu Delete flow
   (`ArtifactsPage.open_bucket_menu("new-bucket")` → `click_bucket_menu_delete_item()` →
   `confirm_delete_bucket()`, all pre-existing ELITEA-1817 methods) if a stale bucket is found.
   Wrap both in try/except so a genuinely-clean environment (the common case) is a no-op, not a
   failure.
2. **Test body**: create fresh, assert per this AFS's 39 steps.
3. **Post-test cleanup (fixture teardown, `finally`/`yield`-based, runs even on assertion
   failure)**: delete the toolkit via `ArtifactAPI.delete_toolkit(toolkit_id)` (capture
   `toolkit_id` from the POST-save response body or the post-save URL's numeric segment,
   e.g. `/toolkits/all/1524` → `1524`) — this call is proven reliable (204 confirmed live).
   Delete the bucket via the SAME UI dot-menu Delete flow used in step 1 (NOT the broken API
   method) — proven live in this session: `DELETE .../buckets/default/399?name=new-bucket →
   200 OK`, bucket row disappeared from the list immediately after.
4. Do not fail the test itself if teardown's best-effort pre-clean finds nothing to delete (the
   normal case) — only surface a hard failure if teardown's OWN delete calls error unexpectedly
   (as opposed to 404/not-found, which just means "already absent").

This is NOT `reuse-existing`/durable fixture data — the case's Preconditions actively forbid that
(a persisted "my-artifact-toolkit"/"new-bucket" would fail precondition on every subsequent run).
It is `generate-per-test` with an explicit idempotent-pre-clean + defect-aware-post-clean shape,
which is the only design that satisfies both "the case demands these exact literal names" and
"repeat runs must not collide" simultaneously given #636's current state.

- **Tool to test**: `List files` — selected from the TEST SETTINGS panel's Tool dropdown by its
  schema key `list_files` (dynamic testid `select-option-list_files`).

## Test Steps

1. Navigate to the Toolkits section (case step 1). Same sidebar-testid gap the ELITEA-1868 AFS
   already documented (`SidebarBody.jsx`/`SidebarMenuItem.jsx` shared component, no testid).
   Implement via direct URL navigation to `${BASE_URL}/toolkits/all` — same observable the
   case's own step 1 expects.
   - **Verify**: page shows the Toolkits list (`sidebar-create-button` visible;
     `ToolkitsListPage.wait_for_page_load()`, existing ELITEA-1868 method).
2. Verify the Toolkits list page is displayed showing all existing toolkits with their types
   (case step 2).
   - **Verify**: at least one `entity-card` is present (this project has pre-existing toolkits
     from other automated cases — confirmed live: 6+ `Artifact`-typed cards visible on load).
     This is a non-empty-state smoke check, not a count assertion (the exact count varies run
     to run as other suites create/delete their own toolkits).
3. Click the "+ Toolkit" button (case step 3).
   - **Verify**: URL becomes `${BASE_URL}/toolkits/create?viewMode=owner`
     (`ToolkitsListPage.click_create_toolkit()`, existing ELITEA-1868 method).
4. Verify the "New Toolkit" page opens with the heading "Choose the toolkit type" (case step 4).
   - **Verify**: URL contains `/toolkits/create` AND the literal heading text "Choose the toolkit
     type" is present (confirmed live via `document.querySelectorAll` text-match — the heading
     itself still has no testid, same gap the ELITEA-1868 AFS flagged as optional; the URL check
     alone already satisfies the case's observable, per that AFS's own reasoning, carried
     forward here — `testid needed: toolkit-wizard-type-picker-heading`, optional).
5. Verify a search input field is present with placeholder text "Search toolkits" (case step 5).
   - **Verify**: `toolkit-wizard-type-search-input` visible (existing ELITEA-1868 handle,
     `ToolkitCreationPage.type_search_input`). Confirmed live the accessible placeholder text
     "Search toolkits" matches the case's expectation exactly.
6. Verify category filter tabs are displayed (case step 6).
   - **Verify**: confirmed live 12 category tabs render as buttons: "Code Repositories",
     "Communication", "Development", "Documentation", "Integrations", "Mcp", "Office", "Other",
     "Project Management", "Storage", "Test Management", "Testing". No testids on the individual
     tab buttons (out of scope for this case — it never clicks a category tab, it uses the search
     field instead per steps 7-9); a simple `count >= 1` / text-match smoke check on the tab
     button group satisfies this step's observable without needing per-tab handles.
7. Type "art" in the search field (case step 7).
   - **Verify**: `toolkit-wizard-type-search-input` reflects `"art"`
     (`ToolkitCreationPage.search_toolkit_type("art")`, existing ELITEA-1868 method — client-side
     filter, no debounce/Enter needed, confirmed live again this run).
8. Verify the toolkit list filters and shows only the "Artifact" toolkit under the "STORAGE"
   section (case step 8).
   - **Verify**: `document.querySelectorAll('[data-testid^="toolkit-type-card-"]')` returns
     EXACTLY one element, `toolkit-type-card-artifact`, and it renders under a section whose
     visible category label is "Storage" (confirmed live).
9. Verify no other toolkit types are displayed (case step 9).
   - **Verify**: same DOM-count check as step 8 — `count === 1` is itself the proof no other
     type card is rendered (folded together with step 8's assertion; the case's own text splits
     "shows only Artifact" vs. "no other types" into two steps for the same single observable).
10. Click on the "Artifact" toolkit card (case step 10).
    - **Verify**: URL becomes `${BASE_URL}/toolkits/create/artifact?viewMode=owner`
      (`ToolkitCreationPage.select_toolkit_type("art", "artifact")`, existing ELITEA-1868
      method — **never locate this card by text-match**, per that AFS's documented gotcha; use
      `TOOLKIT_TYPE_CARD.format("artifact")` only).
11. Verify the form opens with "Form"/"Raw Json" tabs, "CONFIGURATION" section with Toolkit Name,
    Description, Pgvector Configuration, Embedding Model, and Bucket fields (case step 11).
    - **Verify**: tab-panel labelled "New Artifact Toolkit" visible; `toolkit-form-name-input`
      and `toolkit-field-{}-input`.format("bucket") both visible (existing ELITEA-1868 handles).
      "Form"/"Raw Json" toggle buttons present (accessible-name text match — no testid, out of
      scope: this case never switches to Raw Json view). Description/Pgvector
      Configuration/Embedding Model fields confirmed present by label text (Embedding Model
      defaults to `text-embedding-3-small`; Pgvector Configuration has no default selection).
12. Verify the "TOOLS" section shows all 16 available tools with checkmarks (case step 12).
    - **Verify (NEW handle, genuinely fresh surface — not touched by ELITEA-1868)**:
      `document.querySelectorAll('[data-testid^="toolkit-tool-chip-"]')` returns EXACTLY 16
      elements, and EVERY element's `data-selected` attribute equals `"true"` (confirmed live —
      each tool renders as an MUI `Chip` with an SVG checkmark icon when `data-selected="true"`,
      which IS the case's "with checkmarks" observable). The 16 confirmed tool keys:
      `append_data`, `create_file`, `create_new_bucket`, `delete_file`, `edit_file`,
      `get_file_metadata`, `grep_file`, `index_data`, `list_collections`, `list_files`,
      `read_file`, `read_multiple_files`, `remove_index`, `search_index`,
      `stepback_search_index`, `stepback_summary_index`. This is a compliant testid=stable-
      identity + `data-*`=state pattern per `.agents/testing.md` § Locator policy (PR #581
      ruling) — filter on `[data-selected="true"]`, never a state-toggled testid.
13. Verify a "Make tools available by MCP" checkbox (unchecked by default) (case step 13).
    - **Verify (NEW handle)**: `toolkit-field-available_by_mcp-checkbox-field` (the actual
      `<input type="checkbox">` — a SIBLING `-checkbox` testid also exists on the outer
      `<span>` wrapper, use the `-checkbox-field` one for `.is_checked()`/`.checked` reads, same
      "wrapper vs. actual input" gotcha the ELITEA-1824 AFS already documented for a different
      field) is present and `checked === false` (confirmed live). Same generic
      `toolkit-field-{k}-checkbox`/`-checkbox-field` template family as the Bucket field's
      `toolkit-field-{k}-input` (`k` here is literally `available_by_mcp`), so no new template
      constant is needed on top of `TOOLKIT_FIELD_INPUT` — see § Automation Hints for the
      checkbox-variant naming.
14. Verify "Save" and "Cancel" buttons in the top-right (case step 14).
    - **Verify**: `toolkit-form-save-button` and `toolkit-form-cancel-button` both visible
      (existing ELITEA-1868 handles). At this point (before any field is dirtied) Save is
      DISABLED (`shouldDisableSave = isLoading || !formik.dirty`, per the ELITEA-1868 AFS's
      documented root cause) and Cancel is enabled — confirmed live again this run.
15. Click the info (i) icon next to the "Bucket *" field (case step 15).
    - **KNOWN CLARIFICATION — see § Known Defects (#669)**: the case text says "click"; the live
      product's tooltip activates on **hover**, confirmed via source read of the shared
      `InfoTooltip.jsx` component (a plain MUI `Tooltip`, no `onClick` wired — hover/focus is the
      MUI default and the component's only wired trigger). **Verify** using `.hover()`, not
      `.click()`, on the info-icon element. **NEW handle (testid needed)**: the icon wrapper
      currently carries only a generic `data-info-tooltip` boolean attribute (not a testid, and
      NOT unique — the same form renders 3 of these on this page: Pgvector Configuration,
      Embedding Model, and Bucket each have one) — `testid needed:
      toolkit-field-bucket-info-icon` (or, since `InfoTooltip.jsx` is shared, a caller-supplied
      `testId` prop per the shared-component testid ruling, wired specifically at the Bucket
      field's call site in `ToolBaseProperty.jsx`).
16. Verify the tooltip displays the bucket naming rules (case step 16).
    - **Verify**: confirmed live, tooltip text (via `[role="tooltip"]`) reads exactly:
      "Name of the artifact bucket to use for file storage operations. The bucket name must: •
      Start with a lowercase letter • Contain only lowercase letters, numbers, and hyphens • Be
      unique within your project" — matches the case's expected content (start-with-lowercase,
      lowercase/numbers/hyphens-only, unique-within-project) word for word.
17. In the "Toolkit Name *" field enter "my-artifact-toolkit" (case step 17).
    - **Verify**: `toolkit-form-name-input` value === `"my-artifact-toolkit"`
      (`ToolkitCreationPage.fill_name()`, existing ELITEA-1868 method — MUI field, `click()` +
      `press_sequentially()`, confirmed live again this run: `fill()`-equivalent alone does not
      reliably flip `formik.dirty`).
18. In the "Bucket *" field enter "new-bucket" (case step 18).
    - **Verify**: `toolkit-field-{}-input`.format("bucket") value === `"new-bucket"`
      (`ToolkitCreationPage.fill_field("bucket", "new-bucket")`, existing ELITEA-1868 method,
      same MUI click+type pattern).
19. Leave all other fields at their default values (case step 19).
    - **Verify**: Description empty, Pgvector Configuration unselected, Embedding Model still
      `text-embedding-3-small`, MCP checkbox still unchecked (all confirmed live, unchanged from
      steps 11-13's baseline reads).
20. Click the "Save" button (case step 20).
    - **Verify**: `toolkit-form-save-button` becomes enabled once both fields are dirty
      (confirmed live) → click → URL becomes `${BASE_URL}/toolkits/all/{id}` (this run: `1524`).
      **Capture `{id}` here** — it is both the provenance for step 23's URL check AND the value
      teardown needs for `ArtifactAPI.delete_toolkit(id)` (see § Cleanup).
21. Verify the page navigates to the toolkit detail/configuration view (case step 21).
    - **Verify**: same URL check as step 20 — navigation confirmed live, no known defect on this
      path (unlike the sibling ELITEA-1868 case's Cancel path / #655, which this brief's own
      sibling-context section correctly flagged as NOT applicable here — independently
      reverified live this run: Save navigates correctly).
22. Verify the page header displays the toolkit name (case step 22).
    - **Verify (NEW handle)**: `toolkit-detail-title` text === `"my-artifact-toolkit"` (confirmed
      live). Page `<title>` also updates to `"Toolkit: my-artifact-toolkit - Private"` (secondary
      signal, not required for the assertion).
23. Verify the URL updates to reflect the new toolkit (case step 23).
    - **Verify**: URL matches `${BASE_URL}/toolkits/all/{id}?name=my-artifact-toolkit` where
      `{id}` is the numeric toolkit ID captured in step 20 (confirmed live: `1524` this run,
      value is run-specific and MUST be captured dynamically, never hardcoded).
24. Verify "Configuration" and "Indexes" tabs are shown at the top (case step 24).
    - **Verify**: `document.querySelectorAll('[role="tab"]')` returns (at least) two tabs: the
      first (index 0, selected by default) is Configuration — icon-only, no visible text, NO
      testid; the second (index 1) is Indexes — icon-only, no visible text, disabled (Pgvector
      not configured for this toolkit), carries `data-tour="toolkit-indexes-tab"` (a `data-tour`
      attribute, NOT a `data-testid` — not usable as a compliant locator) with parent
      `aria-label="Configure PgVector and Embedding model to enable Indexes options"` (usable as
      an interim non-testid disambiguator, but per this project's testid-only policy the
      compliant fix is `testid needed: toolkit-detail-configuration-tab` /
      `toolkit-detail-indexes-tab`). A third, empty (no icon, no aria-label) tab element also
      exists in the DOM at index 2 — unexplained by this case's own steps, not asserted on,
      flagged here only for completeness (not a defect — case doesn't reference a third tab).
25. Verify the "TEST SETTINGS" panel is visible with model selector, Tool dropdown, and welcome
    message (case step 25).
    - **Verify (NEW handles, the genuinely fresh surface this case introduces)**: `Test Settings`
      heading text visible; `model-selector-button`/`model-selector-name` visible (shows
      "Anthropic Claude 4.5 Sonnet" this run — model-specific, do not assert on the exact model
      name, only that the selector renders non-empty); `toolkit-test-tool-select` (the Tool
      dropdown's clickable combobox) visible; the center panel shows the literal welcome message
      "Welcome! Select a tool from the Test Settings panel and click 'RUN TOOL' to see the
      results here." (confirmed live, exact text match).
26. In the TEST SETTINGS panel click the "Tool" dropdown (case step 26).
    - **Verify**: `toolkit-test-tool-select` click opens a `[role="listbox"]` popper (confirmed
      live).
27. Verify the tool list shows all available tools including "List files" (case step 27).
    - **Verify**: the opened listbox's `[role="option"]` elements total 16, each carrying a
      dynamic testid `select-option-{tool_key}` (a pre-existing, ON-MAIN shared-component
      template — `SingleSelectMenuItem.jsx`, see § Concrete Handles); `select-option-list_files`
      is among them (confirmed live).
28. Select "List files" from the tool dropdown (case step 28).
    - **Verify**: `select-option-list_files` click closes the listbox and the Tool combobox now
      reads "List files" (confirmed live via the combobox's accessible name and its paired
      hidden textbox value `list_files`).
29. Verify the "List files" tool parameters panel shows Bucket Name, Folder, Recursive checkbox,
    Include array, Skip array, and "RUN TOOL" button (case step 29).
    - **Verify (NEW handles)**: `toolkit-test-param-bucket_name`, `toolkit-test-param-folder`,
      `toolkit-test-param-include`, `toolkit-test-param-skip` all visible (confirmed live — a
      generic `toolkit-test-param-{fieldKey}` template shared by `AnyOfPatternField.jsx` and
      `CommonStringField.jsx`, the SAME mechanism every string/array-typed test-tool parameter
      uses). The "Recursive" checkbox has **NO testid** — confirmed live via DOM inspection
      (`CommonBooleanField.jsx`'s wrapper `<Box>` omits the `data-testid={...{fieldKey}}` the
      sibling string-field components DO set) — `testid needed: toolkit-test-param-recursive`
      (same naming convention, just closing a gap in one specific field-type renderer). The
      "RUN TOOL" button ALSO has no testid — confirmed live (`TestToolSettings.jsx`'s
      `Button.BaseBtn`, no `data-testid` prop wired) — `testid needed:
      toolkit-test-run-tool-button`. Both gaps are genuinely new (no sibling AFS touches this
      panel).
30. Click the "RUN TOOL" button (case step 30).
    - **Verify**: leaving all parameter fields at their default (empty) values, per the case's
      own literal step sequence (it does not instruct filling Bucket Name first) — click
      (interim: `page.locator('button:has-text("RUN TOOL")')` until the testid above is added)
      → confirmed live the button was already enabled with all fields empty (List files evidently
      defaults to the toolkit's own configured bucket, "new-bucket", when no explicit Bucket Name
      override is given — see step 31's result).
31. Verify the tool runs and returns a result in the center chat/output panel (case step 31).
    - **Verify**: confirmed live, a new message appears in the center panel within ~3s:
      `✅ list_files (0.176s)` followed by `{'total': 0, 'rows': []}` — an empty result, which is
      the CORRECT expected outcome for a just-created, never-uploaded-to bucket (there are no
      files to list). No console errors accompanied the run (only the pre-existing #656
      warning, unchanged count). Network log confirms `POST
      /api/v2/elitea_core/conversations/prompt_lib/399 → 201` +
      `POST /api/v2/elitea_core/participants/prompt_lib/399/{id} → 200` back the test-panel's
      conversation/tool-run plumbing — no separate REST call to a `list_files`-specific endpoint
      is visible client-side (the tool executes server-side within that conversation).
32. Navigate to the Artifacts section (case step 32). Same sidebar-testid gap as step 1.
    - **Verify**: `artifacts-buckets-heading` visible (existing ELITEA-1808/1809 handle,
      `ArtifactsPage.wait_for_page_load()`).
33. Click the search icon in the "BUCKETS" header (case step 33).
    - **Verify**: `artifacts-search-buckets-button` click reveals `artifacts-bucket-search-input`
      (both existing ELITEA-1808/1809 handles, `ArtifactsPage.open_bucket_search()`).
34. Type "new" in the search field (case step 34).
    - **Verify**: `artifacts-bucket-search-input` reflects `"new"`
      (`ArtifactsPage.search_buckets("new")`, existing method).
35. Verify the bucket list filters and displays buckets containing "new" (case step 35).
    - **Verify**: `document.querySelectorAll('[data-testid^="artifacts-bucket-row-"]')` returns
      2 rows this run: `artifacts-bucket-row-new-bucket` AND
      `artifacts-bucket-row-new-bucketautotest-buck1-800755` (a DIFFERENT, pre-existing bucket
      from an earlier automated case's run that happens to also substring-match "new" — **known
      environment-state caveat, not a defect**: assert on PRESENCE of the specific
      `artifacts-bucket-row-new-bucket` testid, never on an exact row COUNT, since this shared
      DEV project accumulates other suites' `autotest-*`/`new-bucket*`-prefixed data over time —
      same caveat every sibling artifact AFS already documents).
36. Verify "new-bucket" is listed in the filtered results (case step 36).
    - **Verify**: `artifacts-bucket-row-new-bucket` present (existing `BUCKET_ROW` dynamic
      template, `artifacts_page.py`, from ELITEA-1808/1809 — no new handle needed).
37. Click on "new-bucket" to select it (case step 37).
    - **Verify**: `ArtifactsPage.click_bucket_row("new-bucket")` (existing method) → URL becomes
      `${BASE_URL}/artifacts?bucket=new-bucket` (confirmed live).
38. Verify the main panel header displays "new-bucket" (case step 38).
    - **Verify**: `artifacts-breadcrumb-bucket-label` text === `"new-bucket"` (existing
      ELITEA-1824 handle, `ArtifactsPage.get_breadcrumb_bucket_text()`).
39. Verify the main panel shows "No files in this bucket" with an "Upload files" button (case
    step 39).
    - **Verify**: `artifacts-empty-state` text === `"No files in this bucket"` (existing
      ELITEA-1824 handle, `ArtifactsPage.is_bucket_empty()`) AND
      `artifacts-upload-files-empty-state-button` text === `"Upload files"` and is visible
      (existing ELITEA-1824 handle) — both confirmed live, exact text match.

## Expected Results
- The Artifact-type toolkit-creation form opens correctly via the type-picker's search-and-click
  flow, exposes all 16 tools (checkmarked/selected by default) plus the MCP-availability
  checkbox (unchecked by default), and the bucket-field tooltip shows the correct naming rules
  on hover.
- Saving with `Toolkit Name = my-artifact-toolkit` and `Bucket = new-bucket` creates the toolkit
  AND, as a server-side side effect of the SAME create call, the bucket — no separate
  bucket-create request fires.
- The post-save detail view correctly navigates to `/toolkits/all/{id}`, shows the toolkit name
  in the header, and exposes a TEST SETTINGS panel whose Tool dropdown lists all 16 tools
  including "List files".
- Running "List files" with default (empty) parameters against the just-created, empty bucket
  returns `{'total': 0, 'rows': []}` within ~0.2s, displayed as a ✅ success result in the center
  panel.
- The new bucket is visible, searchable, and correctly shows the empty-bucket state
  ("No files in this bucket" + "Upload files" button) in the Artifacts section.
- **No blocking defects.** One case-text CLARIFICATION (#669, click-vs-hover on the info tooltip)
  and one cleanup-mechanism root-cause lead added to a pre-existing defect (#636) — see
  § Known Defects.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in | Session valid | Preconditions | `auth_state` fixture (skips login on localhost) | asserted |
| Preconditions: no existing "my-artifact-toolkit"/"new-bucket" | Names absent before run | Preconditions + Test Data (pre-clean design) | live search (0 toolkit results) + exact-testid bucket check (false) at run start | asserted |
| Test Data: Toolkit name = my-artifact-toolkit | Literal value entered | Step 17 | `toolkit-form-name-input` value check | asserted |
| Test Data: Bucket name = new-bucket | Literal value entered | Step 18 | `toolkit-field-bucket-input` value check | asserted |
| Test Data: Search term = art | Literal value entered | Step 7 | `toolkit-wizard-type-search-input` value check | asserted |
| Test Data: Tool to test = List files | Literal value selected | Step 28 | Tool combobox value === list_files | asserted |
| Step 1: Navigate to Toolkits (sidebar) | Toolkits list displayed | Step 1 | direct nav to `/toolkits/all`, `sidebar-create-button` visible | asserted *(sidebar has no testid — pre-existing, out-of-scope gap, same as ELITEA-1868/1809)* |
| Step 2: Verify Toolkits list shows all toolkits+types | List visible | Step 2 | `entity-card` non-empty-state check | asserted |
| Step 3: Click "+ Toolkit" | "New Toolkit" page opens | Step 3 | URL becomes `/toolkits/create` | asserted |
| Step 4: Verify "Choose the toolkit type" heading | Page title correct | Step 4 | URL check + live text-match | asserted *(heading itself still has no testid — optional gap carried from ELITEA-1868)* |
| Step 5: Verify "Search toolkits" search field | Search field visible | Step 5 | `toolkit-wizard-type-search-input` visible, placeholder text confirmed | asserted |
| Step 6: Verify category filter tabs displayed | All category tabs present | Step 6 | 12 tab buttons confirmed by text-match | asserted *(no testids on individual tabs — out of scope, this case never clicks one)* |
| Step 7: Type "art" in search | Filter applied | Step 7 | search input value | asserted |
| Step 8: Verify only Artifact shown under STORAGE | Filter correct | Step 8 | `toolkit-type-card-artifact` sole visible card (count===1) | asserted |
| Step 9: Verify no other toolkit types displayed | No other types visible | Step 9 | same count===1 check as step 8 | asserted (folded with step 8) |
| Step 10: Click Artifact card | "New Artifact Toolkit" form opens | Step 10 | URL becomes `/toolkits/create/artifact` | asserted |
| Step 11: Verify form tabs+CONFIGURATION fields | All fields present | Step 11 | 2 testid visibility checks + label-text confirmation for the rest | asserted |
| Step 12: Verify TOOLS section — 16 tools with checkmarks | All 16 listed, checkmarked | Step 12 | `toolkit-tool-chip-*` count===16, all `data-selected="true"` | asserted **(NEW handle)** |
| Step 13: Verify MCP checkbox unchecked by default | Checkbox present, unchecked | Step 13 | `toolkit-field-available_by_mcp-checkbox-field` checked===false | asserted **(NEW handle)** |
| Step 14: Verify Save/Cancel buttons present | Both buttons present | Step 14 | `toolkit-form-save-button` (disabled pre-dirty) + `toolkit-form-cancel-button` (enabled) | asserted |
| Step 15: Click info icon next to Bucket field | Tooltip appears | Step 15 | `.hover()`, NOT `.click()` — see § Known Defects (#669) | asserted *(CLARIFICATION filed — case text says click, product uses hover)* |
| Step 16: Verify tooltip content | Correct rules text shown | Step 16 | exact tooltip text match | asserted |
| Step 17: Enter Toolkit Name | Name field shows value | Step 17 | `toolkit-form-name-input` value | asserted |
| Step 18: Enter Bucket name | Bucket field shows value | Step 18 | `toolkit-field-bucket-input` value | asserted |
| Step 19: Leave other fields at defaults | Defaults retained | Step 19 | unchanged-value re-read | asserted |
| Step 20: Click Save | Toolkit saved, navigates to detail | Step 20 | URL becomes `/toolkits/all/{id}`, `{id}` captured | asserted |
| Step 21: Verify navigates to detail view | Detail view shown | Step 21 | same URL check as step 20 | asserted |
| Step 22: Verify header shows toolkit name | Correct name shown | Step 22 | `toolkit-detail-title` text | asserted **(NEW handle)** |
| Step 23: Verify URL reflects new toolkit | URL contains toolkit ID | Step 23 | dynamic `{id}` in URL | asserted |
| Step 24: Verify Configuration/Indexes tabs shown | Both tabs present | Step 24 | 2 icon-only `[role="tab"]` elements confirmed | asserted *(no testids on either tab — `testid needed: toolkit-detail-configuration-tab`/`-indexes-tab`)* |
| Step 25: Verify TEST SETTINGS panel visible | Panel + model selector + Tool dropdown + welcome msg | Step 25 | 4 element checks, one exact-text welcome-message match | asserted **(NEW handles)** |
| Step 26: Click Tool dropdown | Tool list expands | Step 26 | `toolkit-test-tool-select` click opens listbox | asserted **(NEW handle)** |
| Step 27: Verify tool list incl. List files | All 16 tools incl. List files | Step 27 | `select-option-*` count===16, `select-option-list_files` present | asserted |
| Step 28: Select List files | Parameters panel appears | Step 28 | `select-option-list_files` click, combobox value updates | asserted |
| Step 29: Verify List files parameters panel | Bucket Name/Folder/Recursive/Include/Skip/RUN TOOL all present | Step 29 | 4 `toolkit-test-param-*` handles + RUN TOOL button-text match | asserted **(NEW handles; 2 gaps found — Recursive checkbox, RUN TOOL button)** |
| Step 30: Click RUN TOOL | Tool runs, returns result | Step 30 | button click (interim text-locator until testid added) | asserted |
| Step 31: Verify result in center panel | Result displayed | Step 31 | exact-text `✅ list_files (0.176s)` + `{'total': 0, 'rows': []}` | asserted |
| Step 32: Navigate to Artifacts | Artifacts page loads | Step 32 | direct nav to `/artifacts`, `artifacts-buckets-heading` visible | asserted *(same sidebar gap as step 1)* |
| Step 33: Click BUCKETS search icon | Search field opens | Step 33 | `artifacts-search-buckets-button` → `artifacts-bucket-search-input` visible | asserted |
| Step 34: Type "new" | Bucket list filters | Step 34 | search input value | asserted |
| Step 35: Verify filtered results contain "new" | Filtered list shown | Step 35 | `artifacts-bucket-row-*` prefix count (2 this run — see note) | asserted *(assert presence, not exact count — shared-env caveat)* |
| Step 36: Verify "new-bucket" listed | "new-bucket" present | Step 36 | `artifacts-bucket-row-new-bucket` present | asserted |
| Step 37: Click "new-bucket" | Bucket selected | Step 37 | URL becomes `/artifacts?bucket=new-bucket` | asserted |
| Step 38: Verify header shows "new-bucket" | Header shows name | Step 38 | `artifacts-breadcrumb-bucket-label` text | asserted |
| Step 39: Verify empty-bucket state | "No files..." + Upload button shown | Step 39 | `artifacts-empty-state` + `artifacts-upload-files-empty-state-button` text | asserted |
| Expected Final State: toolkit+bucket created, List files works, bucket visible+empty | Composite pass condition | Steps 20-39 | combination of the above | asserted — no known defect blocks any part of this composite |
| Pass criterion: "All steps complete without errors" | No unexpected errors | All steps | console-error check at multiple checkpoints (0 new errors beyond the pre-existing, already-filed #656) | asserted |

### Axis 2 — Observables asserted beyond the case
- **`data-selected="true"` state-attribute check on all 16 tool chips** (step 12) — *added: the
  case says "with checkmarks"; the live implementation renders this as an MUI `Chip` with a
  conditional SVG icon gated by `data-selected`, so asserting the attribute (not just chip
  presence) is what actually proves "checkmarked", and it's already a compliant
  testid+data-attribute pattern per this project's locator policy.*
- **Network-level proof of the create call's shape** (`POST .../tools/prompt_lib/399 → 201`,
  no separate bucket-create POST) — *added: directly supports and documents the case's own
  objective sentence ("which also creates a bucket") at the transport level, not just via the
  UI's eventual empty-bucket-state check.*
- **Console-error checks at 4 separate checkpoints** (after type-picker load, after form-save
  navigation, after RUN TOOL, and idle) — *added: standard side-channel discipline; confirms the
  ONLY console error across the entire 39-step run is the pre-existing, already-filed #656
  warning — no new error was introduced by the Save/RUN TOOL/List files surfaces this case is
  the first to exercise.*
- **Root-cause verification of the bucket-delete defect (#636) via a live A/B of the UI's delete
  call vs. `ArtifactAPI.delete_bucket()`'s URL shape** — *added while designing § Cleanup: not
  part of the case's own 39 steps, but directly load-bearing for making this AFS's
  collision-avoidance design actually work; documented as a comment on #636 rather than a new
  ticket (dedup discipline).*
- **CLARIFICATION filed for the info-tooltip's real activation mode** (#669) — *added per the
  interaction-discovery ladder's mandatory source-read step; prevents the implementer from
  writing a `.click()` that silently no-ops in CI.*

## Cleanup

See § Test Data above for the full collision-avoidance design rationale. Summary:

1. **Pre-test (idempotent, best-effort)**: delete any stale `my-artifact-toolkit` toolkit via
   `ArtifactAPI.delete_toolkit(id)` (look it up by name first, e.g. via
   `ToolkitsListPage.search("my-artifact-toolkit")` + reading the resulting card's ID, or an API
   list-and-filter) and any stale `new-bucket` bucket via the UI dot-menu Delete flow
   (`ArtifactsPage.open_bucket_menu` → `click_bucket_menu_delete_item` → `confirm_delete_bucket`).
   Swallow "not found" outcomes — a clean environment is the expected common case.
2. **Post-test (mandatory, `finally`/fixture-teardown)**:
   - Toolkit: `ArtifactAPI.delete_toolkit(toolkit_id)` where `toolkit_id` is captured from step
     20's post-save URL. **Proven reliable this run**: `DELETE
     /api/v2/elitea_core/tool/prompt_lib/399/1524 → 204 No Content`, toolkit confirmed absent
     from the list afterward.
   - Bucket: UI dot-menu Delete flow (same as pre-test step). **Do NOT use
     `ArtifactAPI.delete_bucket()`** — proven broken this run via #636 (path-segment URL 404s);
     the UI's own call is query-param shaped and IS reliable, proven this run: `DELETE
     /api/v2/artifacts/buckets/default/399?name=new-bucket → 200 OK`, bucket row confirmed
     absent from the list afterward.
3. Both created-entity screenshots/evidence from this exploration session (repo root, untracked,
   safe to leave per this repo's existing pattern): `ELITEA-1866-step1-2-toolkits-list.png`
   through `ELITEA-1866-step37-39-new-bucket-empty-state.png` (13 files total, see repo root).
4. This AFS's own exploration session already fully cleaned up its own `my-artifact-toolkit`
   (id `1524`) / `new-bucket` — confirmed absent from both lists as of the end of this run. The
   implementer's test does not need to account for THIS session's leftovers, only for its own.

## Concrete Handles (discovered during exploration)

**Locator policy note:** this project's locator policy (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`) is **testid-only, no fallback ladder** —
`LocatorDescriptor(testid=...)` with no `fallback=`/`locator=`. Genuine gaps below are specced as
`testid needed:` work orders for the **implementer** to add via `add-data-testid` — not
self-fixed by this analyst pass, per the Analyst-slot rule.

**Provenance verified freshly this run**: `cd ../EliteaUI && git fetch origin` run immediately
before checking (`origin/main` at `c2e5b609`, `origin/automation/testids` at `457f5f44`, both
current as of this session), then `git grep` run against both refs for every testid below (both
literal-string and template forms).

| Element | testid | Status | Provenance | Notes |
|---|---|---|---|---|
| "+ Toolkit" sidebar button | `sidebar-create-button` | existing (shared) | **on-main ✓** | reused from ELITEA-1868 |
| Toolkits list search input | `agent-search-input` | existing (shared, default prop) | **on-main ✓** | reused from ELITEA-1868 |
| Toolkit/generic list card | `entity-card` | existing (shared) | **on-main ✓** | reused from ELITEA-1868 |
| Type-picker search input | `toolkit-wizard-type-search-input` | existing | **on-automation/testids only** | `ToolkitCreationPage.type_search_input`, reused from ELITEA-1868 |
| Toolkit type card (dynamic) | `[data-testid="toolkit-type-card-{}"]` template | existing | **on-automation/testids only** | reused from ELITEA-1868 |
| Toolkit Name input | `toolkit-form-name-input` | existing | **on-automation/testids only** | reused from ELITEA-1868 |
| Schema field (dynamic, text) | `[data-testid="toolkit-field-{}-input"]` template | existing | **on-automation/testids only** | reused for `bucket`; ELITEA-1868 |
| Save button | `toolkit-form-save-button` | existing | **on-automation/testids only** | reused from ELITEA-1868 |
| Cancel button | `toolkit-form-cancel-button` | existing | **on-automation/testids only** | not exercised by this case's happy path, present for completeness |
| **Tool chips (dynamic, 16×)** | `[data-testid="toolkit-tool-chip-{tool_key}"]` template + `data-selected` attribute | existing | **on-automation/testids only** | `ToolActionsItems.jsx` — NEW to this case, compliant testid+state pattern |
| **MCP checkbox (actual input)** | `toolkit-field-available_by_mcp-checkbox-field` | existing | **on-automation/testids only** | same `toolkit-field-{k}-checkbox-field` template family as `-input`; `ToolBase.jsx` |
| MCP checkbox (outer wrapper, do NOT use for `.checked` reads) | `toolkit-field-available_by_mcp-checkbox` | existing | **on-automation/testids only** | wrapper `<span>`, not the real `<input>` — same wrapper-vs-input gotcha ELITEA-1824 already documented for a different field |
| **Bucket-field info icon** | n/a | **testid needed: `toolkit-field-bucket-info-icon`** | n/a | `InfoTooltip.jsx` shared component, only a non-unique `data-info-tooltip` boolean attribute exists (3 instances on this form); needs a caller-supplied `testId` prop per the shared-component testid ruling |
| "Choose the toolkit type" heading | n/a | **testid needed: `toolkit-wizard-type-picker-heading`** (optional — URL check satisfies the observable) | n/a | carried forward unresolved from ELITEA-1868 AFS |
| **Toolkit detail header (name)** | `toolkit-detail-title` | existing | **on-automation/testids only** | `EditToolkit.jsx:418` — NEW to this case |
| **Configuration tab (icon-only)** | n/a | **testid needed: `toolkit-detail-configuration-tab`** | n/a | icon-only, no text, no testid; index-0 `[role="tab"]` is the only current handle |
| **Indexes tab (icon-only, disabled)** | n/a | **testid needed: `toolkit-detail-indexes-tab`** | n/a | has `data-tour="toolkit-indexes-tab"` (not a testid); index-1 `[role="tab"]` is the only current handle |
| **Test Settings — model selector** | `model-selector-button`, `model-selector-name` | existing | **on-automation/testids only** | present, not asserted beyond non-empty visibility |
| **Test Settings — Tool dropdown (combobox)** | `toolkit-test-tool-select`, `toolkit-test-tool-select-combobox` | existing | **on-automation/testids only** | `TestToolSettings.jsx:128` — NEW to this case |
| **Tool dropdown option (dynamic, 16×)** | `[data-testid="select-option-{tool_key}"]` template | existing (shared) | **on-main ✓** | `SingleSelectMenuItem.jsx` — a pre-existing, already-promoted shared component |
| **List files param — Bucket Name** | `toolkit-test-param-bucket_name` | existing | **on-automation/testids only** | `CommonStringField.jsx`/`AnyOfPatternField.jsx` template `toolkit-test-param-{fieldKey}` |
| **List files param — Folder** | `toolkit-test-param-folder` | existing | **on-automation/testids only** | same template |
| **List files param — Include** | `toolkit-test-param-include` | existing | **on-automation/testids only** | same template (array-type field) |
| **List files param — Skip** | `toolkit-test-param-skip` | existing | **on-automation/testids only** | same template (array-type field) |
| **List files param — Recursive (checkbox)** | n/a | **testid needed: `toolkit-test-param-recursive`** | n/a | `CommonBooleanField.jsx`'s wrapper `<Box>` omits the `data-testid={...}` the sibling field-type renderers set — same naming convention, one gap in one renderer |
| **RUN TOOL button** | n/a | **testid needed: `toolkit-test-run-tool-button`** | n/a | `TestToolSettings.jsx`, `Button.BaseBtn` with no `data-testid` prop wired |
| Artifacts buckets heading | `artifacts-buckets-heading` | existing (ELITEA-1808) | **on-automation/testids only** | reused |
| Search buckets button | `artifacts-search-buckets-button` | existing | **on-main ✓** | reused |
| Bucket search input | `artifacts-bucket-search-input` | existing (ELITEA-1809) | **on-automation/testids only** | reused |
| Bucket row (dynamic) | `[data-testid="artifacts-bucket-row-{}"]` template | existing (ELITEA-1808) | **on-automation/testids only** | reused, `BUCKET_ROW` constant in `artifacts_page.py` |
| Bucket dot-menu button (dynamic) | `[data-testid="bucket-menu-{}-menu-button"]` template | existing (ELITEA-1808) | **on-automation/testids only** | used for cleanup only, not part of the case's own 39 steps |
| Bucket dot-menu "Delete" item | `bucket-menu-delete-menuitem` | existing (ELITEA-1817) | **on-automation/testids only** | used for cleanup only |
| Bucket delete-confirm dialog/button | `delete-confirm-dialog`, `delete-confirm-button` | existing (ELITEA-1817) | **on-automation/testids only** | used for cleanup only |
| Bucket header/breadcrumb label | `artifacts-breadcrumb-bucket-label` | existing (ELITEA-1824) | **on-automation/testids only** | reused |
| Empty-state label | `artifacts-empty-state` | existing | **on-main ✓** | reused |
| Empty-state "Upload files" button | `artifacts-upload-files-empty-state-button` | existing (ELITEA-1824) | **on-automation/testids only** | reused |

## Network Behavior
- **Toolkit-create doubles as bucket-create.** `POST /api/v2/elitea_core/tools/prompt_lib/399 →
  201 Created` is the ONLY mutating call observed for the entire create-and-save flow (steps
  17-20) — no separate `POST` to any `/artifacts/buckets/...` endpoint fires. This confirms the
  case's own objective text at the transport level: creating the Artifact toolkit IS what
  creates the bucket, server-side, as part of the same request.
- **RUN TOOL's execution is conversation-based, not a direct REST call.** Clicking RUN TOOL
  (step 30) triggers `POST /api/v2/elitea_core/conversations/prompt_lib/399 → 201` +
  `POST /api/v2/elitea_core/participants/prompt_lib/399/{toolkit_id} → 200` — the tool itself
  executes server-side within that ad-hoc conversation; no separate `list_files`-specific REST
  endpoint is called client-side. The result surfaces via the SAME WebSocket/polling mechanism
  regular chat responses use (consistent with `.agents/testing.md`'s "AI responses arrive over
  WebSocket ~2s after send" note — this run's actual result landed within ~3s of the click,
  well inside any reasonable wait timeout).
- **Bucket-delete URL-shape mismatch (root cause of #636), confirmed live during cleanup
  verification**: the UI's own DELETE call for a bucket is
  `DELETE /api/v2/artifacts/buckets/default/{project_id}?name={bucket_name}` (query-param
  shape, confirmed 200 OK) — DIFFERENT from `automation/api/client.py`'s
  `ArtifactAPI._buckets_url()`, which builds a path-segment shape
  (`/artifacts/buckets/default/{project_id}/{bucket_name}`, confirmed 404 per #636). Toolkit
  delete has no equivalent mismatch: both the UI and `ArtifactAPI._toolkits_url()` /
  `delete_toolkit()` hit `elitea_core/tool/prompt_lib/{project_id}/{toolkit_id}` and both return
  a clean `204 No Content`.

## Known Defects Found During Exploration

- **[INFO/CLARIFICATION] Bucket-field info tooltip activates on hover, case text says "click"**
  — filed as [#669](https://github.com/EliteaAI/elitea-testing-public/issues/669). Root cause
  (read live, `EliteaAI/EliteaUI` `automation/testids`): `src/[fsd]/shared/ui/tooltip/
  InfoTooltip.jsx` wraps the info icon in a plain MUI `<Tooltip>` with no `onClick` handler —
  MUI's default trigger is `mouseenter`/focus, not click. Content shown on hover is correct and
  matches the case's expected text exactly. Not a product defect (reverse-masking guard —
  hover IS the intended/working mode per source); the case's own step-15 wording is what's
  stale. Automation: use `.hover()`, not `.click()`, on the info-icon element (step 15).
- **[Root-cause lead, not a new ticket] Bucket-delete cleanup mechanism** — a comment was added
  to the pre-existing, OPEN [#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)
  ("Artifact bucket cleanup fails silently — delete returns 404") documenting the EXACT URL-shape
  mismatch (query-param vs. path-segment) discovered while designing this AFS's own § Cleanup —
  this is directly load-bearing for the implementer: **do not use `ArtifactAPI.delete_bucket()`
  for this test's teardown until #636 is fixed** (see § Cleanup / § Network Behavior for the
  concrete evidence and the working alternative).
- **[MINOR, pre-existing, already filed] React "unique key prop" console warning** on the
  type-picker screen — [#656](https://github.com/EliteaAI/elitea-testing-public/issues/656),
  filed by the ELITEA-1868 analyst pass, confirmed to still fire on every load of
  `/toolkits/create` this run (steps 3-10). Not re-filed (dedup discipline); not gating; no
  other console error appeared anywhere else across the full 39-step run.

## Blocked Steps
None. All 39 case steps executed and verified end-to-end against the live system.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- **Extend, don't duplicate, the ELITEA-1868 page objects**:
  - `automation/pages/toolkits_list_page.py` — no changes needed, all methods used as-is
    (`wait_for_page_load`, `click_create_toolkit`, `search`, `count_visible_cards`).
  - `automation/pages/toolkit_creation_page.py` — no changes needed for the Save path itself
    (`select_toolkit_type`, `fill_name`, `fill_field`, `is_save_enabled`); ADD a
    `save_creation(timeout=15000) -> int` method that clicks `save_button`, waits for the URL
    to match `**/toolkits/all/*`, and returns the parsed numeric toolkit ID from the URL (needed
    by both step 20's assertion and § Cleanup's teardown).
  - `automation/pages/toolkit_detail_page.py` — ADD `toolkit_title` as a new
    `LocatorDescriptor(testid="toolkit-detail-title")` class field (this page's own identity,
    not test-panel-specific) and a `get_toolkit_title() -> str` convenience method.
- **New page object needed**: `automation/pages/toolkit_test_settings_page.py` (models the
  TEST SETTINGS panel — steps 25-31, a sibling region of `/toolkits/all/{id}`, not a variant of
  the Configuration form `ToolkitDetailPage` already covers). Needs:
  - `tool_select` (`toolkit-test-tool-select`), `TOOL_OPTION` template =
    `[data-testid="select-option-{}"]`.
  - `TOOL_PARAM` template = `[data-testid="toolkit-test-param-{}"]` (covers `bucket_name`,
    `folder`, `include`, `skip`, and — once added — `recursive`).
  - `select_tool(tool_key: str)` — clicks `tool_select`, clicks `TOOL_OPTION.format(tool_key)`,
    waits for the parameters panel to render (wait on the FIRST expected `TOOL_PARAM` for that
    tool becoming visible, not network-idle — same rationale the ELITEA-1868 AFS gives for the
    type-picker's background config GETs: the panel renders before any background call settles).
  - `run_tool()` — clicks the RUN TOOL button (interim: `page.get_by_role("button", name="RUN
    TOOL")` until `toolkit-test-run-tool-button` is added; SWITCH to the testid immediately once
    the implementer adds it — do not leave the interim locator in merged code).
  - `wait_for_tool_result(timeout=15000) -> str` — waits for a new list item to appear in the
    center panel's message list and returns its text content (poll on the ✅/❌ prefix appearing,
    not a fixed sleep — WebSocket-backed per `.agents/testing.md`).
- **MUI field caveat** (same as every other toolkit/artifact form in this codebase): use
  `click()` + `press_sequentially()` for `toolkit-form-name-input` /
  `toolkit-field-bucket-input` — `fill()` does not reliably flip `formik.dirty`.
- **Card-click gotcha** (carried forward from ELITEA-1868, reconfirmed this run): do NOT locate
  the Artifact type card via text-matching — always `[data-testid="toolkit-type-card-artifact"]`.
- **Tool-chip state check**: assert `data-selected="true"` on all 16 `toolkit-tool-chip-*`
  elements, not just their count — a chip present but `data-selected="false"` would silently
  fail a naive count-only check while still failing the case's real "with checkmarks" intent.
- **Info-tooltip interaction**: `.hover()`, not `.click()` — see § Known Defects (#669). If a
  future `testId` prop is added to `InfoTooltip.jsx`'s Bucket-field call site, switch off the
  ambient/duplicated `data-info-tooltip` selector immediately (it currently matches 3 elements
  on this form and is NOT safe to use as-is without additional scoping).
- **Toolkit-ID capture for cleanup**: parse the numeric ID from the post-save URL
  (`/toolkits/all/{id}`) rather than trying to read it from the response body directly in the
  page-object layer — keeps the page object UI-only; if a fixture-level API create/delete path
  is preferred instead of the full UI flow for setup, `ArtifactAPI.create_artifact_toolkit()`
  already exists in `automation/api/client.py:1634` and returns the ID directly, but note this
  AFS's own 39 steps require driving the UI form (the case IS a UI-flow verification), so API
  creation should be reserved for the pre-test idempotent-cleanup helper only, never for the
  test body itself.
- **Do not use `ArtifactAPI.delete_bucket()` for teardown** — broken per #636, confirmed broken
  again live this session. Use the UI dot-menu Delete flow (`ArtifactsPage.open_bucket_menu` →
  `click_bucket_menu_delete_item` → `confirm_delete_bucket`, all pre-existing ELITEA-1817
  methods) instead — proven working live this session.
- Test isolation: per § Test Data, this test needs BOTH a pre-test idempotent-cleanup step AND a
  guaranteed (`finally`/fixture-teardown) post-test cleanup step, because it uses literal
  (non-randomized) names the case's own Preconditions mandate. This is a deliberate deviation
  from the "generate a random suffix" pattern every sibling artifact AFS uses for its OWN test
  data — do not "fix" it by randomizing `my-artifact-toolkit`/`new-bucket`, since the case text
  explicitly specifies these exact literal values as Test Data.
