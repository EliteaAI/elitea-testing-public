---
name: Code node Run Details timeline label is 'pyodide', not the space-stripped id
description: get_run_details_selected_timeline_step_id() for a Code node returns "pyodide", not "Code1" -- LLM/Printer convention doesn't generalize
type: feedback
---

`get_run_details_selected_timeline_step_id()` (`PipelineDetailPage`) reads
the Run Details panel's "Timeline step:" label. For LLM/Printer node types
this is confirmed (ELITEA-2450/2452) to be the YAML node id with its space
stripped (`"LLM 1"` -> `"LLM1"`, `"Printer 1"` -> `"Printer1"`).

**A Code node's step does NOT follow this convention.** Confirmed live
(ELITEA-2446, `test_pipeline_code_node_reads_state_variable.py`): selecting a
Code node's timeline-step dot returns text containing `"pyodide"` — the
underlying Python-sandbox executor's name (same string visible as the chat
panel's tool-call chip, "Python Sandbox: pyodide_sandbox") — NOT `"Code1"`.

If a case/AFS asserts a Code node's timeline label, expect `"pyodide"`
(case-insensitive substring match), not the space-stripped id. Filed as a
clarification, not a defect: `EliteaAI/elitea-testing-public#1385`. The
underlying mechanism (index-based `select_run_details_timeline_step()`,
reading that step's state rows) is unaffected — only the label text.
