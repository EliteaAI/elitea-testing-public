---
name: Dead-code guard "class-name substring" scoping still false-passes
description: A regression guard scoped by `if CLASS_NAME in text` (not import/instantiation) still collides with sibling page objects sharing a field name — verify by hunting a live collision, not by reading the scoping code
type: feedback
---

## What happened (ELITEA-2428, round 2 review)

Round 1 flagged `SkillsListPage.table_view_button` as an unreferenced
`LocatorDescriptor` field that shipped past a freshly-added dead-code guard
(`test_skills_list_page_locator_inventory.py`) because the guard's original
reference search was a bare `\.{field}\b` grep over **every** `.py` file
under `automation/` — it counted `AgentsListPage`'s own
`self.table_view_button.click(...)` as "evidence" that `SkillsListPage`'s
field was referenced.

Round 2's fix scoped the search: only files containing the literal
substring `"SkillsListPage"` (plus the page object's own source) are
searched. This reads like a real fix and the PR/memory narrative claimed it
closed the gap. **It does not, in general.** `automation/pages/
agents_list_page.py` itself contains the substring `"SkillsListPage"` — in
an unrelated comment ("`CredentialsListPage/SkillsListPage/McpListPage;
entity-card-icon is …`", line ~225) — which pulls the WHOLE file into the
guard's search scope. `AgentsListPage` separately defines and uses its own
`card_view_button`/`table_view_button` fields (lines 47, 53, 411, 424, 437,
441, 452, 456). So if either of those two field names were reintroduced on
`SkillsListPage` with zero real callers, the general guard would still
false-pass — traced statically, not executed (reviewer is static-only). The
class-specific hardcoded regression pin the implementer also added
(`test_table_view_button_not_reintroduced_as_unreferenced_field`) happens to
catch that ONE named field, but that pin is a separate, non-generalizing
safety net — it does not validate that the general mechanism actually works.

## The check to run next time

When a "dead-code" or "unreferenced field" static guard claims to scope its
search "to files referencing class X": don't trust that the scoping code
merely EXISTS — grep for the class name as a bare substring across the repo
and check whether any of the hits are **incidental** (a comment, a
cross-reference docstring, an unrelated mention) in a file that ALSO
defines a same-named field on a *different* class. If so, the guard has the
exact same blind spot it was written to close, just narrowed. A sound
version needs to detect actual usage (an import line, `ClassName(page)`
instantiation, or a typed variable), not a bare substring of the class
name anywhere in the file's text.

## Why this is preventive

Any suite with multiple page objects sharing common field names
(`card_view_button`, `table_view_button`, `save_button`, `name_input`, …) —
which this repo has by design (`AgentsListPage`/`SkillsListPage`/
`McpListPage`/`PipelinesListPage` all mirror each other) — will re-trip this
exact false-pass the next time a "scoped" dead-code guard is added or a
field is reintroduced, unless the guard's scoping mechanism is verified
against a live sibling-class collision, not just read and accepted.
