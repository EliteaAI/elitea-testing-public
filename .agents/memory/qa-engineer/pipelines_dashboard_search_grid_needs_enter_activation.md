---
name: Pipelines dashboard search grid needs Enter activation
description: PipelinesListPage.search() only fills the box; grid filter needs Enter/send-icon, per shared SearchBar.jsx
type: feedback
---

`automation/pages/pipelines_list_page.py::search()` (as merged, pre ELITEA-2023)
only does `search_input.fill(query)` — no Enter, no send-icon click. Confirmed
live against `SearchBar.jsx` (shared by Pipelines/Agents/MCP/Credentials/
Toolkits/Skills dashboards): typing alone only updates local input state and
opens a real, API-backed **suggestions popover** (`SuggestionList.jsx`, 500ms
debounce) — it does NOT touch the underlying dashboard grid. The grid-narrowing
dispatch (`onSearch()` → redux `setQuery` + `navigateWithTags`) fires ONLY on
`Enter` (`onKeyDown`) or a click on `data-testid="search-send-button"`.

Practical effect: the merged `TestSearchPipeline::test_search_pipeline_by_name`
/ `test_search_pipeline_no_results` tests pass, but via the suggestions
popover matching, not the grid actually filtering — so they don't prove what
their docstrings claim ("Search and filter pipelines by name" = the dashboard
list). Confirmed live: typed "YAML" + waited past debounce → grid unchanged
(11 pipelines); pressed Enter → grid narrowed to exactly 1 match.

Sibling list pages already have the correct fix — copy their pattern instead
of re-deriving it: `automation/pages/mcp_list_page.py::search()` (types,
`press("Enter")`, waits network + ~1.5s settle) and
`automation/pages/credentials_list_page.py`. `search-clear-button` testid
exists on Pipelines too but has no `PipelinesListPage` LocatorDescriptor field
yet — add one before using it.

Checked for the sibling "clear-from-zero-match-search redirects to /create"
defect (`#585` MCP, `#551` Credentials) — Pipelines does NOT reproduce it;
clearing a zero-match search correctly restores the full grid and stays on
`/pipelines/all`. Don't assume every `SearchBar.jsx`-based list has this bug —
check each one live before filing a sibling.

Case-text pattern: any case implying "type X → grid filters live" for a
dashboard using this shared component is case-text drift, not a defect — file
a `[CLARIFICATION]` (see `#1114` for Chats, `#1302` for Pipelines/ELITEA-2023)
rather than `defect-found`.

AFS: `test-specs/pipelines/lextend_pipeline-dashboard-search-filter-and-clear_ELITEA-2023.md`.
Digest: `test-specs/pipelines/_surface.md` § "Dashboard search — typing alone
does NOT filter the grid".
