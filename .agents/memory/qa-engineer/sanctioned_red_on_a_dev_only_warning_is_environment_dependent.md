---
name: A sanctioned-RED whose signature is a React dev-build warning is environment-dependent
description: Verify a dev-only console signature statically (vite build + no NODE_ENV override) and check whether the spec ASSERTS the defect's presence or merely records it
type: feedback
aliases: [sanctioned RED green on DEV, dev-only console warning, is a green on DEV a mask, closed-set variant environment]
tags: [area/environment, type/failure-classification, area/review]
created: 2026-09-09
updated: 2026-09-09
---

## The review question

When a spec documented **sanctioned-RED** comes back GREEN from a different
environment, the reviewer's job is to decide: honest coverage, or silent loss?
Two checks settle it, and both are STATIC.

### 1. Can the signature structurally exist on that environment?

For a React dev-diagnostic signature (`Received \`true\` for a non-boolean
attribute`, `React does not recognize the \`%s\` prop`, `Maximum update depth
exceeded`) the chain to verify on `origin/main` of the UI repo is:

```bash
git show origin/main:package.json | grep -E '"build"|"react-dom"'   # "vite build", react-dom ^18.x
git show origin/main:vite.config.js | grep -nE "mode|NODE_ENV|define" # no NODE_ENV override, no forced mode
git show origin/main:.github/workflows/build_and_release.yml | grep "npm run"  # the released artifact IS that build
```

`vite build` defaults to `mode=production` -> `NODE_ENV=production` -> React
resolves `react-dom.production.min.js`, where those warnings are **compiled out**,
not suppressed. Three green links = the theory holds as far as static evidence
reaches. The link you canNOT close statically is that the deployment serves that
artifact — say so rather than claiming a live confirmation.

### 2. Does the spec ASSERT the defect, or merely RECORD it?

This is the decisive one and it is easy to skip.

- **Absence-tolerant recorder** — `if [m for m in console_errors if _is_known_defect(m)]: soft_failures.append(...)`.
  Zero matches produce **no signal**. Nothing was weakened; the green is honest.
- **Presence assertion** — anything asserting the defect still fires. A green
  there WOULD mean the detection died.

Ask it of the actual code, not of the docstring.

## The consequence to raise even when you APPROVE

The sanctioned-RED classification becomes **environment-scoped**, and
`.agents/testing.md` § Merge gate does not say so. Its `expect.soft` bullet reads
"a spec carrying one `expect.soft()` + `# Known defect: #N` **is** sanctioned-RED
and its case stays `blocked-on-#N`, never `automated`" — applied mechanically to a
green deployed gate that is now wrong. Recommend the ledger entry be amended to
name the signature as localhost-only, and push the fact out of one role's memory
into `.agents/testing.md` / `.agents/knowledge/` (cross-role + verified + durable +
costly to rediscover — it passes all four promotion tests).

Worked instance: PR #2106 / ELITEA-1892 / defect #611, 2026-09-09.

Related: [[precedent_is_not_authority]]
