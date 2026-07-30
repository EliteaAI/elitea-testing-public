---
name: TMS intake technique
description: Bulk cardless intake — one recursive tree call, filename-derived dedup before any content fetch, sequential filing with URL-matched success, and the unenforced max_new_cards cap
type: reference
---

## Order of operations

1. **One recursive tree call, quoted URL** (a bare `?` glob-expands in zsh/bash and
   fails with "no matches found"):
   `env -u GITHUB_TOKEN gh api "repos/EliteaAI/onetest-ai-tm-Elitea/git/trees/HEAD?recursive=true"`
   → filter `tree[].path` under `tests/automated-full-regression-ui/` ending `.md`.
2. **Derive the dedup delta from FILENAMES — no per-file content fetch.** Every file
   matches `ELITEA-(\d+)_<slug>.md` with the id first (verified zero exceptions
   across all 692 files, 2026-07-23). Regex the last path segment. Verify the
   convention with a sweep before relying on it; fall back to a content fetch only
   for files that break it.
3. **One tracker pull**, `gh issue list --state all --limit 1000 --json title,number`
   → extract carded `ELITEA-(\d+)` from titles.
4. **Fetch content ONLY for the delta** (base64, one `gh api contents/<path>` per
   file, `ThreadPoolExecutor` 5–10 workers — **not** shell `xargs -P`, which fails
   outright with "command line cannot be assembled" at this scale). 2026-07-23: 256
   fetches instead of 692.

## Filing

- **Sequential, not high-concurrency.** A 5-way concurrent burst of 138
  `gh issue create` calls self-reported 138/138 OK; 59 had never landed — exit 0
  with **empty stdout**. Regex stdout against
  `^https://github\.com/.../issues/\d+$` before counting success; refiling the 59
  sequentially with that check gave 59/59 first try.
- **Always cross-check after filing** by re-pulling the full issue list; never trust
  the loop's own tally. If gaps surface later, file a *second* tracking issue rather
  than silently patching — the first summary's counts stay wrong on record.
- **Unset, don't blank, the token in Python subprocesses:**
  `clean_env.pop('GITHUB_TOKEN', None)` — setting it to `''` may still read as set.
  Smoke-test identity with one manual create before a large batch.
- **Title bracket uses the case's YAML `module:` field, not its directory** — they
  diverge (`mcp/` files carry `module: elitea-platform`). Older cards filed without
  the module bracket coexist fine; the dedup key is only the `ELITEA-<id>` substring.
- **Hash-cache gotcha:** `echo "$path" | shasum` includes a trailing newline; a
  Python `hashlib.sha1(path.encode())` re-derivation will not match unless it hashes
  `path + '\n'`. Caused a false "0 files found" on an otherwise-successful fetch.

## The cap

`.agents/test-automation.yaml` states `max_new_cards_per_run: 10`. Observed history
is inconsistent with it ever having been honored (219→436 in a single 2026-07-15
pass; 256 filed as #726–#982 on 2026-07-23; zero capped-run entries in the daily
logs between). **File the full delta** — matches actual practice and the mission's
own task text — but **state the discrepancy explicitly** in the summary issue and
the operator report every run. Do not unilaterally edit the yaml; the last
correction of this shape (the already-automated three-condition rule) was
operator-confirmed before adoption.

## Superseded

Run 1's strict "already-automated AND-of-three" skip rule and its
"contradictory metadata → park unfiled" behavior are **wrong and superseded**
(human-confirmed, run 4, 2026-07-14): every case in that folder is *planned* for
automation, so its own `execution_type`/`status`/`automation_test_id` are unreliable
tagging artifacts. **The sole exclusion is: a tracker issue already exists for this
case id.** A populated real-looking `automation_test_id` is a hint to verify, never a
skip signal on its own. Module-wide metadata weirdness gets one FYI line in the
summary — it never withholds filing. (66 `artifacts` cases were wrongly parked in
run 1 and needed a dedicated run-4 correction pass.)

## Seen 3×

- 2026-07-14 runs 1/4 + 2026-07-15 run 7 — tree API, xargs failure, 59 phantom creates, policy correction.
- 2026-07-23 run — filename-id dedup confirmed across 692 files; 256-file delta.
- 2026-07-23 run — cap discrepancy reconciled against carded-count history and daily logs.

See also: bulk_tms_intake_technique.md ·
intake_max_new_cards_cap_appears_unenforced.md ·
tms_case_filename_embeds_id_cheap_dedup.md
