---
name: TMS back-write discipline
description: Post-merge onetest back-writes are hand-edited git commits, not MCP calls — stage only the case file, re-verify all four fields on every rework, and edit index.json surgically
type: feedback
---

## Rules

1. **No MCP verb writes case frontmatter.** Every `onetest-tms` tool operates on
   execution issues or the index — there is no `update_case`/`set_field`.
   `backwrite_on_done`'s "edit the case file" is literal: `cd ../onetest-ai-tm-Elitea`,
   `Edit` the YAML frontmatter, commit, `env -u GITHUB_TOKEN git push origin main`.
   Commit shape: `chore(<TMS-ID>): back-write automation status — ready/automated`
   plus a `Test merged: <PR URL>` body line.
2. **Stage by exact path — never `git add -A`.** That clone chronically carries a
   multi-thousand-line uncommitted `index.json` drift; a blanket add sweeps it into
   your one-line back-write.
3. **All four fields are re-derived fresh on every rework.** `automation_test_id`
   and `automation_pr` are *independent* facts: a testid-only rework leaves the test
   identity unchanged but supersedes the PR. Check that `automation_pr` names the PR
   currently merged into `automation/base` — "present" is not "correct".
4. **`index.json` back-write is surgical, never a full rebuild.** `correlate_results`
   reads the index, so the case's entry must be updated — but the committed index is
   ~300 cases behind disk, and `_index.py --dir tests --out index.json` yields a
   ~+7000/-1000-line diff over ~283 unrelated cases. Instead load the JSON, mutate
   the one `c["id"] == "ELITEA-XXXX"` entry (`status`/`execution_type`/
   `automation_test_id` — the last is a **list** even for one ref), re-dump with the
   script's exact format (`indent=2, ensure_ascii=False`, trailing newline), and
   confirm `git diff --numstat index.json` is small. A brand-new case not yet indexed
   does need a rebuild — then flag the drift separately, don't bundle it.
5. **Never commit an `index.json` diff without auditing its removals**, whether you
   generated it or found it in the tree:
   `git diff index.json | grep '^-' | grep -oP '"id": "\K[^"]+' | sort -u`, then
   `find . -iname "*<id>_*"` for each. Any removed id that still resolves to a real
   file = regression → `git checkout -- index.json`, do not carry it forward.
6. **A "not found" from `get_test_case`/`search_test_cases` is index staleness until
   proven otherwise.** If the `id:` frontmatter matches on disk, run `build_index`
   once and retry before concluding the ID is wrong.
7. **`status: draft` is this TMS's normal pre-automation state, NOT a skip gate** —
   it is literally the intake selector. The generic playbook's "skip Draft cases"
   example does not apply here and would misroute nearly every dispatch. Exception
   worth knowing: `status: draft` may legitimately be held *after* delivery when a
   known-defect soft-assertion has never yet been observed firing (declared
   improvisation, `question` #613 open) — check #613 for a ruling before treating
   such a delivery as a back-write FAIL.

## Seen 8×

- ELITEA-1894 / #62 (`68420ae`) + ELITEA-1915 / #63 (`c361696`) — hand-edit pattern confirmed twice.
- ELITEA-1974 / #78 — ~9,230-line stray `index.json` diff nearly swept into a one-line back-write.
- ELITEA-1738 / #28 (PR #206) — `automation_pr` missing after rework; ELITEA-1790 / #32 (PR #280) — present but stale at #48 instead of #280.
- …plus 5 earlier occurrence(s) — full per-case detail in the source entries below.

> `.agents/test-automation.yaml`'s Form C canon and the "index.json is NOT
> auto-rebuilt" caveat are already injected every session — this entry deliberately
> does not restate them, only the surgical-edit technique that closes the caveat.

See also: tms_backwrite_is_manual_git_edit_not_mcp_verb.md ·
tms_backwrite_scope_git_add_to_case_file.md ·
tms_back_write_can_go_stale_after_rework.md ·
tms_index_backwrite_surgical_not_full_rebuild.md ·
onetest_mcp_index_can_be_stale.md ·
build_index_regression_must_be_reverted_not_carried.md ·
tms_status_draft_when_defect_net_unreproduced.md ·
onetest_status_draft_is_normal_not_a_gate.md
