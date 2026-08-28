---
name: "Latent-race" claims need a git log -S date check
description: Before accepting "the test always had this race", find WHEN the product mechanism was introduced
type: feedback
---

# A "latent race, product is fine" triage is only half-verified until you date the mechanism

**Reviewing a repair, verifying the root cause in the product source is NOT enough.**
Confirming that `ToolMenu.jsx` today gates a fetch behind `!mcpOpened.current` proves the
race EXISTS. It does not prove the race was ALWAYS there — and repairs routinely claim
exactly that ("unconditional latent race", "the test was sampling too early").

Add one command:

```bash
cd ../EliteaUI && git log -1 --format='%h %ad %s' --date=short \
  -S"<the symbol the root cause turns on>" origin/main -- <file>
```

Worked case (ELITEA-1955 / #1890, 2026-08-28): `mcpOpened`/`forceSkip` was introduced by
EliteaAI/EliteaUI@94a61b81 `fix: [EL-6351] Lazy-load optional data on Agent and Pipeline
detail pages`, dated **2026-08-26** — ONE DAY before the failing GHA run. Before it, the
toolkit query fired on mount, so by the time the spec reached Step 7 the RTK Query cache
was warm and rows rendered synchronously. That is why the spec passed its 3x merge gate
and stayed green for weeks. The AFS's "unconditional latent race" framing was wrong.

**Why it matters even when the fix is right** (it was — a wait is correct either way):

- It changes the triage class from "our test was always sloppy" to "the product changed
  deliberately and our test needed to follow". Different lesson, different follow-up.
- Sibling cards sharing the root cause inherit the wrong story.
- A future reader takes "the test was never sound" at face value — this repo's canon is
  explicit that an unverified claim in a committed record is worse than silence.
- If the `git log -S` date lands on a commit that is NOT deliberate (no perf/refactor
  intent in the message), the "not a product bug" disposition itself is suspect.

Corollary: also spot-check "file is identical on origin/main and origin/automation/testids"
claims with `git diff --stat origin/main origin/automation/testids -- <file>`. Same case
asserted it for `ToolMenu.jsx`; the file actually differs by four additive `*-tooltip`
testid wrappers. Harmless there (the load-bearing logic WAS identical), but the claim as
written was false.
