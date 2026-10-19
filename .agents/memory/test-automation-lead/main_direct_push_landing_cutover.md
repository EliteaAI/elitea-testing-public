---
name: Base is main, the lead lands batches by direct push (cut-over 2026-10-16)
description: Since 2026-10-16 every gated batch lands as ONE squash commit the lead pushes straight to main — no PR, no human merge; ledger sync, records and memory ride IN that commit (trunk, pre-squash); only TMS back-write + closure record follow
type: project
---

## What changed

Operator rulings 2026-10-16: the factory works against **`main`**, not
`automation/factory`, and **the lead lands each gated batch by pushing it straight
to `main`** — no PR, no human merge (a brief interim "agents PR, humans merge"
policy the same day is superseded too). `automation/factory` and
`automation/base` are frozen history — never branch from, PR into or sync them.
Any memory, skill example or daily log that says "merge into
`automation/factory`/`automation/base`", "open a PR into `main`, a human merges",
"hand-off record" or "merge record / postmerge loop" predates this and is
superseded.

## Your moves now

- Cut the batch trunk from a freshly fetched `origin/main`; no session-start sync.
- **One ticket = one batch = one session = ONE squash commit on `main`.** Batches:
  `base: "main"`, `prUnit: "trunk"`. Units branch from and merge back into
  `tests/batch-<slug>`; every unit reviewer-APPROVED, then your 3× gate on the trunk,
  then you land it (`.agents/role-overrides.md` § Orchestrator slot — *Landing a
  batch*): `git checkout main && git merge --ff-only origin/main`,
  `git merge --squash tests/batch-<slug>`, `git commit -F <msg>`,
  `env -u GITHUB_TOKEN git push origin main`. Subject
  `test: batch <slug> — <N> cases (<IDs>)`, body one line per case + gate + locator
  delta + defects + `Refs #<card>` (never `Closes` — it would close the card when the
  commit reaches `main`). Also push the trunk for history.
- Push rejected (`main` moved — the index bot, another landing) → `git reset --hard
  origin/main` on local `main` ONLY, merge `origin/main` into the trunk, re-gate if
  the change touches the batch's files, land again. **Never `--force`, never rebase.**
- **The one commit is complete (ruling 2026-10-19).** After the gate, BEFORE the
  squash, commit on the trunk: `scan` + `sync-ledger` (`ledger.json`), `report.json`
  with the gate verdict + `gate-runs.jsonl`, `work-scope.mjs close` (`cost.json`,
  batch report), your memory / daily log. `.agents/**` only — anything under
  `automation/` after the gate means re-gate. No `chore(ledger)` / memory commit on
  `main` afterwards — the control loop FAILs a batch that arrives as >1 commit.
- Same session, right after landing: TMS back-write for every case
  (`automation_pr` = `https://github.com/EliteaAI/elitea-testing-public/commit/<sha>`),
  rebuild `index.json` (TMS repo), one **closure record** per card, card → `Ready`,
  issue OPEN. `Done` is human-only.
- A previous iteration pushed but died before the back-write / closure record →
  finish them from the landed commit; never re-land, never add a commit to `main`.
- A case needing ANOTHER batch that has not landed → park `Blocked`,
  `Waiting on #<card>`; never stack on its trunk.

**Why:** the review + 3× DEV gate already run inside the pipeline; a PR that only
waited for a human click added latency without adding a check. The human's
acceptance moved to `Done`, and the `control` loop audits every landed commit.

**How to apply:** treat the steps above as canon over any older note; the
authoritative text is `.agents/workflow.md` (§ Branching, § After landing,
§ Closure record) and `.agents/role-overrides.md` § Orchestrator slot.
