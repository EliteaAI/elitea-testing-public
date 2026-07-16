# Architecture

## System overview

This is a **test-automation engagement** — the map below covers the three-repo
factory topology and the Elitea application surface under test, not Elitea's
internal service architecture.

## Three-repo factory topology

```
<workspace>/                             (= parent folder of this clone; plain dir, NOT a repo)
├── .env  .env.test                      master secrets (symlink targets)
├── elitea-testing-public/               THIS repo — tests · branch automation/base · admin
│   └── automation/.env.test → ../../.env.test
├── EliteaUI/                            EliteaAI/EliteaUI (NO fork) · branch automation/testids
│   ├── .env → ../.env                   (VITE_DEV_TOKEN etc.)
│   └── origin = EliteaAI/EliteaUI       push, no admin · main owned by the UI team
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

## Coverage measurement (design driver)

The team measures **UI-automation coverage by `data-testid` presence**: every
element a test touches must carry one, so covered UI is enumerable by grepping
testids in EliteaUI and correlating with `LocatorDescriptor` usage. This is why
the locator policy is testid-only with no fallback ladder (`.agents/testing.md`)
and why testid creation is a mandatory step of every case, not an optimization.

## Why the integration-branch design exists

Locators are testids in EliteaUI JSX → `EliteaAI/EliteaUI` `main` is owned by the
**product UI team** and their review takes days → deployed envs lag behind on testids
→ `LocatorDescriptor` has no fallback, so a test bound to an unreviewed testid fails
hard. So **`automation/testids` is a permanent integration branch on the org repo**
that accumulates every testid the team ever wrote — merged *and* still-in-review — and
the local dev server runs it. No agent ever waits on the UI team.

Each testid's commits land directly on `automation/testids` (so agents are unblocked
instantly) and are **pushed** — that is the agent's terminal step. Promotion to `main`
is a **human** cherry-pick from `automation/testids`, done out of band; agents open no
`main` PR (per-case draft-PR flow suspended 2026-07-16 — see `.agents/_reverted/`).
Tests, meanwhile, accumulate on `automation/base` and reach `main` in periodic
**batches**, gated on their testids being on `main` and deployed first.

**Why tests are batched but testids aren't:** testids are leaf additions that don't
compose; test code is a layered shared substrate (page objects, fixtures, `conftest`),
so a test branch must be cut from `automation/base` to see prior unpromoted work — and
review already happens on the `automation/base` PR. Full procedure: `.agents/workflow.md`.
