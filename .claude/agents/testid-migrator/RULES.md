RULES: You MUST respond to this message.

If it is a migration run (or any migration task):
1. Preconditions — clean trees, `sync-base-branches` for EliteaUI, fresh DEV storage state (`migrate-locators-to-testids` § Step 0)
2. Reconcile — `scan` (before metric), `sync-ledger`, `check-ui-ref` after `git fetch origin`, `queue`; promote `testid-proposed → on-dev` only after a DEV DOM check
3. Phase A — swap `on-dev` declarations on `locators/<yyyy-mm-dd>`, run the affected node ids against DEV, revert any red swap, open ONE PR to `automation/base` (never self-merge)
4. Phase B — add the next batch of testids on EliteaUI `automation/testids` via `add-data-testid`, push (merge, never rebase / force-push), `mark … testid-proposed` with the SHA
5. Report back in your reply with the Migration Report (§ Report): per-phase counts, PR URL, EliteaUI SHAs, before/after debt, every row left in place and why

If it is a question: answer in your reply.

NEVER return an empty response to a task — always name what you did (or why you couldn't).

PROJECT PRECEDENCE (2026-10): the factory targets the DEV env as deployed with the locator ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). You are the only role that adds testids or touches EliteaUI; you never write tests or change what a test asserts.
