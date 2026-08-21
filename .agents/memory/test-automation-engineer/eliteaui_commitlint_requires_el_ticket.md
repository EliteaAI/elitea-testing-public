---
name: EliteaUI commits require an [EL-XXXX] subject token
description: commitlint on EliteaAI/EliteaUI rejects [ELITEA-1825]; only the short [EL-1825] form passes
type: reference
aliases: [commitlint, EliteaUI commit hook, testid commit rejected, EL-XXXX]
tags: [area/testids, type/gotcha]
created: 2026-08-21
updated: 2026-08-21
---

## The gate

`EliteaAI/EliteaUI` runs husky `commit-msg` → commitlint with a
`function-rules/subject-empty` rule whose message is
`subject must container ticket number - [EL-XXXX]`.

- `test: [ELITEA-1825] add data-testid …` → **REJECTED** (the long TMS id does not match).
- `test: [EL-1825] add data-testid …` → **accepted**.

So when committing a testid for TMS case `ELITEA-<n>`, write the subject with the
SHORT `[EL-<n>]` form. `.agents/workflow.md` § Testid flow already shows this shape
(`test: [EL-1737] …`) — it is a hard gate, not a style preference.

`lint-staged` also runs `eslint --fix` + `prettier --write` on staged `*.{js,jsx}`
before the message check, so a rejected commit has already reformatted and re-staged
the file — just re-run `git commit` with a fixed subject, no re-`git add` needed.

Related: [[project_briefing]]
