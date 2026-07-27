---
name: TMS case filenames embed the ELITEA-id — cheap dedup delta without content fetches
description: tests/automated-full-regression-ui/<module>/ELITEA-<id>_<slug>.md filenames always start with the case id, so intake dedup-delta can be computed from the recursive git-trees path list alone, deferring content fetches to only the actual new candidates
type: feedback
---

## What happened

During the 2026-07-23 cardless intake run, confirmed across all 692 files
under `tests/automated-full-regression-ui/` in `onetest-ai-tm-Elitea`:
every filename matches `ELITEA-(\d+)_<slug>.md` with the id as the first
token — zero exceptions (checked via regex over the full recursive
git-trees path list).

`bulk_tms_intake_technique.md` documents fetching every file's content
(base64, one `gh api contents/<path>` call per file, parallelized via
`ThreadPoolExecutor`) to parse YAML frontmatter and get the `id`. That's
necessary to know `title`/`module`/`status` etc., but it is NOT necessary
just to compute the dedup delta.

## Better order of operations

1. Pull the recursive tree once:
   `env -u GITHUB_TOKEN gh api "repos/EliteaAI/onetest-ai-tm-Elitea/git/trees/HEAD?recursive=true"`
   (quote the URL — bare `?` glob-expands in zsh/bash), filter `path`
   under the target prefix ending `.md`.
2. Extract `ELITEA-(\d+)` from each **filename** (last path segment) via
   regex — no API call per file.
3. Pull the tracker's full issue list once (`gh issue list --state all
   --limit 1000 --json title,number`), extract carded ids the same way
   from titles.
4. Delta = filenames-ids minus carded-ids. Only fetch **content** for
   files in the delta (to get `title`/`module`/full metadata for the
   issue body) — not the whole tree.

On the 2026-07-23 run this meant fetching 256 files instead of all 692 —
proportional to how large the delta is relative to the full tree, this
scales the read cost down significantly for incremental runs where the
already-carded set is large.

## Caveat

This assumes the filename-embeds-id convention holds — verify with a
quick regex sweep over the full path list first (as above) before relying
on it; if any file breaks the pattern, fall back to fetching that file's
content specifically rather than assuming its id.
