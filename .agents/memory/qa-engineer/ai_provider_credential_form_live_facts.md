---
name: AI-provider credential form — live facts
description: The Settings AI-provider "+" flow reuses CredentialForm; a valid open_ai credential already exists in .env.test; typing quirks that silently lose input
type: project
aliases: [ai providers, create-ai-provider, ai credential, test connection, llm_model form, open_ai credential]
tags: [area/settings, area/credentials]
created: 2026-08-30
updated: 2026-08-30
---

## Route

`sidebar-create-button` -> `/settings/create-ai-provider?viewMode=owner&from=ai-providers`.
**Without the query string the same route renders the 29 TOOLKIT type cards instead of
the 12 AI ones** — deep links must carry `?viewMode=owner&from=ai-providers`. Cards take
several seconds to appear; poll for `[data-testid^="toolkit-type-card-"]`.

The form itself is `CredentialForm.jsx` — literally the same component as the toolkit
Credentials page (`CreateCredentialFromMain title="New AI Provider"`), so every merged
toolkit-credential handle applies verbatim. Test connection appears whenever the type
schema sets `has_test_connection` (true for `open_ai`, `llm_model`; false for `pgvector`).

## A valid open_ai credential already exists in the suite's test data

`.env.test` has no OpenAI key, but Elitea's own OpenAI-compatible gateway accepts
`ELITEA_API_TOKEN`:

- `api_base = https://dev.elitea.ai/llm/v1`, `api_key = settings.elitea_api_token`
- verified out-of-band: `/llm/v1/models` -> 200 with that token, 401 with a bogus one
- through the UI: `check_connection` -> `200 {"success": true}` + `The connection is OK!`

This is what let ELITEA-2415's success half run honestly with no substitution. Reach for
it before declaring an AI-credential case blocked on missing test data.

## Two typing quirks that cost two runs each

1. **`fill()` does not register** with these MUI controlled inputs — the DOM value looks
   right and the backend receives EMPTY (`400 {"message": "api_base is required"}`).
   Use click -> `ControlOrMeta+a` -> `Backspace` -> `press_sequentially`.
2. **The first keystroke after render can be lost to a re-render.** Settle ~2 s after
   `wait_for_selector`, then type, then READ THE VALUE BACK and retry. Symptom: Save
   stays disabled and the ID field never auto-fills from Display Name.

## Teardown

`DELETE {api}/configurations/configuration/{project}/{id}` -> **204** works for both AI
credentials and LLM models (this resolves ELITEA-2417's "no delete path verified").
Delete the model before the credential it references.

⚠️ A fresh Playwright context defaults to project **399** while the persistent MCP
browser profile sits on **400** — a config created from a scratch script lands in 399.
Read the project id off the request path.

Related: [[chat_error_surface_is_socket_only]]
