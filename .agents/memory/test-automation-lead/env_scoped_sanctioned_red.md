---
name: A sanctioned-RED signature can be environment-scoped — check before you classify
description: Before filing a gate result against a closed defect set, ask whether each member can physically occur on the environment you gated on; a dev-build-only warning makes RED-on-localhost and GREEN-on-DEV both correct
type: feedback
aliases: [sanctioned red green on dev, dev build only warning, react development warnings, closed set environment, blocked-on vs automated, environment scoped defect]
tags: [area/triage, area/merge-gate, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

`.agents/testing.md` § Merge gate says a spec carrying `expect.soft()` + `# Known defect: #N`
**is** sanctioned-RED and its case stays `blocked-on-#N`, never `automated`. Applied
mechanically that is wrong whenever the defect **cannot occur on the environment you gated
on** — and nothing in the rule prompts you to ask.

Worked case, ELITEA-1892 / #2082 (2026-09-09). The closed set is #611 + #614, both OPEN.
**#611's entire signature is React *development-build* diagnostics** (`Received \`true\` for a
non-boolean attribute`, `React does not recognize the \`ownerState\` prop`) which live in
`react-dom.development.js`. EliteaUI ships a production build (`"build": "vite build"`;
`vite.config.js` sets no `NODE_ENV`/`mode` override so `vite build` defaults to
`mode=production`; `.github/workflows/build_and_release.yml:86` releases that artifact), and
React compiles those warnings **out** of it. So the spec is RED on `localhost:5173` (vite dev
server) and GREEN on `dev.elitea.ai` — **both correct**. A DEV gate on it is a legitimate
`automated` green, not `blocked-on-#611`.

## Why the green is not a coverage loss — the discriminator to check

Ask what SHAPE the defect handling has:

- **Absence-tolerant recorder** — `if [m for m in console_errors if _is_611(m)]: soft_failures.append(...)`.
  Zero matching messages produce **no signal**. Nothing is weakened when the defect is
  structurally absent. ✅
- **Presence assertion** — something that asserts the defect DOES manifest. A green would then
  mean detection died. ❌ block.

Also confirm the case's OWN step assertions still run identically on both environments (they
did — #611 was an Axis-2 defect-surfacing addition, never a case observable), and that the
gating assertion ("no *unexpected* console errors") is intact.

## The general rule

**Before classifying any gate result against a closed set, ask whether each member can
physically occur on the environment you gated on.** Then say so explicitly in the closure
record — a later reader seeing a green on a documented sanctioned-RED case will otherwise
either mis-file it or "fix" the localhost red as a regression.

State any inferred link as inferred. Here: that the DEV *deployment* serves the released
production artifact rather than a dev-mode container is inferred from the release workflow, not
confirmed against the served bundle.

Codified in `.agents/testing.md` § Merge gate (`f951d9f64`).

Related: [[sanctioned_red_closed_set_variant]] · [[a_fix_card_can_have_no_work_in_it]] · [[some_specs_cannot_be_gated_on_localhost]]
