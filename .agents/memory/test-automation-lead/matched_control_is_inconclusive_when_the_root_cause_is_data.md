---
name: A local matched control CANNOT reproduce a CI red whose root cause is a DATA precondition
description: A green control is expected, not exoneration — ask what the root cause depends on before running one, and say "inconclusive by construction" out loud
type: feedback
aliases: [control run inconclusive, data precondition control, green control is not exoneration, project data differs from CI]
tags: [area/triage, area/gating, type/process]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

`control_run_before_blame.md` and the `#1082` discipline say: run the pristine-`main` control before
assigning blame. Correct — but a **green** control only exonerates the diff when the failure could
have occurred locally in the first place.

#2180 (ELITEA-2024): I swapped the spec to its `origin/main` pre-repair version, everything else
identical, same DEV target. It **PASSED** — `1 passed in 22.61s`, `reruns.json == {}`. That proves
nothing about the CI red, because #2118's root cause is a **data precondition**: the CI matrix project
holds zero pipelines, and `main`'s Step 7 (`assert list_page.get_card_names()`) is a pure function of
ambient project data. My `.env.test` points at `ELITEA_PROJECT_ID=399`, which holds pipelines ⇒ green
here, red there, **by construction**. CI's project id is a repo secret (`ELITEA_PROJECT_ID_DEV` in
`test-ui-dev-stable.yml`), so the difference cannot be closed locally at all.

## The rule

**Before running a matched control, ask what the root cause DEPENDS ON.**

| Root cause depends on | Control verdict |
|---|---|
| code (a page object, a shared helper, a wait) | conclusive — this is the #2175 case, run it |
| **environment-scoped data** (project contents, seeded entities, org settings, roles) | **inconclusive by construction** |
| build mode (dev vs production React) | inconclusive — see `env_scoped_sanctioned_red.md` |

When it is inconclusive, still run it (it is cheap and rules out the code axis) but **write the words
"inconclusive by construction" in the record**, with the reason. A green control left unqualified reads
to the next person as "the CI red wasn't real", which is the opposite of the truth.

## Same family

`env_scoped_sanctioned_red.md` (#1892/#2082, ELITEA-2354/#2166) asks the mirror question: *can this
failure physically OCCUR on the environment you gated on?* Data-precondition control and
environment-scoped sanctioned RED are the same question pointed in opposite directions.
