# Test Case: Search Skills by Tag

## Metadata
- **TMS ID**: ELITEA-1740
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`).
- A project is selected/accessible (`Private`, id `399` in this run).
- Skills section is available (`/skills/all`), with the page-header "Tags"
  filter panel rendered (confirmed live — it is present unconditionally, not
  gated on any feature flag).
- At least one pre-existing skill (`automated-test-explainer`, id `15`, no
  tags) was present throughout this run and is unaffected by any tag filter
  applied.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill A name: `skill-a` — **not** `"Skill A"` as literally written in the
  case's Test Data table. The live Skill `Name *` field enforces
  lowercase-kebab-case-only client-side validation (same behavior already
  tracked for ELITEA-1737/1738/1739, see
  `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`); a
  capitalized two-word name like `"Skill A"` is rejected. This is case-text
  drift, not a product defect — see Known Defects/Clarification #1.
- Skill A tags: `["formatting", "output"]` (as specified).
- Skill B name: `skill-b` (kebab-case equivalent of "Skill B").
- Skill B tags: `["formatting", "english"]` (as specified).
- Skill C name: `skill-c` (kebab-case equivalent of "Skill C").
- Skill C tags: `["translation"]` (as specified).
- Skill description (all 3): `"Test skill {A|B|C} for ELITEA-1740 tag filter
  verification."` (any non-empty string satisfies the required field;
  content not asserted by this case).
- Skill instructions (all 3): `"You are Skill {A|B|C}, a test skill for
  ELITEA-1740 tag filter verification."` (any non-empty string under the
  2500-char limit; content not asserted by this case).
- Filter tags used: `formatting`, `translation`, `output` (as specified).
- Pre-existing skill in the same project at exploration time:
  `automated-test-explainer` (id `15`, no tags) — present throughout,
  correctly excluded from every tag-filtered view (it carries no tags).

No `reuse-existing` or `generate-shared-with-cleanup` data applies — tag
filter verification only needs the 3 skills created fresh and torn down in
the same run.

## Test Steps
1. Navigate to `${BASE_URL}/skills/create`, create Skill A (`skill-a`, tags
   `formatting` + `output`), Skill B (`skill-b`, tags `formatting` +
   `english`), and Skill C (`skill-c`, tags `translation`) — fill
   Name/Description/Tags/Instructions, Save, confirm the "unsaved changes"
   nav-blocker dialog for each. Tags are entered into the `Tags` combobox
   (Formik `TagEditor` component) by typing the tag text and pressing Enter
   (new tag) or selecting it from the autocomplete dropdown (existing tag —
   confirmed live: after Skill A's tags existed, Skill B's Tags combobox
   showed `formatting`/`output` as clickable autocomplete options).
   Navigate to `${BASE_URL}/skills/all`.
   - **Verify**: all 3 new skill cards plus the pre-existing
     `automated-test-explainer` (4 total) render in the grid, each showing
     its own tag chips inline on the card. Confirmed live (skill ids `129`,
     `130`, `131`). The page-header "Tags" panel lists all 4 distinct tags
     across the project (`formatting`, `output`, `english`, `translation`)
     as clickable filter chips.
2. Click the `formatting` chip in the page-header "Tags" panel.
   - **Verify**: **Passes.** The Skills grid filters down to exactly 2 cards
     — `skill-a` and `skill-b` — `skill-c` and `automated-test-explainer` are
     excluded. URL updates to
     `${BASE_URL}/skills/all?tags%5B%5D=formatting`. Network capture: the
     grid-fetching endpoint **does** re-fire with the tag applied —
     `GET .../elitea_core/skills/prompt_lib/399?sort_by=created_at&sort_order=desc&query=&tags=2&limit=20&offset=0`
     (`tags=2` is the tag's numeric id, resolved client-side from the
     `formatting` chip). The clicked chip shows an `active` state and a
     "Clear all" button appears next to the panel title. No console errors.
3. Click "Clear all", then click the `translation` chip.
   - **Verify**: **Passes.** Clearing restores all 4 cards (see step 5's
     assertion for the "Clear all" case in isolation); clicking `translation`
     then filters the grid down to exactly 1 card — `skill-c` — `skill-a`,
     `skill-b`, and `automated-test-explainer` are excluded. URL:
     `${BASE_URL}/skills/all?tags%5B%5D=translation`.
4. Click "Clear all", then click the `output` chip.
   - **Verify**: **Passes.** Grid filters down to exactly 1 card —
     `skill-a` — `skill-b`, `skill-c`, and `automated-test-explainer` are
     excluded. URL: `${BASE_URL}/skills/all?tags%5B%5D=output`.
5. Click "Clear all".
   - **Verify**: **Passes.** Grid is restored to all 4 cards (`skill-c`,
     `skill-b`, `skill-a`, `automated-test-explainer`), the "Tags" panel
     returns to its unfiltered state (no chip `active`, no "Clear all"
     button), and the URL drops the `tags[]` query param.

## Expected Results
Per the case: filtering by `formatting` returns Skills A and B only; by
`translation` returns Skill C only; by `output` returns Skill A only;
clearing restores the full list. **All of these hold in the live product** —
unlike the sibling case ELITEA-1739 (search-by-name, see
`.agents/memory/qa-engineer/skills_list_search_quirks.md` / issue #44), the
tag-filter mechanism is a genuinely separate, working feature: clicking a tag
chip in the page-header "Tags" panel re-fires the grid-fetching endpoint with
a `tags=<id>` query param and the grid updates correctly. No console errors
observed at any step; no defect found.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Test Data: Skill A/B/C named "Skill A"/"Skill B"/"Skill C" | names as literally specified | step 1 | step 1 (kebab-case substitutes used: `skill-a`/`skill-b`/`skill-c`) | clarification *(case-text drift — see Known Defects #1; product's kebab-case-only name validation is intentional, already tracked since ELITEA-1737, not a new bug)* |
| 1 Create 3 Skills with specified tags, all visible with their tags | 3 skills created, visible with correct tags | step 1 | step 1: 4 cards visible (3 new + 1 pre-existing), each new card shows its own tag chips | asserted |
| 2 Filter by `formatting` → only Skill A and B, Skill C excluded | list narrows to 2 matching cards | step 2 | step 2: grid shows exactly `skill-a` + `skill-b` | asserted |
| 3 Filter by `translation` → only Skill C, A and B excluded | list narrows to 1 card | step 3 | step 3: grid shows exactly `skill-c` | asserted |
| 4 Filter by `output` → only Skill A, B and C excluded | list narrows to 1 card | step 4 | step 4: grid shows exactly `skill-a` | asserted |
| Expected Final State: tag filter handles shared tags (multiple skills) and unique tags (single skill) correctly | both shared-tag and unique-tag cases work | steps 2–4 | steps 2 (`formatting`, shared by A+B) and 3/4 (`translation`/`output`, unique to C/A respectively) | asserted |

*(The case's step list does not include an explicit "clear filter" step —
unlike ELITEA-1739's case text — but "Clear all" is the mechanism used
between filter assertions in steps 3–5 above; see Axis 2.)*

### Axis 2 — Analyst additions

- step 1 documents the concrete tag-entry mechanism (Formik `TagEditor`,
  `automation/../EliteaUI/src/pages/Common/Components/TagEditor.jsx`, backed
  by `AutoCompleteDropDown`) and that previously-created tags surface as
  autocomplete suggestions for later skills in the same project — *added:
  useful implementation detail for the automation engineer building the tag
  helper, not itself a case requirement.*
- step 2 documents the underlying network contract in full (`tags=<numeric
  id>` query param on the skills grid endpoint, URL `tags[]=<name>` param on
  the page) — *added: root-cause-level evidence distinguishing this
  (working) mechanism from ELITEA-1739's (broken) name-search mechanism,
  useful for whoever maintains both.*
- step 5 explicitly asserts "Clear all" restores the grid — *added: the case
  doesn't spell out a clear-filter step, but it's the natural mechanism
  between filter assertions and is worth guarding since ELITEA-1739 showed a
  neighboring "clear" affordance can silently do nothing.*
- All steps assert no console errors during tag creation/filtering — *added:
  standard side-channel check per skill methodology; none found. One
  incidental React dev-mode warning (`Warning: Invalid value for prop sx on
  svg`, from `TagEditor`'s `SvgCheckedIcon` inside the Autocomplete popper's
  `ListItemIcon`) was observed once when selecting `formatting` from the
  autocomplete dropdown while creating Skill B — noted but not filed
  (React-dev-only warning, `sx` prop leaking onto a raw `<svg>`; zero
  functional impact, no user-visible symptom, purely a component-library
  hygiene nit). See Known Defects #2 for the disposition.*

## Cleanup
1. Delete each of the 3 test skills via the overflow menu → "Delete skill" →
   type the skill name to confirm → click Delete (same flow as
   ELITEA-1737/1738/1739). Verified in this run: all 3 (`skill-a` id `129`,
   `skill-b` id `130`, `skill-c` id `131`) deleted cleanly; grid returned to
   just the pre-existing `automated-test-explainer`, and the "Tags" panel
   returned to "No tags to display." — confirming no orphaned tags were left
   over from the deleted skills.
2. For automated cleanup, use the existing `skill_api` fixture
   (`SkillAPI.delete_skill(skill_id)`, `automation/api/client.py:1182`) in
   test teardown for all 3 created skill IDs, mirroring the pattern in
   `test_skill_export_import.py` — do not rely on UI delete in automated
   tests (slower, more brittle); UI-delete was only used here for
   interactive verification/cleanup.

## Concrete Handles (discovered during exploration)

> **Amended 2026-07-15 (implementer rework, testid-only locator policy,
> `.agents/role-overrides.md`).** The original exploration below found no
> `data-testid` on several Tags-panel/card elements and used role/text
> locators as a stop-gap (out of contract under the team's testid-only
> ruling). The rework added the missing testids via `add-data-testid`
> (`EliteaAI/EliteaUI` draft PR
> [#544](https://github.com/EliteaAI/EliteaUI/pull/544)) and converted every
> handle below to `LocatorDescriptor(testid=...)` / UPPER_CASE
> `[data-testid=...]` template constants in
> `automation/pages/skills_list_page.py` /
> `automation/pages/skill_form_page.py`. The table now reflects the
> **testid-only** state; the original role/text locators are struck through
> for traceability.

| Element | Locator | PROVENANCE |
|---|---|---|
| Skills grid cards | `SkillsListPage.skill_card_name` — `LocatorDescriptor(testid="entity-card-name")` (pre-existing, class-level field added in this rework) | on-main ✓ (pre-existing testid) |
| Skill create form fields | Existing `SkillFormPage` (`automation/pages/skill_form_page.py`) — `name_input`, `description_input`, `instructions_editor_content`, `save_button` | on-main ✓ (pre-existing testids) |
| Skills grid card — outer container (scopes per-card queries) | `SkillsListPage.skill_card` — `LocatorDescriptor(testid="entity-card")`, added in this rework on `Card.jsx`'s outer wrapper `Box` | on-automation/testids only (draft [#544](https://github.com/EliteaAI/EliteaUI/pull/544)) |
| Skills grid card — a specific skill's own tag chips (per-card, not the filter panel) | `SkillsListPage.get_card_tags(skill_name)` — scopes via `skill_card.filter(has=skill_card_name...)`, reads `card.locator(self.CARD_TAG_CHIP)` where `CARD_TAG_CHIP = '[data-testid="entity-card-tag-chip"]'`. ~~Was: `.MuiTypography-bodySmall` scoped via an xpath `ancestor::div[...MuiCard-root...]`~~ — the documented collision risk with the "+N" overflow badge and `Like.jsx`'s like-count element is now structurally impossible: `CardTagSectionItem` takes an `isOverflow` prop and renders `entity-card-tag-overflow` instead of `entity-card-tag-chip` for the "+N" badge, and `Like.jsx` was never in this query's scope to begin with. | on-automation/testids only (draft [#544](https://github.com/EliteaAI/EliteaUI/pull/544)) |
| Skills-list page-header "Tags" filter panel — clickable tag chip | `SkillsListPage.filter_by_tag(tag_name)` — `self.page.locator(self.TAGS_PANEL_CHIP.format(tag_name))` where `TAGS_PANEL_CHIP = '[data-testid="tags-panel-chip-{}"]'` (dynamic testid on `Categories.jsx`'s `StyledChip`). ~~Was: `page.get_by_role("button", name=tag_name, exact=True)`~~ | on-automation/testids only (draft [#544](https://github.com/EliteaAI/EliteaUI/pull/544)) |
| Skills-list "Clear all" (tag filter) button | `SkillsListPage.tags_panel_clear_all` — `LocatorDescriptor(testid="tags-panel-clear-all")` on the `IconButton` in `Categories.jsx`. ~~Was: `page.get_by_role("button", name="Clear all")`~~ | on-automation/testids only (draft [#544](https://github.com/EliteaAI/EliteaUI/pull/544)) |
| Skill create form: Tags autocomplete option (existing tag suggestion) | `SkillFormPage.select_existing_tag(tag_name)` — `self.page.locator(self.SKILL_TAG_OPTION.format(tag_name))` where `SKILL_TAG_OPTION = '[data-testid="skill-tag-option-{}"]'` (pre-existing dynamic testid; the rework converted the call site from an inline f-string `get_by_test_id(...)` to the class-constant template shape) | on-main ✓ (pre-existing testid; only the Python-side construction changed) |
| Skill create form: Tags combobox / added tag chip (inside the Tags field) | Existing `SkillFormPage.tags_input` / `tags_input_field` / `tag_chip` / `add_tag()` — unchanged by this rework (not in the ELITEA-1740 test's raw-handle list) | on-main ✓ (pre-existing testids) |

**Automation hint (superseded)**: the original hint below ("none of the
Tags-panel elements carry a `data-testid` today... does not block on
`add-data-testid`") no longer applies — this rework added all 4 missing
testids. Kept for historical traceability only:

> none of the Tags-panel elements (filter chip, "Clear all") carry a
> `data-testid` today. Role+accessible-name locators worked reliably and
> unambiguously in this exploration (tag names are unique per project), so
> this AFS does not block on `add-data-testid` — but if the automation
> engineer hits ambiguity (e.g. a future page reusing the same tag name in
> two panels), route through `add-data-testid` rather than falling back to a
> CSS selector, per `.claude/rules/page-objects.md`.

## Network Behavior
- `GET /api/v2/elitea_core/tags/prompt_lib/399?offset=0&limit=50&entity_coverage=skill`
  — fires on page load and refetches the tag panel's option list (all
  distinct tags across the project's skills).
- `GET /api/v2/elitea_core/skills/prompt_lib/399?sort_by=created_at&sort_order=desc&query=&tags=&limit=20&offset=0`
  — fires on initial page load with `tags=` empty.
- `GET /api/v2/elitea_core/skills/prompt_lib/399?sort_by=created_at&sort_order=desc&query=&tags=<id>&limit=20&offset=0`
  — **re-fires** on every tag-chip click, with `tags=<numeric tag id>` set
  (e.g. `tags=2` for `formatting` in this run) — this is the correct,
  working contract, in contrast to the **name**-search box on the same page
  (issue #44), which never re-fires this same endpoint.
- No error responses (4xx/5xx) observed on any request during this AFS's
  exploration.

## Known Defects Found During Exploration
1. **CLARIFICATION (case-text drift, not filed)** — the case's Test Data
   table specifies literal names `"Skill A"` / `"Skill B"` / `"Skill C"`;
   the live product enforces lowercase-kebab-case-only Skill names
   (`skill-a`/`skill-b`/`skill-c` used instead). This is the same,
   already-tracked product behavior confirmed in ELITEA-1737/1738/1739 (see
   `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`) — not
   re-filed as a new issue.
2. **Not filed (cosmetic, no functional impact)** — a single React dev-mode
   console warning, `Warning: Invalid value for prop %s on <%s> tag ... 'sx'
   'svg'`, fired once when selecting an existing tag from the Tags
   combobox's autocomplete dropdown while creating Skill B (stack trace
   points to `TagEditor.jsx` → `AutoCompleteDropDown.jsx` →
   `SvgCheckedIcon`/`ListItemIcon`). No user-visible symptom, no
   functional regression, reproducible via a normal user action (not a
   synthetic-input artifact) — but severity doesn't clear the bar for a
   ticket per this project's `Bug filing` policy (real, observable, but
   non-functional dev-console noise). Noted here for traceability only.

**No defect blocks this case.** Tag-based Skills filtering works correctly
for shared tags (`formatting` → 2 skills) and unique tags (`translation`,
`output` → 1 skill each), and "Clear all" genuinely restores the unfiltered
list — this is the key finding distinguishing ELITEA-1740 from its sibling
ELITEA-1739 (name-search, which IS broken — issue #44).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`); page object
  `automation/pages/skills_list_page.py` (`SkillsListPage`) is the natural
  home for a new `filter_by_tag(tag_name)` / `clear_tag_filter()` method
  pair — follow the existing `skill_exists_in_list()` pattern for grid
  assertions (case-insensitive substring match against
  `entity-card-name` cards), and additionally assert grid **count**
  (`page.get_by_test_id("entity-card-name").count()`) since this case's
  pass criteria are about exclusion, not just presence.
- Wait strategy: after clicking a tag chip, wait on the grid-fetching
  network response (`GET .../elitea_core/skills/prompt_lib/{project}?...`)
  before asserting card count/content — the URL changes synchronously via
  React Router but the grid re-render depends on the API round-trip.
- Tag creation in `SkillFormPage`: needs a new method, e.g.
  `add_tag(tag_text)`, wrapping "click Tags combobox → press_sequentially
  → Enter" (new tag) — existing-tag selection via autocomplete option
  click is a separate path worth its own method
  (`select_existing_tag(tag_name)`) since it goes through
  `get_by_role("option", ...)` instead of typing+Enter.
- Suggested test structure: one test per shared/unique-tag scenario, OR a
  single parametrized test iterating `[("formatting", ["skill-a",
  "skill-b"]), ("translation", ["skill-c"]), ("output", ["skill-a"])]`
  against the same 3 pre-created skills — cheaper than the case's literal
  per-step structure since all 3 filters share the same setup/teardown.
