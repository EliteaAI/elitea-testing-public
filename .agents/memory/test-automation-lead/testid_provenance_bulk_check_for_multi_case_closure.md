---
name: Testid provenance — bulk check for a multi-case closure sweep
description: for a wave/campaign closing many cases at once, do ONE bulk provenance check across all new testids instead of N per-case checks; extract only diff '+' lines to avoid false positives from unchanged context.
type: feedback
---

## When this applies

`testid_presence_grep_technique.md` covers the per-testid grep shape for a
single case's promotability check. This entry is the scale-up: closing a
wave with dozens of cases sharing dozens of testid-adding commits, checked
once, 2026-08-04 (84 testids across 31 commits, wave-02-05-merged).

## Technique

1. Collect every testid string added by the wave's testid commits in ONE
   pass — iterate the commit SHAs, extract only lines starting with `+`
   (excluding `+++` diff headers) via a small Python script, regex-match
   `(?:data-testid|[a-zA-Z]*[Tt]estId)="([^"]+)"`, dedupe into one list.
2. Dump `origin/main` and `origin/automation/testids` src testid usages
   ONCE each (`git grep -ohE '(data-testid|[a-zA-Z]*[Tt]estId)="[^"]+"' <ref>
   -- src/`), not once per testid.
3. Check membership in-memory (`f'"{t}"' in dump`) for the whole list — this
   is the part that turns 84×2 git invocations into 2.
4. Attach the shared result table to every case's closure record, filtering
   to just the testids that case actually uses.

Cut what would have been ~40 minutes of redundant git operations (39 cases ×
per-case greps) down to under a minute.

## The trap this avoids

**Restrict to added (`+`) lines only.** An earlier pass in this session used
`git show <commit> -- src/` unfiltered, which includes unchanged context
lines too — and picked up 3 false "already on main" hits (`agent-save-button`,
`conversation-search-input`, `toast-message`) that were just pre-existing
testids appearing as context near a real change, not anything this wave
actually added or found on main. Filtering to `+`-prefixed lines (and
dropping `+++` file headers) before matching removed all three.
