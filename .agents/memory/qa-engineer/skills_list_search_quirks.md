---
name: Skills list search quirks
description: Skills-list search box (shared "agent-search-input" testid) only filters the grid on Enter/send-icon (issue #44 closed not-planned — onChange deliberately doesn't fetch); MIN_SEARCH_KEYWORD_LENGTH=3 blocks queries below 3 chars; grid search matches DESCRIPTION text too, not just name; AgentsListPage.agent_exists_in_list() is unscoped; native value-setter needed to reliably clear the input
type: feedback
---

Discovered/corrected across three analyst passes on ELITEA-1739 (Search
Skills by Name, localhost:5173):

- **The grid DOES filter — but only on Enter or the send-icon click, never
  on plain keystrokes.** An early pass mis-read this as "search never
  works" and filed issue #44 as a MAJOR defect; reading
  `EliteaUI/src/components/SearchBar.jsx` showed this is intentional:
  `onChange` only updates local component state (no fetch); `onKeyDown`
  fires `onSearch()` on Enter; the send-icon's `onClick={onSearch}` does
  the same. Issue #44 closed "not planned". A **separate** endpoint,
  `GET .../elitea_core/search_options/prompt_lib/{project}?query=<text>&
  entities[]=tag&entities[]=skill...`, fires on every keystroke (debounced)
  and populates an unrelated Tags/Skills "quick-jump" popover — independent
  of the grid-fetching `GET .../elitea_core/skills/prompt_lib/{project}?
  ...&query=<text>` endpoint, which only fires on the two intended
  activation events.
- **`MIN_SEARCH_KEYWORD_LENGTH = 3`** (`EliteaUI/src/common/constants.js`)
  blocks `onSearch()` from dispatching ANY query below 3 characters, for
  BOTH activation modes — shows a "must be at least 3 letters" toast
  instead, grid stays unfiltered. A 2-char partial term (e.g. the ELITEA-1739
  case's literal "Co") can never narrow the grid; pick partial-search test
  terms ≥3 chars.
- **The grid search endpoint matches on DESCRIPTION text too, not just
  NAME** — a real, previously-undocumented mechanism found while choosing
  ELITEA-1739's Step 2 partial term. Query `ter` unexpectedly matched
  `automated-test-explainer` (via "interaction" in its description) and
  unrelated `elitea-1793-ghost-skill` fixtures (via "after" in theirs),
  despite neither name containing "ter". Not filed as a defect (full-text
  search across name+description is plausibly intentional), but it means
  **short/common substrings are unsafe partial-search test terms** in any
  shared or long-lived environment — prefer a distinctive, full word
  (verified clean against every other skill's name AND description) over a
  generic 3-gram.
- That popover's own matching logic is also not simple substring matching:
  query `"Co"` matched `automated-test-explainer` (no literal "co" in the
  name) while excluding `formatter` — noted in the AFS but not filed as a
  second issue since the primary defect (grid never filters) already makes
  the case un-automatable as written.
- **The search input's testid is `agent-search-input` even on `/skills/all`**
  — it's the same shared component used by `AgentsListPage`
  (`automation/pages/agents_list_page.py`), just reused verbatim on the
  Skills page. Works functionally, just a naming smell if a Skills-specific
  testid is ever wanted.
- **`AgentsListPage.agent_exists_in_list()` is unscoped** —
  `page.locator(f'text="{name}"').first` matches text anywhere on the page,
  including the (non-functional, for Skills) suggestions popover. This means
  the existing `test_agent_search` / `test_agent_search_no_results` tests in
  `test_agent_management.py` would NOT catch the equivalent grid-not-filtering
  bug if it exists on the Agents page too (not verified — out of scope for
  ELITEA-1739, but worth a follow-up look before trusting those tests as
  proof the Agents grid actually filters). Any new Skills-search page-object
  method must scope strictly to `entity-card-name` cards in the grid, not
  reuse this loose pattern.
- **Clearing this search input reliably is harder than it looks**: both
  Playwright's `.fill("")` and a `Control+a` + `Delete` keyboard sequence were
  unreliable in this exploration — one attempt left stale text concatenated
  with newly typed text (`"Coformatter"`), and `Control+a` only removed one
  character instead of selecting the full value. What worked: setting the
  input's value via the native `HTMLInputElement.prototype.value` setter and
  dispatching a bubbling `input` event, e.g.
  `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,
  'value').set.call(el, ''); el.dispatchEvent(new Event('input',
  {bubbles:true}))`. If `AgentsListPage.clear_search()` (which currently just
  calls `self.search_input.fill("")`) is reused for a Skills search test,
  verify it doesn't hit the same flakiness.
- Full AFS: `test-specs/skills/l3_search-skills-by-name_ELITEA-1739.md`
  (status `ready-for-automation` after 3 amendments — activation-mode
  correction, then min-length correction by the implementer, then this
  entry's description-matching fix restoring the case's genuine
  partial-match assertion via a `code-reviewer` → `content-reviewer`
  rename sharing `content` with `content-writer`).
