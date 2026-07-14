---
name: Skills list tag filter quirks
description: Skills-list page-header "Tags" panel IS a working, separate filter mechanism (unlike the broken name-search box, issue #44); tags= numeric-id query param; no testids on chip/Clear-all
type: feedback
---

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
