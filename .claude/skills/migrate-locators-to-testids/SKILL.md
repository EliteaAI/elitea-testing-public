---
name: migrate-locators-to-testids
description: The testid-migrator procedure — reconcile the locator ledger, swap page-object declarations to data-testids already deployed on DEV (phase A → PR to automation/factory), and add the next batch of testids to EliteaUI on automation/testids (phase B). Use only from the testid-migrator agent (started on request, by a person or another party); the factory never runs this.
allowed-tools:
  - Bash
  - Read
  - Edit
  - Grep
  - Glob
  - Skill
---

# Migrate locators to testids

The factory builds tests against DEV on the locator ladder and leaves a `suggested_testid=` on every
non-testid declaration (`.claude/rules/page-objects.md` § Locator Strategy). This skill turns those hints
into real testids — **without ever making a test depend on a testid DEV does not serve yet**, because
`LocatorDescriptor` has no fallback.

```
 factory merges test           phase B (week N)                 human            phase A (week N+k)
 role/label/css/xpath  ──▶  add testid on automation/testids ──▶ cherry-pick ──▶  swap to testid=, run on DEV,
 + suggested_testid         push · ledger: testid-proposed       → main → DEV     PR · ledger: migrated
 ledger: raw                                                     ledger: on-dev
```

All commands run from the repo root unless shown; `INV` below is
`cd automation && ../.venv/bin/python scripts/locator_inventory.py`.

## Ledger states

| State | Meaning | Who moves it |
|---|---|---|
| `raw` | non-testid declaration, no testid in EliteaUI yet | `sync-ledger` (new rows, revived rows) |
| `testid-proposed` | testid committed + pushed on `automation/testids` | you — `mark … testid-proposed --evidence <EliteaUI sha>` |
| `on-dev` | testid on EliteaUI `main` **and observed on DEV** | you — `mark … on-dev --evidence "<main sha> + DEV check <date>"` |
| `migrated` | declaration now `testid=` in the source | `sync-ledger` (automatically, after the swap) |
| `removed` | declaration no longer exists in the source | `sync-ledger` |

Legal `mark` moves: `raw→testid-proposed`, `testid-proposed→on-dev | raw`, `on-dev→migrated | testid-proposed`,
`removed→raw`. Anything else is refused by the script — don't hand-edit `ledger.json`.

## Step 0 — Preconditions (one Bash call)

```bash
cd <repo root> && git status --short && git fetch origin && git checkout automation/factory && git merge --ff-only origin/automation/factory
cd ../EliteaUI && git status --short && git fetch origin && git branch --show-current
```

- Both trees clean (untracked `.agents/automation/*` dirs are other people's work — leave them).
- Run `sync-base-branches` for **EliteaUI** (and `elitea_assistant` if any ledger row lives in a
  Support-Assistant page object) — merge `origin/main` into `automation/testids`, testid-loss guard, push.
  Never rebase or force-push.
- Refresh DEV auth: `cd automation && ../.venv/bin/python scripts/dev_storage_state.py` (prints path +
  cookie count only).

## Step 1 — Reconcile and plan

```bash
cd automation
../.venv/bin/python scripts/locator_inventory.py scan            # paste: the BEFORE metric
../.venv/bin/python scripts/locator_inventory.py sync-ledger     # registers new raw rows, closes removed/migrated
../.venv/bin/python scripts/locator_inventory.py check-ui-ref --ui-repo ../../EliteaUI --ref origin/main
../.venv/bin/python scripts/locator_inventory.py queue --limit 25
```

`queue` returns four lists: `phase_a_swap` (state `on-dev`), `phase_b_add_testid` (`raw` with a hint),
`awaiting_deploy` (`testid-proposed`) and `needs_hint` (legacy `raw` rows with no `suggested_testid`).

### Promote `testid-proposed → on-dev` (the deployment gate)

`check-ui-ref` only proves the testid is in EliteaUI `main` source. **Main is not DEV.** For every
`on_ref: true` row, confirm DEV serves it before marking:

- Open the page the declaration lives on with the **`playwright-dev`** MCP server (storage state from
  Step 0) and `browser_evaluate` `() => document.querySelectorAll('[data-testid="<id>"]').length`
  (for a `-{}` template, `[data-testid^="<prefix>-"]`). Count ≥ 1 on the right element ⇒ deployed.
- Then `INV mark <id> on-dev --evidence "main <sha>; DEV DOM check <yyyy-mm-dd>" --ref origin/main`.
- `on_ref: true` but absent on DEV ⇒ leave it `testid-proposed` (deploy pending) and report it.
- `on_ref: false` for > 4 weeks ⇒ report it as "awaiting human cherry-pick" with the EliteaUI SHA.

Rows promoted here join this run's phase A.

### Name the `needs_hint` rows

Legacy declarations (pre-ladder `locator=` / `fallback=` / CSS without a hint) can't be migrated
mechanically. For each, pick the `{section}-{element}-{type}` testid name (call-site section; dynamic ones
end in `-{}`) and **rewrite the declaration onto the ladder with `suggested_testid=`** — same element,
same rung behaviour, no `locator=`/`fallback=`. These rewrites ride the phase-A PR and must pass the same
DEV run. Cap at 10 per run; they are the riskiest edits you make.

## Step 2 — Phase A: swap to deployed testids (this repo only)

Branch: `locators/<yyyy-mm-dd>` cut from `automation/factory` (run date, e.g. `locators/2026-10-06`).

For each `phase_a_swap` row:

1. **Edit only the declaration** in `automation/pages/…`: replace the rung with `testid="<suggested_testid>"`
   and drop `suggested_testid=` / `name=` / `exact=`. Keep `description=`. `ScopedLocator(role=…, …)` becomes
   `ScopedLocator(testid=…)`; a dynamic `name="{}"` template becomes `testid="<prefix>-{}"`.
2. **Find every test that exercises it:**
   `grep -rn "<attr_name>" automation/pages automation/tests` → the methods using the field → the specs
   calling those methods. Record the node ids.
3. **Run them against DEV** (headless, cwd `automation/`, Bash timeout 600000):
   `HEADLESS=true ../.venv/bin/pytest <node ids> -v -p no:cacheprovider`
   - Green ⇒ keep the swap.
   - Red on the swapped locator (strict-mode duplicate, wrong element, not visible) ⇒ **revert that one
     declaration**, `INV mark <id> testid-proposed --evidence "<failure, node id>"` and report it — usually a
     duplicate testid that needs a scope or a rename in phase B.
   - Red for an unrelated reason ⇒ re-run once against `automation/factory` without your change. Same red ⇒
     pre-existing failure: keep the swap only if the failing step is upstream of the swapped locator, and
     report the failure. Otherwise revert and report. Never edit the spec to make it pass.
4. After all swaps: `INV sync-ledger` (moves swapped rows to `migrated`) and `INV scan` (paste: AFTER metric).

Self-check on the diff, paste the output:

```bash
git diff automation/factory --stat                                   # only automation/pages/** + ledger.json
git diff automation/factory -- automation/pages | grep -nE '^\+.*(locator=|fallback=|nth\(|:nth-child|\.first|\.last)'   # expect 0 hits
cd automation && ../.venv/bin/ruff check pages && ../.venv/bin/pytest tests/unit -q
```

Commit (`refactor(locators): migrate <n> locators to deployed testids (<yyyy-mm-dd>)`), push, open the PR to
**`automation/factory`** with the Migration Report as body. Merge policy is the normal one: a fresh-session
`qa-engineer` review (§ Review) + green DEV run; you do not self-merge.

## Step 3 — Phase B: add the next batch of testids (EliteaUI only)

Start the local UI (`start-ui-localhost` — dev server on `automation/testids`, `localhost:5173`). Use the
plain **`playwright`** MCP server here (no storage state; `VITE_DEV_TOKEN` auth).

For up to `--limit` `phase_b_add_testid` rows, grouped by page:

1. Open the page, snapshot, identify the element the declaration resolves to (read the declaration's rung —
   role+name / label / css / xpath — and match it in the DOM).
2. Run **`add-data-testid`** with the row's `suggested_testid` as the name. Its full discipline applies:
   uniqueness grep first, call-site naming, `testId` / `<part>TestId` props on shared components, state via
   `data-*` attributes (#581), conditional-pair rule (#277), **zero functional impact** (§ Hard gate, Step 5.5).
   Edit `src/` only.
3. Verify in the live DOM that `[data-testid="<id>"]` resolves to exactly the element the old rung found
   (count 1, or for templates one per item).
4. Third-party internals that cannot take a testid (ReactFlow nodes, CodeMirror/Monaco lines, mermaid /
   react-markdown output) ⇒ do **not** force one. Close the row in phase A of this run instead: rewrite the
   declaration as a scoped `css=` rung under a testid parent with the hint removed and the reason in
   `description=` (#579). Report it.

Commit once per page/area on `automation/testids`:
`test: [testid-migrator <yyyy-mm-dd>] add data-testids for <area>` (body lists the testids), then
`git merge origin/main && git push origin automation/testids` (plain push). For every row added:
`INV mark <id> testid-proposed --evidence "EliteaAI/EliteaUI@<sha>"`.

Commit the ledger change on the phase-A branch (or, if phase A had nothing, on its own
`locators/<yyyy-mm-dd>` branch + PR — the ledger is the record).

Phase B touches no test code. It cannot break a test: nothing references a `testid-proposed` testid yet.

## Review (what the reviewer checks — fresh `qa-engineer` session, static)

Dispatch line: *"Review a testid-migrator batch per `.claude/skills/migrate-locators-to-testids/SKILL.md`
§ Review. Static — no execution."*

Phase A PR:
- Diff touches only `automation/pages/**` and `.agents/locator-migration/ledger.json`.
- Every swapped testid is a ledger row that was `on-dev` (or promoted this run with DEV-check evidence) —
  re-run `check-ui-ref` after `git fetch origin` in `../EliteaUI` and paste it. **The fetch is part of the
  check** — a presence verdict from a stale clone is not a verdict (it once produced "0 of 12 on main" when
  the truth was 5/12, added by the UI team in parallel).
- **Reading a presence check honestly — the wiring forms a grep does and doesn't see.** `check-ui-ref`
  matches the testid as a bare substring, which is deliberate: a testid can be wired as a direct attribute
  (`data-testid="agent-name-input"`), an object literal (`'data-testid': '…'`, `testId: '…'`), or through a
  prop (`buttonTestId="agent-name-input"` → `data-testid={buttonTestId}`), and only substring matching finds
  all three. Two consequences:
  - **False positives are possible** — comments (`// TODO: add agent-name-input testid`), prose, variable
    names, and prefix collisions (`agent-form` inside `agent-form-save-button`). Read the hits rather than
    counting them; real wiring matches `grep -iE '(data-testid|testid[[:space:]]*[:=])'` — both the `-i`
    (`TestId` ≠ `testid`) and the `[:=]` (the colon form has no `=`) are load-bearing.
  - **Runtime-composed testids are invisible** — `` data-testid={`${PREFIX}-suffix`} `` cannot be grepped at
    all. When the component file differs between refs, diff the file
    (`git diff origin/main origin/automation/testids -- <path>`) instead of trusting any grep.
  A wrong presence verdict here promotes a row to `on-dev` that DEV does not serve, and phase A then ships a
  locator that never matches — which is why the DEV DOM check, not the grep, is the gate.
- Each swap keeps the method's behaviour: same element, same scoping; no new waits, no assertion changes.
- The Run section lists the node ids per swapped locator with a green DEV result.
- `needs_hint` rewrites stay on the ladder with a hint; no `locator=`/`fallback=`/positional handles.

Phase B (EliteaUI commits on `automation/testids`) — the testid canon, paste each command + output:
- Step 5.5 greps (`add-data-testid`): new hooks, new DOM nodes, real deletions — 0 hits or a declared exception.
- #581: no `data-testid={cond ? … : …}` flipping on the same live element; no state in the testid.
- #277: conditional pairs name only the used branch, or both with both referenced.
- Shared components (`src/components/`, `src/[fsd]/shared/`) carry no feature-scoped literals; props are
  `testId` / `<part>TestId`, never `dataTestId`.
- Scope: every added testid is a ledger row (no blanket adds — `ui-testid-coverage` is a report, not a target).

## Report (end of every run — PR body and final message)

```markdown
## Testid migration — <yyyy-mm-dd>

**Locator debt:** <before>% → <after>%  (declared <n>, non-testid <a> → <b>; unmanaged handles <u>)

| Phase | Rows | Result |
|---|---|---|
| Promote to on-dev | <n> | <ids> — DEV-checked <date> |
| A — swapped | <n> | PR #<N> · DEV run: <node ids> green |
| A — reverted | <n> | <id> — <reason> (back to testid-proposed) |
| Hints named | <n> | <ids> |
| B — testids added | <n> | EliteaAI/EliteaUI@<sha> (+ …) on `automation/testids` — **human cherry-picks to `main`** |
| B — closed as third-party | <n> | <ids> — <library> |
| Awaiting cherry-pick / deploy | <n> | <ids, oldest first, with age> |

**Still open:** <follow-ups, or "none">
```

Cross-repo references are plain text `EliteaAI/EliteaUI@<sha>` / `EliteaAI/EliteaUI#<n>` — never in backticks,
never bare.

## Do not

- Swap a declaration whose testid you have not seen on DEV.
- Touch specs, fixtures, conftest, or anything that changes what a test asserts.
- Add a testid that isn't a ledger row, or rename an existing UI-team testid.
- Open a PR to EliteaUI `main`; rebase or force-push `automation/testids`; create a worktree.
- Hand-edit `ledger.json` — every move goes through `locator_inventory.py` so history stays honest.
