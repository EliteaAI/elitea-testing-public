---
name: single-case batch-build workflow turnaround baseline
description: wall-clock/token baseline for a moderately-novel single-case batch via batch-build.workflow.mjs
type: reference
---

ELITEA-2026 (Pipeline — YAML Editor View, 2026-08-07, `wf_ce07a099-f64`):
single-case batch, moderate novelty (2 genuine testid gaps: one sanctioned
#579 exception, one real `add-data-testid`). End-to-end via
`batch-build.workflow.mjs`:

- Triage: 47s
- Analyst (live execution, AFS write, testid discovery): ~42 min
- Implementer (build + testid add + PR): ~12 min
- Reviewer (static, fresh session): ~4 min
- Merge to trunk: 34s
- Gate (3× independent runs + blast-radius scoping): ~25 min
- Report writer: ~2 min

Total ~87 min wall-clock, 7 agents, 935k tokens, 293 tool calls. Useful as a
rough estimate for similarly-scoped single-case UI batches (1-2 new testids,
no clustering, no rework rounds) — the analyst and gate phases dominate.
