---
name: A Fidelity Declaration's "the seeded value is never asserted" clause needs a grep, not a read
description: The declaration is a claim about the CODE — verify it against the assertions, the way you verify a Coverage-Map row
type: feedback
aliases: [fidelity declaration, seed never asserted, transit substitution, project_context_seed]
tags: [area/review, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## The trap

A transit-substitution row typically ends with a sentence like *"the seed's TEXT is
never asserted; every observable is produced by the product"*. That sentence is what
makes the substitution transit rather than terminal — so it is a **claim about the
implementation**, exactly like a Coverage-Map `already-covered` row, and it earns the
same treatment: grep the spec for the seed constant instead of reading the prose.

Worked instance (ELITEA-2275, PR #1796): both the AFS § Fidelity Declaration and the
module docstring said "The seeded TEXT is never asserted", while the spec's final
assertion was `expect(editor_lines()).to_have_text([SEED_CONTENT])` — the seed
constant, verbatim. Substantively harmless (the case's observable is button state, and
the value round-trips through the real server), but the declaration was false, and a
false declaration is the artifact three later gates trust.

## The check (cheap, one command)

```bash
grep -nE 'SEED[_A-Z]*|<the seed constant>' automation/tests/<spec>.py
```

Any hit inside an `expect(...)`/`assert` is a contradiction of a "never asserted"
clause. Two acceptable fixes, both one-liners: read the baseline off the PRODUCT after
navigation and compare against that (the ELITEA-2274 pattern in the same batch does
exactly this), or amend the declaration to say what is actually asserted and why it is
still transit.

Related: [[seeded_precondition_can_swallow_a_case_step_action]] ·
[[coverage_map_row_can_partially_overclaim_one_clause]]
