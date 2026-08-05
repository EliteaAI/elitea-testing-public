---
name: Component-level testid must not share a prefix selector
description: New dynamic testid on a shared component can accidentally match an existing prefix-based selector (^=), double-counting elements.
type: feedback
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
