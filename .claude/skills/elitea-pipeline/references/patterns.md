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

**This is the official replacement for the deprecated `loop` / `loop_from_tool` nodes** — not a workaround. The docs name "Router + state-based iteration control" as the migration target for both.

The full four-node shape: initialize the counter, do the work, increment + decide, route.

```yaml
state:
  loop_counter:
    type: int
    value: 0
  max_iterations:
    type: int
    value: 10
  continue_loop:
    type: bool
    value: true

nodes:
  - id: InitializeLoop
    type: state_modifier
    template: "{{ 0 }}"
    output:
      - loop_counter
    transition: ProcessItem

  - id: ProcessItem
    type: llm
    # ... the actual per-iteration work
    transition: UpdateCounter

  - id: UpdateCounter
    type: code
    code:
      type: fixed
      value: |
        counter = alita_state.get('loop_counter', 0)
        max_iterations = alita_state.get('max_iterations', 10)
        {
          "loop_counter": counter + 1,
          "continue_loop": counter + 1 < max_iterations
        }
    input:
      - loop_counter
      - max_iterations
    output:
      - loop_counter
      - continue_loop
    structured_output: true
    transition: LoopRouter

  - id: LoopRouter
    type: router
    condition: |
      {% if continue_loop %}
      ProcessItem
      {% else %}
      END
      {% endif %}
    routes:
      - ProcessItem
      - END
    input:
      - continue_loop
    default_output: END
```

> ⚠️ **The published version of this example has a bug — don't copy it verbatim from the docs.** ELITEA's own loop example (and the ones on `states.md` and `nodes/overview.md`) writes the code node's result with a top-level `return {...}`. Code nodes run at **module scope**, so `return` is a `SyntaxError`. The dict literal must be the **last expression**, as written above. Always cap the loop with `max_iterations` — a router loop has no built-in bound.

For a real, working router-loop with lazy per-item fetching, see `examples/AgentStudioGrader.yaml`.

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

### Model routing (auto model selection) — one model per branch

Because pipeline `llm` nodes have **no per-node model** (they all inherit the version's `llm_settings`; inline per-node `llm_settings` is silently ignored), the way to run different steps on different models — an "auto model router" / "auto LLM distribution" — is **model-per-agent**: create one classic agent per model tier (model pinned at each agent's version level), add them as `application` tools, and make each branch an `agent` node.

```yaml
# Classifier is a plain llm node on the VERSION model (pick a cheap one, e.g. Haiku).
- id: Classify            # entry_point — an llm node here because we need the classification
                          # BEFORE routing. (A router *can* be entry_point, but it would have
                          # nothing to route on except raw `input`.)
  type: llm
  input: [input]
  output: [tier, reason]  # structured_output: true; system prompt = complexity rubric
  transition: Route
- id: Route               # deterministic dispatch on state.tier — no LLM
  type: router
  input: [tier]
  condition: |
    {% set t = tier|lower|trim %}
    {% if t == 'simple' %}Simple{% elif t == 'complex' %}Complex{% else %}Standard{% endif %}
  routes: [Simple, Standard, Complex]
  default_output: Standard
- id: Simple              # each branch delegates to an agent pinned to its tier's model
  type: agent
  tool: AutoRouter-Simple     # agent on a fast/cheap model
  input_mapping: { task: {type: fstring, value: '{input}'}, chat_history: {type: fixed, value: []} }
  output: [answer]
  transition: Compose
# Standard → AutoRouter-Standard (mid model); Complex → AutoRouter-Complex (strong/reasoning model)
- id: Compose             # code node: map tier→model label, build a "routed to X because Y" banner
  type: code
  transition: Show
```

This is the truest reading of "auto LLM distribution across the pipeline": the pipeline distributes work across agents that each run on a different model. Get valid `model_name` strings (and their `low_tier`/`high_tier`/`supports_reasoning` flags) from `GET /api/v2/configurations/models/{pid}?include_shared=true`. Full worked artifact: `examples/AutoModelRouter.yaml`. See also `elitea-platform/references/conventions.md` §11 (model resolution) and the LLM-node gotchas in `yaml-schema.md` (remember `chat_history` on the classifier for editor round-trip).

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
