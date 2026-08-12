---
name: Agent-node pipeline-tool transition to next node never executes
description: A node chained via transition: right after an agent node whose tool: resolves to a nested pipeline never runs (defect #1381)
type: feedback
---

## What happened

ELITEA-2445 (subgraph — Node_C state propagation, extend-existing onto
`test_pipeline_subgraph_state_sharing.py`) needed a THREE-node parent:
`CODE1 -> AGENT1 (agent, tool = attached child pipeline) -> CODE2 -> END`,
where `CODE2` reads back the state the Agent-node call's child left behind.

Confirmed live (and re-confirmed on this implementation pass): `CODE2` NEVER
executes. The run still reports "Completed". The Run Details timeline stays
at the SAME entry count the equivalent 2-node parent (`CODE1 -> AGENT1 ->
END`, no `CODE2`) produces — `CODE2` never gains a distinct timeline dot,
and no timeline entry's aria-label ever matches `"CODE2"`.

A control probe (plain `code(CODE1) -> code(CODE2) -> END`, no agent hop)
proved multi-hop `transition:` chaining otherwise works fine — the defect is
isolated specifically to "next node after an Agent node whose `tool:`
resolves to a nested pipeline", not `transition:` chaining in general.

Filed as `EliteaAI/elitea-testing-public#1381`.

## Fix / pattern for a future case

If a case wants to chain something AFTER an Agent-node's nested-pipeline
tool call: don't assert the downstream node's own output — it won't run.
Assert the ABSENCE instead (a soft/known-defect check, not masking):
- timeline step count stays at whatever the Agent-node-terminal shape
  produces (verify live for YOUR fixture recipe — don't assume a number)
- no timeline entry's `get_run_details_timeline_step_node_id()` aria-label
  matches the downstream node's id

Wrap both in the project's `soft_failures` list + `pytest.fail()`-at-end
pattern (see `test_pipeline_hitl_node_runtime_behavior.py` for the
established shape) with a `# Known defect: #1381` comment — this way, IF the
defect gets fixed and the node starts executing, the structural assumption
breaks LOUDLY (caught as a soft failure attributing to #1381) instead of
silently producing a wrong-but-passing test.

## Where

`automation/tests/ui/pipelines/test_pipeline_subgraph_state_sharing.py::test_subgraph_state_sharing_node_c_state_propagation`,
`automation/fixtures/data_fixtures.py::pipeline_parent_child_state_sharing_three_node`,
`EliteaAI/elitea-testing-public#1381`.
