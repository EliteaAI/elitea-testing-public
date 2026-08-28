---
name: Fixing a promoted spec on main only gets reverted at promotion
description: main and automation/base can hold different variants of the SAME spec file — fix both or the fix dies at promotion
type: feedback
aliases: [main vs automation/base, promoted test repair, spec variant drift, port the fix, repair branch strategy]
tags: [area/branching, type/lesson]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

A `[Fix]` card for an already-promoted test says *branch from `main`, PR to
`main`* — correct, and incomplete. `automation/base` is hundreds of commits
ahead and may carry a **different, longer variant of the same spec file**
(unpromoted work by later cards adding tests to it). Land the repair only on
`main` and the next promotion overwrites it with the unfixed variant. The fix
dies silently, months later, attributed to nobody.

Worked case, 2026-08-28 (#1891 / ELITEA-2037):
`test_pipeline_mcp_node_fresh_attach.py` was **264 lines on `main`, 674 on
`automation/base`** — one `open_mcp_popper()` call site vs three.

## The move

Before opening the repair PR:

```bash
git show origin/main:<path> | wc -l
git show origin/automation/base:<path> | wc -l
```

Different → the port is part of the job, not a follow-up. After merging to
`main`, `git merge origin/main` into `automation/base` (the normal sync) and
verify the spec actually merged sensibly — the extra call sites may need the
same treatment.

## Run the matched control before attributing anything

The port surfaces reds that were already there. Prove it rather than assume it:

| | pristine `origin/automation/base` | after the merge |
|---|---|---|
| the spec file | 3 failed | 1 passed, 2 failed |

Strictly better, pre-existing reds isolated and carded separately. One extra
invocation converts *"my merge broke base"* into evidence. Same discipline the
`#1082` entries in `.agents/testing.md` demand.

## Trap inside the trap

"The second `open_mcp_popper()` call is cached, so it needs no wait" is **false
across tests** — each test gets its own `page` fixture, so its first open is a
cold cache. Judge per test, not per file.

Related: [[sibling_fix_cards_can_have_different_root_causes]] · [[verify_handles_and_values_against_main_not_the_working_tree]]
