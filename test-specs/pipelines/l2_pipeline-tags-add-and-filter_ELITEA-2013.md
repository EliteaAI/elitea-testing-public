# Test Case: Pipeline Tags — Add and Filter

## Metadata
- **TMS ID**: ELITEA-2013
- **Linked Story**: none
- **Priority**: l2 (medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `pipelines-remaining-w2`
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` on localhost).
- User is on the `/pipelines/all` dashboard (private-project "All" tab —
  the only tab for a non-public-marketplace project; this is the page
  `PipelinesListPage.navigate()` already targets and every other Pipelines-
  dashboard AFS in this suite uses).

## Test Data
### generate-per-test (via UI, cleaned up in teardown)
- **Pipeline 1**: name `tagged_pipe_1_<uuid8>`, tags `["regression", "smoke"]`
  — created through the create-pipeline form's own Tags field (this IS the
  behavior under test for case Step 1; do **not** seed tags via
  `pipeline_api.create_pipeline()`, whose payload hardcodes `"tags": []`
  with no tags kwarg exposed at all — confirmed by reading
  `automation/api/client.py:616-651`).
- **Pipeline 2**: name `tagged_pipe_2_<uuid8>`, tags `["regression", "integration"]`
  — same UI-driven creation.
- Use a shared `uuid.uuid4().hex[:8]` suffix per test run (mirrors
  `test_skill_tag_filter.py`'s pattern) so tag names don't collide with a
  pre-existing project tag of the same literal text across repeated runs —
  e.g. `regression_<suffix>`, `smoke_<suffix>`, `integration_<suffix>`
  (**underscore separator, NOT hyphen** — amended during implementation:
  confirmed live that a hyphenated tag name silently fails to commit as a
  chip. Root cause read from source, `EliteaUI/src/common/constants.js`:
  `NormalTagNameInputRegExp = /^[\w,\s]+$/g` — `\w` allows letters, digits,
  and underscore only; no hyphen. Typing a hyphenated tag and pressing Enter
  leaves the Tags field with zero chips and no visible error, which would
  otherwise silently no-op the case's own tag-add assertions). This
  analyst session used bare `e2013regression`/`e2013smoke`/`e2013integration`
  for a one-off manual probe; the implementer's automated test uuid-suffixes
  them (underscore-separated) for repeatability across CI runs (a stale
  `regression` tag from run N would otherwise pollute run N+1's
  exact-membership assertions).
- Confirmed live: typing a tag name that **exactly matches an existing
  project tag** and pressing Enter reuses that tag's existing id (TagEditor's
  `handleOnChangeTags`: `tagList.rows.find(t => t.name === tag.name) || tag`)
  — so Pipeline 2's "regression" tag, typed the same way as Pipeline 1's, is
  the SAME tag object project-side. No separate "select existing tag from
  dropdown" step is needed to get this — `add_tag()` (type + Enter) is
  sufficient for both new and pre-existing tag names.

## Test Steps

(Live-executed and confirmed this session end-to-end against
`http://localhost:5173/pipelines/all`, project `Private`/399. Two disposable
pipelines were created, tag-filtered three ways, then deleted via the
detail page's three-dot menu → Delete pipeline confirmation dialog.)

1. **Setup** — navigate to `/pipelines/create?viewMode=owner`
   (`PipelinesListPage.navigate_to_create()`), fill name + description
   (`PipelineFormPage.fill_form()`), add tags `"regression"` then `"smoke"`
   via `PipelineFormPage.add_tag()` (type + Enter, existing method — commits
   each as a chip immediately, confirmed live), save
   (`save_and_wait_for_navigation()`). **Verify**: pipeline created — landed
   on its detail page (`/pipelines/all/<id>?...`); both tag chips
   (`pipeline-tags-chip` testid) render in the Tags field (case Step 1).
2. **Setup** — repeat for Pipeline 2 with tags `"regression"` then
   `"integration"`. **Verify**: created with both tags (case Step 2).
3. Navigate to the Pipelines dashboard (`PipelinesListPage.navigate()`).
   **Verify**: both pipelines visible in the grid
   (`pipeline_exists_in_list()` for each name); each card's own tag chips
   render its two tags (confirmed live via `entity-card-tag-chip` testid —
   same shared `CardTagSectionItem.jsx` component Skills already uses, zero
   pipeline-specific work) (case Step 3).
4. Click the `"smoke"` chip in the page-header Tags filter panel
   (`PipelinesListPage.filter_by_tag("smoke")` — **new method needed**, see
   § Concrete Handles). **Verify** — confirmed live: URL becomes
   `/pipelines/all?tags%5B%5D=smoke` (i.e. `?tags[]=smoke`); the grid narrows
   to **exactly** Pipeline 1 — `get_card_names() == [pipeline_1_name]`,
   Pipeline 2 is absent; "Clear all" (`tags-panel-clear-all`) appears in the
   panel; the clicked chip carries `[active]` accessible state (case Step 4).
5. Clear the filter (`PipelinesListPage.clear_tag_filter()` — new method),
   then click the `"regression"` chip. **Verify** — confirmed live: URL
   becomes `/pipelines/all?tags%5B%5D=regression`; the grid shows **both**
   Pipeline 1 and Pipeline 2 (`get_card_names()` contains both names, and
   ONLY those two among the disposable pair — no third disposable pipeline
   carries this run's `regression` tag) (case Step 5).
6. Clear the filter again (`clear_tag_filter()`). **Verify** — confirmed
   live: URL reverts to bare `/pipelines/all` (no `tags` query param); the
   full unfiltered pipeline count is restored (dashboard's own "Pipelines: N"
   counter in the right panel returns to its pre-filter value; both
   disposable pipelines plus every other pre-existing pipeline are visible
   again) (case Step 6).
7. **Side-channel check** — zero console errors across the whole
   create → filter → filter → clear flow (confirmed live this session:
   `browser_console_messages` — 0 errors at every checkpoint).

## Expected Results
- A pipeline created with tags shows those tags as chips both in its own
  Tags field (create/edit form) and on its dashboard card.
- Clicking a tag chip in the page-header Tags filter panel narrows the grid
  to exactly the pipelines carrying that tag (confirmed for both a
  single-match tag and a two-match shared tag).
- "Clear all" restores the unfiltered grid and strips the `tags` query param
  from the URL.
- Zero console errors across the whole flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create pipeline "tagged_pipe_1" with tags [regression, smoke] | Pipeline is created with both tags | step 1 | detail-page tag chips (`pipeline-tags-chip`) after save | asserted |
| 2 Create pipeline "tagged_pipe_2" with tags [regression, integration] | Pipeline is created with both tags | step 2 | detail-page tag chips after save | asserted |
| 3 Navigate to Pipelines dashboard | Dashboard loads with all pipelines visible | step 3 | `pipeline_exists_in_list()` for both names + card tag chips (`entity-card-tag-chip`) | asserted |
| 4 Filter by tag "smoke" — verify only "tagged_pipe_1" appears | Only "tagged_pipe_1" is shown | step 4 | `filter_by_tag("smoke")` → `get_card_names() == [pipeline_1_name]` + URL `?tags[]=smoke` | asserted |
| 5 Filter by tag "regression" — verify both pipelines appear | Both pipelines are shown | step 5 | `clear_tag_filter()` then `filter_by_tag("regression")` → `get_card_names()` contains both | asserted |
| 6 Remove tag filter — verify all pipelines are listed | All pipelines are visible without filtering | step 6 | `clear_tag_filter()` → URL has no `tags` param, dashboard count restored | asserted |
| Expected Final State: tag filtering correctly narrows/restores the list | — | steps 4–6 | steps 4–6 | asserted |
| Pass/Fail: all steps complete without errors; filters correctly include/exclude | — | all steps | all steps + console-error check | asserted |

### Axis 2 — Analyst additions

- **Exact-match tag reuse on second creation** — *added: the case doesn't
  say whether typing "regression" a second time (Pipeline 2) creates a
  duplicate tag or reuses the existing one. Confirmed live via source read
  (`TagEditor.jsx`'s `handleOnChangeTags`) and live behavior: exact-name
  match reuses the existing tag id — this is why Step 5's shared-tag filter
  correctly returns both pipelines rather than only whichever pipeline
  "owns" a separately-created duplicate tag with the same text.*
- **URL-param proof of filter state** (`?tags[]=<name>`) — *added: a
  stronger, non-flaky proof of the active filter than the visual grid alone,
  same pattern as ELITEA-2024's view-toggle URL-param assertion and
  ELITEA-1740's skill tag filter (`filter_by_tag()`'s own docstring already
  documents this for Skills — Pipelines confirmed to share the exact same
  `useTags` hook / URL-param shape, `src/hooks/useTags.jsx`).*
- **Card-level tag chips reuse the shared `CardTagSectionItem.jsx`
  component** — *added: confirmed live that Pipeline cards render their own
  tags via `entity-card-tag-chip`, the identical testid Skills cards already
  use (same component, `Card.jsx` → `CardTagSection.jsx` →
  `CardTagSectionItem.jsx`) — zero new testid work for this assertion.*
- **Console-error check across the whole flow** — *added: zero-cost given
  the live session was already open; confirmed 0 errors.*

## Cleanup
- Delete both disposable pipelines via the detail page's three-dot menu
  (`agent-actions-menu-button` → `delete-agent-menuitem` → type the exact
  name into the confirmation dialog's `delete-confirm-name-input` → click
  `delete-confirm-button`) — confirmed live this session (both testids
  already exist and work; no `pipeline_api.delete_pipeline()` needed for
  cleanup, though it would also work — `PipelineAPI` requires browser
  cookies, which a pytest fixture has readily available but this analyst's
  standalone MCP browser session did not conveniently expose, so the UI path
  was used instead).
- This analyst session's two probe pipelines (ids `8251`, `8252`,
  `tagged_pipe_1_e2013`/`tagged_pipe_2_e2013`) were deleted via this exact
  flow at the end of the session — confirmed removed from the dashboard
  (re-navigated and verified absence before ending the session). No residue.
- Tag entities themselves (`e2013regression`/`e2013smoke`/`e2013integration`)
  are project-scoped and were NOT deleted — same as the pre-existing
  precedent in `test_skill_tag_filter.py` (its `formatting`/`translation`/
  etc. tags are never cleaned up either; tags have no delete affordance
  surfaced in this flow and are cheap, inert leftovers). The implementer's
  uuid-suffixed tag names (§ Test Data) keep these from ever colliding
  across runs.

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only** — see
`.agents/role-overrides.md` / `.agents/testing.md` § Locator policy.

| Element | Testid | LocatorDescriptor field | Provenance |
|---|---|---|---|
| Tags input (create/edit form) | `pipeline-tags-input` | `tags_input` (existing, `pipeline_form_page.py:86`) | on-main? unconfirmed this session — pre-existing field from ELITEA-2021, confirmed live working |
| Tag chip in form's Tags field | `pipeline-tags-chip` | `tags_chip` (existing, `pipeline_form_page.py:91`) | pre-existing, confirmed live |
| Dashboard card's own tag chip | `entity-card-tag-chip` | **NEW** — add a `CARD_TAG_CHIP = '[data-testid="entity-card-tag-chip"]'` class constant + `get_card_tags(pipeline_name)` method on `PipelinesListPage`, mirroring `SkillsListPage.get_card_tags()` exactly (`automation/pages/skills_list_page.py:141,230-265`) — the testid itself is already live and entity-agnostic, only the page-object plumbing is missing on the Pipelines side | on-main ✓ — shared `CardTagSectionItem.jsx`, confirmed live via source read + DOM (no EliteaUI change needed) |
| Page-header Tags filter panel — per-tag chip | `tags-panel-chip-{name}` (dynamic) | **NEW** — add `TAGS_PANEL_CHIP = '[data-testid="tags-panel-chip-{}"]'` class constant + `filter_by_tag(tag_name)` method, mirroring `SkillsListPage.filter_by_tag()` exactly (`automation/pages/skills_list_page.py:137,519-551`) — only the URL match path differs: `.../elitea_core/applications/prompt_lib/` (pipelines, confirmed by ELITEA-2025's Network Behavior section) vs `.../elitea_core/skills/prompt_lib/` (skills) | on-main ✓ — hardcoded directly in the shared `Categories.jsx:336` (`data-testid={\`tags-panel-chip-${name}\`}`), confirmed live, entity-agnostic (not gated on any per-caller prop) |
| Page-header Tags filter panel — "Clear all" | `tags-panel-clear-all` | **NEW** — add `tags_panel_clear_all = LocatorDescriptor(testid="tags-panel-clear-all", ...)` field + `clear_tag_filter()` method, mirroring `SkillsListPage` exactly (`automation/pages/skills_list_page.py:127-134,553-578`) | on-main ✓ — hardcoded directly in `Categories.jsx:299`, confirmed live |
| Pipeline delete confirmation — name textbox | `delete-confirm-name-input` | not currently on `PipelinesListPage`/`PipelineDetailPage` — only needed for this AFS's own cleanup, not the case's assertions; add if the implementer wants a scripted teardown instead of `pipeline_api.delete_pipeline()` | confirmed live, used this session for cleanup |
| Pipeline delete confirmation — Delete button | `delete-confirm-button` | same as above | confirmed live, used this session for cleanup |
| Three-dot actions menu button (detail page) | `agent-actions-menu-button` | not currently a field; existing method may already reference it — check `pipeline_detail_page.py` before adding a duplicate | confirmed live |
| Delete-pipeline menu item | `delete-agent-menuitem` | already documented in `test-specs/pipelines/_surface.md` § Three-dot Actions menu (ELITEA-2049 session) | confirmed live, matches digest |

**Zero new EliteaUI/`add-data-testid` work for this case.** Every testid the
case's 6 steps touch already exists and is already entity-agnostic
(`Categories.jsx`/`CardTagSectionItem.jsx` are shared components rendering
the SAME literal testids for Pipelines as for Skills — confirmed by source
read, not inference). The only missing pieces are `PipelinesListPage`
**page-object methods** (`filter_by_tag`, `clear_tag_filter`, `get_card_tags`)
— pure Python, mirror `SkillsListPage`'s implementation line-for-line except
for the pipelines vs skills network-URL substring.

## Network Behavior
- Filter apply: `GET /api/v2/elitea_core/applications/prompt_lib/{project}?...tags=<id>...agents_type=pipeline...`
  — confirmed by the URL pattern already documented for the Pipelines
  dashboard in ELITEA-2025's AFS; not independently re-captured via
  `browser_network_requests` this session (URL-param + DOM evidence was
  sufficient and matches the established pattern exactly) — **implementer
  should confirm the exact response URL via `expect_response()` the same way
  `SkillsListPage.filter_by_tag()` does**, substituting the `applications`
  path segment for `skills`.
- Clear filter: same endpoint, `tags` param removed.
- Pipeline create (Steps 1–2): existing, already-covered
  `POST /api/v2/elitea_core/applications/prompt_lib/{project}` (ELITEA-2020/2021).
- Pipeline delete (cleanup): existing, already-covered delete endpoint (same
  family as `PipelineAPI.delete_pipeline()`'s `DELETE .../application/{id}`).

## Known Defects Found During Exploration
None blocking. The case automates cleanly against the live product — tag
creation, per-tag filtering (single-match and shared-tag two-match), and
filter-clear all behave exactly as specced, using entirely pre-existing,
entity-agnostic testids.

**Amended during implementation (two findings, neither blocking):**
1. **Tag-name charset constraint (implementer Phase 2 exploration).** The
   shared `TagEditor`/`AutoCompleteDropDown` validates new tag names against
   `NormalTagNameInputRegExp = /^[\w,\s]+$/g`
   (`EliteaUI/src/common/constants.js`) — alphanumerics, underscore, comma,
   whitespace only; **no hyphen**. A hyphenated uuid-suffixed tag name (as
   originally specced in § Test Data) silently fails to commit as a chip —
   zero chips render, Enter does nothing visible, no error surfaces. Fixed
   by uuid-suffixing with an underscore separator instead
   (`regression_<suffix>`) — see § Test Data amendment. Not filed as a
   product defect: the underlying validation is intentional and documented
   in the component's own help text ("Only alphanumeric characters, white
   space, comma and underscore allowed"); this is a test-data-shape fix, not
   a live-product/case-text drift.
2. **Known, not-filed cosmetic React dev-mode console warning** — same as
   already documented for Skills (ELITEA-1740 AFS Known Defects #2): a
   single `Warning: Invalid value for prop 'sx' on <svg> tag` fires from
   `TagEditor.jsx`'s shared `SvgCheckedIcon`/`ListItemIcon` when selecting/
   re-typing an existing tag name from the Autocomplete dropdown (Pipeline
   2's "regression" reuses Pipeline 1's tag). No user-visible symptom, no
   functional impact — filtered by the implementer's console-error listener
   the same way `test_skill_tag_filter.py` does, so it doesn't mask a real
   regression on this or future runs.

## Blocked Steps
None. All 6 case steps automate cleanly against the live product. No
`add-data-testid` work needed — see § Concrete Handles.

## Automation Hints
- Framework: Playwright + pytest (confirmed, matches every other pipeline spec).
- Use `PipelineFormPage.add_tag()` (existing) for tag creation on both
  pipelines — do NOT seed tags via `pipeline_api.create_pipeline()` (no
  `tags` kwarg exists; the case is explicitly testing the UI tag-add flow).
- Add three new methods to `PipelinesListPage`, mirroring `SkillsListPage`'s
  tag-filter trio (`automation/pages/skills_list_page.py:127-141,230-265,519-578`)
  almost verbatim — only the grid-refetch URL substring changes from
  `/elitea_core/skills/prompt_lib/` to `/elitea_core/applications/prompt_lib/`:
  ```python
  # class-level constants (mirror SkillsListPage)
  tags_panel_clear_all = LocatorDescriptor(
      testid="tags-panel-clear-all",
      description="'Clear all' button in the page-header Tags filter panel",
  )
  TAGS_PANEL_CHIP = '[data-testid="tags-panel-chip-{}"]'
  CARD_TAG_CHIP = '[data-testid="entity-card-tag-chip"]'

  def get_card_tags(self, pipeline_name: str) -> list[str]:
      card = self.page.locator(f'text="{pipeline_name}"').first.locator(
          "xpath=ancestor::*[.//*[@data-testid='entity-card-tag-chip' or "
          "not(@data-testid)]][1]"
      )
      # Prefer mirroring SkillsListPage.get_card_tags()'s exact card-scoping
      # approach (its own card-locator helper) rather than re-deriving one —
      # read that method's full implementation before writing this one.
      ...

  def filter_by_tag(self, tag_name: str, timeout: int = 10000):
      with self.page.expect_response(
          lambda r: "/elitea_core/applications/prompt_lib/" in r.url
          and r.request.method == "GET",
          timeout=timeout,
      ):
          self.page.locator(self.TAGS_PANEL_CHIP.format(tag_name)).click()
      self.wait_for_network(timeout=5000)
      self.page.wait_for_timeout(300)

  def clear_tag_filter(self, timeout: int = 10000):
      with self.page.expect_response(
          lambda r: "/elitea_core/applications/prompt_lib/" in r.url
          and r.request.method == "GET",
          timeout=timeout,
      ):
          self.tags_panel_clear_all.click()
      self.wait_for_network(timeout=5000)
      self.page.wait_for_timeout(300)
  ```
- Reuse `get_card_names()` (existing) for the Step 5 "both pipelines appear"
  assertion — no need for `get_card_tags()` there, only for Step 3's "each
  card shows its own tags" check.
- uuid-suffix all three tag names (§ Test Data) so repeated CI runs never
  collide on stale project-scoped tags from a prior run.
- Suggested markers: `@pytest.mark.p1` or `p2` (medium priority, matches
  sibling `l2_*` pipeline specs — see e.g. `test_pipeline_management.py`'s
  `p1`-marked tests for the closest precedent), `@pytest.mark.pipelines`,
  `@pytest.mark.regression`.
