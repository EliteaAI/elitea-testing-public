---
name: Component-level testid must not share a prefix selector
description: New dynamic testid on a shared component can accidentally match an existing prefix-based selector (^=), double-counting elements.
type: feedback
aliases: [prefix count, ^= selector overcounts, testid family count]
tags: [area/testids, type/gotcha]
updated: 2026-09-30
---

When adding a **new** component-level dynamic testid to a shared component that
already has an existing `columnTestIdPrefix`/similar mechanism (e.g.
`GridTableHeader.jsx`), check whether any EXISTING page-object selector uses a
**prefix match** (`[data-testid^="…"]`, e.g. `COLUMN_HEADER_PREFIX_SELECTOR =
'[data-testid^="user-column-header-"]'`) before naming the new testid.

Concrete case (ELITEA-2292 fix round 2): `admin_users_page.py`'s
`get_column_header_count()` counts elements matching
`[data-testid^="user-column-header-"]` to assert "exactly 5 columns". A new
sort-indicator-icon testid named `${columnTestIdPrefix}-column-header-${field}-sort-icon`
(mirroring the header-cell testid's shape) also starts with
`user-column-header-`, so the SAME prefix selector picked it up too — every
sortable column silently added +1 to the header count (5 real headers + 3
sort icons = 8, test asserted `== 5` and correctly went red).

**Fix:** name the new testid so it does NOT share a prefix with any existing
prefix-matched selector — here, `${columnTestIdPrefix}-sort-icon-${field}`
instead of tucking `-sort-icon` onto the end of the header-cell shape.

**Preventive check before naming any new dynamic/component-level testid:**
`grep -n '\^="' automation/pages/<page>.py` (or the specific page object you're
extending) — if a prefix selector exists, the new testid must not start with
that same prefix unless it is semantically one of that selector's members.

## The other direction: a prefix COUNT you write yourself (2026-09-30, ELITEA-2219)

The same collision bites when you add a **family** of testids and then count them with
`^=`. Naming a card root `help-center-card-{category}` plus sub-elements
`-title` / `-description` / `-icon` makes `[data-testid^="help-center-card-"]` match
**20 nodes for 5 cards**, not 5 — the AFS specified that selector for an "exactly 5
cards" assertion and it was simply wrong (measured live).

CSS cannot express "prefix but no further suffix", so the options are a `:not()` chain
(`:not([data-testid$="-title"]):not(...)`, which must then be kept in sync with every
sub-element you ever add) or a **1:1 proxy**. Proxy is better: count the `-title` nodes
(`[data-testid^="help-center-card-"][data-testid$="-title"]` → exactly 5), since the
component renders exactly one title per card by construction, and an extra testid added
inside a card later cannot perturb it. Catch a RENAMED member with the per-member root
assertions you already have, not with the count.

**Rule of thumb:** a `^=` count is only as precise as the naming family beneath it. Before
writing one, list every testid that shares the prefix — including the ones you are adding
in the same commit.
