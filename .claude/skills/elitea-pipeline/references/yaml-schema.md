# Pipeline YAML Schema

Complete reference for the ELITEA pipeline YAML format: top-level structure, state, all 11 modern node types, and legacy node types (reference only).

## Top-Level Structure

Every pipeline YAML has three required top-level sections:

```yaml
entry_point: <node_id>        # Required — starting node ID
state: {...}                   # Required — state variable definitions
nodes: [...]                   # Required — node configurations
```

Optional top-level fields:
```yaml
interrupt_before: [NodeA, NodeB]   # Pause BEFORE these nodes (global list)
interrupt_after: [NodeA, NodeB]    # Pause AFTER these nodes (global list)
```

**Write the keys in this order:**

```
state → entry_point → interrupt_after → interrupt_before → nodes
```

That's the order the Flow Editor emits. Authoring in it keeps API-authored YAML diff-clean when someone opens the pipeline in the UI and saves it — otherwise a round-trip through the editor reshuffles your file and every subsequent diff is noise. (Related: the `chat_history` round-trip gotcha in `SKILL.md`.)

**Triggers are not in the YAML.** A pipeline's trigger (chat / scheduled / webhook) is server-side state on the entry-point node, set over REST. It does not appear in the YAML, and it will **not** survive an export/import — see `workflows.md` § "Pipeline entry-point triggers".

Alternatively, set interrupts **per node** inline:
```yaml
- id: MyNode
  type: llm
  interrupt_before: true    # pause before this specific node
  interrupt_after: true     # pause after this specific node
  ...
```
Both forms are valid. Inline per-node form is convenient during development to inspect state at a single node without editing the top-level lists.

## State Configuration

State is the pipeline's memory system. Every pipeline has two default states:

- **`input`** (str) — most recent user message (short-term memory)
- **`messages`** (list) — complete conversation history (long-term memory)

Custom state syntax:
```yaml
state:
  <variable_name>:
    type: <str|number|int|float|bool|list|JSON>
    value: <default_value>  # Optional
```

**Data Types:** `str` (string/text), `number`/`int`/`float` (numerics), `bool` (true/false), `list` (ordered collections), `JSON`/`dict` (dict/key-value pairs).

> **Spelling aliases.** The docs are inconsistent: the YAML reference page uses `string` / `number` / `list` / `JSON`, the states page uses `str` / `number` / `list` / `dict`. Both spellings appear in live pipelines and both work. Pick one and be consistent within a file.

`messages` is typed `list[BaseMessage]` — LangChain message objects, **not** plain strings. Don't assume you can `"".join(...)` them.

**Critical Rule:** If you define a custom `state` section, you **must** include `messages: list` within it. Without it, the agent cannot maintain conversation history. If you don't need custom state variables, omit the `state` section entirely to use the default `messages` state.

> **Gotcha — new pipelines ship with `input` and `messages` DISABLED.** When you create a pipeline in the UI, both default states are added but switched **off**. You have to explicitly enable them for the pipeline to see user input or conversation history. This is a prime suspect whenever a node reads `elitea_state.get('input')` and gets an empty string for no apparent reason (it's exactly the trap behind the cron-detection bug in `workflows.md`).

**State Name Rules:**
- Letters (a-z, A-Z), numbers (0-9), underscores (_) only
- Must start with a letter
- No spaces, hyphens, or special characters

## Node Types (11 current types)

> **IMPORTANT:** The CURRENT node set (verified against the live docs, 2026-07-13) is **11 types**:
> `llm, agent, toolkit, mcp, code, custom, router, decision, hitl, state_modifier, printer`.
> **Always use these for new pipelines.**

The docs group them into four families. `hitl` sits under **Control Flow**, not Utility:

| Family | Nodes |
|---|---|
| **Interaction** | `llm`, `agent` |
| **Execution** | `toolkit`, `mcp`, `code`, `custom` |
| **Control Flow** | `router`, `decision`, **`hitl`** |
| **Utility** | `state_modifier`, `printer` |

> **DEPRECATED — never author** (documented at the end for reading old pipelines only): `tool`,
> `function`, `condition`, `loop`, `loop_from_tool`, and **`pipeline` (subgraph)**.
> **Modern looping = a `router` + a state counter** (process node → `code`/`state_modifier`
> increments a counter and sets `continue_loop` → `router` routes back or to `END`; cap with
> `max_iterations`) — this is the *official* migration target, not a workaround.
> **Nested pipelines are gone → delegate to an `agent` node.**
>
> ⚠️ **Where the deprecation is actually written down.** It's on `nodes/overview.md` § "Deprecated Nodes".
> The `nodes/iteration-nodes.md` page is **not** marked legacy — it still documents Loop and Loop from Tool
> with full parameter tables, as though current. That page has not been updated. **Trust `nodes/overview.md`.**
> (Earlier versions of this file claimed iteration-nodes was tagged Legacy; that was wrong, even though the
> conclusion — don't author loops — is right.)
> Live node docs: `https://docs.elitea.ai/how-tos/pipelines/nodes/overview.md`

### Interaction Nodes

**1. LLM Node** — Direct LLM interaction with full control

`prompt.type` can be `string` (plain text) or `fstring` (formatted with `{state_var}` placeholders). When using `fstring`, all referenced variables must be listed in `input`.

```yaml
- id: <unique_id>
  type: llm
  prompt:
    type: string          # string | fstring
    value: ''
  input: [input, messages]
  output: [messages]
  structured_output: false
  transition: <next_node_id>
  input_mapping:
    system:
      type: fixed          # fixed | variable | fstring
      value: "System prompt here"
    task:
      type: fstring
      value: "Process this: {input}"
    chat_history:
      type: variable
      value: messages
  tool_names:               # Optional — bind toolkits/MCPs
    toolkit_name:
      - tool1
      - tool2
```

> **LLM node gotchas (verified live):**
> - **`task` must be `type: fixed` or `fstring` — `type: variable` silently passes EMPTY content** (the LLM gets no task → 0 output tokens → default outputs). To inject a state var verbatim, use `task: {type: fstring, value: '{myvar}'}`. Python `.format` does **not** re-parse `{...}` braces inside the substituted value, so brace-heavy content (e.g. an agent's `{{glossary}}` placeholders) is safe through fstring.
> - With `structured_output: true`, the model returns JSON and the runtime maps each **top-level JSON key → the matching name in `output:`**. Make the prompt demand exactly those keys as **raw JSON (no ``` fences, no extra keys)** to avoid retries/parse failures. Too-small `max_tokens` truncates the JSON → parse fails → vars default; budget 3000–5000.
> - Pipeline `llm` nodes inherit the pipeline VERSION's `llm_settings` (there is no per-node model). **Do NOT set `reasoning_effort`** in those settings — it makes Haiku 4.5 emit 0 tokens on the pipeline path (see `workflows.md` § "Pipeline LLM-node gotchas" and `elitea-platform/references/conventions.md` §11).
> - **Flow Editor round-trip needs all three `input_mapping` keys.** An `llm` node's `input_mapping` must include `chat_history`, `system`, AND `task`. If you omit `chat_history` (easy to do when authoring via API — the runtime doesn't need it), the Flow Editor **blanks `system` and `task` on load** (and flips `task.type` fstring→fixed), inserting a default empty `chat_history`. The pipeline still RUNS (runtime reads the deployed YAML), but the editor's System/Task boxes look empty — and a **UI Save then wipes the prompts**. Always include `chat_history: {type: fixed, value: []}` so API-authored pipelines stay safely UI-editable. (`agent` nodes need only `task` + `chat_history` and round-trip fine.) Verified 2026-07 (project 27, "Auto Model Router" pipeline).

**2. Agent Node** — Delegate to pre-configured agents
```yaml
- id: <unique_id>
  type: agent
  input: [input]
  output: [messages]
  transition: <next_node_id>
  input_mapping:
    task:
      type: fstring
      value: "Do this: {input}"
    chat_history:
      type: fixed
      value: []
  tool: <agent_name>        # Must be added to pipeline first
```

### Execution Nodes

**3. Toolkit Node** — Execute ELITEA toolkit functions (no LLM overhead)
```yaml
- id: <unique_id>
  type: toolkit
  input: [input]
  output: [messages]
  structured_output: false
  transition: <next_node_id>
  toolkit_name: <toolkit_name>
  tool: <tool_name>
  input_mapping:
    param1:
      type: fixed           # fixed | variable | fstring
      value: "static_value"
    param2:
      type: variable
      value: state_var_name
```

**4. MCP Node** — Execute MCP server tools
```yaml
- id: <unique_id>
  type: mcp
  input: [input]
  output: [messages]
  structured_output: false
  transition: <next_node_id>
  toolkit_name: <mcp_server_name>
  tool: <mcp_tool_name>
  input_mapping:
    param1:
      type: fixed
      value: "value"
```

**5. Code Node** — Execute Python in Pyodide sandbox
```yaml
- id: <unique_id>
  type: code
  debug: false             # optional — see "Debug mode" below
  code:
    type: fixed              # fixed | variable | fstring
    value: |
      # Access state via alita_state
      data = alita_state.get('var_name', default)
      # Return dict for structured output
      {"result_var": processed_data}
  input: [var_name]
  output: [result_var]
  structured_output: true
  transition: <next_node_id>
```

**Debug mode (`debug: true`)** — the single best tool for a misbehaving code node.

ELITEA saves a snapshot of the *fully assembled* executable Python before it hands it to the sandbox, into an artifact bucket. The file contains, in order: a simplified `SandboxClient` implementation; an `elitea_client = SandboxClient(...)` block with an auth-token placeholder (`<YOUR_AUTH_TOKEN>`); the state preamble that restores `elitea_state` / `alita_state` / `alita_client`; and your node code wrapped in an async runner so top-level `await` works in stock CPython.

- **Bucket:** **`code-debug`** — hyphen. (Verified live 2026-07-13. The 2.0.4 release notes say `code_debug`; the release notes are **wrong**, the node reference is right.)
- **Mode:** the bucket lives under mode **`default`**, not `prompt_lib` — `GET /api/v2/artifacts/artifacts/default/{pid}/code-debug`. Using `prompt_lib` here 404s.
- **Filename:** `{node_id}__{YYYYMMDD}_{HHMMSS}.py`
- **Retention:** the bucket auto-expires (~30 days). Don't treat debug artifacts as durable.
- **Best-effort:** if the upload fails, the pipeline keeps running and logs a warning. No artifact ≠ no execution.
- **To reproduce locally:** download it, replace `<YOUR_AUTH_TOKEN>`, `pip install requests chardet`, run.

This is the fastest way to see the *actual serialized state* your node received — which is exactly what you need for the `[Errno 7] Argument list too long: 'deno'` failure (see `workflows.md`), where the state has silently grown past the sandbox's argument limit.

**I/O defaults:** `input` defaults to `["input"]`; `output` defaults to `[]`.

**Structured-output behaviour** (from the docs — this is the mechanism behind the "my result didn't surface" bug):
- Only variables listed in `output` get updated.
- Variables not declared in the pipeline `state` are **silently ignored**.
- **If `output` is omitted, or includes `messages`, the result is appended to `messages`.**
- Non-`messages` output variables are overwritten with the result (or with an error message).

Code Node rules:
- Use `alita_state.get('var', default)` to access state
- **A code node's `input:` (and `output:`) MUST be a flat list of state-variable-name STRINGS** —
  e.g. `input: [n, doubled]`. It must NOT be a list of objects like
  `input: [{name: n, source: state, value: n}]` — that fails graph build with
  `ValidationError: input_variables.0 Input should be a valid string`. (The dict / `input_mapping`
  form is ONLY for `llm`/`toolkit`/`mcp` nodes, never for `code` nodes.)
- **A code node only RECEIVES the state variables listed in its `input:`.** `alita_state.get('x')`
  returns the default (e.g. `0`/`None`) for any var NOT in `input:`, even if it's set in `state` and
  populated by an earlier node. When you add a new state var that a code node must read, you MUST add
  it to that node's `input:` list — this is a silent, common bug (the node "ignores" the value).
- Return a dict literal as the LAST expression with `structured_output: true` for state updates
  (e.g. `{'report': report}`). Do NOT use a top-level `return` — code runs at module scope, not
  inside a function, so `return` is a syntax error. Guard early-exits with `if/else` or `raise`
  inside a `try`, keeping the dict literal as the final statement.
- Use `httpx.AsyncClient` for HTTP (not `requests`); top-level `await` is allowed
- Use `micropip` for package installation
- `alita_client` is available for artifact/bucket/app operations

**6. Custom Node** — Advanced manual JSON configuration
```yaml
- id: <unique_id>
  type: custom
  input: [input]
  output: [messages]
  config:
    toolkit_type: "advanced_toolkit"
    parameters:
      custom_param1: "value1"
  transition: END
```

### Control Flow Nodes

**7. Router Node** — Template-based conditional routing (fast, no LLM)
```yaml
- id: <unique_id>
  type: router
  condition: |
    {% if 'approved' in input|lower %}
    ApproveNode
    {% elif 'reject' in input|lower %}
    RejectNode
    {% else %}
    END
    {% endif %}
  input: [input]
  routes:
    - ApproveNode
    - RejectNode
    - END
  default_output: DefaultNode
```

**8. Decision Node** — LLM-powered intelligent routing
```yaml
- id: <unique_id>
  type: decision
  description: |
    Route based on user intent:
    - publish content → ArticlePublisher
    - review content → ContentModerator
    - finish → END
  input: [input, messages]
  nodes:
    - ArticlePublisher
    - ContentModerator
  default_output: END
```

**9. HITL Node** — Human-in-the-Loop: pause for an Approve / Edit / Reject decision

Distinct from `printer` (which only displays): `hitl` presents a message and waits for a human to choose
a route. Uses **`routes`** (a DICT mapping the decision to a node id), NOT `transition`. An `edit` route
REQUIRES `edit_state_key` — a real state variable the human's edit is written into (it must NOT be `END`).
Needs a runtime checkpoint/thread to resume, so — like `printer` — it **BLOCKS forever in a
scheduled/webhook/headless pipeline**; only use it in interactive ones.

```yaml
- id: <unique_id>
  type: hitl
  user_message:
    type: fstring            # fixed | variable | fstring
    value: 'Approve this change?\n\n{proposed}'
  input: [proposed]
  routes:
    approve: ApplyChange     # each value is a node id (or END)
    reject: END
    edit: ReviseDraft        # only include the routes you actually want as buttons
  edit_state_key: proposed   # REQUIRED when an `edit` route exists; a real state var, never END
```

### Utility Nodes

**10. State Modifier Node** — Transform state with Jinja2 templates
```yaml
- id: <unique_id>
  type: state_modifier
  template: '{{ counter + 1 }}'
  variables_to_clean: []
  input: [counter]
  output: [counter]
  transition: <next_node_id>
```

Available custom Jinja2 filters:
- `|from_json` — parse a JSON string into an object (e.g. `{{ api_response|from_json }}`)
- `|base64_to_string` — decode base64-encoded data
- `|split_by_words(n)` — split text into chunks of `n` words
- `|split_by_regex('pattern')` — split text using a regex pattern

Standard filters also work: `|upper`, `|lower`, `|length`, `|default('fallback')`

**11. Printer Node** — Display output to the user and pause for acknowledgement

The Printer Node shows a message to the user and **automatically pauses** the pipeline until the user types anything to continue. Use it for progress updates, review checkpoints, and final output display.

`input_mapping.printer` is the **required field name** — the value can be `fixed`, `variable`, or `fstring`.

```yaml
- id: <unique_id>
  type: printer
  input_mapping:
    printer:
      type: fstring          # fixed | variable | fstring
      value: 'Found {count} results in {project_name}'
  transition: <next_node_id>  # or END
```

> **Note:** If `transition: END`, the pipeline does not fully complete until the user provides input to acknowledge the message.

## Connection Rules

- **`transition`**: Simple single-target connection (most nodes)
- **`routes`** + **`condition`**: Multi-path routing (Router)
- **`nodes`** + **`description`**: LLM-powered routing (Decision)
- **`END`**: Terminate pipeline execution
- Every path must eventually reach END
- **Any node type can be the `entry_point` — including `router` and `decision`.** (See below; this contradicts several doc pages.)
- Decision nodes cannot chain directly to other Decision nodes

> ✅ **`router` and `decision` CAN both be `entry_point` — settled empirically (project 9, 2026-07-13).**
> Not merely "saved without error": both **executed**. A `router` entry_point evaluated its Jinja condition
> against `input="apple"` and branched correctly. A `decision` entry_point ran a real LLM decision
> (`thinking_steps` shows the model emitting the chosen node) and branched correctly.
>
> **The docs are wrong here, in both directions.** `nodes-connectors.md` and `yaml.md` say *"Router nodes
> cannot be entry points"*; `entry-point.md` permits Router but forbids Decision. All three are contradicted
> by the running platform. Earlier versions of this file repeated the doc claim — it was never verified.
>
> Practical note: a Router entry_point still needs its `condition` to evaluate against whatever state exists
> at entry (typically `input`). "Can't be an entry point" was probably a garbled version of "has nothing
> useful to route on unless you give it something" — which is a design caution, not a platform rule.

## Input Mapping Types

| Type | Purpose | Example |
|------|---------|---------|
| `fixed` | Static, unchanging value | `value: "Hello"` |
| `variable` | Reference to state variable | `value: user_input` |
| `fstring` | Template with `{var}` interpolation | `value: "Process {data}"` |

## Legacy Node Types (Pipeline Agent Framework) — REFERENCE ONLY

> **DO NOT USE legacy node types when building new pipelines.** They are documented here solely so you can understand and debug existing pipelines that use them. For new pipelines, always use the modern equivalents.

**Legacy → Modern Mapping:**

| Legacy Node | Modern Equivalent | Notes |
|-------------|-------------------|-------|
| `tool` | `agent` or `toolkit` | Use `agent` for delegating to agents/prompts; `toolkit` for direct tool calls |
| `function` | `agent` or `toolkit` with `input_mapping` | `agent`/`toolkit` nodes provide the same explicit input mapping |
| `loop` | `code` node with loop logic | Implement iteration in a Code node with Router for control flow |
| `loop_from_tool` | `toolkit` + `code` + `router` | Chain a toolkit call → code processing → router loop |
| Inline `condition` | `router` node | Use a separate Router node for Jinja2-based branching |
| Inline `decision` | `decision` node | Use a separate Decision node for LLM-powered routing |

The original Pipeline Agent Framework uses a different set of node types. They may be encountered in existing pipelines.

### `tool` Node — Simple entity delegation (uses LLM internally for input prep)
```yaml
- id: <unique_id>
  type: tool
  tool: <entity_name>          # Name of ELITEA prompt, agent, or datasource
  input: [input]               # Optional
  output: [result]             # Optional
  structured_output: false
  transition: <next_node_id>
```
**Note:** `tool` nodes use LLM overhead internally to prepare inputs. Use `function` nodes for more token-efficient execution.

### `function` Node — Direct ELITEA entity call with explicit input mapping
```yaml
- id: <unique_id>
  type: function
  input: [state_var]           # Mandatory
  output: [result_var]         # Mandatory
  input_mapping:
    task:                      # For agents
      type: fstring            # variable | fstring | fixed
      value: "Process: {state_var}"
    chat_history:              # For agents
      type: fixed
      value: []
    input:                     # For prompts (without variables)
      type: variable
      value: state_var
    query:                     # For datasources
      type: fstring
      value: "Search for {topic}"
  transition: <next_node_id>
```

### `loop` Node — Repeat a task for each item

The entity is named by **`toolkit:`**, not `tool:`. `tool:` appears only when the target is a Toolkit or MCP — it is absent when delegating to an Agent or Pipeline.

```yaml
- id: "process_files"
  type: "loop"
  toolkit: "Code Documentation Agent"
  task: |
    Formulate ALL file paths from chat_history as a list of inputs.
    For each file path, create input as:
    - "task": the file path
    - "chat_history": the entire conversation history
  input: ["messages"]
  output: ["documentation"]
  structured_output: false
  transition: "END"
```

### `loop_from_tool` Node — Iterate over dynamically generated items

Two-stage: `toolkit` + `tool` generate the list **once**; `loop_toolkit` + `loop_tool` then run **per item**. `variables_mapping` (mapping the list-tool's output fields → the loop-tool's input params) is **mandatory**.

```yaml
- id: "document_github_files"
  type: "loop_from_tool"
  toolkit: "GitHub Expert"
  tool: "getFilesFromDirectory"
  loop_toolkit: "Code Documentation Agent"
  variables_mapping:
    file_path: "task"
    file_content: "source_code"
  input: ["repository_name"]
  output: ["documentation"]
  structured_output: true
  transition: "create_readme"
```

## Inline Conditions & Nested Decisions — REFERENCE ONLY (but read the caveat)

In the legacy framework, `condition` and `decision` are **attributes within nodes** (typically `llm` nodes), not separate node types. **For new pipelines, use the flat `router` and `decision` node forms documented above.**

> ⚠️ **The nested `decision:` block is not clearly dead.** Our flat Decision form matches `control-flow-nodes.md`
> (the dedicated node page, and the newest — it's the one that gained HITL). But `yaml.md`, `nodes-connectors.md`
> **and** `nodes/overview.md` all still present the **nested** `decision:` block as current, and the nested form
> supports a `tool_names` key that the flat form's docs never mention:
>
The nested form, as those pages still document it:

```yaml
- id: SmartRouter
  type: decision
  input: [user_input]
  output: [classification]
  decision:
    description: |
      Route to SaveNode if user wants to save, otherwise END
    decisional_inputs: [user_input]
    nodes: [SaveNode]
    default_output: END
  tool_names:              # optional — nested form only
    toolkit1: [tool_a]
```

**Keep authoring the flat form.** But a nested `decision:` in an existing pipeline is not necessarily stale, and if you need `tool_names` the nested form may be your only option. The docs are internally inconsistent here.

### Inline Condition (within an `llm` or `function` node)
```yaml
- id: UserApproval
  type: llm
  input: [input]
  prompt:
    type: string
    value: "Provide details and type 'approved' when ready."
  output: [data_field]
  structured_output: true
  condition:
    condition_input: [data_field, input]
    condition_definition: |
      {% if 'approved' in input|lower and data_field %}
      NextStep
      {% else %}
      UserApproval
      {% endif %}
```

### Inline Decision (within an `llm` node)
```yaml
- id: UserFeedback
  type: llm
  input: [enhanced_us, input]
  prompt:
    type: fstring
    value: "Review this: {enhanced_us}. Type Publish, Edit, or Finish."
  output: [user_feedback]
  decision:
    nodes: ["PublishStory", "RequestEdit", "END", "UserFeedback"]
    description: "Route based on user feedback keywords."
    decisional_inputs: ["input"]
    default_output: "UserFeedback"
```
