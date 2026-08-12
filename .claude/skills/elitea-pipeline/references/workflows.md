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

0. **If the problem is in a `code` node, turn on `debug: true` first.** Don't guess at what the node received — read it. ELITEA writes the fully assembled Python (sandbox client preamble + the *actual injected state* + your code in an async runner) to the **`code-debug`** artifact bucket (mode `default`, i.e. `GET /api/v2/artifacts/artifacts/default/{pid}/code-debug`) as `{node_id}__{YYYYMMDD}_{HHMMSS}.py`. Download it, replace `<YOUR_AUTH_TOKEN>`, `pip install requests chardet`, and run it locally to reproduce the exact failure. This supersedes the interrupt-and-inspect dance below for code-node bugs, and it's the only practical way to see a state blob that has grown past the sandbox's argument limit (see "Pipeline state size limit" below).
1. **Check YAML syntax**: Indentation (spaces not tabs), quotes around special chars
2. **Verify entry_point**: Must reference an existing node ID
3. **Check transitions**: All must point to existing nodes or END
4. **Validate state**: All variables used in nodes must be defined in `state` — and remember that on a **new** pipeline, `input` and `messages` are added but **disabled**; enable them or every `elitea_state.get('input')` returns empty
5. **Inspect input/output**: Ensure node I/O arrays match state variables
6. **Use interrupts**: Add `interrupt_before`/`interrupt_after` to inspect state at key points
7. **Check structured_output**: When true, code/LLM must return dict with keys matching output vars
8. **Review input_mapping**: Ensure correct types (fixed/variable/fstring) and values
9. **Check the Pipeline Runs view** (Flow Editor): node-by-node timeline, per-node state snapshots before/after, stack traces. Run statuses are **In Progress / Completed / Error / Stopped / Interrupt**.

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

MCP tool names are **`snake_case`** (an older version of this file used camelCase — those names don't exist).

- **Inspect existing pipelines**: `get_elitea_core_application` to review current configuration
- **List available tools**: `get_elitea_core_tools` to see what toolkits/MCPs a project has
- **Test tool I/O**: call the toolkit's tools directly to learn their input/output shapes before wiring them into nodes
- **Deploy changes**: `put_elitea_core_version` to update pipeline YAML on the platform
- **Test execution**: ⚠️ **there is no MCP predict any more** — the `postEliteaCorePredict` tool was withdrawn. Run the pipeline over REST: `POST /api/v2/elitea_core/predict/prompt_lib/{pid}/{version_id}`. Same for reading replies: there's no MCP message-read either. MCP is a build-and-browse surface now, not a runtime one — see `elitea-platform/references/mcp-tools.md`.

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

**Artifact Operations (via the bucket handle):**
```python
bucket = alita_client.artifact('bucket-name')
bucket.create('file.txt', 'content')
content = bucket.get('file.txt')
raw    = bucket.get_content_bytes('image.png')     # bytes, not str
bucket.list()
bucket.append('file.txt', 'more data')
bucket.overwrite('file.txt', 'new content')
bucket.delete('file.txt')
```

**Bucket Operations (directly on the client)** — these are what you need to read an attachment or a `debug: true` artifact:
```python
alita_client.bucket_exists('attachments')
alita_client.create_bucket('my-bucket', expiration_measure='months', expiration_value=1)
alita_client.list_artifacts('attachments')
alita_client.create_artifact('my-bucket', 'file.txt', data)
alita_client.download_artifact('attachments', 'report.pdf')
alita_client.delete_artifact('my-bucket', 'file.txt')
```

**Application & Integration:**
```python
alita_client.get_app_details(application_id=123)
alita_client.get_app_version_details(application_id=123, application_version_id=456)
alita_client.get_list_of_apps()
alita_client.unsecret('secret-name')
alita_client.get_mcp_toolkits()
alita_client.mcp_tool_call(params)
alita_client.get_integration_details(integration_id, format_for_model=False)
alita_client.fetch_available_configurations()
alita_client.all_models_and_integrations()
```

**User:**
```python
alita_client.get_user_data()
```

**Image Generation:**
```python
alita_client.generate_image(prompt, n=1, size='auto', quality='auto',
                            response_format='b64_json', style=None)
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
| `[Errno 7] Argument list too long: 'deno'` | Pipeline state too large (bulk data preloaded) serialized to a code node | Keep only lightweight metadata in state; fetch heavy per-item payloads lazily inside the loop; cap large fields. **Set `debug: true` to see the exact serialized state that blew the limit.** |
| `Entry point is not defined in the schema. Please define 'entry_point' in the schema.` | No `entry_point` set | Add one, referencing an existing node id. |
| `Transition target 'Next Step' not found` | A `transition` points at a node that doesn't exist | Fix the id (case-sensitive) or add the node. |
| `Missing required parameter: issue_key` / `During task with name 'Fetch Jira Ticket'` | An `input_mapping` references a state var that's undefined or empty | Declare it in `state` with a default. |
| `Expected type 'int' but got 'str' for variable 'count'` | State type mismatch | Cast in a code node before the consuming node. |
| `Object is not serializable` | A code node returned a class/function instance | Return only JSON-serializable types. |
| Debug enabled but no artifact appears | Debug capture is best-effort; or you looked in the wrong mode | Confirm `debug: true`; list the bucket under mode **`default`** (`/api/v2/artifacts/artifacts/default/{pid}/code-debug` — `prompt_lib` 404s); look for `{node_id}__{YYYYMMDD}_{HHMMSS}.py`; check runtime logs for an upload warning. Bucket auto-expires (~30d). |
| Downloaded debug file won't run locally | Placeholder token / missing deps | Replace `<YOUR_AUTH_TOKEN>`; `pip install requests chardet`. |

**Debugging Strategy:** For code nodes — **`debug: true` → read the assembled source + injected state**. Otherwise: isolate → add interrupts → inspect state → trace transitions → review error messages in the Chat window.

## File attachments into a pipeline

Enabling **Allow attachments** (Configuration → INTERNAL TOOLS) does two things: it adds `attachments` to the pipeline's internal tools, **and it injects an `input_attachments` state variable into the pipeline YAML**. The paperclip then becomes active when the pipeline is used in a conversation.

What's documented and reliable:

- Uploaded files always go to the project's default **`attachments`** bucket. No Artifact-toolkit configuration is needed. Default retention: **30 days**.
- Duplicate filenames are auto-renamed with a timestamp and size: `image_20251106_143022_1.50KB.png`.
- **Images** go straight to the LLM's vision input. **Non-image files** are extracted and indexed into a vector DB, then reached by semantic search.
- ⚠️ **All non-image attachments share ONE collection** in the `attachments` bucket. Retrieval can therefore leak content across files — query specifically and reference filenames explicitly.
- SVG is treated as a **document**, not an image (so it's exempt from the per-image size cap).

### `input_attachments` — the shape, verified end-to-end (project 9, 2026-07-13)

**It's a `list[str]`. Each element is an artifact path**, not a filename and not an object:

```
"attachments/{conversation_uuid}/{filename}"
```

**The state declaration is what makes it work — not the internal-tools toggle.** This is the surprise, and it contradicts how the docs frame it:

```yaml
state:
  input_attachments:
    type: list      # <-- THIS is what populates the variable
  messages:
    type: list
```

Verified: with the state var declared, `input_attachments` populates **even with `internal_tools: ["attachments"]` removed**. The toggle is a UI-side affordance — it edits the YAML for you and lights up the paperclip. The runtime only cares about the declared state variable.

**And if you *don't* declare the state var, the attachment is invisible to state.** It gets appended to `input` as prose instead:

```
...  Attached document: {uuid}/probe.txt (attachments/{uuid}/probe.txt)
```

which is a miserable thing to have to parse. Declare the variable.

**Reading the file** (verified working):

```python
paths = alita_state.get('input_attachments', [])   # ['attachments/<uuid>/probe.txt', ...]
for p in paths:
    bucket, _, name = p.partition('/')             # bucket == 'attachments'
    content = alita_client.artifact(bucket).get(name)      # name == '<uuid>/probe.txt'
    # raw bytes: alita_client.artifact(bucket).get_content_bytes(name)
```

Over REST the same file is at `GET /api/v2/artifacts/artifact/default/{pid}/attachments/{conv_uuid}/{filename}`.

> **Bonus finding from the same probe:** a code node's injected preamble is fully readable in the predict response under `tool_calls_dict[*].tool_inputs.code`. `elitea_state` is a plain `dict`, rehydrated from a zlib+base64 JSON blob. Baseline runtime state keys are `input`, `state_types`, `hitl_decisions`, `parallel_tasks`.

## Quick Reference: Common MCP Workflows

### Workflow 1: Create conversation and send a message

```
1. get_auth_user                      → get user info & personal_project_id
2. post_elitea_core_conversations      → create conversation, get conversation_id and uuid
3. post_elitea_core_participants       → add agent participant to conversation
4. patch_elitea_core_entity_settings    → configure LLM settings
5. post_elitea_core_messages           → send user_input using conversation_uuid
```

### Workflow 2: List agents and get details

```
1. get_projects_project               → list available projects
2. get_elitea_core_applications        → list agents in a project
3. get_elitea_core_application         → get full details for a specific agent
```

### Workflow 3: Create agent with toolkit

```
1. post_elitea_core_applications       → create agent with initial version
2. get_elitea_core_tools               → list available toolkits
3. patch_elitea_core_tool              → link toolkit to agent version
```

### Workflow 4: Upload file and reference in message

```
1. POST /attachments/...        → upload file, get filepath
2. post_elitea_core_messages           → send message with attachments_info containing the filepath
```

### Workflow 5: Direct agent execution (without conversation)

```
1. get_elitea_core_application         → get agent details with version_id
2. POST /predict/...            → execute agent directly with version_id
```

### Workflow 6: Manage agent versions

```
1. get_elitea_core_application         → get current agent with version details
2. post_elitea_core_versions           → create a new version
3. put_elitea_core_version             → update version configuration
4. patch_elitea_core_tool              → link/unlink toolkits to version
```

### Workflow 7: Browse conversation history

```
1. get_elitea_core_conversations       → find conversation by name/query
2. get_elitea_core_conversation        → get conversation details with participants
3. GET /messages/...            → paginate through messages
```

## Key Gotchas

| Gotcha | Details |
|--------|---------|
| `post_elitea_core_messages` uses UUID | The `conversation_uuid` parameter is a UUID string, **not** the integer `conversation_id`. Get it from the conversation's `uuid` field. |
| `POST /predict/...` (REST — no MCP predict) uses `version_id` | Execute against a specific version, not the application ID. Get it from `version_details.id`. |
| `mode` defaults to `prompt_lib` | Almost all tools default to `"prompt_lib"` mode. You rarely need to change this. |
| Pipeline instructions must be YAML | When `agent_type` is `"pipeline"`, the `instructions` field must contain valid YAML. |
| Version name cannot be `"base"` | When creating versions with `post_elitea_core_versions`, the name `"base"` is reserved. |
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

**Configuration:** the trigger is set on the pipeline VERSION via the platform UI (Pipeline Studio → entry-point node settings) or via REST (`PUT /api/v2/elitea_core/pipeline_trigger/prompt_lib/{project_id}/pipeline/{version_id}/trigger` — note the `pipeline_trigger/prompt_lib` prefix; the shorter form 404s).

**The trigger is NOT in the YAML.** It's server-side state; the YAML holds only the `entry_point` node id. So a trigger does **not** survive an export/import, and a version PUT wipes it.

### Schedule trigger specifics

- Two modes: **Default** (visual cron builder) and **Advanced** (raw cron).
- Format: `minute – hour – day(month) – month – day(week)`. Default expression: `0 0 * * 6` (Saturday midnight).
- **The timezone is auto-detected from the browser** that configured the schedule. If you care when it fires, set it explicitly rather than inheriting whichever laptop armed it.
- **Hourly minimum.** Sub-hourly crons are accepted with a 200 and never fire. *(This one is observed live, not documented for pipeline triggers — though the scheduled-indexing docs state the same floor: "Schedules cannot execute more frequently than once per hour." Don't let anyone "correct" it away.)*

### Webhook trigger specifics

Three subtypes, each with its own auth scheme:

| Type | Auth header | Method |
|---|---|---|
| **GitHub** | `X-Hub-Signature-256` | HMAC-SHA256 — `sha256=<computed_hmac>` |
| **GitLab** | `X-Gitlab-Token` | secret token sent directly |
| **Custom** | `X-Webhook-Token` | secret token sent directly |

```bash
curl -X POST "https://next.elitea.ai/webhook/custom" \
  -H "Content-Type: text/plain" \
  -H "X-Webhook-Token: <your_secret>" \
  -d 'Your message or data here'
```

Note `Content-Type: text/plain` and a **raw body** — not JSON. The secret is a 32-byte base64url token, auto-generated and regenerable (click **Apply** to save a regenerated one). **Copy it immediately — once the modal closes it cannot be retrieved, only regenerated.**

The full external-caller view (arming the trigger over REST, reading the URL and secret back, firing it) is in `elitea-testing/SKILL.md` § "Webhook triggering".

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

**The documented mechanism is a silent auto-reset**, and it's nastier than a rejection:

> *"If an interactive element (HITL, Printer) is added while Schedule or Webhook is active, the trigger automatically resets to Chat Message."*

So a pipeline you believe is on a cron **quietly stops being on a cron** the moment anyone adds a Printer node. Nothing errors. Nobody is told. The Schedule/Webhook options simply aren't offered for interactive pipelines, and an existing trigger is reverted.

This is very likely the true explanation for the symptom recorded in the table above (*"`last_run` advances, no conv, hourly cron"*) — the trigger had been reset out from under us.

There is also a runtime-side failure we observed pre-2.0.3 hardening: the trigger fires, the pipeline starts, and execution stops dead at the interactive node with no error surfaced to anyone (because there's no user to surface it *to*).

**Prevention — grep the YAML before arming a non-chat trigger:**

```bash
grep -nE 'type:[[:space:]]*(printer|hitl)|interrupt_(before|after)' pipeline.yaml
```

If that matches anything, the pipeline must stay on `chat_message`. (Note the correct targets: `type: hitl` — HITL is a first-class node type now, not a flag on `custom` — and the two interrupt keys `interrupt_before` / `interrupt_after`, not `interrupt: true`.)

**And re-check the trigger after every edit**, not just after a version PUT: `GET /api/v2/elitea_core/pipeline_trigger/prompt_lib/{project_id}/pipeline/{version_id}/trigger`. "I set it last week" is not evidence it's still set.
