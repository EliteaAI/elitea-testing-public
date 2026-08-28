---
name: A "duplicated with attribution" helper can silently drop the fix the original encodes
description: When a spec copies a suite-local helper "per the same convention", diff it against the original — the copy may reintroduce the anti-pattern the original was written to remove.
type: feedback
aliases: [duplicated helper, suite-local helper, attribution copy, _open_blank_composer, _poll_blank_state_holds]
tags: [area/review, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

This suite shares chat helpers by **per-file duplication with attribution**
(`_open_blank_conversation` → `_open_genuinely_blank_conversation` →
`_open_blank_composer`, …). Each copy's docstring cites its ancestor, which
reads as provenance and invites a reviewer to accept it as "the established
shape".

It is not. A copy can be a REGRESSION of its ancestor:

- `_open_genuinely_blank_conversation()`
  (`automation/tests/ui/chat/test_team_users_mention_and_remove_participants.py`)
  exists precisely because a *fixed sleep-then-recheck-once* loses a race with
  the SPA's last-viewed-conversation restore. Its `_poll_blank_state_holds()`
  polls both signals across the settle window and says so in the docstring.
- `_open_blank_composer()` in
  `automation/tests/ui/settings/test_context_settings_new_conversations_only.py`
  (settings-w08, ELITEA-2390) cites that helper as its ancestor — and then uses
  `chat.page.wait_for_timeout(1500)` + one recheck: the exact shape the ancestor
  documents as inadequate, and a `.agents/conventions.md` § Hard don'ts violation
  (`No sleep/waitForTimeout — framework waits only`).

## Reviewer move

When a diff adds a helper whose docstring says "duplicated with attribution
from X" / "lighter sibling of X": **open X and diff the bodies**, don't read
only the new one. Ask what the ancestor's extra machinery was FOR. The
attribution line is a claim about lineage, never evidence of equivalence —
same class as § *precedent is not authority* in `.agents/role-overrides.md`.

Related: [[teardown_that_reads_a_page_it_may_not_be_on]]
