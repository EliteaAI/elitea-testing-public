---
name: Code node needs dict-literal return, not assignment
description: A Code node's structured_output write requires a bare dict literal as the final statement; a plain assignment silently no-ops
type: feedback
---

Confirmed live 2026-08-09 (ELITEA-2446, pipeline id 8809, 4 probe runs on
localhost:5173): a Code node's script must end with a bare dict-literal
EXPRESSION (`{"code_output": f"Processed: {result}"}`) for `structured_output:
true` to write the value into the declared `output:` state variable.

A plain ASSIGNMENT to a local variable (`code_output = f"Processed: {result}"`
or `output = f"..."`) produces NO state update — the variable stays `""`/`""`
Before/After in Run Details, with zero visible error (run still reports
"Completed"). Confirmed via 3 iterations: assignment → empty; dict-literal →
correct.

This matches `.claude/skills/elitea-pipeline/references/yaml-schema.md`'s own
documented rule verbatim: "Return a dict literal as the LAST expression... Do
NOT use a top-level `return` — code runs at module scope." The product behaves
exactly as documented — TMS case texts that show plain-assignment Code-node
scripts (ELITEA-2446's own source case did) are case-text drift, not a bug.
Filed as CLARIFICATION: `EliteaAI/elitea-testing-public#1383`.

`elitea_state.get(...)` IS a valid accessor (alias of `alita_state.get(...)`,
both restored by the sandbox preamble per the same yaml-schema.md) — no drift
on the accessor name itself, only on the return-shape.

Related gotcha, same session: building a multi-node pipeline via the Flow
Editor's "Add node" clicks does NOT auto-wire an edge between sequentially
added nodes — each lands with an independent `transition: END` (confirmed via
YAML view + canvas edge labels), so the second node never executes. Build via
`PipelineAPI.create_pipeline()`/`create_pipeline_with_nodes()` with an explicit
`transition:` field per node instead (every execution-based fixture in this
suite already does this). Filed as CLARIFICATION:
`EliteaAI/elitea-testing-public#1384`.

Full writeup: `test-specs/pipelines/l3_code-node-read-elitea-state-variables_ELITEA-2446.md`,
`test-specs/pipelines/_surface.md` § "Code node — execution & build-method gotchas".

**Confirmed on a second, independent fixture (2026-08-09, ELITEA-2447, pipeline
id 8816):** the SAME bare-dict-literal rule scales cleanly to a MULTI-key dict
(`{'summary': ..., 'count': ..., 'tags': ...}`, 3 keys of 3 different types) —
all 3 declared `output:` vars update correctly from ONE execution, no partial
writes. Also new: a Code node's `output:` list MAY include a variable that is
ALSO in that same node's `input:` list (`input: [summary]`, `output: [summary,
count, tags]`) — no validation error, Run Details correctly attributes the
update to the one node that both read and wrote it. And: a `state_modifier`
node with a literal Jinja template (no variables) is a good deterministic way
to seed a Code node's input value when the test needs a stable
non-LLM-generated string (avoids `len(text.split())`-style assertions being
LLM-nondeterministic). Full writeup:
`test-specs/pipelines/l3_code-node-return-dict-multiple-state-vars_ELITEA-2447.md`.
