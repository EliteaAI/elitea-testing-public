# ELITEA Skills — versioned instruction packages (2.0.4+)

A **Skill** is a versioned Markdown instruction package that you attach to an agent. It is a first-class ELITEA entity with its own id, versions, import/export, and REST surface — not a field on the agent.

Think of it as the platform's own answer to the thing this repo does with Claude Code skills: reusable guidance you write once, version, and attach to several agents.

> **Naming collision, be careful.** "Skill" now means two different things in this repo: *our* Claude Code skills (`skills/elitea-*/`) and *ELITEA's* Skill entity. This file is about the latter.

## What it is

- **Content is Markdown instructions**, versioned like an agent version.
- **Attached to an agent version**, max **5 per version** (server-enforced).
- **Invoked with a tilde mention** — `~my-skill` — inside agent instructions, and mid-conversation.
- **Team and personal projects only.** Skills are hidden in public projects.

## Constraints (server-enforced — don't discover these the hard way)

| Rule | Value |
|---|---|
| Name charset | lowercase letters, digits, hyphens |
| Name length | ≤ 64 chars |
| **Forbidden in name** | the substrings `claude` and `anthropic` |
| `instructions` length | ≤ **2500** chars |
| `description` length | ≤ 2304 chars |
| First version name | must be `base` (same rule as agents) |
| Max skills per agent version | **5** |
| Attachable to | **agents only** — `entity_type` enum is `["agent"]`. Pipelines cannot carry Skills. |
| Imported skills | always land on `base` |

Deleting the *only* version of a skill returns **400** — delete the skill entity instead.

## REST surface

All paths are `/api/v2/elitea_core/...`, `{mode}` is `prompt_lib`.

```
GET    /skills/{mode}/{pid}                      ?query,tags,author_id,limit,offset,sort_by,sort_order
POST   /skills/{mode}/{pid}                      → 201   create skill (with its first version)
POST   /skill/{mode}/{pid}/{skill_id}            create a NEW version
GET    /skill/{mode}/{pid}/{skill_id}/{version_id}
PUT    /skill/{mode}/{pid}/{skill_id}/{version_id}
DELETE /skill/{mode}/{pid}/{skill_id}/{version_id}   (400 if it's the only version)
DELETE /skill/{mode}/{pid}/{skill_id}            → 204   delete the whole skill
PATCH  /skill/{mode}/{pid}/{skill_id}            → 201   ATTACH / DETACH to an agent version
PATCH  /skill_default_version/{mode}/{pid}/{skill_id}    body {"version_id": N}
GET    /application_skills/{mode}/{pid}/{app_version_id}
GET    /skill_export/{mode}/{pid}/{skill_id}/{version_id}
POST   /skill_import/{mode}/{pid}
```

### Create a skill

```json
POST /api/v2/elitea_core/skills/prompt_lib/{project_id}
{
  "project_id": <project_id>,
  "user_id": <your_user_id>,          // from GET /api/v2/auth/user/{mode}
  "owner_id": <your_user_id>,
  "name": "jira-ticket-hygiene",
  "description": "House rules for writing and grooming Jira tickets.",
  "versions": [
    {
      "name": "base",
      "instructions": "When writing a ticket, always ...",
      "author_id": <your_user_id>,
      "tags": []
    }
  ]
}
→ 201
```

> **Quirk:** the response comes back with `owner_id` set to the **project_id**, not the user id you sent. Don't treat that as an error, and don't "correct" it on a subsequent PUT.

### Attach a skill to an agent version — the one that will trip you

The OpenAPI spec advertises `PATCH /skill/{mode}/{pid}/{skill_id}/{version_id}` for the attach relation. **The server rejects it:**

```
400 {"error": "version_id path segment is not supported for PATCH"}
```

The call that works **omits the version segment** and puts the skill version in the body:

```json
PATCH /api/v2/elitea_core/skill/prompt_lib/{pid}/{skill_id}
{
  "entity_version_id": <agent_version_id>,   // the AGENT's version id
  "entity_type": "agent",                    // enum: ["agent"] only
  "has_relation": true,                      // false to DETACH (→ 200)
  "skill_version_id": <skill_version_id>     // which version of the skill to attach
}
→ 201 {"skill_id": ..., "skill_version_id": ..., "skill_name": "...", "version_name": "base"}
```

### Verify the attachment

```
GET /api/v2/elitea_core/application_skills/prompt_lib/{pid}/{app_version_id}
→ {"skills": [...], "max_skills": 5}
```

`max_skills` is the server telling you the cap — useful as a pre-flight check before attaching a 6th.

## Related: Project Context (2.0.4)

Different mechanism, adjacent purpose. **Project Context** is a single shared Markdown blob, defined in Settings → Project Context, that is auto-injected into **every** agent run and conversation in the project.

- **Team projects only** (not personal, not public).
- Markdown, **2500-char** limit, with an enable/disable toggle and a Build-with-AI generator.
- Individual agents can opt out via an **"Ignore Project Context"** checkbox in their ADVANCED section.
- Permissions: `models.project_context.view` / `models.project_context.edit`.

> ⚠️ **UNVERIFIED: the payload key for the per-agent opt-out.** It is not a typed property on `ApplicationVersionCreateModel` / `UpdateModel`, and it doesn't appear in a live version GET (whose `meta` was just `{"step_limit": 25}`). It's most likely a key inside the untyped `meta` object — but **do not write a guessed field name into a payload.** Resolve it by toggling the checkbox in a *team* project and diffing a version GET. (A personal project can't reproduce it: Project Context doesn't exist there.)
>
> No REST path for reading/writing project context appears in the live spec either (three plausible paths probed → all 404).

## When to reach for which

| You want... | Use |
|---|---|
| Reusable guidance shared across several agents, versioned independently | **Skill** |
| Background that applies to *everything* in a project, with per-agent opt-out | **Project Context** |
| Behaviour specific to one agent | that agent's `instructions` |

## Docs

- https://docs.elitea.ai/menus/skills.md
- https://docs.elitea.ai/menus/settings/project-context.md
