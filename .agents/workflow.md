# How This Team Works

_Seeded 2026-07-10 from operator way-of-work brief + PR sampling (merged PRs #10–15
on `main`). **Revised 2026-07-13: the EliteaUI fork was retired** — `automation/testids`
now lives on `EliteaAI/EliteaUI` directly, and testids reach `main` via per-case draft
PRs instead of a batch. Refresh when the process shifts._

## Git host

- **Host**: GitHub · **CLI**: `gh` · **Unit of change**: Pull Request
- **Remotes**: this repo `EliteaAI/elitea-testing-public` (admin);
  UI repo `EliteaAI/EliteaUI` (push, **no admin**) — worked on **directly, no fork**.
  A stale `fork` remote (`bermudas/EliteaUI`) may still exist locally as a safety
  net; it is **not** part of the workflow. Never push to it.

## The core problem this workflow solves

A test needs a stable locator → the locator is a `data-testid` in EliteaUI JSX →
`main` is owned by the **product UI team**, whose review takes days → deployed envs
lack new testids until that PR merges AND deploys.
`LocatorDescriptor` has **no fallback** — a test bound to a new testid fails hard
anywhere the testid isn't present. Therefore: **`automation/testids` is a permanent
integration branch that accumulates every testid the team ever created** — both the
ones already merged to `main` and the ones still sitting in review. The dev server
runs that branch, so no test and no agent is ever blocked on review latency.

## Branching

| Repo | Long-lived branch | Rule |
|---|---|---|
| elitea-testing-public | `automation/base` (cut from `main`) | small PRs into it, one per test/feature area; **never PR `main` directly** |
| EliteaAI/EliteaUI | `automation/testids` (integration) | **never PR it into `main`.** Per-case `testids/<CASE>-<slug>` branches merge *into* it |

- There is **no CI on `automation/base`** — the green local run before PR is the
  only verification. You are the CI.
- There is **no `pending_testid` marker**. Do not invent one.
- Test work branches: `tests/<case-id>-<slug>`, cut from **`automation/base`**.
- Testid branches: `testids/<case-id>-<slug>`, cut from **fresh `origin/main`** (see below).
- Commit style (sampled from history): conventional-ish — `test: (5199) Add guardrails
  live-reload UI tests`, `refactor: use default gpt-5.2 model`, `docs(afs): amend selectors…`.

### Testid flow — the dual-target rule

A testid branch is **cut from `main`** but **lands in two places**:

```
main ──●────────────────────────●─────────●   EliteaAI/EliteaUI
        \                      /         /    ▲ DRAFT PR — UI team reviews.
         ● testids/EL-1737 ───╯         /       Diff = ONLY this case. Clean.
          \       ● testids/EL-1796 ───╯
           ▼       ▼   (merged immediately, NO review)
    ══════════════════════════════════════▶  automation/testids
             ▲                                ← dev server :5173 runs THIS
             ╰── main merged in, often           agents see EVERY testid,
                                                 merged AND still-in-review
```

**Cut from `main`, not from `automation/testids`.** A PR's diff is computed against
its merge-base — a branch cut from the integration branch would drag every other
case's unmerged testid into your review PR. Cutting from `main` is what keeps the
UI team's PR to a clean single-case diff.

```bash
cd ../EliteaUI
git fetch origin

# 1. cut the per-case branch from FRESH main
git checkout -b testids/EL-1737-skills-import origin/main
#    …edit JSX under src/ ONLY… then commit

# 2. land it on the integration branch IMMEDIATELY (no review, no waiting)
git checkout automation/testids
git merge origin/main                       # keep integration branch current
git merge --no-ff testids/EL-1737-skills-import
git push origin automation/testids          # plain FF push — NEVER --force

# 3. push the case branch and open a DRAFT PR to main for the UI team
git push -u origin testids/EL-1737-skills-import
gh pr create --repo EliteaAI/EliteaUI --base main --draft \
  --head testids/EL-1737-skills-import --title "test(EL-1737): add data-testids for …"
```

**Agents open that PR as a draft.** A human flips it to *ready* when the UI team
should look at it. (This repeals the old rule that agents never PR `EliteaAI/EliteaUI`.)

### Sync: `automation/testids` ← `main`

**Merge. Never rebase, never force-push.** This branch is shared and lives on the org
repo — rewriting its history can clobber a colleague. `--force`/`--force-with-lease`
have **no legitimate use** on it.

```bash
cd ../EliteaUI
git checkout automation/testids
git fetch origin && git merge origin/main
git push origin automation/testids
```

Do this before starting new test work. Conflicts are rare — testid edits are additive
JSX attributes. If `package.json` / `package-lock.json` changed → re-run `npm install`
(a bare version bump doesn't require it).

> **Divergence rule.** If the UI team *changes* a testid during review (renames it,
> moves it), `main`'s version now differs from what's already on `automation/testids`.
> The next `merge origin/main` may conflict. **Resolve in favour of `main`** — it is
> the source of truth — then fix the affected `LocatorDescriptor` in this repo. This
> is inherent to the dual-target design, not a bug.

**Test repo ← main** (periodically): merge `main` into `automation/base`.

**Never shallow clones.** Check `test -f .git/shallow`; fix with `git fetch --unshallow origin`.

## The loop for one new test

1. **Start the local UI** — `start-ui-localhost` skill, or
   `cd ../EliteaUI && npm run dev` → `http://localhost:5173`. It's on
   `automation/testids`, so every team-added testid is present — including ones
   still in review.
2. **Explore** the live UI (Playwright MCP) — find elements lacking testids.
3. **`add-data-testid` skill** — cuts `testids/<case>` from `origin/main`, edits JSX
   under `../EliteaUI/src` (ONLY files under `src/`), merges to `automation/testids`,
   opens the draft PR. Vite HMR reloads — no restart. Naming `{section}-{element}-{type}`;
   verify uniqueness first.
4. **`page-object-generator` skill** — emit **testid-only** descriptors:
   `LocatorDescriptor(testid="agent-form-save-button")`. Never populate `fallback`.
5. **Write the test**, run it green against localhost, PR into `automation/base`.

Nothing in this loop waits on external review. That is the point.

## Promotion — HUMAN-TRIGGERED ONLY

Testid promotion is no longer batched — it happens per case, continuously, via the
draft PRs above. What remains batched is **the tests**, and the lead performs it
**only on explicit request** — never autonomously (`promote-automation-batch` skill):

1. Confirm the testids the batch depends on have **merged to `EliteaAI/EliteaUI` `main`
   and deployed** to the target env. Tests cannot cross into `main` ahead of their testids.
2. Run the suite from GHA against the deployed env.
3. Open the `automation/base → main` gate PR (gate = green deployed run) and merge.

**Ordering invariant, unchanged:** a testid must be merged upstream and deployed
*before* the test that depends on it reaches `main`. Checked once per batch against a
real environment — not per test.

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

### Closure record — the last comment on every automation issue

The work-log comments posted during a run (Started → AFS ready → PR opened → review →
merged) are a **narrative**. The closure record is the **artifact index**. Nobody
re-reads the narrative six months later; they read this one comment to find out where
the work lives and whether it's actually finished. **A bare "✅ merged" is not a closure
record** — that was the gap on #19.

The lead posts this as the final comment on the automation issue, **before** closing it:

```markdown
🔗 **Closure record — <CASE-ID>**

| Artifact | Where | State |
|---|---|---|
| Test | `elitea-testing-public` PR #<N> — `tests/<case>-<slug>` → `automation/base` | ✅ merged (`<sha>`) |
| Testids | `EliteaAI/EliteaUI` PR #<M> — `testids/<case>-<slug>` → `main` | 📝 open, **draft** |
| Testids (integration) | `EliteaAI/EliteaUI` @ `automation/testids` | ✅ merged — dev server serves them |
| AFS | `test-specs/<feature>/l<pri>_<slug>_<CASE-ID>.md` | on `automation/base` |
| Defects filed | #<X>, #<Y> — or "none" | |

**Status:** merged to `automation/base` · ⚠️ NOT yet promotable to `main` — blocked on EliteaUI PR #<M>.
**Unblocks when:** #<M> is marked ready, merged, and deployed to DEV. **Owner:** human.
**Still open:** <follow-ups, or "none">
```

**Why the promotability row is load-bearing here.** Since the fork retirement, a case's
testids can sit in an **open draft PR** while its test is already merged to
`automation/base`. Such a test is **green on localhost and red on any deployed env** —
`automation/testids` has the testids, DEV does not. So *"merged" ≠ "done"*, and the
record must say which. `promote-automation-batch` Stage 1 checks exactly this and will
block the batch; the closure record is what makes that blockage predictable instead of
a surprise months later.

**Do not close an issue whose testids are still in an unmerged PR** — it is `blocked`,
not `completed`. Closing it hides a real cross-repo dependency. Leave it open with the
closure record posted, and let the human close it when the testid PR lands.

Worked example: [issue #19](https://github.com/EliteaAI/elitea-testing-public/issues/19)
(ELITEA-1737) — test merged, testids still in draft PR EliteaUI#525, therefore not
promotable. That is a correct, honest end state.

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
