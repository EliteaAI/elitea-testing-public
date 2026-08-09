---
name: Wave dispatch case snapshot dir has no wave suffix
description: dispatch names <campaign>-w<N>/cases/, actual file is at <campaign>/cases/ (no suffix) — recurring, check that path first
type: feedback
---

## Pattern (recurred 3x this campaign: ELITEA-2043, ELITEA-2053, ELITEA-2066)

A combined analyst+implementer dispatch for the `pipelines-remaining` campaign
names the case snapshot path as
`.agents/automation/pipelines-remaining-w<N>/cases/<ID>.md` (matching the
batch trunk name `tests/batch-pipelines-remaining-w<N>`). That per-wave
`cases/` directory does not exist — the campaign uses ONE shared cases
directory across all waves:

```
.agents/automation/pipelines-remaining/cases/<ID>.md
```

(No `-w<N>` suffix on the campaign-level dir, even though the batch TRUNK
branch and BRANCH naming do carry the wave suffix.)

## What to do

Before returning `needs-analyst` for "digest/case snapshot missing": check
the campaign-level dir (strip the `-w<N>` suffix) FIRST. Only escalate if the
case is genuinely absent from BOTH the wave-suffixed and the un-suffixed path.

This is specific to the `pipelines-remaining` campaign's directory layout as
seeded — other campaigns may lay out `cases/` differently; verify the actual
`.agents/automation/<campaign*>/` tree with `find`/`ls` rather than assuming
either convention.
