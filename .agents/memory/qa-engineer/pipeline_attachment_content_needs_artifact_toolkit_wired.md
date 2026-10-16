---
name: Pipeline attachment content resolution needs an artifact toolkit wired into the node
description: The Attachments MODULES toggle only governs the chat's attach-button UI affordance; it does NOT make attached-file content reachable by the LLM. Confirmed live ELITEA-2059 adjust round, 2026-10-15.
type: feedback
---

## The gap

Turning on a pipeline's "Attachments" MODULES toggle (`agent-canvas-tools-toggle-attachments`)
only does two things: (1) enables the chat panel's attach-files button, (2) (via
`usePipelineAttachmentYamlSync`) syncs an `input_attachments` state-variable key into
the pipeline's YAML. Neither of these gives any node a way to actually READ the
attached file's bytes.

A bare `llm`-type node, even with `input_attachments` wired into its `input` list and
referenced in its `task` fstring, only ever receives a **path reference** as text
(`"Attached document: {uuid}/{filename} (attachments/{uuid}/{filename})"`) — it has
no tool to dereference that path. Confirmed live: it replies with an honest "I can't
access the contents of that attachment" every time, regardless of task-mapping shape.

**Fix**: attach an Artifact toolkit pointed at the `attachments` bucket
(`ToolkitAPI.create_artifact_toolkit(name, description, bucket_name="attachments")`)
to the pipeline's Tools section, AND select it in the LLM node's own Toolkits
multi-select (`pipeline-llm-node-toolkits-select`) with at least `read_file` in its
`tool_names` mapping. Attaching to the Tools section alone is NOT sufficient — the
node-level Toolkits select is a separate, required step (confirmed live: a toolkit
attached-but-not-selected-on-the-node never gets called).

Once wired, the LLM can invoke `read_file` on the exact path from
`input_attachments`, and the response correctly reflects the file's actual content
(verified with literal content `"cat"` + question "what animal is in the
attachment?" -> correct "...is a cat." response, twice: once via an API-authored
pipeline, once via the full UI attach flow from an empty pipeline).

## Where this bit a real case

ELITEA-2059 ("Pipeline — Attach Files in Chat") originally treated the bare-node
"I can't read this" reply as the CORRECT, expected result and asserted only an
acknowledgment-keyword-or-filename match — weak enough to pass without the pipeline
ever reading the file. A human reviewer caught this (issue #2408, overturning an
earlier Class-D parked verdict on #2412) and the AFS/test were adjusted to add the
toolkit-wiring steps and assert on resolved content instead.

## Related

- `.claude/skills/elitea-pipeline/references/workflows.md` § File attachments into
  a pipeline — the `input_attachments` state-var mechanism and the
  `alita_client.artifact(bucket).get(name)` code-node pattern (useful for a `code`
  node reading an attachment; the toolkit-attach path above is the equivalent for an
  `llm` node that can't run code).
- `select_toolkit_in_popper()` does NOT auto-persist (unlike `select_mcp_in_popper()`
  which PATCHes immediately) — an explicit pipeline Save is required after attaching
  a Toolkit, same as the ELITEA-2021 finding.
