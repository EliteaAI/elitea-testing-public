---
name: Skills list search quirks
description: Skills-list search box (shared "agent-search-input" testid) never filters the grid — issue #44; AgentsListPage.agent_exists_in_list() is unscoped and would miss the same bug; native value-setter needed to reliably clear the input
type: feedback
---

Discovered while analysing ELITEA-1739 (Search Skills by Name, localhost:5173):

- **The Skills-list page-header search box does NOT filter the Skills grid at
  all**, in any state (partial match, exact match, non-existent match, or
  cleared). Confirmed via full network log: `GET .../elitea_core/skills/
  prompt_lib/{project}?...&query=...` (the grid-fetching endpoint) fires
  exactly once, at initial page load, with `query=` always empty — no
  keystroke ever re-triggers it. Typing instead only drives a **separate**
  endpoint, `GET .../elitea_core/search_options/prompt_lib/{project}?
  query=<text>&entities[]=tag&entities[]=skill...`, which populates an
  unrelated Tags/Skills "quick-jump" popover below the search box — the grid
  itself is completely unaffected. Filed:
  github.com/EliteaAI/elitea-testing-public/issues/44.
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
  (status `defect-found`).
