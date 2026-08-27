---
name: allure.issue link slug can drift from real TMS filename
description: verify the @allure.issue URL resolves to the actual TMS case file, not a plausible-looking slug
type: feedback
---

## What happened (ELITEA-2064 review, PR #1370)

The implementer's `@allure.issue(...)` decorator built its URL from a
hand-typed slug: `ELITEA-2064_attach-pipeline-as-tool.md`. The real file in
`onetest-ai-tm-Elitea/tests/automated-full-regression-ui/pipelines/` is
`ELITEA-2064_pipeline-attach-pipeline-as-tool.md` (the case's own title-slug,
"Pipeline — Attach Pipeline as Tool" → `pipeline-attach-pipeline-as-tool`).
The typed slug just dropped the leading `pipeline-`. Every OTHER sibling test
in `tests/ui/pipelines/` (checked: 2056, 2030, 2038, 2048, 0860) got this
right — this was a one-off typo, not a convention gap.

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
