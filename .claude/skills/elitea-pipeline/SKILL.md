---
name: elitea-pipeline
description: Author, debug, and deploy ELITEA pipelines (YAML-defined multi-step agent workflows). Knows all 11 modern node types (llm, agent, toolkit, mcp, code, custom, router, decision, hitl, state_modifier, printer), state management, entry-point triggers (chat/scheduled/webhook), code-node debug mode, and the platform-specific runtime helpers (`elitea_client.auth_token`, `elitea_client.base_url`, `elitea_state.get(...)`). Use this skill whenever the user wants to create, modify, debug, or understand an ELITEA pipeline; whenever they show pipeline YAML; whenever they mention node types, state vars, routers, decisions, transitions, entry points, or pipeline triggers. Examples live under `examples/`; the worked nudge case-study lives in `elitea-testing/references/nudge-case-study.md`.
---

# ELITEA Pipeline — Authoring & Debugging

A pipeline is an `agent_type: pipeline` ELITEA agent whose `instructions` field is YAML describing a node graph. This skill covers the YAML schema, the modern node types, common shapes, and the runtime helpers you have inside `code` nodes.

> **Growing this skill:** if a session uncovers a new node-type quirk, state pattern, or pipeline gotcha, append it to `references/{yaml-schema,patterns,workflows}.md` or add a clean working pipeline to `examples/`. See `elitea-platform/references/growing-this-toolkit.md` for the full routing decision tree and "what NOT to promote" guidance.

## Quick lookup

| If you need... | Load |
|---|---|
| YAML top-level structure (entry_point/state/nodes), data types, naming rules | `references/yaml-schema.md` § 1 |
| Detailed schema for every modern node type | `references/yaml-schema.md` § 2 |
| Connection rules (`transition` / `routes` / `nodes` / `END`) | `references/yaml-schema.md` § 3 |
| Legacy node types (only for reading old pipelines — don't write these) | `references/yaml-schema.md` § Legacy |
| When to pick which pipeline shape (linear / loop / branching / converging) | `references/patterns.md` |
| Validation checklist & common debugging steps | `references/workflows.md` |
| How `alita_client` / `elitea_client` helpers work in code nodes | `references/workflows.md` § "Code Node Special Capabilities" |
| Real, working pipeline YAML files to learn from | `examples/*.yaml` (see catalog below) |
| **Entry-point triggers** (chat / scheduled / webhook) + their interactive-node constraint | `references/workflows.md` § "Pipeline entry-point triggers" |

## Example catalog (`examples/`)

| File | What it shows |
|---|---|
| `ConversationHealthAnalyzer.yaml` | **The flagship example.** Full pipeline that fetches conversations, classifies status (errored/completed/active/pending), nudges failed ones, with idempotency guards and `apply`/dry-run modes. Demonstrates: async httpx calls, `elitea_client.auth_token`, `elitea_state.get`, structured output, parallelism via `asyncio.gather`, deterministic classification (no LLM call needed). Walked through end-to-end in `elitea-testing/references/nudge-case-study.md`. |
| `FetchUIContext.yaml` | Router-based dispatch: parses entity_type and routes to one of four `code` nodes that fetch different entity details via the REST API. Best example of `router` + `code` + auth via `elitea_client.auth_token`. Also demonstrates the **secret redaction** pattern (mask any field whose key matches a sensitive-name list). |
| `GetAvailableToolkits.yaml` | Minimal: single `toolkit` node returning the toolkit list. Read first if you're new to pipeline YAML. |
| `GetToolDescription.yaml` | Single toolkit-call pattern with `input_mapping`. |
| `GetAvailableProjectTools.yaml` | Aggregator: combines toolkit metadata with per-toolkit available tools. Good `code`-node example. |
| `getuserdetails.yaml` | Tiny `mcp` node example. |
| `wait2mins.yaml` | Trivial `code` node that just sleeps — useful for testing interrupts/timeouts. |
| `AutoModelRouter.yaml` | **Auto model router.** Classifies each task's complexity with a cheap classifier `llm` node → `router` → three `agent` branches, each delegating to an agent pinned to a different model tier (Haiku / GPT-5.4-mini / Sonnet 4.6), then a `code` node builds a "routed to X because Y" banner. The canonical way to do **per-branch model selection** (pipeline `llm` nodes have no per-node model — distribute via model-per-agent). Demonstrates the `chat_history`-for-editor-round-trip rule. See `patterns.md` § "Model routing". |
| `AgentStudioGrader.yaml` | **Lazy-fetch grading loop.** Grades the public Agent Studio's published agents one-by-one on a weighted rubric. Demonstrates: a `router`+counter loop, a `code` node that lazily fetches ONE item's heavy payload per iteration (keeps state under the deno ARG_MAX limit), an `llm` node with `structured_output` (JSON keys → state vars) feeding a Python accumulator, weighted scoring + ranking in code, and a final `code` node that writes the report to `messages` byte-exact (no LLM echo). Pairs with `workflows.md` §§ "Pipeline LLM-node gotchas" + "Pipeline state size limit". |

## Core rules (always in effect)

- **Modern node types only** in new pipelines — there are **11**: `llm`, `agent`, `toolkit`, `mcp`, `code`, `custom`, `router`, `decision`, `hitl`, `state_modifier`, `printer`. Legacy types (`tool`, `function`, `condition`, `loop`, `loop_from_tool`, `pipeline`/subgraph) appear in `yaml-schema.md` for reading existing pipelines only. The official replacement for the loop nodes is **`router` + a state counter**.
- **`hitl` is a first-class node type** (2.0.1+), not a flag on `custom`. It belongs to the Control Flow family alongside `router` and `decision`.
- **Debugging a `code` node: set `debug: true` on it.** ELITEA writes the fully assembled Python — sandbox client preamble, the *actual injected state*, and your code wrapped in an async runner — to the **`code-debug`** bucket under mode **`default`** (`GET /api/v2/artifacts/artifacts/default/{pid}/code-debug`), as `{node_id}__{YYYYMMDD}_{HHMMSS}.py`. Download it, replace the auth-token placeholder, `pip install requests chardet`, and reproduce the exact run locally. Best-effort: if the upload fails the run still proceeds and logs a warning. Bucket auto-expires (~30d).
- **Pipeline file input:** declare `input_attachments: {type: list}` in `state`. It arrives as a `list[str]` of artifact paths (`attachments/{conversation_uuid}/{filename}`). **The state declaration is what populates it** — the "Allow attachments" toggle is only a UI affordance. Without the declaration the file is invisible to state and only appended to `input` as prose.
- **If you define a custom `state` block, it MUST include `messages: list`.** Otherwise omit `state` entirely to use defaults (`input: str`, `messages: list`).
- **Every execution path must reach `END`.** Router and Decision nodes must declare `default_output`.
- **Any node type can be `entry_point`, including `router` and `decision`** — verified executing live (2026-07-13). Several doc pages claim otherwise; they're wrong. Decision nodes cannot chain directly to another Decision.
- **Produce complete, valid YAML** when generating — never partial snippets. Validate with `python3 -c "import yaml; yaml.safe_load(open('file.yaml'))"`.
- **Never hardcode secrets.** Use `alita_client.unsecret('NAME')` if reading project-stored secrets; use `elitea_client.auth_token` for self-API calls.
- **Inside code nodes use `elitea_state.get('var', default)` and `elitea_client.{auth_token,base_url}`** — these are the runtime-injected helpers. `alita_client` is an alias for some operations (artifacts, apps). When in doubt, prefer `elitea_*`.
- **HTTP from inside code nodes:** use `httpx.AsyncClient(timeout=60, follow_redirects=True)`; do NOT add `Content-Type: application/json` on GET requests (some proxies reject this; use `Accept: application/json` for GETs).

## Workflow when authoring a new pipeline

1. Clarify inputs / outputs / external integrations needed
2. If broad design: load `references/patterns.md` to pick the shape
3. Load `references/yaml-schema.md` for the node-type definitions you'll use
4. Sketch the node IDs and transitions on paper; draft the state block
5. Generate complete YAML
6. Validate against the checklist in `references/workflows.md`
7. Deploy via `POST /api/v2/elitea_core/applications/prompt_lib/{project_id}` with `agent_type: "pipeline"` and the YAML as `instructions` (see `elitea-platform/references/api-reference.md` § 2.1 for the full payload)
8. Test via `POST /api/v2/elitea_core/predict/prompt_lib/{project_id}/{version_id}` — see `elitea-testing` skill

## How to deploy / update an existing pipeline

After editing YAML locally:

```bash
# update version (assumes you know the application_id + version_id)
curl -X PUT -H "Authorization: Bearer $ELITEA_TOKEN" -H "Content-Type: application/json" \
  -d @- "https://next.elitea.ai/api/v2/elitea_core/version/prompt_lib/$PROJECT_ID/$APP_ID/$VER_ID" <<EOF
{
  "id": $VER_ID, "application_id": $APP_ID, "name": "base",
  "agent_type": "pipeline",
  "instructions": $(jq -Rs . < pipeline.yaml),
  ...other fields preserved from the GET response...
}
EOF
```

The full payload shape and "always-GET-first-then-merge" pattern is in `elitea-testing/scripts/update_agent.py`.

## Upstream documentation (self-learning)

The bundled `references/` files are a snapshot. Live docs are fetchable as plain markdown — append `.md` to any `docs.elitea.ai` path. Index: **https://docs.elitea.ai/llms.txt**.

- https://docs.elitea.ai/how-tos/pipelines/overview.md
- https://docs.elitea.ai/how-tos/pipelines/yaml.md
- https://docs.elitea.ai/how-tos/pipelines/states.md
- https://docs.elitea.ai/how-tos/pipelines/nodes-connectors.md
- **https://docs.elitea.ai/how-tos/pipelines/nodes/overview.md** ← the authoritative node registry + the deprecation list
- https://docs.elitea.ai/how-tos/pipelines/nodes/interaction-nodes.md
- https://docs.elitea.ai/how-tos/pipelines/nodes/execution-nodes.md
- https://docs.elitea.ai/how-tos/pipelines/nodes/control-flow-nodes.md
- https://docs.elitea.ai/how-tos/pipelines/nodes/utility-nodes.md
- https://docs.elitea.ai/how-tos/pipelines/nodes/iteration-nodes.md ← still documents the DEPRECATED loop nodes as if current; trust `nodes/overview.md` instead
- https://docs.elitea.ai/how-tos/pipelines/entry-point.md
- https://docs.elitea.ai/how-tos/pipelines/pipeline-runs.md
- https://docs.elitea.ai/how-tos/pipelines/flow-editor.md

**Where the docs are known to be wrong** (all verified live — don't "correct" these back):
- Loop examples use a top-level `return` in a code node. Code runs at module scope; `return` is a `SyntaxError`. The dict literal must be the last expression.
- Several pages claim `router` (and one claims `decision`) cannot be an `entry_point`. **Both work** — verified executing.
- The 2.0.4 release notes call the debug bucket `code_debug`. It's **`code-debug`**.

## Related skills

- **`elitea-platform`** — for any REST endpoint detail, MCP tool reference, ID rules
- **`elitea-toolkit`** — when your pipeline binds a toolkit (`toolkit` or `mcp` node), or needs a new toolkit created
- **`elitea-testing`** — for predict/run/debug; the nudge case study walks through a real build→deploy→test cycle
