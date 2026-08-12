# Toolkit Types — Reference

The ELITEA platform supports a fixed set of toolkit types, each with its own `settings` schema. To get the live registry (JSON-schemas), call:

```
GET /api/v2/elitea_core/toolkits/prompt_lib/{project_id}
```

The response's `<type>.properties.selected_tools.args_schemas` keys enumerate the available operations per type.

## Common toolkit types

### `openapi` — Wrap any REST API by OpenAPI spec

Best for: third-party APIs with a spec or that you can describe with one.

```json
{
  "type": "openapi",
  "name": "My Toolkit",
  "settings": {
    "spec": "<inline-YAML-or-JSON-OpenAPI-spec>",
    "base_url": "",
    "selected_tools": [],
    "openapi_configuration": { "elitea_title": "my-api-creds", "private": false }
  }
}
```

> **Live settings shape (verified):** the spec field is **`spec`** (not `schema`) and the credential
> ref is **`openapi_configuration`** (not `credentials_configuration`). Older docs say otherwise —
> trust this shape.

> ⚠️ **Auth caveat — a stored credential is used for EVERY caller.** An `openapi` toolkit
> authenticates with the ONE credential in `openapi_configuration` (its owner's token), regardless of
> who uses the agent. That's fine for a single-owner toolkit or a service-account API. It is **wrong
> for a shared / multi-user agent that should act as the calling user** — there, wrap the API in a
> **pipeline `code` node** using `elitea_client.auth_token` (the runtime caller's token) and expose it
> as an `application`-type tool. See the `application` type below and `examples/openapi/README.md`.

Details and an example walk-through in `openapi-toolkits.md`. Reference specs: `examples/elitea-api.yaml`
and `examples/openapi/elitea-builder-runtime-api.yaml`.

### `mcp_<flavor>` — Live MCP server

Best for: stdio/SSE MCP servers (`mcp_filesystem`, `mcp_slack`, `mcp_brave`, custom `mcp_*`).

> ⚠️ **Discovering existing MCPs is a multi-type scan.** MCP toolkit instances live under *three*
> `type` conventions: plain `mcp` (remote/HTTP), `mcp_stdio` (npx/stdio), and `mcp_<flavor>`
> (e.g. `mcp_Epam Staffing`). The `GET /tools/...?mcp=true` filter returns **only `type=mcp`** — it
> MISSES `mcp_stdio` and `mcp_<flavor>`. To enumerate ALL configured MCPs in a project, list every
> toolkit (high `limit`) and treat any whose `type` starts with `mcp` as an MCP, in addition to the
> `?mcp=true` results. (Discovered the hard way: a project survey using `?mcp=true` alone silently
> dropped the stdio and flavored MCP servers.)

```json
{
  "type": "mcp_filesystem",
  "name": "Local FS MCP",
  "settings": {
    "url": "https://mcp.example.com/sse",
    "ssl_verify": true,
    "selected_tools": []
  }
}
```

After create, sync tools:

```
POST /api/v2/elitea_core/mcp_sync_tools/prompt_lib/{project_id}
body: {"url": "https://mcp.example.com/sse", "toolkit_type": "mcp_filesystem"}
```

**Remote MCP configuration fields** (2.0.1 added the OAuth ones):

| Field | Notes |
|---|---|
| `URL` | **required** — the HTTP/HTTPS endpoint |
| `Headers` | optional JSON object of auth headers — e.g. `{"Authorization": "Bearer <token>"}` or `{"X-API-Key": "...", "X-Custom-Header": "..."}` |
| `Client ID` | OAuth application client identifier |
| `Client Secret` | OAuth application secret |
| `Scopes` | OAuth permission scopes (space-separated string or array) |
| `Timeout` | request timeout in seconds — default `60`, range 1–3600 |
| `Enable Caching` | bool |
| `Cache TTL` | default `300`, range 60–3600 |

Transports: **remote** = SSE or Streamable HTTP; **local** = STDIO (the Elitea MCP Client). Connection states in the UI: **Connected** (grey) / **Disconnected** (orange — *"MCP exists but cannot reach server; tools unavailable"*).

For OAuth, prefer the Client ID / Secret / Scopes config fields above — that's the documented path. There is also an **API-level** two-step flow that does not appear in the public docs, kept here because we've used it:

1. `POST /api/v2/elitea_core/mcp_dcr_proxy/default/{project_id}` — RFC 7591 dynamic client registration
2. `POST /api/v2/elitea_core/mcp_oauth_proxy/default/{project_id}` — token exchange

### ~~`datasource`~~ — RETIRED. Do not author.

> 🚫 **`datasource` is NOT a toolkit type any more.** Verified live (2026-07-13): `GET /api/v2/elitea_core/toolkits/prompt_lib/{pid}` — the authoritative type registry — returns **64 type schemas, and `datasource` is not among them**. It was migrated away in v1.7.0 (`migration/v1.7.0/migrate-datasources-to-indexing`).
>
> **The replacement is per-toolkit indexing.** Indexing is now a capability *inside* a regular toolkit: `jira`, `confluence`, `github`, `artifact` and friends each carry `embedding_model` + `pgvector_configuration` in their settings, and expose the six standard index tools (see "Indexing" above). You don't create a datasource; you enable indexing on the toolkit that owns the data.
>
> The shape below is kept **only** for reading pre-1.7.0 toolkits that still exist. Creating one today will fail.
>
> (Note: `datasource` still appears as a conversation **participant** `entity_name` — that's a different concept and may still be live. Don't conflate the two.)

```json
{
  "type": "datasource",
  "name": "Company KB",
  "settings": {
    "datasource_id": 12345,
    "embedding_model": {
      "name": "text-embedding-ada-002",
      "ai_credentials": {"elitea_title": "azure-openai", "private": true}
    },
    "vectorstore_model": {
      "model_name": "pinecone",
      "model_project_id": 1
    },
    "search_config": {
      "top_k": 5,
      "similarity_threshold": 0.7,
      "search_type": "similarity"
    }
  }
}
```

### Indexing — the real parameter set

The 2.0.3 release notes advertise "Scoped Index Creation" (targeting folder subsets rather than whole buckets). **There is no folder/path/scope parameter in the docs.** An earlier version of this file told you to "pass the folder path in the indexer's input" — that was a guess, and it's wrong. Scoping is done with **filters**, not a folder field.

Index-creation parameters (same across toolkit types):

| Parameter | Notes |
|---|---|
| **Index Name (Collection Suffix)** | max **7 characters**, unique within the toolkit |
| **Clean Index** | remove existing data before indexing |
| **Progress Step** | progress-reporting interval, 0–100 (default `10`) |
| **Chunking Config** | default `{}` |
| **Skip Unsupported Extensions** | default enabled |

How you actually scope to a subset:

- **Artifact toolkit** — `Include Extensions` / `Skip Extensions`. There is **no** folder, prefix, or path parameter; the index covers the whole bucket, filtered by extension only.
- **GitHub-family** — `Branch` plus `Whitelist` / `Blacklist` path globs, e.g. `["docs/*", "src/*.py"]`. This is how you get directory-level scoping.

**Six standard indexing tools**, identical across 13+ toolkit types: `Index Data` · `Search Index` · `Stepback Search Index` · `Stepback Summary Index` · `Remove Index` · `List Collections`.

**Search parameters:** `Query` (required) · `Collection Suffix` · `Cut-off Score` (default `0.2`) · `Search Top` (default `10`) · `Filter` (metadata refinement).

**Prerequisites:** the `Index Data` tool must be enabled for the Indexes tab to even appear, and indexing needs a **PgVector Configuration** + an **Embedding Model** (defaults: `text-embedding-ada-002`, `text-embedding-3-small`, `text-embedding-3-large`). The PgVector credential takes a Display Name and a Connection String.

**Scheduled indexing** — independently confirms the hourly floor we hit on pipeline triggers: 5-field cron (`minute hour day(month) month day(week)`); *"Schedules cannot execute more frequently than once per hour"*; `*/30 * * * *` explicitly not recommended; default `0 0 * * 6` (Saturday midnight); requires a valid, non-expired PAT.

### `application` — Agent-as-tool (canonical pattern in ELITEA 2.0.3+)

Best for: composing agents (one agent calling another). As of 2.0.3 sub-agents are first-class **standard tools** — call them exactly like an OpenAPI tool, with an explicit task description rather than implicit chat-history inheritance.

```json
{
  "type": "application",
  "name": "Sub-agent: KB Lookup",
  "settings": {
    "variables": [],
    "application_id": 17,
    "application_version_id": 88
  }
}
```

> **Registry gotcha:** the `application` type is **filtered out of the default**
> `GET /toolkits/prompt_lib/{project_id}` schema registry — you'll only see it via
> `GET /toolkit_types/prompt_lib/{project_id}?application=true` (returns `{"rows":["application"],...}`).
> It IS creatable with the shape above regardless. After create, `toolkit_name` is `null` and
> `GET /toolkit_available_tools/...` returns `{"tools":[]}` — that's expected (the "tool" is the agent
> itself, one implicit call). Link it like any toolkit (`PATCH /tool/...`, `selected_tools` omitted).
> Both agents AND pipelines can be wrapped this way (the wrapper's `agent_type` echoes the child's).

**Sub-agent delegation: the child does NOT inherit the parent's chat history (2.0.3+).**

This is the behaviour change that matters, and it is stated in the 2.0.3 release notes: *"Child agent execution now relies on explicit task payloads rather than implicit chat history inheritance."* Sub-agents became isolated, callable components.

What follows from that:

- **Hand the child everything it needs, explicitly.** Construct a self-contained task description per sub-agent call (*"Look up KB articles matching the following user query: …"*). Don't assume the child can see prior turns — it can't.
- **Multi-agent systems authored before 2.0.3 can degrade silently.** If a parent relied on the child seeing earlier conversation, the child now sees nothing and produces a weaker answer with no error. Audit each sub-agent call and inline the context it used to get for free.
- **Inside a pipeline the equivalent is the `agent` node** — see `elitea-pipeline/references/yaml-schema.md`. Same isolation semantics.
- **To deliberately share full history across children, use the `Swarm Mode` internal tool.** The docs describe it as *"enables multi-agent collaboration by allowing all child agents to share the full conversation history and hand off control to each other"* — which is the documented switch for the old behaviour.
- **Parallel fan-out (2.0.4):** a parent can now issue **multiple sub-agent calls from a single response**, executing concurrently — including multi-interrupt HITL when several children each need approval. Any external caller polling such a run must expect *several* simultaneous approval pauses (see `elitea-testing/references/test-patterns.md` § 3b).

> ⚠️ **UNVERIFIED: the payload shape.** An earlier version of this file asserted a literal `task` field in the sub-agent call payload. **No ELITEA doc page shows such a field** — the release-note prose says "task payloads", but the documented UI mechanism is simply adding a nested agent (`+Agent`) plus the Swarm Mode toggle for history. The *behaviour* above is real; the *field name* is not confirmed. Re-derive it from a live `GET /toolkits/prompt_lib/{pid}` before putting a `task` key in a payload.

Migration check for legacy pipelines: search your YAML for `type: agent` nodes that pass only a short prompt; if the original design assumed the child had multi-turn context, inline that context into the prompt explicitly.

> **A third route to agent-as-tool: the `Elitea MCP Tools` internal tool (2.0.4).** Enable it on an agent (TOOLS → INTERNAL TOOLS) and the agent can discover and call other ELITEA agents and toolkit tools through ELITEA's own MCP server — no separate external MCP connection. Naming: an agent's display name is normalized (`"PR Review Agent"` → `PR_Review_Agent`); a toolkit tool becomes `{toolkit_name}_{tool_name}` (`My_GitHub_Toolkit_create_issue`); any character outside `[A-Za-z0-9_-]` becomes `_`.
>
> **The gotcha:** an agent only appears as a callable tool if it carries the **`mcp` tag**, and a toolkit only if it has **"Available via MCP"** enabled in its MCP Options. Without those, the tool list is silently empty.

### ~~`custom_python`~~ — NOT IN THE REGISTRY. Do not author.

> 🚫 **`custom_python` is not a real toolkit type.** Verified live (2026-07-13): it does not appear in the 64-type registry returned by `GET /api/v2/elitea_core/toolkits/prompt_lib/{pid}`. Neither does a plain `custom`.
>
> **What to use instead, depending on what you actually want:**
> - **Run Python as part of a workflow** → a pipeline `code` node (`elitea-pipeline/references/yaml-schema.md`). This is almost always the answer.
> - **Give an agent an ad-hoc Python capability** → the `pyodide` internal tool (`meta.internal_tools: ["pyodide"]`), see the `sandbox` section below.
>
> The shape below is unverified and kept only as a historical note. Don't build on it.

```json
{
  "type": "custom_python",
  "name": "Text utils",
  "settings": {
    "python_version": "3.11",
    "dependencies": ["regex>=2023.0.0"],
    "tools": [
      {
        "name": "normalize_phone",
        "description": "Strip phone to E.164",
        "code": "def normalize_phone(phone: str) -> str:\n    return phone.replace(' ', '').replace('-', '')",
        "input_schema": {"type": "object", "properties": {"phone": {"type": "string"}}}
      }
    ],
    "execution_timeout": 300,
    "memory_limit_mb": 512
  }
}
```

### `sandbox` — runtime Python (`pyodide_sandbox`) — enable via `meta.internal_tools`, NOT a toolkit link

A `sandbox` toolkit (`settings:{stateful, allow_net, selected_tools:["pyodide_sandbox"]}`) runs arbitrary
Python the *agent writes on the fly* — great for pre-flight validation, safe version merges, deterministic
compute, and (because `elitea_client` is injected) acting as a user-authenticated REST client.

⚠️ **But linking a `sandbox`-type toolkit to an `openai` agent does NOT make `pyodide_sandbox` callable
at runtime** (live-verified 2026-06-03). The toolkit shows in `tools[]`, yet the agent can't call it (it
hallucinates a fake result). **The actual switch is `meta.internal_tools: ["pyodide"]` on the agent
VERSION** — set that (with a sensible `step_limit`) and you do NOT need a sandbox toolkit at all. The
built-in pyodide has `elitea_client.{auth_token,base_url}` + `httpx` network (to `next.elitea.ai` and
`raw.githubusercontent.com`), the stdlib + `httpx`/`requests`/`chardet`, but **no `pyyaml`/`micropip`**.
Output: `{result:<last expr>, output:<stdout>, execution_info:…}`. Because there's no YAML parser, author
pipelines as a dict and deploy via `json.dumps(spec)` (a JSON string is valid pipeline `instructions`).
See `elitea-platform/references/conventions.md` §9.

**`pyodide` is one of an `internal_tools` PALETTE** — built-in agent capabilities, NOT toolkits, all enabled via the version's `meta.internal_tools` array.

The real tokens, **harvested from 600 UI-authored agents** (project 1, 2026-07-13) — the docs only ever show the display names:

| UI label | **API token** | What it does |
|---|---|---|
| Attachments | `attachments` | Attach files/images to conversations. On a *pipeline*, pair it with an `input_attachments` state var. |
| Python sandbox | **`pyodide`** | Secure Python execution via Pyodide. |
| Data Analysis | `data_analysis` | pandas + natural-language queries over CSV/Excel (replaced the old Pandas toolkit). |
| Planner | `planner` | Structured planning and task breakdown. |
| Image creation | `image_generation` | Text-to-image (2.0.1). Output lands in the `attachments` bucket. |
| Swarm Mode | `swarm` | Multi-agent collaboration — *"allows all child agents to share the full conversation history and hand off control to each other."* The switch that restores pre-2.0.3 sub-agent history inheritance. |
| Smart Tools Selection | **`lazy_tools_mode`** | Binds meta-tools instead of every tool (~85% token cut at ≥5 toolkits). |
| ELITEA MCP Tools (2.0.4) | *not observed* | Discover/call ELITEA's own agents and toolkit tools via its MCP server. Requires the target agent to carry the `mcp` tag. Token not yet seen in the wild — **don't guess it.** |

Two of these are **unguessable and worth memorizing**:
- The sandbox token is **`pyodide`**, not `sandbox`. (`sandbox` is the *toolkit type*; `pyodide` is its `toolkit_name`.)
- Smart Tools Selection is **`lazy_tools_mode`**. Nothing in the UI hints at that name.

> 🚨 **`meta` IS NOT VALIDATED — a typo fails silently and forever.** Verified live: `PUT` accepted `meta.internal_tools: ["banana"]`, `"not-a-list"`, and `[123]`, storing each verbatim with a success response. Bad tokens are **persisted and then silently ignored at runtime**. There is no discovery endpoint (`/internal_tools`, `/available_tools` → 404), and **asking the agent to self-report its tools is useless** — it returns an identical list whether `internal_tools` is empty or full of nonsense.
>
> So: there is no feedback loop. If you fat-finger a token, the capability just never turns on and nothing anywhere tells you. Copy the tokens from the table above exactly, and confirm by `GET`ting the version back.

**Context Management** (auto prune + summarize) is ON by default and is **not** a per-agent token.

These map to agent-maturity practices (planning, contextual tool filtering, multi-agent collaboration) — pick deliberately when designing an agent.

### `github`, `jira`, `confluence`, `gitlab`, `azure_devops` — First-class integration types

Pre-canned toolkits with built-in operation catalogs. Pass `type: "github"` and only fill credentials + repo/project scope:

```json
{
  "type": "github",
  "name": "GH Toolkit",
  "settings": {
    "github_configuration": {"elitea_title": "my-gh-creds", "private": true},
    "repository": "octocat/Hello-World",
    "active_branch": "main",
    "base_branch": "main",
    "pgvector_configuration": {"elitea_title": "shared-pgvector", "private": false},
    "embedding_model": "text-embedding-ada-002",
    "selected_tools": ["get_files_from_directory", "list_branches_in_repo"]
  }
}
```

Inspect the available operations per type via `GET /toolkit_available_tools/prompt_lib/{project_id}/{toolkit_id}` after create.

#### Which fields live on the CREDENTIAL vs the TOOLKIT

Recent releases moved fields between the two, and getting this wrong produces confusing "missing configuration" errors. The split as documented:

| Integration | On the **credential** | On the **toolkit** |
|---|---|---|
| **Azure DevOps** (Boards/Repos/Wiki/Plans) | `Organization Url` (e.g. `https://dev.azure.com/MyCompany`), `Token` (PAT or a secret ref) | **`Project`** ← moved here in 2.0.3, `Ado Configuration` (selects the credential), PgVector, Embedding Model, `Limit` |
| **Jira / Confluence** | **`Hosting`** (`Auto` \| `Cloud` \| `Server`) ← moved here in 2.0.2, `Base URL` (no `/jira` suffix), `Username`+`API Key` (Basic) or `Token` (Bearer) | **`API Version`** (`Auto` → Cloud=V3, Server=V2), `Limit`, `Labels`, `Verify SSL`, `Additional Fields`, `Custom Headers`; Confluence also takes `Space` (required) |
| **GitHub** | `Base URL`, `Authentication Method` (Anonymous \| Token \| Password \| App Private Key), plus `Token` / `Username`+`Password` / `App ID`+`Private Key` | `Repository` (`owner/repo`), **`Main Branch`**, `Active Branch`, PgVector, Embedding Model |

> **The 2.0.2 release note is half wrong, and it's an easy trap.** It reads as though *both* Hosting and API Version moved to the credential. Only **Hosting** did. The Confluence doc says it outright: *"Hosting lives at the credential level, while API Version resides at the toolkit level."* The point of the split is credential reuse — one ADO credential across many projects, one Jira credential across hosting-compatible toolkits.

> **`base_branch` vs `Main Branch`:** the JSON example above uses `base_branch`, while the docs name the field `Main Branch`. Verify against the live registry (`GET /toolkits/prompt_lib/{pid}`) before trusting either.

#### Per-user credentials on shared toolkits

A shared toolkit can require each user to supply their *own* credential, rather than running on the owner's. Resolution works by **Credential ID** — a lowercase identifier auto-derived from the credential name (spaces → underscores, lowercased: `GitHub Integration Token` → `github_integration_token`). At execution, ELITEA looks in the *calling user's* Private workspace for a credential whose ID matches the one configured on the toolkit. **Only the IDs need to match, and the match is case-sensitive.**

Users without one see: *"This toolkit requires your own private [type] credentials. Create a credential with the matching ID '[credential ID]' in your Private workspace to use this toolkit."*

> ✅ **Resolved (live, 2026-07-13): `elitea_title` IS the "Credential ID".** Same field, two names. The core rule stands — toolkits reference credentials by `{"elitea_title", "private"}`. A credential carries `elitea_title` (the slug ID, e.g. `bot_elitea_kb`) *and* `label` (the display name, e.g. `Bot Elitea KB`); the reference uses the slug.
>
> 🚨 **But note the silent-failure mode:** the server **lowercases `elitea_title` on write** without telling you. If you create a credential as `MyGitHubCreds` it is stored as `mygithubcreds`, and a toolkit referencing `MyGitHubCreds` will not resolve it. Write it lowercase yourself. See `elitea-platform/references/conventions.md` § 6.

### `artifact` — Project artifact storage (for chat attachments)

Best for: persistent chat attachments / agent memory storage.

```json
{
  "type": "artifact",
  "name": "Email attachments",
  "settings": {
    "bucket": "emailattachments",
    "pgvector_configuration": {"elitea_title": "shared-pgvector", "private": false},
    "embedding_model": "text-embedding-ada-002",
    "selected_tools": []
  }
}
```

Set as the conversation's attachment toolkit via `PUT /chat/attachment_storage/...` or as the agent's via `PUT /application_attachment_storage/...`.

## Picking the right type

| You have… | Use type |
|---|---|
| An OpenAPI spec or a REST API to wrap | `openapi` |
| A running MCP server (URL) | `mcp_<flavor>` |
| Indexed docs / vector search | **enable indexing on the toolkit that owns the data** (`jira`, `confluence`, `github`, `artifact` …) — *not* `datasource`, which is retired |
| Another agent in this project | `application` (or an `agent` node in a pipeline) |
| Short Python utility | a pipeline **`code` node**, or the **`pyodide`** internal tool — *not* `custom_python`, which isn't in the registry |
| GitHub / Jira / Confluence access | first-class type (`github`, `jira`, ...) |
| Project bucket for files | `artifact` |

**The authoritative type list is live, not in this file.** `GET /api/v2/elitea_core/toolkits/prompt_lib/{project_id}` returns the JSON-schema registry for every valid type — **64 of them** as of 2026-07-13. When in doubt, read the registry; don't trust a hardcoded list (including this one).

The documented catalog, by category: **Code Repositories** (ADO Repos, Bitbucket, GitHub, GitLab, GitLab Org) · **Communication** (Slack) · **Development** (Sonar, SQL) · **Documentation** (ADO Wiki, Confluence) · **Integrations** (OpenAPI) · **Office** (PPTX, SharePoint) · **Other** (Artifact, Figma, Google Places, Memory, Postman, Salesforce, ServiceNow) · **Project Management** (ADO Boards, Jira, Rally) · **Test Management** (ADO Plans, QTest, TestRail, XRAY Cloud, Zephyr Enterprise/Essential/Scale/Squad) · **Testing** (Carrier, Report Portal, TestIO).

## Linking a toolkit to an agent

After creation, attach a toolkit to an agent VERSION via PATCH:

```
PATCH /api/v2/elitea_core/tool/prompt_lib/{project_id}/{toolkit_id}
body: {
  "entity_id": <agent_id>,
  "entity_version_id": <version_id>,
  "entity_type": "agent",
  "has_relation": true,
  "selected_tools": ["operation_name_1", "operation_name_2"]
}
```

- `selected_tools` **filters** which operations are exposed to the agent. Pass `null`/omit to expose everything the toolkit defines.
- To unlink: same call with `has_relation: false`.

## Gotchas

- **Credential references use `elitea_title` and `private`, NOT raw ids.** The same value can appear in many toolkits.
- **Sensitive fields come back as `"{{secret.NAME}}"`** placeholders on subsequent GETs. Resolve via the secrets endpoint (see `elitea-platform/references/conventions.md` § 5).
- **`toolkit_name`** in responses is the sanitized form of `name` (server strips chars outside `[a-zA-Z0-9_.-]`, then replaces `.` → `_`).
- **MCP toolkits' `online` field is `null` until sync succeeds.** Run `mcp_sync_tools` immediately after create.
- **Test before linking** via `POST /test_toolkit_tool/...` — see `elitea-testing/SKILL.md`.
