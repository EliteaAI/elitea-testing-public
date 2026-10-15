---
name: Skill-attach popper lists unfiltered, server-sorted, PAGE_SIZE=20 — a Skill created before a bulk-API batch falls off page 1
description: AgentDetailPage.attach_skill()'s "+ Skill" popper is driven by SkillMenu.jsx -> useSkillListQuery with no search query by default, server-sorted created_at desc at a fixed PAGE_SIZE=20 (skillsApi.js) — any caller that bulk-creates many OTHER skills between creating a target skill and attaching it via the UI risks pushing that skill off page 1, where attach_skill()'s .filter(has_text=...) times out
type: feedback
---

## The trap

`AgentDetailPage.attach_skill(skill_name)` opens the "+ Skill" popper and
selects a menuitem by `.filter(has_text=skill_name)` against
`[data-testid="toolkit-menu-item"]` — but it never types into the popper's own
search field. The popper's item list comes from `SkillMenu.jsx`'s
`useSkillListQuery({projectId, params: {query: debouncedSearch}})`, and
`debouncedSearch` is `''` unless something actually drives the search input.
Unfiltered, the list is server-sorted `created_at desc` and paginated at a
fixed `PAGE_SIZE = 20` (`src/common/constants.js`, `skillsApi.js`'s
`skillList` query). Already-attached skills are excluded client-side, but
nothing re-ranks the *unattached* ones by recency relative to each other —
they are simply whatever is on page 1 of the raw list.

**Concretely:** if a test creates skill X via the UI, then creates 49 more
skills via the API (a bulk-setup phase, e.g. for a dynamic attach-limit test),
then tries `attach_skill("X")` — X is no longer among the 20 most-recently
created skills in the project, the popper never renders it, and
`option.wait_for(state="visible", timeout=...)` in
`Popper.select_menuitem_by_testid()` times out with no indication of *why*
("waiting for ... .filter(has_text=\"X\") to be visible" — looks like a flake,
not an ordering bug).

## The fix (ELITEA-1790, 2026-10-15 adjustment, issue #2443)

Create the Skill you are about to attach through the UI **last**, immediately
before the `attach_skill()` call — i.e. after any bulk-API skill-creation
batch, not before. That keeps it the single most-recent skill in the project,
which is what keeps it on page 1 regardless of how many other skills exist.

Do **not** "fix" this by making `attach_skill()` search first — it has 8
merged callers relying on its current unfiltered-popper behavior
unchanged, and none of them has this problem (none bulk-creates dozens of
other skills mid-test). Reordering your OWN test's skill creation is the
correct, additive-only fix; mutating the shared method is not.

If a future case genuinely needs to attach a Skill that ISN'T the most recent
(e.g. attaching an old, pre-existing skill in a large project), the actual fix
is a new sibling method using `Popper.search(popper, skill_name, page)` before
selecting — mirroring how `Popper.select_menuitem_by_testid` already has a
raw-`select_menuitem` sibling for the same "don't touch the shared caller"
reason. `Popper.search()` already exists and works (confirmed: `SkillMenu.jsx`
passes its debounced `search` state straight into the list query).

Related: `[[agent_skill_remove_control_quirks]]`, `[[skill_name_validation_contract]]`
