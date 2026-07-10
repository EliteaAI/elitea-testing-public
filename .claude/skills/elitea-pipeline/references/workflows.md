# Workflows, Best Practices, Troubleshooting

Operational guidance for building, debugging, and operating ELITEA pipelines.

## When Creating a Pipeline

1. **Clarify requirements**: Understand inputs, outputs, integrations needed
2. **Design state**: Define all state variables with appropriate types and defaults
3. **Plan node flow**: Sketch the node sequence, branching, and loops
4. **Generate YAML**: Produce valid YAML following the schema exactly
5. **Validate**: Check entry_point references exist, all transitions resolve, state vars are defined
6. **Test incrementally**: Add one node at a time, use interrupts to inspect state

## When Debugging a Pipeline

1. **Check YAML syntax**: Indentation (spaces not tabs), quotes around special chars
2. **Verify entry_point**: Must reference an existing node ID
3. **Check transitions**: All must point to existing nodes or END
4. **Validate state**: All variables used in nodes must be defined in `state`
5. **Inspect input/output**: Ensure node I/O arrays match state variables
6. **Use interrupts**: Add `interrupt_before`/`interrupt_after` to inspect state at key points
7. **Check structured_output**: When true, code/LLM must return dict with keys matching output vars
8. **Review input_mapping**: Ensure correct types (fixed/variable/fstring) and values

## Validation Checklist

- [ ] `entry_point` references an existing node ID
- [ ] All node IDs are unique
- [ ] All transitions reference existing nodes or END
- [ ] State variables in nodes are defined in `state`
- [ ] Input/output arrays use valid variable names
- [ ] Node-specific fields complete (LLM has `input_mapping`, Router has `condition` + `routes`, etc.)
- [ ] No YAML syntax errors (proper indentation with spaces)
- [ ] Quotes around special characters (`:`, `{`, `%`)
- [ ] Every execution path reaches END
- [ ] Router has `default_output` set

## Using MCP Tools for Development

- **Inspect existing pipelines**: Use `getEliteaCoreApplication` to review current configurations
- **List available tools**: Use `getEliteaCoreTools` to see what toolkits/MCPs are available in a project
- **Test tool I/O**: Use Artifact and TestRail toolkit tools directly to understand input/output shapes before wiring them into pipeline nodes
- **Deploy changes**: Use `putEliteaCoreVersion` to update pipeline YAML on the platform
- **Test execution**: Use `postEliteaCorePredict` to run an agent/pipeline version with test inputs

## Best Practices

- Use descriptive node IDs (`FetchUserData` not `Node1`)
- Initialize all state variables with sensible defaults
- Keep state minimal — only create variables you need
- Use Code nodes for complex logic, LLM nodes for intelligence
- Use Router for deterministic branching, Decision for semantic routing
- Always provide `default_output` for Router and Decision nodes
- Include `messages` in output when using interrupts with structured output
- Add comments in YAML to explain complex logic
- Test incrementally: build and verify one node at a time
- Use `alita_state.get('var', default)` in Code nodes to handle missing state gracefully
- Never hardcode secrets — use Credentials/`alita_client.unsecret()`
- Clean up unused state with State Modifier and `variables_to_clean`

## Code Node Special Capabilities

The Code Node's `alita_client` provides access to:

**Artifact Operations:**
```python
bucket = alita_client.artifact('bucket-name')
bucket.create('file.txt', 'content')
content = bucket.get('file.txt')
bucket.list()
bucket.append('file.txt', 'more data')
bucket.overwrite('file.txt', 'new content')
bucket.delete('file.txt')
```

**Application & Integration:**
```python
alita_client.get_app_details(application_id=123)
alita_client.get_list_of_apps()
alita_client.unsecret('secret-name')
alita_client.get_mcp_toolkits()
alita_client.mcp_tool_call(params)
```

**Image Generation:**
```python
alita_client.generate_image(prompt, n=1, size='auto', quality='auto')
```

## Pipeline LLM-node gotchas (verified live)

Runtime behaviours of `llm` nodes *inside a pipeline* (the LangGraph path), distinct from the stateless `predict_llm` endpoint. All bit hard during a real build (`AgentStudioGrader`, project 630, 2026-06-25).

- **`reasoning_effort` → 0 tokens (Haiku 4.5).** The nastiest one. With `llm_settings.reasoning_effort` set (even `"low"`), every pipeline `llm` node emits **zero** output tokens; structured-output vars stay at their defaults, so the whole run looks like the model returned the minimum / nothing. `predict_llm` tolerates the same setting and returns content, so the model looks fine in isolation. **Omit `reasoning_effort` from a pipeline's `llm_settings`** (set just `{model_name, model_project_id, temperature, max_tokens}`; overwrite the whole dict so a prior value isn't inherited). Full write-up + the bisection: `elitea-platform/references/conventions.md` §11.
- **`max_tokens` too low truncates the structured JSON.** A `structured_output: true` llm node returns JSON; if `max_tokens` is small (e.g. 1500) and the model is verbose (Anthropic structured output also emits a secondary `elitea_response` narrative beyond your schema), the JSON is cut off mid-object → parse fails → vars default. Budget generously (3000–5000) even though the JSON itself is tiny. Also: **`temperature` must be > 0** on create (0 → `400 greater_than`).
- **Structured output is forgiving, not free.** The model often wraps JSON in ```` ```json ```` fences and/or adds extra keys; the framework retries and usually recovers, but each retry is another generation (token cost). Instruct "raw JSON only, no code fences, no extra keys" to cut retries.
- **`llm` node `task` must be `fixed` or `fstring`, NOT `variable`.** `input_mapping.task: {type: variable, value: myvar}` silently passes empty content → the LLM gets no task → 0 tokens / default output. Use `{type: fstring, value: '{myvar}'}` (Python `.format` does **not** re-parse `{...}` braces inside the substituted value, so brace-heavy content like `{{glossary}}` is safe).
- **Diagnosing "the LLM didn't really run":** read `llm_response_tokens_output` in the predict response. `0` = no generation happened (suspect `reasoning_effort` or a task-rendering error); `>0` but outputs still at default = generation happened but parsing/mapping failed (suspect truncation or fences).

## Pipeline state size limit — deno ARG_MAX (use lazy fetch)

The pyodide/`deno` sandbox that runs `code` nodes receives the **entire pipeline state serialized as a single CLI argument** (base64+zlib). A single argument is capped (Linux `MAX_ARG_STRLEN` ≈ 128 KB). If a code node stuffs bulk data into state — e.g. the full instructions of dozens of entities you plan to iterate over — a later code node dies with **`{"error": "Error executing code: [Errno 7] Argument list too long: 'deno'"}`** even though its own logic is fine.

**Pattern — don't preload bulk data into state; fetch lazily per iteration.** Store only lightweight metadata (ids, names, a `default_version_id`) for the whole work-list; in the loop body, a `code` node fetches the ONE current item's heavy payload on demand and writes just that into state. Cap any single large field (e.g. `instr[:30000]`). State stays small regardless of work-list size. (`AgentStudioGrader`: `Fetch` builds light `agents_meta`; a `PrepOne` code node fetches one agent's full version each loop turn.)

**Loop step budgeting:** a router-loop costs ~N graph-steps per item (router + each processing node in the body). Set `meta.step_limit` to `≈ steps_per_item × item_count + overhead` — a 4-node-per-item loop over ~70 items needs ~300–400, far above the default 25.

## Response Format

When generating pipeline YAML:
1. Always produce **complete, valid YAML** — never partial snippets
2. Include all required fields for every node type
3. Add inline comments explaining non-obvious logic
4. Follow the validation checklist before presenting
5. Explain the pipeline flow in a brief summary before/after the YAML

When debugging:
1. Identify the specific issue with clear explanation
2. Show the exact fix needed
3. Explain why the fix works

When explaining concepts:
1. Be concise but thorough
2. Use examples from the schema reference
3. Link back to relevant patterns

## Troubleshooting Quick Reference

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Agent won't start | `entry_point` doesn't match any node `id` | Verify exact spelling and case |
| YAML syntax errors | Tabs instead of spaces, or bad indentation | Use spaces only; use YAML Indentation Corrector prompt |
| Unexpected transitions | Wrong `transition`/`condition`/`decision` target | Check all node ID references for typos |
| Node not found | Node ID mismatch (case-sensitive) | Ensure IDs match exactly across transitions, conditions, decisions |
| Wrong state data | State variables not updated correctly | Use `interrupt_before`/`interrupt_after` to inspect state at key points |
| Condition logic errors | Bad Jinja2 syntax in `condition_definition` | Verify `{% if %}` / `{% elif %}` / `{% else %}` / `{% endif %}` blocks |
| Function node fails | Incorrect `input_mapping` types/values | Verify `type` (variable/fstring/fixed) and `value` for each mapped param |
| Toolkit not working | Toolkit not added/configured in agent settings | Add all required toolkits in Configuration tab with correct versions |
| `messages` lost | `messages: list` missing from custom `state` | Always include `messages: list` when defining custom state |
| LLM node returns nothing / all structured outputs at their defaults | `reasoning_effort` set on a pipeline llm node (→ 0 tokens), `max_tokens` too low (truncated JSON), or `task: {type: variable}` (empty task) | Omit `reasoning_effort`; raise `max_tokens` (3000–5000); use `task: fstring`. Check `llm_response_tokens_output` (0 vs >0) to tell which. |
| `[Errno 7] Argument list too long: 'deno'` | Pipeline state too large (bulk data preloaded) serialized to a code node | Keep only lightweight metadata in state; fetch heavy per-item payloads lazily inside the loop; cap large fields. |

**Debugging Strategy:** Isolate → add interrupts → inspect state → trace transitions → review error messages in Chat window.

## Quick Reference: Common MCP Workflows

### Workflow 1: Create conversation and send a message

```
1. getAuthUser                      → get user info & personal_project_id
2. postEliteaCoreConversations      → create conversation, get conversation_id and uuid
3. postEliteaCoreParticipants       → add agent participant to conversation
4. patchEliteaCoreEntitySettings    → configure LLM settings
5. postEliteaCoreMessages           → send user_input using conversation_uuid
```

### Workflow 2: List agents and get details

```
1. getProjectsProject               → list available projects
2. getEliteaCoreApplications        → list agents in a project
3. getEliteaCoreApplication         → get full details for a specific agent
```

### Workflow 3: Create agent with toolkit

```
1. postEliteaCoreApplications       → create agent with initial version
2. getEliteaCoreTools               → list available toolkits
3. patchEliteaCoreTool              → link toolkit to agent version
```

### Workflow 4: Upload file and reference in message

```
1. postEliteaCoreAttachments        → upload file, get filepath
2. postEliteaCoreMessages           → send message with attachments_info containing the filepath
```

### Workflow 5: Direct agent execution (without conversation)

```
1. getEliteaCoreApplication         → get agent details with version_id
2. postEliteaCorePredict            → execute agent directly with version_id
```

### Workflow 6: Manage agent versions

```
1. getEliteaCoreApplication         → get current agent with version details
2. postEliteaCoreVersions           → create a new version
3. putEliteaCoreVersion             → update version configuration
4. patchEliteaCoreTool              → link/unlink toolkits to version
```

### Workflow 7: Browse conversation history

```
1. getEliteaCoreConversations       → find conversation by name/query
2. getEliteaCoreConversation        → get conversation details with participants
3. getEliteaCoreMessages            → paginate through messages
```

## Key Gotchas

| Gotcha | Details |
|--------|---------|
| `postEliteaCoreMessages` uses UUID | The `conversation_uuid` parameter is a UUID string, **not** the integer `conversation_id`. Get it from the conversation's `uuid` field. |
| `postEliteaCorePredict` uses `version_id` | Execute against a specific version, not the application ID. Get it from `version_details.id`. |
| `mode` defaults to `prompt_lib` | Almost all tools default to `"prompt_lib"` mode. You rarely need to change this. |
| Pipeline instructions must be YAML | When `agent_type` is `"pipeline"`, the `instructions` field must contain valid YAML. |
| Version name cannot be `"base"` | When creating versions with `postEliteaCoreVersions`, the name `"base"` is reserved. |
| `meta.step_limit` defaults to 25 | Agent versions default to 25 execution steps. Override via `meta.step_limit`. |
| `author_id` is auto-set | Fields like `author_id` and `owner_id` are automatically set from the authenticated user — do not pass them manually. |

## Pipeline entry-point triggers (ELITEA 2.0.3+)

Before 2.0.3 every pipeline was driven by a user chatting with it (or an external system calling `POST /predict/...`). 2.0.3 introduced **entry-point triggers** declared at the pipeline level — the pipeline runs automatically when its trigger fires.

| Trigger | When it fires | Allowed in pipeline |
|---|---|---|
| `chat` (default) | User sends a message to the pipeline (chat UI, REST, MCP) | All node types — including HITL, Printer, anything that needs user interaction |
| `scheduled` (cron) | Cron expression matches | **No** HITL nodes, **no** Printer nodes, **no** interrupt-requiring nodes. There is no user to interact with. |
| `webhook` | External system POSTs to the pipeline's webhook URL | Same constraint as scheduled — no interactive nodes |

**Hard constraint:** if a pipeline contains any HITL, Printer, or interrupt node, only `chat` is a valid trigger. Switching such a pipeline to `scheduled` or `webhook` will fail validation. To use cron/webhook, refactor the interactive parts out (e.g. replace a Printer with a code node that writes to a state variable, or move HITL to a downstream chat-triggered pipeline).

**Implications for nudging / scheduled scans:** the `ConversationHealthAnalyzer` example pipeline has no Printer or HITL nodes, so it runs natively on a `scheduled` trigger — replacing the GH Actions cron + REST shim in `elitea_support/.github/workflows/nudge-failed-conversations.yaml`. The native trigger is **verified firing reliably** (project 630, cron `45 * * * *`, hundreds of runs). Keep the GH-Actions path only when the pipeline has interactive nodes OR you need pre/post logic outside the pipeline; see `elitea-testing/references/nudge-case-study.md` § "Scheduling".

**Configuration:** the trigger is set on the pipeline VERSION via the platform UI (Pipeline Studio → entry-point node settings) or via REST (`PUT /api/v2/elitea_core/pipeline_trigger/prompt_lib/{project_id}/pipeline/{version_id}/trigger` — note the `pipeline_trigger/prompt_lib` prefix; the shorter form 404s). Exact body shape varies per trigger type; consult the live OpenAPI spec at `https://next.elitea.ai/api/v2/elitea_core/openapi.json` for the current schema (the release notes don't pin it down).

## Operating & debugging scheduled runs

Once a `scheduled` trigger is armed, the cron firing and the pipeline *doing the right thing* are two separate questions. Verified live (project 630, 2026-06-22):

**Where the run history lives.** Each fire creates a conversation named `Scheduled run: <pipeline name>` with **`source: "pipeline"`** (not `elitea`), conversation `meta.scheduled_run: true`, and a seed user message with `meta.scheduled_trigger: true` and content `[Scheduled execution triggered]`. **This is the pipeline's "predict/run history."** Because the default `GET /conversations/...` list filters `source=elitea`, these runs are invisible there — list them with `?source=pipeline`, or GET one directly: `GET /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_id}`. The assistant message group in that conversation holds the run's output (e.g. the report a code node appended to `messages`).

**Three silent failure modes** (the cron looks healthy — `last_run` advances — but nothing useful happens):

| Symptom | Cause | Fix |
|---|---|---|
| `last_run` advances, **no `Scheduled run:` conv created** | Sub-hourly cron (e.g. `*/5 * * * *`). Accepted by PUT (200) but never executes — hourly is the minimum granularity. | Use `0 * * * *` or coarser. |
| `last_run` advances, **no conv**, hourly cron | Pipeline contains a Printer / HITL / interrupt node — blocked silently (no error surfaced). | Remove interactive nodes (route the entry code node straight to `END`), or keep the `chat` trigger. |
| Conv **is** created, but the run does the wrong thing | Trigger config got **wiped by a version PUT** (it lives in `pipeline_settings.trigger`), OR the code mis-reads the trigger input (below). | Re-arm the trigger after every version PUT; fix input detection. |

**The cron-detection trap (code-node pipelines).** A pipeline that needs to behave differently when cron-invoked vs chat-invoked **cannot reliably tell the difference from state.** The `[Scheduled execution triggered]` marker is the *message content* and the `meta.scheduled_trigger` flag, but it does **not** reliably reach `elitea_state.get('input')` **or** `elitea_state.get('messages')` at the entry node (a custom `state` block that doesn't declare `input` makes it worse). `ConversationHealthAnalyzer` first tried `'[Scheduled execution triggered]' in input`, then a `messages` scan — **both** silently evaluated False on every scheduled run, so the pipeline took its chat/default branch and ran 7-day **DRY-RUN** every hour: finding the errored conversations but never nudging.

**Robust fix — don't detect cron; invert the default.** Make the action-taking mode (APPLY) the default and make the safe/preview mode (DRY-RUN) opt-in via an explicit token in the chat input. A scheduled run carries no such token, so it applies; a human previews by typing `dryrun`:

```python
user_input = (elitea_state.get('input', '') or '').strip()
# DRY-RUN only when the human explicitly asks; everything else (incl. every
# scheduled run, whatever its input) APPLIES. No trigger detection needed.
APPLY = not bool(re.search(r'\bdry(?:[\s_-]?run)?\b', user_input, re.IGNORECASE))
```

This is the deployed resolution (projects 630 & 2667, verified 2026-06-22). Window/`project=` parsing still come from the input when a human supplies them. General principle: **if a behavioural switch can't be derived reliably from runtime state, make the safe-to-omit mode the default and require an explicit opt-in for the other** — don't gate the important behaviour on a signal you can't see. Worked end-to-end in `elitea-testing/references/nudge-case-study.md` § 7 (lesson 14).

## Webhook + scheduled triggers vs interactive nodes — failure mode

If you try to switch a pipeline with a Printer/HITL/interrupt node to `scheduled` or `webhook`, the platform will either reject the change at save time OR (worse) accept it but silently skip the interactive step at runtime. Either way the pipeline doesn't behave as designed. Symptom in logs: the trigger fires, the pipeline starts, but execution stops at the interactive node with no error surfaced to any user (because there isn't one). Prevention: validate locally — search your pipeline YAML for `type: printer`, `type: custom` (with HITL flag), and any node with `interrupt: true`; if any are present, keep the trigger at `chat`.
