---
name: Pipeline node after agent-pipeline-tool transition never executes
description: transition: after an agent node with a nested-pipeline tool silently drops the next node (#1381)
type: project
---

Confirmed live 2026-08-09 while analysing ELITEA-2445 (Subgraph Execution —
Verify State Flow in Run Details).

**Finding:** in a pipeline `CODE1 → AGENT1(tool=<attached child pipeline>) →
CODE2 → END`, `CODE2` NEVER executes. The run still reports `Completed`. No
distinct timeline entry appears for `CODE2` in Run Details, and its own writes
never appear in state anywhere. This reproduced 2/2 against fresh pipelines.

**Isolated the cause via a control probe:** a plain `CODE1 → CODE2` chain (no
agent/pipeline-tool hop) executes both nodes correctly — so this is NOT a
generic multi-hop `transition:` chaining bug. It's specific to "a node chained
right after an `agent`-type node whose `tool:` resolves to a nested pipeline
attached via the Tools-section '+ Pipeline' popper."

Filed as `EliteaAI/elitea-testing-public#1381`. ELITEA-2443/2444's own merged
fixtures never hit this because both end `AGENT1`'s `transition:` at `END` —
neither chains anything after the agent-pipeline-tool hop.

**If you're building a pipeline fixture that chains ANYTHING after an Agent
node whose `tool:` is a nested pipeline**: expect the trailing node to be
silently skipped. Assert its absence via `expect.soft()` +
`# Known defect: EliteaAI/elitea-testing-public#1381`, don't skip/mask it, and
don't waste time debugging your own fixture wiring first — the node WILL show
up correctly on canvas (`get_node_ids()`), it just never executes.

Full repro recipe + Gap-assertion AFS:
`test-specs/pipelines/lextend_pipeline-subgraph-node-c-state-propagation_ELITEA-2445.md`.
Live-exploration digest entry: `test-specs/pipelines/_surface.md` (search
"CONFIRMED DEFECT: a node chained via `transition:`").
