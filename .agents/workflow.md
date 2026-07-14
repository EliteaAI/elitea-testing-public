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
| EliteaAI/EliteaUI | `automation/testids` (integration) | **never PR it into `main`.** Testid commits are born ON it; per-case `testids/<CASE>-<slug>` review branches (built on `main`) receive them by cherry-pick |

- There is **no CI on `automation/base`** — the green local run before PR is the
  only verification. You are the CI.
- There is **no `pending_testid` marker**. Do not invent one.
- Test work branches: `tests/<case-id>-<slug>`, cut from **`automation/base`**.
- Testid branches: `testids/<case-id>-<slug>`, cut from **fresh `origin/main`** (see below).
- Commit style (sampled from history): conventional-ish — `test: (5199) Add guardrails
  live-reload UI tests`, `refactor: use default gpt-5.2 model`, `docs(afs): amend selectors…`.

### Testid flow — the dual-target rule

A testid is committed **once, straight onto `automation/testids`** (the dev server
runs it — instant HMR feedback, durable the moment it exists), then **cherry-picked
onto a per-case review branch built on fresh `main`**:

```
main ──●────────────────────────●─────────●   EliteaAI/EliteaUI
        \                      /         /    ▲ DRAFT PR — UI team reviews.
         ● testids/EL-1737 ───╯         /       Diff = ONLY this case. Clean.
          \       ● testids/EL-1796 ───╯        (branches BUILT ON main,
           ▲       ▲                              filled by cherry-pick)
           ┆ cherry-pick ┆
    ══●══════●═══════════════════════════▶  automation/testids
      ▲   testid commits BORN here           ← dev server :5173 runs THIS
      ╰── main merged in, often                 agents see EVERY testid,
                                                merged AND still-in-review
```

**The review branch is built on `main`, never on `automation/testids`.** A PR's
diff is computed against its merge-base — a branch cut from the integration branch
would drag every other case's unmerged testid into your review PR. Building it on
`main` and cherry-picking only this case's commits is what keeps the UI team's PR
to a clean single-case diff (verify with the diff-check in `add-data-testid`).

```bash
cd ../EliteaUI                            # dev server is live on automation/testids
git fetch origin

# 1. edit JSX under src/ ONLY, commit ON automation/testids (HMR shows it instantly),
#    then push the integration branch (plain FF — NEVER --force)
git add src/ && git commit -m "test: [EL-1737] add data-testid for …"
git merge origin/main && git push origin automation/testids

# 2. build the review branch in a WORKTREE — never `git checkout origin/main` in the
#    main tree: that strips every pending testid out from under the running dev server
git worktree add -b testids/EL-1737-skills-import ../.testid-pr origin/main
git -C ../.testid-pr cherry-pick <this case's testid commits>
git -C ../.testid-pr push -u origin testids/EL-1737-skills-import

# 3. open the DRAFT PR to main for the UI team, then clean up
gh pr create --repo EliteaAI/EliteaUI --base main --draft \
  --head testids/EL-1737-skills-import --title "test(EL-1737): add data-testids for …"
git worktree remove ../.testid-pr
```
(Full procedure with diff-verification steps: `add-data-testid` skill § Git flow.)

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
3. **`add-data-testid` skill — MANDATORY for every element the test touches that
   lacks a testid.** There is no fallback rung: locator policy is testid-only
   (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`) because the
   team measures UI-automation coverage by testid presence — a role/CSS handle is
   invisible to that metric. The skill edits JSX under `../EliteaUI/src` (ONLY files
   under `src/`), commits on `automation/testids`, builds `testids/<case>` from
   `origin/main` in a worktree, opens the draft PR. Vite HMR reloads — no restart.
   Naming `{section}-{element}-{type}`; verify uniqueness first.
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
- **Dispatch-prompt contract (lead):** every implementer and reviewer dispatch
  prompt carries the locator-policy line verbatim — see
  `.agents/role-overrides.md` § Orchestrator slot. The dispatch prompt is the gate.
- **Reviewer mechanical check:** any non-testid handle *added* in
  `automation/pages/` or `automation/tests/` is `CHANGES_REQUESTED` — grep the PR
  diff for added `get_by_role|get_by_label|get_by_text|page.locator|.locator(`
  lines; each hit must be a `[data-testid=` selector. Existing raw handles are
  tracked tech debt (#25/#42), not precedent.
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

The lead posts this as the final comment on the automation issue, **before** closing it.
**The promotability row is a verified fact, not a copy of the AFS/implementer claim**
(#35/#36/#37 shipped false "fully promotable" rows that way): grep the case's test +
page-object diff for the testids it uses, then check each against `EliteaAI/EliteaUI`
**main** and `automation/testids` (`git grep 'data-testid="<id>"' origin/main -- src/`
and the same against `origin/automation/testids`). Only testids present on **main**
make a case promotable:

```markdown
🔗 **Closure record — <CASE-ID>**

| Artifact | Where | State |
|---|---|---|
| Test | #<N> — `tests/<case>-<slug>` → `automation/base` | ✅ merged (`<sha>`) |
| Testids | EliteaAI/EliteaUI#<M> — `testids/<case>-<slug>` → `main` | 📝 open, **draft** |
| Testids (integration) | `EliteaAI/EliteaUI` @ `automation/testids` | ✅ merged — dev server serves them |
| AFS | `test-specs/<feature>/l<pri>_<slug>_<CASE-ID>.md` | on `automation/base` |
| Defects filed | #<X>, #<Y> — or "none" | |

**Status:** merged to `automation/base` · ⚠️ NOT yet promotable to `main` — blocked on EliteaAI/EliteaUI#<M>.

> **Cross-repo links: write `EliteaAI/EliteaUI#<M>` as PLAIN TEXT — never inside
> backticks, never bare `#<M>`.** Bare `#<M>` links to THIS repo's #M (wrong), and
> GitHub never auto-links inside code spans. The `owner/repo#N` form renders as a
> clickable cross-repo link AND leaves a "mentioned in…" backlink on the EliteaUI
> PR — the UI team sees which case waits on their review. Same-repo references
> (the test PR) stay bare `#<N>`.
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

**Do not close an issue whose testids are still in an unmerged PR** — and do not
park it in `Blocked` either: nothing is stuck. Post the closure record, leave the
issue OPEN, and move the card to **`Ready`** — the agent-terminal state: delivered,
reviewable, awaiting external merges / human acceptance. **`Done` is human-only**
(the human closes + moves when the case is promotable/accepted), symmetric with
human-only `Approved` on the way in. `Blocked` means a REAL blocker only
(`Waiting on #N` — an open `question`/`bug` that stops work).

Worked example: [issue #19](https://github.com/EliteaAI/elitea-testing-public/issues/19)
(ELITEA-1737) — test merged, testids still in draft PRs EliteaUI#525/#526, therefore
NOT promotable. (Note: #19 was subsequently closed by a human while the drafts were
still open — the correction comment on the issue documents the deviation. The rule
stands: agents leave such issues OPEN; only a human may close early.)

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
