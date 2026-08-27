---
name: A test owns its preconditions — never borrow pre-existing project data
description: Reading a precondition out of whatever data happens to pre-exist inverts the test — it passes on a dirty environment and fails on a clean one
type: feedback
---

## The rule

**If a case needs N entities, the test creates N entities.** Never satisfy a
precondition by looking one up in the target project's existing data
("any pre-existing skill will do"). A test that reads data it did not create
**passes when the environment is dirty and fails when it is clean** — exactly
backwards, and it fails in CI (where projects are clean by design) while
staying green locally forever.

## How it bit us (ELITEA-1790 / #1811, repaired 2026-08-27)

The merged, promoted test needed 6 distinct Skills. It created 5 and looked
the 6th up in the project, filtering out (a) its own 5 ids and (b) its own
naming prefix. Locally that filter had 82 candidates, so the local gate was
green for weeks. On the DEV CI project — where all 18 specs in the `skills`
job create and delete their own data — the filter selected nothing and the
precondition assertion fired before a single case step ran. Four consecutive
`dev-stable` `main` runs failed identically.

Creating the 6th cost **one extra form fill** (~20 s on a ~2 min test).

## Two traps to avoid when fixing this

1. **A conditional skip is worse than the red.** `pytest.skip` when the
   precondition is absent would fire on *every* clean project — permanent
   green-by-absence, while the TMS back-write claims `execution_type:
   automated` for a case nobody exercises. Banned as defect masking.
2. **Seeding a permanent fixture entity into the CI project by hand** just
   relocates the unowned precondition into an environment nobody
   version-controls. The next cleanup sweep re-breaks it, silently.

## Companion rule: run-unique names for anything matched by name

If any downstream step selects or verifies **by name** (attach poppers,
`is_skill_attached()`, list filters), test-data names must be run-unique —
`f"el1790-{uuid4().hex[:8]}-s{n}"`. Fixed literal names collide with orphan
debris from hard-killed runs (whose `finally` cleanup never ran) and produce a
**false-positive match against a stranger's entity** that no assertion can
catch. Mind the create-form validation: lowercase letters / digits / hyphens,
max 32 chars, no leading or trailing hyphen.

## Check before the case text lets you off

Read the case's own **Test Data** table before deciding a precondition must be
borrowed. ELITEA-1790's said "Number of Skills to create: **6**" and its Step 1
read "**Create** or confirm 6 distinct Skills" — the case authorised creation
outright. The borrowed-lookup shape was the drift, not the fix.
