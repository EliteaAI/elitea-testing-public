---
name: build_index regression must be reverted, not carried
description: NEVER call build_index for a routine back-write — duplicate TMS ids make it last-write-wins destructive; always surgical-edit index.json by path
type: feedback
---

## Recurrence #2 (issue #1395, help-center-remaining batch, 2026-08-14) — confirmed the destructive mechanism

Called `mcp__onetest-tms__build_index` after a routine 10-case back-write
(the yaml's "index.json is NOT auto-rebuilt... rebuild it (build_index MCP
verb...)" caveat reads as a routine step when it's in front of you without
this entry's caveat also in view). The diff looked plausible (206 lines,
92+/114-) so it nearly shipped. Comparing before/after by **`path`** (not
`id` — a naive `{c['id']: c for c in cases}` dict comprehension SILENTLY
COLLAPSES collisions and hides the damage) found the rebuild had:
- **Regressed 20 unrelated `skills` cases** (ELITEA-2595 through 2614) from
  `automated`/`ready` with a full `automation_test_id` back to
  `manual`/`[]` — each of these ids ALSO collides with an unrelated case in
  a different module (`onetest_case_id_can_collide_across_modules.md`:
  confirmed systemic, 150+ colliding ids), and the indexer's last-write-wins
  behavior over duplicate ids picked the WRONG file's data for all 20.
- **Silently stripped the closing `]` off two parametrized
  `automation_test_id` strings** (ELITEA-1994/1995,
  `...[ELITEA-1994-description` with no closing bracket) — a distinct
  `_index.py` parsing bug, not a collision artifact.

Fix: `git checkout <pre-rebuild-sha> -- index.json`, then re-applied ONLY
the intended 10-case update by loading the JSON, matching each entry by its
**unique `path` field**, mutating `status`/`execution_type`/
`automation_test_id` in place, and re-dumping (`indent=2,
ensure_ascii=False`, trailing newline). Diff shrank to exactly the 10
touched cases, 0 collateral changes.

## Rule going forward — supersedes "just audit the diff"

**Never call `build_index` for a routine back-write, full stop — this TMS's
id collisions make it actively destructive, not just noisy.** The tool
sounds authoritative ("Rebuild index.json from tests/ front-matter") and its
own diff can look plausible at a glance; only a **by-`path`** before/after
comparison (never by `id` — see above) reveals the damage, and that check is
easy to skip when the diff "looks like" routine maintenance. The safe
default for a routine back-write is always the surgical edit —
`tms_backwrite_discipline.md` rule 4 — load the JSON, find each entry by its
exact `path`, mutate the 3 fields, re-dump. Reserve an actual `build_index`
call for a genuinely NEW case that has never been indexed at all, and even
then audit the full diff (both this entry's `git diff | grep '^-'` check
AND a by-`path` comparison) before committing.

## What happened (ELITEA-1907, issue #85, 2026-07-16)

While landing stray uncommitted files before switching branches for the TMS
back-write, found `onetest-ai-tm-Elitea/index.json` had been regenerated
mid-session (some earlier subagent call — analyst or reviewer — invoked
`build_index` via the onetest-tms MCP server). The diff was large (~9200
lines) and mostly additive (catching the index up to on-disk cases it had
never indexed). But `git diff index.json | grep '^-'` showed 33 removal
lines resolving to 4 fully-deleted case entries: ELITEA-1735 through
ELITEA-1738 (skills module). Checked `find . -iname "*1735_interact*"` etc.
— **all 4 files still exist on disk**. The rebuild didn't move or rename
them; it just dropped them from the index outright. Reverted `index.json`
entirely rather than committing it, then proceeded with only the intended
case-file back-write.

## Why this is a DIFFERENT lesson from the existing stale-index guidance

`tms_backwrite_scope_git_add_to_case_file.md` already covers **pre-existing,
inert drift**: an `index.json` that's been locally stale for days, nobody
touched it this session, out of scope to fix — the rule there is "targeted
`git add`, leave it alone." This is a different failure shape: a **fresh,
active regression** introduced by tooling *during this session*, sitting in
the working tree as an uncommitted diff I was about to land alongside a
legitimate memory-file commit. "Leave stale things alone" and "don't ship a
regression that happens to be sitting in the tree" are both correct, but
they're not the same check — a diff that LOOKS like routine index
maintenance (large, mostly-additive, matches the commit-history precedent of
similar "chore: back-write" commits) still needs the removal lines audited
before it goes anywhere near a push.

## Rule going forward

Before committing ANY `index.json` diff in the TMS sibling clone, whether it
arrived from your own `build_index` call or was found already sitting in the
working tree from a concurrent subagent session:

```bash
git diff index.json | grep '^-' | grep -oP '"id": "\K[^"]+' | sort -u
# for each removed id, confirm the source file still exists:
find . -iname "*<id>_*"
```

If any removed id still resolves to a real file on disk, the diff is a
**regression, not a maintenance update** — `git checkout -- index.json` and
do not carry it forward, regardless of how large or plausible the additive
portion looks. Only commit an index rebuild once every removal has been
independently confirmed to correspond to a genuinely deleted/renamed source
file.
