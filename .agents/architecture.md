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
├── EliteaUI/                            EliteaAI/EliteaUI (NO fork) · automation/testids · migrator-only
│   ├── .env → ../.env                   (VITE_DEV_TOKEN etc.)
│   └── origin = EliteaAI/EliteaUI       push, no admin · main owned by the UI team
└── onetest-ai-tm-Elitea/                TMS repo ($OT_REPO_ROOT) · admin
    ├── .onetest/                        config the @onetest/tms MCP package reads via cwd
    └── tests/automated-full-regression-ui/   case source (markdown + YAML frontmatter)
```

## Runtime data flow (factory loop, 2026-10)

```
pytest (automation/) ──drives──▶ DEV env https://dev.elitea.ai/app (as deployed)
Playwright MCP (analyst/impl) ──▶     │  APP_PREFIX = "/app"
  (storage state from                 ▼
   scripts/dev_storage_state.py) DEV backend (Elitea REST API + WebSocket)
API tests (automation/api/) ──────────┘  (Bearer / cookie auth)

onetest-tms MCP (npx @onetest/tms) ──reads/writes──▶ onetest-ai-tm-Elitea
                                                      (cases, runs, defects → GitHub issues)
```

**Weekly migration loop (`testid-migrator`)** — the only process that runs the local UI:

```
ledger (.agents/locator-migration/ledger.json) ◀── locator_inventory.py sync-ledger
  phase B: localhost:5173 (EliteaUI automation/testids) ── add-data-testid ──▶ push
           ┄┄ human cherry-pick → EliteaUI main → deployed to DEV
  phase A: check-ui-ref sees testid on the deployed ref ──▶ swap descriptor
           ──▶ run affected tests on DEV ──▶ PR → automation/base
```

- **Auth:** Keycloak on DEV (`input[name="username"]`); `auth_state` bypasses login
  via `VITE_DEV_TOKEN` only on localhost (migrator phase B).
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
debt is enumerable and the migration is mechanical. This replaced the earlier
"coverage = testid presence" metric, which forced testid creation into every case
and coupled the factory to EliteaUI review latency.

## Why the integration-branch design still exists (migrator)

EliteaUI `main` is owned by the product UI team (review takes days), so
**`automation/testids` remains a permanent integration branch accumulating every
testid the team writes** — now written only by the weekly `testid-migrator`. The
migrator swaps a test to a testid only after that testid is deployed, so nothing in
`automation/base` ever depends on the integration branch.

**→ `.agents/workflow.md` § The two processes / § The weekly migration loop / § Testid
flow** is the single source for the mechanism.

What lives *only* here — **why the migration is batched weekly:** a swap is only safe
once its testid is on DEV, and deploys arrive in waves; batching the swaps per week
amortises one DEV verification run and one review over many rows, and keeps the
factory's per-case PRs free of cross-repo work.
