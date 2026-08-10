---
name: Agent Hub My Liked filter - DOM removal assertion fix
description: Step 10 must verify agent card removed from 'My Liked' DOM via count check + .count() == 0
type: feedback
---

## Case: ELITEA-2364 (My Liked filter shows only liked agents)

**Blocking finding (Fix Round 1):** Step 10 was missing an explicit DOM assertion for agent card removal.

### What was wrong
- Test only verified like-state changed (`data-liked='false'`)
- Never checked if card was actually REMOVED from the filtered view DOM
- AFS § Step 6 requirement: "card immediately disappeared from the 'My Liked' view"
- Code had a try/except that swallowed removal failures silently

### What the fix adds
1. Capture initial `agent_card_count()` before unlike
2. Call `wait_for_agent_card_count_not(initial_count)` — wait for count to decrease
3. Assert `get_agent_card(agent_name).count() == 0` — explicit DOM removal check
4. Keep `is_agent_liked()` check (already correct)

### Why this matters
The optimistic update must remove the card from the filtered view immediately. A test that only checks state-attribute changes but not DOM removal would miss regressions where the card stays visible with wrong state.

### Locator discipline applied
- `get_agent_card()` — returns a Locator for all matching cards
- `.count() == 0` — native Playwright assertion, zero cards match
- `wait_for_agent_card_count_not()` — existing AgentHubPage method, uses `expect(...).not_to_have_count()`

All handles use page-object methods (testid-only), no fallback.
