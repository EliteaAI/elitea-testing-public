# OpenAPI examples

OpenAPI specs you can wrap as an ELITEA `openapi` toolkit.

| File | What it wraps |
|---|---|
| `elitea-builder-runtime-api.yaml` | **The ELITEA platform's own build + runtime API** (28 operations): create/update agents·pipelines·versions·toolkits, link tools, list models, predict, the conversation runtime (conversations·participants·messages·attachments), `getAuthUser`, and project-name lookup. Project-parametric (`{project_id}` path param). Use this when you want an agent that can build/operate ELITEA itself. |

## Creating an `openapi` toolkit from a spec

The live `openapi` toolkit settings shape (field is `spec`, credential ref is `openapi_configuration`):

```jsonc
POST /api/v2/elitea_core/tools/prompt_lib/{project_id}
{
  "type": "openapi",
  "name": "EliteaBuilderRuntimeAPI",
  "settings": {
    "spec": "<the YAML/JSON spec as a string>",
    "base_url": "",
    "selected_tools": [],
    "openapi_configuration": { "elitea_title": "<your-pat-credential>", "private": false }
  }
}
```

Then confirm discovery (`GET /toolkit_available_tools/prompt_lib/{project_id}/{toolkit_id}`) and link
to an agent version (`PATCH /tool/prompt_lib/{project_id}/{toolkit_id}` with
`{entity_id, entity_version_id, entity_type:"agent", has_relation:true, selected_tools}`).

## ⚠️ Auth caveat — when NOT to use an OpenAPI toolkit

An `openapi` toolkit authenticates with the **stored credential** named in `openapi_configuration`
— i.e. ONE owner's token, used for EVERY caller of the agent. That is fine for:

- a toolkit owned and used by a single person, or
- a 3rd-party API that genuinely needs a service account.

It is **wrong for a shared / multi-user agent that should act as the calling user** (correct identity,
attribution, and per-user permissions). For that case, wrap the API in a **pipeline `code` node** and
call it with `elitea_client.auth_token` (the runtime token of whoever invoked the agent), exposed to
the agent as an `application`-type toolkit. See
`agents/elitea-builder/AGENT.md` and `references/toolkit-types.md` for the decision rule.
