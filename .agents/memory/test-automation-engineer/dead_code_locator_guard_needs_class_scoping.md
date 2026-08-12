---
name: Dead-code locator guard needs class scoping
description: Unreferenced-LocatorDescriptor guard's "class scoping" must key off a real import/instantiation, not a bare class-name substring
type: feedback
---

## Round 3 update — bare substring scoping still false-passes

Round 2's fix below reads as a real fix but isn't one: scoping files by
`if CLASS_NAME in text` still collides with any file that merely **mentions**
the class name in a comment/docstring (`agents_list_page.py` has `# ...
CredentialsListPage/SkillsListPage/McpListPage; ...`), which pulls that
WHOLE file — and its own same-named fields — into scope. A fresh-session
reviewer traced this statically in round 2 review and it reproduced live in
round 3: `SkillsListPage.toast_dismiss_button` (added ELITEA-2438, dead on
this page) was masked the whole time because `chat_page.py` mentions
"SkillsListPage" in a comment and separately defines+uses its OWN
`toast_dismiss_button`.

**Round 3 fix:** scope by a REAL usage regex — the import line
(`from pages.X import ClassName`) or an instantiation call (`ClassName(`) —
never a bare `ClassName in text` substring check. And don't just read the
fix: write a direct test for the scoping function itself against a
synthetic fixture tree reproducing the exact collision (an incidental-mention
file + a real-caller file), asserting the mechanism actually discriminates
them. Reading the scoping code and accepting it as sound is exactly how
round 2 shipped a fix that wasn't.

**Second-order lesson:** tightening a guard's scoping can retroactively
un-mask an OLDER, unrelated dead field that a looser version of the same
bug was hiding. Don't assume every guard-failure post-fix is caused by your
own change — check history (`git log -S<field>`) before reflexively
weakening the guard back down; if the field is genuinely dead, remove it
per the same precedent as the fields the guard was written to catch.

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
