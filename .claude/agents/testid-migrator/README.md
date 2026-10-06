# testid-migrator — "Tess"

> Use for locator-to-testid migration of already-green tests. Swaps page-object locators to
> data-testids already deployed on DEV (phase A, PR to `automation/factory`), and adds the next batch of
> testids to EliteaUI on `automation/testids` (phase B), tracking every locator in the migration ledger.

A **project-local** agent (not part of the sdlc-skills marketplace bundle — a bundle update does not
install or overwrite it). The definition lives in [`AGENT.md`](AGENT.md); its procedure is the
[`migrate-locators-to-testids`](../../skills/migrate-locators-to-testids/SKILL.md) skill.

| | |
|---|---|
| Model | `opus` |
| Group | qa |
| Aliases | `testid-migrator`, `tess`, `migrator` |

## Run

Runs on request — started by a person or by another party (an agent, a job, a scheduler).

```bash
claude --agent testid-migrator "Migration run — limit 25"
```

Prerequisites: sibling `../EliteaUI` clone on `automation/testids`, `TEST_USER_*` for DEV in
`automation/.env.test`, and a keyring `gh` login (`env -u GITHUB_TOKEN gh auth status`).

## Inputs / outputs

| | |
|---|---|
| Reads | `.agents/locator-migration/ledger.json`, `automation/pages/**`, `../EliteaUI` (`origin/main`, `automation/testids`), DEV |
| Writes | phase A PR → `automation/factory` (pages + ledger); phase B commits → EliteaUI `automation/testids` (`src/` only) |
| Never | test specs/fixtures, EliteaUI `main` PRs, rebase / force-push, worktrees |
