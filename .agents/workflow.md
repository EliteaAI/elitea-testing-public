# How This Team Works

_Seeded 2026-07-10 from operator way-of-work brief + PR sampling (merged PRs #10–15
on `main`). **Revised 2026-07-13: the EliteaUI fork was retired** — `automation/testids`
now lives on `EliteaAI/EliteaUI` directly. **Revised 2026-07-16 (current): agents no
longer open per-case draft PRs to EliteaUI `main`.** Testids terminate on
`automation/testids` (committed + pushed); a **human** cherry-picks them to `main`.
This is a suspended-not-deleted policy — restore notes in
`.agents/_reverted/RESTORE-testid-draft-pr-flow.md`. Refresh when the process shifts._

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
| EliteaAI/EliteaUI | `automation/testids` (integration) | **never PR it into `main`, and (since 2026-07-16) never open per-case `main` PRs at all.** Testid commits are born ON it, committed + pushed, and stop there. A human cherry-picks them to `main`. |

- There is **no CI on `automation/base`** — the green local run before PR is the
  only verification. You are the CI.
- There is **no `pending_testid` marker**. Do not invent one.
- Test work branches: `tests/<case-id>-<slug>`, cut from **`automation/base`**.
- Testid work: committed **straight onto `automation/testids`** and pushed — no
  per-case branch, no PR (see § Testid flow below). *(Suspended 2026-07-16: the
  old `testids/<case-id>-<slug>` review branch + draft PR to `main` is on hold —
  `.agents/_reverted/`.)*
- Commit style (sampled from history): conventional-ish — `test: (5199) Add guardrails
  live-reload UI tests`, `refactor: use default gpt-5.2 model`, `docs(afs): amend selectors…`.

### Testid flow — commit + push `automation/testids`, then stop

**Current policy (2026-07-16): a testid is committed once, straight onto
`automation/testids`, and pushed. That is the agent's terminal step.** The dev
server runs that branch, so the testid is live under HMR the moment it exists and
every other agent sees it. Promotion to EliteaUI `main` is a **human** cherry-pick
from `automation/testids`, done out of band — **agents do not open EliteaUI `main`
PRs.**

```
    ══●══════●═══════════════════════════▶  automation/testids   (agent stops here)
      ▲   testid commits BORN + pushed        ← dev server :5173 runs THIS
      ╰── main merged in, often                  agents see EVERY testid
                                              ┄┄▶ human cherry-picks → main, later
```

```bash
cd ../EliteaUI                            # dev server is live on automation/testids
git fetch origin

# edit JSX under src/ ONLY, commit ON automation/testids (HMR shows it instantly),
# keep it in sync with main, then push the integration branch (plain FF — NEVER --force)
git add src/ && git commit -m "test: [EL-1737] add data-testid for …"
git merge origin/main && git push origin automation/testids
```
(Full procedure: `add-data-testid` skill.)

> **Suspended, not deleted.** The prior flow — cherry-pick each case onto a
> `testids/<case>-<slug>` branch cut from fresh `main` and open a **draft PR to
> `main`** — is on hold as of 2026-07-16 by operator request. To restore it see
> `.agents/_reverted/RESTORE-testid-draft-pr-flow.md`. Until then, **the human owns
> the `automation/testids` → `main` promotion**; agents never create that PR.

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
   under `src/`), commits **and pushes `automation/testids`** — and stops there
   (no `main` PR; a human promotes). Vite HMR reloads — no restart.
   Naming `{section}-{element}-{type}`; verify uniqueness first.
4. **`page-object-generator` skill** — emit **testid-only** descriptors:
   `LocatorDescriptor(testid="agent-form-save-button")`. Never populate `fallback`.
5. **Write the test**, run it green against localhost, PR into `automation/base`.

Nothing in this loop waits on external review. That is the point.

## Promotion — HUMAN-TRIGGERED ONLY

Testid promotion to EliteaUI `main` is a **human** step (2026-07-16): the human
cherry-picks from `automation/testids` when they choose. Agents don't gate on it and
don't open that PR. What the lead performs — **only on explicit request**, never
autonomously — is the **test** batch promotion (`promote-automation-batch` skill):

1. Confirm the testids the batch depends on are **present on `EliteaAI/EliteaUI` `main`
   and deployed** to the target env (a human will have promoted them from
   `automation/testids`). Tests cannot cross into `main` ahead of their testids.
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
(#35/#36/#37 shipped false rows by copying; the #19 rework shipped a false row from a
STALE clone — claimed 0/12 on main, truth was 5/12, added by the UI team's own
EL-5400). The verification block, verbatim — **the fetch is part of the check**, and
the output gets PASTED into the record:

```bash
cd ../EliteaUI && git fetch origin      # fresh ground truth — NON-OPTIONAL
for t in <every testid the case's diff uses>; do
  printf "%-32s main:%-3s testids:%s\n" "$t" \
    "$(git grep -q "data-testid=\"$t\"" origin/main -- src/ && echo YES || echo no)" \
    "$(git grep -q "data-testid=\"$t\"" origin/automation/testids -- src/ && echo YES || echo no)"
done
```

The UI team also adds testids in parallel (EL-5400, EL-5634, …). Only testids present
on **main** make a case promotable — and, since 2026-07-16, getting them there is a
**human** cherry-pick from `automation/testids`, not an agent PR. So the row reports
ground truth (on `automation/testids` ✓, on `main` yet?) and names the human as owner
of the gap:

```markdown
🔗 **Closure record — <CASE-ID>**

| Artifact | Where | State |
|---|---|---|
| Test | #<N> — `tests/<case>-<slug>` → `automation/base` | ✅ merged (`<sha>`) |
| Testids | `EliteaAI/EliteaUI` @ `automation/testids` | ✅ pushed — dev server serves them; **human promotes to `main`** |
| AFS | `test-specs/<feature>/l<pri>_<slug>_<CASE-ID>.md` | on `automation/base` |
| Defects filed | #<X>, #<Y> — or "none" | |

**Status:** merged to `automation/base` · testids on `automation/testids` · ⚠️ NOT yet on `main` (awaiting human cherry-pick) → not deployable-env-promotable yet.

> **Cross-repo links** (whenever you reference an `EliteaAI/EliteaUI` issue/PR):
> write `EliteaAI/EliteaUI#<M>` as PLAIN TEXT — never inside backticks, never bare
> `#<M>`. Bare `#<M>` links to THIS repo's #M (wrong), and GitHub never auto-links
> inside code spans. The `owner/repo#N` form renders as a clickable cross-repo link
> AND leaves a "mentioned in…" backlink on the EliteaUI side. Same-repo references
> (the test PR) stay bare `#<N>`.
**Unblocks when:** a human cherry-picks the testids `automation/testids` → `main`, and they deploy to DEV. **Owner:** human.
**Still open:** <follow-ups, or "none">
```

**Why the promotability row is load-bearing here.** A case's testids can sit on
`automation/testids` (pushed, serving the dev server) while `main` doesn't have them
yet — because promotion to `main` is now a **human** cherry-pick, done when they
choose. Such a test is **green on localhost and red on any deployed env** —
`automation/testids` has the testids, DEV does not. So *"merged" ≠ "done"*, and the
record must say which, naming the human as owner of the promotion. `promote-automation-batch`
Stage 1 checks exactly this before a test batch crosses to `main`.

**Do not close an issue whose testids aren't yet on `main`** — and do not
park it in `Blocked` either: nothing is stuck. Post the closure record, leave the
issue OPEN, and move the card to **`Ready`** — the agent-terminal state: delivered,
reviewable, awaiting the human's testid promotion / acceptance. **`Done` is human-only**
(the human closes + moves when the case is promotable/accepted), symmetric with
human-only `Approved` on the way in. `Blocked` means a REAL blocker only
(`Waiting on #N` — an open `question`/`bug` that stops work).

Worked example: [issue #19](https://github.com/EliteaAI/elitea-testing-public/issues/19)
(ELITEA-1737) — test merged, testids on `automation/testids` but not yet cherry-picked
to `main`, therefore NOT promotable. (Historical note: under the prior flow #19's
testids sat in draft PRs EliteaUI#525/#526; a human closed #19 while those were open.
The rule stands: agents leave such issues OPEN; only a human may close early.)

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
