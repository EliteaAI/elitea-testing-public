---
name: allure.issue link slug can drift from real TMS filename
description: verify the @allure.issue URL resolves to the actual TMS case file, not a plausible-looking slug
type: feedback
aliases: [allure issue link, TMS link 404, case filename slug]
tags: [area/review, type/recurring]
updated: 2026-08-23
---

## What happened (ELITEA-2064 review, PR #1370)

The implementer's `@allure.issue(...)` decorator built its URL from a
hand-typed slug: `ELITEA-2064_attach-pipeline-as-tool.md`. The real file in
`onetest-ai-tm-Elitea/tests/automated-full-regression-ui/pipelines/` is
`ELITEA-2064_pipeline-attach-pipeline-as-tool.md` (the case's own title-slug,
"Pipeline — Attach Pipeline as Tool" → `pipeline-attach-pipeline-as-tool`).
The typed slug just dropped the leading `pipeline-`. Every OTHER sibling test
in `tests/ui/pipelines/` (checked: 2056, 2030, 2038, 2048, 0860) got this
right — this looked like a one-off typo at the time. **It is not — see § Recurring below.**

Confirmed via `gh api repos/EliteaAI/onetest-ai-tm-Elitea/contents/<slug>` →
404 for the wrong slug, 200 for the real one. The mechanical grep for
non-testid handles and the additive-only page-object grep both catch nothing
here — this is a link-content defect, invisible to every existing mechanical
check.

## The check (cheap, ~1 tool call)

When a diff adds/touches an `@allure.issue(...)` decorator whose URL points
into the TMS repo, verify the file actually exists at that path before
approving:

```bash
gh api repos/EliteaAI/onetest-ai-tm-Elitea/contents/tests/automated-full-regression-ui/<module>/<slug>.md
```

or, if the TMS repo is checked out locally, just `ls`/`find` the directory
and diff the slug against what's actually there. Do this whenever the PR is
new (not carrying forward a previously-verified link) — it costs one API call
and would have caught this on the first pass.

## Recurrence (ELITEA-2609 review, PR #1475) — same FILE, one commit later

`test_skill_agent_interaction.py`'s ELITEA-2607 sibling test had exactly this
bug (`allure.issue` filename with a wrong `-functionality` suffix) and it was
caught + fixed in that same PR's round-1 review (fix commit `c83ca52a`,
same branch lineage this PR built on). The very next test added to the SAME
file (ELITEA-2609, one PR later) reintroduced the identical class of defect:
linked `skills/ELITEA-2609_skill-explicit-autonomous-invocation-coexistence.md`,
real file is
`skills/ELITEA-2609_skill-explicit-and-autonomous-coexistence.md` (confirmed
via local `onetest-ai-tm-Elitea` clone `ls`). Fixing the bug once in a file
does not inoculate the next test written into that file — check the link on
every `@allure.issue` addition, even in a file that just got this exact fix.
Classified **blocking** here (CHANGES_REQUESTED), consistent with how the
2607 sibling treated it one round earlier in the same file — supersedes the
"not blocking, cosmetic" call in `allure_issue_tms_link_path_drift.md` (a
different PR/file); this project's own review history on this exact file
already set the precedent as blocking.

## Recurrence #3 (ELITEA-2612 review, PR #1479) — different file, same batch

`test_skill_edit_with_ai_navigation_error_handling.py` linked
`skills/ELITEA-2612_edit-with-ai-navigation-error-handling.md` (confirmed 404
via `gh api`); the real file is
`skills/ELITEA-2612_edit-with-ai-skill-navigation-and-errors.md` (confirmed
200). Implementer's own daily-log entry claimed "no live drift, no new gotcha
class" for this case despite this — the check is genuinely never automatic,
it has to be re-run by hand on every `@allure.issue` addition regardless of
how routine the PR looks. Three occurrences across two different files in one
batch (skills-remaining-w4) — worth proposing as a pre-commit/CI grep
(`gh api .../<slug>.md` for every new `@allure.issue` line in a diff) rather
than relying on review to keep catching it.


## Recurring — it is a CONVENTION GAP, not a typo (updated 2026-08-23)

Occurrences to date: ELITEA-2064, ELITEA-1848, ELITEA-1850, and now
**ELITEA-1810** (PR #1678, review round 2) — spec:191 shipped
`ELITEA-1810_create-artifact-bucket-via-folder-icon-retention-policy.md`
(derived from the AFS's own slug) while the real TMS file is
`ELITEA-1810_create-artifact-bucket-path-2-verify-retention-policy.md`.

The three guard unit tests the earlier rounds produced
(`test_artifacts_delete_all_specs_allure_issue_links.py`,
`test_artifacts_tree_specs_allure_issue_links.py`,
`test_skill_agent_interaction_allure_issue_links.py`) each pin ONE named spec
file, so a **new** spec is never covered by any of them — which is why this
keeps reaching review. A repo-wide guard (walk every `tests/ui/**` spec, AST-read
each `@allure.issue` URL, resolve against `../onetest-ai-tm-Elitea`) would
retire the class; worth a `question` card to the lead.

**Reviewer check, one command, run on every test PR that adds a spec:**

```bash
ls ../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/<area>/ | grep -i <CASE-ID>
```
Compare against the filename in the `@allure.issue(...)` URL. Never trust the
AFS slug — the AFS filename and the TMS filename are independently authored.
