# factory-ops — "Rook"

> Use for questions about how the factory operates — which repository owns what, which branch to
> touch, how the container topology differs from this machine's, how a card moves across board #9 —
> and for the sanctioned branch operations (branch/commit/push, merge `main → automation/factory`,
> open a PR into `automation/factory`). Verifies before asserting and pastes the command it ran.

A **project-local** agent (not part of the sdlc-skills marketplace bundle — a bundle update does not
install or overwrite it). The definition lives in [`AGENT.md`](AGENT.md); the verification procedure
it follows on every task is [`RULES.md`](RULES.md).

| | |
|---|---|
| Model | `opus` |
| Group | qa |
| Aliases | `factory-ops`, `rook`, `factory-nav` |

Rook exists because the expensive mistakes in this project are bad *reads*, not bad decisions: a
stale clone of a remote the machine can't reach, a two-dot range that flags your own commit as an
upstream change, a `--limit` that truncates a dedup sweep, a `gh project` call that exits 0 with
half the board. `RULES.md` is the table of those commands and what to run instead.

## Run

```bash
claude --agent factory-ops "Which branch do I cut a new case branch from, and is the harness reachable?"
claude --agent factory-ops "What environment does a new case's test run against?"
claude --agent factory-ops "Merge main into automation/factory and push."
```

Or as a subagent:

```
Agent(subagent_type="factory-ops", prompt="Where does the AFS for a case live, and on which branch?")
```

Prerequisites: the sibling clones in place (`elitea-testing-public`, `onetest-ai-tm-Elitea`,
`EliteaUI`) and a keyring `gh` login (`env -u GITHUB_TOKEN gh auth status`). No browser, no `.venv`
needed for the navigation half; the locator-debt scan needs `.venv` and the `reporting` extra.

## Inputs / outputs

| | |
|---|---|
| Reads | `.agents/*`, `factory/` (config, loops, README), `automation/index.json`, `automation/scripts/locator_inventory.py`, git refs in all four repos, `gh` reads |
| Writes | branches, commits and pushes in `elitea-testing-public`; PRs into `automation/factory`; the merge `main → automation/factory` |
| Never | tracker or board writes · rebase / force-push · worktrees · `EliteaUI` edits · a case PR to `main` · the merge gate (Tal's) · `.env` / `.env.test` contents |

## Where it must live

Factory container sessions read `.claude/` and `.agents/` **only from the checked-out
`FACTORY_WORK_BRANCH`** (`automation/factory`) — `docker/docker-entrypoint.sh` in the harness repo
clones fresh and checks that branch out; the image carries no agent definitions. A definition present
on `main` but not on `automation/factory` is invisible to every unattended session, so this directory
must reach `automation/factory` via the merge-only `main → automation/factory` sync.
