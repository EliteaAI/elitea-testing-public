# How This Team Works

_Seeded 2026-07-10 from operator way-of-work brief + PR sampling (merged PRs #10–15
on `main`; `automation/base` has no PR history yet — it's new). Refresh when the
process shifts._

## Git host

- **Host**: GitHub · **CLI**: `gh` · **Unit of change**: Pull Request
- **Remotes**: this repo `EliteaAI/elitea-testing-public` (admin);
  UI fork `bermudas/EliteaUI` (write) with `upstream = EliteaAI/EliteaUI` (read-only)

## The core problem this workflow solves

A test needs a stable locator → the locator is a `data-testid` in EliteaUI JSX →
we cannot push to `EliteaAI/EliteaUI` (read-only; PR review takes days) → deployed
envs lack new testids until upstream merges AND deploys.
`LocatorDescriptor` has **no fallback** — a test bound to a new testid fails hard
anywhere the testid isn't deployed. Therefore: **both repos keep a long-lived
branch where work accumulates**, and tests run against the local fork where every
testid the team ever added is present.

## Branching

| Repo | Long-lived branch | Rule |
|---|---|---|
| elitea-testing-public | `automation/base` (cut from `main`) | small PRs into it, one per test/feature area; **never PR `main`** |
| EliteaUI fork | `automation/testids` | commit testid edits directly onto it; **never PR `EliteaAI/EliteaUI` yourself** |

- There is **no CI on `automation/base`** — the green local run before PR is the
  only verification. You are the CI.
- There is **no `pending_testid` marker**. Do not invent one.
- Branch naming for work branches: `automation/<case-id>-<slug>` or `tests/<id>-<slug>`,
  cut from `automation/base`.
- Commit style (sampled from history): conventional-ish — `test: (5199) Add guardrails
  live-reload UI tests`, `refactor: use default gpt-5.2 model`, `docs(afs): amend selectors…`.

### Catch-up / sync procedures

**EliteaUI fork ← upstream** (before starting new test work; conflicts rare — testid
edits are additive JSX attributes):

```bash
cd ../EliteaUI
git fetch upstream
git checkout automation/testids && git rebase upstream/main
git push --force-with-lease origin automation/testids   # only after a rebase that moved commits
```

If `package.json` dependencies or `package-lock.json` changed → re-run `npm install`
(a bare version bump doesn't require it). Also pull teammates' testids at the same
moment: `git pull origin automation/testids` (before the rebase).

### Testid commit & push discipline (the fork)

- **During work:** commit testid edits directly onto local `automation/testids`
  (no work branches, no PRs inside the fork). The dev server serves your working
  tree — Vite HMR shows edits immediately; no pull/push needed to "update the UI".
- **On green — together with opening the test PR:** `git push origin automation/testids`
  (plain fast-forward push). Invariant: **origin `automation/testids` must contain
  every testid that origin `automation/base` tests reference** — never merge a test
  PR whose testids aren't pushed.
- **`--force-with-lease` is ONLY for after an upstream rebase** — never for routine
  pushes.

**Test repo ← main** (periodically): merge/rebase `main` into `automation/base`.

**Never shallow clones.** `git rebase upstream/main` silently misbehaves on shallow
clones. Check `test -f .git/shallow`; fix with `git fetch --unshallow origin`.

## The loop for one new test

1. **Start the local UI** — `start-ui-localhost` skill, or
   `cd ../EliteaUI && npm run dev` → `http://localhost:5173`. It's on
   `automation/testids`, so every team-added testid is present.
2. **Explore** the live UI (Playwright MCP) — find elements lacking testids.
3. **`add-data-testid` skill** — edits JSX in `../EliteaUI/src` (ONLY files under
   `src/` — nothing else in the UI repo), commits to `automation/testids`. Vite HMR
   reloads — no restart. Naming `{section}-{element}-{type}`; verify uniqueness first.
4. **`page-object-generator` skill** — emit **testid-only** descriptors:
   `LocatorDescriptor(testid="agent-form-save-button")`. Never populate `fallback`.
5. **Write the test**, run it green against localhost, PR into `automation/base`.

Nothing in this loop waits on external review. That is the point.

## Batch operations — HUMAN-TRIGGERED ONLY

The lead performs these **only on explicit request, with all required clarifications**
— never autonomously:

1. Open PR to `EliteaAI/EliteaUI` with accumulated testids from `automation/testids`
   (periodically a human cuts a clean branch off fresh `upstream/main`, replays
   testids, opens one batched PR).
2. Merge upstream → restart DEV.
3. Run the suite from GHA against the deployed env.
4. Open `automation/base → main` gate PR (gate = green deployed run) and merge.

**The two batches are paired and ordered**: testids must merge upstream and deploy
*before* the matching tests cross into `main`. Checked once per batch against a real
environment — not per test.

## Review gates (pipeline-internal)

- Every automation PR into `automation/base`: adversarial review by `qa-engineer`
  (fresh session, `code-review` + triangulation vs TMS case and AFS) →
  `APPROVED` | `CHANGES_REQUESTED`; the lead merges.
- Commit authority: the implementer commits on the work branch the lead names
  (or creates one from `automation/base` when dispatched standalone). Testid commits
  to `automation/testids` are part of the implementer/analyst loop.

## Work tracking

Board #9 discipline lives in `.agents/profile.md` § Issue tracker — status machine,
human-only `Approved`, `question`/`bug` labels, work-log comments, and the
**identity rule**: every tracker/board write is prefixed `env -u GITHUB_TOKEN` so it
runs as the keyring account, never the shared `GITHUB_TOKEN`. Board mechanics:
`env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --format json`,
`… gh project field-list …`, `… gh project item-edit` — look up ids each time,
never hardcode.
Interactive session → the human in the room authorizes work; factory mode → work only
the one issue the dispatch names.

## Traps (cost someone an hour already)

- `requirements.txt` is **mkdocs-only**. Real deps: `pip install -e ".[reporting]"` —
  pytest won't even start without `allure-pytest` (`--alluredir` in addopts).
- venv must be Python 3.11+ (repo `.venv` is 3.13.13).
- `EliteaUI` has **no `.env.example`** (despite `start-ui-localhost` docs); its `.env`
  is a symlink to the master copy — don't recreate it.
- `npm install` looks hung during resolution — it isn't. Starting the dev server too
  early → `sh: vite: command not found`.
- OneDrive makes clones/fetches/installs slow — background long git/npm commands.
- `.env.test` beats shell exports (`config.py` orders dotenv first) — edit the file.
- Always run with cwd = `elitea-testing-public/` — that's what loads `.claude/skills`,
  `.claude/rules`, `.mcp.json`, `CLAUDE.md`, and lets `add-data-testid` grep `../EliteaUI/src`.

## Unconfirmed

- `automation/base` PR review-approval count (branch is new — no PR history yet;
  pipeline-internal review applies regardless).
