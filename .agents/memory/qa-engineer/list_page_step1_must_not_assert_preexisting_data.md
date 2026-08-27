---
name: A list-page "dashboard loads" step must never assert pre-existing rows
description: Localhost has leftover data, DEV shard users own zero — a "at least one card exists" Step-1 assertion is green locally and red on DEV, and the case never asked for it
type: feedback
aliases: [empty dashboard, assert [], zero agents, shard user, pre-existing card, dashboard loads]
tags: [area/list-pages, type/fidelity]
created: 2026-08-27
updated: 2026-08-27
---

## The pattern

A Step 1 of the shape *"Navigate to the X dashboard → the dashboard loads"*
tempts you into asserting that the list has CONTENT:

```python
assert x_list_page.get_card_names(), "should render at least one existing card"
```

That assertion is **test-invented environment state**, not case content, and it
is a latent DEV-only red:

- **localhost** — one shared identity, never torn down, always has leftovers
  (Agents/`Private` 399 held 20 during the ELITEA-1901 repair). Always green.
- **dev.elitea.ai** — GHA shards run as per-shard users (`autotest_user_N`), and
  every well-behaved spec seeds + cleans up its own entity, so **between tests
  the project is legitimately empty**. `assert []` → red.

Worked case: ELITEA-1901 (`test_import_agent_valid_md_file.py:149`), GHA run
32931571484, board #1813. The TMS Step 1 expected result was only *"The Agents
dashboard loads"* — the assertion was never asked for, so deleting it costs no
coverage.

## The replacement — a data-independent load oracle

Assert the page **shell** plus that the list region reached a *terminal,
non-error* state — never a row count:

1. the page-heading testid is visible **and** has the expected text;
2. the control the next step acts on is visible;
3. **`entity-card-name` OR `empty-state-title` is visible** — a disjunction, as
   one class-level constant so it stays testid-only and greppable:
   ```python
   LIST_SETTLED_SELECTOR = (
       '[data-testid="entity-card-name"], [data-testid="empty-state-title"]'
   )
   ```

Why (3) is stronger than the row-count check it replaces: `CardList.jsx:40-42`
gates BOTH renders behind `!isLoading` and the empty state additionally behind
`!isError`, so the disjunction cannot pass while the list is still loading or
has errored — whereas `get_card_names()` returns `[]` on timeout and cannot
tell "genuinely empty" from "failed to load"
(see [[list_page_getter_timeout_swallow_masks_load_failure]]).

Card rendering itself still gets verified — later, on an entity **the test
itself created**, which is where it belongs.

Applies to every `CardList.jsx`-based page (Agents, Skills, Pipelines,
Toolkits, MCP, Credentials, Applications). `empty-state-title` is a generic
shared-component testid, on `origin/main`, already bound in
`mcp_list_page.py` and `toolkits_list_page.py`.

Related: [[empty_state_preconditions_unreachable_on_localhost]] ·
[[list_page_getter_timeout_swallow_masks_load_failure]]
