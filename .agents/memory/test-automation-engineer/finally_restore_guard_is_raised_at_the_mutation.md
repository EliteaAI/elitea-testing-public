---
name: A finally-restore guard flag is raised AT the mutation, never after its assertions
description: Any statement between a shared-state mutation and its `..._changed = True` guard is a path where a flake skips the restore but teardown still deletes
type: feedback
aliases: [default_changed, cleanup guard, finally restore, teardown flag, restore_section_default]
tags: [area/test-design, type/review-finding]
created: 2026-08-29
updated: 2026-08-29
---

## The rule

When a spec mutates shared project state and guards its `finally` restore with a
boolean, the assignment goes on the line **immediately after the mutating call** —
never after the assertions that verify the mutation.

```python
form.save_and_return_to_list()   # creating a Vector Storage ASSIGNS it as the default
default_changed = True           # <- here, before ANY assertion
providers_page.isolate_section(...)
expect(providers_page.card_for_model(name)).to_have_count(1)
```

## Why it is not cosmetic

Found on PR #1989 (ELITEA-2400). The flag sat four statements after the create. The
`finally` deletes the configuration **unconditionally** but restores the default only
`if default_changed` — so a flake in any of those four statements deletes the
configuration that had just become the project's default, and never puts the old one
back. The shared seeded project is then left with NO default, and the sibling specs
(ELITEA-2399/2401) assert an existing default up front, so they all refuse to run. One
flake would have taken out the whole family, days later, far from the cause.

The tell was asymmetry: the two sibling specs in the same PR set the flag on the very
next line.

## The check

Ask of every guard flag: *what is the widest window between the mutation and the flag?*
Everything in that window is a leak path. Note the inverse is equally wrong — hoisting
the flag ABOVE the mutation makes the restore run on paths that never changed anything.

Pinned statically (AST over the spec source, no browser needed) by
`automation/tests/unit/test_default_changed_guard_is_set_at_the_mutation.py`, which
checks both directions. `test_teardown_restores_are_strict_on_success_path.py` is the
same genre for a different teardown defect — reach for that pattern whenever a review
finding is a control-flow SHAPE rather than a value.

A flag that gates an *assertion* rather than a restore (`body_completed`) is
deliberately late — the rule is about restores.

Related: [[settings_ai_providers_project_switch_and_default_traps]]
