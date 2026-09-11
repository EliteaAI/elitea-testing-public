# Docs compaction advisor — propose a dedup PR, never merge (cardless)

## FOR SEPARATE LOOP maybe?
Unattended run - you are running with no human present,
**No one to ask.** Any needed decision becomes a `question` issue (the question,
   options, your recommendation, "Found while working #<this task>"), park the card
   (`Blocked` + `Waiting on #N`), and stop. Never guess to keep going. You return
   when a human drags the card back.
   
/session-retrospective skill - i want us to have a look and per-role memory.md files and optimize them, add/remove/consolidate/rewrite index of  lessons learned based on durable facts vs just simple log entries - we need to make sure agents get's in wht's important, not something which is just noise. Scope only to memory compaction/optimization, no other analysis.

##
Your mission this tick: find near-verbatim duplication across the 8 shared
`.agents/*` docs (`architecture.md`, `conventions.md`, `profile.md`,
`role-overrides.md`, `team-comms.md`, `test-automation.yaml`, `testing.md`,
`workflow.md` — all `@`-imported into root `CLAUDE.md`, so every byte here is
paid on every session AND every dispatched subagent), replace the
non-canonical copies with a one-line pointer, and open a **draft PR against
`automation/base`** for a human to review. **You never merge this PR. You
never commit this directly to `automation/base`.** This loop only proposes.

**Scope is narrow on purpose** (per the 2026-07-23 audit that justified
building this loop at all): only replace a block that is near-verbatim
(>80% textually similar) duplication of a block in another file, with the
LESS complete/less authoritative copy shrunk to a pointer. Do **not** attempt
general prose-tightening, rewording, or "improving" sentences — that was
tried during the audit and came back essentially empty; this corpus is
already lean outside of true duplication. Anything that isn't a clear
duplicate of another block stays untouched, full stop.

## Seed backlog (from the 2026-07-23 audit — start here on your first run)

1. **Testid-flow / human-cherry-pick rule** — stated in full 3 times inside
   `workflow.md` itself (intro ~19–28, § Testid flow 48–79 — canonical, keep
   this one full — § loop step 3 ~115–121, § closure-record rationale
   ~236–247) and restated in `architecture.md:67–86`, `conventions.md:44–48`,
   `profile.md:45,150–155`. Canonical home: `workflow.md` § Testid flow.
   Replace every other instance with one line: "See `.agents/workflow.md` §
   Testid flow for the full rule." (~2,700 bytes)
2. **`automation_test_id` Form C shape** — fullest in `test-automation.yaml:
   49–88` (includes the derivation + self-check + `index.json` caveat — keep
   full). `testing.md:105–121` and `profile.md:130–134` restate it with the
   identical example string. Replace both with a pointer to
   `.agents/test-automation.yaml`. (~950 bytes)
3. **Reviewer's mechanical grep regex** — `role-overrides.md:224–231` has the
   full regex (`get_by_placeholder`/`get_by_title`/`get_by_alt_text`/
   `get_by_test_id`/`query_selector`); `workflow.md:154–158` has a strict
   subset. Replace `workflow.md`'s partial copy with a pointer to
   `role-overrides.md`'s full one — never the other way around, the subset
   copy is the one missing coverage. (~350 bytes)
4. **Branch/PR policy** (`automation/base`, `tests/<case>-<slug>`, never PR
   `main`, squash merge) — restated in `conventions.md:40–43`,
   `profile.md:144–146,156`, `workflow.md:34,40`. Pick `workflow.md` as
   canonical (it's the fullest), pointer the rest. (~600 bytes)
5. **Small one-liner facts duplicated 2–3× each** (OneDrive slowness,
   `.env.test` precedence, deployed-envs-are-CI-only, never shallow-clone,
   never rebase/force-push `automation/testids`, ~2s WebSocket delay,
   Keycloak/`auth_state`, no-CI-on-`automation/base`, retired fork) — see
   the full audit table (posted to this PR's description by you, or ask
   your dispatcher to re-run the audit if this file has aged) — pick
   whichever file states each most completely, pointer the others.
   (~2,100 bytes)
6. **Stale note** — `workflow.md:272–275` § Unconfirmed claims "no PR
   history yet" on `automation/base`. Verify live with
   `env -u GITHUB_TOKEN gh pr list --base automation/base --state all` (per
   `.agents/profile.md` § Issue tracker identity rule) before touching —
   if PRs exist (they did as of 2026-07-23: hundreds), delete the stale
   claim or replace it with a current one-line fact. (~230 bytes)

**Explicitly OUT of scope this run** (audit classified these RISKY — a
human's call, not this loop's):
- `role-overrides.md`'s per-role condensed rules that summarize (not
  restate) `testing.md`'s fuller versions — these were defensible as
  intentional compression, and even where that rationale has weakened now
  that both files load together every session, a summary-vs-restatement
  judgment call belongs to a human, not this loop.
- Any block where you're not confident the "duplicate" is a real restatement
  rather than a distinct rule that merely uses similar words.
- Legitimate copy-paste payloads (e.g. the closure-record markdown template
  in `workflow.md`) — these are meant to be copied verbatim into GitHub
  comments, not narrative to dedupe.

## Method (for finding NEW duplication on later runs, once the seed backlog is clear)

For each pair of the 8 files, look for a paragraph/bullet in one that
restates — not merely references — a fact already stated more fully
elsewhere. A genuine restatement usually shares distinctive phrases or a
verbatim example (a literal test name, a literal regex, a literal path)
with the other copy. A **summary** that adds framing for a different
audience (e.g. role-overrides.md applying a shared rule to a specific job
function) is not a duplicate — leave it. When genuinely unsure, leave it and
note it in your report as a candidate for a human to judge, rather than
guessing.

## Mechanics

1. **Never touch a file without reading it in full first** — you're editing
   a rulebook other agents rely on for enforcement; partial context here is
   how a rule quietly gets weakened.
2. Branch off **fresh `automation/base`**, named
   `chore/agents-docs-dedup-<YYYY-MM-DD>` (not the `tests/<case>-<slug>`
   pattern — this isn't case work, keep it visually distinct).
3. Make the edits: shrink the non-canonical copy to one pointer line naming
   the exact file + section where the full rule now lives. Never delete a
   fact without leaving a live pointer to where it survives in full.
4. One commit per source file touched, message naming what was deduped and
   the byte delta, e.g. `chore(docs): dedup testid-flow restatement —
   architecture.md 4757 → 3400 bytes, see workflow.md`.
5. Push, then **open a DRAFT PR against `automation/base`**
   (`env -u GITHUB_TOKEN gh pr create --draft --base automation/base ...` —
   tracker-write identity rule, `.agents/profile.md` § Issue tracker). PR
   body must include:
   - A table: file, bytes before, bytes after, what now lives where.
   - Total corpus size before/after and the percentage reduction.
   - An explicit checklist for the human reviewer: **"verify no rule content
     was lost — each row below should read as a relocation, not a
     deletion"** with one line per edit naming the canonical file+section
     the trimmed content now points to.
6. **Stop.** Do not mark the PR ready for review, do not merge it, do not
   ping anyone beyond the PR itself existing. A human decides whether to
   merge, request changes, or close it.

## Do not

- Do not commit directly to `automation/base` under any circumstance — this
  loop's only write path to that branch is a PR, same as case work.
- Do not touch a file's meaning, only its restatement — if trimming a
  passage would require deciding whether two slightly-different wordings
  mean the same thing or not, that's a RISKY judgment call: skip it and note
  it in the PR description as "considered, left alone, human call."
  the whole point is the content survives verbatim, just outside the hook's
  inlined payload.
- Do not open a second compaction PR while an earlier one from this loop is
  still open — check `env -u GITHUB_TOKEN gh pr list --base automation/base
  --search "chore/agents-docs-dedup"` first; if one's open, skip this tick
  and report that instead of piling up parallel proposals.

## Questions

No card exists to park on. If something looks structurally wrong (a file
that no longer parses as expected, a fact you can't verify live), skip that
item, note it in the PR description or your report, and continue — never
guess and edit destructively.

End every run with a short report: files touched, bytes saved per file,
total before/after, the PR URL (or "no PR opened — nothing new to dedup" /
"skipped — an earlier compaction PR is still open").
