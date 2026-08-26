---
name: allure.issue TMS link filename — resolve it on disk, never derive it
description: TMS case slugs are named independently of AFS/case titles; derived @allure.issue URLs 404. Resolve on disk before committing; 116/588 suite links are dead.
type: feedback
aliases: [allure issue link, TMS case link 404, dead test case link]
tags: [area/traceability, type/gotcha]
updated: 2026-08-24
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

## Why it keeps happening (7 occurrences, all caught at review, never by a run)

A dead link never fails a test — it only 404s in an Allure report — so nothing
in the loop catches it except a human reviewer. The seven:

| Case | Derived from | Real slug differed by |
|---|---|---|
| ELITEA-2609 (PR #1475) | case title, hand-typed | missing `and-` |
| ELITEA-2612 (PR #1479) | the **AFS** filename slug | a wholly different slug |
| ELITEA-1836/1837/1838 (2026-08-21) | an invented `…file-tree-behavior-…` shape applied to all three | three different real slugs |
| ELITEA-1848 + ELITEA-1850 (2026-08-22) | the **AFS** filename slug again (1849's happened to coincide and resolved, masking the pair) | `all-files-` not `delete-all-`; `close-x-modal-keeps-items` not `close-x-on-delete-confirmation` |
| ELITEA-1810 (PR #1678, 2026-08-23) | the case **title** / AFS slug (`…via-folder-icon-retention-policy`) | real slug is `…path-2-verify-retention-policy` — the TMS names the case by its *path-2* framing; nothing in the title or the AFS hints at it |
| ELITEA-1942 (PR #1739, 2026-08-24) | the case **title** / AFS slug (`…filter-by-type-remote`) | real slug ends `-remote-only` — the TMS encodes the *scope* qualifier the title omits |

Occurrences #1, #2, #5 and #6 also survived the first fix round untouched — the
expensive failure mode. #5 is the sharpest lesson: this very entry already
existed and was still not consulted, because it carried **no `MEMORY.md` index
line** — a fact that must change your FIRST move is worthless unindexed. Indexed
2026-08-22.

A partially-correct set is its own trap: when 1 of 3 links happens to resolve,
nothing about the spec *looks* wrong. Check every link, not a sample.

## Standing guards (copy the pattern, one file per spec-set)

- `automation/tests/unit/test_skill_agent_interaction_allure_issue_links.py`
- `automation/tests/unit/test_artifacts_tree_specs_allure_issue_links.py`
- `automation/tests/unit/test_artifacts_delete_all_specs_allure_issue_links.py`
- `automation/tests/unit/test_artifacts_bucket_retention_spec_allure_issue_link.py`
- `automation/tests/unit/test_mcp_type_filter_spec_allure_issue_link.py`

Each parses `@allure.issue` URLs with `ast` (handles adjacent-string-literal URL
wrapping), asserts each path resolves in the sibling clone, and skips cleanly
when the clone is absent.

## Suite-wide scale — re-measured 2026-08-23, against freshly fetched `origin/main`

**116 of 588 `@allure.issue` TMS links across the merged suite do not resolve**
(~20%; was 115/420 on 2026-08-21 — the absolute count barely moved while the
link count grew, i.e. new units are mostly clean and the debt is historic).
Two distinct causes, both invisible to any test run:

1. **TMS folder restructuring** — e.g. `settings-analytics/` became
   `settings/analytics/`; the case file exists, the path in the URL does not.
2. **Invented / derived slugs** — the per-case class in the table above.

Scan it against `origin/main` of the sibling clone (no network beyond a fetch,
and immune to a stale working tree): `git ls-tree -r --name-only origin/main`
into a set, then regex every spec's `blob/main/(tests/….md)` after collapsing
adjacent string literals (`re.sub(r'"\s*\n\s*"', '', src)`) and report the
paths not in the set.

This is pre-existing, suite-wide traceability debt, not one unit's mistake, and
per-spec guard files will never close it — a repo-wide parametrized guard would
ship RED on 116 pre-existing links, so it needs a **dedicated tech-task**
(scan + fix + guard in one unit), never a drive-by addition to a case branch.
Until then the manual `ls | grep` above is the only defence.
