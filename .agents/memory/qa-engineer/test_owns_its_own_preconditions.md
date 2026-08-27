---
name: A test must own its own preconditions — borrowed pre-existing data fails on clean projects
description: A test that reads a precondition out of pre-existing project data passes when the env is dirty and fails when it is clean — the inverted signal
type: feedback
aliases: [unowned precondition, borrowed test data, pre-existing skill lookup, clean project failure, environment precondition]
tags: [area/test-design, type/anti-pattern]
created: 2026-08-27
updated: 2026-08-27
---

## The anti-pattern

A test needs N entities. It creates N-1 and **looks the last one up** among whatever
already exists in the project. This inverts the signal: the test **passes when the
environment is dirty and fails when it is clean**.

Worked case: ELITEA-1790 (`test_agent_max_five_skills_limit`, issue #1811). The case
needs 6 Skills; the test created 5 and filtered the project's skill list for a 6th.
Green locally forever (project 399 has 82 qualifying skills), red on **4 consecutive**
DEV CI runs — the CI project is clean by design, because every other spec in the same
job creates and deletes its own data. The one thing that would have made it pass on CI
is another test failing to clean up.

## Tells, before it ever goes red

- The test reads a list endpoint (`list_*`) in **setup**, not in an assertion.
- A `next((x for x in all_items if <not mine>), None)` + `assert ... is not None`.
- The AFS has a `reuse-existing` test-data row for something the case says to *create*.
- The precondition assertion's message explains what the *environment* owes the test.

## The fix, and the two wrong fixes

- **Right:** the test creates every entity its preconditions name, through the same
  interface the case specifies, and deletes all of them. Check the case text first —
  "**Create** or confirm N …" is explicit authority to create.
- **Wrong 1 — conditional `pytest.skip` when the precondition is absent.** It fires on
  every clean env, so the case reports green-by-absence forever while the TMS carries
  `execution_type: automated`. Masking; banned by `.agents/profile.md` § Bug filing.
- **Wrong 2 — hand-seed a permanent fixture entity into the CI project.** Moves the same
  unowned precondition into something nobody version-controls.

## Companion: fixed test-data names are the other half

Fixed entity names (`elitea-1790-skill-2`…) collide with debris from hard-killed runs
(the `finally` never ran). Then name-filtered popper selection and name-based
`is_skill_attached()` start reading a stranger's entity. **Run-unique names**
(`f"el1790-{uuid4().hex[:8]}-s{n}"`, ≤32 chars, lowercase/digits/hyphens) close the whole
class, and — unlike deleting other people's orphans — stay inside the test's own contract.

Related: [[skill_form_and_export_import_quirks]]
