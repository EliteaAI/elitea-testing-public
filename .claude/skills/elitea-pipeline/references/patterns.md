# Pipeline Patterns

Reusable building blocks and end-to-end pipeline shapes expressed with modern node types.

## Common Pipeline Patterns

### Linear Flow
```yaml
entry_point: Step1
nodes:
  - id: Step1
    type: llm
    transition: Step2
  - id: Step2
    type: code
    transition: END
```

### Loop with Router
```yaml
- id: ProcessItem
  type: code
  transition: CheckComplete
- id: CheckComplete
  type: router
  condition: |
    {% if current_index < total_count %}
    ProcessItem
    {% else %}
    END
    {% endif %}
  routes: [ProcessItem, END]
  default_output: END
```

### Converging Paths
```yaml
- id: RouteInput
  type: decision
  nodes: [PathA, PathB]
  default_output: END
- id: PathA
  type: toolkit
  transition: FinalReport
- id: PathB
  type: toolkit
  transition: FinalReport
- id: FinalReport
  type: llm
  transition: END
```

## Pipeline-as-a-tool — output & large responses (gotcha)

When a pipeline is wrapped as an `application`-type toolkit and called by a parent agent, the parent
receives the pipeline's **final node's message** — conventionally an `llm` "echo" node that returns a
result variable verbatim (the `present_*` pattern in `examples/FetchUIContext.yaml`).

⚠️ **An `llm` echo node truncates large payloads** (it's a model generation, not a byte-faithful
passthrough). If a `code` node fetches a big API response — e.g. a full toolkit/version *list* where
each row carries `settings`/`spec`/`instructions` — the echo silently drops rows, so the caller sees
an incomplete result. (Real incident: a `?mcp=true` toolkit list lost its 3rd MCP because one row
embedded a full OpenAPI spec.)

**Mitigations:**
- **Best fix — skip the LLM echo entirely.** A `code` node can write the result straight into
  `messages` and end the pipeline there, so the result IS the returned message with no model in the
  path (faster, byte-exact, no truncation). Pattern (verified):
  ```yaml
  - id: do_work
    type: code
    code: {type: fixed, value: "import json\n# ... compute result ...\n{'messages': [{'role':'assistant','content': json.dumps(result, ensure_ascii=False)}]}"}
    input: [input]
    output: [messages]      # write to messages, not a custom var
    structured_output: true
    transition: END         # no present_* LLM node
  ```
  A code node ending the pipeline with `output: [result]` (a non-`messages` var) does NOT surface to
  the caller — write to `messages` as above.
- Still **compact list rows** in the code node — replace heavy per-row fields (`settings`, `spec`,
  `schema`, `instructions`, `pipeline_settings`) with a `<omitted N chars>` placeholder (keep
  id/name/type) — so even the no-echo message doesn't bloat the caller's context. Fetch a single
  entity when you need its full body.
- If you DO keep an `llm` echo node, know it truncates large payloads. Symptom: a list/survey from a
  pipeline-tool is missing entries you can see via direct API — suspect echo truncation, not the API.

## Common Use Case Patterns

> These patterns are derived from legacy Pipeline Agent Framework use cases, **re-expressed using modern node types**.

1. **User Story Creation Workflow**: `llm` (gather info) → `agent` (aggregate content) → `agent` (draft) → `agent` (enhance) → `llm` (feedback) → `router` (approve/edit/finish) → `agent` (publish to Jira) → END
2. **Code Documentation**: `toolkit` (get file list) → `code` (iterate files) → `agent` (doc per file) → `router` (loop check) → END
3. **Master Orchestration**: `agent` (trigger Agent A) → `agent` (trigger Agent B) → END
4. **Bulk Processing with Publishing Decision**: `llm` (input) → `toolkit` (extract) → `agent` (bulk create) → `llm` (prepare) → `decision` (Jira vs Confluence) → `toolkit` (publish) → END
5. **Data Extraction Pipeline**: `toolkit` (list items) → `code` (process each) → `router` (loop) → END
