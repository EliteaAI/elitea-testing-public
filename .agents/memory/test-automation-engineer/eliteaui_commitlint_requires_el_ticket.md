---
name: EliteaUI commits require an [EL-XXXX] subject token
description: commitlint on EliteaAI/EliteaUI rejects [ELITEA-1825]; only the short [EL-1825] form passes
type: reference
aliases: [commitlint, EliteaUI commit hook, testid commit rejected, EL-XXXX]
tags: [area/testids, type/gotcha]
created: 2026-08-21
updated: 2026-09-30
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

**`[EL-0000]` is the established form when there is no EliteaUI ticket** — the branch
history uses it for testid-only commits driven by a TMS case, with the ELITEA id in a
parenthetical instead (`test: [EL-0000] add Help Center page-load testids (ELITEA-2219)`,
`test: [EL-0000] add Analytics chart tooltip testids (ELITEA-2326/2327/2328)`). Don't
invent an EL number you can't point at.

## The SECOND rule, which fires on the same commit (2026-09-30, ELITEA-2219)

`body-max-line-length` / `footer-max-line-length` from `@commitlint/config-conventional`
cap **every** body and footer line at **100 characters**. A long trailing reference is
the usual offender — a single `AFS: test-specs/help-center/l3_…_ELITEA-2219.md` path at
107 chars failed the commit with `footer's lines must not be longer than 100 characters`.

So a detailed testid commit body needs BOTH: the `[EL-…]` subject token **and** every
line hard-wrapped under 100. Cheapest way to not discover this twice per commit — write
the message to a file, check it, then `git commit -F`:

```bash
awk 'length > 95 {print FILENAME":"NR": "length" chars"}' /tmp/msg.txt   # expect no output
git commit -F /tmp/msg.txt
```

Note both rules are checked at `commit-msg`, i.e. AFTER `lint-staged` has already run
and re-staged — see the lint-staged note above, and
[[never_amend_after_a_failed_husky_commit_on_shared_branch]].

`lint-staged` also runs `eslint --fix` + `prettier --write` on staged `*.{js,jsx}`
before the message check, so a rejected commit has already reformatted and re-staged
the file — just re-run `git commit` with a fixed subject, no re-`git add` needed.

Related: [[project_briefing]]
