---
name: ELITEA-1790 max-5-skills rework testid map
description: agent-add-skill-button already exists on automation/testids (draft #540, same as ELITEA-1789) — a first grep pass can falsely read "needs-adding" if it stops at a coincidental same-line-number match instead of doing a repo-wide git grep for the exact testid string
type: project
---

## Context

Rework pass (2026-07-15) on `test-specs/skills/lp1_max-5-skills-per-agent_ELITEA-1790.md`
after a framework-alignment audit found 3 raw non-testid handles in the
merged PR #48 implementation:

1. `page.get_by_role("button", name="Skill", exact=True)` — Skills-section
   "+ Skill" add button, enabled state
2. `page.locator('[aria-label="Maximum number of skills reached"] button')` —
   same button, disabled state
3. `page.locator('[aria-label="Maximum number of skills reached"]')` —
   wrapper span, used only to read the tooltip/aria-label text

## The self-correction (important methodology note)

My first provenance check ran `git grep -n "Maximum number of skills reached"
origin/main` and `automation/testids`, got a match at the same line number
(162) on both refs, and concluded "no data-testid anywhere in this file on
either ref" from a partial file dump — **wrong**. `agent-add-skill-button`
DOES exist on `automation/testids`, added at line 180 by draft EliteaUI#540
("test: [EL-1735] add data-testid hooks for agent-skills attach/mention
flow", branch `testids/ELITEA-1735-skills-testids`, still DRAFT). It sits a
few lines below the tooltip-title ternary I happened to grep, so my
same-line-number match was a false "these files are identical" signal.

**Lesson: grep for the exact candidate testid string itself, repo-wide,
before concluding "needs-adding."** A match on unrelated nearby text is not
evidence the rest of the file is unchanged. This project's own prior memory
(`elitea_1789_version_selector_rework_testid_map.md`) had already recorded
that #540 adds `agent-add-skill-button` — cross-check existing memory
entries for the same component before re-deriving provenance from scratch.

## Corrected provenance (verified via `git grep` + `gh pr list`, fresh fetch)

- `agent-add-skill-button` (covers BOTH the enabled and the disabled state —
  same `<BaseBtn>` node in `SkillMenu.jsx`, only the `disabled` prop toggles):
  `on-automation/testids only (draft EliteaUI#540)`. Not on `origin/main`.
  No `add-data-testid` run needed — just switch the raw handles to
  `LocatorDescriptor(testid="agent-add-skill-button")`. Test can run/pass
  locally now; promotion to `main`-targeted CI blocked until #540 merges.
- Wrapper `<span aria-label="Maximum number of skills reached">` — no
  additional testid needed. It's the immediate DOM parent of the
  testid-located button; read the `aria-label` via a one-hop parent
  traversal off `agent-add-skill-button` rather than requesting a second
  testid purely for attribute-reading.
- `skill-instructions-editor-content` (used by the shared `_create_skill`
  helper, not specific to this case): `on-automation/testids only (draft
  #526)`, absent from `origin/main` — pre-existing, unrelated dependency,
  re-confirmed here per the fresh-ground-truth rule.

## Reusable fact

`agent-add-skill-button` is the same testid documented in the ELITEA-1789
rework memory — any case touching the Agent-detail Skills "+ Skill" button
(1789, 1790, and likely 1791/1792/1793/1735 too) shares this one handle and
this one promotability dependency (#540).
