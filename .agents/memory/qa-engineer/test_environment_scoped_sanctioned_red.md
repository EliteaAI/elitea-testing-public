---
name: A sanctioned-RED can be environment-scoped — check the build mode before concluding "fixed"
description: Dev-build-only diagnostics (React, Redux Toolkit) make a spec legitimately RED on localhost and GREEN on DEV
type: feedback
aliases: ["#1215", "#611", serializableCheck, dev build only, sanctioned RED environment]
tags: [area/gating, type/triage]
created: 2026-09-10
updated: 2026-09-10
---

Before reading a green gate as "the defect is fixed" or a red one as "a regression", ask whether
the signature can **physically occur** on the environment you gated on.

Two confirmed members of this class on this project:

- **`#611`** (ELITEA-1892) — React *development-build* warnings, compiled out of production.
- **`#1215`** (ELITEA-2354) — "A non-serializable value was detected in an action, in the path:
  `payload.updateFn`". Source: Redux Toolkit's `createSerializableStateInvariantMiddleware`,
  which `buildGetDefaultMiddleware` adds **only** inside
  `if (process.env.NODE_ENV !== "production")` (`redux-toolkit.legacy-esm.js:467-480`,
  `@reduxjs/toolkit@^2.6.1`). EliteaUI ships `"build": "vite build"` → production →
  the middleware is not in the store at all on any deployed env.

Verified live 2026-09-10, same session: `test_agent_hub_like_agent_list_view.py` is
**GREEN 3/3 on dev.elitea.ai** and **RED with the #1215 signature on localhost:5173**. Both correct.

**Nothing is weakened by this**, provided the spec's handling is an absence-tolerant *recorder*
(zero matching messages append nothing) rather than a presence assertion — and provided the
unexpected-console-error hard assert stays intact. The defect stays OPEN on its localhost evidence.

Practical rule: **state the expected gate outcome PER ENVIRONMENT** in any repair brief or closure
record, never as a single verdict.

Related: [[networkidle_is_not_a_settle_signal]]
