# ELITEA Conventions — Quick Reference

The 90% of the platform you'll touch every day. For full endpoint details load `api-reference.md`.

## 1. Base URLs & API versioning

| Environment | Base URL |
|---|---|
| ELITEA (sole environment) | `https://next.elitea.ai/` |

> **History note.** Older docs and existing scripts in the wild reference `https://nexus.elitea.ai/` as "production". That host has been retired — `next.elitea.ai` is now the only ELITEA environment. If you see `nexus.elitea.ai` in a config, PAT example, or old code path, replace it with `next.elitea.ai`. Symptom of the old host still being targeted: a `307 → 302 → 400 access_denied` redirect chain through Centry's OIDC gateway. There is no separate "production" vs "pre-prod" — they were consolidated.

**v2 is the ONLY surface. Every `/api/v1/...` route is gone.** ELITEA 2.0.4 (02-Jul-2026) completed the v1 deprecation; on `next.elitea.ai` the v1 paths now return **404**, not a deprecation warning (verified live 2026-07-13 — `auth`, `projects`, `configurations`, `secrets`, `artifacts`, `models` all 404). The live OpenAPI spec contains zero v1 paths.

If you have code, a doc, or an example still calling v1, it is broken today. Translation table:

| v1 (dead — 404) | v2 (verified live) |
|---|---|
| `GET /api/v1/auth/me` or `/auth/user` | `GET /api/v2/auth/user/{mode}` |
| `GET /api/v1/projects/projects` | `GET /api/v2/projects/project/{mode}/{project_id}` |
| `POST /api/v1/configurations/configurations/{pid}` | `POST /api/v2/configurations/configurations/{pid}` |
| `*/api/v1/configurations/configuration/{pid}/{cid}` | `/api/v2/configurations/configuration/{pid}/{cid}` |
| `GET /api/v1/configurations/models/{pid}` | `GET /api/v2/configurations/models/{pid}` |
| `GET /api/v1/secrets/secret/default/{pid}/{name}` | `GET /api/v2/secrets/secret/{mode}/{pid}/{secret}` |
| `POST /api/v1/secrets/secrets/default/{pid}` | `POST /api/v2/secrets/secrets/{mode}/{pid}` |
| `/api/v1/artifacts/buckets/default/{pid}` | `/api/v2/artifacts/buckets/{mode}/{pid}` |
| `/api/v1/artifacts/artifacts/default/{pid}/{bucket}` | `/api/v2/artifacts/artifacts/{mode}/{pid}/{bucket}` |
| `/api/v1/applications/upload_icon/...` | No v2 equivalent in the live spec — assume dead |

Note the shape change: configurations, secrets and artifacts moved to `/api/v2/` **and** gained a `{mode}` segment (`default`) that the v1 forms didn't carry in the same position. A blind `s/v1/v2/` will produce a 404 — fix the path shape too.

Third-party ELITEA docs still showing v1 (the Power Automate guide, the webhooks how-to) are stale and carry no deprecation notice. Don't copy from them.

## 1a. The live OpenAPI spec — ground truth for "does this endpoint exist?"

Never guess an endpoint, and don't trust a hardcoded list (including the ones in these skills). The platform publishes its own spec, and it comes in **two surfaces**:

| URL | Paths | What it is |
|---|---|---|
| `/shared/openapi/` | **81** | raw OpenAPI 3.1 **JSON** — the project/user surface |
| **`/shared/openapi/?all=true`** | **133** | raw JSON — **everything.** Use this. |
| `/shared/swagger/` · **`/shared/swagger/?all=true`** | 81 · 133 | the **Swagger UI** for the same two surfaces — browse in a browser, don't parse |

**`?all=true` is the flag that matters.** The 81-path view is a strict *subset*. The extra 52 paths are: the whole `/api/v2/admin/*` surface (36), `support_assistant` (5), `projects/groups` + `monitoring` (6), `configurations/check_connections`, `vectorstore`, the task `DELETE`, and the three 2.0.4 **"Build with AI"** draft generators (`generate_application_draft`, `generate_skill_draft`, `generate_project_context_draft`).

**`?full=true` is a NO-OP** — byte-identical to the bare path. It's `?all=true` you want. (Both can be passed together; only `all` does anything.)

**Hosts:** the same paths work on **`next.elitea.ai`** and **`dev.elitea.ai`** — but each environment needs **its own PAT**. A next token gets a `302` on dev. Unauthenticated → `302` to login. Don't send `Content-Type` on the GET (see § 3).

**Bundled helper:** `scripts/fetch_openapi_spec.py` wraps all of this (defaults to `?all=true`).

```bash
python3 scripts/fetch_openapi_spec.py                 # summary: path count, v1 count, groups
python3 scripts/fetch_openapi_spec.py --grep skill    # which paths exist for a feature
python3 scripts/fetch_openapi_spec.py --show <path>   # full schema for one path
python3 scripts/fetch_openapi_spec.py --diff          # live vs the bundled snapshot
python3 scripts/fetch_openapi_spec.py --update        # refresh references/openapi-spec.json
python3 scripts/fetch_openapi_spec.py --user-surface  # the reduced 81-path view
python3 scripts/fetch_openapi_spec.py --base-url https://dev.elitea.ai   # needs a DEV token
```

`references/openapi-spec.json` is a **snapshot** (refreshed 2026-07-13, **133 paths**, zero v1). Re-run `--update` whenever the platform ships; `--diff` tells you if it's drifted.

### 🚨 The spec is authoritative but NOT complete

Even the 133-path surface has **false negatives** — routes that work in production but are declared nowhere. Verified live 2026-07-13:

| Endpoint | Spec | Reality |
|---|---|---|
| `GET /elitea_core/application_task/{mode}/{pid}/{task_id}` | absent | **works** — the async-predict poll |
| `GET /elitea_core/application/{mode}/{pid}/{app_id}/{version_name}` | absent | **works** — get a version by name |
| `PATCH /elitea_core/skill/{mode}/{pid}/{skill_id}` | absent | **works** — this is the skill-attach call |
| `PATCH /elitea_core/skill/{mode}/{pid}/{skill_id}/{version_id}` | **declared** | **rejected** → `400 "version_id path segment is not supported for PATCH"` |

The last two rows are the lesson in miniature: for the *same feature*, the spec **omits the working route and advertises the broken one**.

**So "absent from the spec" is evidence, not proof, that a route is dead.** Before you conclude a route is gone, check two things:

1. **Are you looking at the full surface?** Fetch with `?all=true`. Several routes "missing" from the 81-path view are simply admin-tier.
2. **Are you using the right `{mode}`?** Admin-scoped routes live under `mode=administration` and **404 on `prompt_lib`/`default`** — which looks exactly like a dead route. `vectorstore` is the cautionary example: it is alive and declared (`POST`/`DELETE`), but it 404s on the two modes you'd reach for first.

Only then, to distinguish a genuinely missing route from a working-but-undeclared one: **call it and compare the failure against a deliberately bogus path** (`/api/v2/elitea_core/totally_bogus_route`).
- **Byte-identical generic 404** → the route really doesn't exist.
- **Anything specific** — a 400 with a message, a 500, a validation error → a real handler ran. The route exists, it's just undocumented.

## 2. The `mode` URL segment

Most v2 endpoints embed `<mode>` between the resource and `{project_id}`:

```
/api/v2/elitea_core/<resource>/<mode>/<project_id>/...
```

| `<mode>` | When |
|---|---|
| `prompt_lib` | ~95% of endpoints — default |
| `default` | MCP proxies, secrets, artifacts, tools_list, tools_call |
| `administration` | Admin-only endpoints (e.g., vectorstore) |

## 3. Authentication

Every request needs:

```
Authorization: Bearer <PAT>
Accept: */*                           # auto-added by most clients
Content-Type: application/json        # ONLY for POST/PUT/PATCH with a body
```

> **Do NOT send `Content-Type: application/json` on GET requests** — some proxies/WAFs reject it with a 400. Use `Accept: application/json` instead.

PATs are issued at: **ELITEA Settings → Profile → API Tokens**.

This repo standardizes on env var name **`ELITEA_TOKEN`**. Older code may use `ELITEA_API_TOKEN` or `ELITEA_NEXT_API_KEY` — same value.

### Special headers (rare)

| Header | Where | Why |
|---|---|---|
| `X-SECRET` | `PATCH /version/...` | Server-to-server "expanded view": returns version with credentials resolved inline |
| `X-USERSESSION` | with `X-SECRET` | Auth context; pass `-` for current user |
| `X-Toolkit-Tokens` | `toolkit_validator` | JSON-encoded OAuth tokens for MCP connection test |
| `X-Hub-Signature-256` / `X-Gitlab-Token` | `POST /webhook/...` | Webhook signature verification |

## 4. ID conventions — `id` vs `uuid`

The single most-common integrator bug. Memorize this:

| Resource | Integer `id` used in… | UUID/string used in… |
|---|---|---|
| **Conversation** | participants endpoints, conversation update/delete, entity_settings, attachments | `POST /messages/.../{conversation_uuid}` (send message) |
| **Message group** | (rare) | `GET /message/.../{uuid}`, `DELETE /message/.../{uuid}`, `POST /regenerate/.../{uuid}` |
| **Canvas** | — | `GET/PUT /canvas/.../{canvas_uuid}` |
| **Configuration** | `PUT /configuration/{project_id}/{configuration_id}` | When referenced inside toolkit settings: `{"elitea_title": "...", "private": <bool>}` instead of id |

> **Rule of thumb:** if you got the value from `POST .../conversations` and are about to call `.../messages/`, use the `uuid` field. Everywhere else use `id`.

## 5. Secret placeholders

When you `GET` a configuration, credential, or toolkit settings, **secret-typed fields come back as templated placeholders**, not `null` and not the raw value:

```json
{ "data": { "access_token": "{{secret.gh_pat_abc123}}" } }
```

To resolve:
- `GET /api/v2/secrets/secret/default/{project_id}/{secret_name}` → `{"value": "ghp_..."}`
- OR call `PATCH /api/v2/elitea_core/version/prompt_lib/{project_id}/{application_id}/{version_id}` with the `X-SECRET` header — returns the version with all configuration references resolved inline

Fields auto-vaulted (from `SENSITIVE_TOOLKIT_SETTINGS`): `access_key, password, username, api_key, access_token, token, app_private_key, google_cse_id, google_api_key, app_id, client_secret, gitlab_personal_access_token, private_token, sonar_token, qtest_api_token, client_id, oauth2`.

## 6. Credential references inside toolkits

When a toolkit's `settings` needs a credential, use the **name reference**, NOT a raw integer id:

```json
{
  "settings": {
    "github_configuration": {
      "elitea_title": "my-github-token",
      "private": true
    }
  }
}
```

- `private = not credential.shared` (a credential is "private" when not shared)

The same pattern applies for `pgvector_configuration`, `embedding_model.ai_credentials`, etc.

### What `elitea_title` actually is (verified live 2026-07-13)

**It's the slug ID, not the display name.** A credential carries both:

```json
{ "elitea_title": "bot_elitea_kb",     // ← the ID. Toolkits reference THIS.
  "label":        "Bot Elitea KB" }    // ← the human display name.
```

Four things that will bite you:

1. **`elitea_title` is REQUIRED on create.** The server does **not** derive it from `label`. Omit it and you get `400 {"error": "Field required", "field": "elitea_title"}`.
2. **🚨 Uppercase is silently lowercased.** Send `ZZScratchUpper4` and the server stores `zzscratchupper4` — with a success response. A toolkit setting that references the *cased* form will then silently fail to resolve the credential. **Always write `elitea_title` in lowercase yourself**, so what you send is what you get.
3. **Hyphens ARE allowed**, despite the validation error text implying otherwise. Spaces, dots and colons are rejected.
4. The docs call this the **"Credential ID"**, auto-derived from the name (spaces → underscores, lowercased). Same field, different name. That's also the key used to match a per-user private credential on a shared toolkit — and that match is **case-sensitive**, which is exactly why point 2 matters.

## 7. Status codes & their meanings

| Code | Meaning in this API |
|---|---|
| 200 | OK; also returned by **configuration create** (`POST /api/v2/configurations/configurations/{project_id}`) — unlike most other creates |
| 201 | Created (standard POST result) |
| 202 | Accepted — message still streaming, poll for completion |
| 204 | No Content — typical DELETE |
| 207 | Multi-Status — used by `import_wizard` and `fork` when some sub-entities imported and others failed |
| 400 | Validation / business-rule failure — body usually `{"error": "..."}` or `{"detail": "..."}` |
| 403 | RBAC denied; project blocks publishing |
| 404 | Entity not found |
| 408 | MCP sync timeout (`mcp_sync_tools`) |
| 409 | Already published |
| 422 | Publish validation `FAIL` state |
| 500 | Internal error |

## 8. The "always-true" workflow patterns

### Conversation → participant → message

```
1. POST /api/v2/elitea_core/conversations/prompt_lib/{project_id}
       body: {"name": "...", "is_private": true, "participants": []}
       → save id + uuid

2. POST /api/v2/elitea_core/participants/prompt_lib/{project_id}/{conv_id}
       body: [{"entity_name": "application", "entity_meta": {"id": agent_id, "project_id": project_id}, "entity_settings": {"version_id": ver_id}}]
       → save response[0].id as participant_id

3. POST /api/v2/elitea_core/messages/prompt_lib/{project_id}/{conv_UUID}     ← UUID not id!
       body: {"participant_id": participant_id, "user_input": "...", "await_task_timeout": 60}
       → 201 with message_groups OR 202 streaming OR 200 with task_id
```

### Stateless single-shot predict (no conversation)

```
POST /api/v2/elitea_core/predict/prompt_lib/{project_id}/{version_id}
     body: {"user_input": "...", "chat_history": []}
     → {"result": "...", "task_id": "..."}
```

### Create agent

```
POST /api/v2/elitea_core/applications/prompt_lib/{project_id}
     body: {
       "name": "My agent",
       "description": "...",
       "type": "interface",
       "versions": [
         {
           "name": "base",                              ← MUST be "base"
           "agent_type": "openai"|"pipeline"|"react",
           "instructions": "<system prompt or pipeline YAML>",
           "llm_settings": {model_name, model_project_id, temperature, max_tokens},
           "variables": [], "tools": [], "tags": [],
           "conversation_starters": [], "welcome_message": "...",
           "meta": {"step_limit": 25}
         }
       ]
     }
     → 201 with version_details.id
```

### Create credential

```
POST /api/v2/configurations/configurations/{project_id}
     body: {
       "elitea_title": "name-for-reference-from-toolkits",
       "label": "Human label",
       "type": "github"|"azure_open_ai"|"amazon_bedrock"|"pgvector"|...,
       "data": {...type-specific fields, secrets auto-vaulted...},
       "shared": false
     }
     → 200 (not 201!)
```

## 9. Inside-pipeline runtime helpers

When code runs **inside an ELITEA pipeline** (in a `code` node), the runtime injects helpers — do NOT read `.env`:

```python
# Auth & base URL — already authenticated as the calling user
elitea_client.auth_token        # the calling user's PAT
elitea_client.base_url          # base URL of the platform

# State access
elitea_state.get('var_name', default)

# alita_client (alias for some operations)
alita_client.unsecret('SECRET_NAME')         # resolve a stored secret
alita_client.artifact('bucket-name')         # artifact bucket helpers
alita_client.get_app_details(application_id) # introspect another agent
alita_client.mcp_tool_call(params)           # call an MCP tool
```

The `FetchUIContext.yaml` example pipeline shows all of these in action.

### Giving an `openai` AGENT the same Python sandbox (`pyodide_sandbox`)

An `openai` agent can run Python at runtime via the built-in **`pyodide_sandbox`** tool. **Enable it by
setting `meta.internal_tools: ["pyodide"]` on the agent VERSION** — that is the ONLY switch. Live-verified
(2026-06-03): **linking a `sandbox`-type toolkit does NOT make it callable** — the toolkit appears in
`tools[]` but the agent cannot call `pyodide_sandbox` at runtime (it hallucinates a fake result). PATCH-link,
full PUT, and inline-at-create all fail without the flag; adding `meta.internal_tools:["pyodide"]` fixes it.

The internal pyodide runtime mirrors the pipeline code-node runtime: `elitea_client.auth_token`
(the **calling user's** token) + `elitea_client.base_url` are injected, and `httpx` has network access
(both `next.elitea.ai` and `raw.githubusercontent.com`) — so the sandbox doubles as a
user-authenticated REST client. Call shape: `{code: "<python>"}`; it returns
`{result: <last expression>, output: <stdout>, execution_info: "Execution time: …s, Packages: …"}`
(end on a trailing expression; no top-level `return`; treat as stateless). **Limits:** stdlib +
`httpx`/`requests`/`chardet` only — **no `pyyaml`, and `micropip` cannot install it**. So don't parse
YAML in the sandbox; author pipelines as a Python **dict**, validate the dict, and deploy via
`json.dumps(spec)` — **a JSON string is accepted as pipeline `instructions`** (JSON is valid YAML;
live-verified).

## 10. Misc one-liners worth remembering

- **Double-curly placeholders in `instructions` become VARIABLES.** ELITEA auto-extracts a double-curly
  `name` pattern (Jinja-style) from an agent's `instructions` into its **variables** (UI-side), and
  substitutes them at runtime. So **never put a literal double-curly placeholder in instructions you don't
  want turned into a variable** — it will pollute the agent's settings and get blanked at runtime. There's
  no clean in-band escape (`{% raw %}` and `{{'{{'}}` both 400; create-validation is lenient but the UI
  extracts). When you must SHOW the syntax in a prompt (e.g. a meta-builder's instructions), use a sentinel
  like `<<name>>` and describe the real form in words. Single-brace `{var}` (pipeline fstring) is unaffected.
  Avatar/icon: `icon_meta` is set by the UI flow (upload via `POST …/upload_icon` → returns full
  `{url,name,size,…}`); it is NOT reliably settable via create/version/app PUT (they drop it).
- **Listing PUBLISHED agents in the public studio (project `1`):** the applications list `total` is **unfiltered** (counts draft/rejected/on_moderation/embedded too — e.g. 604 total but only ~73 published). Filter with **`?statuses=published`** (plural, comma-separated; `?statuses=published,embedded` to widen). The singular `?status=` is **silently ignored** (returns everything). The MCP `get_elitea_core_applications` exposes no query params, so drop to direct REST when filtering. ~58% of published agents **lack `meta.default_version_id`**; for those, `GET /application/prompt_lib/1/{id}` returns the prompt under **`version_details.instructions`** (top-level `instructions` is absent) — read both shapes. List rows never carry `instructions`; they do carry `description`, `tags`, `meta.adoption.{project_count,conversation_count}`.
- **Public project (`promptlib_public`, id 1): you can't direct-predict an UNPUBLISHED/draft agent** — `POST /predict/...` on a draft returns `500 {"error":"Can not do predict"}` (verified 2026-06-04; non-public projects predict drafts fine). Only PUBLISHED versions are API-runnable in public; test public drafts in the UI or publish first. **Unpublishing an agent removes its published version AND cascade-deletes its embedded sub-agents** (e.g. a linked evaluator) — re-create + re-link them after unpublish.
- **Publish flow:** `POST …/publish_validate/...` then `…/publish/...` both need `{version_name: "<new>"}`
  (must NOT reuse `"base"`); publish runs an AI-validation that needs platform Postgres — a DB outage
  surfaces as `400 ai_validation_failed` with a server traceback (platform-side, retry later).
- **First agent version MUST be named `"base"`.** Subsequent versions MUST NOT be `"base"`.
- **`POST /participants/...` body is a LIST**, even for one participant. Response is a list. Use `response[0]`.
- **Adding an agent OR a pipeline to a conversation uses `entity_name:"application"`** (the platform reads `agent_type` from the entity; the stored participant carries `meta.agent_type`). `"pipeline"`/`"agent"` are INVALID — the `entity_name` enum is `user, prompt, datasource, application, llm, dummy, toolkit` (a 400 lists these). So test BOTH agents and pipelines as `"application"`.
- **`POST /import_wizard/...` body is a LIST**, not `{items: [...]}`.
- **`section` field on configurations is server-assigned** — don't send it on create.
- **`agent_type: "pipeline"` requires `instructions` to be valid YAML.**
- **Step limit defaults to 25** if `meta.step_limit` is not set on the version.
- **`return_task_id=true` is mutex with `await_task_timeout > 0`** on `POST /messages/...`.
- **Toolkit name gets sanitized server-side**: `re.sub(r'[^a-zA-Z0-9_.-]', '', name).replace('.', '_')`. Response `toolkit_name` is the sanitized form.
- **Tools array shape differs between CREATE and UPDATE.** On `POST /applications/...` each tool entry needs `type`, `toolkit_id`, `toolkit_name`, `name`, `settings`, `selected_tools` (description optional). On `PUT /version/.../{ver_id}` the same entry also needs `author_id`. Missing `author_id` returns `400 [{"loc": ["tools", N, "author_id"], "msg": "Field required"}]`. Easiest path: GET the existing version, mutate, PUT back — see `scripts/update_version_field.py`.

## 11. Model name resolution — do NOT trust short identifiers

`llm_settings.model_name` must be the **exact identifier** returned by the project's models endpoint, not a friendly short name. Wrong names do not error — they silently fall back to the project default (often `gpt-5-mini` or `gpt-5.4-mini`).

Query the live catalog first:

```
GET /api/v2/configurations/models/{project_id}?include_shared=true
→ { "total": N, "items": [
      { "name": "eu.anthropic.claude-sonnet-4-6", "display_name": "Anthropic Claude 4.6 Sonnet",
        "project_id": 1, "shared": true, "context_window": 400000, "max_output_tokens": 128000,
        "supports_reasoning": true, "supports_vision": true,
        "low_tier": false, "high_tier": true, "default": false, ... },
      ...
    ] }
```

> **v1 is retired — this endpoint moved to v2.** `GET /api/v1/configurations/models/...` now 404s on next.elitea.ai; use the v2 path above (verified 2026-07). More broadly, `references/openapi-spec.json` is v2-only (70 paths, incl. `configurations` and `secrets`) and is the source of truth for valid endpoints — prefer v2 everywhere and verify any lingering v1 path in that spec before using it.

Copy `items[].name` verbatim into `llm_settings.model_name` and use `items[].project_id` as `llm_settings.model_project_id`. The shared catalog lives in `project_id=1` (the `promptlib_public` project). Use `scripts/list_models.py` to print a project's catalog. Each model self-reports its tier via `low_tier` / `high_tier` / `supports_reasoning` / `context_window` — use these to pick models by capability (e.g. a cheap classifier vs. a strong reasoner) instead of hardcoding names.

**To verify your choice actually took effect**, fire a predict and inspect `thinking_steps[].generation_info.model_name` in the response — if it doesn't match what you configured, the runtime fell back. The api-reference dummy examples (`claude-sonnet-4-5`, `claude-opus-4-6`) are **illustrative only**; do not paste them into production payloads without confirming via the models endpoint.

**Gotcha — `reasoning_effort` silently zeroes pipeline LLM nodes.** Setting `llm_settings.reasoning_effort` (e.g. `"low"`) with **Anthropic Haiku 4.5** (`eu.anthropic.claude-haiku-4-5-...`) makes every `llm` node *inside a pipeline* (the LangGraph execution path) emit **0 output tokens** — the call returns nothing, so structured-output state vars stay at their defaults and the run looks like the model answered with the minimum or empty. The asymmetric trap: **`POST /predict_llm/...` TOLERATES `reasoning_effort` and returns 200 with real content**, so the model + settings look fine in isolation — only the pipeline path breaks. Diagnose via the predict response: `llm_response_tokens_output: 0` + `thinking_steps: []` + all structured outputs at default. **Fix:** for `agent_type: pipeline` versions, set `llm_settings` to just `{model_name, model_project_id, temperature, max_tokens}` — omit `reasoning_effort` entirely (overwrite the whole dict; don't inherit it from a prior GET). OpenAI models (`gpt-4.1`, etc.) ignore the field and are unaffected. Bisected live on a minimal one-node pipeline (project 630, 2026-06-25).

## 12. Direct REST vs MCP — when each one works

ELITEA exposes two surfaces:

| Surface | Read | Write |
|---|---|---|
| **MCP (`mcp__elitea-next__*`)** | ✅ Works for GETs (`get_projects_project`, `get_elitea_core_applications`, `get_elitea_core_tools`, `get_auth_user`) | ❌ Most write tools (`post_elitea_core_applications`, `POST /predict/...` (REST — no MCP predict), `post_elitea_core_versions`, `put_elitea_core_version`, etc.) expose only `mode`/`project_id` in their schema with `additionalProperties: false` — they cannot carry a JSON body and 415 immediately. |
| **Direct REST (curl/httpx)** | ✅ | ✅ — required for any operation that needs a body |

> **Rule of thumb:** use MCP tools for reads (cleaner, no auth-host juggling); fall back to direct REST against `next.elitea.ai` (or whichever host your PAT covers — see §1) for any create/update/predict call. The `scripts/build_agent_payload.py` and `scripts/update_version_field.py` helpers exist because of this asymmetry — both pull live state via REST, mutate, and PUT/POST back.

Tangentially: `mcp__elitea-next__get_projects_project` is mis-described in its schema as "Retrieve a single project" but actually returns **all projects accessible to the caller** when given any valid `project_id` (e.g., your `personal_project_id` from `get_auth_user`). Use that to discover project IDs by name without crawling.

## 13. ELITEA 2.0.3+ changes worth knowing

These shipped with the 2.0.3 release; if you're working on a pre-2.0.3 ELITEA instance some of this won't apply yet.

- **Pipeline entry-point triggers** — pipelines can declare a `chat` (default), `scheduled` (cron), or `webhook` trigger at the entry-point node. **Constraint:** `scheduled` and `webhook` pipelines cannot contain HITL, Printer, or interrupt-requiring nodes. See `elitea-pipeline/references/workflows.md` § "Pipeline entry-point triggers".
- **Native cron** — once a pipeline has a `scheduled` trigger, ELITEA fires it directly; no need for external GH Actions cron + REST shim. The external shim is still recommended when the pipeline has interactive nodes OR you need pre/post logic. See `elitea-testing/references/nudge-case-study.md` § "Scheduling".
- **Scheduled-run recording & gotchas** (verified live 2026-06-22) — a fired `scheduled` trigger creates a `source: "pipeline"` conversation named `Scheduled run: <name>` with `meta.scheduled_run`/`meta.scheduled_trigger`. These are **hidden from the default `source=elitea` conversation list** — query `?source=pipeline` (or GET by id) to read a pipeline's run history. Trigger config lives at `…/pipeline_trigger/prompt_lib/{pid}/pipeline/{vid}/trigger` (the shorter `…/{pid}/pipeline/{vid}/trigger` **404s**). Cron is **hourly-minimum** (sub-hourly is accepted by PUT but silently no-ops while `last_run` keeps advancing); a **version PUT wipes** `pipeline_settings.trigger` (re-arm after every version update). Inside the pipeline, the `[Scheduled execution triggered]` marker is **NOT reliably in `elitea_state.get('input')` OR `.get('messages')`** at the entry node — so a code-node pipeline can't detect cron from state. Don't try: make the action-taking mode the **default** and require an explicit opt-in token for the other mode (CHA defaults to APPLY; a `dryrun` token opts into preview). A scheduled run carries no token, so it just works. Full debugging guide: `elitea-pipeline/references/workflows.md` § "Operating & debugging scheduled runs".
- **Sub-agents as standard tools + explicit `task` contract** — sub-agents called as tools no longer inherit the parent's chat history implicitly. The parent must pass everything the child needs via the `task` field. Multi-agent pipelines written pre-2.0.3 may behave differently after upgrade — audit and add explicit task context where needed. See `elitea-toolkit/references/toolkit-types.md` § `application`.
- **Pipeline file attachments as input** — uploaded files are stored in the artifact bucket, and the pipeline receives the file path as an input field. Code nodes retrieve via `alita_client.artifact('bucket').get(path)`.
- **Scoped index creation** — datasource indexers can target a folder within a bucket, not just the whole bucket. Lets one bucket back multiple datasources.
- **ADO project at toolkit level** — for Azure DevOps toolkits, the project is now selected in the toolkit settings (not the credential). One ADO credential can back many toolkits each pointing at a different project. Old toolkits keep working with their existing project-in-credential value until edited.
- **Published-agent per-conversation LLM overrides** — for published agents (in Agent Studio published state), users can override `model_name`, `temperature`, etc. via `entity_settings.llm_settings` on the conversation participant without modifying the agent version. Previously this was rejected with `400 "LLM settings override is only allowed for published agents from agent studio"` for non-published agents — that rule still holds for unpublished agents.
