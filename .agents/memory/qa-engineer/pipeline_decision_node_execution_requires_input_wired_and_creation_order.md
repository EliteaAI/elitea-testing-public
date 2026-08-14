---
name: Pipeline Decision node execution requires Input wired and creation order
description: Decision-node routing needs Input="input" wired AND must be created first to become entry point, or classification silently no-ops
type: feedback
---

Live-confirmed 2026-08-08 (ELITEA-2016 analysis, `test-specs/pipelines/l2_pipeline-decision-node-multi-branch-execution_ELITEA-2016.md`).
Two independent, non-obvious setup requirements for any pipeline case that actually
EXECUTES a Decision node (not just configures it — ELITEA-2034 never ran one):

1. **Entry point.** A Decision node can only become `entry_point` by being the FIRST node
   added to the pipeline (auto-set at creation). The node header's "Make entrypoint" menu
   action is unconditionally excluded for Decision/Condition types (confirmed via
   `NodeCardHeader.jsx` source) — `PipelineDetailPage.make_node_entrypoint()` silently
   no-ops on a Decision node. Filed: EliteaAI/elitea-testing-public#1347. Always add the
   Decision node before any branch/target nodes when it must be the entry point, and assert
   via `get_entrypoint_node_id()`, never `make_node_entrypoint()`.

2. **Input variable.** The Decision node's `Input` combobox must include the built-in
   `input` state var (`select_decision_node_input_variables(["input"])`) or the underlying
   LLM tool-call returns `content: '{}'`, `tool_calls: []` and the pipeline "completes" at
   the Decision node without ever executing any branch — NO error surfaces anywhere in the
   UI. This is a DIFFERENT requirement than ELITEA-2034's (that case wired custom state
   vars because its prompt text referenced them by name); this one is needed even when the
   prompt only needs the raw chat message.

Also: Printer's chat-visible output comes from the PRINTER section's **Value** field
(`input_mapping.printer.value`), NOT "Final Message" (a separate, unused-here field) — and
multi-turn continuation in the SAME chat conversation resumes at the last-reached node
rather than re-invoking Decision (clear the chat between differential-routing assertions).
Full details + exact edge-testid strings: the `_surface.md` digest section this entry links
to, and the AFS's Concrete Handles / Automation Hints.
