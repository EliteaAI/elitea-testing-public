---
name: Pipeline LLM/HITL node Variable-type Value field widget swap
description: Type=Variable swaps the Value field from textarea to a Select with NO testid — component gap, one-line fix
type: feedback
---

`SimpleLLMInputItem.jsx` (shared by the LLM node's SYSTEM/TASK/CHAT HISTORY and HITL's
`user_message`) renders the Value field as a `<textarea>` (testid'd via `valueFieldTestId`)
when Type ∈ {Fixed, F-String}, but as a completely different MUI `Select`
(`id="simple-select-Value"`, options = pipeline state variables `input`/`messages`) when
Type = Variable — and that Select branch never receives `data-testid={valueFieldTestId}`
even though the prop is already threaded through the component and correctly applied to the
textarea branch. One-line fix in `SimpleLLMInputItem.jsx`, reuse the same testid name, no
call-site changes.

Also: Value is CLEARED on any Type transition involving Variable (Variable→X or X→Variable),
but PRESERVED across Fixed↔F-String (confirmed via source's `shouldPreserveValue` logic and
live DOM reads both directions). A test walking a field through multiple Types must re-enter
the Value after every transition that touches Variable.

Confirmed live 2026-08-04 during ELITEA-2040 analysis (extend-existing AFS:
`test-specs/pipelines/lextend_pipeline-input-mapping-types-fixed-fstring-variable_ELITEA-2040.md`).
Full detail in `test-specs/pipelines/_surface.md`.
