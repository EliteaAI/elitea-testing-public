# ELITEA Built-in MCP Tools — Catalog

Each REST endpoint marked with `mcp_tool=True` in the ELITEA source is auto-exposed as an MCP tool. The MCP layer is a thin wrapper — the input schema mirrors the REST endpoint's query/path/body params.

For each tool: its REST endpoint and the **`mode` + `project_id` defaults that get injected**. Full input schemas live in `api-reference.md` under the corresponding endpoint section.

## Common path params (injected on most tools)

| Param | Type | Default | Notes |
|---|---|---|---|
| `mode` | str | `"prompt_lib"` | Operating mode |
| `project_id` | int | required | Project ID |

## Tool catalog (22 built-ins)

> **Names are `snake_case`.** Older versions of this file listed them in camelCase (`getEliteaCoreApplication`). That is wrong — the live MCP server exposes `get_elitea_core_application`. Verified against the connected server 2026-07-13.

| # | Tool name | Method | REST endpoint | API-ref §  | One-line purpose |
|---|---|---|---|---|---|
| 1 | `get_auth_user` | GET | `/api/v2/auth/user/{mode}` | §0.7 | Get current authenticated user (name, email, personal_project_id, avatar) |
| 2 | `get_projects_project` | GET | `/api/v2/projects/project/{mode}/{project_id}` | — | Get project the user can access |
| 3 | `get_elitea_core_application` | GET | `/application/{mode}/{project_id}/{application_id}[/{version_name}]` | §1.1 | Get agent details (incl. version_details) |
| 4 | `get_elitea_core_applications` | GET | `/applications/{mode}/{project_id}` | §1 | List agents with filter, sort, pagination |
| 5 | `post_elitea_core_applications` | POST | `/applications/{mode}/{project_id}` | §1.1 | Create a new agent (with initial `base` version) |
| 6 | `post_elitea_core_versions` | POST | `/versions/{mode}/{project_id}/{application_id}` | §1.4 | Create a NEW version of an existing agent |
| 7 | `put_elitea_core_version` | PUT | `/version/{mode}/{project_id}/{application_id}/{version_id}` | §1.3 | Update an existing agent version (instructions, llm_settings, tools, ...) |
| 8 | `get_elitea_core_conversation` | GET | `/conversation/{mode}/{project_id}/{conversation_id}` | §6.2 | Get full conversation detail (participants + messages) |
| 9 | `get_elitea_core_conversations` | GET | `/conversations/{mode}/{project_id}` | §6.1 | List conversations with filter, sort, pagination |
| 10 | `post_elitea_core_conversations` | POST | `/conversations/{mode}/{project_id}` | §6.3 | Create a new conversation |
| 11 | `put_elitea_core_conversation` | PUT | `/conversation/{mode}/{project_id}/{conversation_id}` | §6.4 | Update a conversation (rename, re-parent) |
| 12 | `post_elitea_core_messages` | POST | `/messages/{mode}/{project_id}/{conversation_uuid}` | §8.2 | **Send a message** (uses `conversation_uuid`, not id) and get reply |
| 13 | `get_elitea_core_participant` | GET | `/participant/{mode}/{project_id}/{conversation_id}/{participant_id}` | §7 | Get one participant's detail |
| 14 | `post_elitea_core_participants` | POST | `/participants/{mode}/{project_id}/{conversation_id}` | §7.2 | Add participants (body is a LIST) |
| 15 | `delete_elitea_core_participant` | DELETE | `/participant/{mode}/{project_id}/{conversation_id}/{participant_id}` | §7.4 | Remove a participant from a conversation |
| 16 | `patch_elitea_core_entity_settings` | PATCH | `/entity_settings/{mode}/{project_id}/{conversation_id}[/{participant_id}]` | §7.3 | Configure participant settings (LLM override, version pin, variables, chat_history_template) |
| 17 | `get_elitea_core_tools` | GET | `/tools/{mode}/{project_id}` | §9.1 | List project toolkits |
| 18 | `get_elitea_core_toolkits` | GET | `/toolkits/{mode}/{project_id}` | §9 | Get the toolkit **type registry** (JSON-schema per toolkit type) |
| 19 | `patch_elitea_core_tool` | PATCH | `/tool/{mode}/{project_id}/{tool_id}` | §3.3, §9.9 | Link/unlink agent ↔ toolkit (sets `selected_tools`) |
| 20 | `get_elitea_core_folder` | GET | `/folder/{mode}/{project_id}` | — | List folders (entity organization) |
| 21 | `post_elitea_core_folder` | POST | `/folder/{mode}/{project_id}` | — | Create a folder |
| 22 | `put_elitea_core_folder` | PUT | `/folder/{mode}/{project_id}` | — | Rename/move a folder |

### Tools that USED to exist and are now GONE

These were in the MCP surface and have been withdrawn. If a script or agent still calls them, it breaks:

| Withdrawn tool | Do this instead |
|---|---|
| `postEliteaCorePredict` | **Call `POST /api/v2/elitea_core/predict/...` over plain REST.** There is no MCP predict any more. |
| `getEliteaCoreMessages` | **Poll `GET /api/v2/elitea_core/messages/...` over REST.** You can send via MCP but not read the reply back — see the workflow note below. |
| `postEliteaCoreAttachments` | REST (multipart). |
| `putEliteaCoreAttachmentStorage` | REST. |
| `putEliteaCoreApplicationAttachmentStorage` | REST. |

**The consequence that matters:** the MCP layer can no longer run an agent end-to-end. It can *send* a message but not *read the reply*, and it can't predict at all. **Any run/test/poll loop must use REST.** MCP is now a build-and-browse surface, not a runtime one.

## Tool grouping by capability

### "Browse / introspect"
`get_auth_user`, `get_projects_project`, `get_elitea_core_application`, `get_elitea_core_applications`, `get_elitea_core_conversation`, `get_elitea_core_conversations`, `get_elitea_core_participant`, `get_elitea_core_tools`, `get_elitea_core_toolkits`, `get_elitea_core_folder`

### "Build agents"
`post_elitea_core_applications` (create), `post_elitea_core_versions` (new version), `put_elitea_core_version` (update version)

### "Wire toolkits"
`patch_elitea_core_tool` (link/unlink with `selected_tools`)

### "Set up a chat" (but not run it — see above)
`post_elitea_core_conversations`, `put_elitea_core_conversation`, `post_elitea_core_participants`, `patch_elitea_core_entity_settings`, `post_elitea_core_messages`

### "Organize"
`get_elitea_core_folder`, `post_elitea_core_folder`, `put_elitea_core_folder`

### "Hygiene"
`delete_elitea_core_participant`

## Common workflows — which tools chain together

### 1. Build + test an agent from scratch (MCP for build, REST for the run)

```
post_elitea_core_applications   → returns id + version_details.id
patch_elitea_core_tool          → link toolkits
post_elitea_core_conversations  → creates a test conversation
post_elitea_core_participants   → add the agent
post_elitea_core_messages       → send a probe (uses conversation_uuid)
--- MCP stops here ---
GET /api/v2/elitea_core/messages/...   → poll for the reply over REST
```

### 2. Browse and resume existing conversation

```
get_elitea_core_conversations   → find by query/source
get_elitea_core_conversation    → get full detail incl. participants
post_elitea_core_messages       → continue chatting (read the reply over REST)
```

### 3. Update agent version in place

```
get_elitea_core_application     → fetch current version_details (preserve fields — incl. `notes`!)
put_elitea_core_version         → merge changes back
```

### 4. Stateless single-shot predict — **REST only**

```
get_elitea_core_application               → discover version_id  (MCP)
POST /api/v2/elitea_core/predict/...      → fire predict         (REST — no MCP tool exists)
```

## Pulling in additional endpoints

The 22 tools above are the auto-wrapped subset. The full REST API has many more endpoints (predict, publish, fork, regenerate, canvas, skills, analytics, triggers) — see `api-reference.md`. To call those, use plain HTTPS.

Two further limits on the MCP layer, both learned the hard way:
- **MCP write tools can't carry a JSON body.** They expose only `mode`/`project_id` and return **415** if you try. Any create/update with a real payload must go over REST.
- **MCP is no longer a runtime surface** (no predict, no message reads). Use it to build and browse; use REST to run.
