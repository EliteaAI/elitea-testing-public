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

**Incremental runs (source has grown since last pull):** diff the current
path list against the previous run's saved list — anything new needs
fetching, nothing else does. Confirmed on 2026-07-15 (run 7): source grew
219→436 files (217 new, 0 removed) in one run; a plain `diff` on two saved
path-list files instantly isolates the delta, no need to re-fetch or
re-classify the unchanged 219.

**Hash-cache gotcha:** if the fetch script derives its per-file cache
filename via `echo "$path" | shasum`, that hash includes a **trailing
newline byte** (`echo` appends `\n` by default). Any later cross-language
re-derivation of "the same" hash — e.g. Python's
`hashlib.sha1(path.encode())` — will NOT match unless it also hashes
`path + '\n'`. This caused a real false "0 files found" failure on
2026-07-15 even though the original fetch had succeeded and cached
everything correctly; the fetch script itself was fine, only the
lookup-by-recomputed-hash step was wrong. Either hash `(path + '\n')` on
the Python side to match, or switch the shell script to `echo -n` — but
only do the latter before any cache entries exist under the old scheme,
since switching mid-stream desyncs previously-cached files.

## Dedup

Pull the tracker's full issue list once, never `--search` (index lag
caused duplicate #17/#18 previously):

```bash
env -u GITHUB_TOKEN gh issue list --state all --limit 200 --json title,number
```

Extract `ELITEA-(\d+)` from every title into a set; any candidate case
whose `id` numeral is in that set is already carded — skip regardless of
its own status/automation fields.

## Classification — the real judgment is dedup, not the case's own status fields

**Corrected policy, confirmed by the human on 2026-07-14 (run 4), supersedes
the earlier "strict already-automated rule" approach used in run 1:**
`execution_type: automated` inside
`tests/automated-full-regression-ui/` does NOT mean the case is actually
automated. Every case in that folder is *planned* for automation;
`execution_type`/`status`/`automation_test_id` can be stale or
inconsistent data (a tagging artifact), not a reliable completion signal.
**The sole judgment for whether to file a card is: does a board task
already exist for this case ID?** Nothing else.

Correct classification order per case:
1. Already has a tracker issue (`ELITEA-<id>` substring match against the
   full issue-title pull) → skip (dedup). This is the ONLY exclusion rule.
2. Otherwise → file it, regardless of what its own status/execution_type/
   automation_test_id fields say.

**Run-1 mistake (corrected in run 4):** treated a strict AND-of-three
rule (`execution_type: automated` AND `status: ready` AND non-empty
`automation_test_id`) as grounds to skip, and treated any *partial* match
of that rule as "contradictory metadata" to park unfiled pending human
review. That was over-cautious and wrong per the clarified policy — 66
cases (the entire `artifacts` module, all sharing `status: draft` +
`execution_type: automated` + empty `automation_test_id`) got parked in
run 1 and had to be filed in a dedicated run-4 correction pass once none
of them turned out to have an existing board task. **Contradictory-looking
metadata does not, by itself, block filing — only an existing tracker
issue does.** If a case's own `automation_test_id` looks genuinely
populated with a real test reference (e.g. a `tests.ui....` dotted path
or `file.py::Class::method` pointer), that's a *strong hint* it may
already be covered — but even then, verify against the tracker/repo
before treating it as a skip signal; don't derive the skip decision from
the field alone.

**Still worth noting when a "looks weird" pattern clusters by module** — a
whole-module `execution_type`/`status` mismatch, like the `artifacts`
case, is worth one line in the summary issue as an FYI on data hygiene,
but it is NOT a reason to withhold filing.

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

## Bulk-write pitfall: 120s foreground timeout SIGKILLs mid-loop with an EMPTY log

**Confirmed 2026-08-04**, closing out a 39-case wave: a Python loop issuing
~78 sequential `gh` write calls (per-case closure comment + board
`item-edit`) inside one Bash tool call hit the 120s foreground timeout and
was killed — but stdout had been redirected to a log file and **never
flushed before the SIGKILL, so the log came back completely empty**, with
no way to tell from it how far the loop got. Most of the calls had in fact
already landed against the real API by the time it died.

- **Don't trust an empty log as "nothing happened."** After any such
  timeout, re-verify actual state for every target (`gh issue view --json
  comments`, `gh project item-list`) before assuming failure — a naive
  blind retry-of-everything would have double-posted most of the closure
  comments here (found: 38/39 comments had landed, 38/39 board moves had
  landed, only the very last case in dict-iteration-order was short).
- **For >~15 sequential `gh` write calls**, either run the loop with
  `run_in_background: true` (no 120s cap) or `print(..., flush=True)`
  after each call so a kill still leaves a readable partial log.
- Same underlying family as the `returncode==0`-is-not-proof-of-success and
  `item-edit`-exits-silently lessons below — add "the whole process can die
  before its own log hits disk" as a third failure mode in this class.

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
