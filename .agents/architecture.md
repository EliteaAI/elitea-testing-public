# Architecture

## System overview

This is a **test-automation engagement** — the map below covers the workspace
topology and the Elitea application surface under test, not Elitea's internal
service architecture.

## Workspace topology

```
<workspace>/                             (= parent folder of this clone; plain dir, NOT a repo)
├── .env  .env.test                      master secrets (symlink targets)
├── elitea-testing-public/               THIS repo — tests · branch automation/factory · admin
│   └── automation/.env.test → ../../.env.test
├── onetest-ai-tm-Elitea/                TMS repo ($OT_REPO_ROOT) · admin
│   ├── .onetest/                        config the @onetest/tms MCP package reads via cwd
│   └── tests/automated-full-regression-ui/   case source (markdown + YAML frontmatter)
└── EliteaUI/                            frontend source, READ-ONLY reference (never edited,
                                         never built, never run) — grepped on `main` only to
                                         answer "how is this control wired as DEV ships it"
```

## Runtime data flow

```
pytest (automation/) ──drives──▶ DEV env https://dev.elitea.ai/app (as deployed)
Playwright MCP (analyst/impl) ──▶     │  APP_PREFIX = "/app"
  (storage state from                 ▼
   scripts/dev_storage_state.py) DEV backend (Elitea REST API + WebSocket)
API tests (automation/api/) ──────────┘  (Bearer / cookie auth)

onetest-tms MCP (npx @onetest/tms) ──reads/writes──▶ onetest-ai-tm-Elitea
                                                      (cases, runs, defects → GitHub issues)
```

**DEV is the only environment in the loop.** Nothing is built or served locally;
there is no second target to keep in sync and no frontend change to wait for.

- **Auth:** Keycloak on DEV (`input[name="username"]`); `auth_state` logs in via the API.
- **WebSocket:** AI responses arrive ~2s after send — condition waits required.
- **Other deployed environments** (`next.elitea.ai`, stage) stay CI-only targets.

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

## Locator-debt measurement (design driver, 2026-10)

The team measures **locator debt** — non-testid declarations / all declarations,
plus unmanaged raw handles in method bodies — via
`automation/scripts/locator_inventory.py scan`. Because every locator is a
class-level declaration and every non-testid one names its `suggested_testid`, the
debt is enumerable and burning it down is mechanical.

This replaced an earlier "coverage = testid presence" metric, which made a missing
testid a blocker on every case and pinned each case's fate to a frontend review
cycle. Under the ladder, a missing testid is a hint recorded in the declaration;
the test is green on DEV the day it merges. Converting hints into real testids is a
separate, on-request process with its own session and procedure — out of scope for
any work described in these docs.
