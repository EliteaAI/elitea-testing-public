---
name: SearchBar activation is submit-based, not live-filter
description: Shared SearchBar.jsx (agent-search-input testid) filters only on Enter/send-icon click, never on typing (issue #44); MIN_SEARCH_KEYWORD_LENGTH=3 blocks queries below 3 chars; grid search matches DESCRIPTION text too, not just name — short/common substrings are unsafe partial-search test terms
type: feedback
---

`EliteaUI/src/components/SearchBar.jsx` — the shared search box component
behind `data-testid="agent-search-input"` (used on `/skills/all`, `/agents/all`,
likely others) is **submit-activated, not live-filtering**:

- `onChange` (`handleInputChange`) only updates local `searchString` state —
  no fetch, no grid re-filter.
- `onKeyDown`: `Enter` → `onSearch()`.
- The send-icon (`StyledSendIcon`, right-aligned, only visible once text is
  present) → `onClick={onSearch}`.
- `onSearch` dispatches `actions.setQuery(...)` → `navigateWithTags(...)`,
  which is what actually triggers the entity list endpoint
  (`.../skills/prompt_lib/...?query=...`) to refetch.
- A separate, unrelated endpoint (`.../search_options/...?query=...`) fires
  on every keystroke regardless — but it only feeds a quick-jump
  Tags/Skills suggestion popover, not the main grid. Don't confuse the two
  when reading Network tab evidence.
- The cancel/X icon clears both the input and the grid filter correctly.
- Neither the cancel nor send icon has an `aria-label` — they're invisible
  to the accessibility tree/snapshot; to interact with them programmatically
  you have to locate the `<svg>` by DOM traversal from the input testid (walk
  up ~3 parents, `querySelectorAll('svg')`) and tag a temp id for a real
  Playwright click, rather than relying on accessible name/role.

**Why this matters:** issue #44 was initially reported (and by me,
independently re-confirmed) as "search box doesn't filter the grid" by only
testing live typing. Both were wrong — re-testing with real Enter keypress
and a real icon click showed the grid filters correctly via either intended
mode. Root cause of the false-positive: never checked the component source
before verdicting. Per `.agents/role-overrides.md`'s interaction-discovery
ladder (step 6, source read, is decisive), any "doesn't update on typing"
report on this project should grep the placeholder/label text in
`../EliteaUI/src` and check for `onKeyDown`/submit-icon handlers **before**
confirming a live-filter assumption as a bug.

## Two more findings, surfaced during ELITEA-1739 test-data corrections

- **`MIN_SEARCH_KEYWORD_LENGTH = 3`** (`EliteaUI/src/common/constants.js`)
  blocks `onSearch()` from dispatching ANY query below 3 characters, on
  BOTH activation modes — shows a "must be at least 3 letters" toast
  instead, grid stays unfiltered. Verified the exact boundary live: a
  3-char term (`cod`) fires the fetch correctly, a 2-char term (`Co`)
  never does. Any partial-search test data must use terms ≥3 characters.
- **The grid-fetching endpoint (`GET .../elitea_core/skills/prompt_lib/
  {project}?...&query=<text>`) matches on DESCRIPTION text too, not just
  NAME.** Discovered while picking an ELITEA-1739 partial-search term:
  query `ter` unexpectedly matched `automated-test-explainer` (via
  "interaction" in its description) and unrelated `elitea-1793-ghost-skill`
  fixtures (via "after" in theirs) — neither name contains "ter". Not
  filed as a defect (full-text search across name+description is
  plausibly intentional product behavior), but it means **short/common
  substrings are unsafe partial-search test terms** in any shared or
  long-lived environment — prefer a distinctive, full word verified clean
  against every other skill's name AND description over a generic 3-gram.
  Full write-up in `skills_list_search_quirks.md` and
  `test-specs/skills/l3_search-skills-by-name_ELITEA-1739.md` Known
  Defects Clarification #5.
