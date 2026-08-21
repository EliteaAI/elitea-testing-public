---
name: allure.issue TMS link filename must be verified against the TMS repo
description: Specs invent a plausible TMS filename for @allure.issue; ls the cases dir — three shipped 404s in one PR
type: feedback
aliases: [allure issue link, tms case link, traceability link 404, onetest case filename]
tags: [area/review, type/traceability]
created: 2026-08-21
updated: 2026-08-21
---

## What happens

Every artifacts spec carries an `@allure.issue(...)` URL of the shape
`https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/<area>/<ELITEA-ID>_<slug>.md`.
The slug is NOT derivable from the case title — the TMS filenames drop words
("file-tree-subfolder-expands-collapses-on-click", not
"file-tree-behavior-subfolder-expands-and-collapses"). An implementer writing the
link from the case title produces a plausible-looking 404 that no gate catches:
Allure renders the link happily, pytest never fetches it.

Observed 2026-08-21, PR #1632 (ELITEA-1836/1837/1838): all three links wrong,
while every neighbouring artifacts spec's link matched exactly.

## Reviewer check (one command, do it on every spec-adding PR)

```bash
ls ../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/<area>/ | grep <ELITEA-ID>
# compare byte-for-byte with the filename in the spec's @allure.issue URL
```

Related: [[afs_filed_issue_claims_need_tracker_verification]]
