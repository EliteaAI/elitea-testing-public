---
name: A sanctioned RED can be DEV-build-only — check NODE_ENV before you gate
description: Redux/React dev-only middleware makes a console-error signature fire on localhost and be impossible on any deployed env
type: feedback
aliases: [environment-scoped sanctioned red, dev build only console error, "#1215", "#611", NODE_ENV gate expectation]
tags: [area/gating, type/lesson]
created: 2026-09-10
updated: 2026-09-10
---

## The rule

Before gating a spec whose RED is a **console-error signature**, ask whether that message can
physically occur on the environment you are gating against. A whole class of them cannot.

`#1215` (ELITEA-2354, Agent Hub like/unlike) comes from Redux Toolkit's
`createSerializableStateInvariantMiddleware`, which `buildGetDefaultMiddleware` adds **only**
inside `if (process.env.NODE_ENV !== "production")` (`@reduxjs/toolkit@^2.6.1`,
`redux-toolkit.legacy-esm.js:467-480`). EliteaUI ships `"build": "vite build"` → `mode=production`
→ the middleware is **not in the store at all** on any deployed env.

So the same spec, same day: **RED on `localhost:5173`, GREEN 3/3 on `dev.elitea.ai`, and both are
correct.** A DEV green is a legitimate `automated`, NOT `blocked-on-#1215` — which is the opposite
of what a mechanically-applied "it carries a soft assert, therefore sanctioned-RED" reading gives.

Identical mechanism to `#611` / ELITEA-1892 / #2082, whose signature is React
*development-build* diagnostics. Two instances now — treat it as a class, not a curiosity.

## What this does NOT license

Nothing is weakened by the scoping. It holds only because the spec's handling is an
**absence-tolerant recorder** (zero matching messages append nothing), and the
unexpected-console-error hard assert is untouched — a genuinely new error still fails on either
environment. The defect stays **OPEN** on its own localhost evidence; it is quiescent-by-topology,
not fixed.

Write the environment scope into the **spec docstring**, not just the AFS — the next person
triaging the red reads the test.

Related: [[env_test_is_a_symlink_dev_swap_recipe]] · [[dev_page_goto_flake_is_a_precondition]]
