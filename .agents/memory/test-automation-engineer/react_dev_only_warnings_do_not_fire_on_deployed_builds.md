---
name: A sanctioned-RED built on React dev warnings goes GREEN on DEV — that is not masking
description: React prop warnings exist only in the development build; localhost serves it, dev.elitea.ai does not
type: feedback
aliases: [sanctioned RED green on DEV, React does not recognize the prop, non-boolean attribute, console error only on localhost]
tags: [area/environment, type/failure-classification]
created: 2026-09-09
updated: 2026-09-09
---

## The fact

React's development-only diagnostics — `Received \`%s\` for a non-boolean
attribute \`%s\``, `React does not recognize the \`%s\` prop on a DOM element`,
`Maximum update depth exceeded` and friends — are emitted by
`react-dom.development.js`. They **do not exist in the production bundle**;
they are not "suppressed", the code is compiled out.

EliteaUI's `package.json` has `"dev": "vite"` and `"build": "vite build"`, so:

| Target | Build | Dev `console.error` warnings |
|---|---|---|
| `localhost:5173` | `vite` dev server (development) | present |
| `dev.elitea.ai` (and any deployed env) | `vite build` (production) | **structurally absent** |

## Why it matters when triaging

A spec whose sanctioned-RED signature is a React prop warning (e.g.
`test_agent_publish_unpublish_version.py`, known defect #611 — the Publish
wizard Stepper's `SvgCheckedIcon` leaking MUI props onto the DOM `<svg>`)
is **RED on localhost and GREEN on DEV, by construction**.

So when a card sends you to DEV to verify such a spec and it comes back fully
green: that is the **expected** outcome, not evidence that the defect was fixed
and not evidence that something masked it. Verified live 2026-09-09 on
`https://dev.elitea.ai`: the spec's own console-cleanliness step (Step 6a)
passed while the same step fails deterministically on localhost.

**Two consequences worth stating out loud in a Run Report**, because a lead
expecting RED will otherwise suspect masking:

1. Don't "confirm" a product warning is gone from a green deployed run.
2. Don't treat a green deployed gate as proof the localhost signature is stale —
   the defect issue stays open on its own evidence.

Related: [[run_a_spec_against_dev_via_env_test_symlink_swap]]
