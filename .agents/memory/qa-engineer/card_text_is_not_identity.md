---
name: Card text is not identity — volatile counters ride along in text_content()
description: A card's text_content() concatenates every child incl. live counters; use the id testid for identity
type: feedback
aliases: [like count in card text, text_content identity, agent card identity, catalog card name]
tags: [area/agent-hub, type/flake-rootcause]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

Reading a list item's identity via `text_content()` on its ROOT element silently includes every
descendant — including live, shared counters that nothing in the test controls.

Worked case: ELITEA-2363 (Agent Hub search) compared `restored_cards == baseline_cards` where each
"name" came from `locator(CARD_PREFIX).nth(i).text_content()`. `AgentCard.jsx` renders name +
author-initials avatar + `Like.jsx:70` `<Typography>{likes}</Typography>` inside one `<Card>`, so the
string was `name + initials + likeCount`. A sibling spec in the SAME suite liked a 0-like agent
(`find_zero_like_application()`, cleanup soft-asserted), the counter went 0→1, and CI read it as a
changed agent name (`...1f1c00TB0` → `TB1`).

**Fix: take identity from the element's own id-bearing testid** (`catalog-agent-card-{id}`), which is
immune to any content churn and needs no new testid.

## Two things that generalise

1. **A helper's docstring can carry the false premise that kills it.** This one said the like-count
   contamination was *"harmless … since no like state changes during this case"* — an assumption the
   spec had no power to enforce. When a docstring justifies an artifact by asserting what OTHER tests
   won't do, that is the bug, written down in advance.
2. **Check unique-vs-total before choosing `set()`.** The same grid rendered 27 cards but 24 unique
   ids (3 agents appear in Trending *and* their category). A `set()` comparison would have collapsed
   them and stopped detecting a genuinely dropped card. Sorted list / multiset is the safe default.

Related: [[ordering_deterministic_until_the_sort_key_moves]]
