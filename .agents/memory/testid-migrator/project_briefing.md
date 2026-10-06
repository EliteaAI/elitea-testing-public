---
name: Project briefing
description: Two-phase locator→testid migration — ledger states, deployment gate, diff scopes, report
type: project
---

## Project Knowledge

- **You run on request (from a person or another party), in your own session — never inside a factory batch.** Procedure:
  `.claude/skills/migrate-locators-to-testids/SKILL.md`. Policy: `.agents/testing.md`
  § Locator policy + § Testid-migrator rules; `.agents/role-overrides.md` § Testid migrator slot.
- **The ledger is the work queue:** `.agents/locator-migration/ledger.json`, one row per
  non-testid page-object declaration. States `raw → testid-proposed → on-dev → migrated`
  (`removed` when the declaration disappears). Every move goes through
  `automation/scripts/locator_inventory.py` (`sync-ledger`, `queue`, `check-ui-ref`,
  `mark <id> <state> --evidence …`) — never a hand edit. `sync-ledger` alone sets
  `migrated` / `removed`.
- **Phase A (DEV, test repo):** rows in `on-dev` → swap the declaration to `testid=`
  on branch `locators/<yyyy-mm-dd>` from `automation/base`, run every node id that uses
  the field green against `https://dev.elitea.ai` (`APP_PREFIX=/app`), revert any red
  swap (`mark … testid-proposed`), ONE PR → `automation/base`. Diff touches
  `automation/pages/**` + the ledger only — specs, fixtures, conftest, assertions are
  out of bounds. You never self-merge; a fresh `qa-engineer` reviews per the skill's § Review.
- **Phase B (localhost:5173, EliteaUI):** the next `raw` batch (`queue --limit 25`)
  gets testids named by its `suggested_testid` via `add-data-testid`, committed on
  `automation/testids` (`src/` only), pushed — merge `origin/main` in, never rebase /
  force-push. Then `mark … testid-proposed --ref <sha>`. A human cherry-picks to
  `main`; you open no `main` PR.
- **Deployment gate (`testid-proposed → on-dev`):** the testid is on EliteaUI
  `origin/main` (`git fetch origin` in the SAME command block as `check-ui-ref`)
  **and** observed in the DEV DOM (count ≥ 1, unique in the declared scope). Main is
  not DEV.
- **Rows without a hint** (`suggested_testid: null`, e.g. the 21 legacy rows at cut-over)
  land in `queue`'s `needs_hint` bucket — name the hint in the page object first
  (one small phase-A-style change), never invent a testid without it.
- **Connected repo:** Support Assistant testids go in `../elitea_assistant` on its own
  `automation/testids`; phase A there additionally waits for EliteaUI's dependency bump.
- **Report:** the Migration Report (skill § Report) — per-phase counts, PR URL,
  EliteaUI SHAs, `scan` before/after (locator debt %, unmanaged handles), and every
  row left in place with a one-line reason.
