# OpenAPI Toolkits — Authoring Reference

An OpenAPI toolkit wraps any REST API by giving ELITEA an OpenAPI 3.x spec. The platform reads it, extracts operations, and exposes each as a callable tool.

## Minimal anatomy

```yaml
openapi: 3.0.3
info:
  title: My API
  version: "1.0"
servers:
  - url: https://api.example.com
paths:
  /users/{id}:
    get:
      operationId: getUser              # exposed as the tool name
      summary: Fetch a user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema: {type: integer}
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties: {...}
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
security:
  - bearerAuth: []
```

Save as `.yaml` (or `.json`) and stick the whole thing inline in **`settings.spec`** when creating the toolkit.

> **Field names — get these right.** The toolkit settings keys are **`spec`** and **`openapi_configuration`**. Earlier versions of this file said `schema` and `credentials_configuration`; those are wrong and will not bind. The UI labels the credential field "OpenAPI credentials configuration", which is the tell. There is also **no `schema_url` field** — the spec field itself accepts JSON, YAML, a URL, or raw text, so a hosted spec goes in the same `spec` key.

**Base URL.** If your spec's `servers[0].url` is relative, set the toolkit's `Base Url` field — it must be absolute (`http://` or `https://`). This is a first-class toolkit field, not a spec extension.

## ELITEA-specific extensions — UNVERIFIED

| Extension | Where | Purpose |
|---|---|---|
| `x-elitea-base-url` | top-level | Override `servers[0].url` at runtime |
| `x-elitea-operation-name` | per operation | User-facing tool name (overrides `operationId`) |
| `x-elitea-tool-description` | per operation | Override `summary` as the LLM-visible description |
| `x-elitea-credentials-key` | securityScheme | Reference into the credential's `data` |

> ⚠️ **None of these `x-` extensions appear in the ELITEA docs.** The OpenAPI toolkit page documents no vendor extensions at all, and gives a first-class `Base Url` toolkit field as the documented answer to the `x-elitea-base-url` use case. Our own `examples/elitea-api.yaml` uses them and reportedly works, which is evidence they exist undocumented — but treat them as unsupported until confirmed against a live toolkit. **Vanilla OpenAPI 3 works and is the safe path.**

## Example: catalog of real toolkits

The `examples/` directory contains four real specs you can copy:

- `elitea-api.yaml` · `openapi/elitea-builder-runtime-api.yaml` · `githubissues.json` · `githuboardmoovement.json`

### `elitea-api.yaml` — ELITEA's own API as a toolkit

Demonstrates:
- Bearer auth via `securitySchemes`
- Path-parameterized URLs (`/api/v2/elitea_core/applications/prompt_lib/{project_id}`)
- Mixed param locations (path + query + body)
- `x-elitea-operation-name` to give user-friendly tool names

Use this when you want **an ELITEA agent to call back into ELITEA**.

### `githubissues.json` — GitHub Issues REST

Demonstrates:
- Multiple operations per resource (list, get, create, search)
- Required `Accept` header for GitHub's versioned API
- Pagination params (`per_page`, `page`)
- Body schema for `POST /issues` (title required, body/labels/assignees optional)

Note: JSON form of OpenAPI is also accepted by ELITEA.

### `openapi/elitea-builder-runtime-api.yaml` — the full ELITEA build + runtime API

The largest worked spec in the repo. Reach for it when an agent needs to *build* ELITEA artifacts (create agents, versions, toolkits) rather than just call one.

### `githuboardmoovement.json` — GitHub Projects v2 Boards

Demonstrates:
- **GraphQL wrapping** — single `POST /graphql` endpoint with the GraphQL query in the request body
- ELITEA exposes this as separate "tools" by templating the GraphQL query string per operation

## How operations become tools

Each path × method pair in the spec becomes one tool. Naming priority:

1. `x-elitea-operation-name` if present
2. `operationId` from the OpenAPI spec
3. Auto-derived from path + method (last resort)

The LLM-visible description is `summary` (or `x-elitea-tool-description`).

Input schemas are built from `parameters` (path/query) + `requestBody.content."application/json".schema`. Required fields are properly marked.

## Auth wiring

**A credential is mandatory** — even for a public API with no auth, where you attach an **Anonymous** credential. There is no "no credential" option.

```json
{
  "type": "openapi",
  "settings": {
    "spec": "<the YAML/JSON spec>",
    "openapi_configuration": {
      "elitea_title": "my-api-creds",  // name of a stored credential
      "private": true
    }
  }
}
```

Three credential types, with their exact fields:

| Type | Fields |
|---|---|
| **API Key** | `Api Key` (the token value) · `Auth Type` (`Bearer` \| `Basic` \| `Custom`) · `Custom Header Name` (required only when Auth Type is `Custom`) |
| **OAuth 2.0** | `client_id` · `client_secret` · `token_url` · `auth_url` (optional) · `scope` (optional) · `method` (optional — `default` or `Basic`) |
| **Anonymous** | none — use for public APIs |

For an API Key credential with `Auth Type: Bearer`, the value is injected as `Authorization: Bearer ...` on every tool call. For `Custom`, it goes into the header you name.

## Creation workflow

```bash
# 1. Author the spec
$EDITOR my-toolkit.yaml

# 2. Validate locally
python3 -c "import yaml; yaml.safe_load(open('my-toolkit.yaml'))"

# 3. Create the credential (mandatory — use an Anonymous credential for public APIs)
curl -X POST -H "Authorization: Bearer $ELITEA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "elitea_title": "my-api-creds",
    "label": "My API",
    "type": "openapi",
    "data": {"access_token": "<token>"},
    "shared": false
  }' \
  "https://next.elitea.ai/api/v2/configurations/configurations/$PROJECT_ID"
# → 200, not 201

# 4. Create the toolkit
SPEC=$(jq -Rs . < my-toolkit.yaml)   # JSON-escape the YAML
curl -X POST -H "Authorization: Bearer $ELITEA_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"openapi\",
    \"name\": \"My Toolkit\",
    \"settings\": {
      \"spec\": $SPEC,
      \"openapi_configuration\": {\"elitea_title\": \"my-api-creds\", \"private\": true}
    }
  }" \
  "https://next.elitea.ai/api/v2/elitea_core/tools/prompt_lib/$PROJECT_ID"

# 5. Verify operations were discovered
curl -H "Authorization: Bearer $ELITEA_TOKEN" \
  "https://next.elitea.ai/api/v2/elitea_core/toolkit_available_tools/prompt_lib/$PROJECT_ID/$TOOLKIT_ID"

# 6. Test a single operation (see elitea-testing)
curl -X POST -H "Authorization: Bearer $ELITEA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": '$PROJECT_ID',
    "toolkit_config": {...},
    "tool_name": "getUser",
    "tool_params": {"id": 42}
  }' \
  "https://next.elitea.ai/api/v2/elitea_core/test_toolkit_tool/prompt_lib/$PROJECT_ID?await_response=true"

# 7. Link to an agent version
curl -X PATCH -H "Authorization: Bearer $ELITEA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": '$AGENT_ID',
    "entity_version_id": '$VER_ID',
    "entity_type": "agent",
    "has_relation": true,
    "selected_tools": ["getUser", "createUser"]
  }' \
  "https://next.elitea.ai/api/v2/elitea_core/tool/prompt_lib/$PROJECT_ID/$TOOLKIT_ID"
```

## Updating an existing toolkit

```
PUT /api/v2/elitea_core/tool/prompt_lib/{project_id}/{toolkit_id}
body: {name, description, type, settings, meta}
```

After update, also patch any pipeline YAML that references the old tool names if you renamed operations (the platform DOES auto-rename in pipelines, but verify).

## Common gotchas

- **JSON-escape the YAML schema** when embedding inline in the create payload. Use `jq -Rs .` or `json.dumps(yaml_text)`.
- **No CORS issues** — toolkit operations run server-side, not in the browser.
- **Operation names must be valid identifiers** for LLM tool calling — alphanumeric + underscore. Stick to snake_case.
- **Avoid huge response schemas** — the LLM sees the schema in its context. For large APIs, narrow `selected_tools` to the subset the agent actually needs.
