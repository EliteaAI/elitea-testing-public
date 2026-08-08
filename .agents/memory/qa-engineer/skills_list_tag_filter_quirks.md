---
name: Skills list tag filter quirks
description: Categories.jsx "Tags" panel IS a working filter, SHARED verbatim across Skills/Pipelines (entity-agnostic testids, zero per-entity testid work)
type: feedback
---

**UPDATE 2026-08-08 (ELITEA-2013 analysis):** the "no testid on chip/Clear-all"
bullet below is STALE — the ELITEA-1740 rework added
`tags-panel-chip-{name}` (dynamic) and `tags-panel-clear-all` (static),
hardcoded directly in the shared `Categories.jsx` (lines 336/299) and
`CardTagSectionItem.jsx` (line 22, `entity-card-tag-chip`/
`entity-card-tag-overflow` for card-level tag chips) — confirmed live.
**These are entity-agnostic: confirmed working verbatim for Pipelines too**
(`PrivatePipelinesList.jsx` → `RightInfoPanel.jsx` → `Categories.jsx`, same
component tree), with ZERO new EliteaUI testid work needed. Before assuming
a new "tag filter" case on any entity (Agents, Toolkits, MCPs, Credentials)
needs `add-data-testid` work, check whether that entity's list page already
renders `Categories.jsx`/`RightInfoPanel.jsx` — if so, the testids are
already there; only page-object methods (`filter_by_tag`/`clear_tag_filter`/
`get_card_tags`, mirror `SkillsListPage`) are missing.
See `test-specs/pipelines/l2_pipeline-tags-add-and-filter_ELITEA-2013.md`.

Discovered while analysing ELITEA-1740 (Search Skills by Tag, localhost:5173):

- **The Skills-list page-header "Tags" panel (`EliteaUI/src/components/
  Categories.jsx`) genuinely filters the grid** — this is a *different*
  component from the name-search box documented in
  `skills_list_search_quirks.md` (issue #44). Clicking a tag chip:
  - Updates the URL with `?tags[]=<tag-name>`.
  - Re-fires the grid-fetching endpoint with the tag's **numeric id**:
    `GET .../elitea_core/skills/prompt_lib/{project}?...&tags=<id>&...`
    (e.g. `tags=2` for `formatting`) — this endpoint is the SAME one that
    issue #44 proved never re-fires for the name-search box, so the two
    mechanisms diverge exactly at whether they drive this endpoint.
  - Grid correctly narrows: a tag shared by 2 skills returns both; a tag
    unique to 1 skill returns just that one; skills with no matching tag
    (or no tags at all, like the pre-existing `automated-test-explainer`)
    are excluded.
  - "Clear all" (only rendered while a filter is active, via a `Tooltip
    title="Clear all"` wrapping an `IconButton`) genuinely restores the
    full, unfiltered grid and drops the `tags[]` param.
- **No defect** — all 3 filter scenarios (shared tag, two different unique
  tags) and the clear-restore case passed exactly as specified. No console
  errors during any of it.
- **Neither the tag-filter chip nor "Clear all" carry a `data-testid`.**
  Used `page.get_by_role("button", name=tag_name)` scoped to the panel
  below the search input (heading "Tags") — worked unambiguously since tag
  names are unique per project in this run. Not a blocker for automation,
  just flag to `add-data-testid` if a future page ever needs to disambiguate
  two same-named chips in different panels.
- **Tag entry on the create/edit form** (Formik `TagEditor` backed by
  `AutoCompleteDropDown`) — type text + Enter creates a new tag chip;
  previously-created tags (project-scoped) surface as clickable
  `get_by_role("option", name=...)` items in an autocomplete dropdown for
  later skills. A single cosmetic React dev-mode console warning (`sx` prop
  on a raw `<svg>`, from `TagEditor`'s `SvgCheckedIcon`/`ListItemIcon`) fired
  once when selecting an existing tag from that dropdown — no functional
  impact, not filed.
- Full AFS: `test-specs/skills/l3_search-skills-by-tag_ELITEA-1740.md`
  (status `ready-for-automation`).
