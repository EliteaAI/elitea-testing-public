---
name: Agent Hub / Skill Hub Catalog — a bulk fetch's row count != rendered card count
description: AgentCategorySection.jsx (and its Skill-Hub analogue) only renders each category's first INITIAL_CARD_DISPLAY_COUNT items initially — "Show more" hides the rest. Never wait for DOM card count == bulk response row count; wait for "any card visible" instead.
type: feedback
---

## What happened (ELITEA-2363, PR #1230, review fix round)

Fixing a genuine "baseline read races the async fetch" reviewer finding, the
first attempt waited like this:

```python
applications = agent_hub.navigate_and_capture_applications(timeout=NAVIGATION_TIMEOUT)
agent_hub.wait_for_agent_card_count(len(applications), timeout=UI_ELEMENT_TIMEOUT)  # WRONG
baseline_cards = agent_hub.get_visible_agent_card_names()
```

This failed immediately and deterministically:

```
AssertionError: Locator expected to have count '46'
Actual value: 23
```

`navigate_and_capture_applications()`'s bulk response genuinely returns
**every** published agent (46 rows this session) — but the Catalog only
**renders** each category's first `INITIAL_CARD_DISPLAY_COUNT` items on
initial load (`AgentCategorySection.jsx`):

```js
const visibleItems = useMemo(() => items.slice(0, displayCount), [items, displayCount]);
```

The rest sit behind a "Show more" toggle per category. So response-row-count
and rendered-card-count are simply **two different numbers by design** —
comparing them isn't a race fix, it's asserting the wrong invariant.

## The fix

Don't wait for an exact count when you don't actually know what the correct
count is. Wait for the WEAKEST signal that's still sufficient: "at least one
card is visible" (`AgentHubPage.wait_for_any_agent_card()`, a plain
`.first.wait_for(state="visible")` on the existing `AGENT_CARD_PREFIX`
constant). This works because all the per-category buckets are set via
separate `dispatch()` calls issued synchronously inside the SAME fetch
`.then()`/async continuation, and React 18 batches those into one commit —
so by the time any card renders, every category's initial slice has already
landed in that same commit. No card-count arithmetic needed.

## Generalize

If you ever need "the initial render finished" as a wait condition on this
Catalog (Agent Hub `/elitea-catalog`, and check the Skill Hub analogue before
assuming it's identical — `useSkillHubData.hooks.js` uses the same
`fetchAllAndCategorize` naming, worth a quick grep for its own
`INITIAL_CARD_DISPLAY_COUNT` usage before reusing this exact reasoning
there): reach for "first matching element visible", not "count equals N" —
unless N is a number you can independently prove is the number that WILL be
rendered (e.g. after a search/clear where you already captured that number
from a PRIOR settled DOM read, as `wait_for_agent_card_count`/`_not` do
correctly elsewhere in this same page object, comparing DOM-to-DOM, not
DOM-to-raw-response).

See also: never_assume_a_transition_settled.md (rule 5 — a different flavor
of the same "network resolved != DOM you're about to read reflects it" family,
that one about which of several PARALLEL requests you waited on, this one
about MAPPING a resolved response's own payload shape to the wrong DOM metric).
