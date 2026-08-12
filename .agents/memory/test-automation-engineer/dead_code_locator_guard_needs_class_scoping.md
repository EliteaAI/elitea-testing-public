---
name: Dead-code locator guard needs class scoping
description: Static-analysis guard for unreferenced LocatorDescriptor fields must scope its grep to files referencing the class, not all of automation/
type: feedback
---

## What happened (ELITEA-2428, fix round 1 → round 2)

A static-analysis regression test (`test_skills_list_page_locator_inventory.py`)
was added to catch unreferenced `LocatorDescriptor` fields on `SkillsListPage`
(the `entity_card_icon` dead-code finding). Its implementation grepped **every**
`.py` file under `automation/` for a bare `\.{field}\b` match to decide if a
field was "referenced".

That let a genuinely unreferenced `SkillsListPage.table_view_button` field ship
past the guard: `AgentsListPage` defines its **own** `card_view_button` /
`table_view_button` fields and uses them internally
(`self.table_view_button.click(...)`, `self.table_view_button.get_attribute(...)`
in `agents_list_page.py`). Those string-identical hits were counted as
"`SkillsListPage.table_view_button` is referenced" even though no file ever
wrote `<skills_list_page_var>.table_view_button` — the field had zero real
callers on `SkillsListPage`'s own test path.

## Fix

Scope the reference search to files that actually mention the owning class
name (`if CLASS_NAME in text: include`), plus the page object's own source
file unconditionally (so internal `self.<field>` usages inside its own
methods still count). Any file that never mentions the class can only
contribute a same-named-field false positive from a sibling page object.

## Why this is preventive

Any project with multiple page objects sharing common field names
(`card_view_button`, `table_view_button`, `save_button`, `name_input`, …) will
hit this exact false-pass the first time a dead-code guard like this is
written, unless the guard is scoped from the start. Check this BEFORE trusting
a "0 unreferenced fields" green from a freshly-added guard of this shape —
verify the guard's scoping, not just that it ran green.
