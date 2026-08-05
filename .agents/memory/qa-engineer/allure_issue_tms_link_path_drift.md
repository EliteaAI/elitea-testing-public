---
name: allure.issue TMS link path drift
description: allure.issue() TMS-case links in test_personal_token_create_and_verify.py use a stale path/slug that doesn't match the real onetest-ai-tm-Elitea repo layout
type: feedback
---

`test_personal_token_create_and_verify.py`'s `@allure.issue(...)` decorators
(ELITEA-2280, ELITEA-2284, ELITEA-2286 — confirmed on all three, review of
PR #1177) all link to
`.../tests/automated-full-regression-ui/settings-personal-tokens/ELITEA-<id>_<slug>.md`
— a flat directory with a hyphenated name and a slug that doesn't match the
title. The **real** path in `onetest-ai-tm-Elitea` is a nested directory,
`tests/automated-full-regression-ui/settings/personal-tokens/` (slash, not
hyphen), and the filename slug is auto-derived from the case title verbatim
(e.g. `ELITEA-2286_token-name-validation-only-alphanumeric-characters-underscor.md`,
not `...-invalid-characters-rejected.md`). All three links in this file are
dead (404 on GitHub).

Not blocking on review — it's a cosmetic Allure-report traceability link,
inherited precedent (ELITEA-2280 introduced it, ELITEA-2284 and ELITEA-2286
both copied the same broken shape), doesn't affect test correctness or the
Coverage Map. But it should get fixed the next time this file is touched:
derive the link from `git -C ../onetest-ai-tm-Elitea log --oneline -1 --
'**/ELITEA-<id>_*'` (or just `find`) instead of guessing the slug/path from
the case title.
