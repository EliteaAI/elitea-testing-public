---
name: elitea-platform
description: Foundation reference for the ELITEA platform — REST API conventions (v2-only since 2.0.4), authentication, project IDs, conversation id-vs-uuid rules, secret placeholders, the 22 built-in MCP tools, the Skills entity, status codes, and base URLs. Use this skill whenever working with ELITEA from outside the platform (REST/HTTP) or whenever an answer requires looking up exact endpoint paths, payload shapes, or error semantics. Other ELITEA skills (elitea-pipeline, elitea-toolkit, elitea-testing) build on this one — load this first when in doubt.
---

# ELITEA Platform — Foundation

The ELITEA platform exposes everything via a REST API and (separately) via an MCP layer. This skill is the index. The deep references live in `references/`.

## Quick lookup — which file answers which question?

| If you need... | Load |
|---|---|
| Auth header, base URL, what `mode=prompt_lib` means | `references/conventions.md` (small) |
| Exact endpoint path, body shape, response codes | `references/api-reference.md` (canonical — the full doc) |
| MCP tool name + input schema (the 22 built-ins) | `references/mcp-tools.md` |
| Quick ID rules (when to use `uuid` vs `id`) | `references/conventions.md` § 3 |
| What `{{secret.NAME}}` placeholders mean | `references/conventions.md` § 4 |
| Standard "create conversation → add participant → send message" flow | `references/conventions.md` § 5 |
| **Skills** — versioned Markdown instruction packages attached to agents (2.0.4) | `references/skills-entity.md` |
| A v1 path that used to work and now 404s | `references/conventions.md` § 1 (translation table) |
| **"Does endpoint X exist? What's its exact schema?"** | **Fetch the live spec** — `scripts/fetch_openapi_spec.py`, or `references/conventions.md` § 1a |

## Always-true facts (no need to load anything)

- **Base URL:** `https://next.elitea.ai/` (the only ELITEA environment — the older `nexus.elitea.ai` host has been retired)
- **Auth header:** `Authorization: Bearer <PAT>` on every request
- **API versions:** **v2 is the only surface.** Since 2.0.4 (02-Jul-2026) every `/api/v1/...` route returns 404 — including configurations, artifacts and secrets, which used to be v1-only. See `references/conventions.md` § 1 for the translation table (the paths also gained a `{mode}` segment, so a blind `s/v1/v2/` still 404s)
- **`mode` segment:** `prompt_lib` for ~95% of endpoints; `default` for MCP proxies / secrets / artifacts; `administration` for admin-only
- **PATs are issued at:** ELITEA Settings → Profile → API Tokens
- **Project ID:** every project has an integer ID visible in the URL (`/app/{project_id}/...`)

## The classic gotchas (memorize these — every integrator hits them)

1. **`POST /messages/...` uses `conversation_uuid` (string), every other conversation endpoint uses the integer `id`.** Capture BOTH from the conversation-create response.
2. **`POST /participants/...` body is a JSON LIST**, even for one participant. Response is also a list — always `response[0]`.
3. **First version of a new agent MUST be named `"base"`**. Subsequent versions MUST NOT be `"base"`.
4. **Toolkit settings reference credentials by `{"elitea_title": "...", "private": bool}`**, never by raw id. `private = not credential.shared`.
5. **Secret-typed fields come back as `"{{secret.<name>}}"` placeholders.** Resolve via `GET /api/v2/secrets/secret/default/{project_id}/{secret_name}` → `{"value": "..."}`.
6. **`POST /api/v2/configurations/configurations/{project_id}` returns 200**, not 201 — one of the few endpoints that breaks the create-returns-201 convention.
7. **Application-version `entity_settings.llm_settings` override is rejected for non-published agents** unless it exactly matches the version baseline. 2.0.3 added per-conversation model overrides *for published agents* — it did NOT loosen this rule for unpublished ones (re-verified live 2026-07-13: `400 "LLM settings override is only allowed for published agents from agent studio"`).
8. **A version PUT wipes fields you omit.** `notes` (2.0.4) joins `author_id` on the list of fields a GET → mutate → PUT round-trip must carry through, or you silently erase them.

## Auth — environment variable conventions

This repo standardizes on **`ELITEA_TOKEN`** for local `.env`. Older code may reference `ELITEA_API_TOKEN` or `ELITEA_NEXT_API_KEY` — they all mean the same PAT. Set up your `.env` once:

```bash
cp .env.example .env
# then edit .env and paste your PAT:
# ELITEA_TOKEN=<paste-here>
```

In Python: `os.environ["ELITEA_TOKEN"]`. In curl: `-H "Authorization: Bearer $ELITEA_TOKEN"`.

When running an ELITEA pipeline whose code calls back into the platform, the runtime injects `elitea_client.auth_token` for free — **do not** read `.env` from inside a pipeline; use `elitea_client.auth_token` and `elitea_client.base_url`.

## Upstream documentation (self-learning)

The repo's `references/` files are a snapshot. The live source of truth is **https://docs.elitea.ai**, and every page is fetchable as plain markdown by appending `.md` to its path — no scraping, no GitHub mirror.

Start here:

- **https://docs.elitea.ai/llms.txt** — the complete page index (every doc URL, grouped by section). This is the entry point; use it to find the right page instead of guessing paths.
- **https://docs.elitea.ai/release-notes/rn_current** — what shipped most recently. Check this first if platform behaviour contradicts these skills.
- Any page: `https://docs.elitea.ai/<path-from-llms.txt>.md`

Archived release notes live at `https://docs.elitea.ai/release-notes/archived/rn-<x-y-z>.md`. Release cadence in 2026: 2.0.0 B2 (19-Jan) · 2.0.0 (19-Feb) · 2.0.1 (26-Mar) · 2.0.2 (30-Apr) · 2.0.3 (28-May) · 2.0.4 (02-Jul).

Two live surfaces beat the docs when they disagree, because the docs lag:

- **`https://next.elitea.ai/shared/openapi/?all=true`** — the raw OpenAPI 3.1 JSON (**133 paths**). This is what the server actually routes. Swagger UI for the same thing: **`https://next.elitea.ai/shared/swagger/?all=true`**. **`?all=true` is the flag that matters** — without it you get a reduced 81-path subset (no admin, no support-assistant, no Build-with-AI draft generators). `?full=true` is a no-op. Both hosts (`next` and `dev`) serve it; each needs its OWN PAT. Fetch with `scripts/fetch_openapi_spec.py` (`--grep`, `--show`, `--diff`, `--update`).
- A real `GET` against the artifact in question.

⚠️ The spec is authoritative but **not complete** — it omits some working routes and advertises at least one broken one. `conventions.md` § 1a lists the known false negatives and how to distinguish a missing route from an undeclared one.

Known-stale doc pages (do not copy from them): the Power Automate integration guide and the webhooks how-to still show `/api/v1/` paths and the retired `nexus.elitea.ai` host, with no deprecation notice.

## Related skills

- **`elitea-pipeline`** — when authoring/debugging pipeline YAML
- **`elitea-toolkit`** — when creating/configuring toolkits (OpenAPI, MCP, first-class integrations, indexing, agent-as-tool)
- **`elitea-testing`** — when running, predicting, debugging, or scheduling ELITEA artifacts

## Core rules (always in effect)

- Never hardcode a PAT in code — read from env / vault / `alita_client.unsecret()`
- Never invent endpoint paths. Copy from `references/api-reference.md` — and when it's silent, ambiguous, or you suspect it's stale, **fetch the live spec**: `python3 scripts/fetch_openapi_spec.py --grep <term>` / `--show <path>`. The spec is what the server actually routes.
- Always use HTTPS; the platform redirects HTTP and the redirect drops Authorization

## Growing this toolkit

When you finish a real task and notice the skill didn't know something, route the learning back: scripts → `scripts/`, gotchas → `references/conventions.md`, response-shape facts → `references/api-reference.md`. Full decision tree, generalization checklist, and "what NOT to promote" rules in **`references/growing-this-toolkit.md`** — load it before adding a new file or section so you put the knowledge in the place future sessions will actually find it.

## Bundled scripts

- **`scripts/fetch_openapi_spec.py` — fetch the LIVE OpenAPI spec.** The answer to "does endpoint X exist / what's its schema". `--grep <term>` to find paths for a feature, `--show <path>` for one path's full schema, `--diff` to see if the bundled snapshot has drifted, `--update` to refresh it. Reach for this **before** trusting any endpoint list in these files, including `api-reference.md`.
- `scripts/list_models.py` — print the LLM models available to a project. Run this BEFORE writing any `llm_settings.model_name`; the api-reference shortnames are illustrative and wrong names silently fall back to the project default.
- `scripts/build_agent_payload.py` — compose a complete `POST /applications/...` payload by pulling live toolkit settings from the project. Handles the `type`+`settings`+`selected_tools` shape that the create endpoint actually requires.
- `scripts/update_version_field.py` — GET an agent version, mutate a small set of fields (dotted-path syntax), PUT it back. Preserves tools, `author_id` and `notes`. Dry-run by default; `--apply` to commit.
