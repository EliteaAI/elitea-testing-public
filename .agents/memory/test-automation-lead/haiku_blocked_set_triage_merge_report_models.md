---
name: haiku blocked for this team — pass triageModel/mergeModel/reporterModel
description: batch-build defaults triage/merge/report agents to haiku; team 403s on it (2026-11-25)
type: feedback
---
batch-build uses haiku for triage, merge and report. On this team that 403s ("team not allowed to access model"), parking the unit as "merge agent failed". Pass `triageModel/mergeModel/reporterModel: "sonnet"` in args from the start. Resume with changed args matched 0 cached calls (re-ran from scratch, ~20 min) — so set them up front.
