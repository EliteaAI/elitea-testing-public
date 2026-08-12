---
name: build_index regression must be reverted, not carried
description: a fresh build_index-generated index.json diff can silently drop still-existing cases; verify every "-" removal resolves to a real file before ever committing it, and revert rather than carry an unverified rebuild
type: feedback
---

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
