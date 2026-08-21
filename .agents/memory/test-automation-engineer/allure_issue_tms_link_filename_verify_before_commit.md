---
name: allure.issue TMS link filename — resolve it on disk, never derive it
description: TMS case slugs are named independently of AFS/case titles; derived @allure.issue URLs 404. Resolve on disk before committing; 115/420 suite links are dead.
type: feedback
aliases: [allure issue link, TMS case link 404, dead test case link]
tags: [area/traceability, type/gotcha]
updated: 2026-08-21
---

## The rule

**Never derive a TMS case filename** — not from the case title, not from the AFS
filename, not from a sibling spec's URL shape. TMS slugs are named
*independently* of both. Resolve the real name on disk before typing it into an
`@allure.issue` URL (the sibling clone is mandatory per `.agents/architecture.md`
— no network needed):

```bash
ls ../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/<feature>/ | grep -i <ELITEA-id>
```

And when a reviewer flags this class, **grep your own diff for the exact string
before claiming it fixed** — an "addressed" round with no line touching the
decorator reads as a skip, and reviewers treat it as one.

## Why it keeps happening (4 occurrences, all caught at review, never by a run)

A dead link never fails a test — it only 404s in an Allure report — so nothing
in the loop catches it except a human reviewer. The four:

| Case | Derived from | Real slug differed by |
|---|---|---|
| ELITEA-2609 (PR #1475) | case title, hand-typed | missing `and-` |
| ELITEA-2612 (PR #1479) | the **AFS** filename slug | a wholly different slug |
| ELITEA-1836/1837/1838 (2026-08-21) | an invented `…file-tree-behavior-…` shape applied to all three | three different real slugs |

Occurrences #1 and #2 also survived the first fix round untouched — the
expensive failure mode.

## Standing guards (copy the pattern, one file per spec-set)

- `automation/tests/unit/test_skill_agent_interaction_allure_issue_links.py`
- `automation/tests/unit/test_artifacts_tree_specs_allure_issue_links.py`

Both parse `@allure.issue` URLs with `ast` (handles adjacent-string-literal URL
wrapping), assert each path resolves in the sibling clone, and skip cleanly when
the clone is absent.

## Suite-wide scale — measured 2026-08-21, against freshly fetched `origin/main`

**115 of 420 `@allure.issue` TMS links across 282 specs do not resolve** (~27%).
This is a pre-existing, suite-wide traceability debt, not one unit's mistake, and
per-spec guard files will never close it. The fix is one **parametrized repo-wide
guard** walking every spec's decorators — proposed to the lead as a tech-task;
until it exists, the manual `ls | grep` above is the only defence.
