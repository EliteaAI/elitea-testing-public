# Architecture

## System overview

This is a **test-automation engagement** — the map below covers the three-repo
factory topology and the Elitea application surface under test, not Elitea's
internal service architecture.

## Three-repo factory topology

```
$LOCAL_ELITEA_FOLDER/                    (= parent folder of this clone; plain dir, NOT a repo)
├── .env  .env.test                      master secrets (symlink targets)
├── elitea-testing-public/               THIS repo — tests · branch automation/base · admin
│   └── automation/.env.test → ../../.env.test
├── EliteaUI/                            fork bermudas/EliteaUI · branch automation/testids
│   ├── .env → ../.env                   (VITE_DEV_TOKEN etc.)
│   └── upstream = EliteaAI/EliteaUI     (READ-ONLY — the reason the fork exists)
└── onetest-ai-tm-Elitea/                TMS repo ($OT_REPO_ROOT) · admin
    ├── .onetest/                        config the @onetest/tms MCP package reads via cwd
    └── tests/automated-full-regression-ui/   case source (markdown + YAML frontmatter)
```

## Runtime data flow (local test loop)

```
pytest (automation/) ──drives──▶ EliteaUI dev server :5173 (automation/testids)
                                        │  Vite, APP_PREFIX = ""
                                        ▼
                                 DEV backend (Elitea REST API + WebSocket)
API tests (automation/api/) ────────────┘  (Bearer / cookie auth)

onetest-tms MCP (npx @onetest/tms) ──reads/writes──▶ onetest-ai-tm-Elitea
                                                      (cases, runs, defects → GitHub issues)
```

- **Auth:** Keycloak on deployed envs (`input[name="username"]`); on localhost
  `auth_state` bypasses login via `VITE_DEV_TOKEN`.
- **WebSocket:** AI responses arrive ~2s after send — condition waits required.
- **Deployed environments** (`dev.elitea.ai`, `next.elitea.ai`, `/app` prefix) are
  CI-only targets — reached by GHA workflows during batch gates, never by the local loop.

## Elitea application surfaces (sidebar navigation)

| Surface | What it is | Test area |
|---|---|---|
| Chat | AI conversations, model selection | `tests/ui/chat/` |
| Agents | Configurable AI assistants | `tests/ui/agents/` |
| Pipelines | Multi-step AI workflows | `tests/ui/pipelines/` |
| Skills | Reusable skills | `tests/ui/skills/` |
| Credentials | Auth management | (marker `credentials`) |
| Toolkits | Integrations (Jira, GitHub, …) | `tests/ui/toolkits/` |
| Apps / MCPs | Published apps, MCP servers | — |
| Artifacts | File storage & RAG | `tests/ui/artifacts/` |
| Agents Studio | Agent builder | — |
| Settings / Admin | Configuration, guardrails, voice | `tests/ui/admin/`, `tests/ui/voice/` |
| Support Assistant | Chatbot widget | `tests/ui/support_assistant/` |

## Why the fork + long-lived-branch design exists

Locators are testids in EliteaUI JSX → upstream is read-only and PR review takes
days → deployed envs lag behind on testids → `LocatorDescriptor` has no fallback.
So testids accumulate on the fork's `automation/testids` (served locally with every
testid present) and tests accumulate on `automation/base`; paired batch PRs move
both to their mains, testids first. Full procedure: `.agents/workflow.md`.
