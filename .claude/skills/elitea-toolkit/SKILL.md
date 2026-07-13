---
name: elitea-toolkit
description: Create, configure, and link ELITEA toolkits — OpenAPI/REST toolkits, MCP server toolkits, first-class integrations (GitHub/Jira/ADO/…), artifact toolkits, per-toolkit indexing, and application-as-tool (sub-agents). Knows the toolkit type registry, the OpenAPI spec format ELITEA accepts (with examples), how credentials and secrets link in via `{"elitea_title", "private"}` references, and the patch/associate flow for binding toolkits to agent versions with `selected_tools`. Use this skill whenever the user wants to wrap an external API as an ELITEA toolkit, expose an MCP server to agents, or wire a tool onto an agent/pipeline. Real ELITEA-on-OpenAPI specs live under `examples/`.
---

# ELITEA Toolkit — Create, Configure, Link

A toolkit is an ELITEA wrapper around an external capability (REST API, MCP server, indexed data, or another ELITEA agent). Once created, toolkits are linked to agent versions with optional `selected_tools` filtering.

> **Growing this skill:** when a session reveals a new toolkit-type pattern, OpenAPI extension, or credential-shape gotcha, append it to `references/{toolkit-types,openapi-toolkits}.md` or add a reusable spec to `examples/`. See `elitea-platform/references/growing-this-toolkit.md` for the full routing decision tree.

## Quick lookup

| If you need... | Load |
|---|---|
| What toolkit types exist + when to pick each | `references/toolkit-types.md` |
| OpenAPI spec format ELITEA accepts (info, paths, components, x-elitea-* extensions) | `references/openapi-toolkits.md` |
| Exact REST payload to `POST /tools/...` | `elitea-platform/references/api-reference.md` § 3.1 |
| How to link a toolkit to an agent version with selected_tools | `elitea-platform/references/api-reference.md` § 3.3 + § 9.9 |
| How credentials are referenced (`elitea_title`, `private`) | `elitea-platform/references/conventions.md` § 4 + § 6 |
| Real toolkit specs (GitHub, ELITEA-API itself, etc.) | `examples/` (catalog below) |

## Example catalog (`examples/`)

| File | What it shows |
|---|---|
| `elitea-api.yaml` | **OpenAPI spec for ELITEA's own REST API** wrapped as a toolkit — so ELITEA agents can call ELITEA endpoints. Demonstrates `x-elitea-base-url`, `x-elitea-operation-name`, OAuth-style header auth, parameter location (path/query/body) declarations. Use this as the template for any new OpenAPI toolkit. |
| `openapi/elitea-builder-runtime-api.yaml` | The **full ELITEA build + runtime API** as one OpenAPI toolkit — the biggest worked spec in the repo. |
| `githubissues.json` | **GitHub Issues toolkit** — REST operations for listing/creating/searching issues. Demonstrates `Accept: application/vnd.github.v3+json` headers, pagination params, `body` schema for `POST /issues`. |
| `githuboardmoovement.json` | GitHub Projects (v2 Board) movement operations. Demonstrates GraphQL endpoint wrapping (`POST /graphql` with the query in the body). |

## Core rules (always in effect)

- **`type` field determines the toolkit kind.** Live values include `openapi` (REST), `mcp`/`mcp_stdio`/`mcp_<flavor>` (MCP servers), `application` (agent-as-tool), `artifact`, `sandbox`, and the first-class integrations (`github`, `jira`, `confluence`, `gitlab`, `azure_devops`, `sharepoint`, `figma`, …). **`datasource` and `custom_python` are NOT valid types** — verified against the live registry (64 types, 2026-07-13); use per-toolkit indexing and pipeline `code` nodes instead. Always read the registry rather than trusting a hardcoded list: `GET /api/v2/elitea_core/toolkits/prompt_lib/{project_id}`.
- **Credentials reference by name, not id.** Inside `settings`, use `{"elitea_title": "<credential-title>", "private": <bool>}`. `private = not credential.shared`.
- **Sensitive fields come back as `"{{secret.<name>}}"`** on subsequent GETs — that's expected, resolve via the secrets endpoint when you need the raw value.
- **`selected_tools` is the linking filter.** When you `PATCH /tool/...` to link a toolkit to an agent version, pass `selected_tools: ["op_name_1", "op_name_2"]` to expose only specific operations; omit/null to expose all.
- **Toolkit name gets sanitized server-side.** The platform applies `re.sub(r'[^a-zA-Z0-9_.-]', '', name).replace('.', '_')`. Response `toolkit_name` is the sanitized form.
- **For MCP toolkits, sync after create:** `POST /api/v2/elitea_core/mcp_sync_tools/prompt_lib/{project_id}` with `{url, toolkit_type}` discovers and registers the MCP server's tools.

## Workflow — create an OpenAPI toolkit and link it

1. **Write the OpenAPI spec.** Start by copying `examples/elitea-api.yaml` or `examples/githubissues.json` as a template. Required: `info`, `paths`, optional `components.securitySchemes`. ELITEA-specific extensions:
   - `x-elitea-base-url` — overrides `servers[0].url`
   - `x-elitea-operation-name` (per operation) — the user-facing tool name
2. **Create credential** — **mandatory**, even for public APIs (use an Anonymous credential there):
   `POST /api/v2/configurations/configurations/{project_id}` with `type: "github"` (or appropriate), `data: { access_token: "..." }`. Returns **200**, not 201. The server stores `access_token` as a secret automatically.
3. **Create the toolkit:** `POST /api/v2/elitea_core/tools/prompt_lib/{project_id}` with `type: "openapi"`, `settings: { spec: <inline JSON/YAML/URL>, openapi_configuration: {elitea_title: "...", private: true} }`. The keys are `spec` and `openapi_configuration` — **not** `schema` / `credentials_configuration`.
4. **Verify tools were discovered:** `GET /api/v2/elitea_core/toolkit_available_tools/prompt_lib/{project_id}/{toolkit_id}`.
5. **Test a single operation** before linking: `POST /api/v2/elitea_core/test_toolkit_tool/prompt_lib/{project_id}` with `{toolkit_config, tool_name, tool_params}` — see `elitea-testing` skill.
6. **Link to an agent version:** `PATCH /api/v2/elitea_core/tool/prompt_lib/{project_id}/{toolkit_id}` with `{entity_id: <agent_id>, entity_version_id: <version_id>, entity_type: "agent", has_relation: true, selected_tools: [...]}`.

## Workflow — wrap an MCP server as a toolkit

1. **Discover the MCP server first (no toolkit yet):** `POST /api/v2/elitea_core/toolkit_discover_tools/prompt_lib/{project_id}/mcp_<flavor>` with `{settings: {url, ...}}`. Returns `{success, tools: [{name, description, inputSchema}]}`.
2. If the server requires OAuth, configure via `/mcp_dcr_proxy/...` (RFC 7591 DCR) then `/mcp_oauth_proxy/...` (token exchange).
3. **Create the toolkit:** `POST /tools/...` with `type: "mcp_<flavor>"`, `settings: {url, ...}`.
4. **Sync tools:** `POST /mcp_sync_tools/...` with the toolkit's URL.
5. Link to agents the same way as OpenAPI.

## Upstream documentation (self-learning)

Live docs are fetchable as plain markdown — append `.md` to any `docs.elitea.ai` path. Index: **https://docs.elitea.ai/llms.txt**.

- https://docs.elitea.ai/menus/toolkits.md
- https://docs.elitea.ai/menus/mcps.md
- https://docs.elitea.ai/menus/credentials.md
- https://docs.elitea.ai/integrations/toolkits/openapi_toolkit.md
- https://docs.elitea.ai/integrations/mcp/create-and-use-remote-mcp.md
- https://docs.elitea.ai/how-tos/indexing/indexing-overview.md
- Per-integration pages: `https://docs.elitea.ai/integrations/toolkits/<name>_toolkit.md`

**The live registry beats all of them:** `GET /api/v2/elitea_core/toolkits/prompt_lib/{project_id}` returns the JSON-schema for every valid toolkit type (64 of them). When a doc and the registry disagree, the registry is right.

## Related skills

- **`elitea-platform`** — for the REST endpoint exact payloads (especially § 3 Toolkits, § 9 Tool & Toolkit Discovery)
- **`elitea-pipeline`** — when binding a toolkit inside a pipeline `toolkit` or `mcp` node
- **`elitea-testing`** — for `test_toolkit_tool` and live tool invocation
