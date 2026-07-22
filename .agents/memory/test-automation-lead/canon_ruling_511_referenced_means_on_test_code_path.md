---
name: Canon ruling #511 — "referenced" means called on the test's actual code path
description: A testid wired into a page-object method that the test never calls is NOT "referenced" for checklist item 2; no carve-out for reusable scaffolding, parameterized methods reused by sibling cases with other args, or "plausible future use." Structural locator-disambiguation pairs (#277) are a distinct axis.
type: feedback
---

**Ruling (Aliaksandr, 2026-07-22, on issue #511):** Option 1 — no carve-out.
Checklist item 2's "every added testid must be referenced by the case's
test/page-object diff" means the test **actually invokes** the page-object
method that uses the testid, on the case's executed code path. A
`LocatorDescriptor` field wired into a real, callable method that the test
never calls is NOT "referenced" — same FAIL bar as an orphan testid with zero
consuming methods anywhere.

## Why

- **The metric is presence-based.** Testids in the codebase are supposed to
  correspond to elements tests actually depend on. A testid wired into a
  never-called method depends on nothing — it fails the metric's definition,
  not just its letter.
- **"Wired into a page-object method" is trivial to game.** If that's the bar,
  "unused testid" becomes an empty category — every convenience add gets
  laundered through a one-line method. Option 2 (carve-out for reusable POM
  scaffolding) doesn't tighten the rule, it dissolves it.
- **Option 3 (paperwork carve-out) has the same problem, slower.** A PR
  sentence naming "future case X" is cheap to write and impossible to enforce
  — nobody comes back six months later to check whether X shipped.
- **YAGNI + cheap reversal.** If a future case genuinely needs
  `switch_to_form_view()`, that case's PR adds the testid and the method — at
  which point the testid is genuinely used. No coverage lost by deferring.

## How to apply

- **In control audits:** a wired-but-uninvoked testid is a solo-FAIL on item 2,
  not a `question`. Grep for calls to the wiring method on the test's actual
  code path — a `.` after the field name in the test file (or a helper the
  test reaches). Zero call-site hits = FAIL. (See also
  [[orphan_testid_vs_wired_but_uninvoked]] — orphan is a fortiori covered.)
- **In implementer dispatch:** when the AFS names a testid you need to add
  inside a JSX array literal, add ONLY that one testid, not its siblings.
  Sibling adds "while I'm in the file" corrupt the coverage metric even when
  they compile.
- **In reviewer dispatch:** the mechanical grep for item 2 must be "grep the
  new testid's field name for `.` invocations on the test's call path," not
  "grep the testid for ANY reference." The stricter query catches the
  wired-but-uninvoked shape.
- **In `add-data-testid` skill use:** the skill now carries an explicit
  scope-discipline section and a checklist item that rejects "while I'm here"
  sibling adds. (Landed same commit as this memory.)

## Boundary

- **#277 is a distinct axis, still open.** Structural locator-disambiguation
  pairs (e.g. `entity-card-tag-chip` needs `entity-card-tag-overflow` alongside
  it so the used testid's locator is unambiguous — a genuine locator-honesty
  dependency, not a convenience add) are NOT covered by this ruling. Do not
  cite #511 to solo-FAIL a #277-shape delivery — it's a separate question the
  team hasn't answered yet.
- **A testid PROP on a shared component** (opt-in from the caller) is not
  affected — it renders nothing unless a caller passes it, so it can't
  corrupt the metric on its own.

## Concrete instances that now solo-FAIL under this ruling

- `#60/#511` (ELITEA-1922, PR #292/EliteaUI#554): `toolkit-form-view-toggle`
  wired into `McpFormPage.switch_to_form_view()`, test never calls it.
- `#298` (ELITEA-2095, PR #693): `chat-participants-badge-users` wired into
  parameterized `is_participants_badge_visible(section=...)`/
  `open_participants_popover(section=...)`, never called with
  `section="users"` anywhere in the test.
- `#317` (ELITEA-2114, PR #696): `chat-conversation-menu-make-public-menuitem`
  and `chat-conversation-menu-share-menuitem`, wired into a new same-PR
  `get_conversation_menu_item()` mechanism, never invoked with those two keys.

All three were flagged in their control-audit verdicts as "recommendation was
option 1, awaiting human ruling." That ruling now exists — retro-audit is not
needed (the verdicts already flagged them), but future occurrences are plain
solo-FAILs.

## Instructions tuned in the same commit

- `.agents/testing.md` — locator-strategy section now defines "referenced"
  explicitly, cites this ruling.
- `.agents/role-overrides.md` § Every role — "touches" now means "test
  invokes on its executed path," cites this ruling.
- `.claude/skills/add-data-testid/SKILL.md` — new "Scope discipline" section
  + explicit checklist item.
