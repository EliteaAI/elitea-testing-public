# Test Case: Create Remote MCP — Minimal Required Fields

## Metadata
- **TMS ID**: ELITEA-1921
- **Linked Story**: none
- **Priority**: l1
  - **Contradictory case metadata (report, not guess):** the TMS case's own frontmatter says `priority: critical` while its body prose says `**Priority:** high`. Used the frontmatter (structured field, l1 = critical) as authoritative for this file's priority digit; flagging the mismatch here per the intake rule ("contradictory-metadata → report not guess") rather than silently picking one. Does not block automation — noted for the lead/TMS owner to reconcile the case text.
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths the dev server, confirmed "Elitea is connected" in the sidebar after page load)
- **Analyst**: qa-engineer (agent), session 2026-07-18
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (on localhost this is automatic via `VITE_DEV_TOKEN`; on deployed envs, standard Keycloak login via `${TEST_USER}`).
- Project context is set (sidebar shows `Project: <name>`; project id read from `${ELITEA_PROJECT_ID}`, confirmed live as project id `399`, project name "Private").
- No precondition data needs seeding — MCP creation is a self-contained create flow.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Toolkit Name: `autotest_remote_mcp_minimal` per the case text, but **MUST be uuid-suffixed for uniqueness** the same way ELITEA-1922's covering test does (`f"autotest_mcp_full_{uuid.uuid4().hex[:6]}"`) — **with one correction discovered this session**: `automation/pages` has no length guard, and `EliteaUI/src/common/constants.js`'s `MAX_NAME_LENGTH = 32` silently truncates anything longer (confirmed constant, and independently documented by the ELITEA-1922 implementer). `"autotest_remote_mcp_minimal"` is already 27 characters — appending ELITEA-1922's 6-hex-char pattern (`_XXXXXX`, 7 more chars) would total 34 and silently truncate, producing a toolkit name that doesn't match what the test thinks it created. Use a **4-hex-char** suffix instead: `f"autotest_remote_mcp_minimal_{uuid.uuid4().hex[:4]}"` = 27 + 1 + 4 = 32 chars exactly (at, not over, the cap).
- URL: `https://mcp.example.com/sse` (static — matches the case text; live exploration found several pre-existing MCPs in the project already sharing this exact URL with no apparent uniqueness constraint on it, so it does not need uniquification).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.

## Test Steps

1. Navigate to the MCPs section via the sidebar: click the "MCPs" nav item (`/mcps/all`), then click the sidebar's create button (single combined "+ MCP" button, testid `sidebar-create-button` — see Concrete Handles note on case-text drift).
   - **Verify**: navigates to `${BASE_URL}/mcps/create` (observed live URL: `/mcps/create?viewMode=owner` — the `?viewMode=owner` query param is always appended, `in page.url` substring assertion still holds).
2. Verify the "Choose the MCP type" type-picker page shows both a **Local** section (message "Still no local MCP available. Follow creation guides in our Documentation.") and a **Remote** section (a "Remote MCP" card).
   - **Verify**: `mcp-type-picker-local-empty-state` element is visible and its text contains "Still no local MCP available"; `toolkit-type-card-mcp` element is visible and its text contains "Remote MCP".
3. Click the Remote MCP type card (`toolkit-type-card-mcp`).
   - **Verify**: URL becomes `${BASE_URL}/mcps/create/mcp` (observed: `/mcps/create/mcp?viewMode=owner`); the `toolkit-form-name-input` field becomes visible (this is the same load-complete signal `McpFormPage.select_remote_mcp_type()` already uses — no testid exists on the tab label itself, see Concrete Handles).
4. Verify the Save button (`toolkit-form-save-button`) is **disabled** on the pristine, untouched form.
   - **Verify**: `save_button.is_disabled() == True`.
5. Fill Toolkit Name (`toolkit-form-name-input`) with the generated name.
   - **Verify**: field displays the typed value.
6. Fill Url (`toolkit-field-url-input`) with `https://mcp.example.com/sse`.
   - **Verify**: field displays the typed value.
7. Verify the Save button becomes **enabled** once both required fields hold values.
   - **Verify**: `save_button.is_disabled() == False`. **Do NOT additionally assert an intermediate "Save still disabled after only Name (or only Url) is filled" state** — live exploration found Save's enabled/disabled toggle is dirty-based (flips to enabled the instant ANY field is touched, not once all required fields are complete); asserting the stricter reading will flake/fail. See Known Defects (CLARIFICATION #633) — actual submission is still correctly gated by inline Yup validation, so this is not a functional risk, just an assertion-writing trap.
8. Click Save (`toolkit-form-save-button`).
   - **Verify**: `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` returns `201 Created`; page navigates to `${BASE_URL}/mcps/all/{id}?name={toolkit_name}`.
9. On the MCP detail page, verify the page heading (`toolkit-detail-title`) contains the generated toolkit name, and the Form view's Toolkit Name / Url inputs show the persisted values.
   - **Verify**: `toolkit-detail-title` text == generated toolkit name; `toolkit-form-name-input.input_value() == toolkit_name`; `toolkit-field-url-input.input_value() == "https://mcp.example.com/sse"`.
10. Navigate to the MCP list (`/mcps/all`); locate the card matching the generated toolkit name and verify it carries a "Remote" type badge.
    - **Verify**: within the matching `entity-card` (filtered by `entity-card-name` text), an `entity-card-tag-chip` element with text exactly `"Remote"` is present.

## Expected Results
- Save is disabled on the pristine form and becomes enabled once both Toolkit Name and Url are filled (see step 7's flake-avoidance note on the exact enable trigger).
- The Remote MCP toolkit is created (`POST .../tools/prompt_lib/{project}` → `201`) and the detail page (`/mcps/all/{id}`) loads showing the correct name and the two filled fields, with every other field left at its schema default (no Description, no Headers, default Timeout/Cache TTL/Enable Caching/Ssl Verify — this case intentionally does NOT touch those, unlike ELITEA-1922).
- The new MCP appears in the `/mcps/all` list with a "Remote" type badge (`entity-card-tag-chip` text "Remote").
- No console errors beyond the two already-filed, pre-existing, unrelated React dev-mode warnings (`#291` — see Known Defects).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, has access to MCPs section | — | — | fixture-level (`auth_state` / localhost dev-token) | asserted |
| 1 Navigate to MCPs section from sidebar (click "MCPs") | MCPs section loads | step 1 | `step 1` | asserted |
| 2 Click "+" button next to "MCP" label | MCP creation flow initiates | step 1 | `step 1`: URL becomes `/mcps/create...` | asserted — **case-text drift, non-blocking**: live product renders ONE combined button (icon + "MCP" text, single `sidebar-create-button` testid), not a separate "+" icon beside a "MCP" label as the case text implies. Intent (click to start MCP creation) is fully satisfied; not filed as a defect (purely cosmetic case-wording, no functional ambiguity — see Concrete Handles). |
| 3 Verify "Choose the MCP type" page at `/app/mcps/create` | page displays at correct URL | step 1 | `step 1`: `in page.url` substring | asserted — **localhost has no `/app` prefix** (`APP_PREFIX` empty per `.agents/profile.md`); URL observed live is `/mcps/create?viewMode=owner` — substring assertion, not exact match, same pattern ELITEA-1922 already uses |
| 4 Verify Local (empty message) + Remote (card) sections | both visible with correct content | step 2 | `step 2`: `mcp-type-picker-local-empty-state` + `toolkit-type-card-mcp` text | asserted — **testid added this session** (`mcp-type-picker-local-empty-state`, commit `750d72f7` on `automation/testids`); previously this text had no testid anywhere (confirmed via live DOM inspection) |
| 5 Click "Remote MCP" card | navigates to `/mcps/create/mcp`, "New Remote MCP" tab selected | step 3 | `step 3`: URL + `toolkit-form-name-input` visible | asserted |
| 6 Verify form at `/mcps/create/mcp`, tab "New Remote MCP" selected | correct URL and tab active | step 3 | `step 3` (decomposed with step 5 — same click, same expected result; case's steps 5 and 6 collapse to one AFS step) | asserted — **no testid exists on the tab element** (confirmed live); the URL + name-input-visible proxy is the same signal `McpFormPage.select_remote_mcp_type()` already uses successfully in the merged ELITEA-1922 test, so no new testid was added for the tab text itself |
| 7 Verify Save button disabled when form empty | Save button disabled | step 4 | `step 4`: `save_button.is_disabled()` | asserted |
| 8 Fill "Toolkit Name *" with "autotest_remote_mcp_minimal" | field accepts and displays input | step 5 | `step 5` | asserted *(generated, uuid-suffixed name — see Test Data)* |
| 9 Fill "Url *" with "https://mcp.example.com/sse" | field accepts and displays input | step 6 | `step 6` | asserted |
| 10 Verify Save button becomes enabled | Save button clickable | step 7 | `step 7`: `save_button.is_disabled() == False` | asserted — **clarification filed (issue #633)**: live behavior is dirty-based enabling (any single field touched enables Save), not full-required-completeness-based, though by the time both fields are filled (this step) Save is certainly enabled either way — the case's literal claim holds at THIS point in the flow, the risk is only in an intermediate single-field assertion nobody should add (see step 7 note) |
| 11 Click Save | operation succeeds, redirect occurs | step 8 | `step 8`: `201` + navigation | asserted |
| 12 Verify redirect to detail page with correct name | detail page loads with correct MCP name | step 9 | `step 9`: `toolkit-detail-title` text | asserted |
| 13 Navigate to MCP list, verify "Remote" type badge | new MCP listed with "Remote" badge | step 10 | `step 10`: `entity-card-tag-chip` text "Remote" scoped to the matching `entity-card` | asserted — **no new testid needed**: `entity-card-tag-chip` is an existing, on-`main` generic testid (`CardTagSectionItem.jsx`) already used for every entity-list badge/tag; confirmed live via the raw `GET .../tools/prompt_lib/399?...` response that the API does NOT return a `tags` field at all — the "Remote" text is derived **client-side** from `ToolkitsHelpers.enhanceToolkitData()` (`toolkits.helpers.js:310`), which synthesizes a `tags: [{name: label}]` array from the toolkit's `type` via `getToolkitIcon()`'s schema-driven label |
| Expected Final State: MCP visible in list with "Remote" badge, detail page accessible | — | steps 9–10 | steps 9–10 | asserted |
| Pass/Fail criteria: all steps complete without error, MCP created and listed correctly | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- `step 4`/`step 7` assert the Save button's disabled↔enabled transition explicitly with `.is_disabled()` DOM reads (not just "button is clickable") — *added: this is the one non-obvious, easy-to-get-wrong part of the whole case; a naive read of case steps 7/8/9/10 suggests asserting Save stays disabled through partial fills, which does NOT hold live (see step 7 note and CLARIFICATION #633). Made explicit so the implementer doesn't write a flaky intermediate assertion.*
- `step 9` asserts the Form view's Toolkit Name/Url inputs show the persisted values (not just the heading) — *added: proves the two filled fields actually round-tripped through the `201` create + subsequent detail-page `GET`, not just that SOME toolkit with that id exists.*
- `step 9` (implicit) — this case deliberately does **not** touch Description/Headers/Client Id/Client Secret/Scopes/Timeout/Cache TTL/Enable Caching/Ssl Verify; ELITEA-1922's covering test already asserts every one of those fields' persistence with all fields populated. This case's whole point is the *minimal*-fields path (only Name + Url) plus the Save-button gating and list-badge behavior ELITEA-1922 doesn't touch — no redundant field-by-field re-assertion added here.
- No console-error assertion added for the same two pre-existing, unrelated React dev-mode warnings ELITEA-1922's AFS documented (missing `key` prop in `CategorySection`/`GroupedCategory`; invalid `<p>`-in-`<p>` DOM nesting from `InfoTooltip`) — both reproduced again this session on `/mcps/create` and `/mcps/create/mcp`, already filed as `EliteaAI/elitea-testing-public#291`, not refiled.

## Cleanup

1. This case creates a persistent MCP toolkit (server-side `tool` entity, confirmed via `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` → `201 Created` with a numeric `id`, e.g. `id: 1507` during this session's exploration).
2. Delete it in test teardown via the existing `ToolkitAPI.delete_toolkit(toolkit_id)` client (`automation/api/client.py`) — same pattern as `test_create_remote_mcp_all_fields_populated`'s `finally` block. Capture the id from the Save response (network wait) or the post-save detail-page URL (`/mcps/all/{id}`).
3. This session's own exploration toolkit (id `1507`, name `autotest_remote_mcp_minimal`) **was deleted live** via the UI's own delete flow (three-dot menu → Delete → type-to-confirm → confirm), confirmed via `DELETE /api/v2/elitea_core/tool/prompt_lib/399/1507` → `204 No Content` — no residue left behind for the implementer to clean up (unlike ELITEA-1922's exploration session).
4. No credential/secret cleanup needed — this case never touches Client Secret (minimal-fields path).

## Concrete Handles (discovered/re-confirmed during exploration)

`ToolBaseProperty.jsx` is a shared, schema-driven field renderer — the dynamic `toolkit-field-{k}-*` testids are identical between the create form and the detail page for a given schema key. All handles below were exercised live against `http://localhost:5173` (dev server on `EliteaAI/EliteaUI` @ `automation/testids`).

**PROVENANCE verified via `cd ../EliteaUI && git fetch origin` then `git grep <testid> origin/main` / `origin/automation/testids`, immediately before writing this table.**

| Element | Locator | PROVENANCE | Fallback |
|---|---|---|---|
| Sidebar create-MCP button (combined "+MCP" button) | `[data-testid="sidebar-create-button"]` | on-main ✓ | none — testid-only |
| Local empty-state message ("Still no local MCP available...") | `[data-testid="mcp-type-picker-local-empty-state"]` | **needs-adding** — added THIS session, commit `750d72f7` on `automation/testids`; not yet on `main` | none |
| Remote MCP type-selector card | `[data-testid="toolkit-type-card-mcp"]` | on-automation/testids only | none |
| Toolkit Name input | `[data-testid="toolkit-form-name-input"]` | on-automation/testids only | none |
| Url input | `[data-testid="toolkit-field-url-input"]` | on-automation/testids only | none |
| Save button (create form) | `[data-testid="toolkit-form-save-button"]` | on-automation/testids only | none |
| Detail page title heading | `[data-testid="toolkit-detail-title"]` | on-automation/testids only | none |
| MCP list card outer container | `[data-testid="entity-card"]` | on-main ✓ | none |
| MCP list card name | `[data-testid="entity-card-name"]` | on-main ✓ | none |
| MCP list card type/tag badge (e.g. "Remote") | `[data-testid="entity-card-tag-chip"]` — collection locator, one per tag chip; scope inside the matched `entity-card` via `.filter(has_text=name)` then `.locator(...)` | on-main ✓ | none |
| Three-dot actions menu button (cleanup) | `[data-testid="controls-menu-button"]` | on-main ✓ | none |
| Delete menu item (cleanup) | `[data-testid="toolkit-actions-delete-menuitem"]` | on-automation/testids only | none |
| Delete-confirm dialog (cleanup) | `[data-testid="delete-confirm-dialog"]` | on-automation/testids only | none |
| Delete-confirm Name field (cleanup) | `[data-testid="delete-confirm-name-input"]` | on-main ✓ | none |
| Delete-confirm button (cleanup) | `[data-testid="delete-confirm-button"]` | on-automation/testids only | none |

**No tab-label testid exists** for "New Remote MCP" (case step 6) — confirmed live (`document.querySelector('[role="tab"]').getAttribute('data-testid')` → `null`). Not added: the URL + `toolkit-form-name-input`-visible signal already fully satisfies this step's intent and is the exact same signal the merged `McpFormPage.select_remote_mcp_type()` already relies on — adding a testid here would be scope creep against a value nothing in this case actually needs to read.

## Network Behavior
- `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` — fires on Save click; `201 Created` on success; response body's `id` is the new toolkit id (confirmed live: `id: 1507`).
- `GET /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{id}?` — fires on detail-page load; confirms persisted values — wait for this before asserting persisted values (same as ELITEA-1922).
- `GET /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}?...&mcp=true&...` — fires on `/mcps/all` list load; response has **no `tags` field** — the "Remote" badge text is synthesized client-side (see Coverage Map row 13), so there is nothing to assert at the network layer for the badge itself, only in the rendered DOM.
- `DELETE /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{id}` — fires on delete-confirm click (cleanup); `204 No Content` on success (confirmed live for id `1507`).
- No `POST` fires when Save is clicked with an incomplete form (confirmed live for both "Name-only" and "Url-only" partial states) — client-side Yup validation blocks the request entirely, see Known Defects / CLARIFICATION #633.

## Known Defects Found During Exploration

**No functional defects found.** Both findings below are informational clarifications, not blocking:

- **[INFO] Save button enables on first dirty field, not required-field completeness** — filed as `EliteaAI/elitea-testing-public#633` (label `bug`, `[INFO]` severity). Documents that the Save button's disabled→enabled toggle is dirty-based rather than validity-based, and that this is intentional (client-side validation still correctly blocks submission of an incomplete form — confirmed no `POST` fires and an inline "Field is required" error appears). See Test Steps 4/7 and Coverage Map row 10 for the exact implication for automation.
- **[MINOR] Pre-existing React dev-mode console warnings on `/mcps/create` and `/mcps/create/mcp`** — already filed as `EliteaAI/elitea-testing-public#291` (found during the ELITEA-1922 analysis session, re-confirmed identical this session: missing `key` prop in `CategorySection`/`GroupedCategory`, and invalid `<p>`-in-`<p>` DOM nesting from `InfoTooltip` in `ToolBaseProperty.jsx`). Not refiled; no console-error assertion added to this case for the same reason ELITEA-1922 didn't add one (would couple a functional test to unrelated cosmetic warnings).
- No CLARIFICATION filed for the sidebar "+ button next to MCP label" case-text vs. the live single combined "+MCP" button — purely cosmetic case-wording, the click's functional intent is unambiguous and fully satisfied (see Coverage Map row 2).
- **Case-metadata note (not a product defect):** the TMS case's frontmatter (`priority: critical`) disagrees with its own body prose (`**Priority:** high`) — see Metadata section. Reported here per the intake "contradictory-metadata → report not guess" rule; not filed as a tracker issue since this is a TMS-authoring quality note, not a product defect.

## Blocked Steps

None. All 13 case steps were executed to completion against the live local environment, including full create → verify → list-badge → delete cleanup.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (per `.agents/testing.md`).
- **Reuse existing page objects — do not duplicate methods** (`.claude/rules/page-objects.md` § Critical: NO Method Duplication):
  - `automation/pages/mcp_form_page.py` (`McpFormPage`) already has `navigate_to_create()`, `select_remote_mcp_type()`, `fill_name()`, `fill_url()`, `save_and_wait_for_created()`, `get_detail_heading_text()`, plus the full delete-flow (`open_controls_menu()`, `click_delete_menu_item()`, `fill_delete_confirm_name()`, `confirm_delete()`) needed for teardown. **Missing**: a `is_save_button_disabled()` (or similarly named) helper wrapping `self.save_button.is_disabled()` — add this as a new method, it doesn't exist today (only `save_button` the `LocatorDescriptor` itself exists).
  - `automation/pages/mcp_list_page.py` (`McpListPage`) already has `navigate()`, `open_card_by_name()`, `get_card_names()`. **Missing**: a method to read a specific card's type/tag badge text — needs a new `entity_card_tag_chip` `LocatorDescriptor` field (or a scoped `UPPER_CASE` selector constant, e.g. `CARD_TAG_CHIP_SELECTOR = '[data-testid="entity-card-tag-chip"]'`, per the page-objects.md scoped-selector pattern) plus a method like `get_card_type_badge_text(name: str) -> str` that does `self.mcp_card.filter(has_text=name).locator(self.CARD_TAG_CHIP_SELECTOR).first.text_content()`.
  - **New page object needed** for the type-picker's Local/Remote section content (case step 4) — neither existing page object has a field for `mcp-type-picker-local-empty-state`; add it to `McpFormPage` (it already owns `remote_mcp_type_card` for the same page) rather than creating a third page object for a single field.
- Suggested test name: `test_create_remote_mcp_minimal_required_fields`, as a **new sibling test function in the same file** as ELITEA-1922's covering test (`automation/tests/ui/toolkits/test_mcp_create_remote.py`) — same feature area, same page objects, but a genuinely distinct scenario (minimal-fields path + Save-button gating + list-badge assertion, none of which the existing test touches). This is `ready-for-automation` (fresh implementation work), **not** `extend-existing` — appending Save-button-state-machine and list-badge assertions onto ELITEA-1922's "fill every field, verify full persistence" test would conflate two different test purposes and make that test do double duty; the AFS boundary-call guidance in `test-case-analysis` SKILL.md § Classify findings supports keeping this a separate test function even within the same file.
- **A dirty, unsaved form triggers a native `beforeunload` confirm dialog** if the harness ever navigates away mid-test — confirmed live (same as ELITEA-1922's AFS finding). Register `page.on("dialog", lambda dialog: dialog.accept())` before any such navigation, same pattern the covering test already uses.
- **Direct URL navigation to `/mcps/create/mcp` does NOT load the form** — confirmed live: navigating straight to that URL (bypassing the type-card click) redirects back to the `/mcps/create` type-picker with the wrong tab pre-selected ("New Mcp" generic, not "New Remote MCP"). The form only loads correctly via the click-through flow (`navigate_to_create()` → `select_remote_mcp_type()`), which is exactly what the existing page object already does — just flagging so nobody "optimizes" this into a direct navigate later.
- Toolkit Name length cap: **32 characters** (`MAX_NAME_LENGTH` in `EliteaUI/src/common/constants.js`), silently truncates anything longer — see Test Data for the exact uuid-suffix-length math for this case's specific base name (must use a 4-hex-char suffix, not ELITEA-1922's 6-hex-char one, or the name silently truncates).
- Wait strategy: wait for the `POST .../tools/prompt_lib/{project}` `201` response before asserting navigation to the detail page (same as ELITEA-1922) — the Save button's `onClick` fires an async event-emitter chain with a `setTimeout(..., 0)` inside.
