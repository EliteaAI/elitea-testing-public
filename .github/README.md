# QA Orchestrator — ELITEA Test Automation Workspace

A VS Code–based QA automation workspace that uses **GitHub Copilot Agent Mode** to run an end-to-end test generation pipeline for the [ELITEA platform](https://next.elitea.ai/app/). Given a GitHub issue link, the **QA Orchestrator** agent automatically reads the issue, researches documentation, explores the live UI, audits existing test coverage, generates a functional testing checklist, and pushes structured test cases to **OneTest**.

---

## How It Works

```
GitHub Issue URL
       │
       ▼
 [1] reading-github-issue     ← parse issue details & derive tags
       │
       ▼ (parallel)
 [2a] elitea-docs-researcher   ← query ELITEA documentation indexes
 [2b] elitea-playwright-explorer ← live browser exploration of the feature
 [2c] onetest-researcher      ← audit existing test coverage in OneTest
       │
       ▼
 [3] checklist-generator      ← produce P0/P1/P2 functional testing checklist
       │
       ▼ (after user approval)
 [4] test-case-generator      ← generate, review, and push test cases to OneTest
```

---

## Project Structure

```
.github/
├── agents/
│   └── qa-orchestrator.md          # Main agent definition
├── prompts/
│   └── create-test-case.prompt.md  # Reusable prompt shortcut
└── skills/
    ├── elitea-docs-researcher/       # ELITEA docs research skill
    ├── checklist-generator/         # P0/P1/P2 checklist generation skill
    ├── elitea-playwright-explorer/  # Live UI exploration via Playwright
    ├── onetest-researcher/          # Existing test coverage audit skill
    ├── reading-github-issue/        # GitHub issue reader skill
    └── test-case-generator/         # OneTest test case creation skill

```

---

## Prerequisites

| Requirement | Purpose |
|---|---|
| [VS Code](https://code.visualstudio.com/) — **latest version required** | Editor with Copilot Agent Mode support. Agent Mode and MCP features require the most recent release. |
| [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) extension | Powers the agent and skills |
| [Node.js](https://nodejs.org/) ≥ 18 | Required by the Playwright MCP server (`npx`) |
| A GitHub account with Copilot access | Required for agent mode and GitHub API calls |
| An ELITEA account at [next.elitea.ai](https://next.elitea.ai) | For documentation research and live UI exploration |
| [`gh` CLI](https://cli.github.com/) authenticated via `gh auth login` | Required by `onetest-tms` for reading and creating test cases in the TMS repo |

---

## Setup Instructions

### 1. Update VS Code to the latest version

Agent Mode and MCP server support require the most recent VS Code release. The workspace was created and tested on **VS Code 1.109.5**. Check for updates before proceeding:

```
Help → Check for Updates
```

Or download the latest version directly from [code.visualstudio.com](https://code.visualstudio.com/).

### 2. Clone / copy this workspace

Copy the entire folder to your machine and open it in VS Code:

```
File → Open Folder → select the project folder
```

### 3. Configure your credentials and place `mcp.json`

A ready-to-use `mcp.json` file with all MCP servers pre-configured is provided in the [docs/required-mcps-for-tc-agent](../docs/required-mcps-for-tc-agent/) folder. You only need to open it, fill in your personal credentials for two servers — **`EliteA_by_mcp`** and **`github`** — and then move the file into your `.vscode` folder. The **`onetest-tms`** and **`microsoft/playwright-mcp`** servers require no credentials — they use `npx` and `gh` CLI ambient authentication respectively.

**Steps:**

1. Open [docs/required-mcps-for-tc-agent/mcp.json](../docs/required-mcps-for-tc-agent/mcp.json).
2. Replace every `${...}` placeholder with your actual credentials (see table below).
3. Move the file to a `.vscode/` folder at the root of this workspace. If the `.vscode/` folder does not exist yet, create it first, then place `mcp.json` inside it:

```
<workspace-root>/
└── .vscode/
    └── mcp.json   ← place the file here
```

- *(alternative)* **Set via Command Palette**  — press `Ctrl+Shift+P` (Windows / Linux) or `Cmd+Shift+P` (macOS), type **`MCP: Open User Configuration`**, and press `Enter`. Note: this opens the *user-level* global config, not the workspace one — use this only if you prefer to store credentials globally instead of per-workspace.

#### Where to get each credential

| Credential | How to obtain |
|---|---|
| `${YOUR_GITHUB_PERSONAL_ACCESS_TOKEN}` | GitHub → Settings → Developer settings → Personal access tokens → Generate new token (classic). Scopes needed: `repo`, `read:user` |
| `${YOUR_ELITEA_AUTH_TOKEN}` | In ELITEA → open the **Elitea Testing Team** project → Settings / Secrets → copy `secret.auth_token` |

> **Note:** The `onetest-tms` server uses `gh` CLI for authentication (ambient auth via `gh auth login`) — no separate API key is needed.

> **Security note:** Never commit credentials to version control. Make sure the `.vscode/` folder is not pushed to a public repository.

### 4. Verify MCP servers are active

Open VS Code **Copilot Chat** and switch to **Agent Mode** and select configure tools. All four MCP servers should be accessible. If any server shows an error, recheck that the credentials in `.vscode/mcp.json` are correct and belong to the same project (project ID and `auth_token` must match).

**Important:** If after setup the `create-test-case.prompt.md` prompt underlines the **"QA Orchestrator"** name (agent not recognized), or if the **QA Orchestrator** agent in Copilot Chat shows **all** available MCP tools instead of only the required ones, do the following:

 1. Open `.github/agents/qa-orchestrator.md` in VS Code.
 2. Above the tools list in the agent definition, click **"Configure Tools"**.
 3. Click **OK** to confirm.
 - The `tool` label might dissapear after confirming, so make sure to type add it back. 
After this, the prompt will correctly resolve the agent reference, and the agent will have access only to the tools it needs.

---

## How to Use

### Option A — Use the QA Orchestrator agent directly

1. Open VS Code **Copilot Chat** (`Ctrl+Alt+I` / `Cmd+Alt+I`).
2. Switch to **Agent Mode**.
3. Select the **QA Orchestrator** agent from the agent picker.
4. Paste a GitHub issue URL and send:

   ```
   https://github.com/your-org/your-repo/issues/123
   ```

5. The agent will automatically:
   - Parse the issue
   - Research ELITEA documentation
   - Explore the live UI via Playwright
   - Audit existing OneTest coverage
   - Generate a P0/P1/P2 functional testing checklist

6. After reviewing the checklist, confirm when asked to generate and push test cases to OneTest.

### Option B — Use the prompt shortcut

1. Open Copilot Chat in Agent Mode.
2. Type `/create-test-case` and attach a GitHub issue URL.
3. The prompt automatically targets the **QA Orchestrator** agent and starts the workflow.

---

## Skills Reference

| Skill | Trigger | What it does |
|---|---|---|
| `reading-github-issue` | Step 1 of orchestrator | Fetches and parses GitHub issue into a structured report |
| `elitea-docs-researcher` | Step 2 (parallel) | Queries all three ELITEA documentation indexes for the feature |
| `elitea-playwright-explorer` | Step 2 (parallel) | Logs into ELITEA and explores the relevant feature page via browser automation |
| `onetest-researcher` | Step 2 (parallel) | Searches OneTest for existing test cases related to the feature |
| `checklist-generator` | Step 3 | Produces a P0/P1/P2 functional testing checklist from all research outputs |
| `test-case-generator` | Step 4 (after approval) | Generates test cases, detects duplicates, resolves suites, and pushes to OneTest |

---

## Fixed Configuration (do not change)

The following value is hardcoded across all skills and the orchestrator agent — **do not ask users for it**:

- **TM_REPO:** `EliteaAI/onetest-ai-tm-Elitea`

---

## Troubleshooting

| Issue | Solution |
|---|---|
| MCP server not connecting | Double-check the bearer token and URL in `mcp.json`; restart VS Code |
| Playwright login fails | Ensure Node.js is installed and `npx playwright install chromium` has been run; check ELITEA credentials |
| Test case PR creation fails | Ensure `gh` CLI is authenticated (`gh auth login`) and the TMS workspace is cloned at `~/.onetest-workspaces/EliteaAI/onetest-ai-tm-Elitea` |
| Agent not appearing in picker | Ensure the GitHub Copilot extension is up to date and agent mode is enabled in VS Code settings |
| Skills not found | Confirm the `.github/skills/` folder is present and VS Code recognizes it as the workspace root |
