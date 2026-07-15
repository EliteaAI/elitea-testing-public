---
name: Ghost skill mention popper + participants popper quirks (implementer)
description: SUPERSEDED by the ELITEA-1793 testid rework (issue #35, PR #284) — all raw get_by_role/xpath-ancestor handles below were replaced with testid-only locators. Escape-dismiss leaving the literal "~" in the input is still true and still handled the same way. See ghost_skill_participant_popper_quirks section "Rework update" for the current shape.
type: feedback
---

## Rework update (2026-07-15, issue #35 / PR #284) — read this first

The raw-handle gotchas documented below (sections 1-2, and the "Reusable
pattern") describe the **pre-rework** state of `chat_page.py` (merged PR
#52) and are now **obsolete** — the framework-alignment audit flagged all
of PR #52's handles as testid-policy violations, and the rework
(elitea-testing-public PR #284) replaced every one of them:

- `open_participants_popover()` now clicks
  `PARTICIPANTS_BADGE.format(section)` → `PARTICIPANTS_BADGE_BUTTON`
  (scoped) and returns `self.participants_popper`
  (`chat-participants-popper` testid) — no more `p`-tag+text-filter or
  `ancestor::div[3]` walk.
- `remove_agent_participant()` signature changed from `agent_name: str` to
  `agent_id: int` — it resolves the row directly via
  `PARTICIPANT_ROW.format(f"application_{agent_id}_{project_id}")`
  (`getChatParticipantUniqueId()`'s shape, confirmed by reading
  `participants.helpers.js`), no more `get_by_text(agent_name)` +
  `ancestor::div[2]`.
- `open_mention_skill_popper()` / `is_mention_popper_open()` now just wait
  on `self.mention_skill_list` (`skill-mention-list` testid) — no more
  `get_by_text("Mention skill")` + ancestor walk.
- `is_skill_in_mention_popper()` tries `MENTION_SKILL_ITEM.format(name)`
  first, then falls back to `MENTION_SKILL_ITEM_PREFIX` (a
  `[data-testid^="skill-mention-item-"]` prefix-match constant) +
  `.filter(has_text=...)` for description-substring checks.
- `is_mention_popper_empty_state()` now checks `MENTION_LIST_EMPTY`
  (`skill-mention-list-empty` testid) instead of `get_by_text(...)`.

**Section 3 below (Escape leaves the literal "~") is still accurate and
unchanged** — that's a product-behavior fact, not a locator technique, so
the rework didn't touch it.

Full testid map + the dynamic-testid-evades-literal-grep lesson:
`.agents/memory/qa-engineer/elitea_1793_participant_removal_testid_map.md`.

---

## [OBSOLETE — pre-rework] Original context

Implementing ELITEA-1793 ("Ghost skill not shown after Agent participant
removed") — a `defect-found` AFS with a confirmed, deterministic (2/2)
product defect (issue #51: the "Mention skill" popper retains a removed
agent's skill). Three implementer-side (infrastructure) gotchas surfaced
while writing `ChatPage.open_participants_popover()` /
`remove_agent_participant()` / `open_mention_skill_popper()` that the
analyst's manual/live-tool exploration couldn't have caught the same way:

## 1. [OBSOLETE] `get_by_role("paragraph", ...)` matches 0 elements, even when the live a11y tree shows role "paragraph"

`playwright-cli snapshot` (and any accessibility-tree dump) will show a
plain `<p>` element as `paragraph [ref=...]: Agents` — but calling
`page.get_by_role("paragraph", name="Agents", exact=True)` in real
Playwright code returns **0 matches**, confirmed live via `run-code`. The
snapshot's "paragraph" role label does not correspond to a role Playwright's
`getByRole` engine recognizes/matches for a bare `<p>`. Don't trust the
snapshot's structural-role labels (paragraph, generic, etc.) as if they were
`getByRole`-queryable ARIA roles — only roles from the real ARIA spec
(button, menuitem, dialog, heading, ...) are reliably queryable that way.
This whole workaround is now moot: `chat-participants-popper` resolves the
popper directly, no text-based lookup needed at all.

## 2. [OBSOLETE] Popper container ancestor depth had to be verified live, per popper

The "Mention skill" popper's container used to be `ancestor::div[2]` from
its heading, and the "Agents" participants popper's container was
`ancestor::div[3]` — different depths, confirmed by walking ancestor
chains to a first-common-ancestor via `run-code`. Now both poppers resolve
via their own testid (`skill-mention-list` / `chat-participants-popper`) —
no ancestor-walk of any kind remains in either code path.

## 3. Escape-dismissing the mention popper leaves the literal "~" in the input — retyping "~" without clearing first breaks the trigger

**Still true post-rework — not a locator issue, a product-behavior fact.**
Dismissing the "Mention skill" popper via Escape does NOT clear the
composer input — the literal `~` character remains. If a later step types
`~` again without clearing first, the input ends up `~~`, which does
**not** re-trigger the popper (confirmed live: screenshot showed literal
`~~` in the composer with no popper open, causing a false-negative 10s
timeout). `open_mention_skill_popper()` still does `Control+a` +
`Backspace` before every `press_sequentially("~")` so the trigger is
always a single fresh `~` regardless of prior composer state.

## [OBSOLETE] Reusable pattern

The text-based ancestor-walk pattern this section described has been fully
replaced by testid-based resolution (see "Rework update" above). The
Escape/`~~` handling in section 3 is the only part of this entry still in
effect.
