---
name: Bulk TMS intake technique
description: How to pull the full onetest-ai-tm-Elitea backlog tree, dedup against the tracker, and bulk-file GitHub issues without hitting shell/xargs or gh-token pitfalls
type: reference
---

## Pulling the full backlog case tree

`onetest-ai-tm-Elitea`'s `tests/automated-full-regression-ui/` is nested
(module subdirs, some with a `build_with_ai/` sub-subdir). Don't walk it
directory-by-directory with `gh api contents/...` — use the recursive git
trees API in one call:

```bash
env -u GITHUB_TOKEN gh api "repos/EliteaAI/onetest-ai-tm-Elitea/git/trees/HEAD?recursive=true"
```

(Quote the URL — the bare `?` glob-expands in zsh/bash and the command
silently fails with "no matches found".) Filter the returned `tree[]` for
`path` starting with the target prefix and ending `.md`. This returned all
219 case files in one call at the time of the 2026-07-14 run, vs. dozens
of per-directory calls.

There's no bulk-content endpoint — fetch each file's base64 content with
one `gh api repos/.../contents/<path>` call per file. Parallelize with a
**python** driver (`concurrent.futures.ThreadPoolExecutor`, 5-10 workers),
not shell `xargs -P -I{} bash -c '...'` — the xargs approach failed
outright ("command line cannot be assembled") for ~139-219 items in this
run; don't burn time debugging xargs quoting, go straight to python.

Parse each file's YAML frontmatter (delimited by `---\n...\n---`) into a
dict per case: `id`, `title`, `module`, `status`, `execution_type`,
`automation_test_id`, `tags`, etc.

## Dedup

Pull the tracker's full issue list once, never `--search` (index lag
caused duplicate #17/#18 previously):

```bash
env -u GITHUB_TOKEN gh issue list --state all --limit 200 --json title,number
```

Extract `ELITEA-(\d+)` from every title into a set; any candidate case
whose `id` numeral is in that set is already carded — skip regardless of
its own status/automation fields.

## Classification order matters

Apply in this order per case (after the dedup-against-tracker check):
1. Already has a tracker issue → skip (dedup).
2. Strict already-automated rule (`execution_type: automated` AND
   `status: ready` AND non-empty `automation_test_id`) → skip.
3. Partial match on that rule (some but not all three signals present) →
   contradictory — do NOT file, do NOT skip silently, report it.
4. Otherwise → candidate to file.

**Contradictory metadata often clusters by module, not randomly.** In the
2026-07-14 run all 66 contradictory cases were the entire `artifacts`
module, sharing `status: draft` + `execution_type: automated` + empty
`automation_test_id` — almost certainly `execution_type: automated` means
something different in that module's authoring convention ("designated
for automation") than elsewhere. When a contradiction pattern spans an
entire module, flag it as ONE systemic note in the summary rather than
filing N separate `question` issues — cheaper for a human to triage and
correctly represents "one root cause," not N independent ambiguities.

## Title format nuance

The mission's canonical format includes a module bracket:
`[Automate][ELITEA-<id>][<module>] <title>`. Use the case's own YAML
`module:` field for the bracket, NOT its source directory name — they
diverge (e.g. files under `mcp/` carry `module: elitea-platform`, files
under `credentials/` carry `module: toolkits-credentials`). Some
pre-existing issues on the board were filed without the module bracket at
all (an earlier convention) — that's fine, the dedup key is just the
`ELITEA-<id>` substring so old and new formats coexist without collision.

## Bulk-filing pitfall: `returncode == 0` is not proof of success under concurrency

**Confirmed live on 2026-07-14**: a 5-way-concurrent `ThreadPoolExecutor`
batch of 138 `gh issue create` calls reported 138/138 "OK" by checking only
`proc.returncode == 0`. A follow-up cross-check against a fresh
`gh issue list` pull found **59 of those 138 had never actually landed** —
those calls returned exit code 0 with **empty stdout** (no issue URL),
silently miscounted as success. Root cause unconfirmed (suspected `gh`/
GitHub secondary rate-limiting under concurrent burst creation), but the
mitigation is proven:

- **Never trust `returncode == 0` alone for `gh issue create` in a batch.**
  Regex-match stdout against `^https://github\.com/.../issues/\d+$` before
  counting a call as successful.
- **Prefer sequential filing over high-concurrency parallel** for a burst
  of 100+ tracker writes — the repair run refiled the missing 59
  sequentially (no thread pool) with the stricter check and got 59/59
  clean on the first attempt, 0 retries.
- **Always do a final cross-check pass**: after "filing" N candidates,
  re-pull the full issue list and confirm every candidate ID is actually
  present. Don't rely on the filing loop's own self-reported tally —
  it's exactly the thing that was wrong here.
- If gaps are found after the fact, file a **second** tracking-only
  summary issue documenting the gap + repair rather than silently
  patching and pretending the first summary was accurate — the original
  summary's counts stay wrong on record otherwise.

## Bulk-filing pitfall: env var removal

To run `gh` as the keyring identity (never the shared `GITHUB_TOKEN`) from
a **python** subprocess (not a plain shell command), you must actually
delete the key from the env dict passed to `subprocess.run(env=...)`:

```python
clean_env = dict(os.environ)
clean_env.pop('GITHUB_TOKEN', None)   # correct
# clean_env['GITHUB_TOKEN'] = ''      # WRONG — gh may still treat this as "set"
```

Setting it to an empty string is not equivalent to unsetting it and risks
silently writing as the wrong identity. Verify identity with one manual
`gh issue create` test call before kicking off a large parallel batch, and
check the returned URL is on the expected repo/account.

## Summary/tracking issue + board Done

A single "intake sync" issue (not routed to the pipeline) documents the
run: source scanned, dedup count, already-automated count, contradictory
count + pattern, filed count + breakdown table, issue number range. File
it, let auto-add place it on the board, then move it straight to Done:

```bash
env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --limit 300 --format json  # find the item id for the new issue number
env -u GITHUB_TOKEN gh project item-edit --project-id <PVT_...> --id <PVTI_...> \
  --field-id <Status field id> --single-select-option-id <Done option id>
```

`item-edit` exits silently on success — always read back via a fresh
`item-list` filter to confirm the status actually landed, don't trust the
exit code alone.
